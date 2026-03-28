/**
 * gadgets/toggle-bank.js
 *
 * Reusable breaker / switch bank puzzle for pattern-matching states.
 * Best for 3-5 toggles driven entirely by hotspot.json data.
 *
 * CONTRACT — required keys in hotspot.json › popup:
 *   interaction {string}     must be "toggle-bank"
 *   prompt      {string}     instruction text shown above the switches
 *   switches    {string[]}   ordered list of switch labels, e.g. ["TV","WINDOW"]
 *   initial     {boolean[]}  initial on/off state per switch (same length)
 *   target      {boolean[]}  correct on/off pattern the player must reach
 *   on_success  {string}     message displayed when the pattern matches
 *   on_fail     {string}     message displayed when CHECK fails
 *   hint        {string?}    optional hint text; HINT button hidden if absent
 */

import { addText, makeButton } from "./panel.js";

function makeStateButton(label, position, w, h, getColors) {
  const btn = document.createElement("a-plane");
  btn.setAttribute("width", String(w));
  btn.setAttribute("height", String(h));
  btn.setAttribute("material", "shader: flat; opacity: 0.95");
  btn.setAttribute("position", position);
  btn.classList.add("vr-panel-btn", "clickable-panel");

  const txt = document.createElement("a-text");
  txt.setAttribute("value", label);
  txt.setAttribute("align", "center");
  txt.setAttribute("width", String(w * 3.8));
  txt.setAttribute("position", "0 0 0.002");
  txt.setAttribute("shader", "msdf");
  btn.appendChild(txt);

  function paint(hovered = false) {
    const colors = getColors();
    const fill = hovered ? colors.hover : colors.bg;
    btn.setAttribute("material", `shader: flat; opacity: 0.95; color: ${fill}`);
    txt.setAttribute("value", colors.label);
    txt.setAttribute("color", colors.text);
  }

  btn.addEventListener("mouseenter", () => paint(true));
  btn.addEventListener("mouseleave", () => paint(false));
  paint(false);

  return { btn, paint };
}

/**
 * Populate `root` with a breaker-toggle puzzle UI.
 *
 * @param {Element}  root      panel root <a-entity> (shell already built)
 * @param {object}   data      popup object from hotspot.json
 * @param {Function} onSolve   called with no args when pattern is correct
 * @param {Function} onClose   called with no args when CLOSE is pressed
 */
export function buildToggleBank(root, data, onSolve, onClose) {
  const switchLabels = Array.isArray(data.switches) ? data.switches : [];
  const count = switchLabels.length;
  const initial = Array.isArray(data.initial) ? data.initial : [];
  const target = Array.isArray(data.target) ? data.target : [];
  const states = switchLabels.map((_, i) => Boolean(initial[i]));
  const targetStates = switchLabels.map((_, i) => Boolean(target[i]));

  let solved = false;
  let hintOn = false;

  addText(root, data.prompt || "",
    "0 0.26 0.002",
    { color: "#d8ecc0", width: "1.35", scale: 0.56, baseline: "top", wrapCount: 32 });

  const feedbackText = addText(root, "", "0 -0.56 0.003",
    { color: "#7ecf3a", width: "1.3", scale: 0.54, baseline: "top", wrapCount: 32 });

  const hintText = addText(root, "", "0 -0.67 0.003",
    { color: "#7a9a6a", width: "1.3", scale: 0.49, baseline: "top", wrapCount: 34 });

  function setFeedback(msg, color) {
    feedbackText.setAttribute("value", msg || "");
    feedbackText.setAttribute("color", color || "#7ecf3a");
  }

  const rowTop = 0.00;
  const rowBottom = -0.42;
  const rowGap = count > 1 ? (rowTop - rowBottom) / (count - 1) : 0.16;
  const togglePainters = [];

  switchLabels.forEach((label, i) => {
    const y = rowTop - i * rowGap;

    addText(root, label, `0 ${y} 0.003`, {
      color: "#d8ecc0",
      width: "1.0",
      scale: 0.52,
      align: "left",
      xOffset: -0.71
    });

    const stateButton = makeStateButton("OFF", `0.47 ${y} 0.003`, 0.32, 0.11, () => {
      const active = states[i];
      return active
        ? { label: "ON", bg: "#294f16", hover: "#34661d", text: "#bff48d" }
        : { label: "OFF", bg: "#1a1a1a", hover: "#343434", text: "#888888" };
    });

    stateButton.btn.addEventListener("click", (e) => {
      e.stopPropagation();
      if (solved) return;
      states[i] = !states[i];
      stateButton.paint(false);
      setFeedback("", "#7ecf3a");
    });

    togglePainters.push(stateButton.paint);
    root.appendChild(stateButton.btn);
  });

  function patternsMatch() {
    return states.length === targetStates.length &&
      states.every((value, i) => value === targetStates[i]);
  }

  const checkBtn = makeButton("CHECK", "-0.54 -0.80 0.003",
    0.26, 0.11, "#3a5a1a", "#7ecf3a");
  checkBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    if (solved) return;
    if (patternsMatch()) {
      solved = true;
      setFeedback(data.on_success, "#7ecf3a");
      onSolve();
    } else {
      setFeedback(data.on_fail, "#f08080");
    }
  });
  root.appendChild(checkBtn);

  const resetBtn = makeButton("RESET", "-0.18 -0.80 0.003",
    0.26, 0.11, "#1a1a1a", "#888888");
  resetBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    if (solved) return;
    states.forEach((_, i) => { states[i] = Boolean(initial[i]); });
    togglePainters.forEach((paint) => paint(false));
    setFeedback("", "#7ecf3a");
  });
  root.appendChild(resetBtn);

  if (data.hint) {
    const hintBtn = makeButton("HINT", "0.18 -0.80 0.003",
      0.26, 0.11, "#3a5a1a", "#7a9a6a");
    hintBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      hintOn = !hintOn;
      hintText.setAttribute("value", hintOn ? data.hint : "");
    });
    root.appendChild(hintBtn);
  }

  const closeBtn = makeButton("CLOSE", "0.54 -0.80 0.003",
    0.26, 0.11, "#1a1a1a", "#888888");
  closeBtn.addEventListener("click", (e) => { e.stopPropagation(); onClose(); });
  root.appendChild(closeBtn);

  root.querySelectorAll("a-plane").forEach(p => p.classList.add("vr-panel-btn"));
}
