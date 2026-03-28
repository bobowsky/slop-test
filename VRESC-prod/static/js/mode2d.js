/**
 * mode2d.js — 2D canvas viewer with polygon hotspots.
 */

import { pointInPolygon, showToast } from "./hotspots.js";

let canvas, ctx, sceneData;
let mediaEl = null;   // HTMLVideoElement | HTMLImageElement
let rafId   = null;
let hoveredHotspot = null;

const FILL_NORMAL   = "rgba(255, 200, 0, 0.20)";
const FILL_HOVER    = "rgba(255, 200, 0, 0.45)";
const STROKE_NORMAL = "rgba(255, 200, 0, 0.80)";
const STROKE_HOVER  = "rgba(255, 255, 100, 1.00)";
const LABEL_COLOR   = "#fff";
const LINE_WIDTH    = 2;

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export function init2D(canvasEl, data) {
  canvas = canvasEl;
  ctx = canvas.getContext("2d");
  sceneData = data;

  if (data.video) {
    const vid = document.createElement("video");
    vid.src = data.video;
    vid.loop = true;
    vid.muted = true;
    vid.playsInline = true;
    vid.addEventListener("loadedmetadata", () => {
      mediaEl = vid;
      resizeCanvas();
      vid.play();
      startLoop();
    });
  } else if (data.image) {
    const img = new Image();
    img.onload = () => {
      mediaEl = img;
      resizeCanvas();
      render();
    };
    img.src = data.image;
  }

  canvas.addEventListener("mousemove", onMouseMove);
  canvas.addEventListener("click", onClick);
  window.addEventListener("resize", onResize);
}

export function destroy2D() {
  if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null; }
  if (mediaEl instanceof HTMLVideoElement) { mediaEl.pause(); mediaEl.src = ""; }
  mediaEl = null;
  if (canvas) {
    canvas.removeEventListener("mousemove", onMouseMove);
    canvas.removeEventListener("click", onClick);
  }
  window.removeEventListener("resize", onResize);
}

function onResize() { resizeCanvas(); }

function startLoop() {
  function tick() {
    render();
    rafId = requestAnimationFrame(tick);
  }
  rafId = requestAnimationFrame(tick);
}

// ---------------------------------------------------------------------------
// Internal
// ---------------------------------------------------------------------------

function mediaWidth()  {
  return mediaEl instanceof HTMLVideoElement ? mediaEl.videoWidth  : mediaEl.naturalWidth;
}
function mediaHeight() {
  return mediaEl instanceof HTMLVideoElement ? mediaEl.videoHeight : mediaEl.naturalHeight;
}

function resizeCanvas() {
  if (!mediaEl) return;
  const container = canvas.parentElement;
  const w = container.clientWidth;
  const h = Math.round(w * (mediaHeight() / mediaWidth()));
  canvas.width = w;
  canvas.height = h;
  canvas.style.width = w + "px";
  canvas.style.height = h + "px";
}

function render() {
  if (!mediaEl || !canvas.width) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(mediaEl, 0, 0, canvas.width, canvas.height);
  drawHotspots();
}

function drawHotspots() {
  for (const hs of sceneData.hotspots) {
    const isHovered = hs === hoveredHotspot;
    drawPolygon(hs.polygon, isHovered);
    drawLabel(hs.polygon, hs.popup?.title, isHovered);
  }
}

function drawPolygon(polygon, hovered) {
  const pts = toPixels(polygon);
  ctx.beginPath();
  ctx.moveTo(pts[0].x, pts[0].y);
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i].x, pts[i].y);
  ctx.closePath();

  ctx.fillStyle   = hovered ? FILL_HOVER    : FILL_NORMAL;
  ctx.strokeStyle = hovered ? STROKE_HOVER  : STROKE_NORMAL;
  ctx.lineWidth   = LINE_WIDTH;

  ctx.fill();
  ctx.stroke();
}

function drawLabel(polygon, label, hovered) {
  if (!label) return;
  const pts = toPixels(polygon);
  const cx = pts.reduce((s, p) => s + p.x, 0) / pts.length;
  const cy = pts.reduce((s, p) => s + p.y, 0) / pts.length;

  ctx.save();
  ctx.font      = `bold ${hovered ? 14 : 12}px sans-serif`;
  ctx.fillStyle = LABEL_COLOR;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.shadowColor  = "rgba(0,0,0,0.8)";
  ctx.shadowBlur   = 4;
  ctx.fillText(label, cx, cy);
  ctx.restore();
}

// ---------------------------------------------------------------------------
// Coordinate helpers
// ---------------------------------------------------------------------------

function toPixels(polygon) {
  return polygon.map(([nx, ny]) => ({
    x: nx * canvas.width,
    y: ny * canvas.height,
  }));
}

function toNormalized(clientX, clientY) {
  const rect = canvas.getBoundingClientRect();
  return {
    nx: (clientX - rect.left) / rect.width,
    ny: (clientY - rect.top)  / rect.height,
  };
}

// ---------------------------------------------------------------------------
// Event handlers
// ---------------------------------------------------------------------------

function findHotspot(nx, ny) {
  for (const hs of sceneData.hotspots) {
    if (pointInPolygon(nx, ny, hs.polygon)) return hs;
  }
  return null;
}

function onMouseMove(e) {
  const { nx, ny } = toNormalized(e.clientX, e.clientY);
  const hit = findHotspot(nx, ny);
  if (hit !== hoveredHotspot) {
    hoveredHotspot = hit;
    canvas.style.cursor = hit ? "pointer" : "default";
    render();
  }
}

function onClick(e) {
  const { nx, ny } = toNormalized(e.clientX, e.clientY);
  const hit = findHotspot(nx, ny);
  if (hit) showToast(hit.popup?.title ?? hit.id);
}
