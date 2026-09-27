# Utkarsh Upadhyay — portfolio

Professional portfolio and project demos for [GitHub Pages](https://blaze99git.github.io/html-portfolio/). The static site has no third-party runtime dependencies. Project examples are original, use synthetic data and fictional documents, and demonstrate engineering practices around interactive dashboards and evidence-based retrieval.

## Profile links

- Portfolio: [blaze99git.github.io/html-portfolio](https://blaze99git.github.io/html-portfolio/)
- GitHub: [Blaze99git](https://github.com/Blaze99git)
- LinkedIn: [Utkarsh Upadhyay](https://www.linkedin.com/in/utkarsh-upadhyay-b8b1a6191/)
- LeetCode: [Utkarsh_0320](https://leetcode.com/u/Utkarsh_0320/)
- Email: [upadhyayutkarsh484@gmail.com](mailto:upadhyayutkarsh484@gmail.com)

The home page and project pages link back to these profiles and to the corresponding project source folders in this repository. `site-config.js` is the single place to update these URLs.

## Projects

- [Manufacturing Operations Monitor](projects/operations-monitor/README.md): responsive dashboard simulation with an OEE view, station and alert controls, CSV export, and PostgreSQL schema and reporting queries.
- [Industrial Knowledge Assistant](projects/industrial-knowledge-assistant/README.md): citation-first retrieval prototype with deterministic document ingestion, intent routing, a browser version, and an optional local Python API.

## Run and validate locally

Serve the repository root to try the static portfolio and both project pages:

```bash
python3 -m http.server 8000
```

Open `http://127.0.0.1:8000/`. The assistant page uses its browser-local retriever in this mode. To run the Python API version instead, stop the first server and run:

```bash
python3 projects/industrial-knowledge-assistant/run_demo.py
```

The commands below regenerate the knowledge base, run unit tests and site-link checks, and build the browser-safe Pages artifact outside the repository:

```bash
python3 projects/industrial-knowledge-assistant/ingest.py
python3 -m unittest discover -s tests -v
python3 scripts/check_site.py
python3 scripts/build_site.py --output /tmp/portfolio-site
```

No package installation, API key, database, paid service, or external model is required for the demos.

## GitHub Pages deployment

The repository includes GitHub Actions workflows for quality checks and GitHub Pages deployment. On the repository's **Settings → Pages** page, set **Build and deployment → Source** to **GitHub Actions**. Each push to `main` then builds and deploys the static site. GitHub Pages is available for public repositories on GitHub Free; see the [GitHub Pages documentation](https://docs.github.com/en/pages/getting-started-with-github-pages).

The generated Pages artifact excludes the Python server and tests. It includes the HTML, CSS, JavaScript, SQL examples, and fictional source documents used by the browser demo.

## Project boundaries

The operations dashboard uses generated sample readings and does not connect to equipment or plant systems. Assistant documents are fictional and are not real operating instructions. Neither demo includes employer code, customer data, credentials, or a production integration. The portfolio omits the phone number from the supplied resume.
