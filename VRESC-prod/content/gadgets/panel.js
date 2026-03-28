/**
 * gadgets/panel.js
 *
 * Low-level A-Frame geometry helpers shared across all rooms and quests.
 * No interaction logic — only primitive builders used by all gadgets.
 *
 * CONTRACT — shared keys in hotspot.json › popup (read by buildShell):
 *   title  {string}   panel heading shown in title bar and content area
 *   badge  {string?}  small category label shown below the title bar
 *
 * These keys are required by every hotspot regardless of interaction type.
 * Gadget-specific keys are defined in each gadget's own CONTRACT block.
 */

/**
 * Add an <a-text> child to parent.
 * @param {Element} parent
 * @param {string}  value
 * @param {string}  position  "x y z"
 * @param {object}  opts
 * @returns {Element}
 */
export function addText(parent, value, position, opts = {}) {
  const el = document.createElement("a-text");
  el.setAttribute("value", value);
  el.setAttribute("align", opts.align || "center");
  el.setAttribute("color", opts.color || "#ffffff");
  el.setAttribute("width", String(opts.width || "1.4"));
  el.setAttribute("wrap-count", String(opts.wrapCount || 28));
  el.setAttribute("shader", "msdf");
  if (opts.baseline) el.setAttribute("baseline", opts.baseline);

  const [bx, by, bz] = position.split(" ").map(Number);
  el.setAttribute("position", `${bx + (opts.xOffset || 0)} ${by} ${bz}`);

  if (opts.scale != null) {
    const s = opts.scale;
    el.setAttribute("scale", `${s} ${s} ${s}`);
  }

  parent.appendChild(el);
  return el;
}

/**
 * Create a flat <a-plane> button with a text label.
 * Gets classes "vr-panel-btn" and "clickable-panel" for raycaster targeting.
 * @returns {Element}
 */
export function makeButton(label, position, w, h,
  bgColor = "#181e12", textColor = "#7ecf3a") {
  const btn = document.createElement("a-plane");
  btn.setAttribute("width",    String(w));
  btn.setAttribute("height",   String(h));
  btn.setAttribute("color",    bgColor);
  btn.setAttribute("material", "shader: flat; opacity: 0.95");
  btn.setAttribute("position", position);
  btn.classList.add("vr-panel-btn", "clickable-panel");

  btn.addEventListener("mouseenter", () =>
    btn.setAttribute("material", "shader: flat; opacity: 0.95; color: #2a4a1a"));
  btn.addEventListener("mouseleave", () =>
    btn.setAttribute("material", `shader: flat; opacity: 0.95; color: ${bgColor}`));

  const txt = document.createElement("a-text");
  txt.setAttribute("value",    label);
  txt.setAttribute("align",    "center");
  txt.setAttribute("color",    textColor);
  txt.setAttribute("width",    String(w * 6));
  txt.setAttribute("position", "0 0 0.002");
  txt.setAttribute("shader",   "msdf");
  btn.appendChild(txt);

  return btn;
}

/**
 * Build the standard outer panel shell: border, background, title bar,
 * badge, heading.  Returns the root <a-entity> — caller appends to camera.
 *
 * Content area coordinate system (metres, origin at panel centre):
 *   Y  +0.95  top edge
 *   Y  +0.77  bottom of title bar  ← content starts here
 *   Y  -0.95  bottom edge
 *   X  ±0.80  left / right edges
 *
 * @param {object} popup  full popup object from hotspot.json
 * @returns {Element}
 */
export function buildShell(popup) {
  const root = document.createElement("a-entity");
  root.setAttribute("id",       "vr-panel-root");
  root.setAttribute("position", "0 0 -1.8");

  // ── border (sits behind background) ─────────────────────────────────────
  const border = document.createElement("a-plane");
  border.setAttribute("width",    "2");
  border.setAttribute("height",   "2");
  border.setAttribute("color",    "#3a5a1a");
  border.setAttribute("material", "shader: flat; opacity: 0.5");
  border.setAttribute("position", "0 0 -0.001");
  root.appendChild(border);

  // ── main background ──────────────────────────────────────────────────────
  const bg = document.createElement("a-plane");
  bg.setAttribute("width",    "1.98");
  bg.setAttribute("height",   "1.98");
  bg.setAttribute("color",    "#0a0d0f");
  bg.setAttribute("material", "shader: flat; opacity: 0.5");
  root.appendChild(bg);

  // ── heading ──────────────────────────────────────────────────────────────
  addText(root, popup.title,
    "0 0.90 0.002",
    { color: "#7ecf3a", width: "1.4", scale: 0.75, baseline: "top" });

  return root;
}
