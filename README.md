# Effect Size: Cohen's d, Hedges' g, and Glass's Delta

A research calculator for independent-group standardized mean differences. Use it in a browser, as a Python library, from the CLI, or with a local FastAPI service.

## Features

- **Cohen's d:** difference in group means divided by the sample-size-weighted pooled standard deviation.
- **Hedges' g:** Cohen's d multiplied by the approximate small-sample bias factor, J(df) ≈ 1 − 3/(4df − 1), where df = n1 + n2 − 2.
- **Glass's delta:** difference in means divided by **group 2's** (control) sample standard deviation.
- **Standard error:** large-sample approximation for **Cohen's d**, not an exact SE for g or Glass's delta.
- **CSV processing:** preserve source columns and output all calculated statistics.
- **Browser application:** self-contained HTML/JavaScript calculations, no backend or third-party assets.

The sign of each effect size is *group 1 minus group 2*. Each group must contain at least two observations; both SDs must be nonnegative, and the control SD and pooled SD must be positive. Non-finite inputs and undefined standardized effects are rejected.

Conventional absolute-magnitude bands (0.2, 0.5, 0.8) are **descriptive**, not validated clinical thresholds. Calculations assume independent groups; repeated-measures effects require other estimators.

## Browser app

Open [the local browser app](web/index.html) or the deployed GitHub Pages application when enabled. Enter means, sample SDs, and group sizes, and select **Calculate effect sizes**. Batch CSV files must have these columns:

**mean1, mean2, std1, std2, n1, n2**

The browser preserves additional columns, reports malformed rows, and downloads a results CSV. Maximum 2 MB and 10,000 data rows. Study values remain on the user's device. JavaScript performs the calculations directly, so Pyodide is not needed.

## Python / CLI

Python 3.10 or later. From the repository directory:

~~~bash
python -m pip install -e ".[web,test]"
python -m pytest -q
node --test web/test-app.cjs    # optional; requires Node.js
~~~

Single calculation:

~~~bash
effect-size single --mean1 10 --mean2 8 --std1 2 --std2 2 --n1 30 --n2 30
~~~

Batch CSV:

~~~bash
effect-size batch -i statistical-input.csv -o results.csv
~~~

Python:

~~~python
from effect_sizes import calculate_metrics
result = calculate_metrics(mean1=10, mean2=8, std1=2, std2=2, n1=30, n2=30)
print(result["hedges_g"])  # 0.987 (rounded)
~~~

The historical v1/v2 mode is retained for compatibility, but is **not a statistical effect size**. The original [sample.csv](sample.csv) illustrates that legacy input format rather than independent-group statistics.

## Optional API and demonstration audit

~~~bash
python cli.py serve --host 127.0.0.1 --port 8000
~~~

Open http://127.0.0.1:8000/ for the calculator or http://127.0.0.1:8000/audit-console for the separate demonstration audit workflow. POST /api/effect-size accepts the six statistical inputs; POST /api/audit evaluates illustrative project-specific thresholds. /health and /metrics report local process state. The mock chat provider performs no scientific inference.

**Security limits:** The audit is not a validated clinical decision-support system. Its PHI screening uses a limited set of regular expressions, not comprehensive de-identification. The HMAC ledger is in memory and does not survive restarts; configure AUDIT_SECRET_KEY when a stable key is needed. API routes do not implement authentication. Do not supply patient information or expose the demonstration API publicly.

## Docker

Generate an audit secret for a local Docker Compose session:

~~~bash
export AUDIT_SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
docker compose up --build
~~~

The Compose service binds to 127.0.0.1:8000. Never commit real keys or patient information.

## Technology and tests

The statistical module uses the Python standard library. The optional API uses FastAPI, Uvicorn, and Pydantic. The offline browser app uses vanilla JavaScript. Tests cover numeric formulas, invalid inputs, CSV, API, HMAC tamper detection, and JavaScript calculations. CI runs Python 3.10–3.12 and Node.js tests.

The enrichment.py modules contain illustrative threshold-based placeholders; names such as repeated measures, robust effects and meta-analysis do **not** mean those methods are implemented.

## License

MIT; see [LICENSE](LICENSE).
