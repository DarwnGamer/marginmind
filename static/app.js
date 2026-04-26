const state = {
  document: null,
  session: null,
  pageNumber: 1,
  pageData: null,
  gazePoll: null,
  lastSelection: "",
  zoom: 1,
  gazeRunning: false,
  pageChangeInFlight: false,
  pendingPageDelta: 0,
  pendingPageSource: "button",
  wheelDelta: 0,
  wheelTimer: null,
  pendingWheelDelta: 0,
  lastWheelPageAt: 0,
};

const WHEEL_PAGE_THRESHOLD = 72;
const WHEEL_PAGE_COOLDOWN_MS = 360;

const setupView = document.querySelector("#setupView");
const readerView = document.querySelector("#readerView");
const notesView = document.querySelector("#notesView");
const uploadForm = document.querySelector("#uploadForm");
const pageSurface = document.querySelector("#pageSurface");
const pageLabel = document.querySelector("#pageLabel");
const docTitle = document.querySelector("#docTitle");
const gazeStatus = document.querySelector("#gazeStatus");
const toast = document.querySelector("#toast");

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = document.querySelector("#docFile").files[0];
  if (!file) return;

  const form = new FormData();
  form.append("file", file);
  showToast("正在保存文档，阅读页会显示原文档页面…");
  const documentData = await request("/api/documents", { method: "POST", body: form });

  const noteGoal = document.querySelector("#noteGoal").value.trim();
  const readerProfile = {
    purpose: document.querySelector("#readingPurpose").value,
    note_style: document.querySelector("#noteStyle").value,
  };
  const session = await request("/api/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentData.id, note_goal: noteGoal, reader_profile: readerProfile }),
  });

  state.document = documentData;
  state.session = session;
  state.pageNumber = 1;
  setupView.classList.add("hidden");
  notesView.classList.add("hidden");
  readerView.classList.remove("hidden");
  document.body.classList.add("reader-mode");
  docTitle.textContent = documentData.title || "澜页";
  updateZoomLabel();
  await renderPage();
});

document.querySelector("#prevPage").addEventListener("click", () => changePage(-1, "button"));
document.querySelector("#nextPage").addEventListener("click", () => changePage(1, "button"));
document.querySelector("#zoomOutBtn").addEventListener("click", () => changeZoom(-0.08));
document.querySelector("#zoomInBtn").addEventListener("click", () => changeZoom(0.08));
document.querySelector("#zoomResetBtn").addEventListener("click", () => setZoom(1));
document.querySelector("#fullscreenBtn").addEventListener("click", async () => {
  await document.documentElement.requestFullscreen?.();
  setTimeout(() => {
    resizeRenderedPage();
    sendLayout();
  }, 300);
});
document.querySelector("#startGazeBtn").addEventListener("click", startGaze);
document.querySelector("#stopGazeBtn").addEventListener("click", stopGaze);
document.querySelector("#notesBtn").addEventListener("click", generateNotes);
document.querySelector("#backToReader").addEventListener("click", () => {
  notesView.classList.add("hidden");
  readerView.classList.remove("hidden");
  document.body.classList.add("reader-mode");
  requestAnimationFrame(() => requestAnimationFrame(() => {
    resizeRenderedPage();
    sendLayout();
  }));
});

window.addEventListener("resize", debounce(() => {
  resizeRenderedPage();
  sendLayout();
}, 150));
document.addEventListener("selectionchange", debounce(captureSelection, 350));
document.addEventListener("keydown", (event) => {
  if (readerView.classList.contains("hidden")) return;
  if (event.key === "ArrowLeft" || event.key === "PageUp") {
    event.preventDefault();
    changePage(-1, "keyboard");
  }
  if (event.key === "ArrowRight" || event.key === "PageDown" || event.key === " ") {
    event.preventDefault();
    changePage(1, "keyboard");
  }
});
document.addEventListener("wheel", handleReaderWheel, { passive: false });

async function startGaze() {
  if (!state.session) return;
  gazeStatus.textContent = "GazeFollower 正在启动模型与摄像头…";
  startGazePolling();
  showToast("正在启动 GazeFollower。校准窗口出现后，请按提示完成校准；完成后采样才会参与笔记。");
  const result = await request("/api/gaze/start", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      session_id: state.session.id,
      camera_id: 0,
      sample_hz: 24,
      preview: false,
      calibrate: true,
    }),
  });
  gazeStatus.textContent = `GazeFollower ${result.status}，PID ${result.pid || "-"}`;
  state.gazeRunning = true;
}

async function stopGaze() {
  if (!state.session) return;
  await request("/api/gaze/stop", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: state.session.id }),
  });
  state.gazeRunning = false;
  gazeStatus.textContent = "GazeFollower 已停止";
}

function startGazePolling() {
  clearInterval(state.gazePoll);
  state.gazePoll = setInterval(async () => {
    if (!state.session) return;
    const status = await request(`/api/gaze/status/${state.session.id}`);
    state.gazeRunning = status.status === "running" && status.progress < 100 ? state.gazeRunning : status.status === "running";
    if (status.phase === "正在采样") state.gazeRunning = true;
    if (status.status === "exited" || status.phase === "未启动") state.gazeRunning = false;
    gazeStatus.textContent = `${status.phase || status.status} ${status.progress || 0}% ，样本 ${status.sample_count}`;
  }, 750);
}

async function changePage(delta, source = "button") {
  if (!state.document) return;
  if (state.pageChangeInFlight) {
    state.pendingPageDelta = delta;
    state.pendingPageSource = source;
    return;
  }

  state.pageChangeInFlight = true;
  try {
    const next = Math.min(Math.max(state.pageNumber + delta, 1), state.document.page_count || 1);
    if (next === state.pageNumber) return;
    await sendEvents([
      {
        type: "layout_change",
        reason: "page_change",
        source,
        from_page: state.pageNumber,
        to_page: next,
        ts: now(),
      },
    ]);
    state.pageNumber = next;
    await renderPage();
  } finally {
    state.pageChangeInFlight = false;
    const pendingDelta = state.pendingPageDelta;
    const pendingSource = state.pendingPageSource;
    state.pendingPageDelta = 0;
    state.pendingPageSource = "button";
    if (pendingDelta) {
      window.setTimeout(() => changePage(pendingDelta, pendingSource), 90);
    }
  }
}

function handleReaderWheel(event) {
  if (readerView.classList.contains("hidden")) return;
  event.preventDefault();
  if (!state.document || event.ctrlKey || event.metaKey) return;

  const primaryDelta = Math.abs(event.deltaY) >= Math.abs(event.deltaX) ? event.deltaY : event.deltaX;
  if (!primaryDelta) return;

  state.wheelDelta += normalizeWheelDelta(primaryDelta, event.deltaMode);
  if (Math.abs(state.wheelDelta) < WHEEL_PAGE_THRESHOLD) return;

  const delta = state.wheelDelta > 0 ? 1 : -1;
  state.wheelDelta = 0;
  queueWheelPage(delta);
}

function normalizeWheelDelta(delta, deltaMode) {
  if (deltaMode === 1) return delta * 24;
  if (deltaMode === 2) return delta * Math.max(pageSurface.clientHeight, 1);
  return delta;
}

function queueWheelPage(delta) {
  state.pendingWheelDelta = delta;
  const wait = Math.max(WHEEL_PAGE_COOLDOWN_MS - (Date.now() - state.lastWheelPageAt), 0);
  clearTimeout(state.wheelTimer);
  if (wait === 0 && !state.pageChangeInFlight) {
    flushWheelPage();
    return;
  }
  state.wheelTimer = window.setTimeout(flushWheelPage, Math.max(wait, 80));
}

function flushWheelPage() {
  const delta = state.pendingWheelDelta;
  state.pendingWheelDelta = 0;
  if (!delta) return;
  if (state.pageChangeInFlight) {
    state.pendingWheelDelta = delta;
    state.wheelTimer = window.setTimeout(flushWheelPage, 120);
    return;
  }
  state.lastWheelPageAt = Date.now();
  changePage(delta, "wheel");
}

async function renderPage() {
  state.pageData = await request(`/api/documents/${state.document.id}/page/${state.pageNumber}`);
  state.document.page_count = state.pageData.page_count;
  pageSurface.textContent = "";
  pageLabel.textContent = `第 ${state.pageData.page_number} / ${state.pageData.page_count} 页`;

  if (state.pageData.render_mode === "pdf-image") {
    renderPdfPage(state.pageData);
  } else {
    renderTextPage(state.pageData);
  }

  await sendEvents([{ type: "page_view", page_number: state.pageNumber, ts: now(), viewport: viewportMeta() }]);
  requestAnimationFrame(() => requestAnimationFrame(sendLayout));
}

function renderPdfPage(page) {
  const docPage = document.createElement("div");
  docPage.className = "doc-page";
  docPage.style.aspectRatio = `${page.source_width} / ${page.source_height}`;
  applyPageSize(docPage, page.source_width, page.source_height);

  const img = document.createElement("img");
  img.className = "doc-page-image";
  img.alt = `第 ${page.page_number} 页`;
  img.src = page.image_url;
  img.addEventListener("load", () => {
    positionPdfOverlay(docPage, page);
    sendLayout();
  }, { once: true });

  const overlay = document.createElement("div");
  overlay.className = "text-overlay";
  docPage.appendChild(img);
  docPage.appendChild(overlay);
  pageSurface.appendChild(docPage);
}

function positionPdfOverlay(docPage, page) {
  const overlay = docPage.querySelector(".text-overlay");
  overlay.textContent = "";
  for (const span of page.spans || []) {
    if (!span.source_box) continue;
    const box = span.source_box;
    const node = document.createElement("span");
    node.className = "segment pdf-segment";
    node.dataset.segmentId = `${page.page_number}-${span.id}`;
    node.textContent = span.text;
    node.style.left = `${(box.x / page.source_width) * 100}%`;
    node.style.top = `${(box.y / page.source_height) * 100}%`;
    node.style.width = `${(box.w / page.source_width) * 100}%`;
    node.style.height = `${(box.h / page.source_height) * 100}%`;
    overlay.appendChild(node);
  }
}

function renderTextPage(page) {
  const docPage = document.createElement("div");
  docPage.className = "doc-page text-doc-page";
  applyPageSize(docPage, page.source_width, page.source_height);
  const content = document.createElement("div");
  content.className = "text-page-content";
  const lines = (page.text || "").split(/\n+/).filter(Boolean);
  for (const [index, line] of lines.entries()) {
    const node = document.createElement("p");
    node.className = "segment text-segment";
    node.dataset.segmentId = `${page.page_number}-line-${index}`;
    node.textContent = line;
    content.appendChild(node);
  }
  docPage.appendChild(content);
  pageSurface.appendChild(docPage);
}

function resizeRenderedPage() {
  if (!state.pageData) return;
  const docPage = pageSurface.querySelector(".doc-page");
  if (!docPage) return;
  applyPageSize(docPage, state.pageData.source_width || 800, state.pageData.source_height || 1100);
}

function applyPageSize(node, sourceWidth, sourceHeight) {
  const maxWidth = Math.max(320, pageSurface.clientWidth - 36);
  const maxHeight = Math.max(320, pageSurface.clientHeight - 28);
  const scale = Math.min(maxWidth / sourceWidth, maxHeight / sourceHeight) * state.zoom;
  node.style.width = `${Math.floor(sourceWidth * scale)}px`;
  node.style.height = `${Math.floor(sourceHeight * scale)}px`;
}

async function changeZoom(delta) {
  await setZoom(Math.min(1.35, Math.max(0.82, state.zoom + delta)));
}

async function setZoom(value) {
  state.zoom = value;
  updateZoomLabel();
  if (state.session) {
    await sendEvents([{ type: "layout_change", reason: "zoom", zoom: state.zoom, page_number: state.pageNumber, ts: now() }]);
  }
  resizeRenderedPage();
  setTimeout(sendLayout, 120);
  showToast("已调整显示大小。调整附近的短暂视线样本会被忽略，以保持轨迹对齐。");
}

function updateZoomLabel() {
  document.querySelector("#zoomResetBtn").textContent = `${Math.round(state.zoom * 100)}%`;
}

async function sendLayout() {
  if (!state.session || !state.document || !state.pageData || readerView.classList.contains("hidden")) return;
  const spans = [...pageSurface.querySelectorAll(".segment")].map((node) => ({
    id: node.dataset.segmentId,
    page_number: state.pageNumber,
    text: node.textContent,
    boxes: [...node.getClientRects()].map((rect) => ({
      x: rect.left,
      y: rect.top,
      w: rect.width,
      h: rect.height,
    })),
  })).filter((span) => span.boxes.length > 0);

  await request(`/api/sessions/${state.session.id}/page-layout`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      page_number: state.pageNumber,
      viewport: viewportMeta(),
      spans,
      ts: now(),
    }),
  });
}

async function captureSelection() {
  if (!state.session || readerView.classList.contains("hidden")) return;
  const selection = window.getSelection();
  const text = selection?.toString().trim() || "";
  if (!text || text.length < 2 || text === state.lastSelection) return;
  if (!pageSurface.contains(selection.anchorNode) || !pageSurface.contains(selection.focusNode)) return;
  state.lastSelection = text;
  await sendEvents([{ type: "text_selection", page_number: state.pageNumber, text, ts: now() }]);
  showToast("已记录主动标注。它会作为附加信号，不会替代视线追踪。");
}

async function generateNotes() {
  if (!state.session) return;
  showToast("正在停止摄像头并生成笔记…");
  await sendLayout();
  if (state.gazeRunning) {
    await stopGaze();
  }
  showToast("正在后台解析原文、叠合视线轨迹并生成笔记…");
  const result = await request(`/api/sessions/${state.session.id}/notes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      note_goal: document.querySelector("#noteGoal").value.trim(),
      use_ai: true,
    }),
  });
  readerView.classList.add("hidden");
  notesView.classList.remove("hidden");
  document.body.classList.remove("reader-mode");
  const readPages = result.read_pages?.length ? `，提交页：${result.read_pages.join(", ")}` : "，未检测到稳定阅读页";
  document.querySelector("#notesProvider").textContent = `阅读笔记（${result.provider}${readPages}）`;
  document.querySelector("#notesOutput").textContent = result.notes;
}

async function sendEvents(events) {
  if (!state.session || events.length === 0) return;
  await request(`/api/sessions/${state.session.id}/events`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ events }),
  });
}

function viewportMeta() {
  return {
    inner_width: window.innerWidth,
    inner_height: window.innerHeight,
    outer_width: window.outerWidth,
    outer_height: window.outerHeight,
    screen_left: window.screenX ?? window.screenLeft ?? 0,
    screen_top: window.screenY ?? window.screenTop ?? 0,
    device_pixel_ratio: window.devicePixelRatio || 1,
    fullscreen: Boolean(document.fullscreenElement),
  };
}

async function request(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let message = response.statusText;
    try {
      const data = await response.json();
      message = data.detail || message;
    } catch {
      message = await response.text();
    }
    showToast(message);
    throw new Error(message);
  }
  return response.json();
}

function now() {
  return Date.now() / 1000;
}

function debounce(fn, wait) {
  let timer = null;
  return (...args) => {
    clearTimeout(timer);
    timer = setTimeout(() => fn(...args), wait);
  };
}

function showToast(message) {
  toast.textContent = message;
  toast.classList.remove("hidden");
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => toast.classList.add("hidden"), 4200);
}
