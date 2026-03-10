/* ═══════════════════════════════════════════
   MalariaVision – Client-side Logic
   ═══════════════════════════════════════════ */
(() => {
  "use strict";

  // ── DOM refs ──
  const dropzone       = document.getElementById("dropzone");
  const dropzoneIdle   = document.getElementById("dropzone-idle");
  const dropzonePreview= document.getElementById("dropzone-preview");
  const previewImg     = document.getElementById("preview-img");
  const fileInput      = document.getElementById("file-input");
  const btnRemove      = document.getElementById("btn-remove");
  const btnAnalyze     = document.getElementById("btn-analyze");
  const btnText        = btnAnalyze.querySelector(".btn-text");
  const spinner        = document.getElementById("spinner");
  const resultsCard    = document.getElementById("results-card");
  const errorCard      = document.getElementById("error-card");
  const errorMsg       = document.getElementById("error-msg");
  const btnNew         = document.getElementById("btn-new");
  const btnErrorDismiss= document.getElementById("btn-error-dismiss");

  // Result elements
  const resultIcon     = document.getElementById("result-icon");
  const resultLabel    = document.getElementById("result-label");
  const confValue      = document.getElementById("conf-value");
  const confBarFill    = document.getElementById("conf-bar-fill");
  const probParasitized= document.getElementById("prob-parasitized");
  const probUninfected = document.getElementById("prob-uninfected");

  const ALLOWED_EXT    = new Set(["png", "jpg", "jpeg", "bmp", "tiff"]);
  const MAX_SIZE       = 16 * 1024 * 1024; // 16 MB

  let selectedFile = null;

  // ── Helpers ──
  const show  = (el) => el.classList.remove("hidden");
  const hide  = (el) => el.classList.add("hidden");

  function getExt(name) {
    const parts = name.split(".");
    return parts.length > 1 ? parts.pop().toLowerCase() : "";
  }

  function validateFile(file) {
    if (!file) return "No file selected.";
    const ext = getExt(file.name);
    if (!ALLOWED_EXT.has(ext)) return `File type ".${ext}" is not supported. Use PNG, JPG, JPEG, BMP, or TIFF.`;
    if (file.size > MAX_SIZE) return `File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Max is 16 MB.`;
    return null;
  }

  // ── File selection ──
  function handleFile(file) {
    const err = validateFile(file);
    if (err) { showError(err); return; }

    selectedFile = file;
    const reader = new FileReader();
    reader.onload = (e) => {
      previewImg.src = e.target.result;
      hide(dropzoneIdle);
      show(dropzonePreview);
      btnAnalyze.disabled = false;
    };
    reader.readAsDataURL(file);

    // Hide previous results
    hide(resultsCard);
    hide(errorCard);
  }

  function clearFile() {
    selectedFile = null;
    fileInput.value = "";
    previewImg.src = "";
    show(dropzoneIdle);
    hide(dropzonePreview);
    btnAnalyze.disabled = true;
    hide(resultsCard);
    hide(errorCard);
  }

  // ── Drag & drop ──
  dropzone.addEventListener("click", () => fileInput.click());
  dropzone.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") fileInput.click(); });
  fileInput.addEventListener("change", () => { if (fileInput.files[0]) handleFile(fileInput.files[0]); });
  btnRemove.addEventListener("click", (e) => { e.stopPropagation(); clearFile(); });

  ["dragenter", "dragover"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.add("drag-over"); })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => { e.preventDefault(); dropzone.classList.remove("drag-over"); })
  );
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  });

  // ── Prediction ──
  async function predict() {
    if (!selectedFile) return;

    // UI → loading
    btnAnalyze.disabled = true;
    btnText.textContent = "Analyzing…";
    show(spinner);
    hide(resultsCard);
    hide(errorCard);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch("/predict", { method: "POST", body: formData });
      const data = await response.json();

      if (!response.ok) {
        showError(data.error || `Server error (${response.status})`);
        return;
      }

      showResults(data);
    } catch (err) {
      showError("Unable to reach the server. Make sure the Flask backend is running.");
    } finally {
      // Restore button
      btnAnalyze.disabled = false;
      btnText.textContent = "Analyze Image";
      hide(spinner);
    }
  }

  btnAnalyze.addEventListener("click", predict);

  // ── Show results ──
  function showResults(data) {
    const isParasitized = data.label === "Parasitized";
    const pct = (data.confidence * 100).toFixed(1);

    resultIcon.textContent = isParasitized ? "🦟" : "✅";
    resultLabel.textContent = data.label;
    resultLabel.className = "result-label " + (isParasitized ? "parasitized" : "uninfected");

    confValue.textContent = pct + "%";
    confBarFill.className = "conf-bar-fill " + (isParasitized ? "parasitized" : "uninfected");

    // Animate bar (requestAnimationFrame for transition trigger)
    confBarFill.style.width = "0";
    requestAnimationFrame(() => {
      requestAnimationFrame(() => { confBarFill.style.width = pct + "%"; });
    });

    probParasitized.textContent = (data.parasitized_probability * 100).toFixed(2) + "%";
    probUninfected.textContent  = (data.uninfected_probability * 100).toFixed(2) + "%";

    // Glow effect on the card
    resultsCard.style.boxShadow = isParasitized
      ? "var(--shadow-card), var(--shadow-glow-red)"
      : "var(--shadow-card), var(--shadow-glow-teal)";

    hide(errorCard);
    show(resultsCard);

    // Scroll to results on mobile
    if (window.innerWidth <= 900) {
      resultsCard.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }

  // ── Error display ──
  function showError(msg) {
    errorMsg.textContent = msg;
    hide(resultsCard);
    show(errorCard);
  }

  // ── Reset buttons ──
  btnNew.addEventListener("click", clearFile);
  btnErrorDismiss.addEventListener("click", () => { hide(errorCard); });

  // ── Navbar shrink on scroll ──
  const navbar = document.getElementById("navbar");
  let ticking = false;
  window.addEventListener("scroll", () => {
    if (!ticking) {
      requestAnimationFrame(() => {
        navbar.style.background = window.scrollY > 60
          ? "rgba(11, 15, 25, 0.92)"
          : "rgba(11, 15, 25, 0.75)";
        ticking = false;
      });
      ticking = true;
    }
  });
})();
