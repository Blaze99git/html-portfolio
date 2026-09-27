(() => {
  const form = document.getElementById("ask-form");
  const input = document.getElementById("question");
  const button = document.getElementById("ask-button");
  const chat = document.getElementById("chat-body");
  const mode = document.getElementById("engine-mode");
  let corpus = [];
  const stopwords = new Set(["a", "about", "after", "an", "and", "are", "at", "be", "before", "by", "do", "for", "from", "how", "i", "if", "in", "is", "it", "me", "my", "of", "on", "or", "should", "the", "this", "to", "what", "when", "where", "which", "with", "you"]);
  const tokenize = (text) => (text.toLowerCase().match(/[a-z0-9]+/g) || []).filter((word) => !stopwords.has(word));
  const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
  const intentTerms = {
    maintenance: new Set(["alarm", "air", "compressor", "equipment", "gauge", "lubrication", "maintenance", "pressure", "regulator", "repair", "service"]),
    quality: new Set(["defect", "inspection", "quality", "reject", "retry", "serial", "test", "trace", "weld", "hold"]),
    data: new Set(["communication", "flag", "freshness", "plc", "quality", "signal", "stale", "tag", "timestamp", "telemetry"]),
    operations: new Set(["downtime", "handover", "line", "operator", "shift", "station", "start", "stop", "work", "order"]),
  };
  const intentLabels = {
    maintenance: "maintenance notes",
    quality: "quality procedures",
    data: "signal health notes",
    operations: "operations procedures",
    all: "full knowledge library",
  };

  function classifyIntent(query) {
    const terms = new Set(tokenize(query));
    const scores = Object.fromEntries(Object.entries(intentTerms).map(([category, keywords]) => [category, [...terms].filter((term) => keywords.has(term)).length]));
    const priority = ["maintenance", "data", "quality", "operations"];
    const best = [...priority].sort((a, b) => scores[b] - scores[a] || priority.indexOf(a) - priority.indexOf(b))[0];
    return scores[best] ? best : "all";
  }

  async function loadCorpus() {
    try {
      const response = await fetch("data/knowledge_base.json");
      if (!response.ok) throw new Error("Knowledge data did not load");
      corpus = await response.json();
    } catch (error) {
      mode.textContent = "KNOWLEDGE LIBRARY UNAVAILABLE";
      corpus = [];
    }
  }

  function localSearch(query) {
    const queryTerms = tokenize(query);
    if (!queryTerms.length || !corpus.length) return [];
    const category = classifyIntent(query);
    const bodyTokens = corpus.map((doc) => tokenize(doc.text));
    const titleTokens = corpus.map((doc) => tokenize(`${doc.title} ${doc.section}`));
    const df = new Map();
    corpus.forEach((_, index) => new Set([...bodyTokens[index], ...titleTokens[index]])
      .forEach((word) => df.set(word, (df.get(word) || 0) + 1)));
    const rank = (filterCategory) => corpus.map((doc, index) => {
      if (filterCategory !== "all" && doc.category !== filterCategory) return null;
      const bodyCounts = new Map();
      const titleCounts = new Map();
      bodyTokens[index].forEach((word) => bodyCounts.set(word, (bodyCounts.get(word) || 0) + 1));
      titleTokens[index].forEach((word) => titleCounts.set(word, (titleCounts.get(word) || 0) + 1));
      const score = queryTerms.reduce((total, term) => {
        const weightedFrequency = (bodyCounts.get(term) || 0) + (titleCounts.get(term) || 0) * 2;
        return weightedFrequency ? total + (1 + Math.log(weightedFrequency)) * Math.log(1 + corpus.length / (1 + df.get(term))) : total;
      }, 0);
      return score > 0 ? { ...doc, score } : null;
    }).filter(Boolean).sort((a, b) => b.score - a.score || a.id.localeCompare(b.id)).slice(0, 3);
    let sources = rank(category);
    const fallback = !sources.length && category !== "all";
    if (fallback) sources = rank("all");
    return { sources, route: { category, tool: intentLabels[category], fallback_to_all: fallback } };
  }

  async function retrieve(query) {
    const localHost = ["localhost", "127.0.0.1"].includes(window.location.hostname) && window.location.port === "8000";
    if (localHost) {
      try {
        const response = await fetch(`/projects/industrial-knowledge-assistant/api/ask?q=${encodeURIComponent(query)}`);
        if (response.ok) {
          mode.textContent = "LOCAL PYTHON RETRIEVAL API";
          return await response.json();
        }
      } catch (_) { /* The static browser retriever below is the offline fallback. */ }
    }
    mode.textContent = "BROWSER-LOCAL RETRIEVAL · NO EXTERNAL MODEL";
    const { sources, route } = localSearch(query);
    const answer = sources.length
      ? `In ${sources[0].title} (${sources[0].id}), the sample procedure says: ${sources[0].text}`
      : "I couldn't find a matching passage in the local sample library. Try using terms from a station event, quality check, maintenance note, or shift procedure.";
    return { answer, sources, route, retrieved_count: sources.length };
  }

  function appendQuestion(query) {
    const message = document.createElement("article");
    message.className = "chat-message user";
    message.innerHTML = `<div class="chat-meta"><span>YOUR QUESTION</span><span>LOCAL QUERY</span></div><p>${escapeHtml(query)}</p>`;
    chat.append(message);
  }

  function appendAnswer(result) {
    const article = document.createElement("article");
    article.className = "chat-message assistant";
    const answer = escapeHtml(result.answer || "No answer is available.");
    const route = result.route || { tool: "full knowledge library" };
    const sources = (result.sources || []).map((source, index) => `<div class="source-card"><span class="source-number">[${index + 1}]</span><a class="source-name" href="data/source_docs/${encodeURIComponent(source.id)}.md">${escapeHtml(source.id)} · ${escapeHtml(source.title)} / rev ${escapeHtml(source.revision || "1.0")}</a><span class="source-score">${escapeHtml(source.section || "SOURCE")}</span><span class="source-excerpt">${escapeHtml(source.text)}</span></div>`).join("");
    article.innerHTML = `<div class="chat-meta"><span>ROUTE: ${escapeHtml(route.tool || "knowledge library").toUpperCase()}</span><span>${sources ? `${result.retrieved_count} PASSAGES` : "NO MATCH"}</span></div><p>${answer}</p>${sources ? `<div class="chat-sources" aria-label="Retrieved source passages">${sources}</div>` : ""}`;
    chat.append(article);
    article.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const query = input.value.trim().slice(0, 240);
    if (!query) return;
    input.value = "";
    input.disabled = true;
    button.disabled = true;
    appendQuestion(query);
    const progress = document.createElement("div");
    progress.className = "typing";
    progress.textContent = "Searching local sample passages…";
    chat.append(progress);
    try {
      appendAnswer(await retrieve(query));
    } catch (error) {
      appendAnswer({ answer: "The local sample library could not be searched. Please reload the page and try again.", sources: [], retrieved_count: 0 });
    } finally {
      progress.remove();
      input.disabled = false;
      button.disabled = false;
      input.focus();
    }
  });

  document.querySelectorAll(".prompt-chip").forEach((chip) => chip.addEventListener("click", () => {
    input.value = chip.textContent;
    form.requestSubmit();
  }));

  loadCorpus();
})();
