// RoleTrace Content Script
// Injected into apply pages to expose job context + animated field filling

(function () {

  // ─── GET FORM FIELDS ────────────────────────────────────────
  function getFormFields() {
    return Array.from(document.querySelectorAll("[data-field]"))
      .map(el => el.getAttribute("data-field"));
  }


  // ─── TYPEWRITER ENGINE ──────────────────────────────────────
  // Types text into an element character-by-character.
  // Speed adapts so any text finishes in ~1.8s (min 18ms/char).
  function typewriterFill(el, text) {
    return new Promise(resolve => {
      el.value = "";
      el.style.transition = "box-shadow 0.3s ease, border-color 0.3s ease";
      el.style.boxShadow = "0 0 0 3px rgba(124, 58, 237, 0.25)";
      el.style.borderColor = "#7c3aed";

      const chars = text.split("");
      const totalMs = Math.max(chars.length * 18, 600);
      const delay = Math.min(totalMs / chars.length, 40);

      let i = 0;
      function typeNext() {
        if (i >= chars.length) {
          // Pulse green on completion
          el.style.boxShadow = "0 0 0 3px rgba(16, 185, 129, 0.3)";
          el.style.borderColor = "#10b981";
          el.dispatchEvent(new Event("input", { bubbles: true }));
          el.dispatchEvent(new Event("change", { bubbles: true }));
          setTimeout(() => {
            el.style.boxShadow = "";
            el.style.borderColor = "";
            resolve();
          }, 350);
          return;
        }
        el.value += chars[i++];
        el.dispatchEvent(new Event("input", { bubbles: true }));
        setTimeout(typeNext, delay + Math.random() * 10); // slight jitter
      }
      typeNext();
    });
  }


  // ─── FILL ONE FIELD (animated) ──────────────────────────────
  async function fillOneField(fieldKey, value) {
    const el = document.querySelector(`[data-field="${fieldKey}"]`);
    if (!el || !value) return false;

    // Scroll field into view smoothly
    el.scrollIntoView({ behavior: "smooth", block: "center" });
    await new Promise(r => setTimeout(r, 250)); // wait for scroll

    await typewriterFill(el, value);
    return true;
  }


  // ─── MESSAGE LISTENER ───────────────────────────────────────
  chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {

    if (msg.type === "GET_JOB_CONTEXT") {
      sendResponse({
        jobContext: window.jobContext || null,
        sessionId: window.__roletrace_session || "",
        fields: getFormFields()
      });
    }

    if (msg.type === "GET_FORM_VALUES") {
      const values = {};
      getFormFields().forEach(f => {
        const el = document.querySelector(`[data-field="${f}"]`);
        if (el) values[f] = el.value;
      });
      sendResponse({ values });
    }

    // Animated: fill one field at a time (called sequentially from sidepanel.js)
    if (msg.type === "FILL_FIELD_ANIMATED") {
      fillOneField(msg.field, msg.value).then(ok => {
        sendResponse({ ok });
      });
      return true; // keep channel open for async response
    }

    // Legacy instant fill (kept as fallback)
    if (msg.type === "FILL_FORM") {
      let filled = 0;
      for (const [key, value] of Object.entries(msg.data)) {
        const el = document.querySelector(`[data-field="${key}"]`);
        if (el && value) { el.value = value; filled++; }
      }
      sendResponse({ filled });
    }
  });

  window.__roletrace_ready = true;
})();
