# Stock DD MAS

Stock DD MAS is a modular stock due-diligence research application intended to help organize evidence about a public company, evaluate the quality and durability of the business, estimate an intrinsic-value range, and compare that estimate with the market price.

The project is currently in **alpha development**. It is a portfolio/learning project and is being built incrementally with practical industry-standard Python practices: typed domain models, provider-independent interfaces, explicit validation, test coverage, CI, raw-source preservation, and evidence traceability.

> **Important:** Stock DD MAS is a research tool under development. Its outputs are not financial advice and should not be treated as a recommendation to buy or sell a security.

---

## Project identity

Use these names consistently:

- **Application:** Stock DD MAS
- **Python distribution:** `stock-dd`
- **Python package:** `stock_dd`
- **Current package version:** `0.1.0`
- **Python version used for development:** **3.14.2**

The repository name may still contain `Stock_Due_Diligence`, but application and code references should use the names above.

---

## Current platform support

### Supported development platform

This alpha version currently supports **Windows only** for contributor setup and manual development.

The expected local environment is:

- Windows 11
- PowerShell
- Python 3.14.2
- Git
- VS Code or another Python-capable editor

Linux and macOS are **not currently supported contributor environments**. They may work, but platform-specific behavior has not been validated and contributors should not assume compatibility.

GitHub Actions currently executes automated quality checks on Ubuntu. This is useful as an additional compatibility signal, but it does **not** mean Linux is an officially supported local-development platform for this alpha version.

---

## Current project status

The original financial-data foundation is working.

### Completed

- `src`-layout Python package
- `pyproject.toml` packaging
- editable installation
- offline JSON research-data loader and validation
- typed dataclass domain models
- financial calculations:
  - revenue growth
  - operating margin
  - free cash flow
- Markdown report generation
- offline pipeline
- live financial-data pipeline
- CLI subcommands
- provider-independent financial collector protocol
- Financial Modeling Prep (FMP) collector using HTTPX
- FMP normalization
- raw FMP response storage
- central application exceptions
- configurable logging
- `.env`-based configuration
- Ruff linting and formatting
- strict mypy type checking
- pytest
- branch coverage with a minimum threshold of 90%
- GitHub Actions CI
- management-research requirements
- management-research domain models
- company and company-listing repository contracts

### Current development area

The current design work is the **management-research foundation**.

At the time of writing, the active development branch is:

```text
feature/management-research-foundation
```

Before beginning work, check the repository to confirm which branch is currently designated for active development.

The immediate architectural sequence is:

```text
Repository contracts
    ↓
SQLite persistence
    ↓
Provider-independent SEC collection interfaces
    ↓
SEC collection and raw filing storage
    ↓
Unstructured research-agent interface
    ↓
Candidate evidence
    ↓
Evidence validation
    ↓
Trusted management records
    ↓
Management research packet/report
    ↓
Later scoring and valuation integration
```

The detailed management-research specification is in:

```text
docs/management-research-requirements.md
```

Read that file before making changes to management-related models, storage, collection, or scoring.

---

## Long-term objective

Stock DD MAS is intended to produce three different outputs.

### 1. Company-quality assessment

Evaluate how solid the company appears using evidence such as:

- financial performance
- management quality
- execution record
- capital allocation
- shareholder alignment
- stability and governance risk
- later business and industry factors

### 2. Estimated intrinsic-value range

The application should eventually estimate a defensible **range** rather than claiming to know one exact "true value."

### 3. Market comparison

The estimated intrinsic-value range can eventually be compared with the current market price together with confidence, assumptions, and supporting evidence.

Management quality must not mechanically add or subtract an arbitrary dollar amount from valuation.

---

## Current financial pipeline

The live financial pipeline currently looks like this:

```text
Ticker
    ↓
FMPFinancialDataCollector
    ↓
Raw provider response
    ↓
Raw-data storage
    ↓
FMP normalizer
    ↓
CompanyResearchData
    ↓
Financial calculations
    ↓
Markdown report
```

The provider-specific collector is intentionally separated from normalized application models.

---

## Management-research architecture

Management research uses two collection lanes.

### Structured-data lane

Used for information available in predictable structured or semi-structured formats.

Examples:

- company identifiers
- financial statements
- SEC filing metadata
- capital expenditures
- debt issuance and repayment
- dividends
- share repurchases
- share issuance
- structured insider ownership/transaction data

### Unstructured-research lane

Used for narrative documents and webpages.

Examples:

- executive biographies
- previous career positions
- management guidance
- company milestones
- setbacks
- explanations for executive departures
- governance concerns
- company announcements
- reputable independent reporting

The unstructured lane may eventually use a research agent, but agent output is **not automatically trusted data**.

The intended flow is:

```text
External source
    ↓
Raw source storage
    ↓
Structured parser or research agent
    ↓
CandidateEvidence
    ↓
Validation / conflict handling
    ↓
Trusted normalized domain records
    ↓
Analysis
```

Do not create a design where an agent searches the web and directly assigns a management score.

---

## Initial management-research scope

The first management-research implementation is intentionally limited.

Initial company coverage:

- US domestic publicly traded companies

Initial executive coverage:

- current CEO
- current CFO
- recent CEO/CFO appointments and departures
- available previous career history, primarily over the previous five years

Initial trusted facts include:

- company identity
- SEC CIK
- executive identity
- current role
- role start/effective dates where disclosed
- previous employers
- previous titles
- previous-role dates where disclosed
- appointment events
- departure events
- source/evidence metadata

The first implementation does **not** yet:

- calculate a final management-quality score
- classify executives as "good" or "bad"
- automatically interpret insider selling
- perform complete compensation analysis
- perform full board-governance scoring
- automatically alter valuation assumptions
- mine every website available

---

## Evidence rules

Evidence traceability is a core design requirement.

Every accepted management fact should ultimately be traceable to one or more sources unless it is a deterministic calculation from already sourced data.

Preferred source order:

1. regulator filings and official government records
2. audited company filings
3. company investor-relations documents
4. official company announcements
5. reputable independent reporting
6. direct executive interviews or conference materials
7. discovery sources such as Wikipedia
8. optional manually reviewed professional profiles

Wikipedia can be useful for discovery, but it should not replace an available primary source.

LinkedIn is **not a required automated source** for this project.

When sources disagree, do not silently overwrite one value with another. Preserve the evidence and surface the conflict.

---

## Point-in-time correctness

Management research must eventually support an explicit `as_of_date`.

A historical research run must not use information that became public after the requested date.

For example:

```text
Research as of: 2024-12-31
```

must not use an executive appointment first announced in 2025.

Preserve relevant dates separately when possible:

- publication/filing date
- retrieval timestamp
- announcement date
- effective date
- reporting period

Do not invent exact dates when a source provides only a year or month. The domain layer includes `PartialDate` for this reason.

---

## Repository structure

The important top-level directories are:

```text
.
├── .github/
│   └── workflows/
├── data/
│   └── samples/
├── docs/
├── reports/
├── src/
│   └── stock_dd/
├── tests/
├── .env.example
├── .gitignore
├── pyproject.toml
└── README.md
```

The Python package currently includes:

```text
src/stock_dd/
├── collectors/
├── models/
├── normalizers/
├── repositories/
├── storage/
├── __init__.py
├── __main__.py
├── calculations.py
├── config.py
├── exceptions.py
├── loader.py
├── logging_config.py
├── pipeline.py
└── report.py
```

### `collectors/`

External data collection.

Provider-independent contracts should be defined before provider-specific network implementations.

### `normalizers/`

Convert provider-specific raw data into trusted Stock DD MAS domain models.

### `models/`

Typed application/domain models.

Current model modules include:

```text
models/
├── __init__.py
├── company.py
├── dates.py
├── evidence.py
├── events.py
├── executives.py
└── identifiers.py
```

`models/__init__.py` is the public re-export surface. Application code should normally import public models from:

```python
from stock_dd.models import CompanyIdentity, Executive
```

rather than depending unnecessarily on a model's internal module location.

### `repositories/`

Provider-independent persistence contracts.

Repository interfaces define what application logic needs without coupling it to SQLite or another database implementation.

Current examples include:

```text
CompanyRepository
CompanyListingRepository
```

### `storage/`

Raw-provider data storage and other concrete storage concerns.

Raw source data and normalized database data are intentionally different layers.

---

## Data-storage strategy

Use three conceptual layers.

### 1. Raw external data

Examples:

- FMP JSON
- future SEC JSON
- future SEC filing HTML
- downloaded reports
- extracted webpage text
- future raw research-agent output

Raw data should be preserved separately so normalization can be rerun without recollecting the source.

Current raw data defaults to:

```text
data/raw/
```

and is ignored by Git.

### 2. Candidate evidence

Information extracted by an agent or parser but not yet accepted as trusted fact.

### 3. Normalized trusted data

Examples:

- `CompanyIdentity`
- `CompanyListing`
- `Executive`
- `ExecutiveRole`
- `CareerPosition`
- `CompanyEvent`
- `EvidenceSource`

Normalized linked records are planned to be stored in SQLite through repository interfaces.

Application logic should operate on typed domain objects, not raw SQL rows.

---

## Windows development setup

### 1. Clone the repository

```powershell
git clone https://github.com/limkyouyou/Stock_Due_Diligence.git
cd Stock_Due_Diligence
```

### 2. Switch to the current development branch

At the time of writing:

```powershell
git switch feature/management-research-foundation
git pull
```

For future work, confirm the active development branch before starting.

### 3. Confirm Python

The project is developed using Python 3.14.2.

```powershell
python --version
```

Expected:

```text
Python 3.14.2
```

### 4. Create the virtual environment

```powershell
python -m venv .venv
```

### 5. Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, a temporary per-process policy can be used:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Do not change machine-wide execution policy just for this project.

### 6. Upgrade pip

```powershell
python -m pip install --upgrade pip
```

### 7. Install the project in editable mode with development tools

```powershell
python -m pip install --editable ".[dev]"
```

Editable installation means changes under `src/stock_dd/` are immediately used by the active environment.

---

## Environment configuration

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Current variables:

```dotenv
STOCK_DD_FINANCIAL_API_KEY=
STOCK_DD_RAW_DATA_DIR=data/raw
```

### `STOCK_DD_FINANCIAL_API_KEY`

Required for the live FMP financial-data pipeline.

Do not commit real API keys.

### `STOCK_DD_RAW_DATA_DIR`

Controls where unmodified provider responses are stored.

Default:

```text
data/raw
```

`.env`, `.env.*` except `.env.example`, generated reports, and collected raw provider data are ignored by Git.

---

## Running Stock DD MAS

### Offline mode

Offline mode requires no API key.

```powershell
python -m stock_dd offline --input data/samples/northstar_robotics.json
```

Optional output path:

```powershell
python -m stock_dd offline `
    --input data/samples/northstar_robotics.json `
    --output reports/northstar.md
```

### Live financial mode

Requires an FMP API key in `.env` or the process environment.

```powershell
python -m stock_dd live --ticker AAPL
```

Request a different number of annual periods:

```powershell
python -m stock_dd live --ticker AAPL --annual-limit 5
```

### Verbose logging

`--verbose` is a global CLI option and should appear before the subcommand:

```powershell
python -m stock_dd --verbose live --ticker AAPL
```

or:

```powershell
python -m stock_dd -v offline --input data/samples/northstar_robotics.json
```

---

## Current FMP behavior

Financial Modeling Prep is currently the live financial-data provider.

The project collects:

- company profile
- annual income statements
- annual balance sheets
- annual cash-flow statements

The FMP normalizer converts provider responses into Stock DD MAS models.

Important normalization rule:

```text
FMP capitalExpenditure
→ normalized as a positive amount spent
```

The annual financial-statement date is used as the financial report's `as_of_date`.

The raw collection timestamp is stored separately from the statement reporting date.

FMP news is **not currently part of the project**. Do not assume access to paid FMP news endpoints.

---

## Quality requirements

All code changes should pass the same local quality checks before being pushed.

```powershell
python -m ruff format .
python -m ruff check .
python -m mypy
python -m pytest --cov=stock_dd --cov-branch --cov-report=term-missing
```

Mypy is configured in strict mode.

Coverage includes branch coverage and must remain at or above:

```text
90%
```

Do not rely only on CI to format code. Run Ruff formatting locally before committing.

---

## Continuous integration

GitHub Actions runs quality checks for configured branches and pull requests.

CI currently checks:

- Ruff linting
- Ruff formatting
- strict mypy
- pytest with coverage

A contribution should not be considered ready to merge while CI is failing.

---

## Development principles

### Keep provider-specific code behind interfaces

For example:

```text
FinancialDataCollector
    ↓
FMPFinancialDataCollector
```

The rest of the application should not depend directly on FMP response structures.

Use the same principle for future SEC collection, research agents, and persistence.

### Define interfaces before network code

Do not begin a new provider implementation until the provider-independent contract is defined and tested.

### Keep raw data separate from normalized data

Raw external responses should be preserved.

Normalization converts those responses into trusted application models.

### Do not let agents become the source of truth

Future web-research agents should produce `CandidateEvidence`.

Validation and normalization decide whether a claim becomes a trusted record.

### Preserve evidence

Do not create trusted management facts without source traceability.

### Avoid unsupported inference

Acceptable:

```text
Operating margin increased during the CEO's tenure.
```

Not automatically acceptable:

```text
The CEO caused the operating-margin increase.
```

### Represent missing information honestly

Do not invent values to fill gaps.

Missing data and conflicting evidence should be preserved as such.

### Keep scoring out of the collection layer

Collection gathers evidence.

Normalization structures evidence.

Analysis interprets evidence.

Scoring comes later.

---

## Branch and collaboration workflow

Before starting a contribution:

1. Pull the latest target branch.
2. Read this README.
3. Read relevant files under `docs/`.
4. Inspect the existing implementation and tests before changing architecture.
5. Confirm the next roadmap item or issue.
6. Create a focused feature/fix branch.

Example:

```powershell
git switch feature/management-research-foundation
git pull
git switch -c feature/evidence-repository
```

Use clear branch names such as:

```text
feature/<short-description>
fix/<short-description>
refactor/<short-description>
test/<short-description>
docs/<short-description>
```

Keep commits focused.

Examples:

```text
feat: add evidence repository contract
fix: handle missing filing date
refactor: extract executive models
test: cover historical ticker lookup
docs: update collaborator setup
```

Before pushing:

```powershell
python -m ruff format .
python -m ruff check .
python -m mypy
python -m pytest --cov=stock_dd --cov-branch --cov-report=term-missing
```

Then:

```powershell
git status
git add .
git commit -m "..."
git push -u origin <branch-name>
```

Do not commit directly to `main` for collaborative feature work unless the project maintainer explicitly asks for it.

---

## Where a new collaborator should start

### Step 1: Understand the current application

Run:

```powershell
python -m stock_dd offline --input data/samples/northstar_robotics.json
```

Then inspect:

```text
src/stock_dd/pipeline.py
src/stock_dd/models/
src/stock_dd/collectors/
src/stock_dd/normalizers/
src/stock_dd/storage/
tests/
```

### Step 2: Read the management-research requirements

Read:

```text
docs/management-research-requirements.md
```

This is the source of truth for the management-research design.

### Step 3: Inspect repository contracts

Read:

```text
src/stock_dd/repositories/
```

The project is currently building the persistence boundary before adding SQLite.

### Step 4: Check the current roadmap item

At the time of writing, work is progressing through repository contracts before SQLite persistence.

Do not skip ahead to:

- SQLite repository implementations
- SEC network collection
- a browsing/research agent
- final management scoring

unless the earlier boundary is already complete or the maintainer has explicitly changed the roadmap.

### Step 5: Pick a small, testable contribution

Good early contributions include:

- repository protocol + contract tests
- model validation tests
- raw-storage improvements
- documentation
- deterministic normalization
- test fixtures
- targeted bug fixes

A new contributor should avoid making a large cross-cutting architecture change as a first contribution.

---

## Current roadmap

### Foundation

- [x] Offline financial prototype
- [x] Engineering-quality foundation
- [x] Live financial-data pipeline
- [x] Management Research Requirements v0.1
- [x] Management domain models
- [ ] Complete repository contracts
- [ ] SQLite persistence

### Structured management research

- [ ] Provider-independent company/SEC collection interfaces
- [ ] SEC company identity resolution
- [ ] SEC filing discovery
- [ ] Raw SEC filing storage
- [ ] Structured management-data extraction

### Unstructured management research

- [ ] Provider-independent research-agent interface
- [ ] Versioned research tasks
- [ ] Candidate-evidence ingestion
- [ ] Evidence validation
- [ ] Conflict handling
- [ ] Promotion to trusted domain records

### Research output

- [ ] Management research packet
- [ ] Management Markdown report

### Later analysis

- [ ] Capital-allocation analysis
- [ ] Shareholder-alignment analysis
- [ ] Guidance/execution tracking
- [ ] Company milestone/setback research
- [ ] Governance analysis
- [ ] Peer benchmarks
- [ ] Management-quality score
- [ ] Intrinsic-value model
- [ ] Market-price comparison
- [ ] Evidence-based AI analyst
- [ ] Human/trader evaluation

---

## Important files

```text
README.md
    Contributor orientation and local setup.

docs/management-research-requirements.md
    Detailed management-research requirements and design constraints.

pyproject.toml
    Package metadata, dependencies, Ruff, mypy, pytest, and coverage settings.

.env.example
    Supported environment variables without real secrets.

src/stock_dd/__main__.py
    CLI entry point.

src/stock_dd/pipeline.py
    Offline and live pipeline orchestration.

src/stock_dd/models/
    Typed domain models.

src/stock_dd/collectors/
    Provider-independent collection contracts and provider implementations.

src/stock_dd/normalizers/
    Provider-specific raw-data normalization.

src/stock_dd/repositories/
    Provider-independent persistence contracts.

src/stock_dd/storage/
    Raw-data storage implementation.

tests/
    Unit and contract tests.

.github/workflows/ci.yml
    Automated quality checks.
```

---

## Secrets, generated files, and Git

Never commit:

- `.env`
- API keys
- credentials
- raw provider data under `data/raw/`
- generated reports under `reports/`
- `.venv/`
- coverage/cache files

The committed `.env.example` is intentionally safe and contains no real credentials.

Before pushing, always check:

```powershell
git status
```

If a secret is accidentally committed, removing it in a later commit is not sufficient because it remains in Git history. Notify the maintainer and rotate the credential.

---

## Notes for architectural changes

Before proposing an architectural change:

1. Inspect the existing code.
2. Identify the current abstraction boundary.
3. Explain what problem the change solves.
4. Prefer the smallest design that solves the current requirement.
5. Add or update tests.
6. Update documentation when behavior or architecture changes.

This project intentionally avoids adding large frameworks unless they provide a clear practical benefit.

For example:

- no external multi-agent framework is currently required
- SQLite is planned before introducing a database server
- repository protocols are defined before concrete SQLite repositories
- provider-independent interfaces are defined before network implementations

---

## Contribution expectations

A useful contribution should be:

- focused
- typed
- tested
- evidence-aware where applicable
- consistent with existing naming and architecture
- free of secrets and generated raw data
- formatted with Ruff
- accepted by strict mypy
- covered by pytest
- passing CI

When uncertain about an implementation detail, prefer inspecting the current code and requirements before introducing a new abstraction.

---

## Questions before contributing

If the README, current branch, requirements document, and tests do not clearly answer where a change belongs, discuss the intended boundary before implementing a large solution.

Stock DD MAS is being built incrementally. Small, well-tested changes that preserve clear boundaries are preferred over large changes that try to implement several future roadmap stages at once.
