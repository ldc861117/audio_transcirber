(() => {
  const $ = (id) => document.getElementById(id);

  // ── Toolbar & Config ──
  const configToggle = $("configToggle");
  const configPanel  = $("configPanel");
  const pillModel    = $("pillModel");
  const pillDot      = $("pillDot");

  // ── Config Form ──
  const baseUrlInput = $("baseUrl");
  const modelInput   = $("modelName");
  const apiKeyInput  = $("apiKey");
  const maxMinInput  = $("maxMinutes");
  const maxMBInput   = $("maxMB");
  const saveConfigBtn = $("saveConfigBtn");
  const testBtn      = $("testBtn");
  const testResult   = $("testResult");
  const toggleKeyVis = $("toggleKeyVisibility");

  // ── Drop Zone ──
  const dropZone     = $("dropZone");
  const dropContent  = $("dropContent");
  const fileInfo     = $("fileInfo");
  const fileInput    = $("fileInput");
  const fileName     = $("fileName");
  const fileSize     = $("fileSize");
  const cancelFileBtn = $("cancelFileBtn");
  const startBtn     = $("startBtn");

  // ── Progress ──
  const progressCard = $("progressCard");
  const statusBadge  = $("statusBadge");
  const timerDisplay = $("timerDisplay");
  const timerETA     = $("timerETA");
  const progressBar  = $("progressBar");
  const progressText = $("progressText");
  const chunksGrid   = $("chunksGrid");

  // ── Result ──
  const resultCard      = $("resultCard");
  const transcriptOutput = $("transcriptOutput");
  const copyBtn     = $("copyBtn");
  const downloadBtn = $("downloadBtn");
  const downloadMdBtn = $("downloadMdBtn");
  const newTaskBtn  = $("newTaskBtn");

  // ── State ──
  let selectedFile = null, currentTaskId = null;
  let pollTimer = null, timerInterval = null, timerStart = 0;

  const SPEAKER_COLORS = [
    "#6393ff","#f0883e","#3fb950","#bc8cff",
    "#f778ba","#56d4dd","#dbab09","#ff7b72",
  ];

  // ── Config Persistence ────────────────────────────────────
  function saveConfig() {
    const cfg = {
      baseUrl: baseUrlInput.value, model: modelInput.value,
      apiKey: apiKeyInput.value, maxMinutes: maxMinInput.value,
      maxMB: maxMBInput.value,
    };
    localStorage.setItem("audioTranscriberConfig", JSON.stringify(cfg));
    pillModel.textContent = cfg.model || "未配置";
  }

  function loadConfig() {
    const raw = localStorage.getItem("audioTranscriberConfig");
    if (!raw) {
      // First time — open config panel
      configPanel.classList.remove("collapsed");
      configToggle.classList.add("active");
      return;
    }
    const cfg = JSON.parse(raw);
    baseUrlInput.value = cfg.baseUrl || "";
    modelInput.value = cfg.model || "";
    apiKeyInput.value = cfg.apiKey || "";
    maxMinInput.value = cfg.maxMinutes || 10;
    maxMBInput.value = cfg.maxMB || 20;
    pillModel.textContent = cfg.model || "未配置";
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
  dropZone.addEventListener("dragover", (e) => { e.preventDefault(); dropZone.classList.add("drag-over"); });
  dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));
  dropZone.addEventListener("drop", (e) => {
    e.preventDefault(); dropZone.classList.remove("drag-over");
    if (e.dataTransfer.files[0]) selectFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener("change", () => { if (fileInput.files[0]) selectFile(fileInput.files[0]); });

  async function selectFile(file) {
    selectedFile = file;
    fileName.textContent = file.name;
    fileSize.textContent = formatSize(file.size);
    dropContent.style.display = "none";
    fileInfo.style.display = "flex";
    dropZone.classList.add("file-selected");

    const dur = await getAudioDuration(file);
    if (dur && isFinite(dur)) {
      fileSize.textContent = formatSize(file.size) + "  ·  " + formatDuration(dur * 1000);
    }

    progressCard.style.display = "none";
    resultCard.style.display = "none";
    if (pollTimer) clearInterval(pollTimer);
  }

  cancelFileBtn.addEventListener("click", (e) => {
    e.stopPropagation();
    selectedFile = null; fileInput.value = "";
    fileInfo.style.display = "none";
    dropContent.style.display = "flex";
    dropZone.classList.remove("file-selected");
  });

  // ── Start Transcription ───────────────────────────────────
  startBtn.addEventListener("click", async () => {
    if (!selectedFile) return;
    if (currentTaskId) { showToast("⚠️ 任务进行中", "error"); return; }
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
  function stopTimer() { if (timerInterval) { clearInterval(timerInterval); timerInterval = null; } }

  // ── Poll Status ───────────────────────────────────────────
  function pollStatus() {
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(async () => {
      if (!currentTaskId) return;
      try {
        const res = await fetch(`/api/status/${currentTaskId}`);
        const d = await res.json();
        updateProgress(d);
        if (d.status === "done") {
          clearInterval(pollTimer); pollTimer = null; stopTimer();
          statusBadge.textContent = "完成"; statusBadge.className = "status-badge done";
          progressBar.className = "progress-bar done";
          progressBar.style.width = "100%";
          renderTranscript(d.transcript || "");
          resultCard.style.display = "block";
          currentTaskId = null;
        } else if (d.status === "error") {
          clearInterval(pollTimer); pollTimer = null; stopTimer();
          statusBadge.textContent = "错误"; statusBadge.className = "status-badge error";
          showToast("❌ 转写出错: " + (d.error || "未知错误"), "error");
          currentTaskId = null;
        }
      } catch { /* retry next tick */ }
    }, 2000);
  }

  function updateProgress(d) {
    const chunks = d.chunks || [];
    const total = d.total_chunks || chunks.length || 1;
    const done = chunks.filter(c => c.status === "done").length;
    const pct = Math.round((done / total) * 100);
    progressBar.style.width = pct + "%";
    progressBar.className = "progress-bar active";
    statusBadge.textContent = "转写中"; statusBadge.className = "status-badge";
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

    blocks.forEach(block => {
      const m = block.match(/^【(.+?)】/);
      if (!m) { html += `<p>${boldify(esc(block.trim()))}</p>`; return; }
      const name = m[1];
      if (!colorMap[name]) colorMap[name] = SPEAKER_COLORS[colorIdx++ % SPEAKER_COLORS.length];
      const clr = colorMap[name];
      const content = block.replace(/^【.+?】\s*/, "").trim();
      html += `<div class="speaker-block" style="border-left-color:${clr}">` +
        `<span class="speaker-chip" style="background:${clr}22;color:${clr}">${esc(name)}</span>` +
        `<p>${boldify(esc(content))}</p></div>`;
    });
    transcriptOutput.innerHTML = html;
  }

  function esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; }
  function boldify(s) { return s.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>"); }

  // ── Copy / Download ───────────────────────────────────────
  copyBtn.addEventListener("click", async () => {
    const text = transcriptOutput.innerText;
    try { await navigator.clipboard.writeText(text); copyBtn.textContent = "✅ 已复制"; }
    catch { showToast("❌ 复制失败", "error"); }
    setTimeout(() => { copyBtn.textContent = "📋 复制"; }, 2000);
  });

  downloadBtn.addEventListener("click", () => {
    dl(transcriptOutput.innerText, (selectedFile?.name || "transcript") + ".txt", "text/plain");
  });
  downloadMdBtn.addEventListener("click", () => {
    dl(transcriptOutput.innerText, (selectedFile?.name || "transcript") + ".md", "text/markdown");
  });

  function dl(content, name, mime) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([content], { type: mime }));
    a.download = name; a.click(); URL.revokeObjectURL(a.href);
  }

  // ── New Task ──────────────────────────────────────────────
  newTaskBtn.addEventListener("click", () => {
    selectedFile = null; currentTaskId = null; fileInput.value = "";
    if (pollTimer) clearInterval(pollTimer);
    stopTimer();
    progressCard.style.display = "none";
    resultCard.style.display = "none";
    fileInfo.style.display = "none";
    dropContent.style.display = "flex";
    dropZone.classList.remove("file-selected");
    progressBar.style.width = "0%";
    progressBar.className = "progress-bar";
    chunksGrid.innerHTML = "";
    transcriptOutput.innerHTML = "";
    timerDisplay.textContent = "0:00";
    timerETA.textContent = "";
    progressText.textContent = "等待开始...";
    statusBadge.textContent = "准备中"; statusBadge.className = "status-badge";
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
    const s = Math.floor(ms / 1000) % 60, m = Math.floor(ms / 60000);
    return `${m}:${String(s).padStart(2, "0")}`;
  }

  // ── Audio Duration ────────────────────────────────────────
  function getAudioDuration(file) {
    return new Promise((resolve) => {
      const audio = new Audio();
      const t = setTimeout(() => resolve(null), 5000);
      audio.addEventListener("loadedmetadata", () => {
        clearTimeout(t); resolve(audio.duration); URL.revokeObjectURL(audio.src);
      });
      audio.addEventListener("error", () => {
        clearTimeout(t); resolve(null); URL.revokeObjectURL(audio.src);
      });
      audio.src = URL.createObjectURL(file);
    });
  }

  // ── Keyboard Shortcuts ────────────────────────────────────
  document.addEventListener("keydown", (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault(); if (selectedFile && !startBtn.disabled) startBtn.click();
    }
    if ((e.metaKey || e.ctrlKey) && e.key === "s") {
      e.preventDefault(); saveConfigBtn.click();
    }
  });

  // ── Init ──────────────────────────────────────────────────
  loadConfig();
})();
