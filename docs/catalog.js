// Author: GPT-6.1 Sol
// Date: 29-October-2026
// Updated: 30-October-2026, Claude Opus 5.5 — highlight cards plus a compact grid, both from catalog.json.
// Updated: 31-October-2026, Claude Sonnet 5.5 — a Play link on every card, to the game's page on arc3.sonpham.net.
// Updated: 31-October-2026, Claude Sonnet 5.5 — the page shows only the highlighted picks (Mark's best); the other approved games stay in catalog.json and games/. The compact card is gone.
// Updated: 01-November-2026, Claude Opus 5.5 — no human row when no play is recorded.
// Updated: 02-November-2026, Claude Opus 5.5 High — the Boss's spoilers page: each card shows the game's rules, what is special
//   about it, its look and how it differs from the public 25, from the game's "spoiler" entry in catalog.json. No human numbers.
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
function section(label, body) {
  const box = el('section', 'part');
  box.append(el('h3', '', label), body);
  return box;
}
function card(game) {
  const node = el('article', 'spoiler');
  const pictures = el('div', 'pictures');
  const image = el('img');
  image.src = game.media.play;
  image.alt = `Opening screen of ${game.id}`;
  image.width = 256;
  image.height = 256;
  pictures.append(image, strip(game));
  const copy = el('div', 'info');
  const head = el('div', 'head');
  const title = el('a', 'name', game.id.toUpperCase());
  title.href = SOURCE_BASE + game.path;
  const play = el('a', 'play', 'PLAY ↗');
  play.href = game.play;
  head.append(title, play, el('span', 'keys', (game.inputs || []).map(i => INPUTS[i]).join(' ')));
  copy.append(head);
  // Spoilers on purpose: what we are proud of first, then the rules written out, then how it differs from ARC's public 25 and its look.
  const notes = game.spoiler || {};
  if (notes.special) copy.append(section('WHAT’S SPECIAL', el('p', 'lead', notes.special)));
  if (notes.rules && notes.rules.length) {
    const list = el('ul', 'rules');
    for (const rule of notes.rules) list.append(el('li', '', rule));
    copy.append(section('THE RULES', list));
  }
  if (notes.vsPublic) copy.append(section('NOT IN THE PUBLIC 25', el('p', '', notes.vsPublic)));
  if (notes.look) copy.append(section('THE LOOK', el('p', '', notes.look)));
  if (notes.markSaid) copy.append(el('blockquote', 'said', `“${notes.markSaid}” — Mark`));
  node.append(pictures, copy);
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
