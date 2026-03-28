import { polygonTo3D } from "./hotspots.js";

const sceneContainer = document.getElementById("scene-container");
const messageEl = document.getElementById("viewer-message");
const closeBtn = document.getElementById("close-btn");

let currentPanel = null;
let ambientAudio = null;

if (closeBtn) {
  closeBtn.addEventListener("click", () => window.close());
}

bootstrap().catch((error) => {
  showMessage(error?.message || "Failed to initialize viewer.");
});

async function bootstrap() {
  const roomId = new URLSearchParams(window.location.search).get("room");
  if (!roomId) {
    showMessage("Missing room id. Open this page from the results dashboard.");
    return;
  }

  const response = await fetch(`/api/scene/${encodeURIComponent(roomId)}`);
  if (!response.ok) {
    throw new Error(`Unable to load scene for ${roomId} (${response.status}).`);
  }
  const scene = await response.json();

  if (!scene?.image && !scene?.video) {
    throw new Error("Scene has no panorama/video asset.");
  }

  sceneContainer.innerHTML = buildSceneHTML(scene);
  wireHotspotClicks(scene.hotspots || [], roomId);

  if (scene.video) kickVideoPlayback();
  if (scene.audio) kickAudioPlayback(scene.audio);
}

function buildSceneHTML(scene) {
  const hotspotEntities = (scene.hotspots || []).map(buildHotspotEntity).join("\n");
  const assetHTML = scene.video
    ? `<video id="sky-asset" src="${scene.video}" crossorigin="anonymous" autoplay loop muted playsinline preload="auto"></video>`
    : `<img id="sky-asset" src="${scene.image}" crossorigin="anonymous">`;
  const skyHTML = scene.video
    ? `<a-videosphere src="#sky-asset" rotation="0 -90 0"></a-videosphere>`
    : `<a-sky src="#sky-asset" rotation="0 -90 0"></a-sky>`;

  return `
<a-scene
  id="aframe-scene"
  embedded
  style="width:100%;height:100%;"
  vr-mode-ui="enabled: false"
  loading-screen="dotsColor: #a7b6ff; backgroundColor: #05060a"
>
  <a-assets>
    ${assetHTML}
  </a-assets>

  ${skyHTML}

  <a-entity id="hotspot-group">
    ${hotspotEntities}
  </a-entity>

  <a-entity camera look-controls>
    <a-entity
      cursor="fuse: false; rayOrigin: mouse"
      raycaster="objects: .hotspot-hit, .vr-panel-btn; far: 30"
    ></a-entity>
  </a-entity>
</a-scene>`;
}

function buildHotspotEntity(hotspot) {
  if (!Array.isArray(hotspot?.polygon) || hotspot.polygon.length < 3) {
    return "";
  }
  const popup = hotspot.popup || {};
  const title = escapeAttr(popup.title || hotspot.id || "Hotspot");
  const interaction = String(popup.interaction || "info").toLowerCase();
  const color = interaction === "numpad" || interaction === "toggle-bank" ? "#7ecf3a" : "#a7b6ff";
  const { x, y, z, yaw, pitch } = polygonTo3D(hotspot.polygon, 9.5);

  return `
  <a-entity
    class="hotspot-entity"
    data-hotspot-id="${escapeAttr(hotspot.id || "")}"
    position="${x.toFixed(4)} ${y.toFixed(4)} ${z.toFixed(4)}"
    rotation="${pitch.toFixed(2)} ${(-yaw).toFixed(2)} 0"
  >
    <a-torus
      class="hotspot-hit"
      radius="0.45"
      radius-tubular="0.04"
      color="${color}"
      material="shader: flat; opacity: 0.85"
    ></a-torus>
    <a-circle
      class="hotspot-hit"
      radius="0.40"
      color="${color}"
      material="shader: flat; opacity: 0.30; side: double"
      animation__hover="property: material.opacity; from: 0.30; to: 0.60; dir: alternate; dur: 900; loop: true; easing: easeInOutSine"
    ></a-circle>
    <a-text
      value="${title}"
      align="center"
      color="#ffffff"
      width="4"
      position="0 -0.60 0"
      shader="msdf"
    ></a-text>
  </a-entity>`;
}

function wireHotspotClicks(hotspots, roomId) {
  const byId = Object.fromEntries(hotspots.map((hotspot) => [hotspot.id, hotspot]));
  const scene = sceneContainer.querySelector("a-scene");
  if (!scene) return;

  const bind = () => {
    sceneContainer.querySelectorAll("[data-hotspot-id]").forEach((entity) => {
      const hotspot = byId[entity.dataset.hotspotId];
      if (!hotspot) return;
      entity.addEventListener("click", (event) => {
        event.stopPropagation();
        openPanel(hotspot, roomId).catch((error) => {
          showMessage(error?.message || "Unable to open hotspot interaction.");
        });
      });
    });
  };

  if (scene.hasLoaded) bind();
  else scene.addEventListener("loaded", bind, { once: true });
}

async function openPanel(hotspot, roomId) {
  closePanel();
  const popup = hotspot?.popup;
  if (!popup) return;

  const camera = document.querySelector("[camera]");
  if (!camera) return;

  const { buildShell } = await import("/content/gadgets/panel.js");
  const root = buildShell(popup);
  currentPanel = root;

  const moduleUrl = `/content/rooms/${encodeURIComponent(roomId)}/hotspots/${encodeURIComponent(
    hotspot.id
  )}/interface.js`;
  const interaction = await import(/* @vite-ignore */ moduleUrl);
  interaction.mountInterface(
    root,
    popup,
    () => {
      window.dispatchEvent(new CustomEvent("hs:solved", { detail: { id: hotspot.id } }));
    },
    closePanel
  );

  camera.appendChild(root);
  root.querySelectorAll("a-plane").forEach((plane) => plane.classList.add("vr-panel-btn"));
}

function closePanel() {
  if (currentPanel?.parentNode) {
    currentPanel.parentNode.removeChild(currentPanel);
  }
  currentPanel = null;
}

function kickVideoPlayback() {
  const play = () => {
    const video = sceneContainer.querySelector("#sky-asset");
    if (video && video.tagName === "VIDEO") {
      video.muted = true;
      video.play().catch(() => {});
    }
  };
  setTimeout(play, 0);
  const scene = sceneContainer.querySelector("a-scene");
  if (scene) scene.addEventListener("loaded", play, { once: true });
}

function kickAudioPlayback(src) {
  if (ambientAudio && ambientAudio.src.endsWith(src)) {
    ambientAudio.play().catch(() => {});
    return;
  }
  stopAmbientAudio();
  ambientAudio = new Audio(src);
  ambientAudio.loop = true;
  ambientAudio.volume = 0.55;
  ambientAudio.play().catch(() => {});
}

function stopAmbientAudio() {
  if (!ambientAudio) return;
  ambientAudio.pause();
  ambientAudio.src = "";
  ambientAudio = null;
}

function showMessage(message) {
  if (!messageEl) return;
  messageEl.textContent = message;
  messageEl.style.display = "flex";
}

function escapeAttr(text) {
  return String(text).replace(/&/g, "&amp;").replace(/"/g, "&quot;");
}

window.addEventListener("beforeunload", () => {
  closePanel();
  stopAmbientAudio();
});
