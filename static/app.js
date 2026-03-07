(() => {
  const $ = (id) => document.getElementById(id);

  // ── Toolbar & Config ──
  const configToggle = $("configToggle");
  const configPanel = $("configPanel");
  const pillModel = $("pillModel");
  const pillDot = $("pillDot");

  // ── Config Form ──
  const providerSelect = $("providerSelect");
  const baseUrlInput = $("baseUrl");
  const modelInput = $("modelName");
  const apiKeyInput = $("apiKey");
  const getKeyLink = $("getKeyLink");
  const maxMinInput = $("maxMinutes");
  const maxMBInput = $("maxMB");
  const saveConfigBtn = $("saveConfigBtn");
  const testBtn = $("testBtn");
  const testResult = $("testResult");
  const toggleKeyVis = $("toggleKeyVisibility");

  // ── Recording Elements ──
  const recordTimer = $("recordTimer");
  const micSelect = $("micSelect");
  const sourceToggles = $("sourceToggles");
  const toggleMicBtn = $("toggleMic");
  const toggleSysBtn = $("toggleSys");
  const startRecordBtn = $("startRecordBtn");
  const stopRecordBtn = $("stopRecordBtn");

  // ── Transcription UI ──
  const dropZone = $("dropZone");
  const dropContent = $("dropContent");
  const fileInput = $("fileInput");
  const fileInfo = $("fileInfo");
  const fileName = $("fileName");
  const fileSize = $("fileSize");
  const cancelFileBtn = $("cancelFileBtn");
  const startBtn = $("startBtn");
  const progressCard = $("progressCard");
  const progressBar = $("progressBar");
  const statusBadge = $("statusBadge");
  const progressText = $("progressText");
  const chunksGrid = $("chunksGrid");
  const resultCard = $("resultCard");
  const copyBtn = $("copyBtn");
  const downloadBtn = $("downloadBtn");
  const downloadMdBtn = $("downloadMdBtn");
  const transcriptOutput = $("transcriptOutput");
  const newTaskBtn = $("newTaskBtn");
  const timerDisplay = $("timerDisplay");
  const timerETA = $("timerETA");
  const audioPreview = $("audioPreview");

  // ── Test Mode ──
  const testModeBanner = $("testModeBanner");
  const demoCard = $("demoCard");
  const demoFilesGrid = $("demoFilesGrid");
  const demoHint = $("demoHint");

  // ── State ──
  let mediaRecorder = null;
  let recordedChunks = [];
  let recordTimeStart = 0;
  let recordInterval = null;
  let combinedStream = null;
  let micGainNode = null;
  let sysGainNode = null;
  let micStream = null;
  let systemStream = null;
  let audioCtx = null;
  let selectedFile = null;
  let currentTaskId = null;
  let timerInterval = null;
  let timerStart = 0;
  let pollTimer = null;
  let providerConfigs = {}; // { provider: { baseUrl, apiKey, model } }
  let lastRecordTick = 0; // for system sleep detection
  let isRecording = false; // stable flag for event listeners

  const SPEAKER_COLORS = [
    "#007AFF",
    "#34C759",
    "#FF9500",
    "#AF52DE",
    "#FF3B30",
    "#5856D6",
  ];

  // Speaker-related state
  const speakerCard = $("speakerCard");
  const speakerResults = $("speakerResults");
  const saveSpeakersBtn = $("saveSpeakersBtn");
  const speakerLibraryCard = $("speakerLibraryCard");
  const libraryList = $("libraryList");
  const refreshLibraryBtn = $("refreshLibraryBtn");
  let lastTaskId = null;
  let lastSpeakers = [];

  const PROVIDERS = {
    gemini: {
      url: "https://generativelanguage.googleapis.com/v1beta/openai",
      model: "gemini-2.5-flash",
      link: "https://aistudio.google.com/apikey",
      serverKey: true, // API key managed by server
    },
    aliyun: {
      url: "https://dashscope.aliyuncs.com/compatible-mode/v1",
      model: "qwen-audio-turbo",
      link: "https://bailian.console.aliyun.com/",
    },
    tencent: {
      url: "https://api.tensor.so/openai/v1",
      model: "tencent-audio",
      link: "https://console.cloud.tencent.com/asr",
    },
    volc: {
      url: "https://ark.cn-beijing.volces.com/api/v3",
      model: "doubao-pro-4k",
      link: "https://console.volcengine.com/speech/service/8",
    },
    zhipu: {
      url: "https://open.bigmodel.cn/api/paas/v4",
      model: "glm-4-flash",
      link: "https://bigmodel.cn/invite?invite_code=6N4G5H",
      isZhipuSDK: true,
    },
    modelscope: {
      url: "https://api-inference.modelscope.ai/v1",
      model: "iic/SenseVoiceSmall",
      link: "https://www.modelscope.cn/my/myaccesstoken",
    },
    custom: { url: "", model: "", link: "" },
  };

  function updateProviderUI() {
    const p = providerSelect.value;
    if (!p) return;

    const isCustom = p === "custom";
    const providerInfo = PROVIDERS[p];

    // Get stored config for this provider or use defaults
    const config = providerConfigs[p] || {};

    baseUrlInput.disabled = false;
    modelInput.disabled = false;
    apiKeyInput.disabled = false;
    baseUrlInput.parentElement.style.opacity = "1";
    apiKeyInput.parentElement.style.opacity = "1";

    // Reset placeholders
    baseUrlInput.placeholder = "https://api.example.com/v1";
    modelInput.placeholder = "model-name";
    apiKeyInput.placeholder = "sk-......";

    if (providerInfo && providerInfo.serverKey) {
      // Built-in provider: server manages base_url and api_key
      baseUrlInput.parentElement.style.opacity = "0.5";
      baseUrlInput.value = providerInfo.url;
      baseUrlInput.disabled = true;
      apiKeyInput.parentElement.style.opacity = "0.5";
      apiKeyInput.value = "(server-env)";
      apiKeyInput.disabled = true;
      modelInput.value = config.model || providerInfo.model;
      pillDot.classList.add("connected");
    } else if (providerInfo && providerInfo.isZhipuSDK) {
      baseUrlInput.parentElement.style.opacity = "0.5";
      baseUrlInput.value = "使用官方 SDK 直连";
      baseUrlInput.disabled = true;
      modelInput.value = config.model || providerInfo.model;
      apiKeyInput.value = config.apiKey || "";
    } else {
      baseUrlInput.value =
        config.baseUrl || (providerInfo ? providerInfo.url : "");
      modelInput.value =
        config.model || (providerInfo ? providerInfo.model : "");
      apiKeyInput.value = config.apiKey || "";
    }

    if (providerInfo && providerInfo.link) {
      getKeyLink.href = providerInfo.link;
      getKeyLink.style.display = "inline-block";
      getKeyLink.textContent = providerInfo.serverKey
        ? "🔗 查看官网"
        : "🔗 去注册领取免费额度";
    } else {
      getKeyLink.style.display = "none";
    }

    pillModel.textContent = modelInput.value || "未配置";
  }

  providerSelect.addEventListener("change", () => {
    // Save current before switching to load next
    const prevProvider = localStorage.getItem("lastSavedProvider");
    if (prevProvider) {
      // We sync on every change to avoid loss
      providerConfigs[prevProvider] = {
        baseUrl: baseUrlInput.value,
        model: modelInput.value,
        apiKey: apiKeyInput.value,
      };
      localStorage.setItem("providerConfigs", JSON.stringify(providerConfigs));
    }
    updateProviderUI();
    localStorage.setItem("lastSavedProvider", providerSelect.value);
  });

  // ── Config Persistence ────────────────────────────────────
  function saveConfig() {
    const p = providerSelect.value;
    providerConfigs[p] = {
      baseUrl: baseUrlInput.value.trim(),
      model: modelInput.value.trim(),
      apiKey: apiKeyInput.value.trim(),
    };

    const globalCfg = {
      provider: p,
      maxMinutes: maxMinInput.value,
      maxMB: maxMBInput.value,
    };

    localStorage.setItem("audioTranscriberConfig", JSON.stringify(globalCfg));
    localStorage.setItem("providerConfigs", JSON.stringify(providerConfigs));
    localStorage.setItem("lastSavedProvider", p);

    pillModel.textContent = modelInput.value || "未配置";
  }

  function loadConfig() {
    const rawGlobal = localStorage.getItem("audioTranscriberConfig");
    const rawProviders = localStorage.getItem("providerConfigs");

    if (rawProviders) {
      providerConfigs = JSON.parse(rawProviders);
    }

    if (!rawGlobal) {
      configPanel.classList.remove("collapsed");
      configToggle.classList.add("active");
      updateProviderUI();
      return;
    }

    const cfg = JSON.parse(rawGlobal);
    providerSelect.value = cfg.provider || "openai";
    maxMinInput.value = cfg.maxMinutes || 10;
    maxMBInput.value = cfg.maxMB || 20;

    // Migration from old flat config to provider map if needed
    if (!rawProviders && cfg.apiKey) {
      providerConfigs[cfg.provider || "openai"] = {
        baseUrl: cfg.baseUrl,
        model: cfg.model,
        apiKey: cfg.apiKey,
      };
      localStorage.setItem("providerConfigs", JSON.stringify(providerConfigs));
    }

    localStorage.setItem("lastSavedProvider", providerSelect.value);
    updateProviderUI();
  }

  // ── Config Toggle (pill button) ───────────────────────────
  configToggle.addEventListener("click", () => {
    configPanel.classList.toggle("collapsed");
    configToggle.classList.toggle("active");
  });

  // ── API Key Visibility ────────────────────────────────────
  toggleKeyVis.addEventListener("click", () => {
    const isPwd = apiKeyInput.type === "password";
    apiKeyInput.type = isPwd ? "text" : "password";
    toggleKeyVis.textContent = isPwd ? "🙈" : "👁️";
  });

  // ── Save Config ───────────────────────────────────────────
  saveConfigBtn.addEventListener("click", () => {
    saveConfig();
    showToast("✅ 配置已保存", "success");
    setTimeout(() => {
      if (!configPanel.classList.contains("collapsed")) {
        configPanel.classList.add("collapsed");
        configToggle.classList.remove("active");
      }
    }, 600);
  });

  // ── Test Connection ───────────────────────────────────────
  testBtn.addEventListener("click", async () => {
    testResult.textContent = "";
    testBtn.disabled = true;
    testBtn.innerHTML = '<span class="spinner"></span> 测试中…';
    saveConfig();
    try {
      const res = await fetch("/api/test-connection", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          base_url: baseUrlInput.value,
          model: modelInput.value,
          api_key: apiKeyInput.value,
          provider: providerSelect.value || "openai",
        }),
      });
      const data = await res.json();
      if (data.ok) {
        testResult.textContent = "✅ 连接成功";
        testResult.className = "test-result ok";
        pillDot.classList.add("connected");
      } else {
        testResult.textContent = "❌ " + (data.error || "连接失败");
        testResult.className = "test-result err";
        pillDot.classList.remove("connected");
      }
    } catch {
      testResult.textContent = "❌ 网络错误";
      testResult.className = "test-result err";
    } finally {
      testBtn.disabled = false;
      testBtn.textContent = "🔗 测试连接";
    }
  });

  // ── Drag & Drop ───────────────────────────────────────────
  dropZone.addEventListener("click", (e) => {
    if (e.target.closest("button")) return;
    fileInput.click();
  });
  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("drag-over");
  });
  dropZone.addEventListener("dragleave", () =>
    dropZone.classList.remove("drag-over"),
  );
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("drag-over");
    if (e.dataTransfer.files[0]) selectFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) selectFile(fileInput.files[0]);
  });

  // ── Device Enumeration ────────────────────────────────────
  async function listDevices() {
    try {
      // Prompt for permission if not already granted to get labels
      await navigator.mediaDevices.getUserMedia({ audio: true });
      const devices = await navigator.mediaDevices.enumerateDevices();
      const mics = devices.filter((d) => d.kind === "audioinput");

      micSelect.innerHTML =
        mics
          .map(
            (m) =>
              `<option value="${m.deviceId}">${m.label || "默认麦克风"}</option>`,
          )
          .join("") || '<option value="">无可用设备</option>';
    } catch (err) {
      micSelect.innerHTML = '<option value="">无法访问麦克风</option>';
      console.error("enumerateDevices error:", err);
    }
  }

  // ── Recording Logic ───────────────────────────────────────
  startRecordBtn.addEventListener("click", async () => {
    try {
      recordedChunks = [];

      // 1. Get Microphone stream with selected device
      const micConstraints = {
        audio: micSelect.value
          ? { deviceId: { exact: micSelect.value } }
          : true,
      };
      micStream = await navigator.mediaDevices.getUserMedia(micConstraints);

      // 2. Get System Audio stream via getDisplayMedia
      try {
        systemStream = await navigator.mediaDevices.getDisplayMedia({
          video: true,
          audio: true,
        });
        // We only need audio - stop any video tracks immediately
        systemStream.getVideoTracks().forEach((t) => t.stop());
      } catch (err) {
        micStream.getTracks().forEach((t) => t.stop());
        console.error("[Recording] getDisplayMedia failed:", err);
        throw new Error("无法获取系统音频。\n请确认已授予屏幕录制权限并重试。");
      }

      audioCtx = new AudioContext();
      await audioCtx.resume(); // Ensure context is running
      const destination = audioCtx.createMediaStreamDestination();

      // Setup Mic Gain
      micGainNode = audioCtx.createGain();
      const micSource = audioCtx.createMediaStreamSource(micStream);
      micSource.connect(micGainNode);
      micGainNode.connect(destination);

      // Setup System Gain
      if (systemStream.getAudioTracks().length > 0) {
        sysGainNode = audioCtx.createGain();
        const sysSource = audioCtx.createMediaStreamSource(systemStream);
        sysSource.connect(sysGainNode);
        sysGainNode.connect(destination);
      } else {
        micStream.getTracks().forEach((t) => t.stop());
        systemStream.getTracks().forEach((t) => t.stop());
        throw new Error("未检测到系统音轨。请确保在共享时勾选了“共享音频”。");
      }

      combinedStream = destination.stream;
      mediaRecorder = new MediaRecorder(combinedStream, {
        mimeType: "audio/webm",
      });

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) recordedChunks.push(e.data);
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(recordedChunks, { type: "audio/webm" });
        const file = new File(
          [blob],
          `recording_${new Date().getTime()}.webm`,
          { type: "audio/webm" },
        );

        // Clean up
        micStream.getTracks().forEach((t) => t.stop());
        systemStream.getTracks().forEach((t) => t.stop());
        audioCtx.close();
        audioCtx = null;

        selectFile(file);
        showToast("✅ 录制完成", "success");
        sourceToggles.style.display = "none";
      };

      mediaRecorder.start(5000); // flush data every 5 seconds for crash safety
      isRecording = true;

      // UI Update
      startRecordBtn.disabled = true;
      startRecordBtn.classList.add("recording");
      startRecordBtn.textContent = "正在录制...";
      stopRecordBtn.disabled = false;
      micSelect.disabled = true;

      sourceToggles.style.display = "flex";
      toggleMicBtn.classList.add("active");
      toggleSysBtn.classList.add("active");

      recordTimeStart = Date.now();
      lastRecordTick = Date.now();
      recordTimer.textContent = "00:00";
      recordInterval = setInterval(() => {
        lastRecordTick = Date.now();
        const diff = Date.now() - recordTimeStart;
        const s = Math.floor(diff / 1000) % 60;
        const m = Math.floor(diff / 60000);
        recordTimer.textContent = `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
      }, 1000);

      // Register sleep detection listeners
      document.addEventListener("visibilitychange", handleSleepWake);
      window.addEventListener("beforeunload", handleBeforeUnload);
    } catch (err) {
      showToast("❌ 录制失败: " + err.message, "error");
      console.error(err);
    }
  });

  // Dynamic Toggles
  toggleMicBtn.addEventListener("click", () => {
    if (!micGainNode) return;
    const isActive = toggleMicBtn.classList.toggle("active");
    micGainNode.gain.setValueAtTime(isActive ? 1 : 0, audioCtx.currentTime);
  });

  toggleSysBtn.addEventListener("click", () => {
    if (!sysGainNode) return;
    const isActive = toggleSysBtn.classList.toggle("active");
    sysGainNode.gain.setValueAtTime(isActive ? 1 : 0, audioCtx.currentTime);
  });

  stopRecordBtn.addEventListener("click", () => {
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      mediaRecorder.stop();
    }
    clearInterval(recordInterval);
    isRecording = false;
    startRecordBtn.disabled = false;
    startRecordBtn.classList.remove("recording");
    startRecordBtn.textContent = "🔴 开始录制";
    stopRecordBtn.disabled = true;
    micSelect.disabled = false;
    // Remove sleep detection listeners
    document.removeEventListener("visibilitychange", handleSleepWake);
    window.removeEventListener("beforeunload", handleBeforeUnload);
  });

  // ── System Sleep/Hibernation Detection ────────────────────
  function handleSleepWake() {
    if (document.visibilityState === "visible" && isRecording) {
      const now = Date.now();
      const gap = now - lastRecordTick;
      if (gap > 30000) {
        console.warn(
          `[Recorder] System sleep detected (gap: ${Math.round(gap / 1000)}s). Auto-stopping recording.`,
        );
        emergencyStopRecording();
      }
    }
  }

  function handleBeforeUnload(e) {
    if (isRecording) {
      emergencyStopRecording();
      e.preventDefault();
      e.returnValue = "";
    }
  }

  function emergencyStopRecording() {
    if (!isRecording) return;
    isRecording = false;

    // Try to gracefully stop MediaRecorder
    if (mediaRecorder && mediaRecorder.state !== "inactive") {
      try {
        mediaRecorder.stop();
      } catch {
        // If stop() fails, do emergency save with existing chunks
        if (recordedChunks.length > 0) {
          const blob = new Blob(recordedChunks, { type: "audio/webm" });
          const file = new File([blob], `recording_${Date.now()}.webm`, {
            type: "audio/webm",
          });
          // Clean up streams
          micStream?.getTracks().forEach((t) => t.stop());
          systemStream?.getTracks().forEach((t) => t.stop());
          if (audioCtx) {
            audioCtx.close();
            audioCtx = null;
          }
          selectFile(file);
        }
      }
    } else if (recordedChunks.length > 0) {
      // MediaRecorder already inactive, save whatever we have
      const blob = new Blob(recordedChunks, { type: "audio/webm" });
      const file = new File([blob], `recording_${Date.now()}.webm`, {
        type: "audio/webm",
      });
      micStream?.getTracks().forEach((t) => t.stop());
      systemStream?.getTracks().forEach((t) => t.stop());
      if (audioCtx) {
        audioCtx.close();
        audioCtx = null;
      }
      selectFile(file);
    }

    clearInterval(recordInterval);
    startRecordBtn.disabled = false;
    startRecordBtn.classList.remove("recording");
    startRecordBtn.textContent = "🔴 开始录制";
    stopRecordBtn.disabled = true;
    micSelect.disabled = false;
    sourceToggles.style.display = "none";

    showToast("⚠️ 检测到系统休眠，录音已自动保存", "success");

    // Clean up listeners
    document.removeEventListener("visibilitychange", handleSleepWake);
    window.removeEventListener("beforeunload", handleBeforeUnload);
  }

  async function selectFile(file) {
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatSize(file.size);
    dropContent.style.display = "none";
    fileInfo.style.display = "flex";
    dropZone.classList.add("file-selected");

    // Load preview
    const url = URL.createObjectURL(file);
    audioPreview.src = url;

    const dur = await getAudioDuration(file);
    if (dur && isFinite(dur)) {
      fileSize.textContent =
        formatSize(file.size) + "  ·  " + formatDuration(dur * 1000);
    }

    progressCard.style.display = "none";
    resultCard.style.display = "none";
    if (pollTimer) clearInterval(pollTimer);
  }

  cancelFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    if (audioPreview.src) {
      URL.revokeObjectURL(audioPreview.src);
      audioPreview.src = "";
    }
    selectedFile = null;
    fileInput.value = "";
    fileInfo.style.display = "none";
    dropContent.style.display = "flex";
    dropZone.classList.remove("file-selected");
  });

  // ── Start Transcription ───────────────────────────────────
  startBtn.addEventListener("click", async () => {
    if (!selectedFile) return;
    if (currentTaskId) {
      showToast("⚠️ 任务进行中", "error");
      return;
    }
    startBtn.disabled = true;
    startBtn.textContent = "⏳ 上传中…";

    // Auto-close config panel
    if (!configPanel.classList.contains("collapsed")) {
      configPanel.classList.add("collapsed");
      configToggle.classList.remove("active");
    }

    const form = new FormData();
    form.append("audio", selectedFile);
    form.append("max_minutes", maxMinInput.value);
    form.append("max_mb", maxMBInput.value);
    form.append("base_url", baseUrlInput.value);
    form.append("api_key", apiKeyInput.value);
    form.append("model", modelInput.value);
    form.append("provider", providerSelect.value || "openai");
    form.append(
      "enable_diarization",
      $("diarizeToggle").checked ? "true" : "false",
    );

    try {
      const res = await fetch("/api/upload", { method: "POST", body: form });
      const data = await res.json();
      if (!data.task_id) throw new Error(data.error || "上传失败");
      currentTaskId = data.task_id;
      progressCard.style.display = "block";
      resultCard.style.display = "none";
      startTimer();
      pollStatus();
    } catch (err) {
      showToast("❌ " + err.message, "error");
    } finally {
      startBtn.disabled = false;
      startBtn.textContent = "🚀 开始转写";
    }
  });

  // ── Timer ─────────────────────────────────────────────────
  function startTimer() {
    timerStart = Date.now();
    timerDisplay.textContent = "0:00";
    timerETA.textContent = "";
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      timerDisplay.textContent = formatDuration(Date.now() - timerStart);
    }, 1000);
  }
  function stopTimer() {
    if (timerInterval) {
      clearInterval(timerInterval);
      timerInterval = null;
    }
  }

  // ── Poll Status ───────────────────────────────────────────
  function pollStatus() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(async () => {
      if (!currentTaskId) return;
      try {
        const res = await fetch(`/api/status/${currentTaskId}`);
        const d = await res.json();
        updateProgress(d);
        if (d.status === "diarizing") {
          statusBadge.textContent = "识别说话人";
          statusBadge.className = "status-badge";
          progressText.textContent = "正在分析说话人声纹...";
          progressBar.style.width = "95%";
        } else if (d.status === "done") {
          clearInterval(pollTimer);
          pollTimer = null;
          stopTimer();
          statusBadge.textContent = "完成";
          statusBadge.className = "status-badge done";
          progressBar.className = "progress-bar done";
          progressBar.style.width = "100%";
          renderTranscript(d.transcript || "");
          resultCard.style.display = "block";

          // Speaker results
          if (d.speakers && d.speakers.length > 0) {
            lastTaskId = currentTaskId;
            lastSpeakers = d.speakers;
            renderSpeakerResults(d.speakers);
            speakerCard.style.display = "block";
          }

          currentTaskId = null;
        } else if (d.status === "error") {
          clearInterval(pollTimer);
          pollTimer = null;
          stopTimer();
          statusBadge.textContent = "错误";
          statusBadge.className = "status-badge error";
          showToast("❌ 转写出错: " + (d.error || "未知错误"), "error");
          currentTaskId = null;
        }
      } catch {
        /* retry next tick */
      }
    }, 2000);
  }

  function updateProgress(d) {
    const chunks = d.chunks || [];
    const total = d.total_chunks || chunks.length || 1;
    const done = chunks.filter((c) => c.status === "done").length;
    const pct = Math.round((done / total) * 100);
    progressBar.style.width = pct + "%";
    progressBar.className = "progress-bar active";
    statusBadge.textContent = "转写中";
    statusBadge.className = "status-badge";
    progressText.textContent = `正在转写片段 ${done + (done < total ? 1 : 0)}/${total}（已完成 ${done} 个）`;

    // ETA
    if (done > 0 && done < total) {
      const elapsed = Date.now() - timerStart;
      const eta = (elapsed / done) * (total - done);
      timerETA.textContent = `预计还需 ~${formatDuration(eta)}`;
    }

    // Chunks grid
    chunksGrid.innerHTML = "";
    chunks.forEach((c, i) => {
      const tag = document.createElement("span");
      tag.className = "chunk-tag " + (c.status || "pending");
      tag.textContent = `#${i + 1}`;
      chunksGrid.appendChild(tag);
    });
  }

  // ── Render Transcript ─────────────────────────────────────
  function renderTranscript(text) {
    const speakerRegex = /【(.+?)】/g;
    const hasSpeakers = speakerRegex.test(text);

    if (!hasSpeakers) {
      transcriptOutput.innerHTML = `<div style="white-space:pre-wrap;line-height:1.8">${esc(text)}</div>`;
      return;
    }

    const colorMap = {};
    let colorIdx = 0;
    const blocks = text.split(/(?=【.+?】)/);
    let html = "";

    blocks.forEach((block) => {
      const m = block.match(/^【(.+?)】/);
      if (!m) {
        html += `<p>${boldify(esc(block.trim()))}</p>`;
        return;
      }
      const name = m[1];
      if (!colorMap[name])
        colorMap[name] = SPEAKER_COLORS[colorIdx++ % SPEAKER_COLORS.length];
      const clr = colorMap[name];
      const content = block.replace(/^【.+?】\s*/, "").trim();
      html +=
        `<div class="speaker-block" style="border-left-color:${clr}">` +
        `<span class="speaker-chip" style="background:${clr}22;color:${clr}">${esc(name)}</span>` +
        `<p>${boldify(esc(content))}</p></div>`;
    });
    transcriptOutput.innerHTML = html;
  }

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s;
    return d.innerHTML;
  }
  function boldify(s) {
    return s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  }

  // ── Copy / Download ───────────────────────────────────────
  copyBtn.addEventListener("click", async () => {
    const text = transcriptOutput.innerText;
    try {
      await navigator.clipboard.writeText(text);
      copyBtn.textContent = "✅ 已复制";
    } catch {
      showToast("❌ 复制失败", "error");
    }
    setTimeout(() => {
      copyBtn.textContent = "📋 复制";
    }, 2000);
  });

  downloadBtn.addEventListener("click", () => {
    dl(
      transcriptOutput.innerText,
      (selectedFile?.name || "transcript") + ".txt",
      "text/plain",
    );
  });
  downloadMdBtn.addEventListener("click", () => {
    dl(
      transcriptOutput.innerText,
      (selectedFile?.name || "transcript") + ".md",
      "text/markdown",
    );
  });

  function dl(content, name, mime) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([content], { type: mime }));
    a.download = name;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  // ── New Task ──────────────────────────────────────────────
  newTaskBtn.addEventListener("click", () => {
    if (audioPreview.src) {
      URL.revokeObjectURL(audioPreview.src);
      audioPreview.src = "";
    }
    selectedFile = null;
    currentTaskId = null;
    lastTaskId = null;
    lastSpeakers = [];
    fileInput.value = "";
    if (pollTimer) clearInterval(pollTimer);
    stopTimer();
    progressCard.style.display = "none";
    resultCard.style.display = "none";
    speakerCard.style.display = "none";
    fileInfo.style.display = "none";
    dropContent.style.display = "flex";
    dropZone.classList.remove("file-selected");
    progressBar.style.width = "0%";
    progressBar.className = "progress-bar";
    chunksGrid.innerHTML = "";
    transcriptOutput.innerHTML = "";
    speakerResults.innerHTML = "";
    timerDisplay.textContent = "0:00";
    timerETA.textContent = "";
    progressText.textContent = "等待开始...";
    statusBadge.textContent = "准备中";
    statusBadge.className = "status-badge";
  });

  // ── Toast ─────────────────────────────────────────────────
  function showToast(msg, type) {
    const el = document.createElement("div");
    el.className = "toast " + type;
    el.textContent = msg;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 3000);
  }

  // ── Helpers ───────────────────────────────────────────────
  function formatSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1048576) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / 1048576).toFixed(1) + " MB";
  }
  function formatDuration(ms) {
    const s = Math.floor(ms / 1000) % 60,
      m = Math.floor(ms / 60000);
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  // ── Audio Duration ────────────────────────────────────────
  function getAudioDuration(file) {
    return new Promise((resolve) => {
      const audio = new Audio();
      const t = setTimeout(() => resolve(null), 5000);
      audio.addEventListener("loadedmetadata", () => {
        clearTimeout(t);
        resolve(audio.duration);
        URL.revokeObjectURL(audio.src);
      });
      audio.addEventListener("error", () => {
        clearTimeout(t);
        resolve(null);
        URL.revokeObjectURL(audio.src);
      });
      audio.src = URL.createObjectURL(file);
    });
  }

  // ── Keyboard Shortcuts ────────────────────────────────────
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      if (selectedFile && !startBtn.disabled) startBtn.click();
    }
    if ((e.metaKey || e.ctrlKey) && e.key === "s") {
      e.preventDefault();
      saveConfigBtn.click();
    }
  });

  // ── Test Mode / Demo Files ─────────────────────────────────
  async function loadTestConfig() {
    try {
      const res = await fetch("/api/test-config");
      const cfg = await res.json();

      if (cfg.test_mode && cfg.has_config) {
        testModeBanner.style.display = "flex";

        providerSelect.value = "custom";
        baseUrlInput.value = cfg.base_url || "";
        modelInput.value = cfg.model || "";
        if (cfg.api_key_set) {
          apiKeyInput.value = "(server-env)";
          apiKeyInput.placeholder = "Already configured via .env";
        }
        pillModel.textContent = cfg.model || "Test Mode";
        pillDot.classList.add("connected");
        saveConfig();

        if (!configPanel.classList.contains("collapsed")) {
          configPanel.classList.add("collapsed");
          configToggle.classList.remove("active");
        }
      }

      if (cfg.demo_files && cfg.demo_files.length > 0) {
        demoCard.style.display = "block";
        if (demoHint) demoHint.style.display = "block";
        demoFilesGrid.innerHTML = "";
        cfg.demo_files.forEach((f) => {
          const btn = document.createElement("button");
          btn.className = "demo-file-btn";
          btn.innerHTML = `<span>\uD83C\uDFB5</span> ${esc(f.name)} <span class="demo-file-size">${f.size_mb} MB</span>`;
          btn.addEventListener("click", () => loadDemoFile(f.name));
          demoFilesGrid.appendChild(btn);
        });
      }
    } catch {
      // test-config endpoint not available, skip
    }
  }

  async function loadDemoFile(filename) {
    try {
      const res = await fetch(`/api/demo-file/${encodeURIComponent(filename)}`);
      if (!res.ok) throw new Error("Failed to fetch demo file");
      const blob = await res.blob();
      const file = new File([blob], filename, { type: blob.type });
      selectFile(file);
      showToast(
        "\u2705 \u5DF2\u52A0\u8F7D\u6D4B\u8BD5\u97F3\u9891: " + filename,
        "success",
      );
    } catch (err) {
      showToast("\u274C \u52A0\u8F7D\u5931\u8D25: " + err.message, "error");
    }
  }

  // ── Auth: Load current user & logout ────────────────────────
  const currentUsername = $("currentUsername");
  const logoutBtn = $("logoutBtn");

  async function loadCurrentUser() {
    try {
      const res = await fetch("/api/auth/me");
      if (res.ok) {
        const data = await res.json();
        if (currentUsername) currentUsername.textContent = data.username;
      } else if (res.status === 401) {
        window.location.href = "/login";
      }
    } catch {
      /* ignore */
    }
  }

  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        await fetch("/api/auth/logout", { method: "POST" });
      } catch {
        /* ignore */
      }
      window.location.href = "/login";
    });
  }

  // ── Init ──────────────────────────────────────────────────
  loadCurrentUser();
  loadConfig();
  listDevices();
  loadTestConfig();

  // Auto-select Gemini if available and no prior config
  (async () => {
    try {
      const res = await fetch("/api/builtin-providers");
      const data = await res.json();
      if (data.gemini && data.gemini.available) {
        const savedCfg = localStorage.getItem("audioTranscriberConfig");
        if (!savedCfg) {
          providerSelect.value = "gemini";
          updateProviderUI();
          saveConfig();
          // Auto-collapse config panel
          if (!configPanel.classList.contains("collapsed")) {
            configPanel.classList.add("collapsed");
            configToggle.classList.remove("active");
          }
        }
      }
    } catch {
      /* ignore */
    }
  })();

  // ── Speaker Results Rendering ──────────────────────────────
  function renderSpeakerResults(speakers) {
    speakerResults.innerHTML = "";
    speakers.forEach((s, idx) => {
      const color = SPEAKER_COLORS[idx % SPEAKER_COLORS.length];
      const card = document.createElement("div");
      card.className = "speaker-result-item";
      card.style.borderLeftColor = color;

      const nameVal = s.matched_name || s.label;
      const matchHint = s.matched_name
        ? `<span class="match-hint" style="color:${color}">🔗 匹配: ${esc(s.matched_name)} (${Math.round(s.match_similarity * 100)}%)</span>`
        : "";

      let clipsHtml = "";
      if (s.clips && s.clips.length > 0) {
        clipsHtml = s.clips
          .map(
            (c) =>
              `<button class="btn-clip" onclick="this.nextElementSibling.paused ? this.nextElementSibling.play() : this.nextElementSibling.pause()">
            ▶ ${c.duration}s
          </button>
          <audio src="/api/clips/${c.filename}" preload="none"></audio>`,
          )
          .join(" ");
      }

      card.innerHTML = `
        <div class="speaker-result-header">
          <span class="speaker-chip" style="background:${color}22;color:${color}">${esc(s.label)}</span>
          <input class="speaker-name-input" data-label="${esc(s.label)}" value="${esc(nameVal)}" placeholder="输入名称..." />
          ${matchHint}
        </div>
        <div class="speaker-result-meta">
          <span>📊 ${s.segment_count} 段 · ${s.total_duration}s</span>
          <span>${s.has_embedding ? "✅ 声纹已提取" : "⚠️ 音频太短"}</span>
        </div>
        <div class="speaker-clips">${clipsHtml}</div>
      `;
      speakerResults.appendChild(card);
    });
  }

  // ── Save Speakers ──────────────────────────────────────────
  saveSpeakersBtn.addEventListener("click", async () => {
    if (!lastTaskId || !lastSpeakers.length) {
      showToast("⚠️ 没有可保存的说话人", "error");
      return;
    }

    const speakerData = [];
    speakerResults.querySelectorAll(".speaker-name-input").forEach((input) => {
      const label = input.dataset.label;
      const name = input.value.trim() || label;
      const sp = lastSpeakers.find((s) => s.label === label);
      speakerData.push({
        label,
        name,
        matched_profile_id: sp?.matched_profile_id || null,
      });
    });

    try {
      saveSpeakersBtn.disabled = true;
      saveSpeakersBtn.textContent = "⏳ 保存中...";
      const res = await fetch("/api/speakers/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: lastTaskId, speakers: speakerData }),
      });
      const data = await res.json();
      if (data.ok) {
        // Refresh transcript with actual speaker names
        if (data.transcript) {
          renderTranscript(data.transcript);
        }
        const created = data.saved.filter((s) => s.action === "created").length;
        const updated = data.saved.filter((s) => s.action === "updated").length;
        let msg = "✅ ";
        if (created > 0) msg += `新增 ${created} 个`;
        if (created > 0 && updated > 0) msg += "，";
        if (updated > 0) msg += `更新 ${updated} 个`;
        msg += " 说话人";
        showToast(msg, "success");
        loadSpeakerLibrary();
      } else {
        showToast("❌ " + (data.error || "保存失败"), "error");
      }
    } catch (err) {
      showToast("❌ 保存失败: " + err.message, "error");
    } finally {
      saveSpeakersBtn.disabled = false;
      saveSpeakersBtn.textContent = "💾 保存到声纹库";
    }
  });

  // ── Speaker Library ────────────────────────────────────────
  async function loadSpeakerLibrary() {
    try {
      const res = await fetch("/api/speakers");
      if (!res.ok) return;
      const profiles = await res.json();
      if (!profiles.length) {
        speakerLibraryCard.style.display = "none";
        return;
      }

      speakerLibraryCard.style.display = "block";
      libraryList.innerHTML = "";

      profiles.forEach((p, idx) => {
        const color = SPEAKER_COLORS[idx % SPEAKER_COLORS.length];
        const item = document.createElement("div");
        item.className = "library-item";
        item.style.borderLeftColor = color;

        let clipsHtml = "";
        if (p.clips && p.clips.length > 0) {
          clipsHtml = p.clips
            .map(
              (c) =>
                `<button class="btn-clip" onclick="this.nextElementSibling.paused ? this.nextElementSibling.play() : this.nextElementSibling.pause()">▶ ${c.duration}s</button>
             <audio src="/api/speakers/${p.id}/clips/${c.filename}" preload="none"></audio>`,
            )
            .join(" ");
        }

        item.innerHTML = `
          <div class="library-item-header">
            <span class="speaker-chip" style="background:${color}22;color:${color}">${esc(p.name)}</span>
            <div class="library-item-actions">
              <button class="btn btn-ghost btn-xs" data-action="rename" data-id="${p.id}" title="重命名">✏️</button>
              <button class="btn btn-ghost btn-xs" data-action="delete" data-id="${p.id}" title="删除">🗑️</button>
            </div>
          </div>
          <div class="library-item-meta">
            <span>创建: ${p.created_at ? new Date(p.created_at).toLocaleDateString() : "未知"}</span>
          </div>
          <div class="speaker-clips">${clipsHtml}</div>
        `;
        libraryList.appendChild(item);
      });

      // Wire up rename/delete buttons
      libraryList.querySelectorAll("[data-action=rename]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = btn.dataset.id;
          const name = prompt("输入新名称:");
          if (!name) return;
          try {
            await fetch(`/api/speakers/${id}/name`, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ name }),
            });
            showToast("✅ 已重命名", "success");
            loadSpeakerLibrary();
          } catch {
            showToast("❌ 重命名失败", "error");
          }
        });
      });

      libraryList.querySelectorAll("[data-action=delete]").forEach((btn) => {
        btn.addEventListener("click", async () => {
          const id = btn.dataset.id;
          if (!confirm("确定要删除此说话人吗？")) return;
          try {
            await fetch(`/api/speakers/${id}`, { method: "DELETE" });
            showToast("✅ 已删除", "success");
            loadSpeakerLibrary();
          } catch {
            showToast("❌ 删除失败", "error");
          }
        });
      });
    } catch {
      /* ignore */
    }
  }

  refreshLibraryBtn.addEventListener("click", () => loadSpeakerLibrary());

  // Load library on init
  loadSpeakerLibrary();
})();
