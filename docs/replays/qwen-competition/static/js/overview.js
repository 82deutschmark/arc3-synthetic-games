// The run overview: every game in the run, at once.
// 17-Oct-2026 (Main): runs that mix the official 25 with copycats or generated games get an "All games / Official 25"
// switch (remembered per browser); cards keep their run index, so opening a filtered card opens the right game.
// 18-Oct-2026 (Main; Son: "when inspecting each run, still show all"): the switch starts on All games.
// The thumbnails were all black: board.js must be imported with the same URL as main.js, or the browser loads a
// second copy whose palette main.js never sets, and every cell paints the "#000" fallback.

import { paintThumb } from "./board.js?v=20261030-diffpane";
import { isOfficialGame } from "./official-games.js";

const SET_KEY = "arc3-overview-game-set";
const readSet = () => { try { return localStorage.getItem(SET_KEY) || "all"; } catch { return "all"; } };
const writeSet = (value) => { try { localStorage.setItem(SET_KEY, value); } catch { /* private window */ } };

export function renderOverview(root, totalsEl, payload, { onOpen, filterEl }) {
  const all = (payload.games || []).map((game, index) => ({ game, index }));
  const officialCount = all.filter(({ game }) => isOfficialGame(game.game_id)).length;
  const mixed = officialCount > 0 && officialCount < all.length;
  const set = mixed ? readSet() : "all";
  const shown = set === "official" ? all.filter(({ game }) => isOfficialGame(game.game_id)) : all;
  if (filterEl) {
    filterEl.hidden = !mixed;
    filterEl.innerHTML = mixed ? `<span class="mode-seg" role="group" aria-label="Games shown">
      <button type="button" data-set="all" class="${set === "all" ? "on" : ""}">All games (${all.length})</button>
      <button type="button" data-set="official" class="${set === "official" ? "on" : ""}">Official 25 (${officialCount})</button>
    </span>` : "";
    filterEl.querySelectorAll("button[data-set]").forEach((button) => button.addEventListener("click", () => {
      writeSet(button.dataset.set);
      renderOverview(root, totalsEl, payload, { onOpen, filterEl });
    }));
  }
  const games = shown.map(({ game }) => game);
  renderTotals(totalsEl, games);

  root.innerHTML = "";
  if (!games.length) {
    root.innerHTML = '<div class="empty">No games in this run yet.</div>';
    return;
  }

  // A multi-pass run repeats every game_id, so the pass has to be on the card or the cards lie.
  const multiPass = new Set(games.map((g) => g.game_id)).size < games.length;

  shown.forEach(({ game, index }) => {
    const pass = multiPass && game.pass_label !== undefined ? ` <span class="pass">p${escapeHtml(game.pass_label)}</span>` : "";
    const card = document.createElement("div");
    card.className = `card is-${game.status || "unknown"}`;
    card.innerHTML = `
      <div class="card-head">
        <span class="game-id">${escapeHtml(game.game_id || "?")}${pass}</span>
        <span class="card-status status-${game.status}">${escapeHtml(game.status || "")}</span>
      </div>
      <canvas></canvas>
      <div class="levelbar"></div>
      <div class="card-meta">
        <span>L ${game.levels_completed ?? 0}/${game.total_levels ?? "?"}</span>
        ${game.final_score != null ? `<span>score ${Number(game.final_score).toFixed(1)}</span>` : ""}
        <span>${game.actionCount ?? 0} actions</span>
      </div>`;

    paintThumb(card.querySelector("canvas"), game.board_ascii, 2);
    renderLevelBar(card.querySelector(".levelbar"), game);
    card.addEventListener("click", () => onOpen(index));
    root.appendChild(card);
  });
}

function renderLevelBar(bar, game) {
  const total = game.total_levels || (game.actions_per_level || []).length || 1;
  const done = game.levels_completed ?? 0;
  const perLevel = game.actions_per_level || [];
  for (let i = 0; i < total; i += 1) {
    const cell = document.createElement("i");
    if (i < done) cell.className = "done";
    else if (perLevel[i]) cell.className = "active"; // started but not cleared
    bar.appendChild(cell);
  }
}

function renderTotals(el, games) {
  const count = (status) => games.filter((g) => g.status === status).length;
  const sum = (key) => games.reduce((total, g) => total + (g[key] || 0), 0);
  const levels = games.reduce((total, g) => total + (g.levels_completed || 0), 0);
  const totalLevels = games.reduce((total, g) => total + (g.total_levels || 0), 0);

  // 17-Oct: the run's score over the games shown (mean of each game's final_score, the board's per-game score)
  const scored = games.filter((g) => g.final_score != null);
  const score = scored.length ? (scored.reduce((total, g) => total + Number(g.final_score), 0) / games.length).toFixed(2) : "—";
  const stats = [
    ["score", score],
    ["games", games.length],
    ["win", count("win") + count("won")],   // exports write "won" (17-Oct: the counter showed 0)
    ["playing", count("playing")],
    ["gave up", count("gave_up")],
    ["levels", `${levels}/${totalLevels}`],
    ["actions", sum("actionCount").toLocaleString()],
  ];

  el.innerHTML = stats
    .map(([label, value]) => `<div class="stat"><div class="label">${label}</div><div class="value">${value}</div></div>`)
    .join("");
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}
