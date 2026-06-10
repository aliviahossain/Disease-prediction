/* eslint-env browser */
/* global window, document, fetch */

/**
 * history.js — patient-history UI controller.
 *
 * Talks to /api/history. Handles:
 *   - initial load & pagination
 *   - filtering by prediction type
 *   - viewing one entry in a modal
 *   - deleting a single entry
 *   - clearing all entries
 *   - empty / auth-required / network error states
 *
 * Part of the fix for issue #230 — the page existed but never
 * called any API, so it always looked empty.
 */

(function () {
  "use strict";

  // ----- Config -------------------------------------------------------- //
  const API_BASE = "/api/history";
  const DEFAULT_PER_PAGE = 20;

  // ----- DOM refs ------------------------------------------------------ //
  const $list        = document.getElementById("history-list");
  const $loading     = document.getElementById("history-loading");
  const $status      = document.getElementById("history-status");
  const $typeFilter  = document.getElementById("history-type-filter");
  const $refreshBtn  = document.getElementById("history-refresh-btn");
  const $clearBtn    = document.getElementById("history-clear-btn");
  const $pagination  = document.getElementById("history-pagination");
  const $prevBtn     = document.getElementById("history-prev-btn");
  const $nextBtn     = document.getElementById("history-next-btn");
  const $pageInd     = document.getElementById("history-page-indicator");
  const $modal       = document.getElementById("history-modal");
  const $modalBody   = document.getElementById("history-modal-body");

  // Defensive: page wasn't loaded → script bailed in.
  if (!$list) return;

  // ----- State --------------------------------------------------------- //
  const state = {
    page: 1,
    perPage: DEFAULT_PER_PAGE,
    type: "",
    pages: 1,
    total: 0,
  };
  let lastFocusedElement = null;
  // ----- Utilities ----------------------------------------------------- //

  /** Escape user-controlled strings before putting them in HTML. */
  function escapeHTML(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  /** "2026-05-20T11:30:00Z" → "May 20, 2026, 11:30 AM" (user locale). */
  function formatDate(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return iso;
    return d.toLocaleString(undefined, {
      year: "numeric", month: "short", day: "numeric",
      hour: "2-digit", minute: "2-digit",
    });
  }

  const TYPE_LABELS = {
    bayes:   "Bayes calculator",
    symptom: "Symptom-based",
    eye:     "Eye disease",
    skin:    "Skin disease",
  };

  function showStatus(msg, kind /* "info" | "error" | "" */) {
    if (!msg) {
      $status.textContent = "";
      $status.className = "history-status";
      return;
    }
    $status.textContent = msg;
    $status.className = "history-status history-status--" + (kind || "info");
  }

  // ----- Rendering ----------------------------------------------------- //

  function renderEmpty() {
    $list.innerHTML = `
      <li class="history-empty">
        <p>You haven't run any predictions yet.</p>
        <a href="/" class="btn btn-primary">Run your first prediction</a>
      </li>
    `;
  }

  function renderCard(entry) {
    const probPct = entry.probability_percent !== null &&
                    entry.probability_percent !== undefined
      ? entry.probability_percent.toFixed(2) + "%"
      : "—";

    const risk = entry.risk_level || "—";
    const riskClass = risk === "high"   ? "risk-high"
                    : risk === "medium" ? "risk-medium"
                    : risk === "low"    ? "risk-low"
                    : "";

    const typeLabel = TYPE_LABELS[entry.prediction_type]
                   || entry.prediction_type
                   || "Prediction";

    return `
      <li class="history-card" data-id="${entry.id}">
        <div class="history-card-main">
          <div class="history-card-line1">
            <span class="history-card-type">${escapeHTML(typeLabel)}</span>
            <span class="history-card-disease">${escapeHTML(entry.disease || "—")}</span>
          </div>
          <div class="history-card-line2">
            <time datetime="${escapeHTML(entry.created_at)}">
              ${escapeHTML(formatDate(entry.created_at))}
            </time>
          </div>
        </div>

        <div class="history-card-stats">
          <div class="history-card-prob">
            <span class="label">Probability</span>
            <span class="value">${escapeHTML(probPct)}</span>
          </div>
          <div class="history-card-risk ${riskClass}">
            <span class="label">Risk</span>
            <span class="value">${escapeHTML(risk)}</span>
          </div>
        </div>

        <div class="history-card-actions">
          <button type="button" class="btn btn-link" data-action="view"
                  aria-label="View details for entry ${entry.id}">View</button>
          <button type="button" class="btn btn-link btn-link--danger" data-action="delete"
                  aria-label="Delete entry ${entry.id}">Delete</button>
        </div>
      </li>
    `;
  }

  function renderList(items) {
    if (!items.length) {
      renderEmpty();
      return;
    }
    $list.innerHTML = items.map(renderCard).join("");
  }

  function renderPagination() {
    if (state.pages <= 1) {
      $pagination.hidden = true;
      return;
    }
    $pagination.hidden = false;
    $pageInd.textContent = `Page ${state.page} of ${state.pages} · ${state.total} total`;
    $prevBtn.disabled = state.page <= 1;
    $nextBtn.disabled = state.page >= state.pages;
  }

  function renderModal(entry) {
    const inputs  = entry.inputs  ? JSON.stringify(entry.inputs,  null, 2) : "—";
    const results = entry.results ? JSON.stringify(entry.results, null, 2) : "—";
    const probPct = entry.probability_percent !== null &&
                    entry.probability_percent !== undefined
      ? entry.probability_percent.toFixed(2) + "%"
      : "—";

    $modalBody.innerHTML = `
      <dl class="history-modal-grid">
        <dt>Type</dt>
        <dd>${escapeHTML(TYPE_LABELS[entry.prediction_type] || entry.prediction_type || "—")}</dd>

        <dt>Disease</dt>
        <dd>${escapeHTML(entry.disease || "—")}</dd>

        <dt>Probability</dt>
        <dd>${escapeHTML(probPct)}</dd>

        <dt>Risk level</dt>
        <dd>${escapeHTML(entry.risk_level || "—")}</dd>

        <dt>When</dt>
        <dd>${escapeHTML(formatDate(entry.created_at))}</dd>

        ${entry.notes ? `
          <dt>Notes</dt>
          <dd>${escapeHTML(entry.notes)}</dd>
        ` : ""}
      </dl>

      <details class="history-modal-raw">
        <summary>Inputs</summary>
        <pre>${escapeHTML(inputs)}</pre>
      </details>
      <details class="history-modal-raw">
        <summary>Results</summary>
        <pre>${escapeHTML(results)}</pre>
      </details>
    `;
    lastFocusedElement = document.activeElement;
    $modal.hidden = false;
    $modal.setAttribute("aria-hidden", "false");
  }

  function closeModal() {
    if (
      lastFocusedElement &&
      document.contains(lastFocusedElement)
    ) {
      lastFocusedElement.focus();
    }

    $modal.hidden = true;
    $modal.setAttribute("aria-hidden", "true");
    $modalBody.innerHTML = "";
  }

  // ----- Network ------------------------------------------------------- //

  async function fetchPage() {
    showStatus("", "");
    $loading.hidden = false;
    $list.innerHTML = "";

    const params = new URLSearchParams({
      page: state.page,
      per_page: state.perPage,
    });
    if (state.type) params.set("type", state.type);

    try {
      const resp = await fetch(`${API_BASE}?${params.toString()}`, {
        credentials: "same-origin",
        headers: { "Accept": "application/json" },
      });

      if (resp.status === 401) {
        $list.innerHTML = "";
        showStatus(
          "You need to log in to view your history.",
          "error"
        );
        $pagination.hidden = true;
        return;
      }

      if (!resp.ok) {
        showStatus(
          `Could not load history (HTTP ${resp.status}).`,
          "error"
        );
        return;
      }

      const data = await resp.json();
      state.page = data.page;
      state.pages = data.pages;
      state.total = data.total;
      renderList(data.items || []);
      renderPagination();
    } catch (err) {
      console.error("history fetch failed", err);
      showStatus("Network error — please try again.", "error");
    } finally {
      $loading.hidden = true;
    }
  }

  async function deleteEntry(id) {
    if (!window.confirm("Delete this history entry? This can't be undone.")) {
      return;
    }
    try {
      const resp = await fetch(`${API_BASE}/${encodeURIComponent(id)}`, {
        method: "DELETE",
        credentials: "same-origin",
        headers: { "Accept": "application/json" },
      });
      if (resp.ok) {
        await fetchPage();
      } else {
        showStatus("Could not delete entry.", "error");
      }
    } catch (err) {
      console.error("delete failed", err);
      showStatus("Network error while deleting.", "error");
    }
  }

  async function clearAll() {
    if (!window.confirm(
      "Delete ALL of your patient history? This can't be undone."
    )) {
      return;
    }
    try {
      const resp = await fetch(API_BASE, {
        method: "DELETE",
        credentials: "same-origin",
        headers: { "Accept": "application/json" },
      });
      if (resp.ok) {
        state.page = 1;
        await fetchPage();
      } else {
        showStatus("Could not clear history.", "error");
      }
    } catch (err) {
      console.error("clear failed", err);
      showStatus("Network error while clearing.", "error");
    }
  }

  async function viewEntry(id) {
    try {
      const resp = await fetch(`${API_BASE}/${encodeURIComponent(id)}`, {
        credentials: "same-origin",
        headers: { "Accept": "application/json" },
      });
      if (!resp.ok) {
        showStatus("Could not load entry details.", "error");
        return;
      }
      const entry = await resp.json();
      renderModal(entry);
    } catch (err) {
      console.error("view failed", err);
      showStatus("Network error while loading details.", "error");
    }
  }

  // ----- Events -------------------------------------------------------- //

  $list.addEventListener("click", function (ev) {
    const btn = ev.target.closest("button[data-action]");
    if (!btn) return;
    const card = ev.target.closest("li.history-card");
    if (!card) return;
    const id = card.dataset.id;
    if (!id) return;

    if (btn.dataset.action === "delete") {
      deleteEntry(id);
    } else if (btn.dataset.action === "view") {
      viewEntry(id);
    }
  });

  $refreshBtn.addEventListener("click", function () {
    fetchPage();
  });

  $clearBtn.addEventListener("click", clearAll);

  $typeFilter.addEventListener("change", function () {
    state.type = $typeFilter.value;
    state.page = 1;
    fetchPage();
  });

  $prevBtn.addEventListener("click", function () {
    if (state.page > 1) {
      state.page -= 1;
      fetchPage();
    }
  });

  $nextBtn.addEventListener("click", function () {
    if (state.page < state.pages) {
      state.page += 1;
      fetchPage();
    }
  });

  $modal.addEventListener("click", function (ev) {
    if (ev.target.closest("[data-close-modal]")) {
      closeModal();
    }
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape" && !$modal.hidden) closeModal();
  });

  // ----- Boot ---------------------------------------------------------- //
  fetchPage();
})();