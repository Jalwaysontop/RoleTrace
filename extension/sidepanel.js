// RoleTrace Side Panel Logic
// Communicates with content.js to read job context and fill forms

// ─────────────────────────────────────────
// CONFIG — update after Render deploy
// ─────────────────────────────────────────
const BACKEND_URL = "https://roletrace.duckdns.org";
// For local dev, comment the above and use:
// const BACKEND_URL = "http://localhost:8000";

// ─────────────────────────────────────────
// STATE
// ─────────────────────────────────────────
let currentTab = null;
let jobContext = null;
let sessionId = "";
let formFields = [];

// ─────────────────────────────────────────
// INIT — get active tab and load context
// ─────────────────────────────────────────
async function init() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    currentTab = tab;

    if (!isApplyPage(tab.url)) {
      setStatus("warn", "Not on a RoleTrace apply page");
      return;
    }

    setStatus("pulse", "Loading form context...");

    // Small delay to let content script settle
    await sleep(300);

    const response = await sendToContent({ type: "GET_JOB_CONTEXT" });

    if (!response || !response.jobContext) {
      setStatus("err", "Could not read form context");
      showError("Could not detect job context. Make sure you are on a RoleTrace apply page.");
      return;
    }

    jobContext = response.jobContext;
    sessionId = response.sessionId || "";
    formFields = response.fields || [];

    renderJobContext();
    renderFieldList();
    setStatus("ok", "Apply form detected ✓");

    document.getElementById("autofillBtn").disabled = false;
    document.getElementById("emptyState").style.display = "none";

  } catch (err) {
    console.error("Init error:", err);
    setStatus("err", "Error loading panel");
    showError("Extension error: " + err.message);
  }
}

// ─────────────────────────────────────────
// AUTOFILL FLOW
// ─────────────────────────────────────────
async function startAutofill() {
  const btn = document.getElementById("autofillBtn");
  const spin = document.getElementById("spin");
  const label = document.getElementById("btnLabel");
  const progress = document.getElementById("progressWrap");
  const bar = document.getElementById("progressBar");
  const progressLabel = document.getElementById("progressLabel");

  btn.disabled = true;
  spin.style.display = "block";
  label.textContent = "Generating answers...";
  document.getElementById("errorBanner").style.display = "none";
  document.getElementById("successBanner").style.display = "none";

  progress.style.display = "flex";
  animateBar(bar, 0, 40, 600);

  try {
    progressLabel.textContent = "Calling AI...";
    animateBar(bar, 0, 40, 800);

    const res = await fetch(BACKEND_URL + "/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job: jobContext,
        fields: formFields,
        session_id: sessionId
      })
    });

    if (!res.ok) throw new Error("Backend returned " + res.status);

    const data = await res.json();
    const filledKeys = Object.keys(data);

    // ── SEQUENTIAL ANIMATED FILL ────────────────────────────────
    progressLabel.textContent = "Filling form...";
    label.textContent = "Filling fields...";
    spin.style.display = "block";

    for (let i = 0; i < filledKeys.length; i++) {
      const key = filledKeys[i];
      const value = data[key];
      if (!value) continue;

      // Highlight current field in panel list
      setFieldState(key, "filling");
      progressLabel.textContent = `Filling: ${formatFieldName(key)}...`;

      // Animate progress bar proportionally
      const pct = 40 + ((i + 1) / filledKeys.length) * 55;
      animateBar(bar, parseFloat(bar.style.width) || 40, pct, 400);

      // Fill this field with typewriter (waits until done)
      await sendToContent({ type: "FILL_FIELD_ANIMATED", field: key, value });

      // Mark done in panel
      setFieldState(key, "done");
      await sleep(120); // small pause between fields
    }

    animateBar(bar, parseFloat(bar.style.width) || 95, 100, 300);
    await sleep(350);

    // Show success & chat box
    document.getElementById("successBanner").style.display = "block";
    document.getElementById("chatBox").style.display = "block";
    progress.style.display = "none";

    label.textContent = "✨ Autofill with AI";
    spin.style.display = "none";
    btn.disabled = false;

  } catch (err) {
    console.error("Autofill error:", err);
    progress.style.display = "none";
    showError("Autofill failed: " + err.message + ". Is the backend running?");
    label.textContent = "✨ Autofill with AI";
    spin.style.display = "none";
    btn.disabled = false;
  }
}

// ─────────────────────────────────────────
// RENDER HELPERS
// ─────────────────────────────────────────
function renderJobContext() {
  document.getElementById("jobBox").style.display = "block";
  document.getElementById("jobRole").textContent = jobContext.role || "—";
  document.getElementById("jobCompany").textContent = jobContext.company || "—";

  const skills = (jobContext.skills || "").split(",").filter(Boolean);
  const row = document.getElementById("skillsRow");
  row.innerHTML = skills.slice(0, 5).map(s =>
    `<span class="skill-tag">${esc(s.trim())}</span>`
  ).join("");
}

function renderFieldList() {
  document.getElementById("fieldsBox").style.display = "block";
  const list = document.getElementById("fieldList");
  list.innerHTML = formFields.map(f =>
    `<div class="field-item" id="fi_${f}">
       <div class="field-check" id="fc_${f}">·</div>
       <span>${formatFieldName(f)}</span>
     </div>`
  ).join("");
}

function markFieldsDone(fields) {
  fields.forEach(f => setFieldState(f, "done"));
}

function setFieldState(field, state) {
  const item = document.getElementById("fi_" + field);
  const check = document.getElementById("fc_" + field);
  if (!item || !check) return;

  item.classList.remove("field-filling", "field-done");
  check.classList.remove("done", "filling");

  if (state === "filling") {
    item.classList.add("field-filling");
    check.classList.add("filling");
    check.textContent = "…";
  } else if (state === "done") {
    item.classList.add("field-done");
    check.classList.add("done");
    check.textContent = "✓";
  }
}

function setStatus(type, text) {
  const dot = document.getElementById("statusDot");
  const txt = document.getElementById("statusText");
  txt.textContent = text;
  dot.className = "status-dot";
  if (type === "ok") dot.classList.add("dot-ok");
  else if (type === "err") dot.classList.add("dot-err");
  else if (type === "pulse") { dot.classList.add("dot-warn", "dot-pulse"); }
  else dot.classList.add("dot-warn");
}

function showError(msg) {
  const el = document.getElementById("errorBanner");
  el.textContent = "⚠ " + msg;
  el.style.display = "block";
}

// ─────────────────────────────────────────
// UTILITIES
// ─────────────────────────────────────────
function isApplyPage(url) {
  return url && (url.includes("/apply") );
}

function sendToContent(msg) {
  return new Promise((resolve) => {
    if (!currentTab) { resolve(null); return; }
    chrome.tabs.sendMessage(currentTab.id, msg, (resp) => {
      if (chrome.runtime.lastError) { resolve(null); return; }
      resolve(resp);
    });
  });
}

function animateBar(el, from, to, duration) {
  const start = performance.now();
  function step(now) {
    const p = Math.min((now - start) / duration, 1);
    el.style.width = (from + (to - from) * p) + "%";
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function formatFieldName(f) {
  return f.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

function esc(s) {
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// ─────────────────────────────────────────
// REWRITE FLOW
// ─────────────────────────────────────────
async function startRewrite() {
  const input = document.getElementById("chatInput");
  const select = document.getElementById("chatField");
  const btn = document.getElementById("rewriteBtn");
  const instruction = input.value.trim();
  
  if (!instruction) return;
  
  const spin = document.getElementById("spin");
  const progress = document.getElementById("progressWrap");
  const bar = document.getElementById("progressBar");
  const progressLabel = document.getElementById("progressLabel");
  const successBanner = document.getElementById("successBanner");
  const successTitle = document.getElementById("successTitle");
  const successText = document.getElementById("successText");
  
  input.disabled = true;
  select.disabled = true;
  btn.disabled = true;
  successBanner.style.display = "none";
  
  spin.style.display = "block";
  progress.style.display = "flex";
  progressLabel.textContent = "Reading current answers...";
  animateBar(bar, 0, 20, 400);
  
  try {
    const resp = await sendToContent({ type: "GET_FORM_VALUES" });
    const currentAnswers = resp ? resp.values : {};
    
    const targetField = select.value;
    const fieldsToRewrite = targetField === "all" ? formFields : [targetField];

    progressLabel.textContent = "Asking AI to rewrite...";
    animateBar(bar, 20, 60, 800);
    
    const res = await fetch(BACKEND_URL + "/rewrite", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        job: jobContext,
        instruction: instruction,
        current_answers: currentAnswers,
        fields: fieldsToRewrite,
        session_id: sessionId
      })
    });
    
    if (!res.ok) throw new Error("Backend returned " + res.status);
    
    const data = await res.json();
    const filledKeys = Object.keys(data);
    
    if (filledKeys.length === 0) {
      throw new Error("AI returned no changes.");
    }
    
    progressLabel.textContent = "Applying rewrites...";
    for (let i = 0; i < filledKeys.length; i++) {
      const key = filledKeys[i];
      const value = data[key];
      if (!value) continue;

      setFieldState(key, "filling");
      progressLabel.textContent = `Rewriting: ${formatFieldName(key)}...`;

      const pct = 60 + ((i + 1) / filledKeys.length) * 35;
      animateBar(bar, parseFloat(bar.style.width) || 60, pct, 400);

      await sendToContent({ type: "FILL_FIELD_ANIMATED", field: key, value });

      setFieldState(key, "done");
      await sleep(120);
    }
    
    animateBar(bar, parseFloat(bar.style.width) || 95, 100, 300);
    await sleep(350);

    successTitle.textContent = "Answers Refined!";
    successText.textContent = "The form has been updated with the rewritten content.";
    successBanner.style.display = "block";
    
    input.value = "";
    input.placeholder = "Rewrite again? (e.g. Sound more excited)";
    
  } catch (err) {
    console.error("Rewrite error:", err);
    showError("Rewrite failed: " + err.message);
  } finally {
    progress.style.display = "none";
    spin.style.display = "none";
    input.disabled = false;
    select.disabled = false;
    btn.disabled = false;
  }
}

// ─────────────────────────────────────────
// START
// ─────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  init();
  document.getElementById("autofillBtn").addEventListener("click", startAutofill);
  document.getElementById("rewriteBtn").addEventListener("click", startRewrite);
  document.getElementById("chatInput").addEventListener("keypress", (e) => {
    if (e.key === "Enter") startRewrite();
  });
});
