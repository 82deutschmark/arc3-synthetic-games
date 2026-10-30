// Author: GPT-6.1 Sol
// Date: 29-October-2026
// Updated: 30-October-2026, Claude Sonnet 5.5 Medium — featured games lead the page; the featured order comes from catalog.json.
// PURPOSE: Render and filter the real release catalog using safe DOM APIs.
// SRP/DRY check: Pass — catalog.json is authoritative; no duplicate game list.
'use strict';
const SOURCE_BASE = 'https://github.com/82deutschmark/arc3-synthetic-games/blob/main/';
const QUICK_START = 'https://github.com/82deutschmark/arc3-synthetic-games#quick-start';
const grid = document.querySelector('#games');
const search = document.querySelector('#search');
const view = document.querySelector('#view');
const count = document.querySelector('#count');
const featuredList = document.querySelector('#featured-list');
let games = [];
let featuredIds = [];
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function link(label, href, className) {
  const anchor = el('a', className, label);
  anchor.href = href;
  return anchor;
}
function levelStrip(game) {
  const tiles = game.levels || 0;
  const strip = el('div', 'strip');
  strip.setAttribute('role', 'img');
  strip.setAttribute('aria-label', `The first frame of each of ${game.id}'s ${tiles} levels`);
  strip.style.setProperty('--n', tiles);
  for (let index = 0; index < tiles; index++) {
    const tile = el('span');
    tile.style.backgroundImage = `url("${game.media.levels}")`;
    tile.style.backgroundPosition = `${tiles > 1 ? (index / (tiles - 1)) * 100 : 0}% 0`;
    strip.append(tile);
  }
  return strip;
}
function featureCard(game, position) {
  const card = el('article', 'feature');
  const screen = el('figure', 'screen');
  const image = el('img');
  image.src = game.media.opening;
  image.alt = `Level one of ${game.id}, played by a recorded winning line`;
  image.width = 320;
  image.height = 320;
  screen.append(image, el('figcaption', '', `${game.id.toUpperCase()} · LEVEL ONE, REPLAYED`));
  const copy = el('div', 'copy');
  const facts = el('dl', 'facts');
  for (const [label, value] of [['CONTROLS', game.controls], ['CREDIT', game.credit]]) {
    if (value) facts.append(el('dt', '', label), el('dd', '', value));
  }
  const strip = game.media.levels && game.levels ? [levelStrip(game), el('p', 'strip-label', 'EVERY LEVEL, FIRST FRAME')] : [];
  const actions = el('div', 'actions');
  actions.append(link('Read the source ↗', SOURCE_BASE + game.path, 'primary'), link('Run it yourself ↗', QUICK_START));
  copy.append(el('p', 'eyebrow', `FEATURED ${String(position + 1).padStart(2, '0')}${game.levels ? ` · ${game.levels} LEVELS` : ''}`),
    el('h2', '', game.id.toUpperCase()), el('p', 'note', game.note || ''), facts, ...strip, actions);
  card.append(screen, copy);
  return card;
}
function renderFeatured() {
  const picks = featuredIds.map(id => games.find(game => game.id === id)).filter(game => game && game.media && game.media.opening);
  featuredList.replaceChildren(...picks.map(featureCard));
  document.querySelector('#featured').hidden = !picks.length;
}
function render() {
  const query = search.value.trim().toLowerCase();
  const matching = games.filter(game => game.id.includes(query) && (view.value !== 'preview' || game.preview));
  // Featured games first, in the catalog's featured order; the rest keep their catalog order.
  const rank = game => (featuredIds.includes(game.id) ? featuredIds.indexOf(game.id) : featuredIds.length);
  const visible = matching.map((game, order) => ({ game, order })).sort((a, b) => rank(a.game) - rank(b.game) || a.order - b.order).map(item => item.game);
  grid.replaceChildren();
  count.textContent = `${visible.length} of ${games.length} released environments`;
  if (!visible.length) {
    grid.append(el('p', '', 'No games match. Try another game ID.'));
  }
  for (const game of visible) {
    const card = el('article', featuredIds.includes(game.id) ? 'game is-featured' : 'game');
    if (game.preview) {
      const image = el('img');
      image.src = game.preview;
      image.alt = `Initial observation of ${game.id}`;
      image.loading = 'lazy';
      image.width = 256;
      image.height = 256;
      card.append(image);
    }
    const links = el('div', 'links');
    links.append(link('Game source ↗', SOURCE_BASE + game.path));
    if (game.source_url) links.append(link('Provenance ↗', game.source_url));
    card.append(el('h3', '', game.id), links);
    grid.append(card);
  }
}
search.addEventListener('input', render);
view.addEventListener('change', render);
fetch('catalog.json').then(response => {
  if (!response.ok) throw new Error(`Catalog request failed (${response.status})`);
  return response.json();
}).then(catalog => {
  if (!Array.isArray(catalog.games)) throw new Error('Catalog is missing its game list');
  games = catalog.games;
  featuredIds = Array.isArray(catalog.featured) ? catalog.featured : [];
  renderFeatured();
  render();
}).catch(() => {
  count.textContent = 'Collection unavailable';
  const error = document.querySelector('#error');
  error.hidden = false;
  error.textContent = 'The catalog could not load. Reload the page or use the GitHub source link above.';
});
