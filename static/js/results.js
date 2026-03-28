(function () {
  "use strict";

  const API_BASE = window.location.origin;

  const scenario = JSON.parse(sessionStorage.getItem("scenario") || "null");
  if (!scenario) {
    window.location.href = "/static/index.html";
    return;
  }
  function normalizeCategory(value) {
    const raw = String(value || "").trim();
    if (!raw) return "The Archive";
    if (raw === "The Archive" || raw === "The Cold Case") return raw;
    return "The Archive";
  }
  const puzzleSteps = Array.isArray(scenario.puzzles) ? scenario.puzzles : [];
  const totalPuzzleSteps = puzzleSteps.length;
  const DEBUG_TRUE_VALUES = new Set(["1", "true", "yes", "on"]);
  const STOP_WORDS = new Set([
    "the",
    "a",
    "an",
    "is",
    "are",
    "was",
    "were",
    "to",
    "in",
    "of",
    "for",
    "and",
    "or",
    "but",
    "it",
    "its",
    "that",
    "this",
    "from",
  ]);
  const playState = {
    currentStep: 1,
    solvedSteps: [],
    isEscaped: false,
    didShowEscapeModal: false,
  };
  const vapiState = {
    client: null,
    lastPublicKey: "",
    callActive: false,
    callConnecting: false,
    sdkConstructor: null,
  };

  // --- Populate Overview ---

  const titleEl = document.getElementById("result-title");
  const storyEl = document.getElementById("result-story");
  const themeTag = document.getElementById("tag-theme");

  if (titleEl) titleEl.textContent = scenario.title;
  if (storyEl) storyEl.textContent = scenario.story;
  const normalizedCategory = normalizeCategory(scenario.theme);
  if (themeTag) themeTag.textContent = `CATEGORY: ${normalizedCategory.toUpperCase()}`;

  const resultsTrySampleBtn = document.getElementById("results-try-sample-btn");
  const resultsAgentBtn = document.getElementById("results-agent-btn");
  const voiceHostCard = document.getElementById("voice-host-card");

  if (resultsTrySampleBtn) {
    resultsTrySampleBtn.addEventListener("click", () => {
      window.location.href = "/static/index.html?sample=1";
    });
  }

  if (resultsAgentBtn) {
    resultsAgentBtn.addEventListener("click", () => {
      if (voiceHostCard) {
        voiceHostCard.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    });
  }

  // --- Images ---

  const originalImg = document.getElementById("original-image");
  const panoramaCard = document.getElementById("panorama-preview-card");
  const panoramaThumbnail = document.getElementById("panorama-thumbnail");
  const panoramaOpenBtn = document.getElementById("panorama-open-btn");
  const panoramaStatus = document.getElementById("panorama-status");

  if (originalImg && scenario.original_image_url) {
    originalImg.src = scenario.original_image_url;
    originalImg.alt = "Original uploaded scene";
  }

  const viewerUrl =
    scenario.viewer_url ||
    (scenario.room_id
      ? `/static/viewer.html?room=${encodeURIComponent(scenario.room_id)}`
      : "");
  const panoramaThumbUrl = scenario.panorama_thumbnail_url || scenario.generated_image_url || "";

  if (panoramaThumbnail && panoramaThumbUrl) {
    panoramaThumbnail.src = panoramaThumbUrl;
  }
  if (panoramaStatus) {
    panoramaStatus.textContent = viewerUrl
      ? "Your 360 learning world is ready to explore."
      : "360 preview is being prepared.";
  }
  if (panoramaOpenBtn && viewerUrl) {
    panoramaOpenBtn.addEventListener("click", () => {
      window.open(viewerUrl, "_blank", "noopener,noreferrer");
    });
  }

  // --- Transformations Table ---

  const transformBody = document.getElementById("transformations-body");
  const transformCount = document.getElementById("transform-count");

  if (transformBody && scenario.transformations) {
    if (transformCount) {
      transformCount.textContent = `${scenario.transformations.length} Items Detected`;
    }
    transformBody.innerHTML = scenario.transformations
      .map(
        (t) => `
      <tr class="group hover:bg-slate-50/50 transition-colors">
        <td class="py-4 font-semibold text-slate-700">${esc(t.real_object)}</td>
        <td class="py-4">
          <div class="flex items-center text-indigo-600 font-medium">
            <span class="material-symbols-outlined mr-2 text-lg">auto_fix_high</span>
            ${esc(t.game_object)}
          </div>
        </td>
        <td class="py-4 text-on-surface-variant">${esc(t.puzzle_role)}</td>
      </tr>`
      )
      .join("");
  }

  // --- Puzzle Progression ---

  const puzzleFlow = document.getElementById("puzzle-flow");
  if (puzzleFlow && scenario.puzzles) {
    const icons = ["qr_code_scanner", "lock_open", "key", "door_front"];
    const shortLabels = scenario.puzzles.map((p) => {
      const words = p.title.split(" ");
      return words.length <= 2 ? p.title : words[words.length - 1];
    });
    shortLabels.push("Complete");

    const statusForStep = (stepNum) => {
      if (playState.isEscaped) return "done";
      if (playState.currentStep > totalPuzzleSteps) {
        return stepNum <= totalPuzzleSteps ? "done" : "active";
      }
      if (playState.solvedSteps.includes(stepNum)) return "done";
      if (stepNum === playState.currentStep) return "active";
      return "pending";
    };

    const renderPuzzleFlow = () => {
      puzzleFlow.innerHTML = `
        <div class="absolute top-6 left-12 right-12 h-[2px] bg-slate-100 -z-0"></div>
        ${shortLabels
          .map((label, i) => {
            const stepNum = i + 1;
            const status = statusForStep(stepNum);
            const iconName =
              status === "done" ? "check" : icons[i] || "circle";
            const circleClass =
              status === "active"
                ? "bg-indigo-600 text-white shadow-lg shadow-indigo-100"
                : status === "done"
                  ? "bg-tertiary text-white"
                  : "bg-surface-container-high text-on-surface-variant";
            const labelClass =
              status === "active" || status === "done"
                ? "text-on-surface"
                : "text-slate-400";

            return `
          <div class="flex flex-col items-center text-center relative z-10 max-w-[80px]">
            <div class="w-12 h-12 rounded-full ${circleClass} flex items-center justify-center mb-3">
              <span class="material-symbols-outlined text-xl">${iconName}</span>
            </div>
            <span class="text-xs font-bold ${labelClass} truncate w-full">${esc(label)}</span>
          </div>`;
          })
          .join("")}
      `;
    };

    playState.renderPuzzleFlow = renderPuzzleFlow;
    renderPuzzleFlow();
  }

  // --- JSON Preview ---

  const jsonDebugCard = document.getElementById("json-debug-card");
  const jsonPreview = document.getElementById("json-preview");
  const isDebugMode = isDebugModeEnabled();

  if (jsonDebugCard) {
    jsonDebugCard.classList.toggle("hidden", !isDebugMode);
  }

  if (jsonPreview && isDebugMode) {
    jsonPreview.textContent = JSON.stringify(scenario, null, 2);
  }

  // --- Play Mode ---

  const playProgress = document.getElementById("play-progress");
  const playStepTitle = document.getElementById("play-step-title");
  const playStepDescription = document.getElementById("play-step-description");
  const playStepView = document.getElementById("play-step-view");
  const playAnswerInput = document.getElementById("play-answer-input");
  const playCheckBtn = document.getElementById("play-check-btn");
  const playRevealHintBtn = document.getElementById("play-reveal-hint-btn");
  const playRevealSolutionBtn = document.getElementById("play-reveal-solution-btn");
  const playNextBtn = document.getElementById("play-next-btn");
  const playFeedback = document.getElementById("play-feedback");
  const playHintBox = document.getElementById("play-hint-box");
  const playSolutionBox = document.getElementById("play-solution-box");
  const playFinalView = document.getElementById("play-final-view");
  const playFinalObjective = document.getElementById("play-final-objective");
  const playFinalInput = document.getElementById("play-final-input");
  const playFinalCheckBtn = document.getElementById("play-final-check-btn");
  const playFinalFeedback = document.getElementById("play-final-feedback");
  const playCompleteView = document.getElementById("play-complete-view");
  const gameEndModal = document.getElementById("game-end-modal");
  const gameEndCloseBtn = document.getElementById("game-end-close-btn");
  const gameEndDashboardBtn = document.getElementById("game-end-dashboard-btn");
  const gameEndNewBtn = document.getElementById("game-end-new-btn");

  renderPlayStep();

  if (playCheckBtn) {
    playCheckBtn.addEventListener("click", () => {
      const step = puzzleSteps[playState.currentStep - 1];
      if (!step) return;
      const attempt = playAnswerInput ? playAnswerInput.value : "";
      if (!attempt.trim()) {
        showPlayFeedback("Please enter an answer first.", false);
        return;
      }
      if (isStepAnswerMatch(attempt, step.solution)) {
        markCurrentStepSolved();
        showPlayFeedback("Correct. You can move to the next step.", true);
      } else {
        showPlayFeedback("Not quite. Try a different answer or reveal a hint.", false);
      }
    });
  }

  if (playRevealHintBtn) {
    playRevealHintBtn.addEventListener("click", async () => {
      const step = puzzleSteps[playState.currentStep - 1];
      if (!step) return;
      const hint = await fetchHint(getHintStepForApi(), null, "play");
      if (!hint) showPlayHint(step.hint);
    });
  }

  if (playRevealSolutionBtn) {
    playRevealSolutionBtn.addEventListener("click", () => {
      const step = puzzleSteps[playState.currentStep - 1];
      if (!step) return;
      showPlaySolution(step.solution);
      markCurrentStepSolved();
      showPlayFeedback("Solution revealed. You can move to the next step.", true);
    });
  }

  if (playNextBtn) {
    playNextBtn.addEventListener("click", () => {
      if (!isCurrentStepSolved()) return;
      playState.currentStep += 1;
      renderPlayStep();
    });
  }

  if (playFinalCheckBtn) {
    playFinalCheckBtn.addEventListener("click", () => {
      if (playState.isEscaped) return;
      const expected = normalizeText(scenario.final_escape?.solution || "");
      const actual = normalizeText(playFinalInput ? playFinalInput.value : "");
      if (!actual) {
        showPlayFinalFeedback("Enter the final answer.", false);
        return;
      }
      if (actual === expected) {
        playState.isEscaped = true;
        playState.currentStep = totalPuzzleSteps + 1;
        lockFinalEscape(true);
        showPlayFinalFeedback("Knowledge unlocked. Challenge complete.", true);
        if (playCompleteView) playCompleteView.classList.remove("hidden");
        if (playState.renderPuzzleFlow) playState.renderPuzzleFlow();
        if (!playState.didShowEscapeModal) {
          openGameEndModal();
          playState.didShowEscapeModal = true;
        }
      } else {
        showPlayFinalFeedback("Incorrect answer. Try again.", false);
      }
    });
  }

  if (gameEndCloseBtn) {
    gameEndCloseBtn.addEventListener("click", closeGameEndModal);
  }

  if (gameEndDashboardBtn) {
    gameEndDashboardBtn.addEventListener("click", () => {
      closeGameEndModal();
      document
        .getElementById("result-title")
        ?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  if (gameEndNewBtn) {
    gameEndNewBtn.addEventListener("click", () => {
      window.location.href = "/static/index.html";
    });
  }

  if (gameEndModal) {
    gameEndModal.addEventListener("click", (e) => {
      if (e.target === gameEndModal) closeGameEndModal();
    });
  }

  function renderPlayStep() {
    const isFinal = playState.currentStep > totalPuzzleSteps;
    if (playState.renderPuzzleFlow) playState.renderPuzzleFlow();

    if (playStepView) playStepView.classList.toggle("hidden", isFinal);
    if (playFinalView) playFinalView.classList.toggle("hidden", !isFinal);
    if (playCompleteView) playCompleteView.classList.add("hidden");

    if (isFinal) {
      if (playProgress) {
        playProgress.textContent = playState.isEscaped
          ? "Challenge Complete"
          : "Final Challenge";
      }
      if (playStepTitle) playStepTitle.textContent = "Final Challenge";
      if (playStepDescription) {
        playStepDescription.textContent =
          "Use everything you discovered in the previous tasks.";
      }
      if (playFinalObjective) {
        playFinalObjective.textContent =
          scenario.final_escape?.objective || "Enter the final answer.";
      }
      if (playState.isEscaped) {
        lockFinalEscape(true);
        if (playFinalInput) {
          playFinalInput.value = scenario.final_escape?.solution || "";
        }
        showPlayFinalFeedback("Session locked: challenge already completed.", true);
        if (playCompleteView) playCompleteView.classList.remove("hidden");
      } else {
        lockFinalEscape(false);
        if (playFinalInput) playFinalInput.value = "";
        if (playFinalFeedback) playFinalFeedback.classList.add("hidden");
      }
      return;
    }

    const step = puzzleSteps[playState.currentStep - 1];
    if (!step) return;
    if (playProgress) playProgress.textContent = `Step ${playState.currentStep} / ${totalPuzzleSteps}`;
    if (playStepTitle) playStepTitle.textContent = step.title || `Step ${playState.currentStep}`;
    if (playStepDescription) playStepDescription.textContent = step.description || "";
    if (playAnswerInput) playAnswerInput.value = "";
    if (playFeedback) playFeedback.classList.add("hidden");
    if (playHintBox) playHintBox.classList.add("hidden");
    if (playSolutionBox) playSolutionBox.classList.add("hidden");
    if (playNextBtn) {
      playNextBtn.classList.toggle("hidden", !isCurrentStepSolved());
      playNextBtn.textContent =
        playState.currentStep >= totalPuzzleSteps ? "Go to Final Challenge" : "Next Task";
    }
  }

  function isCurrentStepSolved() {
    return playState.solvedSteps.includes(playState.currentStep);
  }

  function markCurrentStepSolved() {
    if (!playState.solvedSteps.includes(playState.currentStep)) {
      playState.solvedSteps.push(playState.currentStep);
    }
    if (playState.renderPuzzleFlow) playState.renderPuzzleFlow();
    if (playNextBtn) {
      playNextBtn.classList.remove("hidden");
      playNextBtn.textContent =
        playState.currentStep >= totalPuzzleSteps ? "Go to Final Challenge" : "Next Task";
    }
  }

  function isStepAnswerMatch(input, solution) {
    const normalizedInput = normalizeText(input);
    const normalizedSolution = normalizeText(solution);
    if (!normalizedInput || !normalizedSolution) return false;

    const inputDigits = input.replace(/\D+/g, "");
    const solutionDigits = solution.replace(/\D+/g, "");
    if (inputDigits && solutionDigits && inputDigits === solutionDigits) {
      return true;
    }

    const compactInput = normalizedInput.replace(/\s+/g, "");
    const compactSolution = normalizedSolution.replace(/\s+/g, "");
    if (compactInput.length >= 3 && compactSolution.includes(compactInput)) {
      return true;
    }

    const keywords = normalizedSolution
      .split(" ")
      .filter((word) => word.length >= 3 && !STOP_WORDS.has(word));
    if (!keywords.length) return false;

    const matched = keywords.filter((word) => normalizedInput.includes(word)).length;
    return matched >= Math.max(1, Math.ceil(keywords.length / 2));
  }

  function showPlayHint(text) {
    if (!playHintBox) return;
    playHintBox.textContent = text;
    playHintBox.classList.remove("hidden");
  }

  function showPlaySolution(text) {
    if (!playSolutionBox) return;
    playSolutionBox.textContent = `Solution: ${text}`;
    playSolutionBox.classList.remove("hidden");
  }

  function showPlayFeedback(text, isSuccess) {
    if (!playFeedback) return;
    playFeedback.textContent = text;
    playFeedback.classList.remove("hidden");
    playFeedback.classList.toggle("text-tertiary", isSuccess);
    playFeedback.classList.toggle("text-error", !isSuccess);
  }

  function showPlayFinalFeedback(text, isSuccess) {
    if (!playFinalFeedback) return;
    playFinalFeedback.textContent = text;
    playFinalFeedback.classList.remove("hidden");
    playFinalFeedback.classList.toggle("text-tertiary", isSuccess);
    playFinalFeedback.classList.toggle("text-error", !isSuccess);
  }

  function lockFinalEscape(locked) {
    if (playFinalInput) {
      playFinalInput.disabled = locked;
      playFinalInput.readOnly = locked;
      playFinalInput.classList.toggle("opacity-60", locked);
      playFinalInput.classList.toggle("cursor-not-allowed", locked);
    }
    if (playFinalCheckBtn) {
      playFinalCheckBtn.disabled = locked;
      playFinalCheckBtn.classList.toggle("opacity-60", locked);
      playFinalCheckBtn.classList.toggle("cursor-not-allowed", locked);
      playFinalCheckBtn.textContent = locked ? "Completed" : "Complete";
    }
  }

  function openGameEndModal() {
    if (!gameEndModal) return;
    gameEndModal.classList.remove("hidden");
  }

  function closeGameEndModal() {
    if (!gameEndModal) return;
    gameEndModal.classList.add("hidden");
  }

  function getHintStepForApi() {
    if (totalPuzzleSteps === 0) return 1;
    return Math.max(1, Math.min(playState.currentStep, totalPuzzleSteps));
  }

  // --- Copy / Download JSON ---

  const copyBtn = document.getElementById("copy-json-btn");
  const downloadBtn = document.getElementById("download-json-btn");

  if (copyBtn && isDebugMode) {
    copyBtn.addEventListener("click", () => {
      navigator.clipboard
        .writeText(JSON.stringify(scenario, null, 2))
        .then(() => {
          copyBtn.title = "Copied!";
          setTimeout(() => (copyBtn.title = "Copy JSON"), 2000);
        });
    });
  }

  if (downloadBtn && isDebugMode) {
    downloadBtn.addEventListener("click", () => {
      const blob = new Blob([JSON.stringify(scenario, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${scenario.experience_id || "scenario"}.json`;
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  // --- Image Modal ---

  const modal = document.getElementById("image-modal");
  const modalImg = document.getElementById("modal-image");
  const modalClose = document.getElementById("modal-close");

  if (modalClose) {
    modalClose.addEventListener("click", () => modal.classList.add("hidden"));
  }

  if (modal) {
    modal.addEventListener("click", (e) => {
      if (e.target === modal) modal.classList.add("hidden");
    });
  }

  // --- Voice Host (Vapi) ---

  const voiceStartBtn = document.getElementById("voice-start-btn");
  const voiceEndBtn = document.getElementById("voice-end-btn");
  const voiceOutput = document.getElementById("voice-output");
  const callStatusText = document.getElementById("call-status-text");
  const callIndicator = document.getElementById("call-indicator");

  if (voiceStartBtn) {
    voiceStartBtn.addEventListener("click", async () => {
      await startVapiCall("intro");
    });
  }

  if (voiceEndBtn) {
    voiceEndBtn.addEventListener("click", async () => {
      await endVapiCall();
    });
  }

  syncVoiceUi();
  setCallStatus("Idle", "idle");

  async function fetchHint(step, question, target) {
    try {
      const resp = await fetch(`${API_BASE}/api/hint`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_context: scenario,
          current_step: step,
          user_question: question || null,
        }),
      });

      if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
      const data = await resp.json();
      const text = data.hint || data.voice_friendly || "";
      if (target === "play") {
        showPlayHint(text || "Hint unavailable right now. Try again.");
      } else {
        showVoiceOutput(text || "Hint unavailable right now. Try again.");
      }
      return text;
    } catch (err) {
      const fallbackText = "Hint unavailable right now. Try again.";
      if (target === "play") {
        showPlayHint(fallbackText);
      } else {
        showVoiceOutput(fallbackText);
      }
      return fallbackText;
    }
  }

  const VAPI_SDK_URL = "https://cdn.jsdelivr.net/npm/@vapi-ai/web@2.5.2/+esm";

  function resolveVapiConstructor(mod) {
    const candidates = [
      mod?.default,
      mod?.Vapi,
      mod?.default?.default,
      mod?.default?.Vapi,
    ];
    for (const candidate of candidates) {
      if (typeof candidate === "function") return candidate;
    }
    return null;
  }

  function parseVapiErrorMessage(error) {
    const rawMessage =
      error?.error?.message ||
      error?.message ||
      error?.error?.error?.message ||
      "Unknown Vapi error.";
    const normalized = String(rawMessage);
    if (normalized.toLowerCase().includes("unauthorized") || normalized.includes("401")) {
      return (
        "Vapi authentication failed (401). Check VAPI_PUBLIC_KEY. " +
        "Use your real Vapi public key from the dashboard, not a placeholder or private API key."
      );
    }
    return normalized;
  }

  async function loadVapiSdk() {
    if (vapiState.sdkConstructor) {
      console.log("[Vapi] SDK constructor already cached");
      return vapiState.sdkConstructor;
    }
    console.log("[Vapi] Loading SDK from", VAPI_SDK_URL);
    try {
      const mod = await import(VAPI_SDK_URL);
      const VapiClass = resolveVapiConstructor(mod);
      console.log("[Vapi] Module keys:", Object.keys(mod));
      console.log("[Vapi] Export types:", {
        default: typeof mod?.default,
        Vapi: typeof mod?.Vapi,
        defaultDefault: typeof mod?.default?.default,
        defaultVapi: typeof mod?.default?.Vapi,
      });
      if (!VapiClass) {
        console.error("[Vapi] No constructor export found.");
        throw new Error("Vapi SDK module has no usable export.");
      }
      vapiState.sdkConstructor = VapiClass;
      console.log("[Vapi] SDK loaded successfully; constructor:", VapiClass.name || "<anonymous>");
      return VapiClass;
    } catch (err) {
      console.error("[Vapi] Failed to load SDK:", err);
      throw new Error(`Failed to load Vapi SDK: ${err.message}`);
    }
  }

  async function startVapiCall(callType) {
    if (vapiState.callActive || vapiState.callConnecting) return;
    vapiState.callConnecting = true;
    syncVoiceUi();
    setCallStatus("Connecting", "connecting");
    showVoiceOutput("Connecting to your guide...");

    try {
      console.log("[Vapi] startVapiCall:", callType, "step:", getHintStepForApi());

      console.log("[Vapi] Fetching assistant config from backend...");
      const resp = await fetch(`${API_BASE}/api/vapi/assistant-config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          scenario_context: scenario,
          current_step: getHintStepForApi(),
          call_type: callType,
        }),
      });

      if (!resp.ok) {
        const details = await resp.text();
        console.error("[Vapi] Backend error:", resp.status, details);
        throw new Error(details || `Server error: ${resp.status}`);
      }

      const data = await resp.json();
      console.log("[Vapi] Got config response. public_key present:", !!data?.public_key,
                  "assistant_config keys:", data?.assistant_config ? Object.keys(data.assistant_config) : "none");

      const publicKey = data?.public_key || "";
      const assistantConfig = data?.assistant_config;
      if (!publicKey || !assistantConfig) {
        throw new Error("Invalid Vapi assistant config response.");
      }
      if (publicKey.toLowerCase() === "your-vapi-public-key-here") {
        throw new Error(
          "VAPI_PUBLIC_KEY is still a placeholder. Set a real Vapi public key in backend .env and restart the server."
        );
      }

      const client = await ensureVapiClient(publicKey);
      clearVoiceOutput();
      console.log("[Vapi] Starting call with full config:", JSON.stringify(assistantConfig, null, 2));
      await client.start(assistantConfig);
      console.log("[Vapi] client.start() resolved");
    } catch (error) {
      console.error("[Vapi] startVapiCall failed:", error);
      vapiState.callConnecting = false;
      vapiState.callActive = false;
      syncVoiceUi();
      setCallStatus("Error", "error");
      showVoiceOutput(`Voice connection failed: ${error.message || "Unknown error."}`);
    }
  }

  async function ensureVapiClient(publicKey) {
    const VapiClass = await loadVapiSdk();

    if (vapiState.client && vapiState.lastPublicKey === publicKey) {
      console.log("[Vapi] Reusing existing client");
      return vapiState.client;
    }

    console.log("[Vapi] Creating new Vapi client");
    const client = new VapiClass(publicKey);
    vapiState.client = client;
    vapiState.lastPublicKey = publicKey;

    client.on("call-start", () => {
      console.log("[Vapi] Event: call-start");
      vapiState.callConnecting = false;
      vapiState.callActive = true;
      syncVoiceUi();
      setCallStatus("Active", "active");
      showVoiceOutput("Connected. Speak to your guide.");
    });

    client.on("call-end", () => {
      console.log("[Vapi] Event: call-end");
      vapiState.callConnecting = false;
      vapiState.callActive = false;
      syncVoiceUi();
      setCallStatus("Idle", "idle");
      showVoiceOutput("Call ended.");
    });

    client.on("speech-start", () => {
      console.log("[Vapi] Event: speech-start (assistant speaking)");
    });

    client.on("speech-end", () => {
      console.log("[Vapi] Event: speech-end");
    });

    client.on("volume-level", () => {
      // Intentionally silent -- fires very frequently
    });

    client.on("message", (message) => {
      console.log("[Vapi] Event: message", message?.type, message?.role, message?.transcriptType);
      const transcript = extractTranscriptFromMessage(message);
      if (!transcript) return;
      updateVoiceTranscript(transcript.role, transcript.text, transcript.isFinal);
    });

    client.on("error", (error) => {
      console.error("[Vapi] Event: error", JSON.stringify(error, null, 2));
      vapiState.callConnecting = false;
      vapiState.callActive = false;
      syncVoiceUi();
      setCallStatus("Error", "error");
      showVoiceOutput(`Voice error: ${parseVapiErrorMessage(error)}`);
    });

    return client;
  }

  async function endVapiCall() {
    if (!vapiState.client || (!vapiState.callActive && !vapiState.callConnecting)) return;
    console.log("[Vapi] Ending call...");
    try {
      await vapiState.client.stop();
      console.log("[Vapi] Call stopped");
    } catch (error) {
      console.error("[Vapi] Failed to end call:", error);
      setCallStatus("Error", "error");
      showVoiceOutput(`Failed to end call: ${error.message || "Unknown error."}`);
    }
  }

  function syncVoiceUi() {
    const disableActionButtons = vapiState.callConnecting || vapiState.callActive;
    [voiceStartBtn].forEach((button) => {
      if (!button) return;
      button.disabled = disableActionButtons;
      button.classList.toggle("opacity-60", disableActionButtons);
      button.classList.toggle("cursor-not-allowed", disableActionButtons);
    });
    if (voiceEndBtn) {
      const shouldShowEnd = vapiState.callConnecting || vapiState.callActive;
      voiceEndBtn.classList.toggle("hidden", !shouldShowEnd);
      voiceEndBtn.disabled = !shouldShowEnd;
    }
  }

  function setCallStatus(label, tone) {
    if (callStatusText) callStatusText.textContent = label;
    if (!callIndicator) return;
    callIndicator.classList.remove("bg-slate-400", "bg-amber-500", "bg-tertiary", "bg-error");
    if (tone === "active") callIndicator.classList.add("bg-tertiary");
    else if (tone === "connecting") callIndicator.classList.add("bg-amber-500");
    else if (tone === "error") callIndicator.classList.add("bg-error");
    else callIndicator.classList.add("bg-slate-400");
  }

  function showVoiceOutput(text) {
    if (!voiceOutput) return;
    voiceOutput.innerHTML = "";
    const line = document.createElement("p");
    line.className = "text-sm";
    line.textContent = text;
    voiceOutput.appendChild(line);
    voiceOutput.classList.remove("hidden");
  }

  function clearVoiceOutput() {
    if (!voiceOutput) return;
    voiceOutput.innerHTML = "";
    voiceOutput.classList.remove("hidden");
  }

  let lastTranscriptEl = null;
  let lastTranscriptRole = null;

  function updateVoiceTranscript(role, text, isFinal) {
    if (!voiceOutput) return;
    voiceOutput.classList.remove("hidden");
    const label = role === "assistant" ? "Guide" : "You";
    const html = `<span class="font-semibold text-on-surface">${esc(label)}:</span> ${esc(text)}`;

    if (lastTranscriptEl && lastTranscriptRole === role) {
      lastTranscriptEl.innerHTML = html;
    } else {
      const line = document.createElement("p");
      line.className = "text-sm";
      line.innerHTML = html;
      voiceOutput.appendChild(line);
      lastTranscriptEl = line;
      lastTranscriptRole = role;
    }

    if (isFinal) {
      lastTranscriptEl = null;
      lastTranscriptRole = null;
    }

    voiceOutput.scrollTop = voiceOutput.scrollHeight;
  }

  function extractTranscriptFromMessage(message) {
    if (!message || message.type !== "transcript") return null;
    const text = String(
      message.transcript || message.text || message.message?.content || ""
    ).trim();
    if (!text) return null;
    const role = message.role === "user" ? "user" : "assistant";
    const isFinal = message.transcriptType === "final";
    return { role, text, isFinal };
  }

  function normalizeText(value) {
    return String(value || "")
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, " ")
      .replace(/\s+/g, " ")
      .trim();
  }

  function isDebugModeEnabled() {
    const debugParam = new URLSearchParams(window.location.search).get("debug");
    if (
      debugParam &&
      DEBUG_TRUE_VALUES.has(String(debugParam).toLowerCase())
    ) {
      return true;
    }
    if (sessionStorage.getItem("room2learn_debug") === "1") return true;
    if (localStorage.getItem("room2learn_debug") === "1") return true;
    return false;
  }

  function esc(str) {
    const d = document.createElement("div");
    d.textContent = str;
    return d.innerHTML;
  }
})();
