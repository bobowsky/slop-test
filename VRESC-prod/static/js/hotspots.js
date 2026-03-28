/**
 * hotspots.js — shared logic for 2D and VR hotspot handling.
 *
 * Coordinate convention:
 *   Normalized (nx, ny) where nx ∈ [0,1] maps to yaw ∈ [-180°, 180°]
 *   and ny ∈ [0,1] maps to pitch ∈ [90°, -90°] (top→bottom).
 */

// ---------------------------------------------------------------------------
// Polygon math
// ---------------------------------------------------------------------------

/**
 * Compute the centroid of a polygon given as [[x,y], ...].
 * Uses the arithmetic mean of vertices.
 * @param {number[][]} polygon
 * @returns {{ x: number, y: number }}
 */
export function centroid(polygon) {
  const n = polygon.length;
  let sx = 0, sy = 0;
  for (const [x, y] of polygon) { sx += x; sy += y; }
  return { x: sx / n, y: sy / n };
}

/**
 * Ray-casting point-in-polygon test.
 * @param {number} px  - normalized x
 * @param {number} py  - normalized y
 * @param {number[][]} polygon
 * @returns {boolean}
 */
export function pointInPolygon(px, py, polygon) {
  let inside = false;
  const n = polygon.length;
  for (let i = 0, j = n - 1; i < n; j = i++) {
    const [xi, yi] = polygon[i];
    const [xj, yj] = polygon[j];
    const intersects =
      yi > py !== yj > py &&
      px < ((xj - xi) * (py - yi)) / (yj - yi) + xi;
    if (intersects) inside = !inside;
  }
  return inside;
}

// ---------------------------------------------------------------------------
// Equirectangular ↔ 3D conversions
// ---------------------------------------------------------------------------

/**
 * Convert normalized (nx, ny) to yaw/pitch in degrees.
 * nx=0 → yaw=-180°, nx=1 → yaw=+180°
 * ny=0 → pitch=+90° (top), ny=1 → pitch=-90° (bottom)
 * @param {number} nx
 * @param {number} ny
 * @returns {{ yaw: number, pitch: number }}
 */
export function normalizedToYawPitch(nx, ny) {
  const yaw = (nx * 360) - 180;
  const pitch = 90 - ny * 180;
  return { yaw, pitch };
}

/**
 * Convert yaw/pitch (degrees) to a 3D point on a unit sphere.
 * A-Frame coordinate system: Y-up, camera looks toward -Z at yaw=0.
 * @param {number} yaw   - degrees, -180..180
 * @param {number} pitch - degrees, -90..90
 * @param {number} [r=10] - sphere radius
 * @returns {{ x: number, y: number, z: number }}
 */
export function yawPitchToPosition(yaw, pitch, r = 10) {
  const yRad = (yaw * Math.PI) / 180;
  const pRad = (pitch * Math.PI) / 180;
  return {
    x: r * Math.cos(pRad) * Math.sin(yRad),
    y: r * Math.sin(pRad),
    z: -r * Math.cos(pRad) * Math.cos(yRad),
  };
}

/**
 * Full pipeline: polygon → centroid → yaw/pitch → 3D position.
 * @param {number[][]} polygon
 * @param {number} [r=10]
 * @returns {{ x: number, y: number, z: number, yaw: number, pitch: number }}
 */
export function polygonTo3D(polygon, r = 10) {
  const c = centroid(polygon);
  const { yaw, pitch } = normalizedToYawPitch(c.x, c.y);
  const pos = yawPitchToPosition(yaw, pitch, r);
  return { ...pos, yaw, pitch };
}

// ---------------------------------------------------------------------------
// Toast notification
// ---------------------------------------------------------------------------

let toastTimer = null;

/**
 * Show a brief toast message in the UI.
 * @param {string} message
 */
export function showToast(message) {
  let toast = document.getElementById("hs-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "hs-toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.classList.add("visible");

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("visible"), 3500);
}
