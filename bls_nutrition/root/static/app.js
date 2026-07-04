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
  let mapEnabled = false;
  let favoritesEnabled = false;
  let favoritesConfirmDelete = true;
  let activePanel = "search";
  let mapRadiusKm = 20;
  const favoriteByKey = new Map();
  let searchAbortController = null;
  let searchDebounceTimer = null;
  let ingredientCounter = 0;
  let scanStream = null;
  let scanFrameId = null;
  let barcodeDetector = null;
  let mapInstance = null;
  let mapMarkersLayer = null;
  let mapLoaded = false;
  let detailsHasResult = false;

  const $ = (id) => document.getElementById(id);

  function parseConfigFlag(value, defaultValue = false) {
    if (value === true || value === "true") return true;
    if (value === false || value === "false") return false;
    return defaultValue;
  }

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

  function updateMapVisibility() {
    const navMapBtn = $("nav-map-btn");
    const mapPanel = $("panel-map");
    if (navMapBtn) navMapBtn.hidden = !mapEnabled;
    if (mapPanel && !mapEnabled) {
      mapPanel.hidden = true;
      mapPanel.classList.remove("active");
      if (document.querySelector('.nav-btn[data-panel="map"]')?.classList.contains("active")) {
        switchPanel("search");
      }
    }
  }

  function updateFavoritesIoVisibility(panelName) {
    const wrap = $("favorites-io-wrap");
    if (!wrap) return;
    wrap.hidden = !favoritesEnabled || panelName !== "favorites";
    if (wrap.hidden) closeFavoritesIoMenu();
  }

  function closeFavoritesIoMenu() {
    const menu = $("favorites-io-menu");
    const btn = $("favorites-io-btn");
    if (menu) menu.hidden = true;
    if (btn) btn.setAttribute("aria-expanded", "false");
  }

  function toggleFavoritesIoMenu() {
    const menu = $("favorites-io-menu");
    const btn = $("favorites-io-btn");
    if (!menu || !btn) return;
    const open = menu.hidden;
    menu.hidden = !open;
    btn.setAttribute("aria-expanded", String(open));
  }

  function confirmFavoriteDelete() {
    if (!favoritesConfirmDelete) return Promise.resolve(true);
    const dialog = $("favorite-delete-dialog");
    if (!dialog || typeof dialog.showModal !== "function") {
      return Promise.resolve(window.confirm("Favorit wirklich löschen?"));
    }
    return new Promise((resolve) => {
      const cancelBtn = $("favorite-delete-cancel");
      const confirmBtn = $("favorite-delete-confirm");
      const onCancel = () => {
        cleanup();
        resolve(false);
      };
      const onConfirm = () => {
        cleanup();
        resolve(true);
      };
      const cleanup = () => {
        dialog.close();
        cancelBtn?.removeEventListener("click", onCancel);
        confirmBtn?.removeEventListener("click", onConfirm);
        dialog.removeEventListener("cancel", onCancel);
      };
      cancelBtn?.addEventListener("click", onCancel);
      confirmBtn?.addEventListener("click", onConfirm);
      dialog.addEventListener("cancel", onCancel);
      dialog.showModal();
    });
  }

  async function downloadFavoritesExport(format) {
    const res = await fetch(`favorites/export?format=${format}`);
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch (_) { /* ignore */ }
      throw new Error(detail);
    }
    const blob = await res.blob();
    const disposition = res.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="([^"]+)"/);
    const filename = match ? match[1] : `bls-favorites.${format}`;
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  }

  async function importFavoritesFile(file) {
    const replace = window.confirm(
      "Alle bestehenden Favoriten ersetzen?\n\nOK = Ersetzen\nAbbrechen = Zusammenführen (Duplikate überspringen)"
    );
    const mode = replace ? "replace" : "merge";
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`favorites/import?mode=${mode}`, {
      method: "POST",
      body: formData,
    });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch (_) { /* ignore */ }
      throw new Error(detail);
    }
    const result = await res.json();
    await loadFavoritesIndex();
    const parts = [`${result.imported} importiert`];
    if (result.skipped) parts.push(`${result.skipped} übersprungen`);
    if (result.errors?.length) parts.push(`${result.errors.length} Fehler`);
    showStatus(`Import abgeschlossen: ${parts.join(", ")}.`, false);
    if (result.errors?.length) {
      showError(result.errors.slice(0, 3).join(" · "));
    }
  }

  function initFavoritesIo() {
    const btn = $("favorites-io-btn");
    const menu = $("favorites-io-menu");
    const fileInput = $("favorites-import-input");
    btn?.addEventListener("click", (event) => {
      event.stopPropagation();
      toggleFavoritesIoMenu();
    });
    menu?.querySelectorAll("[data-action]").forEach((item) => {
      item.addEventListener("click", async () => {
        const action = item.dataset.action;
        closeFavoritesIoMenu();
        try {
          if (action === "export-json") {
            await downloadFavoritesExport("json");
            showStatus("Favoriten als JSON exportiert.", false);
          } else if (action === "export-csv") {
            await downloadFavoritesExport("csv");
            showStatus("Favoriten als CSV exportiert.", false);
          } else if (action === "import" && fileInput) {
            fileInput.value = "";
            fileInput.click();
          }
        } catch (err) {
          showError(err.message);
        }
      });
    });
    fileInput?.addEventListener("change", async () => {
      const file = fileInput.files?.[0];
      if (!file) return;
      try {
        await importFavoritesFile(file);
      } catch (err) {
        showError(err.message);
      } finally {
        fileInput.value = "";
      }
    });
    document.addEventListener("click", (event) => {
      if (!menu || menu.hidden) return;
      const wrap = $("favorites-io-wrap");
      if (wrap && !wrap.contains(event.target)) closeFavoritesIoMenu();
    });
  }

  function updateHeroTilesVisibility(panelName) {
    const heroTiles = $("hero-tiles");
    if (heroTiles) heroTiles.hidden = panelName === "map";
    const detailsSection = $("details-section");
    if (detailsSection) {
      detailsSection.hidden = panelName === "map" || !detailsHasResult;
    }
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

  async function apiPatch(path, data) {
    const res = await fetch(path, {
      method: "PATCH",
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

  async function apiDelete(path) {
    const res = await fetch(path, { method: "DELETE" });
    if (!res.ok) {
      let detail = res.statusText;
      try {
        const body = await res.json();
        detail = body.detail || detail;
      } catch (_) { /* ignore */ }
      throw new Error(detail);
    }
    try {
      return await res.json();
    } catch (_) {
      return {};
    }
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
      const wrapChip = document.createElement("span");
      wrapChip.className = "recent-chip-wrap";
      const heartBtn = createFavoriteButton(
        { source: r.source, id: r.id, name: r.name, brand: r.brand },
        r.amount_g
      );
      if (heartBtn) wrapChip.appendChild(heartBtn);
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
      wrapChip.appendChild(btn);
      chips.appendChild(wrapChip);
    }
  }

  // --- Favorites ---

  function favoriteKey(source, id) {
    return `${source}:${id}`;
  }

  function heartIconHtml(active) {
    const fill = active ? "currentColor" : "none";
    return (
      `<svg class="favorite-heart-icon" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">` +
      `<path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" fill="${fill}" stroke="currentColor" stroke-width="1.5"/></svg>`
    );
  }

  function createFavoriteButton(item, defaultAmount = 100) {
    if (!favoritesEnabled) return null;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn-favorite-heart";
    btn.setAttribute("aria-label", "Favorit");
    const key = favoriteKey(item.source || "bls", item.id);
    if (favoriteByKey.has(key)) btn.classList.add("is-active");
    btn.innerHTML = heartIconHtml(favoriteByKey.has(key));
    btn.addEventListener("click", (event) => {
      event.stopPropagation();
      event.preventDefault();
      toggleFavorite(item, defaultAmount);
    });
    return btn;
  }

  async function loadFavoritesIndex() {
    favoriteByKey.clear();
    if (!favoritesEnabled) {
      renderFavoritesList([]);
      return;
    }
    try {
      const items = await apiGet("favorites");
      for (const fav of items) {
        favoriteByKey.set(favoriteKey(fav.source, fav.source_id), fav);
      }
      renderFavoritesList(items);
    } catch (err) {
      renderFavoritesList([]);
    }
  }

  const FAVORITE_PLACEHOLDER_IMAGE = "static/assets/favorite-food-placeholder.svg";

  function favoriteImageSrc(fav) {
    const resolved = fav.resolved_image;
    if (resolved && String(resolved).startsWith("http")) return resolved;
    if (resolved) return resolved;
    if (fav.has_local_image) return `favorites/${fav.id}/image`;
    return FAVORITE_PLACEHOLDER_IMAGE;
  }

  function isFavoritePlaceholderImage(src) {
    return src === FAVORITE_PLACEHOLDER_IMAGE;
  }

  function renderFavoritesList(items) {
    const list = $("favorites-list");
    const empty = $("favorites-empty");
    if (!list) return;
    list.innerHTML = "";
    if (!favoritesEnabled) {
      if (empty) empty.hidden = true;
      return;
    }
    if (!items.length) {
      if (empty) empty.hidden = false;
      return;
    }
    if (empty) empty.hidden = true;

    for (const fav of items) {
      const li = document.createElement("li");
      li.className = "favorite-card";
      li.dataset.favoriteId = String(fav.id);

      const thumbWrap = document.createElement("div");
      thumbWrap.className = "favorite-thumb-wrap";
      const imgSrc = favoriteImageSrc(fav);
      const img = document.createElement("img");
      img.className = "favorite-thumb";
      img.alt = "";
      img.src = imgSrc;
      if (isFavoritePlaceholderImage(imgSrc)) {
        img.classList.add("is-placeholder");
      }
      img.addEventListener("error", () => {
        img.src = FAVORITE_PLACEHOLDER_IMAGE;
        img.classList.add("is-placeholder");
      });
      thumbWrap.appendChild(img);

      const body = document.createElement("div");
      body.className = "favorite-body";
      const name = document.createElement("p");
      name.className = "favorite-name";
      name.textContent = fav.display_name;
      const meta = document.createElement("p");
      meta.className = "favorite-meta";
      meta.textContent = `${fav.source.toUpperCase()} · ${fav.default_amount_g} g Standard`;
      body.appendChild(name);
      body.appendChild(meta);

      const actions = document.createElement("div");
      actions.className = "favorite-actions";
      const calcBtn = document.createElement("button");
      calcBtn.type = "button";
      calcBtn.className = "btn btn-primary btn-sm";
      calcBtn.textContent = "Berechnen";
      calcBtn.addEventListener("click", () => {
        runQuickPortion(
          {
            source: fav.source,
            id: fav.source_id,
            name: fav.display_name,
            brand: fav.brand,
          },
          fav.default_amount_g,
          true
        );
      });
      const editBtn = document.createElement("button");
      editBtn.type = "button";
      editBtn.className = "btn btn-secondary btn-sm";
      editBtn.textContent = "Bearbeiten";
      editBtn.addEventListener("click", () => openFavoriteEditor(li, fav));
      const delBtn = document.createElement("button");
      delBtn.type = "button";
      delBtn.className = "btn btn-secondary btn-sm";
      delBtn.textContent = "Entfernen";
      delBtn.addEventListener("click", async () => {
        try {
          const confirmed = await confirmFavoriteDelete();
          if (!confirmed) return;
          await apiDelete(`favorites/${fav.id}`);
          await loadFavoritesIndex();
          showStatus("Favorit entfernt.", false);
        } catch (err) {
          showError(err.message);
        }
      });
      actions.appendChild(calcBtn);
      actions.appendChild(editBtn);
      actions.appendChild(delBtn);

      thumbWrap.addEventListener("click", () => calcBtn.click());
      body.addEventListener("click", () => calcBtn.click());

      li.appendChild(thumbWrap);
      li.appendChild(body);
      li.appendChild(actions);
      list.appendChild(li);
    }
  }

  function openFavoriteEditor(card, fav) {
    if (card.classList.contains("is-editing")) return;
    card.classList.add("is-editing");
    card.innerHTML = "";

    const form = document.createElement("div");
    form.className = "favorite-edit-form";

    const nameInput = document.createElement("input");
    nameInput.type = "text";
    nameInput.className = "input";
    nameInput.value = fav.display_name;
    nameInput.setAttribute("aria-label", "Anzeigename");

    const amountInput = document.createElement("input");
    amountInput.type = "number";
    amountInput.className = "input input-narrow";
    amountInput.min = "1";
    amountInput.step = "1";
    amountInput.value = String(fav.default_amount_g);
    amountInput.setAttribute("aria-label", "Standardmenge in Gramm");

    const fileInput = document.createElement("input");
    fileInput.type = "file";
    fileInput.accept = "image/jpeg,image/png,image/webp";
    fileInput.setAttribute("aria-label", "Eigenes Bild");

    const saveBtn = document.createElement("button");
    saveBtn.type = "button";
    saveBtn.className = "btn btn-primary";
    saveBtn.textContent = "Speichern";
    saveBtn.addEventListener("click", async () => {
      try {
        await apiPatch(`favorites/${fav.id}`, {
          display_name: nameInput.value.trim() || fav.display_name,
          default_amount_g: parseFloat(amountInput.value) || fav.default_amount_g,
        });
        if (fileInput.files && fileInput.files[0]) {
          const body = new FormData();
          body.append("file", fileInput.files[0]);
          const res = await fetch(`favorites/${fav.id}/image`, {
            method: "POST",
            body,
          });
          if (!res.ok) {
            const payload = await res.json().catch(() => ({}));
            throw new Error(payload.detail || res.statusText);
          }
        }
        await loadFavoritesIndex();
        showStatus("Favorit gespeichert.", false);
      } catch (err) {
        showError(err.message);
      }
    });

    const cancelBtn = document.createElement("button");
    cancelBtn.type = "button";
    cancelBtn.className = "btn btn-secondary";
    cancelBtn.textContent = "Abbrechen";
    cancelBtn.addEventListener("click", () => loadFavoritesIndex());

    form.appendChild(nameInput);
    form.appendChild(amountInput);
    form.appendChild(fileInput);
    form.appendChild(saveBtn);
    form.appendChild(cancelBtn);
    card.appendChild(form);
  }

  async function toggleFavorite(item, defaultAmount = 100) {
    if (!favoritesEnabled || !item?.id) return;
    const source = item.source || "bls";
    const key = favoriteKey(source, item.id);
    try {
      if (favoriteByKey.has(key)) {
        const fav = favoriteByKey.get(key);
        await apiDelete(`favorites/${fav.id}`);
        showStatus("Aus Favoriten entfernt.", false);
      } else {
        await apiPost("favorites", {
          display_name: (item.name || item.id).trim(),
          source,
          id: item.id,
          barcode: source === "off" ? item.id : item.barcode || null,
          brand: item.brand || null,
          default_amount_g: defaultAmount,
        });
        showStatus("Zu Favoriten hinzugefügt.", false);
      }
      await loadFavoritesIndex();
    } catch (err) {
      showError(err.message);
    }
  }

  function updateFavoritesVisibility() {
    const navBtn = $("nav-favorites-btn");
    const panel = $("panel-favorites");
    if (navBtn) navBtn.hidden = !favoritesEnabled;
    if (panel && !favoritesEnabled) {
      panel.hidden = true;
      panel.classList.remove("active");
      if (document.querySelector('.nav-btn[data-panel="favorites"]')?.classList.contains("active")) {
        switchPanel("search");
      }
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
    if (!todoListEnabled) return null;
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
    detailsHasResult = true;
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

      const header = document.createElement("div");
      header.className = "result-item-header";
      const heartBtn = createFavoriteButton(item);
      if (heartBtn) header.appendChild(heartBtn);
      header.appendChild(button);

      const quickPanel = createQuickPortionPanel(item);
      button.addEventListener("click", () => {
        const wasExpanded = wrap.classList.contains("is-expanded");
        collapseAllResults(container.closest(".result-list") || container);
        if (!wasExpanded) {
          wrap.classList.add("is-expanded");
          quickPanel.hidden = false;
        }
      });

      wrap.appendChild(header);
      wrap.appendChild(quickPanel);

      if (showScores && todoListEnabled) {
        const actions = document.createElement("div");
        actions.className = "result-item-actions";
        const todoBtn = createTodoButton(item);
        if (todoBtn) {
          actions.appendChild(todoBtn);
          wrap.appendChild(actions);
        }
      }
      container.appendChild(wrap);
    }
    if (showScores) {
      applyTodoListVisibility();
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
      const favRow = document.createElement("div");
      favRow.className = "barcode-favorite-row";
      const heartBtn = createFavoriteButton(
        { source: "off", id: product.id, name: product.name, brand: product.brand },
        parseFloat($("barcode-amount")?.value) || 100
      );
      if (heartBtn) favRow.appendChild(heartBtn);
      if (favRow.childElementCount) resultEl.appendChild(favRow);
      if (todoListEnabled) {
        const actions = document.createElement("div");
        actions.className = "result-item-actions";
        const todoBtn = createTodoButton(product);
        if (todoBtn) actions.appendChild(todoBtn);
        if (actions.childElementCount) resultEl.appendChild(actions);
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

  // --- Map ---

  function showMapStatus(message) {
    const status = $("map-status");
    if (!status) return;
    status.textContent = message || "";
    status.hidden = !message;
  }

  function clearMapMarkers() {
    if (mapMarkersLayer) {
      mapMarkersLayer.clearLayers();
    }
  }

  function ensureMap() {
    if (mapInstance) return mapInstance;
    if (typeof L === "undefined") {
      throw new Error("Leaflet konnte nicht geladen werden.");
    }
    const canvas = $("map-canvas");
    if (!canvas) {
      throw new Error("Kartencontainer fehlt.");
    }
    mapInstance = L.map(canvas, { zoomControl: true });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    }).addTo(mapInstance);
    mapMarkersLayer = L.layerGroup().addTo(mapInstance);
    return mapInstance;
  }

  function supermarketMarkerStatus(isOpenNow) {
    if (isOpenNow === true) return "open";
    if (isOpenNow === false) return "closed";
    return "unknown";
  }

  function supermarketStatusLabel(isOpenNow) {
    if (isOpenNow === true) return "Geöffnet";
    if (isOpenNow === false) return "Geschlossen";
    return "Öffnungszeiten unbekannt";
  }

  function createMapMarkerIcon(status) {
    return L.divIcon({
      className: "",
      html: `<span class="map-marker-pin map-marker-${status}" aria-hidden="true"></span>`,
      iconSize: [26, 36],
      iconAnchor: [13, 36],
      popupAnchor: [0, -32],
    });
  }

  function renderMapItems(center, items) {
    const map = ensureMap();
    clearMapMarkers();
    const homeMarker = L.marker([center.lat, center.lon], {
      icon: createMapMarkerIcon("home"),
    }).addTo(mapMarkersLayer);
    homeMarker.bindPopup("Home Assistant Standort");
    for (const item of items) {
      const markerStatus = supermarketMarkerStatus(item.is_open_now);
      const marker = L.marker([item.lat, item.lon], {
        icon: createMapMarkerIcon(markerStatus),
      }).addTo(mapMarkersLayer);
      const address = item.address ? `<br>${escapeHtml(item.address)}` : "";
      const statusLine = `<br><span class="map-popup-status map-popup-status-${markerStatus}">${escapeHtml(
        supermarketStatusLabel(item.is_open_now)
      )}</span>`;
      const hours = item.opening_hours_display
        ? `<div class="map-popup-hours"><strong>Öffnungszeiten:</strong><br>${escapeHtml(
            item.opening_hours_display
          ).replace(/\n/g, "<br>")}</div>`
        : "";
      marker.bindPopup(
        `<strong>${escapeHtml(item.name || "Supermarkt")}</strong><br>` +
          `${escapeHtml(item.type || "shop")} · ${formatNum(item.distance_km)} km${statusLine}${address}${hours}`
      );
    }
    const allPoints = [[center.lat, center.lon], ...items.map((item) => [item.lat, item.lon])];
    const bounds = L.latLngBounds(allPoints);
    map.fitBounds(bounds, { padding: [24, 24], maxZoom: 14 });
    setTimeout(() => map.invalidateSize(), 0);
  }

  async function loadMapData() {
    const mapCanvas = $("map-canvas");
    const radiusHint = $("map-radius-hint");
    if (radiusHint) radiusHint.textContent = `Radius: ${mapRadiusKm} km`;
    if (!mapCanvas) return;
    mapCanvas.hidden = true;
    showMapStatus("Lade Supermärkte in deiner Umgebung…");
    try {
      const payload = await apiGet(`map/supermarkets?radius_km=${encodeURIComponent(mapRadiusKm)}`);
      renderMapItems(payload.center, payload.items || []);
      mapCanvas.hidden = false;
      if ((payload.items || []).length) {
        showMapStatus(`${payload.count} Märkte im Umkreis von ${payload.radius_km} km gefunden.`);
      } else {
        showMapStatus(`Keine Märkte im Umkreis von ${payload.radius_km} km gefunden.`);
      }
      mapLoaded = true;
    } catch (err) {
      showMapStatus(err.message || "Map konnte nicht geladen werden.");
    }
  }

  // --- Navigation ---

  function switchPanel(panelName) {
    if (panelName === "map" && !mapEnabled) {
      panelName = "search";
    }
    if (panelName === "favorites" && !favoritesEnabled) {
      panelName = "search";
    }
    activePanel = panelName;
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
    if (panelName === "map" && mapEnabled && !mapLoaded) {
      loadMapData().catch((err) => showMapStatus(err.message));
    }
    if (panelName === "favorites" && favoritesEnabled) {
      loadFavoritesIndex().catch(() => {});
    }
    updateHeroTilesVisibility(panelName);
    updateFavoritesIoVisibility(panelName);
    showError(null);
  }

  function applySearchLayout(layout) {
    const grid = $("search-results-grid");
    grid.classList.remove("search-layout-stacked", "search-layout-side-by-side");
    grid.classList.add(
      layout === "side_by_side" ? "search-layout-side-by-side" : "search-layout-stacked"
    );
  }

  function applyTodoListVisibility() {
    const todoEl = $("result-todo-action");
    if (todoEl) {
      if (!todoListEnabled) {
        todoEl.innerHTML = "";
        todoEl.hidden = true;
      }
    }
    if (!todoListEnabled) {
      document.querySelectorAll(".result-item-actions .btn-todo").forEach((btn) => {
        btn.closest(".result-item-actions")?.remove();
      });
      const barcodeResult = $("barcode-result");
      barcodeResult
        ?.querySelector(".result-item-actions")
        ?.remove();
    }
  }

  function formatImportedAt(iso) {
    if (!iso) return null;
    try {
      const date = new Date(iso);
      if (Number.isNaN(date.getTime())) return null;
      return date.toLocaleString("de-DE", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch (_) {
      return null;
    }
  }

  function formatDbStatusLine(health) {
    const status = health.database_status || "ready";
    const engine = (health.database_engine || "duckdb").toUpperCase();
    if (status === "importing") {
      return `Datenbank (${engine}): Import läuft…`;
    }
    if (status === "error") {
      return `Datenbank (${engine}): Fehler beim Import`;
    }
    const parts = [`Datenbank (${engine}): bereit`];
    const imported = formatImportedAt(health.imported_at);
    if (imported) {
      parts.push(`BLS-Import: ${imported}`);
    }
    if (health.food_count != null) {
      parts.push(`${Number(health.food_count).toLocaleString("de-DE")} Lebensmittel`);
    }
    if (health.off_products_count != null && health.off_products_count > 0) {
      parts.push(`${Number(health.off_products_count).toLocaleString("de-DE")} OFF-Produkte im Cache`);
    }
    return parts.join(" · ");
  }

  async function loadHealth() {
    try {
      const health = await apiGet("health");
      const dbStatus = $("db-status-line");
      if (dbStatus) {
        dbStatus.textContent = formatDbStatusLine(health);
      }
      $("bls-version").textContent = `BLS ${health.bls_version || "4.0"}`;
      offEnabled = parseConfigFlag(health.open_food_facts_enabled, true);
      todoListEnabled = parseConfigFlag(health.todo_list_enabled, false);
      searchRecentsEnabled = parseConfigFlag(health.search_recents_enabled, true);
      mapEnabled = parseConfigFlag(health.map_enabled, false);
      favoritesEnabled = parseConfigFlag(health.favorites_enabled, true);
      favoritesConfirmDelete = parseConfigFlag(health.favorites_confirm_delete, true);
      mapRadiusKm = Math.max(1, Math.min(50, Number(health.map_radius_km) || 20));
      applySearchLayout(health.search_layout || "stacked");
      applyTodoListVisibility();
      renderRecents();
      updateMapVisibility();
      updateFavoritesVisibility();
      updateFavoritesIoVisibility(activePanel);
      await loadFavoritesIndex();
    } catch (_) {
      const dbStatus = $("db-status-line");
      if (dbStatus) {
        dbStatus.textContent = "Datenbank: nicht erreichbar";
      }
      todoListEnabled = false;
      mapEnabled = false;
      favoritesEnabled = false;
      applyTodoListVisibility();
      updateMapVisibility();
      updateFavoritesVisibility();
      updateFavoritesIoVisibility(activePanel);
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

  async function init() {
    initTheme();
    initNavigation();
    initDetailsToggle();
    initFavoritesIo();
    await loadHealth();
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
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
