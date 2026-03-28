/**
 * gadgets/info.js
 *
 * Body builder for display-only hotspots (no interaction, no answer).
 * Renders a body text block and a CLOSE button inside the panel shell.
 *
 * CONTRACT — required keys in hotspot.json › popup:
 *   interaction {string}  must be "info"
 *   body        {string}  descriptive text shown in the panel body
 */

import { addText, makeButton } from "./panel.js";

/**
 * Populate `root` with an info panel body.
 *
 * @param {Element}  root     panel root <a-entity> (shell already built)
 * @param {object}   data     popup object { body }
 * @param {Function} onClose  called when CLOSE is pressed
 */
export function buildInfo(root, data, onClose) {
  console.log("buildInfo", data);
  const hasImage = !!data.image;

  // ── IMAGE (optional) ───────────────────────────────────
  if (hasImage) {
    const img = document.createElement("a-image");

    img.setAttribute("src", data.image);

    // set ONE dimension only (height or width)
    img.setAttribute("height", "0.6");
    img.setAttribute("position", "0 0.4 0.002");
    img.setAttribute("material", "transparent: true");

    img.addEventListener("materialtextureloaded", (e) => {
      const image = e.detail.texture.image;

      const ratio = image.width / image.height;

      const height = 0.6;
      const width = height * ratio;

      img.setAttribute("width", width);
    });

    root.appendChild(img);
  }

  // ── TEXT (position depends on image) ───────────────────
  const textY = hasImage ? -0.05 : 0.4;

  addText(
    root,
    data.body,
    `0 ${textY} 0.002`,
    {
      color: "#d8ecc0",
      width: "1.35",
      scale: 1,
      baseline: "top",
      wrapCount: 32
    }
  );

  // ── CLOSE BUTTON ───────────────────────────────────────
  const closeBtn = makeButton("CLOSE", "0 -0.80 0.003", 0.36, 0.13);
  closeBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    onClose();
  });

  root.appendChild(closeBtn);

  root.querySelectorAll("a-plane").forEach(p =>
    p.classList.add("vr-panel-btn")
  );
}
