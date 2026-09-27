(function () {
  const profile = window.PORTFOLIO_PROFILE || {};
  const links = [
    ["github", "GitHub", "GH"],
    ["linkedin", "LinkedIn", "in"],
    ["leetcode", "LeetCode", "LC"],
  ];

  document.querySelectorAll("[data-profile-links]").forEach((container) => {
    links.forEach(([key, label, mark]) => {
      const url = profile[key];
      if (!url || !/^https:\/\//i.test(url)) return;
      const anchor = document.createElement("a");
      anchor.className = "social-link";
      anchor.href = url;
      anchor.target = "_blank";
      anchor.rel = "noopener noreferrer";
      anchor.innerHTML = `<span aria-hidden="true">${mark}</span>${label}<span aria-hidden="true">↗</span>`;
      container.append(anchor);
    });
  });

  document.querySelectorAll("[data-profile-email]").forEach((anchor) => {
    const email = profile.email;
    if (!email) {
      anchor.hidden = true;
      return;
    }
    anchor.href = `mailto:${email}`;
    const text = anchor.querySelector("[data-email-text]");
    if (text) text.textContent = email;
  });

  document.querySelectorAll("[data-profile-github]").forEach((anchor) => {
    const url = profile.github;
    if (!url || !/^https:\/\//i.test(url)) {
      anchor.hidden = true;
      return;
    }
    anchor.href = url;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
  });

  document.querySelectorAll("[data-project-repo]").forEach((anchor) => {
    const repo = profile.githubRepo;
    const path = anchor.dataset.projectRepo;
    if (!repo || !/^https:\/\//i.test(repo)) {
      anchor.hidden = true;
      return;
    }
    anchor.href = `${repo.replace(/\/$/, "")}/tree/main/projects/${path}`;
    anchor.target = "_blank";
    anchor.rel = "noopener noreferrer";
  });
})();
