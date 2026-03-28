"""
helpers/prompt.py — Render a metaprompt template and write it to src_prompts/.

Called by each prompt handler in handlers/.
The rendered file is saved to artifacts/{room_id}/src_prompts/{filename}
so the user can copy-paste it into their AI tool.
"""

from pathlib import Path

HERE = Path(__file__).parent.parent  # roombuilder/
METAPROMPTS = HERE / "metaprompts"


def render(
    filename: str,
    params: dict,
    auto: dict,
    artifacts_dir: Path,
    log,
) -> None:
    out_dir = artifacts_dir / "src_prompts"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / filename

    template_path = METAPROMPTS / filename
    if not template_path.exists():
        raise FileNotFoundError(f"Metaprompt not found: {template_path}")

    variables = dict(params)
    for var_name, loader in auto.items():
        room_id = params.get("room_id", "")
        variables[var_name] = loader(room_id)

    try:
        rendered = template_path.read_text(encoding="utf-8").format(**variables)
    except KeyError as e:
        raise RuntimeError(f"Undefined variable {e} in metaprompt {filename}") from e

    out_file.write_text(rendered, encoding="utf-8")
    log(f"wrote  src_prompts/{filename}")
