(function () {
  "use strict";

  const API_BASE = window.location.origin;
  const SAMPLE_IMAGE_SOURCES = [
    "/static/assets/sample_room.jpg",
    "https://lh3.googleusercontent.com/aida-public/AB6AXuCtXTI8zRH4dHXmBBR5L15mCXsM2TjujloGh61bPxDXVyLHKDMoDaeSKCATEL4geSRV9qjUZ_RcuPMo2PN5CTVXyDEBqXd4bBOf2U7D41Heo8jqCkkE9yU2kr0mygGBx9cyzd2BqMUfaPLk7GQQhMet7K-yYBzUbkg18UvQB9R3-Tg5IBSjiQnVnDTZMASVzzMwHMP14JM0jieGYxE6DtPtk-QvB1HXAPRsG0K6gZPGsbiNt3ZgHHKo7xIqV-_HlPUMm2WJ5qoe-cs",
  ];
  const ERROR_CONTEXT_KEY = "room2learn_error_context";
  const PENDING_CONFIG_KEY = "room2learn_pending_config";
  const TRUE_VALUES = new Set(["1", "true", "yes", "on"]);

  const uploadZone = document.getElementById("upload-zone");
  const fileInput = document.getElementById("file-input");
  const selectFileBtn = document.getElementById("select-file-btn");
  const previewContainer = document.getElementById("preview-container");
  const uploadPlaceholder = document.getElementById("upload-placeholder");
  const imagePreview = document.getElementById("image-preview");
  const fileNameDisplay = document.getElementById("file-name-display");
  const themeSelect = document.getElementById("theme-select");
  const modeSelect = document.getElementById("mode-select");
  const difficultySelect = document.getElementById("difficulty-select");
  const generateBtn = document.getElementById("generate-btn");
  const sampleBtn = document.getElementById("sample-btn");
  const trySampleHeader = document.getElementById("try-sample-header");
  const processingOverlay = document.getElementById("processing-overlay");

  const stepEls = [
    document.getElementById("step-1"),
    document.getElementById("step-2"),
    document.getElementById("step-3"),
    document.getElementById("step-4"),
  ];

  let selectedFile = null;
  let previewObjectUrl = null;

  restorePendingConfig();
  setLoadingState(false);
  maybeAutoStartSample();

  // --- File Selection ---

  selectFileBtn.addEventListener("click", (e) => {
    e.preventDefault();
    fileInput.click();
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0]);
    }
  });

  // --- Drag and Drop ---

  uploadZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadZone.classList.add("ring-2", "ring-primary/40");
  });

  uploadZone.addEventListener("dragleave", () => {
    uploadZone.classList.remove("ring-2", "ring-primary/40");
  });

  uploadZone.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadZone.classList.remove("ring-2", "ring-primary/40");
    if (e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  function handleFileSelected(file) {
    const allowed = ["image/jpeg", "image/png", "image/webp"];
    if (!allowed.includes(file.type)) {
      goToErrorPage("unsupported_input", "Unsupported file type. Please upload a JPG, PNG, or WebP image.", {
        retryable: true,
      });
      return;
    }
    selectedFile = file;
    if (previewObjectUrl) URL.revokeObjectURL(previewObjectUrl);
    previewObjectUrl = URL.createObjectURL(file);
    imagePreview.src = previewObjectUrl;
    imagePreview.classList.remove("hidden");
    uploadPlaceholder.classList.add("hidden");
    previewContainer.classList.remove("hidden");
    setLoadingState(false);
    if (fileNameDisplay) {
      fileNameDisplay.textContent = file.name;
      fileNameDisplay.classList.remove("hidden");
    }
  }

  // --- Generate Experience ---

  generateBtn.addEventListener("click", async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      nudgeUploadZone();
      return;
    }
    await startGeneration(selectedFile);
  });

  // --- Sample Scene ---

  async function useSample(options) {
    const opts = options || { autoStart: true };
    try {
      const file = await loadSampleFile();
      handleFileSelected(file);
      if (opts.autoStart) {
        await startGeneration(file);
      }
    } catch (err) {
      goToErrorPage(
        "sample_unavailable",
        "Could not load a sample scene right now. Please upload your own image.",
        { retryable: true }
      );
    }
  }

  sampleBtn.addEventListener("click", (e) => {
    e.preventDefault();
    useSample();
  });

  if (trySampleHeader) {
    trySampleHeader.addEventListener("click", (e) => {
      e.preventDefault();
      useSample();
    });
  }

  // --- Generation Flow ---

  async function startGeneration(file) {
    savePendingConfig();
    setLoadingState(true);

    const formData = new FormData();
    formData.append("image", file);
    formData.append("theme", themeSelect.value);
    formData.append("mode", modeSelect.value);
    formData.append("difficulty", difficultySelect.value);

    try {
      const resp = await fetch(`${API_BASE}/api/generate`, {
        method: "POST",
        body: formData,
      });

      if (!resp.ok) {
        const err = await resp.json().catch(() => ({}));
        throw new Error(err.detail || `Server error: ${resp.status}`);
      }

      const { job_id, original_image_url } = await resp.json();
      if (!job_id) {
        throw new Error("Invalid generation response: missing job id.");
      }
      sessionStorage.setItem("original_image_url", original_image_url);

      showProcessingOverlay();
      connectSSE(job_id);
    } catch (err) {
      hideOverlay();
      goToErrorPage("generation_failed", err.message || "Generation failed. Please try again.", {
        retryable: true,
      });
    }
  }

  // --- Processing Overlay ---

  function showProcessingOverlay() {
    processingOverlay.classList.remove("hidden");
    resetSteps();
  }

  function resetSteps() {
    stepEls.forEach((el) => {
      if (!el) return;
      el.dataset.status = "pending";
      const icon = el.querySelector(".step-icon");
      const label = el.querySelector(".step-label");
      icon.innerHTML = "";
      icon.className =
        "step-icon w-6 h-6 rounded-full bg-surface-container-high";
      label.className = "step-label font-inter text-on-surface-variant text-sm";
      el.className = "flex items-center gap-4 opacity-40";
    });
  }

  function backendStepToUiStep(backendStep) {
    if (backendStep <= 2) return 1;
    if (backendStep <= 5) return 2;
    if (backendStep <= 8) return 3;
    return 4;
  }

  function updateStep(rawStepNum) {
    const stepNum = backendStepToUiStep(rawStepNum);
    stepEls.forEach((el, i) => {
      if (!el) return;
      const icon = el.querySelector(".step-icon");
      const label = el.querySelector(".step-label");
      const idx = i + 1;

      if (idx < stepNum) {
        // Completed
        el.className = "flex items-center gap-4";
        el.dataset.status = "done";
        icon.className =
          "step-icon w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center";
        icon.innerHTML =
          '<span class="material-symbols-outlined text-primary text-sm font-bold">check</span>';
        label.className = "step-label font-inter text-on-surface/90 font-medium";
      } else if (idx === stepNum) {
        // Active
        el.className = "flex items-center gap-4";
        el.dataset.status = "active";
        icon.className =
          "step-icon w-6 h-6 rounded-full bg-indigo-100 flex items-center justify-center relative";
        icon.innerHTML =
          '<div class="absolute inset-0 rounded-full border-2 border-indigo-500 border-t-transparent animate-spin"></div>';
        label.className = "step-label font-inter text-indigo-600 font-semibold";
      } else {
        // Pending
        el.className = "flex items-center gap-4 opacity-40";
        el.dataset.status = "pending";
        icon.className =
          "step-icon w-6 h-6 rounded-full bg-surface-container-high";
        icon.innerHTML = "";
        label.className = "step-label font-inter text-on-surface-variant text-sm";
      }
    });
  }

  // --- SSE Connection ---

  function connectSSE(jobId) {
    const source = new EventSource(`${API_BASE}/api/generate/${jobId}/stream`);

    source.addEventListener("progress", (e) => {
      try {
        const data = JSON.parse(e.data);
        updateStep(data.step);
      } catch {
        // ignore malformed events
      }
    });

    source.addEventListener("complete", (e) => {
      source.close();
      try {
        const scenario = JSON.parse(e.data);
        sessionStorage.setItem("scenario", JSON.stringify(scenario));
        window.location.href = "/static/results.html";
      } catch {
        hideOverlay();
        goToErrorPage(
          "malformed_response",
          "Received malformed scenario data. Please regenerate the experience.",
          { retryable: true }
        );
      }
    });

    source.addEventListener("failed", (e) => {
      source.close();
      hideOverlay();
      goToErrorPage(
        "pipeline_failed",
        e?.data || "Room generation pipeline failed. Please try again.",
        { retryable: true }
      );
    });

    source.addEventListener("error", () => {
      source.close();
      hideOverlay();
      goToErrorPage(
        "stream_disconnected",
        "Connection lost during processing. Please try again.",
        { retryable: true }
      );
    });
  }

  function hideOverlay() {
    processingOverlay.classList.add("hidden");
    setLoadingState(false);
  }

  function setLoadingState(isLoading) {
    const hasFile = Boolean(selectedFile);
    if (generateBtn) {
      generateBtn.disabled = isLoading || !hasFile;
      generateBtn.textContent = isLoading ? "Processing..." : "Generate Learning Portal";
      generateBtn.classList.toggle("opacity-60", generateBtn.disabled);
      generateBtn.classList.toggle("cursor-not-allowed", generateBtn.disabled);
    }
    if (sampleBtn) {
      sampleBtn.disabled = isLoading;
      sampleBtn.classList.toggle("opacity-60", isLoading);
      sampleBtn.classList.toggle("cursor-not-allowed", isLoading);
    }
    if (trySampleHeader) {
      trySampleHeader.disabled = isLoading;
      trySampleHeader.classList.toggle("opacity-60", isLoading);
      trySampleHeader.classList.toggle("cursor-not-allowed", isLoading);
    }
  }

  async function loadSampleFile() {
    for (const sourceUrl of SAMPLE_IMAGE_SOURCES) {
      try {
        const resp = await fetch(sourceUrl, { cache: "no-store" });
        if (!resp.ok) continue;
        const blob = await resp.blob();
        if (!blob.type.startsWith("image/")) continue;
        return new File([blob], "sample_room.jpg", {
          type: blob.type || "image/jpeg",
        });
      } catch {
        // Try next source.
      }
    }
    throw new Error("No sample source available");
  }

  function nudgeUploadZone() {
    if (!uploadZone) return;
    uploadZone.classList.add("ring-2", "ring-error/40");
    setTimeout(() => {
      uploadZone.classList.remove("ring-2", "ring-error/40");
    }, 1200);
  }

  function goToErrorPage(type, message, options) {
    const context = {
      type: type || "unknown_error",
      message: message || "An unexpected error occurred.",
      retryable: options?.retryable !== false,
      timestamp: Date.now(),
      config: {
        theme: themeSelect ? themeSelect.value : "",
        mode: modeSelect ? modeSelect.value : "",
        difficulty: difficultySelect ? difficultySelect.value : "",
      },
    };
    sessionStorage.setItem(ERROR_CONTEXT_KEY, JSON.stringify(context));
    const params = new URLSearchParams();
    params.set("type", context.type);
    if (context.retryable) params.set("retryable", "1");
    window.location.href = `/static/error.html?${params.toString()}`;
  }

  function savePendingConfig() {
    const config = {
      theme: themeSelect ? themeSelect.value : "",
      mode: modeSelect ? modeSelect.value : "",
      difficulty: difficultySelect ? difficultySelect.value : "",
    };
    sessionStorage.setItem(PENDING_CONFIG_KEY, JSON.stringify(config));
  }

  function restorePendingConfig() {
    const raw = sessionStorage.getItem(PENDING_CONFIG_KEY);
    if (!raw) return;
    try {
      const config = JSON.parse(raw);
      setSelectValue(themeSelect, config.theme);
      setSelectValue(modeSelect, config.mode);
      setSelectValue(difficultySelect, config.difficulty);
    } catch {
      // Ignore invalid stored config.
    }
  }

  function setSelectValue(selectEl, value) {
    if (!selectEl || !value) return;
    const hasOption = Array.from(selectEl.options).some((opt) => opt.value === value);
    if (hasOption) {
      selectEl.value = value;
    }
  }

  function maybeAutoStartSample() {
    const params = new URLSearchParams(window.location.search);
    const sampleParam = params.get("sample");
    if (!sampleParam) return;
    if (!TRUE_VALUES.has(sampleParam.toLowerCase())) return;
    useSample({ autoStart: true });
  }
})();
