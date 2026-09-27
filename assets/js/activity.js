(() => {
  "use strict";

  const $ = (selector) => document.querySelector(selector);
  const activityRoot = $("#activity-calendar");
  const escapeHtml = (value) => String(value).replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]);
  const localDay = (date) => {
    const parts = new Intl.DateTimeFormat("en-CA", { year: "numeric", month: "2-digit", day: "2-digit" }).formatToParts(date);
    const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
    return values.year + "-" + values.month + "-" + values.day;
  };
  const longDate = (date) => new Intl.DateTimeFormat("en-IN", { weekday: "short", day: "numeric", month: "short" }).format(date);
  const relativeDate = (date) => {
    const days = Math.floor((Date.now() - date.getTime()) / 86_400_000);
    return days <= 0 ? "Today" : days === 1 ? "Yesterday" : longDate(date);
  };

  function setClock() {
    const date = new Date();
    $("#local-date").textContent = new Intl.DateTimeFormat("en-IN", {
      timeZone: "Asia/Kolkata", weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZoneName: "short",
    }).format(date);
  }

  function renderCalendar(events) {
    const counts = new Map();
    for (const event of events) {
      if (event.type !== "PushEvent") continue;
      const day = localDay(new Date(event.created_at));
      counts.set(day, (counts.get(day) || 0) + 1);
    }
    const days = [];
    const today = new Date();
    for (let offset = 34; offset >= 0; offset -= 1) {
      const date = new Date(today);
      date.setDate(today.getDate() - offset);
      date.setHours(12, 0, 0, 0);
      const day = localDay(date);
      const pushes = counts.get(day) || 0;
      const level = pushes === 0 ? 0 : pushes === 1 ? 1 : pushes <= 3 ? 2 : pushes <= 5 ? 3 : 4;
      const title = longDate(date) + " · " + pushes + " public " + (pushes === 1 ? "push" : "pushes");
      days.push('<span class="calendar-day level-' + level + (offset === 0 ? " today" : "") + '" title="' + escapeHtml(title) + '" aria-label="' + escapeHtml(title) + '"></span>');
    }
    activityRoot.innerHTML = days.join("");
  }

  function renderPushes(events) {
    const recentCutoff = Date.now() - 30 * 86_400_000;
    const pushes = events.filter((event) => event.type === "PushEvent" && Date.parse(event.created_at) >= recentCutoff)
      .sort((a, b) => Date.parse(b.created_at) - Date.parse(a.created_at));
    const commitTotal = pushes.reduce((total, event) => total + Number(event.payload?.size || event.payload?.commits?.length || 0), 0);
    $("#push-count").textContent = String(pushes.length);
    $("#commit-count").textContent = String(commitTotal);
    $("#latest-push").textContent = pushes.length ? relativeDate(new Date(pushes[0].created_at)) : "No public pushes yet";
    $("#pushes-count").textContent = pushes.length + " PUSH EVENTS";
    $("#github-updated").textContent = "UPDATED " + new Intl.DateTimeFormat("en-IN", { hour: "2-digit", minute: "2-digit" }).format(new Date());
    if (!pushes.length) {
      $("#push-list").innerHTML = '<p class="activity-empty">No public pushes were returned for GitHub’s current events window. Open the profile to see the full contribution history.</p>';
      return;
    }
    $("#push-list").innerHTML = pushes.slice(0, 14).map((event) => {
      const repoName = String(event.repo?.name || "repository");
      const repoUrl = "https://github.com/" + repoName;
      const branch = String(event.payload?.ref || "").replace(/^refs\/heads\//, "");
      const commits = Array.isArray(event.payload?.commits) ? event.payload.commits.slice(0, 5) : [];
      const commitMarkup = commits.map((commit) => {
        const sha = String(commit.sha || "");
        const shortSha = sha.slice(0, 7);
        const url = sha ? repoUrl + "/commit/" + encodeURIComponent(sha) : repoUrl;
        return '<div class="commit-row"><a class="commit-sha" href="' + escapeHtml(url) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(shortSha || "commit") + '</a><span>' + escapeHtml(commit.message || "Commit message unavailable") + "</span></div>";
      }).join("");
      const size = Number(event.payload?.size || commits.length || 0);
      const created = new Date(event.created_at);
      return '<article class="push-group"><time class="push-date" datetime="' + escapeHtml(event.created_at) + '">' + escapeHtml(relativeDate(created)) + " · " + escapeHtml(new Intl.DateTimeFormat("en-IN", { hour: "2-digit", minute: "2-digit" }).format(created)) + '</time><div class="push-main"><div class="push-repo"><a href="' + escapeHtml(repoUrl) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(repoName) + "</a>" + (branch ? '<span class="branch-label">' + escapeHtml(branch) + "</span>" : "") + '<span class="push-summary">' + size + " " + (size === 1 ? "commit" : "commits") + "</span></div><div class=\"commit-list\">" + (commitMarkup || '<span class="push-summary">Individual commit details are not available in this event.</span>') + "</div></div></article>";
    }).join("");
  }

  async function loadGithubActivity() {
    const cacheKey = "portfolio.github.activity.v1";
    try {
      let cached = null;
      try { cached = JSON.parse(sessionStorage.getItem(cacheKey) || "null"); } catch (_) { /* Storage can be disabled by the browser. */ }
      let events;
      if (cached && Date.now() - cached.savedAt < 15 * 60_000 && Array.isArray(cached.events)) {
        events = cached.events;
      } else {
        const response = await fetch("https://api.github.com/users/Blaze99git/events/public?per_page=100");
        if (!response.ok) throw new Error("GitHub returned HTTP " + response.status);
        events = await response.json();
        if (!Array.isArray(events)) throw new Error("GitHub returned an unexpected response");
        try { sessionStorage.setItem(cacheKey, JSON.stringify({ savedAt: Date.now(), events })); } catch (_) { /* The feed still works without a browser cache. */ }
      }
      renderCalendar(events);
      renderPushes(events);
    } catch (error) {
      $("#github-updated").textContent = "FEED UNAVAILABLE";
      $("#push-count").textContent = "—";
      $("#commit-count").textContent = "—";
      $("#latest-push").textContent = "Open GitHub";
      $("#pushes-count").textContent = "RETRY LATER";
      $("#push-list").innerHTML = '<p class="activity-empty">GitHub activity could not be fetched in this browser session (' + escapeHtml(error.message) + '). The profile remains available from the link above.</p>';
      activityRoot.innerHTML = '<p class="activity-empty">The public activity calendar needs a connection to GitHub.</p>';
    }
  }

  async function loadLeetcodeLog() {
    try {
      const response = await fetch("data/leetcode-log.json", { cache: "no-store" });
      if (!response.ok) throw new Error("Practice log is unavailable.");
      const log = await response.json();
      const entries = Array.isArray(log.entries) ? log.entries.slice().sort((a, b) => b.date.localeCompare(a.date)) : [];
      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() - 29);
      const recent = entries.filter((entry) => new Date(entry.date + "T12:00:00") >= cutoff);
      $("#leetcode-total").textContent = String(recent.length);
      $("#leetcode-streak").textContent = recent.length
        ? recent.filter((entry) => entry.status === "solved").length + " solved · " + recent.filter((entry) => entry.status !== "solved").length + " in progress"
        : "Start by logging a problem you worked on.";
      if (!entries.length) {
        $("#study-list").innerHTML = '<p class="activity-empty">No problems logged yet. When you submit a LeetCode entry through the GitHub Actions form, the problem and reflection will appear here.</p>';
        return;
      }
      $("#study-list").innerHTML = entries.slice(0, 20).map((entry) => {
        const status = ["solved", "attempted", "revisit"].includes(entry.status) ? entry.status : "attempted";
        const problem = entry.url
          ? '<a href="' + escapeHtml(entry.url) + '" target="_blank" rel="noopener noreferrer">' + escapeHtml(entry.title) + "</a>"
          : escapeHtml(entry.title);
        const notes = entry.reflection ? '<p class="study-notes">' + escapeHtml(entry.reflection) + "</p>" : "";
        const date = new Date(entry.date + "T12:00:00");
        return '<article class="study-entry"><time class="study-date" datetime="' + escapeHtml(entry.date) + '">' + escapeHtml(longDate(date)) + '</time><div><div class="study-problem">' + problem + "</div>" + notes + '</div><span class="study-status ' + status + '">' + escapeHtml(status) + "</span></article>";
      }).join("");
    } catch (error) {
      $("#leetcode-streak").textContent = "Practice log unavailable.";
      $("#study-list").innerHTML = '<p class="activity-empty">' + escapeHtml(error.message) + "</p>";
    }
  }

  setClock();
  $("#year").textContent = String(new Date().getFullYear());
  window.setInterval(setClock, 60_000);
  Promise.all([loadGithubActivity(), loadLeetcodeLog()]);
})();
