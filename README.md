# Effect Size Hedges G Glass Delta

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** `Standard Clinical Formulations & ISO/IEC Quality Frameworks`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Computes standardized mean difference effect sizes:
- **Cohen's d** — pooled standard deviation effect size
- **Hedges' g** — Cohen's d with small-sample bias correction
- **Glass's Delta** — control-group standard deviation effect size (unequal variance)
- **Standard Error** — standard error of the effect size estimate

Zero-dependency Python implementation with single and batch evaluation.

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`cohens_d(mean1, mean2, std1, std2, n1, n2)`** — Cohen's d with pooled standard deviation
- **`hedges_g(mean1, mean2, std1, std2, n1, n2)`** — Hedges' g with small-sample correction
- **`glasses_delta(mean1, mean2, std_control)`** — Glass's delta using control group SD
- **`standard_error_effect_size(d, n1, n2)`** — Standard error of the effect size
- **`calculate_metrics(**kwargs)`** — Unified interface returning all metrics with classification
- **`process_batch(input_csv, output_csv)`** — Batch CSV processing

---

## 📐 Mathematical Formulation

### Cohen's d
```
d = (mean1 - mean2) / SD_pooled
SD_pooled = sqrt(((n1-1)*SD1^2 + (n2-1)*SD2^2) / (n1+n2-2))
```

### Hedges' g
```
g = d * J(df)
J(df) = 1 - 3 / (4*df - 1)   where df = n1 + n2 - 2
```

### Glass's Delta
```
Δ = (mean1 - mean2) / SD_control
```

### Standard Error
```
SE = sqrt((n1+n2)/(n1*n2) + d^2 / (2*(n1+n2)))
```

### Effect Size Classification (Hedges' g)
| Magnitude | |g| Range |
|-----------|----------|
| Negligible | < 0.2 |
| Small | 0.2 – 0.5 |
| Medium | 0.5 – 0.8 |
| Large | ≥ 0.8 |

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/effect-size-hedges-g-glass-delta.git
cd effect-size-hedges-g-glass-delta

# Install core (no dependencies required for statistical functions)
pip install -e .

# Install with web API support
pip install -e ".[web]"

# Install with test dependencies
pip install -e ".[test]"
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Evaluation (Statistical Mode)
```bash
python effect_sizes.py single --mean1 10.0 --mean2 8.0 --std1 2.0 --std2 2.0 --n1 30 --n2 30
```

### 2. Batch CSV Processing
```bash
python effect_sizes.py batch -i sample.csv -o results.csv
```

### 3. Enterprise CLI (Full Platform)
```bash
# Audit task evaluation
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch processing
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail
python cli.py verify-audit

# Launch REST API server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Input Data Schema (Batch CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `mean1` | Group 1 mean | Required for stats |
| `mean2` | Group 2 mean | Required for stats |
| `std1` | Group 1 standard deviation | Required for stats |
| `std2` | Group 2 standard deviation | Required for stats |
| `n1` | Group 1 sample size | Optional (default: 1) |
| `n2` | Group 2 sample size | Optional (default: 1) |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation and state transition.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Run with coverage:

```bash
pytest -v --cov=effect_sizes --cov=agents
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 100
```

---

## 🐳 Container Deployment

```bash
docker build -t effect-size-hedges-g-glass-delta .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key effect-size-hedges-g-glass-delta
```

Or with Docker Compose:

```bash
docker-compose up -d
```

---

## 📁 Project Structure

```
effect-size-hedges-g-glass-delta/
├── effect_sizes.py          # Core statistical algorithms
├── cli.py                   # Enterprise CLI interface
├── enrichment.py            # Extended analytical engines
├── simulator.py             # High-throughput stress testing
├── agents/
│   ├── __init__.py
│   ├── base.py              # PHI guard, HMAC audit trail
│   ├── models.py            # Pydantic data models
│   ├── supervisor.py        # Multi-agent orchestrator
│   ├── workers.py           # Specialized evaluation workers
│   ├── api.py               # FastAPI REST endpoints
│   ├── llm_factory.py       # LLM provider abstraction
│   ├── learning.py          # Bayesian calibration engine
│   ├── metrics.py           # Prometheus metrics collector
│   └── streamer.py          # WebSocket telemetry broadcaster
├── tests/
│   ├── test_effect_size_hedges_g_glass_delta.py
│   └── test_enrichment.py
├── web/
│   └── index.html           # Operations console UI
├── test_effect_sizes.py     # Core algorithm tests
├── sample.csv               # Example input data
├── pyproject.toml           # Project configuration
├── Dockerfile
└── docker-compose.yml
```
