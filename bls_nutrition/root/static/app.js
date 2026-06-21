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

  const $ = (id) => document.getElementById(id);

  function formatNum(value) {
    if (value === null || value === undefined) return "—";
    const n = Number(value);
    if (Number.isNaN(n)) return "—";
    return n.toLocaleString("de-DE", { maximumFractionDigits: 2 });
  }

  function showError(message) {
    const el = $("error-msg");
    if (!message) {
      el.hidden = true;
      el.textContent = "";
      return;
    }
    el.textContent = message;
    el.hidden = false;
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

  async function loadHealth() {
    try {
      const health = await apiGet("health");
      const count = health.food_count;
      $("food-count-badge").textContent =
        count != null ? `${count.toLocaleString("de-DE")} LM` : "—";
      const blsVer = health.bls_version || "4.0";
      $("bls-version").textContent = `BLS ${blsVer}`;
    } catch (_) {
      $("food-count-badge").textContent = "offline";
    }
  }

  async function handleSearch(event) {
    event.preventDefault();
    showError(null);
    const query = $("search-query").value.trim();
    if (!query) return;

    const list = $("search-results");
    list.innerHTML = "";
    const btn = $("search-form").querySelector("button");
    btn.disabled = true;

    try {
      const results = await apiGet(
        `foods/search?q=${encodeURIComponent(query)}&limit=20`
      );
      if (!results.length) {
        list.innerHTML = "<li><p class=\"result-item-meta\">Keine Treffer.</p></li>";
        return;
      }
      for (const item of results) {
        const li = document.createElement("li");
        const button = document.createElement("button");
        button.type = "button";
        button.className = "result-item";
        button.innerHTML =
          `<span class="result-item-name">${escapeHtml(item.name)}</span>` +
          `<span class="result-item-meta">${escapeHtml(item.id)}</span>`;
        button.addEventListener("click", () => {
          selectFoodForPortion(item.source || "bls", item.id, item.name);
        });
        li.appendChild(button);
        list.appendChild(li);
      }
    } catch (err) {
      showError(err.message);
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
        (product.brand ? `<br><span class="result-item-meta">${escapeHtml(product.brand)}</span>` : "");
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
