/**
 * gadgets/numpad.js
 *
 * Reusable numpad builder for numeric-answer puzzles.
 * Works in any room or quest — just call buildNumpad() with the panel root.
 *
 * CONTRACT — required keys in hotspot.json › popup:
 *   interaction {string}   must be "numpad"
 *   prompt      {string}   question shown above the pad
 *   answer      {string}   correct numeric answer, e.g. "7" or "1957"
 *   on_success  {string}   message displayed when the answer is correct
 *   on_fail     {string}   message displayed when the answer is wrong
 *   hint        {string?}  optional hint text; HINT button hidden if absent
 *
 * Layout (Y coords relative to panel root centre):
 *   0.20  prompt text
 *  -0.22  digit display
 *  -0.28  numpad top row  (1 2 3)
 *  -0.46  row 2           (4 5 6)
 *  -0.64  row 3           (7 8 9)
 *  -0.76  bottom row      (CLR 0 ENT)
 *  -0.88  HINT / CLOSE
 */

import { addText, makeButton } from "./panel.js";

/**
 * Populate `root` with a numeric-answer puzzle UI.
 *
 * @param {Element}  root      panel root <a-entity> (shell already built)
 * @param {object}   data      popup object from hotspot.json
 *                             { prompt, answer, hint, on_success, on_fail }
 * @param {Function} onSolve   called with no args when answer is correct
 * @param {Function} onClose   called with no args when CLOSE is pressed
 */
export function buildNumpad(root, data, onSolve, onClose) {
  let input  = "";
  let solved = false;
  let hintOn = false;
  const maxLen = Math.max(String(data.answer).length, 4);

  // ── prompt ───────────────────────────────────────────────────────────────
  addText(root, data.prompt,
    "0 0.75 0.002",
    { color: "#d8ecc0", width: "1.35", scale: 0.8, baseline: "top" });

  // ── digit display ─────────────────────────────────────────────────────────
  const dispBg = document.createElement("a-plane");
  dispBg.setAttribute("width",    "0.5");
  dispBg.setAttribute("height",   "0.14");
  dispBg.setAttribute("color",    "#0a0a08");
  dispBg.setAttribute("material", "shader: flat");
  dispBg.setAttribute("position", "0 0.14 0.002");
  root.appendChild(dispBg);

  const dispText = addText(root, "_", "0 0.14 0.003",
    { color: "#7ecf3a", width: "0.8", scale: 2 });

  function updateDisplay() {
    dispText.setAttribute("value", input || "_");
  }

  // ── feedback + hint text ──────────────────────────────────────────────────
  const feedbackText = addText(root, "", "0 -0.70 0.003",
    { color: "#7ecf3a", width: "1.3", scale: 0.65, baseline: "top" });

  const hintText = addText(root, "", "0 -0.70 0.003",
    { color: "#a4ccae", width: "1.3", scale: 0.65, baseline: "top" });

  function setFeedback(msg, color) {
    feedbackText.setAttribute("value", msg);
    feedbackText.setAttribute("color", color || "#7ecf3a");
  }

  // ── answer logic ──────────────────────────────────────────────────────────
  function onKey(key) {
    if (solved) return;
    if (key === "CLR") {
      input = "";
      setFeedback("", "");
    } else if (key === "ENT") {
      hintText.setAttribute("value", "");
      if (input === String(data.answer)) {
        solved = true;
        setFeedback(data.on_success, "#7ecf3a");
        onSolve();
      } else {
        setFeedback(data.on_fail, "#f08080");
        input = "";
        updateDisplay();
      }
    } else {
      if (input.length < maxLen) input += key;
    }
    updateDisplay();
  }

  // ── numpad grid  1-2-3 / 4-5-6 / 7-8-9 / CLR-0-ENT ─────────────────────
  const PAD_KEYS = [
    ["1", "2", "3"],
    ["4", "5", "6"],
    ["7", "8", "9"],
    ["CLR", "0", "ENT"],
  ];
  const KW = 0.26, KH = 0.12, KGAP = 0.05;
  const padTop = -0.08;

  PAD_KEYS.forEach((row, ri) => {
    row.forEach((key, ci) => {
      const kx = (ci - 1) * (KW + KGAP);
      const ky = padTop - ri * (KH + KGAP);
      const btn = makeButton(key, `${kx} ${ky} 0.003`, KW, KH);
      btn.addEventListener("click", (e) => { e.stopPropagation(); onKey(key); });
      root.appendChild(btn);
    });
  });

  // ── HINT button ───────────────────────────────────────────────────────────
  if (data.hint) {
    const hintBtn = makeButton("HINT", "-0.6 -0.76 0.003",
      0.26, 0.11);
    hintBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      hintOn = !hintOn;
      hintText.setAttribute("value", hintOn ? data.hint : "");
      setFeedback("", "");
    });
    root.appendChild(hintBtn);
  }

  // ── CLOSE button ──────────────────────────────────────────────────────────
  const closeBtn = makeButton("CLOSE", "0.6 -0.76 0.003",
    0.26, 0.11);
  closeBtn.addEventListener("click", (e) => { e.stopPropagation(); onClose(); });
  root.appendChild(closeBtn);

  // Register all newly added planes with the raycaster
  root.querySelectorAll("a-plane").forEach(p => p.classList.add("vr-panel-btn"));
}
