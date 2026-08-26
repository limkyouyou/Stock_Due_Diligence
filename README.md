# Stock DD MAS

Stock DD MAS is a modular stock due-diligence research application for organizing evidence about public companies, assessing business and management quality, estimating an intrinsic-value range, and eventually comparing that range with the market price.

The project is in **early development** and is being built incrementally as a portfolio/learning project using practical industry-standard Python practices: typed domain models, provider-independent interfaces, explicit validation, repository boundaries, SQLite persistence, test coverage, CI, raw-source preservation, and evidence traceability.

> **Important:** Stock DD MAS is a research tool under development. Its outputs are not financial advice and should not be treated as a recommendation to buy or sell a security.

---

## Project identity

Use these names consistently:

- **Application:** Stock DD MAS
- **Python distribution:** `stock-dd`
- **Python package:** `stock_dd`
- **Current package version:** `0.1.0`
- **Python version used for development:** **3.14.2**

The GitHub repository is currently named `Stock_Due_Diligence`, but application and code references should use the names above.

Repository:

```text
https://github.com/limkyouyou/Stock_Due_Diligence
```

---

## Current platform support

### Supported contributor environment

The current development setup officially supports **Windows only**:

- Windows 11
- PowerShell
- Python 3.14.2
- Git
- VS Code or another Python-capable editor

Linux and macOS are not currently validated contributor environments. They may work, but contributors should not assume platform-specific compatibility.

GitHub Actions runs automated quality checks on Ubuntu. This provides an additional compatibility signal but does not make Linux an officially supported local-development environment.

---

## Current project status

The original financial-data foundation is working, and the first management-research persistence foundation is now implemented.

### Completed financial foundation

- `src`-layout Python package
- `pyproject.toml` packaging
- editable installation
- offline JSON research-data loading and validation
- typed dataclass models
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

### Completed engineering foundation

- Ruff linting and formatting
- strict mypy type checking
- pytest
- branch coverage with a minimum threshold of 90%
- GitHub Actions CI
- isolated SQLite test databases
- explicit SQLite connection management
- caller-owned SQLite transactions
- SQLite foreign-key enforcement

### Completed management-research foundation

- management-research requirements document
- management-research domain models
- typed internal identifiers
- `PartialDate` for incomplete dates
- evidence-source and candidate-evidence models
- company and listing identity models
- executive, role, and career-position models
- company-event model
- provider-independent repository contracts
- SQLite schema version 1
- eight concrete SQLite repository implementations:
  - `SQLiteCompanyRepository`
  - `SQLiteCompanyListingRepository`
  - `SQLiteEvidenceSourceRepository`
  - `SQLiteCandidateEvidenceRepository`
  - `SQLiteExecutiveRepository`
  - `SQLiteExecutiveRoleRepository`
  - `SQLiteCareerPositionRepository`
  - `SQLiteCompanyEventRepository`

The persistence layer preserves evidence citations, historical listing validity, partial-date precision, executive/event relationships, and ordered child collections where order is part of the domain representation.

---

## Active development branch

At the time of writing, active management-research development is on:

```text
feature/management-research-foundation
```

Before beginning work, confirm that this is still the active branch and inspect its latest code rather than assuming `main` is current.

---

## Immediate development sequence

The repository contracts and first SQLite implementations are complete.

The immediate sequence is now:

```text
SQLite persistence integration test
    ↓
Provider-independent SEC/company collection interfaces
    ↓
SEC company identity resolution
    ↓
SEC filing discovery
    ↓
Raw SEC filing storage
    ↓
Structured management-data extraction
    ↓
Unstructured research-agent interface
    ↓
Candidate evidence
    ↓
Evidence validation / conflict handling
    ↓
Promotion to trusted management records
    ↓
Management research packet/report
    ↓
Later scoring and valuation integration
```

Do not skip directly to a research agent or management score before the collection, evidence, and validation boundaries are in place.

The detailed management-research specification is:

```text
docs/management-research-requirements.md
```

Read that file before changing management-related models, storage, collection, validation, or scoring.

---

## Long-term objective

Stock DD MAS is intended to produce three broad outputs.

### 1. Company-quality assessment

Evaluate how solid a company appears using evidence such as:

- financial performance
- management quality
- execution record
- capital allocation
- shareholder alignment
- stability and governance risk
- later business and industry factors

### 2. Estimated intrinsic-value range

The application should eventually estimate a defensible **range** rather than claim one exact "true value."

### 3. Market comparison

The intrinsic-value range can later be compared with market price together with assumptions, uncertainty, confidence, and supporting evidence.

Management quality should contribute evidence to investment analysis. It should not mechanically add or subtract an arbitrary dollar amount from valuation.

---

## Current financial pipeline

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

Provider-specific response structures are intentionally isolated from normalized application models.

---

## Management-research architecture

Management research uses two collection lanes.

### Structured-data lane

Used for predictable structured or semi-structured information, including:

- company identifiers
- SEC filing metadata
- financial statements
- capital expenditures
- debt issuance and repayment
- dividends
- share repurchases
- share issuance
- structured insider ownership and transaction data

### Unstructured-research lane

Used for narrative documents and webpages, including:

- executive biographies
- previous career positions
- management guidance
- company milestones
- setbacks
- executive appointment/departure explanations
- governance concerns
- company announcements
- reputable independent reporting

A future research agent may assist the unstructured lane, but agent output is **not automatically trusted data**.

Intended flow:

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

A research agent should not search the web and directly assign a management score.

---

## Initial management-research scope

### Companies

Initial coverage is limited to:

- US domestic publicly traded companies

### Executives

Initial executive coverage focuses on:

- current CEO
- current CFO
- recent CEO/CFO appointments and departures
- available previous career history, primarily over the previous five years

### Initial trusted facts

Examples include:

- company identity
- SEC CIK
- listing identity/history
- executive identity
- current role
- role start/effective dates where disclosed
- previous employers
- previous titles
- previous-role dates where disclosed
- appointment events
- departure events
- source/evidence metadata

### Not in the first implementation

The initial management-research system does not yet:

- calculate a final management-quality score
- classify executives as "good" or "bad"
- automatically interpret insider selling
- perform complete compensation analysis
- perform full board-governance scoring
- automatically alter valuation assumptions
- mine every available website

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

Discovery sources may help locate evidence but should not replace an available primary source.

When sources disagree, do not silently overwrite one value with another. Preserve evidence and surface the conflict.

---

## Point-in-time correctness

Management research must eventually support an explicit `as_of_date`.

A historical research run must not use information that became public after the requested cutoff.

Example:

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

Do not invent an exact day when a source provides only a year or month.

`PartialDate` exists for this reason.

Examples:

```text
2022
2022-07
2022-07-15
```

must remain distinguishable.

---

## Domain model structure

Important management-domain modules:

```text
src/stock_dd/models/
├── __init__.py
├── company.py
├── dates.py
├── evidence.py
├── events.py
├── executives.py
└── identifiers.py
```

`models/__init__.py` is the public re-export surface.

Application code should normally prefer:

```python
from stock_dd.models import CompanyIdentity, Executive
```

over importing internal model modules directly.

### Important domain types

Company identity:

- `CompanyIdentity`
- `CompanyListing`
- `CompanyId`
- `CompanyListingId`

Evidence:

- `EvidenceSource`
- `EvidenceCitation`
- `CandidateEvidence`
- `EvidenceSourceId`
- `CandidateEvidenceId`

Management:

- `Executive`
- `ExecutiveRole`
- `CareerPosition`
- `ExecutiveId`
- `ExecutiveRoleId`
- `CareerPositionId`

Events:

- `CompanyEvent`
- `CompanyEventId`

Dates:

- `PartialDate`
- `DatePrecision`

---

## Repository boundary

Provider-independent repository contracts live under:

```text
src/stock_dd/repositories/
```

Current contracts:

```text
CompanyRepository
CompanyListingRepository
EvidenceSourceRepository
CandidateEvidenceRepository
ExecutiveRepository
ExecutiveRoleRepository
CareerPositionRepository
CompanyEventRepository
```

Application/service logic should depend on these contracts where practical rather than on SQLite-specific classes.

Concrete SQLite implementations live under:

```text
src/stock_dd/repositories/sqlite/
```

---

## SQLite persistence

SQLite is now the first implemented normalized persistence backend.

### Database path

Default:

```text
data/stock_dd.sqlite3
```

Configurable with:

```dotenv
STOCK_DD_DATABASE_PATH=data/stock_dd.sqlite3
```

Local SQLite database files are ignored by Git.

### Schema

Schema initialization is defined in:

```text
src/stock_dd/storage/sqlite_schema.py
```

Current schema version:

```text
1
```

Important tables include:

- companies
- company alternate names
- company listings
- evidence sources
- candidate evidence
- executives
- executive alternate names
- executive citations
- executive roles
- executive-role citations
- career positions
- career-position citations
- company events
- company-event citations
- company-event executive relationships
- company-event role relationships

### Partial dates

Incomplete dates are stored as separate components:

```text
year
month
day
```

The persistence layer must not convert year-only or month-only dates into fake exact dates.

Shared SQLite conversion helpers live in:

```text
src/stock_dd/repositories/sqlite/_dates.py
```

### Connection and transaction rules

SQLite connection helpers live in:

```text
src/stock_dd/storage/sqlite_connection.py
```

Connections:

- use `sqlite3.Row`
- enable `PRAGMA foreign_keys = ON`
- are explicitly closed

Transactions are caller-owned.

Repository implementations must **not** call `commit()` or start their own transaction.

This allows multiple repository writes to participate in one atomic operation.

### Repository `save()` semantics

Repository `save()` methods are full-object upserts.

For child tuples such as:

```python
event.related_executive_ids
event.related_role_ids
event.citations
```

the saved tuple is treated as the complete current representation, not as a partial patch.

For example, to add an executive while preserving existing executives, higher-level logic should first load the existing event and construct the complete updated tuple.

Merge/add/remove semantics belong in a future application/service layer rather than being guessed by generic repositories.

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

Raw data should be preserved so normalization can be rerun without recollecting the source.

Default raw-data directory:

```text
data/raw/
```

It is ignored by Git.

### 2. Candidate evidence

Information extracted by a parser or research agent but not yet accepted as trusted fact.

`CandidateEvidence` preserves the extracted value, citation, extraction method, verification status, optional confidence, and optional links to known company/executive identities.

### 3. Normalized trusted data

Examples:

- `CompanyIdentity`
- `CompanyListing`
- `Executive`
- `ExecutiveRole`
- `CareerPosition`
- `CompanyEvent`
- `EvidenceSource`

These records are now persistable in SQLite through repository interfaces.

Application logic should operate on typed domain objects rather than raw SQL rows.

---

## Repository structure

Important top-level paths:

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

Important package areas:

```text
src/stock_dd/
├── collectors/
├── models/
├── normalizers/
├── repositories/
│   └── sqlite/
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

---

## Windows development setup

### 1. Clone the repository

```powershell
git clone https://github.com/limkyouyou/Stock_Due_Diligence.git
cd Stock_Due_Diligence
```

### 2. Switch to the active development branch

At the time of writing:

```powershell
git switch feature/management-research-foundation
git pull
```

For future work, confirm the active branch before starting.

### 3. Confirm Python

```powershell
python --version
```

Expected development version:

```text
Python 3.14.2
```

### 4. Create a virtual environment

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

### 7. Install the project with development dependencies

```powershell
python -m pip install --editable ".[dev]"
```

---

## Environment configuration

Copy:

```powershell
Copy-Item .env.example .env
```

Current environment variables:

```dotenv
STOCK_DD_FINANCIAL_API_KEY=
STOCK_DD_RAW_DATA_DIR=data/raw
STOCK_DD_DATABASE_PATH=data/stock_dd.sqlite3
```

### `STOCK_DD_FINANCIAL_API_KEY`

Required for the live FMP financial-data pipeline.

Never commit real API keys.

### `STOCK_DD_RAW_DATA_DIR`

Directory for unmodified provider responses.

Default:

```text
data/raw
```

### `STOCK_DD_DATABASE_PATH`

Path to the local SQLite database containing normalized application data.

Default:

```text
data/stock_dd.sqlite3
```

---

## Running Stock DD MAS

### Offline mode

No API key required:

```powershell
python -m stock_dd offline --input data/samples/northstar_robotics.json
```

Optional output:

```powershell
python -m stock_dd offline `
    --input data/samples/northstar_robotics.json `
    --output reports/northstar.md
```

### Live financial mode

Requires an FMP API key:

```powershell
python -m stock_dd live --ticker AAPL
```

Request another annual period limit:

```powershell
python -m stock_dd live --ticker AAPL --annual-limit 5
```

### Verbose logging

`--verbose` is a global option and appears before the subcommand:

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

Important normalization rule:

```text
FMP capitalExpenditure
→ normalized as a positive amount spent
```

The annual financial-statement date is used as the financial report's `as_of_date`.

The raw collection timestamp is stored separately from the statement reporting date.

FMP news is not currently part of the project. Do not assume access to paid FMP news endpoints.

---

## Quality requirements

Before pushing code:

```powershell
python -m ruff format .
python -m ruff check .
python -m mypy
python -m pytest --cov=stock_dd --cov-branch --cov-report=term-missing
```

Requirements:

- Ruff formatting
- Ruff linting
- strict mypy
- pytest
- branch coverage
- coverage of at least 90%

Do not rely on CI to format code.

---

## Continuous integration

GitHub Actions currently runs quality checks for:

- pushes to `main`
- pushes to `feature/management-research-foundation`
- pull requests

CI checks:

- Ruff linting
- Ruff formatting
- strict mypy
- pytest with coverage

A contribution should not be considered ready to merge while CI is failing.

---

## Development principles

### Keep provider-specific code behind interfaces

Example:

```text
FinancialDataCollector
    ↓
FMPFinancialDataCollector
```

Use the same design principle for SEC collection, research agents, and persistence.

### Define interfaces before provider/network implementations

Do not begin a provider-specific network implementation until the application-facing contract is clear and tested.

### Keep raw data separate from normalized data

Raw external responses should be preserved.

Normalization converts provider-specific content into application-domain data.

### Do not let agents become the source of truth

Future research agents should produce `CandidateEvidence`.

Validation and promotion decide whether a claim becomes trusted data.

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

Missing and conflicting information should remain visible.

### Keep scoring out of collection

```text
Collection
    ↓
Normalization / extraction
    ↓
Validation
    ↓
Trusted evidence
    ↓
Analysis
    ↓
Scoring later
```

### Preserve identity boundaries

Do not assume two people are the same because their names match.

Do not treat a free-text employer name as a resolved `CompanyIdentity`.

### Preserve temporal precision

Do not convert uncertain dates into fake exact dates.

---

## Branch and collaboration workflow

Before starting a contribution:

1. Pull the latest target branch.
2. Read this README.
3. Read relevant files under `docs/`.
4. Inspect the current implementation and tests.
5. Confirm the next roadmap item.
6. Make a focused change.

Branch naming examples:

```text
feature/<short-description>
fix/<short-description>
refactor/<short-description>
test/<short-description>
docs/<short-description>
```

Commit examples:

```text
feat: add SEC company collector contract
fix: preserve company event relationship order
refactor: extract SQLite date helpers
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
git push
```

Do not commit directly to `main` for normal collaborative feature work unless the maintainer explicitly requests it.

---

## Where a new collaborator should start

### Step 1: Run the existing application

```powershell
python -m stock_dd offline --input data/samples/northstar_robotics.json
```

### Step 2: Read the management requirements

```text
docs/management-research-requirements.md
```

### Step 3: Inspect the management domain and repositories

```text
src/stock_dd/models/
src/stock_dd/repositories/
src/stock_dd/repositories/sqlite/
src/stock_dd/storage/sqlite_schema.py
src/stock_dd/storage/sqlite_connection.py
```

### Step 4: Check the current roadmap item

At the time of writing, repository contracts and the first SQLite repository implementations are complete.

The next planned engineering step is a persistence integration test before beginning SEC collection interfaces.

### Step 5: Make a small, tested contribution

Avoid large cross-cutting architecture changes as a first contribution.

---

## Current roadmap

### Foundation

- [x] Offline financial prototype
- [x] Engineering-quality foundation
- [x] Live financial-data pipeline
- [x] Management Research Requirements v0.1
- [x] Management domain models
- [x] Repository contracts
- [x] SQLite schema and transaction infrastructure
- [x] SQLite repository implementations
- [ ] Persistence integration test

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
    Contributor orientation, setup, architecture, and roadmap.

docs/management-research-requirements.md
    Management-research requirements and design constraints.

pyproject.toml
    Package metadata, dependencies, Ruff, mypy, pytest, and coverage settings.

.env.example
    Supported environment variables without real secrets.

src/stock_dd/models/
    Typed domain models.

src/stock_dd/repositories/
    Provider-independent persistence contracts.

src/stock_dd/repositories/sqlite/
    Concrete SQLite repository implementations.

src/stock_dd/storage/sqlite_schema.py
    SQLite schema version and initialization.

src/stock_dd/storage/sqlite_connection.py
    SQLite connection and caller-owned transaction helpers.

src/stock_dd/collectors/
    Provider-independent collection contracts and provider implementations.

src/stock_dd/normalizers/
    Provider-specific normalization.

src/stock_dd/pipeline.py
    Offline and live pipeline orchestration.

tests/
    Unit, contract, repository, and persistence tests.

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
- local SQLite databases
- generated reports
- `.venv/`
- coverage/cache files

Before pushing:

```powershell
git status
```

If a secret is accidentally committed, deleting it in a later commit does not remove it from Git history. Rotate the credential and address the history appropriately.

---

## Notes for architectural changes

Before proposing an architectural change:

1. inspect the current implementation
2. inspect the relevant tests
3. identify the current abstraction boundary
4. explain the problem the change solves
5. prefer the smallest practical design
6. add or update tests
7. update documentation when behavior or architecture changes

This project intentionally avoids unnecessary frameworks and abstractions.

Current examples:

- no external multi-agent framework is required
- SQLite is the first normalized persistence backend
- repository protocols exist before provider-specific persistence dependencies
- provider-independent interfaces are designed before SEC network implementations

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

When uncertain, inspect the current feature branch, requirements, contracts, implementation, and tests before adding a new abstraction.
