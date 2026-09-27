# Utkarsh Upadhyay — portfolio

Professional portfolio and industrial project demos for https://blaze99git.github.io/html-portfolio/. The public portfolio is static; local projects include runnable Python APIs and use fictional documents or generated plant telemetry.

## Profile links

- Portfolio: https://blaze99git.github.io/html-portfolio/
- Daily activity: https://blaze99git.github.io/html-portfolio/activity.html
- GitHub: https://github.com/Blaze99git
- LinkedIn: https://www.linkedin.com/in/utkarsh-upadhyay-b8b1a6191/
- LeetCode: https://leetcode.com/u/Utkarsh_0320/
- Email: upadhyayutkarsh484@gmail.com

The home page, activity page, and project pages link back to these profiles and to the project source folders in this repository. site-config.js is the shared source for profile URLs.

## Projects

- Manufacturing Operations Monitor: locally runnable JSON API, background simulated telemetry, SQLite persistence, OEE and quality calculations, alert acknowledgement, reporting UI, and PostgreSQL reference schema. See projects/operations-monitor/README.md.
- Industrial Knowledge Assistant: citation-first local retrieval service with deterministic document ingestion, intent routing, evidence ranking, a browser preview, and a Python API. See projects/industrial-knowledge-assistant/README.md.

## Run the portfolio and project demos

Serve the repository root to try the static portfolio and browser previews:

    python3 -m http.server 8000

Open http://127.0.0.1:8000/. The assistant page uses its browser-local retriever in this mode. To run the Python retrieval API, stop the root server and run:

    python3 projects/industrial-knowledge-assistant/run_demo.py

The operations monitor has a separate local API, database, and simulator:

    python3 projects/operations-monitor/server.py

Open http://127.0.0.1:8100/projects/operations-monitor/ while it runs. The SQLite database is local and ignored by Git. You can keep the root preview on port 8000 and the operations API on port 8100 at the same time.

The project maintenance commands regenerate the knowledge base, run the current checks, and build a browser-safe Pages artifact outside the repository:

    python3 projects/industrial-knowledge-assistant/ingest.py
    python3 -m unittest discover -s tests -v
    python3 scripts/check_site.py
    python3 scripts/build_site.py --output /tmp/portfolio-site

The projects use Python’s standard library and need no package installation or API keys. GitHub Pages hosts the portfolio and static previews for free; it does not run the project APIs or simulators continuously.

## Activity monitor and daily LeetCode log

The daily activity page reads recent public push events from GitHub in the visitor’s browser. It cannot show private activity, and the events feed may lag. LeetCode problem titles, links, statuses, and optional reflections are logged through the “Log LeetCode practice and update portfolio” workflow under GitHub Actions. Each entry is published on the portfolio, so submit only details you want public. The workflow commits the entry and deploys the updated static page.

## GitHub Pages deployment

The repository includes GitHub Actions workflows for quality checks and GitHub Pages deployment. On the repository’s Settings → Pages page, set Build and deployment → Source to GitHub Actions. Each push to main then builds and deploys the static site. The generated Pages artifact excludes Python APIs, simulator code, and tests. It includes the HTML, CSS, JavaScript, readme files, sample schemas, fictional source documents, and public learning log.

## Project boundaries

The operations monitor uses generated sample readings and does not connect to equipment or plant systems. Assistant documents are fictional and are not real operating instructions. Neither demo includes employer code, customer data, credentials, or a production integration. The portfolio omits the phone number from the supplied resume.
