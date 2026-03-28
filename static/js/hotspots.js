/**
 * Shared hotspot coordinate utilities for the 360 viewer.
 */

export function centroid(polygon) {
  const n = polygon.length;
  let sx = 0;
  let sy = 0;
  for (const [x, y] of polygon) {
    sx += x;
    sy += y;
  }
  return { x: sx / n, y: sy / n };
}

export function normalizedToYawPitch(nx, ny) {
  const yaw = nx * 360 - 180;
  const pitch = 90 - ny * 180;
  return { yaw, pitch };
}

export function yawPitchToPosition(yaw, pitch, r = 10) {
  const yRad = (yaw * Math.PI) / 180;
  const pRad = (pitch * Math.PI) / 180;
  return {
    x: r * Math.cos(pRad) * Math.sin(yRad),
    y: r * Math.sin(pRad),
    z: -r * Math.cos(pRad) * Math.cos(yRad),
  };
}

export function polygonTo3D(polygon, r = 10) {
  const c = centroid(polygon);
  const { yaw, pitch } = normalizedToYawPitch(c.x, c.y);
  const pos = yawPitchToPosition(yaw, pitch, r);
  return { ...pos, yaw, pitch };
}
