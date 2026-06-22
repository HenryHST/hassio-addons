(function () {
  "use strict";

  const NUTRIENT_LABELS = {
    ENERCC: "Energie (kcal)",
    ENERCJ: "Energie (kJ)",
    CHO: "Kohlenhydrate (g)",
    FAT: "Fett (g)",
    PROT625: "Protein (g)",
    FIBT: "Ballaststoffe (g)",
    NACL: "Salz (g)",
    WATER: "Wasser (g)",
  };

  const SEARCH_LIMIT = 10;
  const SEARCH_MIN_CHARS = 2;
  const SEARCH_DEBOUNCE_MS = 300;
  const RECENTS_KEY = "bls_recents";
  const RECENTS_MAX = 5;
  const THEME_KEY = "bls_theme";
  const PORTION_CHIPS = [50, 100, 150];

  let barcodeProduct = null;
  let offEnabled = true;
  let todoListEnabled = false;
  let searchRecentsEnabled = true;
  let searchAbortController = null;
  let searchDebounceTimer = null;
  let ingredientCounter = 0;
  let scanStream = null;
  let scanFrameId = null;
  let barcodeDetector = null;

  const $ = (id) => document.getElementById(id);

  function formatNum(value) {
    if (value === null || value === undefined) return "—";
    const n = Number(value);
    if (Number.isNaN(n)) return "—";
    return n.toLocaleString("de-DE", { maximumFractionDigits: 2 });
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text ?? "";
    return div.innerHTML;
  }

  function showStatus(message, isError) {
    const el = $("error-msg");
    if (!message) {
      el.hidden = true;
      el.textContent = "";
      el.classList.remove("status-success");
      return;
    }
    el.textContent = message;
    el.hidden = false;
    el.classList.toggle("status-success", isError === false);
  }

  function showError(message) {
    if (!message) {
      showStatus(null);
      return;
    }
    showStatus(message, true);
  }

  async function apiGet(path, signal) {
    const res = await fetch(path, signal ? { signal } : undefined);
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch (_) { /* ignore */ }
      throw new Error(detail);
    }
    return res.json();
  }

  async function apiPost(path, data) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch (_) { /* ignore */ }
      throw new Error(detail);
    }
    return res.json();
  }

  // --- Theme ---

  const THEME_META_COLORS = { light: "#1b5e20", dark: "#121212", auto: "#1b5e20" };
  const THEME_ICONS = { auto: "◐", light: "☀", dark: "☾" };

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(THEME_KEY, theme);
    const meta = $("meta-theme-color");
    if (meta) meta.content = THEME_META_COLORS[theme] || THEME_META_COLORS.auto;
    const icon = $("theme-toggle-icon");
    if (icon) icon.textContent = THEME_ICONS[theme] || THEME_ICONS.auto;
  }

  function cycleTheme() {
    const order = ["auto", "light", "dark"];
    const current = localStorage.getItem(THEME_KEY) || "auto";
    const next = order[(order.indexOf(current) + 1) % order.length];
    applyTheme(next);
  }

  function initTheme() {
    applyTheme(localStorage.getItem(THEME_KEY) || "auto");
    $("theme-toggle")?.addEventListener("click", cycleTheme);
  }

  // --- Recents ---

  function loadRecents() {
    try {
      const raw = sessionStorage.getItem(RECENTS_KEY);
      const data = raw ? JSON.parse(raw) : [];
      return Array.isArray(data) ? data : [];
    } catch (_) {
      return [];
    }
  }

  function saveRecent(entry) {
    if (!searchRecentsEnabled) return;
    const recents = loadRecents().filter(
      (r) => !(r.source === entry.source && r.id === entry.id && r.amount_g === entry.amount_g)
    );
    recents.unshift(entry);
    sessionStorage.setItem(RECENTS_KEY, JSON.stringify(recents.slice(0, RECENTS_MAX)));
    renderRecents();
  }

  function renderRecents() {
    const wrap = $("search-recents");
    const chips = $("search-recents-chips");
    if (!wrap || !chips) return;
    if (!searchRecentsEnabled) {
      wrap.hidden = true;
      return;
    }
    const recents = loadRecents();
    if (!recents.length) {
      wrap.hidden = true;
      return;
    }
    wrap.hidden = false;
    chips.innerHTML = "";
    for (const r of recents) {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "recent-chip";
      btn.textContent = `${r.name} · ${r.amount_g} g`;
      btn.addEventListener("click", () => {
        runQuickPortion(
          { source: r.source, id: r.id, name: r.name, brand: r.brand },
          r.amount_g,
          false
        );
      });
      chips.appendChild(btn);
    }
  }

  // --- Todo / Scores ---

  function todoCartIconHtml() {
    return (
      '<svg class="btn-todo-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" ' +
      'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" ' +
      'stroke-linejoin="round" aria-hidden="true">' +
      '<circle cx="9" cy="21" r="1"/>' +
      '<circle cx="20" cy="21" r="1"/>' +
      '<path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6"/>' +
      "</svg>"
    );
  }

  function createTodoButton(product) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-todo";
    btn.innerHTML =
      todoCartIconHtml() + '<span class="btn-todo-label">Zur Einkaufsliste</span>';
    btn.addEventListener("click", (event) => {
      event.stopPropagation();
      event.preventDefault();
      addToTodoList(product);
    });
    return btn;
  }

  async function addToTodoList(product) {
    if (!product?.name) return;
    showStatus(null);
    try {
      await apiPost("todo-list/items", {
        name: product.name,
        barcode: product.id || product.barcode || null,
        brand: product.brand || null,
      });
      showStatus(`„${product.name}" zur Einkaufsliste hinzugefügt.`, false);
    } catch (err) {
      showStatus(err.message, true);
    }
  }

  function scoreBadgeItem(label, imgHtml) {
    return (
      `<span class="score-badge-item">` +
      `<span class="score-badge-label">${escapeHtml(label)}</span>` +
      imgHtml +
      `</span>`
    );
  }

  function renderScoreBadges(scores) {
    if (!scores) return "";
    const parts = [];
    if (scores.nutriscore) {
      parts.push(
        scoreBadgeItem(
          "Nutri-Score",
          `<img class="score-badge" src="static/assets/scores/nutriscore-${escapeHtml(scores.nutriscore.toLowerCase())}.svg" alt="Nutri-Score ${escapeHtml(scores.nutriscore.toUpperCase())}">`
        )
      );
    }
    if (scores.nova_group) {
      parts.push(
        scoreBadgeItem(
          "Nova",
          `<img class="score-badge" src="static/assets/scores/nova-${escapeHtml(String(scores.nova_group))}.svg" alt="Nova ${escapeHtml(String(scores.nova_group))}">`
        )
      );
    }
    if (scores.ecoscore) {
      parts.push(
        scoreBadgeItem(
          "Eco-Score",
          `<img class="score-badge" src="static/assets/scores/ecoscore-${escapeHtml(scores.ecoscore.toLowerCase())}.svg" alt="Eco-Score ${escapeHtml(scores.ecoscore.toUpperCase())}">`
        )
      );
    }
    if (!parts.length) return "";
    return `<span class="score-badges">${parts.join("")}</span>`;
  }

  function updateHeroTiles(diabetes) {
    const mapping = [
      ["val-gkh", "tile-gkh", diabetes.g_kh],
      ["val-be", "tile-be", diabetes.be],
      ["val-ke", "tile-ke", diabetes.ke],
      ["val-fpe", "tile-fpe", diabetes.fpe],
    ];
    for (const [valId, tileId, value] of mapping) {
      $(valId).textContent = formatNum(value);
      const tile = $(tileId);
      tile.classList.remove("tile-updated");
      void tile.offsetWidth;
      tile.classList.add("tile-updated");
    }
  }

  function showDetails(result) {
    const section = $("details-section");
    const nameEl = $("result-name");
    const rowsEl = $("nutrient-rows");
    const toggle = $("details-toggle");
    const content = $("details-content");

    const parts = [];
    if (result.name) parts.push(result.name);
    if (result.amount_g) parts.push(`${formatNum(result.amount_g)} g`);
    if (result.servings && result.servings > 1) {
      parts.push(`${result.servings} Portionen`);
    }
    nameEl.textContent = parts.join(" · ") || "Ergebnis";

    const scoresEl = $("result-scores");
    if (scoresEl) {
      scoresEl.innerHTML = renderScoreBadges(result);
      scoresEl.hidden = !scoresEl.innerHTML;
    }

    const todoEl = $("result-todo-action");
    if (todoEl) {
      todoEl.innerHTML = "";
      if (todoListEnabled && result.source === "off" && result.name) {
        todoEl.appendChild(
          createTodoButton({
            name: result.name,
            id: result.id,
            brand: result.brand || null,
          })
        );
        todoEl.hidden = false;
      } else {
        todoEl.hidden = true;
      }
    }

    rowsEl.innerHTML = "";
    const nutrients = result.nutrients || {};
    const order = ["ENERCC", "PROT625", "FAT", "CHO", "FIBT", "NACL"];
    for (const code of order) {
      const value = nutrients[code];
      if (value === null || value === undefined) continue;
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${NUTRIENT_LABELS[code] || code}</td><td>${formatNum(value)}</td>`;
      rowsEl.appendChild(tr);
    }

    section.hidden = false;
    toggle.setAttribute("aria-expanded", "false");
    content.hidden = true;
  }

  async function runQuickPortion(item, amount, saveToRecents = true) {
    const amountG = parseFloat(amount);
    if (!item?.id || !amountG || amountG <= 0) {
      showError("Bitte eine gültige Menge eingeben.");
      return;
    }
    showError(null);
    try {
      const result = await apiPost("calculate/portion", {
        source: item.source || "bls",
        id: item.id,
        amount_g: amountG,
      });
      updateHeroTiles(result.diabetes);
      showDetails(result);
      if (saveToRecents) {
        saveRecent({
          name: item.name || item.id,
          source: item.source || "bls",
          id: item.id,
          amount_g: amountG,
          brand: item.brand || null,
        });
      }
      showStatus(`${item.name || item.id}: ${amountG} g berechnet.`, false);
    } catch (err) {
      showError(err.message);
    }
  }

  function createQuickPortionPanel(item) {
    const panel = document.createElement("div");
    panel.className = "quick-portion";
    panel.hidden = true;

    const chips = document.createElement("div");
    chips.className = "portion-chips";
    for (const amt of PORTION_CHIPS) {
      const chip = document.createElement("button");
      chip.type = "button";
      chip.className = "portion-chip";
      chip.textContent = `${amt} g`;
      chip.addEventListener("click", (e) => {
        e.stopPropagation();
        runQuickPortion(item, amt);
      });
      chips.appendChild(chip);
    }
    panel.appendChild(chips);

    const custom = document.createElement("div");
    custom.className = "portion-custom";
    const input = document.createElement("input");
    input.type = "number";
    input.className = "input input-narrow portion-custom-input";
    input.value = "100";
    input.min = "1";
    input.step = "1";
    input.setAttribute("aria-label", "Menge in Gramm");
    const calcBtn = document.createElement("button");
    calcBtn.type = "button";
    calcBtn.className = "btn btn-primary btn-sm";
    calcBtn.textContent = "Berechnen";
    calcBtn.addEventListener("click", (e) => {
      e.stopPropagation();
      runQuickPortion(item, input.value);
    });
    custom.appendChild(input);
    custom.appendChild(calcBtn);
    panel.appendChild(custom);

    return panel;
  }

  function collapseAllResults(container) {
    container.querySelectorAll(".result-item-wrap.is-expanded").forEach((wrap) => {
      wrap.classList.remove("is-expanded");
      const panel = wrap.querySelector(".quick-portion");
      if (panel) panel.hidden = true;
    });
  }

  function renderSkeletonList(container, count) {
    container.innerHTML = "";
    for (let i = 0; i < count; i++) {
      const li = document.createElement("li");
      li.className = "skeleton-item";
      li.innerHTML = '<div class="skeleton-line"></div><div class="skeleton-line short"></div>';
      container.appendChild(li);
    }
  }

  function renderResultList(container, items, emptyMessage, showScores) {
    container.innerHTML = "";
    if (!items.length) {
      const li = document.createElement("li");
      li.innerHTML = `<p class="result-item-meta">${escapeHtml(emptyMessage)}</p>`;
      container.appendChild(li);
      return;
    }
    for (const item of items) {
      const wrap = document.createElement("li");
      wrap.className = "result-item-wrap";

      const button = document.createElement("button");
      button.type = "button";
      button.className = "result-item";
      const meta = item.brand
        ? `${escapeHtml(item.id)} · ${escapeHtml(item.brand)}`
        : escapeHtml(item.id);
      const scoresHtml = showScores ? renderScoreBadges(item) : "";
      button.innerHTML =
        `<span class="result-item-name">${escapeHtml(item.name)}</span>` +
        `<span class="result-item-meta">${meta}</span>` +
        scoresHtml;

      const quickPanel = createQuickPortionPanel(item);
      button.addEventListener("click", () => {
        const wasExpanded = wrap.classList.contains("is-expanded");
        collapseAllResults(container.closest(".result-list") || container);
        if (!wasExpanded) {
          wrap.classList.add("is-expanded");
          quickPanel.hidden = false;
        }
      });

      wrap.appendChild(button);
      wrap.appendChild(quickPanel);

      if (showScores && todoListEnabled) {
        const actions = document.createElement("div");
        actions.className = "result-item-actions";
        actions.appendChild(createTodoButton(item));
        wrap.appendChild(actions);
      }
      container.appendChild(wrap);
    }
  }

  // --- Search ---

  async function performSearch(query) {
    const grid = $("search-results-grid");
    const blsList = $("search-results-bls");
    const offList = $("search-results-off");

    if (query.length < SEARCH_MIN_CHARS) {
      grid.hidden = true;
      return;
    }

    if (searchAbortController) searchAbortController.abort();
    searchAbortController = new AbortController();
    const signal = searchAbortController.signal;

    blsList.innerHTML = "";
    offList.innerHTML = "";
    grid.hidden = false;

    const btn = $("search-form")?.querySelector("button[type=submit]");
    if (btn) btn.disabled = true;

    if (offEnabled) renderSkeletonList(offList, 3);

    try {
      const blsResults = await apiGet(
        `foods/search?q=${encodeURIComponent(query)}&limit=${SEARCH_LIMIT}`,
        signal
      );
      if (signal.aborted) return;
      renderResultList(blsList, blsResults, "Keine Treffer.", false);

      if (!offEnabled) {
        renderResultList(offList, [], "Open Food Facts deaktiviert.", false);
      } else {
        try {
          const offResults = await apiGet(
            `foods/search/off?q=${encodeURIComponent(query)}&limit=${SEARCH_LIMIT}`,
            signal
          );
          if (signal.aborted) return;
          renderResultList(offList, offResults, "Keine OFF-Treffer für diese Suche.", true);
        } catch (offErr) {
          if (offErr.name === "AbortError") return;
          renderResultList(
            offList,
            [],
            offErr.message || "Open Food Facts nicht erreichbar.",
            false
          );
        }
      }
    } catch (err) {
      if (err.name === "AbortError") return;
      showError(err.message);
      grid.hidden = true;
    } finally {
      if (!signal.aborted && btn) btn.disabled = false;
    }
  }

  function handleSearchSubmit(event) {
    event.preventDefault();
    showError(null);
    performSearch($("search-query").value.trim());
  }

  function initLiveSearch() {
    $("search-query")?.addEventListener("input", () => {
      clearTimeout(searchDebounceTimer);
      const query = $("search-query").value.trim();
      searchDebounceTimer = setTimeout(() => {
        showError(null);
        performSearch(query);
      }, SEARCH_DEBOUNCE_MS);
    });
  }

  // --- Barcode / Camera ---

  function canUseBarcodeScanner() {
    return (
      typeof BarcodeDetector !== "undefined" &&
      navigator.mediaDevices &&
      typeof navigator.mediaDevices.getUserMedia === "function"
    );
  }

  function updateScannerAvailability() {
    const unsupported = $("barcode-scanner-unsupported");
    const startBtn = $("barcode-scan-start");
    if (!unsupported || !startBtn) return;
    const available = canUseBarcodeScanner();
    unsupported.hidden = available;
    startBtn.disabled = !available;
  }

  function stopBarcodeScan() {
    if (scanFrameId) {
      cancelAnimationFrame(scanFrameId);
      scanFrameId = null;
    }
    if (scanStream) {
      scanStream.getTracks().forEach((t) => t.stop());
      scanStream = null;
    }
    const video = $("barcode-video");
    if (video) video.srcObject = null;
    const wrap = $("barcode-scanner-wrap");
    if (wrap) wrap.hidden = true;
  }

  async function startBarcodeScan() {
    if (!canUseBarcodeScanner()) {
      showError("Kamera-Scan wird von diesem Browser nicht unterstützt.");
      return;
    }
    stopBarcodeScan();
    showError(null);

    try {
      const formats = await BarcodeDetector.getSupportedFormats();
      const wanted = ["ean_13", "ean_8", "upc_a", "upc_e"].filter((f) =>
        formats.includes(f)
      );
      if (!wanted.length) {
        showError("EAN-Barcodes werden von diesem Browser nicht unterstützt.");
        return;
      }
      barcodeDetector = new BarcodeDetector({ formats: wanted });
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: { ideal: "environment" } },
        audio: false,
      });
      scanStream = stream;
      const video = $("barcode-video");
      video.srcObject = stream;
      await video.play();
      $("barcode-scanner-wrap").hidden = false;

      const tick = async () => {
        if (!barcodeDetector || !video.videoWidth) {
          scanFrameId = requestAnimationFrame(tick);
          return;
        }
        try {
          const codes = await barcodeDetector.detect(video);
          if (codes.length > 0 && codes[0].rawValue) {
            const code = codes[0].rawValue.replace(/\D/g, "");
            stopBarcodeScan();
            $("barcode-input").value = code;
            await lookupBarcodeByCode(code);
            return;
          }
        } catch (_) { /* ignore frame errors */ }
        scanFrameId = requestAnimationFrame(tick);
      };
      scanFrameId = requestAnimationFrame(tick);
    } catch (err) {
      stopBarcodeScan();
      showError(err.message || "Kamera konnte nicht gestartet werden.");
    }
  }

  async function lookupBarcodeByCode(barcode) {
    if (!barcode) return;
    showError(null);
    const btn = $("barcode-form")?.querySelector("button[type=submit]");
    if (btn) btn.disabled = true;
    $("barcode-result").hidden = true;
    $("barcode-portion-form").hidden = true;
    barcodeProduct = null;

    try {
      const product = await apiGet(`foods/barcode/${encodeURIComponent(barcode)}`);
      barcodeProduct = product;
      const resultEl = $("barcode-result");
      resultEl.hidden = false;
      resultEl.innerHTML =
        `<strong>${escapeHtml(product.name || "Unbekannt")}</strong>` +
        (product.brand ? `<br><span class="result-item-meta">${escapeHtml(product.brand)}</span>` : "") +
        renderScoreBadges(product);
      if (todoListEnabled) {
        const actions = document.createElement("div");
        actions.className = "result-item-actions";
        actions.appendChild(createTodoButton(product));
        resultEl.appendChild(actions);
      }
      $("barcode-portion-form").hidden = false;
    } catch (err) {
      showError(err.message);
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  async function handleBarcodeLookup(event) {
    event.preventDefault();
    stopBarcodeScan();
    await lookupBarcodeByCode($("barcode-input").value.trim());
  }

  async function handleBarcodePortion(event) {
    event.preventDefault();
    if (!barcodeProduct) return;
    await runQuickPortion(
      {
        source: barcodeProduct.source || "off",
        id: barcodeProduct.id || barcodeProduct.barcode,
        name: barcodeProduct.name,
        brand: barcodeProduct.brand,
      },
      $("barcode-amount").value
    );
  }

  // --- Portion / Recipe ---

  async function handlePortion(event) {
    event.preventDefault();
    await runQuickPortion(
      {
        source: $("portion-source").value,
        id: $("portion-id").value.trim(),
        name: $("portion-id").value.trim(),
      },
      $("portion-amount").value
    );
  }

  function addRecipeIngredientRow(source = "bls", id = "", amount = 100) {
    const index = ingredientCounter++;
    const fieldset = document.createElement("fieldset");
    fieldset.className = "ingredient-fieldset";
    fieldset.dataset.index = String(index);

    const legend = document.createElement("legend");
    legend.textContent = "Zutat";
    fieldset.appendChild(legend);

    const row = document.createElement("div");
    row.className = "ingredient-row";

    const sourceSelect = document.createElement("select");
    sourceSelect.className = "input ingredient-source";
    sourceSelect.dataset.index = String(index);
    for (const [val, label] of [
      ["bls", "BLS"],
      ["off", "OFF"],
      ["custom", "Eigen"],
    ]) {
      const opt = document.createElement("option");
      opt.value = val;
      opt.textContent = label;
      if (val === source) opt.selected = true;
      sourceSelect.appendChild(opt);
    }

    const idInput = document.createElement("input");
    idInput.type = "text";
    idInput.className = "input ingredient-id";
    idInput.dataset.index = String(index);
    idInput.placeholder = "Code / ID";
    idInput.value = id;
    idInput.required = true;

    const amountInput = document.createElement("input");
    amountInput.type = "number";
    amountInput.className = "input ingredient-amount";
    amountInput.dataset.index = String(index);
    amountInput.placeholder = "g";
    amountInput.value = String(amount);
    amountInput.min = "1";
    amountInput.step = "1";
    amountInput.required = true;

    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.className = "ingredient-remove";
    removeBtn.setAttribute("aria-label", "Zutat entfernen");
    removeBtn.textContent = "×";
    removeBtn.addEventListener("click", () => {
      const container = $("recipe-ingredients");
      if (container.children.length <= 1) return;
      fieldset.remove();
      renumberRecipeIngredients();
    });

    row.appendChild(sourceSelect);
    row.appendChild(idInput);
    row.appendChild(amountInput);
    row.appendChild(removeBtn);
    fieldset.appendChild(row);
    $("recipe-ingredients").appendChild(fieldset);
    renumberRecipeIngredients();
  }

  function renumberRecipeIngredients() {
    $("recipe-ingredients")
      .querySelectorAll(".ingredient-fieldset")
      .forEach((fs, i) => {
        const legend = fs.querySelector("legend");
        if (legend) legend.textContent = `Zutat ${i + 1}`;
      });
  }

  function initRecipeIngredients() {
    $("recipe-add-ingredient")?.addEventListener("click", () => addRecipeIngredientRow());
    addRecipeIngredientRow();
    addRecipeIngredientRow();
  }

  async function handleRecipe(event) {
    event.preventDefault();
    showError(null);
    const servings = parseInt($("recipe-servings").value, 10) || 1;
    const ingredients = [];
    document.querySelectorAll(".ingredient-fieldset").forEach((fs) => {
      const idInput = fs.querySelector(".ingredient-id");
      const amountInput = fs.querySelector(".ingredient-amount");
      const sourceSelect = fs.querySelector(".ingredient-source");
      const id = idInput?.value.trim();
      const amount = parseFloat(amountInput?.value);
      const source = sourceSelect?.value || "bls";
      if (id && amount > 0) {
        ingredients.push({ source, id, amount_g: amount });
      }
    });
    if (!ingredients.length) {
      showError("Mindestens eine Zutat mit Code und Menge angeben.");
      return;
    }
    try {
      const result = await apiPost("calculate/recipe", { ingredients, servings });
      updateHeroTiles(result.diabetes);
      showDetails(result);
    } catch (err) {
      showError(err.message);
    }
  }

  // --- Navigation ---

  function switchPanel(panelName) {
    if (panelName !== "barcode") stopBarcodeScan();
    document.querySelectorAll(".panel").forEach((panel) => {
      const isActive = panel.id === `panel-${panelName}`;
      panel.classList.toggle("active", isActive);
      panel.hidden = !isActive;
    });
    document.querySelectorAll(".nav-btn").forEach((btn) => {
      const isActive = btn.dataset.panel === panelName;
      btn.classList.toggle("active", isActive);
      if (isActive) btn.setAttribute("aria-current", "page");
      else btn.removeAttribute("aria-current");
    });
    showError(null);
  }

  function applySearchLayout(layout) {
    const grid = $("search-results-grid");
    grid.classList.remove("search-layout-stacked", "search-layout-side-by-side");
    grid.classList.add(
      layout === "side_by_side" ? "search-layout-side-by-side" : "search-layout-stacked"
    );
  }

  async function loadHealth() {
    try {
      const health = await apiGet("health");
      $("food-count-badge").textContent =
        health.food_count != null
          ? `${health.food_count.toLocaleString("de-DE")} LM`
          : "—";
      $("bls-version").textContent = `BLS ${health.bls_version || "4.0"}`;
      offEnabled = health.open_food_facts_enabled !== false;
      todoListEnabled = health.todo_list_enabled !== false;
      searchRecentsEnabled = health.search_recents_enabled !== false;
      applySearchLayout(health.search_layout || "stacked");
      renderRecents();
    } catch (_) {
      $("food-count-badge").textContent = "offline";
    }
  }

  function initNavigation() {
    document.querySelectorAll(".nav-btn").forEach((btn) => {
      btn.addEventListener("click", () => switchPanel(btn.dataset.panel));
    });
  }

  function initDetailsToggle() {
    $("details-toggle")?.addEventListener("click", () => {
      const toggle = $("details-toggle");
      const content = $("details-content");
      const expanded = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!expanded));
      content.hidden = expanded;
    });
  }

  function init() {
    initTheme();
    initNavigation();
    initDetailsToggle();
    initLiveSearch();
    initRecipeIngredients();
    updateScannerAvailability();

    $("search-form")?.addEventListener("submit", handleSearchSubmit);
    $("barcode-form")?.addEventListener("submit", handleBarcodeLookup);
    $("barcode-portion-form")?.addEventListener("submit", handleBarcodePortion);
    $("barcode-scan-start")?.addEventListener("click", startBarcodeScan);
    $("barcode-scan-stop")?.addEventListener("click", stopBarcodeScan);
    $("portion-form")?.addEventListener("submit", handlePortion);
    $("recipe-form")?.addEventListener("submit", handleRecipe);

    loadHealth();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
