/**
 * app.js — entry point.
 * Fetches scene JSON, wires up mode switching between 2D canvas and VR.
 */

import { init2D, destroy2D } from "./mode2d.js";
import { initVR, destroyVR } from "./modeVR.js";

// ---------------------------------------------------------------------------
// State
// ---------------------------------------------------------------------------

let currentMode = null;  // "2d" | "vr"
let sceneData   = null;

// ---------------------------------------------------------------------------
// Bootstrap
// ---------------------------------------------------------------------------

async function main() {
  sceneData = await fetchScene();

  const toggle2D = document.getElementById("btn-2d");
  const toggleVR = document.getElementById("btn-vr");

  toggle2D.addEventListener("click", () => setMode("2d"));
  toggleVR.addEventListener("click", () => setMode("vr"));

  // Start in 2D by default
  setMode("2d");
}

async function fetchScene() {
  const res = await fetch("/api/scene");
  if (!res.ok) throw new Error("Failed to load scene data");
  return res.json();
}

// ---------------------------------------------------------------------------
// Mode switching
// ---------------------------------------------------------------------------

function setMode(mode) {
  if (mode === currentMode) return;
  currentMode = mode;

  const container2D = document.getElementById("container-2d");
  const containerVR = document.getElementById("container-vr");
  const canvas      = document.getElementById("canvas-2d");
  const btn2D       = document.getElementById("btn-2d");
  const btnVR       = document.getElementById("btn-vr");

  if (mode === "2d") {
    containerVR.classList.add("hidden");
    destroyVR(containerVR);

    container2D.classList.remove("hidden");
    init2D(canvas, sceneData);

    btn2D.classList.add("active");
    btnVR.classList.remove("active");
  } else {
    container2D.classList.add("hidden");
    destroy2D();

    containerVR.classList.remove("hidden");
    initVR(containerVR, sceneData);

    btnVR.classList.add("active");
    btn2D.classList.remove("active");
  }
}

// ---------------------------------------------------------------------------
// Run
// ---------------------------------------------------------------------------

document.addEventListener("DOMContentLoaded", main);
