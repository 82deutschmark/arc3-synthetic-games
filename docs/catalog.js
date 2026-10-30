// Author: GPT-6.1 Sol
// Date: 29-October-2026
// PURPOSE: Render and filter the real release catalog using safe DOM APIs.
// SRP/DRY check: Pass — catalog.json is authoritative; no duplicate game list.
'use strict';
const grid = document.querySelector('#games');
const search = document.querySelector('#search');
const view = document.querySelector('#view');
const count = document.querySelector('#count');
let games = [];
function link(label, href) {
  const anchor = document.createElement('a');
  anchor.textContent = label;
  anchor.href = href;
  return anchor;
}
function render() {
  const query = search.value.trim().toLowerCase();
  const visible = games.filter(game => game.id.includes(query) && (view.value !== 'preview' || game.preview));
  grid.replaceChildren();
  count.textContent = `${visible.length} of ${games.length} released environments`;
  if (!visible.length) {
    const empty = document.createElement('p');
    empty.textContent = 'No games match. Try another game ID.';
    grid.append(empty);
  }
  for (const game of visible) {
    const card = document.createElement('article');
    card.className = 'game';
    if (game.preview) {
      const image = document.createElement('img');
      image.src = game.preview;
      image.alt = `Initial observation of ${game.id}`;
      image.loading = 'lazy';
      image.width = 256;
      image.height = 256;
      card.append(image);
    }
    const title = document.createElement('h3');
    title.textContent = game.id;
    const links = document.createElement('div');
    links.className = 'links';
    links.append(link('Game source ↗', `https://github.com/82deutschmark/arc3-synthetic-games/blob/main/${game.path}`), link('Provenance ↗', game.source_url));
    card.append(title, links);
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
  render();
}).catch(() => {
  count.textContent = 'Collection unavailable';
  const error = document.querySelector('#error');
  error.hidden = false;
  error.textContent = 'The catalog could not load. Reload the page or use the GitHub source link above.';
});
