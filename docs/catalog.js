// Author: GPT-6.1 Sol
// Date: 29-October-2026
// Updated: 30-October-2026, Claude Opus 5.5 — highlight cards plus a compact grid, both from catalog.json.
// Updated: 31-October-2026, Claude Sonnet 5.5 — a Play link on every card, to the game's page on arc3.sonpham.net.
// Updated: 31-October-2026, Claude Sonnet 5.5 — the page shows only the highlighted picks (Mark's best); the other approved games stay in catalog.json and games/. The compact card is gone.
// Updated: 01-November-2026, Claude Opus 5.5 — no human row when no play is recorded.
// PURPOSE: Render the highlighted games using safe DOM APIs.
// SRP/DRY check: Pass — catalog.json is authoritative; one card builder.
'use strict';
const SOURCE_BASE = 'https://github.com/82deutschmark/arc3-synthetic-games/blob/main/';
const INPUTS = { 1: '↑', 2: '↓', 3: '←', 4: '→', 5: 'Space', 6: 'Click', 7: 'Undo' };
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function strip(game) {
  const box = el('div', 'strip');
  box.setAttribute('role', 'img');
  box.setAttribute('aria-label', `Opening frame of each of ${game.id}'s levels`);
  box.style.setProperty('--n', game.levels);
  for (let index = 0; index < game.levels; index++) {
    const tile = el('span');
    tile.style.backgroundImage = `url("${game.media.levels}")`;
    tile.style.backgroundPosition = `${game.levels > 1 ? (index / (game.levels - 1)) * 100 : 0}% 0`;
    box.append(tile);
  }
  return box;
}
function card(game) {
  const node = el('article', 'pick');
  const image = el('img');
  image.src = game.media.play;
  image.alt = `Gameplay of ${game.id}`;
  image.width = 256;
  image.height = 256;
  const copy = el('div', 'info');
  const title = el('a', 'name', game.id.toUpperCase());
  title.href = SOURCE_BASE + game.path;
  const facts = el('dl', 'facts');
  // A game with no recorded play simply has no human row; a dash read as "nobody played this".
  const rows = [['INPUTS', (game.inputs || []).map(i => INPUTS[i]).join(' ')]];
  if (game.human) rows.unshift(['HUMAN', `${game.human.actions} actions, ${game.human.levels}/${game.levels} levels`]);
  for (const [label, value] of rows) {
    facts.append(el('dt', '', label), el('dd', '', value));
  }
  const play = el('a', 'play', 'PLAY ↗');
  play.href = game.play;
  copy.append(title, play, facts);
  copy.append(strip(game));
  node.append(image, copy);
  return node;
}
fetch('catalog.json').then(response => {
  if (!response.ok) throw new Error(`Catalog request failed (${response.status})`);
  return response.json();
}).then(catalog => {
  const picks = catalog.featured.map(id => catalog.games.find(game => game.id === id));
  document.querySelector('#count').textContent = `${picks.length} games`;
  document.querySelector('#featured').append(...picks.map(card));
}).catch(() => {
  const error = document.querySelector('#error');
  error.hidden = false;
  error.textContent = 'The catalog could not load. Reload the page.';
});
