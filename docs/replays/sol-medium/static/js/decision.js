// The decision panel: every LLM call of a turn -- reasoning, the python it ran, what came back.
//
// The raw transcript is a ~38KB wall of text. The backend already splits it into an ordered
// interleave of [THINKING] / [TOOL CALL: python] / [TOOL RESULT: python] / [ASSISTANT] sections,
// so the job here is ordering and triage: lead with what the model did, collapse what it was
// told, and diff the one part of the prompt that actually changes.

import { annotateCoordRefs, MODE } from "./coords.js?v=20261030-diffpane";
import { decodeBoard, paintDiffThumb, paintThumb } from "./board.js?v=20261030-diffpane";
import { createVotes } from "./trace-votes.js?v=20261002-votes";

const NOISE = /^(MODEL CONTEXT|MODEL RESPONSE META|PROMPT LOG SNAPSHOT|ACTION_RESPONSE)$/i;
const IS_CODE = /^TOOL CALL/i;
const IS_SYSTEM = /^SYSTEM PROMPT$/i;
const IS_USER = /^USER PROMPT$/i;

// A per-type colour cue, keyed off the section label so it is finer than the
// backend `kind` (which lumps THINKING+ASSISTANT and TOOL CALL+TOOL RESULT).
// The `t-*` class picks the accent colour in app.css.
function typeClass(label) {
  const l = String(label || "").toUpperCase();
  if (l.startsWith("USER PROMPT")) return "t-user";        // green
  if (l.startsWith("SYSTEM PROMPT")) return "t-system";    // neutral
  if (l.startsWith("THINKING")) return "t-thinking";       // blue
  if (l.startsWith("ASSISTANT")) return "t-assistant";     // purple
  if (l.startsWith("TOOL CALL")) return "t-toolcall";      // orange
  if (l.startsWith("TOOL RESULT")) return "t-toolresult";  // amber
  if (l.startsWith("ERROR")) return "t-error";             // red
  return "";
}

// `feedback` names the turn being shown ({ run, gameIndex, gameId, stepIndex, turn }). With it,
// each section of model output gets thumbs up / thumbs down; without it there is nothing stable to
// attach a mark to, so no thumbs.
// Both views file a mark under the section's place in this turn's own transcript
// (step.localContext.sections), so a mark made in one view shows in the other.
// `modelImages` ({diff, fatal, flags} from main.js) adds the harness's diff images to the "frames received" gallery.
export function renderDecision(root, step, { currentClick, previousStep, mode = "review", showFrames = true, feedback = null, modelImages = null } = {}) {
  root.innerHTML = "";
  if (!step) {
    root.innerHTML = '<div class="empty">No analyzer turn for this frame.</div>';
    return;
  }

  const votes = feedback ? createVotes(feedback) : null;
  root.appendChild(renderHead(step, currentClick));
  if (mode === "literal") {
    root.appendChild(renderLiteral(step, votes));
    votes?.load();
    return;
  }
  if (showFrames) root.appendChild(renderAbsorbedFrames(step, modelImages));

  // A mark is filed under the section's place in the stored transcript, noise included.
  const position = new Map((step.localContext?.sections || []).map((s, index) => [s, index]));
  const sections = (step.localContext?.sections || []).filter((s) => !NOISE.test(s.label || ""));
  if (!sections.length) {
    root.insertAdjacentHTML("beforeend", '<div class="empty">No transcript for this turn.</div>');
    return;
  }

  // The transcript IS the conversation, so render it in order: prompt, think, call, result,
  // nag, think, call... Reordering it into buckets destroys the thing a reviewer is reading for.
  const previous = previousStep?.localContext?.sections || [];
  // Each user prompt is diffed against the one before it in the conversation -- which is exactly
  // the delta the model saw. The first of a turn diffs against the previous turn's last, so the
  // chain is unbroken across turn boundaries.
  let priorPrompt = lastContent(previous, "USER PROMPT");

  let call = 0;
  for (const section of sections) {
    if (IS_SYSTEM.test(section.label)) {
      const unchanged = normalize(lastContent(previous, "SYSTEM PROMPT")) === normalize(section.content);
      root.appendChild(renderSection(section, { open: false, note: unchanged ? "unchanged" : "" }));
      continue;
    }
    if (IS_USER.test(section.label)) {
      root.appendChild(renderPrompt(section, priorPrompt));
      priorPrompt = String(section.content || "");
      continue;
    }
    if (IS_CODE.test(section.label)) call += 1;
    const details = renderSection(section, { open: true, call: IS_CODE.test(section.label) ? call : 0 });
    if (votes && literalDirection(section.label) === "output") {
      votes.attach(details, { sectionIndex: position.get(section), label: section.label, content: section.content || "" });
    }
    root.appendChild(details);
  }

  root.appendChild(renderRaw(step));
  votes?.load();
}

/**
 * The literal view lists the whole saved request -- earlier turns included -- so its rows are
 * numbered differently from this turn's transcript. Find which rows are this turn's own output
 * and return row -> the transcript section it is. This turn's sections are the last ones, so
 * match from the end. Earlier turns' text gets no thumbs here: it is marked on its own turn.
 */
function ownOutput(step, shown) {
  const local = step.localContext?.sections || [];
  const same = (a, b) => a.label === b.label && String(a.content || "").trim() === String(b.content || "").trim();
  const found = new Map();
  // Never look above where this turn starts in the list (its first prompt), so a row from an
  // earlier turn that happens to hold the same words is not given this turn's thumbs.
  const opening = local.find((s) => IS_USER.test(s.label || ""));
  let floor = 0;
  if (opening) for (let row = shown.length - 1; row >= 0; row -= 1) if (same(shown[row], opening)) { floor = row; break; }
  let cursor = shown.length - 1;
  for (let index = local.length - 1; index >= 0; index -= 1) {
    if (literalDirection(local[index].label) !== "output") continue;
    for (let row = cursor; row >= floor; row -= 1) {
      if (!same(shown[row], local[index])) continue;
      found.set(shown[row], { sectionIndex: index, section: local[index] });
      cursor = row - 1;
      break;
    }
  }
  return found;
}

function renderLiteral(step, votes = null) {
  const wrap = document.createElement("section");
  wrap.className = "literal-trace";
  const modelContext = step.context || step.localContext || {};
  const exact = step.traceInputExact === true || modelContext.hasExactModelContext === true;
  const timestamp = String(step.traceTimestamp || "timestamp unavailable in this export");
  const basis = String(step.traceTimestampBasis || "no timestamp metadata");
  const source = exact ? "Exact saved request context" : "Stored transcript reconstruction";

  const notice = document.createElement("div");
  notice.className = `literal-notice ${exact ? "is-exact" : "is-reconstructed"}`;
  notice.innerHTML = `<b>${escapeHtml(source)}</b><span>${escapeHtml(timestamp)} · ${escapeHtml(basis)}</span>`;
  if (!exact) {
    notice.insertAdjacentHTML("beforeend", "<small>Section text is shown verbatim. Older TAAF runs did not save the exact request JSON, so input-context membership is inferred from the transcript.</small>");
  }
  wrap.appendChild(notice);

  const sections = modelContext.sections || [];
  if (!sections.length) {
    wrap.insertAdjacentHTML("beforeend", '<div class="empty">No stored model input/output for this turn.</div>');
    return wrap;
  }

  const own = votes ? ownOutput(step, sections) : new Map();
  for (const section of sections) {
    const direction = literalDirection(section.label);
    const record = document.createElement("article");
    record.className = `literal-record is-${direction}`;
    const head = document.createElement("div");
    head.className = "literal-record-head";
    const contextTag = section.inContext === false
      ? (exact ? " · not present in captured request" : " · context carry not verified")
      : "";
    head.innerHTML = `<b>${escapeHtml(direction.toUpperCase())}</b><span>${escapeHtml(section.label || "SECTION")}${escapeHtml(contextTag)}</span><time>${escapeHtml(timestamp)}</time>`;
    const pre = document.createElement("pre");
    pre.textContent = String(section.content || "");
    record.append(head, pre);
    const mine = own.get(section);
    // The mark is saved against the transcript's copy of the text, so it is the same mark
    // (same words, same hash) the review view shows.
    if (mine) votes.attach(record, { head, sectionIndex: mine.sectionIndex, label: mine.section.label, content: mine.section.content || "" });
    wrap.appendChild(record);
  }
  return wrap;
}

function literalDirection(label) {
  const value = String(label || "").toUpperCase();
  if (value === "SYSTEM PROMPT" || value === "USER PROMPT" || value.startsWith("TOOL RESULT")) return "input";
  if (value === "THINKING" || value === "ASSISTANT" || value === "OUTPUT" || value.startsWith("TOOL CALL")) return "output";
  return "trace";
}

// The harness tells the model about the diff image in its system prompt only when ARC3_DIFF_IMAGE is on, so runs
// exported before run-overview carried harnessImages still say whether they sent it.
const DIFF_IMAGE_SENTENCE = /you receive a diff image/i;

function harnessSends(step, flags, key) {
  if (typeof flags?.[key] === "boolean") return flags[key];
  if (key !== "diffImage") return null;
  const sections = step.localContext?.sections || step.context?.sections || [];
  return sections.some((s) => IS_SYSTEM.test(s.label || "") && DIFF_IMAGE_SENTENCE.test(String(s.content || "")));
}

function figureWith(gallery, caption, paint) {
  const figure = document.createElement("figure");
  const canvas = document.createElement("canvas");
  const label = document.createElement("figcaption");
  figure.append(canvas, label);
  gallery.appendChild(figure);
  const text = paint(canvas);
  label.textContent = typeof text === "string" ? text : caption;
}

function renderAbsorbedFrames(step, modelImages = null) {
  const explicit = Array.isArray(step.absorbedFrames) ? step.absorbedFrames : [];
  const fallback = step.boardEvent ? [{
    label: "Current settled frame (attached to the model)",
    board: step.boardEvent.board,
    board_ascii: step.boardEvent.board_ascii,
  }] : [];
  const frames = explicit.length ? explicit : fallback;
  const section = document.createElement("section");
  section.className = "absorbed-frames";

  const heading = document.createElement("div");
  heading.className = "absorbed-frames-title";
  heading.textContent = "Frames the model received for this reasoning step";
  section.appendChild(heading);

  const gallery = document.createElement("div");
  gallery.className = "absorbed-frames-gallery";
  for (const frame of frames) {
    figureWith(gallery, frame.label || "Frame seen by model", (canvas) => paintThumb(canvas, frame.board || frame.board_ascii, 3));
  }

  // Son 30-Oct-2026: "show the diff image next to it as well, given that in our harness we also do diff map". Redrawn
  // from the frames by the harness's own rules (main.js modelDiffFor / fatalDiffFor); checked against E7's request logs.
  const flags = modelImages?.flags || null;
  const notes = [];
  const diff = modelImages?.diff;
  if (diff && harnessSends(step, flags, "diffImage")) {
    if (diff.reference) {
      figureWith(gallery, "", (canvas) => {
        const changed = paintDiffThumb(canvas, diff.current.board_ascii, diff.reference.board_ascii, 3);
        return `Diff image, ${diff.span} (attached to the model): ${changed} changed cell${changed === 1 ? "" : "s"} in their new colour, the rest navy`;
      });
    } else if (diff.reason) {
      notes.push(`No diff image this turn (${diff.reason.replace(/: no diff image$/, "")}).`);
    }
  }
  const fatal = modelImages?.fatal;
  const fatalOn = harnessSends(step, flags, "gameoverDiffImage");
  if (fatal && fatalOn !== false) {
    const sent = fatalOn === true ? "attached to the model" : "sent when ARC3_GAMEOVER_DIFF_IMAGE is on";
    figureWith(gallery, "", (canvas) => {
      const changed = paintDiffThumb(canvas, fatal.death.board_ascii, fatal.alive.board_ascii, 3);
      return `Fatal step diff image, last alive frame → death frame, ${fatal.span} (${sent}): ${changed} changed cell${changed === 1 ? "" : "s"}`;
    });
  }

  if (!gallery.children.length) {
    section.insertAdjacentHTML("beforeend", '<div class="empty">Frame input was not recorded for this turn.</div>');
  } else {
    section.appendChild(gallery);
  }
  for (const note of notes) {
    const line = document.createElement("div");
    line.className = "absorbed-frames-note";
    line.textContent = note;
    section.appendChild(line);
  }
  if (step.animation) section.appendChild(renderAnimation(step, flags));
  return section;
}

// Son 31-Oct-2026: "When clicking on each turns, shows the animation frame that was feeding in as well. I need to have a
// sense of what was put in". The harness (ARC3_ANIMATION=1) keeps the frames of the last move before the call. It
// attaches no picture of them (ARC3_ANIMATION_IMAGE off); the opener names them in one line only when cells changed and
// changed back, and the model can read them from Python. step.animation comes from scripts/export_animations.py
// (the run's intermediate_states.pkl): the board before the move, then each frame as changes to the one before.
const READS_ANIMATION = /last_animation_frames|last_animation_timeline|last_transition\.frames/g;

function animationGrids(anim) {
  const first = decodeBoard(anim.before);
  if (!first) return [];
  const grids = [first];
  for (const delta of anim.deltas || []) {
    const next = grids[grids.length - 1].map((row) => row.slice());
    for (let i = 0; i + 2 < delta.length; i += 3) {
      if (next[delta[i]]) next[delta[i]][delta[i + 1]] = delta[i + 2];
    }
    grids.push(next);
  }
  return grids;
}

function paintAnimationFrame(canvas, grid, anim, cell) {
  paintThumb(canvas, grid, cell);
  if (!anim.bbox) return;
  const [top, left, bottom, right] = anim.bbox;   // where cells changed and changed back
  const ctx = canvas.getContext("2d");
  ctx.lineWidth = Math.max(1, cell / 2);
  ctx.setLineDash([cell * 2, cell]);
  ctx.strokeStyle = "#ffffff";
  ctx.strokeRect(left * cell - 1, top * cell - 1, (right - left + 1) * cell + 2, (bottom - top + 1) * cell + 2);
}

function renderAnimation(step, flags) {
  const anim = step.animation;
  const grids = animationGrids(anim);
  const box = document.createElement("div");
  box.className = "anim";
  const title = document.createElement("div");
  title.className = "absorbed-frames-title";
  title.textContent = `Animation of the last move before this turn: ${anim.action || "move"} (move ${anim.actionNum}), `
    + `${anim.frames} frame${anim.frames === 1 ? "" : "s"} after the board before it`;
  box.appendChild(title);

  const how = [];
  if (flags?.animation === false) {
    how.push("This run's harness had ARC3_ANIMATION off: the model could not read these frames at all.");
  } else {
    const picture = flags?.animationImage && flags.animationImage !== "off";
    how.push(picture
      ? `Picture: the harness attaches one (ARC3_ANIMATION_IMAGE=${flags.animationImage}) only when the move left the board unchanged.`
      : "Not attached as a picture: the model got only the settled board above.");
    if (anim.notice) {
      how.push(`Its opener said: “${anim.notice}”`
        + (anim.noticeMatches === false ? " (these frames do not match that line's counts: it may describe a neighbouring move)" : ""));
    } else {
      how.push("Its opener said nothing about it: no cell changed and changed back, so the settled board already shows where everything ended.");
    }
    const code = (step.localContext?.sections || step.context?.sections || [])
      .filter((s) => IS_CODE.test(s.label || "")).map((s) => String(s.content || "")).join("\n");
    const reads = [...new Set(code.match(READS_ANIMATION) || [])];
    how.push(reads.length
      ? `This turn's code read ${reads.join(" and ")}.`
      : "This turn's code did not read the frames (last_animation_frames / last_animation_timeline).");
  }
  for (const text of how) {
    const line = document.createElement("div");
    line.className = "absorbed-frames-note";
    line.textContent = text;
    box.appendChild(line);
  }
  if (!grids.length) return box;

  const player = document.createElement("div");
  player.className = "anim-player";
  const canvas = document.createElement("canvas");
  const controls = document.createElement("div");
  controls.className = "anim-controls";
  controls.innerHTML = '<button type="button" data-a="prev" aria-label="Previous frame">◀</button>'
    + '<button type="button" data-a="play">Play</button>'
    + '<button type="button" data-a="next" aria-label="Next frame">▶</button>'
    + `<input type="range" min="0" max="${grids.length - 1}" value="0" aria-label="Animation frame">`
    + '<span class="anim-pos"></span>';
  player.append(canvas, controls);
  box.appendChild(player);

  const strip = document.createElement("div");
  strip.className = "anim-strip";
  grids.forEach((grid, i) => {
    const thumb = document.createElement("canvas");
    thumb.title = i ? `Frame ${i} of ${grids.length - 1}` : "Before the move";
    paintAnimationFrame(thumb, grid, anim, 1);
    thumb.addEventListener("click", () => { stop(); show(i); });
    strip.appendChild(thumb);
  });
  box.appendChild(strip);
  if (anim.bbox) {
    const key = document.createElement("div");
    key.className = "absorbed-frames-note";
    key.textContent = `Dashed box: the ${anim.transient} cell${anim.transient === 1 ? "" : "s"} that changed and changed back `
      + "(they are in no board the model sees unless its code reads these frames).";
    box.appendChild(key);
  }

  const slider = controls.querySelector("input");
  const pos = controls.querySelector(".anim-pos");
  const playButton = controls.querySelector('[data-a="play"]');
  let current = 0;
  let timer = null;
  function show(i) {
    current = (i + grids.length) % grids.length;
    paintAnimationFrame(canvas, grids[current], anim, 4);
    slider.value = String(current);
    pos.textContent = current ? `frame ${current} of ${grids.length - 1}` : "before the move";
    strip.querySelectorAll("canvas").forEach((c, k) => c.classList.toggle("on", k === current));
  }
  function stop() {
    clearInterval(timer);
    timer = null;
    playButton.textContent = "Play";
  }
  controls.addEventListener("click", (event) => {
    const action = event.target.closest("button")?.dataset.a;
    if (action === "prev" || action === "next") { stop(); show(current + (action === "next" ? 1 : -1)); }
    if (action !== "play") return;
    if (timer) { stop(); return; }
    playButton.textContent = "Pause";
    timer = setInterval(() => {
      if (!canvas.isConnected) { stop(); return; }   // the panel was redrawn for another turn
      show(current + 1);
    }, 450);
  });
  slider.addEventListener("input", () => { stop(); show(Number(slider.value)); });
  show(0);
  return box;
}

function renderHead(step, currentClick) {
  const head = document.createElement("div");
  head.className = "decision-head";

  const title = document.createElement("div");
  title.className = "turn-title";
  title.textContent = step.title || "Turn";
  head.appendChild(title);

  const actions = String(step.actionDisplay || "").split("->").map((a) => a.trim()).filter(Boolean);
  if (actions.length) {
    const chips = document.createElement("div");
    chips.className = "chips";
    for (const action of actions) {
      const chip = document.createElement("span");
      chip.className = "chip";
      chip.textContent = action;
      if (currentClick && action.includes(`row=${currentClick.row}`) && action.includes(`col=${currentClick.col}`)) {
        chip.classList.add("current");
      }
      chips.appendChild(chip);
    }
    head.appendChild(chips);
    annotateCoordRefs(chips, MODE.PROSE);
  }

  const bits = [];
  if (step.reward) bits.push(`reward ${step.reward > 0 ? "+" : ""}${step.reward}`);
  bits.push(`score ${step.score ?? 0}`);
  bits.push(`level ${step.level ?? "?"}`);
  if (step.toolCallCount) bits.push(`${step.toolCallCount} tool calls`);
  if (step.attemptCount > 1) bits.push(`${step.attemptCount} attempts`);
  if (step.llm) {
    if (step.llm.promptTokens || step.llm.completionTokens) {
      bits.push(`in ${fmtK(step.llm.promptTokens)} / out ${fmtK(step.llm.completionTokens)}`);
    }
    if (step.llm.errors) bits.push(`${step.llm.errors} errors`);
  }
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = step.metaText ?? bits.join(" · ");
  head.appendChild(meta);

  return head;
}

function renderSection(section, { open, call = 0, note = "" }) {
  const label = section.label || "SECTION";
  const content = section.content || "";
  const details = document.createElement("details");
  details.className = `section kind-${section.kind || "text"} ${typeClass(label)}`.trim();
  details.open = open;
  details.appendChild(summaryFor(label, content.length, { call, note }));

  const pre = document.createElement("pre");
  pre.textContent = content;
  details.appendChild(pre);

  const annotate = () => annotateCoordRefs(pre, IS_CODE.test(label) ? MODE.CODE : MODE.PROSE);
  if (open) annotate();
  else details.addEventListener("toggle", () => details.open && annotate(), { once: true });
  return details;
}

/**
 * The user prompt is ~3KB of board state resent every turn. What a reviewer needs is the
 * delta, so highlight the changed lines and let the unchanged bulk collapse away.
 */
function renderPrompt(section, previousContent) {
  const lines = String(section.content || "").split("\n");
  const before = new Set(String(previousContent || "").split("\n"));
  const changed = previousContent ? lines.filter((line) => !before.has(line)).length : lines.length;

  const details = document.createElement("details");
  details.className = `section kind-meta ${typeClass(section.label)}`.trim();
  details.appendChild(
    summaryFor(section.label, section.content.length, {
      note: previousContent ? (changed ? `${changed} changed lines` : "unchanged") : "",
    }),
  );

  const render = () => {
    const pre = document.createElement("pre");
    pre.className = "prompt";
    for (const line of lines) {
      const row = document.createElement("div");
      row.className = previousContent && !before.has(line) ? "line changed" : "line";
      row.textContent = line || " ";
      pre.appendChild(row);
    }
    details.appendChild(pre);
    annotateCoordRefs(pre, MODE.PROSE);
  };
  // 3KB of DOM nobody reads until they open it.
  details.addEventListener("toggle", () => details.open && !details.querySelector("pre") && render(), { once: true });
  return details;
}

function renderRaw(step) {
  const sections = step.localContext?.sections || [];
  const raw = sections.map((s) => `[${s.label}]\n${s.content}`).join("\n\n");
  const details = document.createElement("details");
  details.className = "section kind-meta";
  details.appendChild(summaryFor("RAW TRANSCRIPT", raw.length, {}));
  details.addEventListener("toggle", () => {
    if (!details.open || details.querySelector("pre")) return;
    const pre = document.createElement("pre");
    pre.textContent = raw;
    details.appendChild(pre);
  }, { once: true });
  return details;
}

function summaryFor(label, size, { call = 0, note = "" }) {
  const summary = document.createElement("summary");
  const name = call ? `${label} #${call}` : label;
  summary.innerHTML =
    `<span>${escapeHtml(name)}</span><span class="spacer"></span>` +
    (note ? `<span class="note">${escapeHtml(note)}</span>` : "") +
    `<span class="size">${fmtBytes(size)}</span>`;
  return summary;
}

function lastContent(sections, label) {
  for (let i = sections.length - 1; i >= 0; i -= 1) {
    if (sections[i]?.label === label) return String(sections[i].content || "");
  }
  return "";
}

const normalize = (value) => String(value || "").replaceAll("\r\n", "\n").trimEnd();

function fmtK(value) {
  const n = Number(value || 0);
  return n >= 1000 ? `${(n / 1000).toFixed(1)}K` : String(n);
}

function fmtBytes(n) {
  return n >= 1024 ? `${(n / 1024).toFixed(1)} KB` : `${n} B`;
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  })[c]);
}

export { fmtK };
