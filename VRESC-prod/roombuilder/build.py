#!/usr/bin/env python3
"""
build.py — VRESC Room Builder CLI

Usage:
    python roombuilder/build.py <params.json> [options]

Runs the full room build pipeline defined in stages.yaml.
  • Prompt steps   — render a metaprompt → src_prompts/, then wait for the
                     human/AI to drop the output_artifact into artifacts/.
  • Action steps   — run automatically (ffmpeg frame extract, file writers, etc.)

Flags:
  --deploy                  Also run the deploy_room stage (copies artifacts →
                            content/). Skipped by default.
  --clean                   Delete all artifacts for the room, then exit.
  --clean-from <stage>      Delete artifacts for <stage> and all downstream stages,
                            then exit.
  --cleanbuild              Delete all artifacts, then run the full build.
  --cleanbuild-from <stage> Delete artifacts from <stage> onward, then build.

Progress is displayed as a live animated panel that redraws in place.
"""

import argparse
import importlib
import json
import sys
import threading
import time
from collections import deque
from pathlib import Path

import yaml

# ── paths ────────────────────────────────────────────────────────────────────

HERE = Path(__file__).parent
STAGES_YAML = HERE / "stages.yaml"
ROOT = HERE.parent
CONTENT_DIR = ROOT / "content"

# ── ANSI colour palette ──────────────────────────────────────────────────────


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BRED = "\033[91m"
    BGREEN = "\033[92m"
    BYELLOW = "\033[93m"
    BBLUE = "\033[94m"
    BMAGENTA = "\033[95m"
    BCYAN = "\033[96m"
    BWHITE = "\033[97m"

    BG_BLACK = "\033[40m"
    BG_BLUE = "\033[44m"
    BG_GREEN = "\033[42m"


# ── step states ──────────────────────────────────────────────────────────────

BLOCKED = "blocked"
READY = "ready"
RUNNING = "running"  # action steps executing
WAITING = "waiting"  # prompt steps — waiting for human artifact
DONE = "done"  # executed and completed this session
STUBBED = "stubbed"  # completed using a stub / placeholder
CACHED = "cached"  # not executed — artifact was already present
SKIPPED = "skipped"
ERROR = "error"

# ── spinner frames ───────────────────────────────────────────────────────────

SPINNER_BLOCKS = ["▏", "▎", "▍", "▌", "▋", "▊", "▉", "█", "▉", "▊", "▋", "▌", "▍", "▎"]
SPINNER_DOTS = ["⣾", "⣽", "⣻", "⢿", "⡿", "⣟", "⣯", "⣷"]
WAIT_PULSE = ["░░", "▒░", "▓▒", "██", "▓▒", "▒░", "░░", "░░"]

# ── load stages.yaml ─────────────────────────────────────────────────────────


def load_stages() -> dict:
    from helpers import loaders as _loaders

    loader_registry = {name: fn for name, fn in vars(_loaders).items() if callable(fn) and not name.startswith("_")}

    raw = yaml.safe_load(STAGES_YAML.read_text(encoding="utf-8"))
    stages = {}
    for name, cfg in raw.items():
        auto_raw = cfg.get("auto") or {}
        auto = {}
        for var, loader_name in auto_raw.items():
            if loader_name not in loader_registry:
                raise ValueError(f"stages.yaml: step '{name}' auto.{var} references unknown loader '{loader_name}'")
            auto[var] = loader_registry[loader_name]

        stages[name] = {
            "prompt": cfg.get("prompt"),
            "action": cfg.get("action"),
            "depends_on": cfg.get("depends_on") or [],
            "required": cfg.get("required") or [],
            "auto": auto,
            "output_artifact": cfg.get("output_artifact"),
        }
    return stages


# ── params loading ────────────────────────────────────────────────────────────


def load_params(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    resolved = {}
    for k, v in data.items():
        if isinstance(v, str) and v.startswith("@"):
            ref = ROOT / v[1:]
            if not ref.exists():
                sys.exit(f"Error: params field {k!r} references missing file: {ref}")
            resolved[k] = ref.read_text(encoding="utf-8").strip()
        else:
            resolved[k] = str(v) if not isinstance(v, str) else v
    return resolved


# ── topological sort ──────────────────────────────────────────────────────────


def topo_sort(stages: dict) -> list[str]:
    visited, order = set(), []

    def visit(name):
        if name in visited:
            return
        visited.add(name)
        for dep in stages[name]["depends_on"]:
            if dep in stages:
                visit(dep)
        order.append(name)

    for name in stages:
        visit(name)
    return order


# ── cache helpers ─────────────────────────────────────────────────────────────


def downstream(stages: dict, roots: set[str]) -> set[str]:
    """Return roots plus every stage that transitively depends on any root."""
    affected = set(roots)
    changed = True
    while changed:
        changed = False
        for name, step in stages.items():
            if name not in affected and any(d in affected for d in step["depends_on"]):
                affected.add(name)
                changed = True
    return affected


def clean_artifacts(stages: dict, artifacts_dir: Path, room_id: str, names: set[str]) -> list[str]:
    """Delete output_artifact files for each named stage. Returns list of deleted paths."""
    deleted = []
    for name in names:
        template = stages[name].get("output_artifact")
        if not template:
            continue
        path = artifacts_dir / template.format(room_id=room_id)
        if path.exists():
            path.unlink()
            deleted.append(str(path.relative_to(artifacts_dir.parent)))
    return deleted


# ── artifact helpers ──────────────────────────────────────────────────────────


def artifact_path(artifacts_dir: Path, template: str, room_id: str) -> Path:
    return artifacts_dir / template.format(room_id=room_id)


def artifact_exists(artifacts_dir: Path, template: str | None, room_id: str) -> bool:
    if not template:
        return True
    return artifact_path(artifacts_dir, template, room_id).exists()


_SUCCESS = (DONE, STUBBED, CACHED)


def deps_done(step: dict, states: dict) -> bool:
    return all(states.get(d) in _SUCCESS for d in step["depends_on"])


def deps_unresolvable(step: dict, states: dict) -> bool:
    """True if any dependency is in a terminal non-success state (error or skipped)."""
    return any(states.get(d) in (ERROR, SKIPPED) for d in step["depends_on"])


def params_ok(step: dict, params: dict) -> bool:
    return all(f in params and params[f] for f in step["required"])


# ── display engine ────────────────────────────────────────────────────────────


class Display:
    """
    Redraws the full progress panel in place using ANSI cursor control.
    Runs in a background thread; the main thread calls .update() to push new state.
    """

    LOG_LINES = 6  # number of log lines shown at the bottom

    def __init__(self, room_id: str, order: list[str], stages: dict):
        self.room_id = room_id
        self.order = order
        self.stages = stages
        self.states = {n: BLOCKED for n in order}
        self.started = {n: None for n in order}
        self.log_buf = deque(maxlen=self.LOG_LINES)
        self._lock = threading.Lock()
        self._frame = 0
        self._lines = 0  # lines printed last redraw (for cursor rewind)
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)

    def start(self):
        self._clear_screen()
        self._thread.start()

    def stop(self):
        self._running = False
        self._thread.join(timeout=2)

    def update(self, name: str, state: str):
        with self._lock:
            self.states[name] = state
            if state in (RUNNING, WAITING) and self.started[name] is None:
                self.started[name] = time.monotonic()

    def log(self, name: str, msg: str):
        ts = time.strftime("%H:%M:%S")
        with self._lock:
            self.log_buf.append((ts, name, msg))

    def _clear_screen(self):
        print("\033[2J\033[H", end="", flush=True)

    def _rewind(self):
        if self._lines:
            print(f"\033[{self._lines}A\033[J", end="", flush=True)

    def _elapsed(self, name: str) -> str:
        t = self.started[name]
        if t is None:
            return ""
        s = int(time.monotonic() - t)
        return f"{s // 60:02d}:{s % 60:02d}"

    def _dot(self, state: str, frame: int) -> str:
        if state == DONE:
            return f"{C.BGREEN}██{C.RESET}"
        if state == STUBBED:
            return f"{C.BYELLOW}▓▓{C.RESET}"
        if state == CACHED:
            return f"{C.GREEN}▒▒{C.RESET}"
        if state == ERROR:
            return f"{C.BRED}██{C.RESET}"
        if state == SKIPPED:
            return f"{C.DIM}··{C.RESET}"
        if state == RUNNING:
            spinner = SPINNER_BLOCKS[frame % len(SPINNER_BLOCKS)]
            return f"{C.BCYAN}{spinner}{spinner}{C.RESET}"
        if state == WAITING:
            pulse = WAIT_PULSE[frame % len(WAIT_PULSE)]
            return f"{C.BYELLOW}{pulse}{C.RESET}"
        if state == READY:
            return f"{C.BBLUE}░░{C.RESET}"
        return f"{C.DIM}──{C.RESET}"  # BLOCKED

    def _state_label(self, state: str) -> str:
        labels = {
            DONE: f"{C.BGREEN}done{C.RESET}",
            STUBBED: f"{C.BYELLOW}stub{C.RESET}",
            CACHED: f"{C.GREEN}cached{C.RESET}",
            ERROR: f"{C.BRED}error{C.RESET}",
            SKIPPED: f"{C.DIM}skipped{C.RESET}",
            RUNNING: f"{C.BCYAN}running{C.RESET}",
            WAITING: f"{C.BYELLOW}waiting artifact{C.RESET}",
            READY: f"{C.BBLUE}ready{C.RESET}",
            BLOCKED: f"{C.DIM}blocked{C.RESET}",
        }
        return labels.get(state, state)

    def _render(self, frame: int) -> list[str]:
        lines = []

        # ── header ──────────────────────────────────────────────────────────
        lines.append(
            f"\n  {C.BOLD}{C.BWHITE}VRESC Room Builder{C.RESET}  "
            f"{C.BMAGENTA}·{C.RESET}  "
            f"{C.BCYAN}{self.room_id}{C.RESET}"
        )
        lines.append(f"  {C.DIM}{'─' * 58}{C.RESET}\n")

        # ── step rows ────────────────────────────────────────────────────────
        with self._lock:
            states = dict(self.states)
            started = dict(self.started)
            logs = list(self.log_buf)

        for i, name in enumerate(self.order):
            state = states[name]
            step = self.stages[name]
            kind = "action" if step["action"] else "prompt"
            dot = self._dot(state, frame + i)
            label = self._state_label(state)
            elapsed = ""
            if state in (RUNNING, WAITING) and started[name]:
                s = int(time.monotonic() - started[name])
                elapsed = f"  {C.DIM}{s // 60:02d}:{s % 60:02d}{C.RESET}"

            kind_col = f"{C.BBLUE}prompt{C.RESET}" if kind == "prompt" else f"{C.BMAGENTA}action{C.RESET}"
            lines.append(f"  {dot}  {C.BOLD}{name:<28}{C.RESET}  {kind_col:<6}  {label}{elapsed}")

        # ── separator ────────────────────────────────────────────────────────
        lines.append(f"\n  {C.DIM}{'─' * 58}{C.RESET}")

        # ── next action hint ─────────────────────────────────────────────────
        hint = ""
        for name in self.order:
            if states[name] == WAITING:
                art = self.stages[name]["output_artifact"]
                if art:
                    hint = (
                        f"  {C.BYELLOW}▶{C.RESET}  Drop "
                        f"{C.BOLD}artifacts/{self.room_id}/"
                        f"{art.format(room_id=self.room_id)}{C.RESET}"
                        f"  to continue"
                    )
                break
            if states[name] == RUNNING:
                hint = f"  {C.BCYAN}▶{C.RESET}  Running {C.BOLD}{name}{C.RESET}…"
                break

        lines.append(hint if hint else f"  {C.DIM}waiting…{C.RESET}")

        # ── log tail ─────────────────────────────────────────────────────────
        lines.append(f"\n  {C.DIM}{'─' * 58}{C.RESET}")
        if logs:
            for ts, step_name, msg in logs:
                step_col = f"{C.DIM}{step_name}{C.RESET}"
                lines.append(f"  {C.DIM}{ts}{C.RESET}  {step_col:<28}  {msg}")
        else:
            lines.append(f"  {C.DIM}no log entries yet{C.RESET}")

        lines.append("")
        return lines

    def _loop(self):
        frame = 0
        while self._running:
            lines = self._render(frame)
            out = "\n".join(lines)
            # rewind and redraw
            self._rewind()
            print(out, end="", flush=True)
            self._lines = out.count("\n") + 1
            frame += 1
            time.sleep(0.12)

        # final draw — static
        lines = self._render(frame)
        self._rewind()
        print("\n".join(lines), flush=True)


# ── build engine ──────────────────────────────────────────────────────────────


def run_build(
    params_path: Path,
    deploy: bool = False,
    clean_all: bool = False,
    clean_from: str | None = None,
    build: bool = True,
):
    params = load_params(params_path)
    room_id = params.get("room_id")
    if not room_id:
        sys.exit("Error: params file must contain 'room_id'")

    stages = load_stages()
    order = topo_sort(stages)
    artifacts_dir = HERE / "artifacts" / room_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # ── cache cleaning ────────────────────────────────────────────────────────
    if clean_all:
        deleted = clean_artifacts(stages, artifacts_dir, room_id, set(stages))
        if deleted:
            print(f"\n  {C.BYELLOW}cache cleared{C.RESET}  {len(deleted)} artifact(s) removed")
            for p in deleted:
                print(f"  {C.DIM}  {p}{C.RESET}")
            print()
        else:
            print(f"\n  {C.DIM}cache already empty{C.RESET}\n")
    elif clean_from:
        if clean_from not in stages:
            sys.exit(f"Error: unknown stage '{clean_from}'. Valid stages: {', '.join(order)}")
        affected = downstream(stages, {clean_from})
        deleted = clean_artifacts(stages, artifacts_dir, room_id, affected)
        if deleted:
            print(
                f"\n  {C.BYELLOW}cache cleared from {C.BOLD}{clean_from}{C.RESET}"
                f"{C.BYELLOW} ({len(affected)} stage(s) affected){C.RESET}"
            )
            for p in deleted:
                print(f"  {C.DIM}  {p}{C.RESET}")
            print()
        else:
            print(f"\n  {C.DIM}nothing to clean from {clean_from!r}{C.RESET}\n")

    if not build:
        return

    # Stages pinned to SKIPPED before the build starts (not subject to refresh).
    pinned_skipped: set[str] = set()
    if not deploy and "deploy_room" in stages:
        pinned_skipped.add("deploy_room")

    disp = Display(room_id, order, stages)
    for name in pinned_skipped:
        disp.update(name, SKIPPED)
    disp.start()

    # ── initial state pass ────────────────────────────────────────────────────
    def refresh_states():
        for name in order:
            if name in pinned_skipped:
                continue
            step = stages[name]
            state = disp.states[name]
            if state in (DONE, STUBBED, CACHED, ERROR, SKIPPED):
                continue
            if not params_ok(step, params):
                disp.update(name, SKIPPED)
                continue
            if deps_unresolvable(step, disp.states):
                disp.update(name, SKIPPED)
                continue
            if deps_done(step, disp.states):
                # Action steps with no output_artifact must always run explicitly;
                # only mark them DONE via the main loop after run() succeeds.
                if step["output_artifact"] is not None and artifact_exists(
                    artifacts_dir, step["output_artifact"], room_id
                ):
                    disp.update(name, CACHED)
                else:
                    disp.update(name, READY)
            else:
                disp.update(name, BLOCKED)

    refresh_states()

    # ── main loop ─────────────────────────────────────────────────────────────
    stub_flags: dict[str, bool] = {n: False for n in order}

    def make_log(step_name):
        def _log(msg):
            disp.log(step_name, msg)
            if msg.startswith("stub:"):
                stub_flags[step_name] = True

        return _log

    try:
        while True:
            refresh_states()

            # find the next ready step
            next_step = None
            for name in order:
                if disp.states[name] == READY:
                    next_step = name
                    break

            if next_step is None:
                # check if everything is done / blocked-forever / waiting
                active = [n for n in order if disp.states[n] not in (DONE, STUBBED, CACHED, SKIPPED, ERROR)]
                if not active:
                    break  # all done

                # if only waiting states remain — poll for artifacts
                non_waiting = [n for n in active if disp.states[n] != WAITING]
                if not non_waiting:
                    time.sleep(1)
                    continue

                time.sleep(0.5)
                continue

            name = next_step
            step = stages[name]
            log = make_log(name)
            is_prompt = bool(step["prompt"])

            # ── set initial state ─────────────────────────────────────────────
            disp.update(name, WAITING if is_prompt else RUNNING)

            # ── dispatch to handlers/{name}.py ────────────────────────────────
            try:
                mod = importlib.import_module(f"handlers.{name}")
                mod.run(room_id, params, artifacts_dir, CONTENT_DIR, log)
            except Exception as e:
                disp.update(name, ERROR)
                log(f"ERROR: {e}")
                refresh_states()
                continue

            # ── for prompt steps: poll until artifact appears ─────────────────
            if is_prompt:
                art_template = step["output_artifact"]
                if art_template:
                    art = artifact_path(artifacts_dir, art_template, room_id)
                    while not art.exists():
                        time.sleep(1)
                    log(f"artifact received  {art.name}")

            disp.update(name, STUBBED if stub_flags[name] else DONE)

            # Merge scene_analyze output into params so downstream stages
            # can use scene_description / scene_summary in their metaprompts.
            if name == "scene_analyze":
                scene_file = artifacts_dir / "scene_analyze.json"
                if scene_file.exists():
                    scene_data = json.loads(scene_file.read_text(encoding="utf-8"))
                    for key, value in scene_data.items():
                        if key not in params or not params[key]:
                            params[key] = value

            refresh_states()

    except KeyboardInterrupt:
        pass
    finally:
        time.sleep(0.3)
        disp.stop()

    # ── final pass: any stage still BLOCKED was never executed → SKIPPED ────────
    for name in order:
        if disp.states.get(name) == BLOCKED:
            disp.update(name, SKIPPED)

    # ── final summary ─────────────────────────────────────────────────────────
    counts = {s: 0 for s in (DONE, STUBBED, CACHED, SKIPPED, ERROR, WAITING)}
    for n in order:
        st = disp.states.get(n, SKIPPED)
        counts[st] = counts.get(st, 0) + 1

    stub_note = f"  {C.BYELLOW}{counts[STUBBED]} stubbed{C.RESET}" if counts[STUBBED] else ""
    print(
        f"\n  {C.BOLD}Build complete{C.RESET}  "
        f"{C.BGREEN}{counts[DONE]} done{C.RESET}  "
        f"{stub_note}"
        f"{C.DIM}{counts[CACHED]} cached{C.RESET}  "
        f"{C.DIM}{counts[SKIPPED]} skipped{C.RESET}  "
        f"{C.BRED}{counts[ERROR]} errors{C.RESET}\n"
    )


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="build.py",
        description="VRESC Room Builder — run the full room build pipeline.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python roombuilder/build.py params.json\n"
            "  python roombuilder/build.py params.json --deploy\n"
            "  python roombuilder/build.py params.json --clean\n"
            "  python roombuilder/build.py params.json --clean-from hotspot_content\n"
            "  python roombuilder/build.py params.json --cleanbuild\n"
            "  python roombuilder/build.py params.json --cleanbuild-from hotspot_content\n"
        ),
    )
    parser.add_argument("params", metavar="params.json", help="Path to the room params JSON file")
    parser.add_argument(
        "--deploy",
        action="store_true",
        default=False,
        help="Also run deploy_room (copies artifacts → content/). Skipped by default.",
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--clean",
        action="store_true",
        default=False,
        help="Delete all cached artifacts, then exit (no build).",
    )
    mode_group.add_argument(
        "--clean-from",
        metavar="STAGE",
        default=None,
        help="Delete artifacts for STAGE and all downstream stages, then exit (no build).",
    )
    mode_group.add_argument(
        "--cleanbuild",
        action="store_true",
        default=False,
        help="Delete all cached artifacts, then run the full build.",
    )
    mode_group.add_argument(
        "--cleanbuild-from",
        metavar="STAGE",
        default=None,
        help="Delete artifacts for STAGE and all downstream stages, then build.",
    )
    args = parser.parse_args()

    params_file = Path(args.params)
    if not params_file.exists():
        sys.exit(f"Error: params file not found: {params_file}")

    # make handlers importable regardless of cwd
    sys.path.insert(0, str(HERE))

    run_build(
        params_file,
        deploy=args.deploy,
        clean_all=args.clean or args.cleanbuild,
        clean_from=args.clean_from or args.cleanbuild_from,
        build=not (args.clean or args.clean_from),
    )
