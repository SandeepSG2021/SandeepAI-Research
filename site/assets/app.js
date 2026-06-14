/* SandeepAI Research — front-end controller
   Loads /data/<source>.json on tab click and renders cards. */

const TABS = [
  { id: "arxiv",     label: "ARXIV-AI",     file: "data/arxiv.json",     external: "https://arxiv.org/list/cs.AI/recent" },
  { id: "google",    label: "Google-AI",    file: "data/google.json",    external: "https://ai.google/research/" },
  { id: "microsoft", label: "Microsoft-AI", file: "data/microsoft.json", external: "https://www.microsoft.com/en-us/research/research-area/artificial-intelligence/" },
  { id: "openai",    label: "OpenAI-AI",    file: "data/openai.json",    external: "https://openai.com/research/" },
  { id: "anthropic", label: "Anthropic-AI",  file: "data/anthropic.json", external: "https://www.anthropic.com/research" },
  { id: "meta",      label: "Meta-AI",      file: "data/meta.json",      external: "https://ai.meta.com/research/" },
];

const cache = new Map();
const tabsEl   = document.querySelector(".tabs");
const papersEl = document.getElementById("papers");
const emptyEl  = document.getElementById("empty");
const stampEl  = document.getElementById("lastUpdated");

function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k === "class") node.className = v;
    else if (k === "html") node.innerHTML = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const c of children.flat()) {
    if (c == null) continue;
    node.appendChild(typeof c === "string" ? document.createTextNode(c) : c);
  }
  return node;
}

function renderTabs(activeId) {
  tabsEl.innerHTML = "";
  for (const t of TABS) {
    const count = cache.get(t.id)?.papers?.length ?? "";
    const btn = el("button", {
      class: "tab-btn",
      role: "tab",
      "aria-selected": String(t.id === activeId),
      "data-id": t.id,
      onclick: () => selectTab(t.id),
    }, t.label, count !== "" ? el("span", { class: "count" }, String(count)) : null);
    tabsEl.appendChild(btn);
  }
}

function renderBullets(items) {
  if (!items || !items.length) return null;
  return el("ul", {}, items.map((x) => el("li", {}, x)));
}

function renderCard(paper, sourceLabel) {
  const titleNode = paper.link
    ? el("h3", {}, el("a", { href: paper.link, target: "_blank", rel: "noopener" }, paper.title || "Untitled"))
    : el("h3", {}, paper.title || "Untitled");

  const byline = el("div", { class: "byline" },
    el("span", { class: "src" }, sourceLabel),
    paper.authors ? el("span", { class: "dot" }, "·") : null,
    paper.authors ? el("span", {}, paper.authors) : null,
    paper.published ? el("span", { class: "dot" }, "·") : null,
    paper.published ? el("span", {}, paper.published) : null,
  );

  const sections = [];

  if (paper.summary) {
    sections.push(el("div", { class: "section-block summary" },
      el("h4", {}, "Summary"),
      el("p", {}, paper.summary)
    ));
  }

  const bcase = paper.insurance_business_case;
  if (bcase) {
    const body = typeof bcase === "string"
      ? el("p", {}, bcase)
      : el("div", {},
          bcase.headline ? el("p", {}, el("strong", {}, bcase.headline)) : null,
          renderBullets(bcase.points),
        );
    sections.push(el("div", { class: "section-block bcase" },
      el("h4", {}, "Insurance Business Case (Life & Health)"),
      body,
    ));
  }

  const tech = paper.technical_details;
  if (tech) {
    const body = typeof tech === "string"
      ? el("p", {}, tech)
      : el("div", {},
          tech.pattern ? el("p", {}, el("strong", {}, tech.pattern)) : null,
          renderBullets(tech.points),
        );
    sections.push(el("div", { class: "section-block tech" },
      el("h4", {}, "Technical Details"),
      body,
    ));
  }

  const tags = (paper.tags || []).length
    ? el("div", { class: "tags" }, paper.tags.map((t) => el("span", { class: "tag" }, t)))
    : null;

  return el("article", { class: "card glass" }, titleNode, byline, ...sections, tags);
}

async function loadTab(id) {
  if (cache.has(id)) return cache.get(id);
  const tab = TABS.find((t) => t.id === id);
  try {
    const res = await fetch(tab.file, { cache: "no-cache" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    cache.set(id, json);
    return json;
  } catch (err) {
    console.error(`Failed to load ${tab.file}`, err);
    cache.set(id, { papers: [], error: err.message });
    return cache.get(id);
  }
}

async function selectTab(id) {
  const data = await loadTab(id);
  renderTabs(id);
  papersEl.innerHTML = "";

  const tab = TABS.find((t) => t.id === id);
  const papers = data?.papers || [];
  if (!papers.length) {
    emptyEl.classList.remove("hidden");
    emptyEl.querySelector("h3").textContent =
      data?.error ? `Could not load ${tab.label}` : `No papers yet for ${tab.label}`;
    return;
  }
  emptyEl.classList.add("hidden");
  for (const p of papers) papersEl.appendChild(renderCard(p, tab.label));

  if (data.last_updated) {
    stampEl.textContent = `Updated ${data.last_updated}`;
  }
}

async function boot() {
  // Pre-warm all caches so tab counts and "last updated" reflect reality.
  await Promise.all(TABS.map((t) => loadTab(t.id)));

  // Pick the freshest tab as the default landing tab.
  let bestId = TABS[0].id;
  let bestStamp = "";
  for (const t of TABS) {
    const ts = cache.get(t.id)?.last_updated || "";
    if (ts > bestStamp) { bestStamp = ts; bestId = t.id; }
  }
  selectTab(bestId);
}

boot();
