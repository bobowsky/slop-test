(function () {
  "use strict";

  const ERROR_CONTEXT_KEY = "room2learn_error_context";
  const PENDING_CONFIG_KEY = "room2learn_pending_config";

  const uploadCard = document.getElementById("upload-error-card");
  const generationCard = document.getElementById("generation-error-card");
  const emptyCard = document.getElementById("empty-state-card");
  const uploadMessage = document.getElementById("upload-error-message");
  const generationMessage = document.getElementById("generation-error-message");

  const retryUploadBtn = document.getElementById("retry-upload-btn");
  const trySampleBtn = document.getElementById("try-sample-btn");
  const headerTrySampleBtn = document.getElementById("header-try-sample-btn");
  const viewDocsBtn = document.getElementById("view-docs-btn");
  const browseGalleryBtn = document.getElementById("browse-gallery-btn");

  const context = getErrorContext();

  renderContext(context);
  wireActions(context);

  function getErrorContext() {
    const params = new URLSearchParams(window.location.search);
    const typeFromQuery = params.get("type");

    try {
      const raw = sessionStorage.getItem(ERROR_CONTEXT_KEY);
      if (raw) {
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === "object") {
          return parsed;
        }
      }
    } catch {
      // Ignore invalid stored context.
    }

    if (typeFromQuery) {
      return {
        type: typeFromQuery,
        message: "The operation could not be completed. Please try again.",
        retryable: true,
      };
    }

    return null;
  }

  function renderContext(errorContext) {
    if (!errorContext) {
      setVisibility({ upload: false, generation: false, empty: true });
      return;
    }

    const type = String(errorContext.type || "").toLowerCase();
    const message = String(errorContext.message || "");
    const uploadTypes = new Set(["unsupported_input", "upload_failed"]);
    const generationTypes = new Set([
      "generation_failed",
      "stream_disconnected",
      "malformed_response",
      "sample_unavailable",
      "unknown_error",
    ]);

    if (uploadTypes.has(type)) {
      setVisibility({ upload: true, generation: false, empty: false });
      if (uploadMessage && message) uploadMessage.textContent = message;
      return;
    }

    if (generationTypes.has(type) || type) {
      setVisibility({ upload: false, generation: true, empty: false });
      if (generationMessage && message) generationMessage.textContent = message;
      return;
    }

    setVisibility({ upload: false, generation: false, empty: true });
  }

  function setVisibility(state) {
    if (uploadCard) uploadCard.classList.toggle("hidden", !state.upload);
    if (generationCard) generationCard.classList.toggle("hidden", !state.generation);
    if (emptyCard) emptyCard.classList.toggle("hidden", !state.empty);
  }

  function wireActions(errorContext) {
    if (retryUploadBtn) {
      retryUploadBtn.addEventListener("click", () => {
        if (errorContext && errorContext.config) {
          sessionStorage.setItem(PENDING_CONFIG_KEY, JSON.stringify(errorContext.config));
        }
        window.location.href = "/static/index.html";
      });
    }

    if (trySampleBtn) {
      trySampleBtn.addEventListener("click", () => {
        window.location.href = "/static/index.html?sample=1";
      });
    }

    if (headerTrySampleBtn) {
      headerTrySampleBtn.addEventListener("click", () => {
        window.location.href = "/static/index.html?sample=1";
      });
    }

    if (viewDocsBtn) {
      viewDocsBtn.addEventListener("click", () => {
        window.location.href = "/static/DESIGN.md";
      });
    }

    if (browseGalleryBtn) {
      browseGalleryBtn.addEventListener("click", () => {
        window.location.href = "/static/index.html#gallery";
      });
    }
  }
})();
