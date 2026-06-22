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

  let barcodeProduct = null;
  let offEnabled = true;
  let todoListEnabled = false;

  const SEARCH_LIMIT = 10;

  const $ = (id) => document.getElementById(id);

  function formatNum(value) {
    if (value === null || value === undefined) return "—";
    const n = Number(value);
    if (Number.isNaN(n)) return "—";
    return n.toLocaleString("de-DE", { maximumFractionDigits: 2 });
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

  function createTodoButton(product) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "btn btn-todo";
    btn.textContent = "Zur Einkaufsliste";
    btn.addEventListener("click", (event) => {
      event.stopPropagation();
      event.preventDefault();
      addToTodoList(product);
    });
    return btn;
  }

  async function apiGet(path) {
    const res = await fetch(path);
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
    const nutriscore = scores.nutriscore;
    const novaGroup = scores.nova_group;
    const ecoscore = scores.ecoscore;

    if (nutriscore) {
      parts.push(
        scoreBadgeItem(
          "Nutri-Score",
          `<img class="score-badge" src="static/assets/scores/nutriscore-${escapeHtml(nutriscore.toLowerCase())}.svg" alt="Nutri-Score ${escapeHtml(nutriscore.toUpperCase())}" title="Nutri-Score ${escapeHtml(nutriscore.toUpperCase())}">`
        )
      );
    }
    if (novaGroup) {
      parts.push(
        scoreBadgeItem(
          "Nova",
          `<img class="score-badge" src="static/assets/scores/nova-${escapeHtml(String(novaGroup))}.svg" alt="Nova ${escapeHtml(String(novaGroup))}" title="Nova ${escapeHtml(String(novaGroup))}">`
        )
      );
    }
    if (ecoscore) {
      parts.push(
        scoreBadgeItem(
          "Eco-Score",
          `<img class="score-badge" src="static/assets/scores/ecoscore-${escapeHtml(ecoscore.toLowerCase())}.svg" alt="Eco-Score ${escapeHtml(ecoscore.toUpperCase())}" title="Eco-Score ${escapeHtml(ecoscore.toUpperCase())}">`
        )
      );
    }
    if (!parts.length) return "";
    return `<span class="score-badges">${parts.join("")}</span>`;
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
      const label = NUTRIENT_LABELS[code] || code;
      tr.innerHTML = `<td>${label}</td><td>${formatNum(value)}</td>`;
      rowsEl.appendChild(tr);
    }

    section.hidden = false;
    toggle.setAttribute("aria-expanded", "false");
    content.hidden = true;
  }

  function switchPanel(panelName) {
    document.querySelectorAll(".panel").forEach((panel) => {
      const isActive = panel.id === `panel-${panelName}`;
      panel.classList.toggle("active", isActive);
      panel.hidden = !isActive;
    });
    document.querySelectorAll(".nav-btn").forEach((btn) => {
      const isActive = btn.dataset.panel === panelName;
      btn.classList.toggle("active", isActive);
      if (isActive) {
        btn.setAttribute("aria-current", "page");
      } else {
        btn.removeAttribute("aria-current");
      }
    });
    showError(null);
  }

  function selectFoodForPortion(source, id, name) {
    $("portion-source").value = source;
    $("portion-id").value = id;
    switchPanel("portion");
    if (name) {
      showError(`Ausgewählt: ${name}`);
    }
  }

  function applySearchLayout(layout) {
    const grid = $("search-results-grid");
    grid.classList.remove("search-layout-stacked", "search-layout-side-by-side");
    if (layout === "side_by_side") {
      grid.classList.add("search-layout-side-by-side");
    } else {
      grid.classList.add("search-layout-stacked");
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
      const li = document.createElement("li");
      li.className = showScores ? "result-item-row" : "";
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
      button.addEventListener("click", () => {
        selectFoodForPortion(item.source || "bls", item.id, item.name);
      });
      li.appendChild(button);
      if (showScores && todoListEnabled) {
        li.appendChild(createTodoButton(item));
      }
      container.appendChild(li);
    }
  }

  async function loadHealth() {
    try {
      const health = await apiGet("health");
      const count = health.food_count;
      $("food-count-badge").textContent =
        count != null ? `${count.toLocaleString("de-DE")} LM` : "—";
      const blsVer = health.bls_version || "4.0";
      $("bls-version").textContent = `BLS ${blsVer}`;
      offEnabled = health.open_food_facts_enabled !== false;
      todoListEnabled = health.todo_list_enabled !== false;
      applySearchLayout(health.search_layout || "stacked");
    } catch (_) {
      $("food-count-badge").textContent = "offline";
    }
  }

  async function handleSearch(event) {
    event.preventDefault();
    showError(null);
    const query = $("search-query").value.trim();
    if (!query) return;

    const grid = $("search-results-grid");
    const blsList = $("search-results-bls");
    const offList = $("search-results-off");
    blsList.innerHTML = "";
    offList.innerHTML = "";
    grid.hidden = false;

    const btn = $("search-form").querySelector("button");
    btn.disabled = true;

    if (offEnabled) {
      offList.innerHTML = '<li><p class="result-item-meta">Open Food Facts wird geladen…</p></li>';
    }

    try {
      const blsResults = await apiGet(
        `foods/search?q=${encodeURIComponent(query)}&limit=${SEARCH_LIMIT}`
      );
      renderResultList(blsList, blsResults, "Keine Treffer.", false);

      if (!offEnabled) {
        renderResultList(offList, [], "Open Food Facts deaktiviert.", false);
      } else {
        try {
          const offResults = await apiGet(
            `foods/search/off?q=${encodeURIComponent(query)}&limit=${SEARCH_LIMIT}`
          );
          renderResultList(offList, offResults, "Keine Treffer.", true);
        } catch (offErr) {
          renderResultList(
            offList,
            [],
            offErr.message || "Open Food Facts nicht erreichbar.",
            false
          );
        }
      }
    } catch (err) {
      showError(err.message);
      grid.hidden = true;
    } finally {
      btn.disabled = false;
    }
  }

  async function handleBarcodeLookup(event) {
    event.preventDefault();
    showError(null);
    const barcode = $("barcode-input").value.trim();
    if (!barcode) return;

    const btn = $("barcode-form").querySelector("button");
    btn.disabled = true;
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
      btn.disabled = false;
    }
  }

  async function handleBarcodePortion(event) {
    event.preventDefault();
    if (!barcodeProduct) return;
    showError(null);
    const amount = parseFloat($("barcode-amount").value);
    if (!amount || amount <= 0) {
      showError("Bitte eine gültige Menge eingeben.");
      return;
    }
    try {
      const result = await apiPost("calculate/portion", {
        source: barcodeProduct.source || "off",
        id: barcodeProduct.id || barcodeProduct.barcode,
        amount_g: amount,
      });
      updateHeroTiles(result.diabetes);
      showDetails(result);
    } catch (err) {
      showError(err.message);
    }
  }

  async function handlePortion(event) {
    event.preventDefault();
    showError(null);
    const source = $("portion-source").value;
    const id = $("portion-id").value.trim();
    const amount = parseFloat($("portion-amount").value);
    if (!id || !amount || amount <= 0) {
      showError("Bitte ID und Menge ausfüllen.");
      return;
    }
    try {
      const result = await apiPost("calculate/portion", {
        source,
        id,
        amount_g: amount,
      });
      updateHeroTiles(result.diabetes);
      showDetails(result);
    } catch (err) {
      showError(err.message);
    }
  }

  async function handleRecipe(event) {
    event.preventDefault();
    showError(null);
    const servings = parseInt($("recipe-servings").value, 10) || 1;
    const ingredients = [];
    document.querySelectorAll(".ingredient-id").forEach((input) => {
      const id = input.value.trim();
      const index = input.dataset.index;
      const amountEl = document.querySelector(`.ingredient-amount[data-index="${index}"]`);
      const amount = parseFloat(amountEl?.value);
      if (id && amount > 0) {
        ingredients.push({ source: "bls", id, amount_g: amount });
      }
    });
    if (!ingredients.length) {
      showError("Mindestens eine Zutat mit Code und Menge angeben.");
      return;
    }
    try {
      const result = await apiPost("calculate/recipe", {
        ingredients,
        servings,
      });
      updateHeroTiles(result.diabetes);
      showDetails(result);
    } catch (err) {
      showError(err.message);
    }
  }

  function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text ?? "";
    return div.innerHTML;
  }

  function initNavigation() {
    document.querySelectorAll(".nav-btn").forEach((btn) => {
      btn.addEventListener("click", () => switchPanel(btn.dataset.panel));
    });
  }

  function initDetailsToggle() {
    $("details-toggle").addEventListener("click", () => {
      const toggle = $("details-toggle");
      const content = $("details-content");
      const expanded = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", String(!expanded));
      content.hidden = expanded;
    });
  }

  function init() {
    initNavigation();
    initDetailsToggle();
    $("search-form").addEventListener("submit", handleSearch);
    $("barcode-form").addEventListener("submit", handleBarcodeLookup);
    $("barcode-portion-form").addEventListener("submit", handleBarcodePortion);
    $("portion-form").addEventListener("submit", handlePortion);
    $("recipe-form").addEventListener("submit", handleRecipe);
    loadHealth();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
