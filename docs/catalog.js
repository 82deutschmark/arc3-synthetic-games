// Author: GPT-6.1 Sol
// Date: 29-October-2026
// Updated: 30-October-2026, Claude Opus 5.5 — highlight cards plus a compact grid, both from catalog.json.
// Updated: 31-October-2026, Claude Sonnet 5.5 — a Play link on every card, to the game's page on arc3.sonpham.net.
// Updated: 31-October-2026, Claude Sonnet 5.5 — the page shows only the highlighted picks (Mark's best); the other approved games stay in catalog.json and games/. The compact card is gone.
// Updated: 01-November-2026, Claude Opus 5.5 — no human row when no play is recorded.
// Updated: 02-November-2026, Claude Opus 5.5 High — the Boss's spoilers page: each card shows the game's rules, what is special
//   about it, its look and how it differs from the public 25, from the game's "spoiler" entry in catalog.json. No human numbers.
// Updated: 02-November-2026, Claude Opus 5.5 High — data-dense: twelve small cards, six to a row on a laptop; a click opens the
//   game's full write-up in a dialog. arc.markbarney.net mirrors this layout from the same catalog.json.
//   Same day: the catalog's "highlight" (ES01 and LT03, outbreak and air strikes, no guardrails hit) shows under the grid,
//   marks those two cards and leads their panels.
// Updated: 05-November-2026, Claude Opus 5.5 — a panel leads with "why AI struggles" (catalog spoiler.hard, plain gamer talk, with the
//   Slippery Seven cousin where there is one); the long write-up folds under FULL RULES. Play links go to the lab, which records plays.
// Updated: 04-November-2026, Claude Opus 5.5 High — each card face shows the game's short teaser (catalog "spoiler.teaser").
// Updated: 05-November-2026, Claude Sonnet 5.5 — the count line says "N best games", with no "of M": the catalog is only the games
//   in this repository, not everything the team made, and Mark's picks are a hand-picked few from far more.
// PURPOSE: Render the highlighted games using safe DOM APIs.
// SRP/DRY check: Pass — catalog.json is authoritative; one card builder.
'use strict';
const SOURCE_BASE = 'https://github.com/82deutschmark/arc3-synthetic-games/blob/main/';
// The catalog's one called-out note (two games and why), shown under the grid and in their panels.
let HIGHLIGHT = null;
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
// A card face only has room for the first sentence of "what is special".
function hook(text) {
  const match = (text || '').match(/^.*?[.!?](?=\s|$)/);
  return match ? match[0] : (text || '');
}
function keys(game) {
  return (game.inputs || []).map(i => INPUTS[i]).join(' ');
}
// The full write-up for one game, shown in the page's one <dialog>.
function openPanel(game) {
  const dialog = document.querySelector('#panel');
  const body = dialog.querySelector('.panel-body');
  const notes = game.spoiler || {};
  const side = el('div', 'side');
  const image = el('img');
  image.src = game.media.play;
  image.alt = `Opening screen of ${game.id}`;
  image.width = 256;
  image.height = 256;
  const play = el('a', 'play big', `PLAY ${game.id.toUpperCase()} ↗`);
  play.href = game.play;
  const source = el('a', 'source', 'Python source ↗');
  source.href = SOURCE_BASE + game.path;
  side.append(image, strip(game), el('p', 'meta', `${game.levels} levels · ${keys(game)}`), play, source);
  const text = el('div', 'text');
  if (HIGHLIGHT && HIGHLIGHT.games.includes(game.id)) text.append(el('p', 'flag', HIGHLIGHT.text));
  // Plain gamer talk first: why this one is hard for an AI. The long write-up folds underneath.
  if (notes.hard) text.append(section('WHY AI STRUGGLES', el('p', 'lead', notes.hard)));
  const full = el('details', 'full');
  full.append(el('summary', '', 'FULL RULES AND DETAILS'));
  if (notes.special) full.append(section('WHAT’S SPECIAL', el('p', '', notes.special)));
  if (notes.rules && notes.rules.length) {
    const list = el('ul', 'rules');
    for (const rule of notes.rules) list.append(el('li', '', rule));
    full.append(section('THE RULES', list));
  }
  if (notes.vsPublic) full.append(section('NOT IN THE PUBLIC 25', el('p', '', notes.vsPublic)));
  if (notes.look) full.append(section('THE LOOK', el('p', '', notes.look)));
  text.append(full);
  if (notes.markSaid) text.append(el('blockquote', 'said', `“${notes.markSaid}” — Mark`));
  dialog.querySelector('.panel-title').textContent = game.id.toUpperCase();
  body.replaceChildren(side, text);
  dialog.showModal();
  dialog.scrollTop = 0;
}
// A small card: opening board, code, level count, inputs, one line. The whole card opens the panel.
function card(game) {
  const node = el('button', 'pick');
  node.type = 'button';
  node.setAttribute('aria-label', `${game.id.toUpperCase()}: rules and details`);
  const image = el('img');
  image.src = game.media.play;
  image.alt = '';
  image.width = 256;
  image.height = 256;
  image.loading = 'lazy';
  const head = el('span', 'head');
  head.append(el('b', '', game.id.toUpperCase()), el('span', '', `${game.levels} LV`));
  const notes = game.spoiler || {};
  // Mark's short teaser leads the card; the first sentence of "what is special" covers a game without one.
  node.append(image, head, el('span', 'keys', keys(game)), el('span', 'hook', notes.teaser || hook(notes.special)));
  if (HIGHLIGHT && HIGHLIGHT.games.includes(game.id)) node.classList.add('flagged');
  node.addEventListener('click', () => openPanel(game));
  return node;
}
fetch('catalog.json', { cache: 'no-cache' }).then(response => {
  if (!response.ok) throw new Error(`Catalog request failed (${response.status})`);
  return response.json();
}).then(catalog => {
  HIGHLIGHT = catalog.highlight || null;
  if (HIGHLIGHT) {
    const line = document.querySelector('#highlight');
    line.textContent = HIGHLIGHT.text;
    line.hidden = false;
  }
  const picks = catalog.featured.map(id => catalog.games.find(game => game.id === id));
  document.querySelector('#count').textContent = `${picks.length} best games`;
  document.querySelector('#featured').append(...picks.map(card));
}).catch(() => {
  const error = document.querySelector('#error');
  error.hidden = false;
  error.textContent = 'The catalog could not load. Reload the page.';
});
