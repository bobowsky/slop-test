/**
 * modeVR.js — A-Frame VR viewer with hotspot entities.
 *
 * Strategy:
 *  1. Build an A-Frame scene programmatically and inject into #vr-container.
 *  2. For each hotspot convert polygon → centroid → yaw/pitch → 3D position.
 *  3. Place a clickable disc at that position, always facing the camera.
 *  4. On click, import the hotspot's interface.js and call mountInterface().
 *     Every hotspot — info or puzzle — has its own interface.js.
 *
 * The engine owns:
 *   - scene construction
 *   - hotspot disc geometry
 *   - panel outer shell (background, border, title bar, badge, heading)
 *   - panel lifecycle (open / close, camera attachment)
 *   - solved event dispatch
 *
 * The engine does NOT own:
 *   - interaction logic, input widgets  →  each hotspot's interface.js
 *   - any content strings               →  each hotspot's hotspot.json
 */

import { polygonTo3D, showToast } from "./hotspots.js";

// ---------------------------------------------------------------------------
// Panel lifecycle
// ---------------------------------------------------------------------------

let _currentPanel = null;

function closePanel() {
  if (_currentPanel && _currentPanel.parentNode) {
    _currentPanel.parentNode.removeChild(_currentPanel);
  }
  _currentPanel = null;
}

async function openPanel(hs, room) {
  closePanel();

  const popup = hs.popup;
  if (!popup) { showToast(hs.id); return; }

  const camera = document.querySelector("[camera]");
  if (!camera) return;

  // Build the outer shell (engine-owned) from the shared helper.
  // Dynamic import so the helper is also served as a plain ES module.
  const { buildShell } = await import(
    "/content/gadgets/panel.js"
  );
  const root = buildShell(popup);
  _currentPanel = root;

  // Every hotspot owns an interface.js that exports mountInterface().
  // Info hotspots delegate to buildInfo; puzzle hotspots to their gadget.
  // A missing or broken interface.js is a real error — not silently swallowed.
  const mod = await import(
    /* @vite-ignore */ `/content/rooms/${room}/hotspots/${hs.id}/interface.js`
  );
  mod.mountInterface(
    root,
    popup,
    () => {
      window.dispatchEvent(
        new CustomEvent("hs:solved", { detail: { id: hs.id } })
      );
      // Leave panel open so the player can read the success message.
    },
    closePanel
  );

  camera.appendChild(root);

  // Ensure all planes added by the puzzle/info builder are raycaster-visible.
  root.querySelectorAll("a-plane").forEach(p => p.classList.add("vr-panel-btn"));
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export function initVR(container, data) {
  container.innerHTML = buildSceneHTML(data);
  attachClickHandlers(container, data.hotspots, data.room);
  if (data.video) kickVideoPlayback(container);
  if (data.audio) kickAudioPlayback(container, data.audio);
}

function kickVideoPlayback(container) {
  // Video is always muted — room audio comes from the dedicated mp3 track.
  const tryPlay = () => {
    const vid = container.querySelector("#sky-asset");
    if (vid && vid.tagName === "VIDEO") {
      vid.muted = true;
      vid.play().catch(() => {});
    }
  };

  setTimeout(tryPlay, 0);

  const scene = container.querySelector("a-scene");
  if (scene) scene.addEventListener("loaded", tryPlay, { once: true });
}

let _ambientAudio = null;

function kickAudioPlayback(container, src) {
  // Reuse existing Audio element if same src (hot-reload resilience).
  if (_ambientAudio && _ambientAudio.src.endsWith(src)) {
    _ambientAudio.play().catch(() => {});
    return;
  }

  stopAmbientAudio();

  const audio = new Audio(src);
  audio.loop   = true;
  audio.volume = 0.55;
  _ambientAudio = audio;

  // Browsers require a user gesture before playing audio.
  // The user already clicked "VR View" so we should be inside a gesture stack,
  // but we also retry on the first scene interaction just in case.
  const tryPlay = () => audio.play().catch(() => {});
  tryPlay();

  const scene = container.querySelector("a-scene");
  if (scene) scene.addEventListener("loaded", tryPlay, { once: true });
}

function stopAmbientAudio() {
  if (_ambientAudio) {
    _ambientAudio.pause();
    _ambientAudio.src = "";
    _ambientAudio = null;
  }
}

export function destroyVR(container) {
  closePanel();
  stopAmbientAudio();
  container.innerHTML = "";
}

// ---------------------------------------------------------------------------
// Scene builder
// ---------------------------------------------------------------------------

function buildSceneHTML(data) {
  const hotspotEntities = data.hotspots.map(buildHotspotEntity).join("\n");

  const assetHTML = data.video
    ? `<video id="sky-asset" src="${data.video}" crossorigin="anonymous"
         autoplay loop muted playsinline preload="auto"></video>`
    : `<img id="sky-asset" src="${data.image}" crossorigin="anonymous">`;

  const skyHTML = data.video
    ? `<a-videosphere src="#sky-asset" rotation="0 -90 0"></a-videosphere>`
    : `<a-sky           src="#sky-asset" rotation="0 -90 0"></a-sky>`;

  return `
<a-scene
  id="aframe-scene"
  embedded
  style="width:100%;height:100%;"
  vr-mode-ui="enabled: true"
  loading-screen="dotsColor: #ffd700; backgroundColor: #111"
>
  <a-assets>
    ${assetHTML}
  </a-assets>

  <!-- 360 sky -->
  ${skyHTML}

  <!-- Hotspot discs -->
  <a-entity id="hotspot-group">
    ${hotspotEntities}
  </a-entity>

  <!-- Camera with mouse cursor -->
  <a-entity camera look-controls>
    <a-entity
      cursor="fuse: false; rayOrigin: mouse"
      raycaster="objects: .hotspot-hit, .vr-panel-btn; far: 30"
    ></a-entity>
  </a-entity>

  <!-- Meta Quest / WebXR hand controllers -->
  <a-entity
    id="left-controller"
    laser-controls="hand: left"
    raycaster="objects: .hotspot-hit, .vr-panel-btn; far: 30; lineColor: #ffd700; lineOpacity: 0.6"
  ></a-entity>
  <a-entity
    id="right-controller"
    laser-controls="hand: right"
    raycaster="objects: .hotspot-hit, .vr-panel-btn; far: 30; lineColor: #ffd700; lineOpacity: 0.6"
  ></a-entity>
</a-scene>`;
}

// ---------------------------------------------------------------------------
// Hotspot disc entity
// ---------------------------------------------------------------------------

function buildHotspotEntity(hs) {
  const { x, y, z, yaw, pitch } = polygonTo3D(hs.polygon, 9.5);
  const rotX =  pitch.toFixed(2);
  const rotY = (-yaw).toFixed(2);

  // Green disc for interactive gadgets, gold for display-only info.
  const INTERACTIVE_GADGETS = ["numpad", "toggle-bank"];
  const discColor = INTERACTIVE_GADGETS.includes(hs.popup?.interaction)
    ? "#7ecf3a"
    : "#ffd700";

  return `
    <a-entity
      class="hotspot-entity"
      data-hotspot-id="${hs.id}"
      position="${x.toFixed(4)} ${y.toFixed(4)} ${z.toFixed(4)}"
      rotation="${rotX} ${rotY} 0"
    >
      <!-- Glow ring — carries the raycaster class so the laser/cursor hits it -->
      <a-torus
        class="hotspot-hit"
        radius="0.45"
        radius-tubular="0.04"
        color="${discColor}"
        material="shader: flat; opacity: 0.85"
      ></a-torus>

      <!-- Inner disc — also raycaster-hittable -->
      <a-circle
        class="hotspot-hit"
        radius="0.40"
        color="${discColor}"
        material="shader: flat; opacity: 0.30; side: double"
        animation__hover="property: material.opacity; from: 0.30; to: 0.60;
          dir: alternate; dur: 900; loop: true; easing: easeInOutSine"
      ></a-circle>

      <!-- Label -->
      <a-text
        value="${escapeAttr(hs.popup?.title ?? hs.id)}"
        align="center"
        color="#ffffff"
        width="4"
        position="0 -0.60 0"
        shader="msdf"
      ></a-text>
    </a-entity>`;
}

// ---------------------------------------------------------------------------
// Interaction
// ---------------------------------------------------------------------------

function attachClickHandlers(container, hotspots, room) {
  const map = Object.fromEntries(hotspots.map(hs => [hs.id, hs]));

  // A-Frame's raycaster fires a synthetic "click" directly on the geometry
  // element (torus / circle).  We listen on their parent entity which carries
  // data-hotspot-id, using event bubbling within the A-Frame element tree.
  //
  // We must wait for the scene to finish loading before querying entities.
  const scene = container.querySelector("a-scene");

  function wireEntities() {
    container.querySelectorAll("[data-hotspot-id]").forEach(entity => {
      const hs = map[entity.dataset.hotspotId];
      if (!hs) return;

      // Synthetic A-Frame click bubbles from child geometry → parent entity
      entity.addEventListener("click", (e) => {
        e.stopPropagation();
        openPanel(hs, room);
      });
    });
  }

  if (!scene) return;

  if (scene.hasLoaded) {
    // Scene already loaded (e.g. hot-reload) — wire immediately
    wireEntities();
  } else {
    scene.addEventListener("loaded", wireEntities, { once: true });
  }
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function escapeAttr(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;");
}
