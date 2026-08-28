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

The original financial-data foundation is working.

The management-research domain and SQLite persistence foundation are implemented and integration-tested.

The first SEC company-identity collection and ingestion vertical is also implemented and tested end to end.

The project is now ready to begin **SEC filing discovery**.

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
- repository-level persistence tests
- full SQLite persistence integration test
- transaction/reopen verification
- relationship-order preservation tests

The persistence layer preserves evidence citations, historical listing validity, partial-date precision, executive/event relationships, and ordered child collections where order is part of the domain representation.

### Completed SEC company-identity foundation

- provider-independent `CompanyIdentityCollector` contract
- typed `CompanyIdentityDataset`
- typed `CollectedCompanyIdentity`
- `SECCompanyIdentityCollector`
- SEC ticker/company/exchange collection
- configurable SEC `User-Agent`
- SEC HTTP error handling
- mocked HTTP tests
- SEC payload/schema validation
- ticker normalization
- zero-padded SEC CIK normalization
- support for missing SEC exchange values
- `CompanyIdentityIngestionService`
- application-owned `CompanyId` and `CompanyListingId` generation
- company resolution by CIK
- listing resolution by company/ticker/exchange
- preservation of existing internal IDs
- duplicate-prevention behavior
- SQLite-backed company-identity ingestion integration test
- database-close/reopen verification

The SEC provider adapter does **not** create trusted application IDs. Internal identity creation and persistence remain application/service responsibilities.

---

## Active development branch

At the time of writing, active management-research development is on:

```text
feature/management-research-foundation
```

Before beginning work, confirm that this is still the active branch and inspect its latest code rather than assuming `main` is current.

---

## Immediate development sequence

The financial foundation, management domain, SQLite persistence foundation, and SEC company-identity vertical are complete.

The immediate sequence is now:

```text
Provider-independent SEC filing discovery contract
    ↓
SEC filing discovery implementation
    ↓
Initial filing types:
    DEF 14A
    10-K
    8-K
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

## Current SEC company-identity pipeline

```text
Ticker
    ↓
SECCompanyIdentityCollector
    ↓
SEC company/ticker/exchange data
    ↓
CompanyIdentityDataset
    ↓
CollectedCompanyIdentity
    ↓
CompanyIdentityIngestionService
    ↓
CompanyIdentity + CompanyListing
    ↓
Repository contracts
    ↓
SQLite
```

Important identity rules:

- SEC-specific collection remains behind a provider-independent collector contract.
- SEC CIK values are normalized to 10-digit zero-padded strings.
- `CompanyId` and `CompanyListingId` are internal Stock DD MAS identifiers.
- Provider adapters do not generate application IDs.
- Existing companies are resolved by CIK.
- Existing listings are resolved within the trusted company by ticker and exchange.
- Repeated ingestion should reuse trusted records rather than create duplicates.
- A missing SEC exchange does not cause the application to invent an exchange.
- If the exchange is missing, the company can be stored without creating a trusted listing.
- The SEC collection timestamp is not treated as the listing's historical start date.
- Conflicting trusted identity information must not be silently overwritten.

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

## Collector boundaries

Provider-independent collection contracts live under:

```text
src/stock_dd/collectors/
```

The current collector architecture includes financial collection and company-identity collection.

Examples:

```text
FinancialDataCollector
    ↓
FMPFinancialDataCollector
```

and:

```text
CompanyIdentityCollector
    ↓
SECCompanyIdentityCollector
```

Application code should depend on provider-independent contracts where practical.

Provider-specific adapters are responsible for:

- network communication
- provider-specific request requirements
- provider response validation
- provider response normalization into collector-level types
- translating network/provider failures into application exceptions

Provider-specific collectors should not:

- create internal database identities
- persist trusted records directly
- assign management scores
- silently resolve conflicting trusted evidence

---

## Service boundary

Application services live under:

```text
src/stock_dd/services/
```

Services handle application-level workflows that should not belong to provider adapters or generic repositories.

The first implemented service is:

```text
CompanyIdentityIngestionService
```

Its responsibilities include:

- accepting typed collected identity data
- requiring an unambiguous collected match
- resolving an existing company by CIK
- creating a company when no trusted company exists
- preserving an existing internal company ID
- resolving an existing listing
- creating a listing when enough trusted information exists
- preserving existing listing IDs
- refusing to silently overwrite conflicting legal-company identity data

This layer is also responsible for internal ID creation rather than allowing external providers to invent application identities.

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

SQLite is the first implemented normalized persistence backend.

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

Merge/add/remove semantics belong in application/service logic rather than being guessed by generic repositories.

### Persistence integration

The SQLite persistence integration test verifies that a connected management-research graph can:

1. be written using the real repository implementations
2. participate in one caller-owned transaction
3. survive database closure
4. survive database reopening
5. retain important cross-record relationships
6. retain partial-date precision

A separate identity-ingestion integration test verifies the flow from SEC collector output through `CompanyIdentityIngestionService` into real SQLite repositories.

---

## Data-storage strategy

Use three conceptual layers.

### 1. Raw external data

Examples:

- FMP JSON
- SEC company/ticker data
- future SEC filing JSON/metadata
- future SEC filing HTML
- downloaded reports
- extracted webpage text
- future raw research-agent output

Raw data should be preserved where appropriate so parsing and normalization can be rerun without recollecting the source.

Default raw-data directory:

```text
data/raw/
```

It is ignored by Git.

FMP raw-response storage is already implemented.

SEC filing raw-source storage is a planned upcoming milestone.

### 2. Candidate evidence

Information extracted by a parser or research agent but not yet accepted as trusted fact.

`CandidateEvidence` preserves:

- extracted value
- citation
- extraction method
- verification status
- optional confidence
- optional company identity
- optional executive identity

Candidate evidence is not automatically trusted.

### 3. Normalized trusted data

Examples:

- `CompanyIdentity`
- `CompanyListing`
- `Executive`
- `ExecutiveRole`
- `CareerPosition`
- `CompanyEvent`
- `EvidenceSource`

These records are persistable in SQLite through repository interfaces.

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
├── services/
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
STOCK_DD_SEC_USER_AGENT=
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

### `STOCK_DD_SEC_USER_AGENT`

Identifying `User-Agent` used for automated SEC requests.

Example:

```text
Stock DD MAS contact@example.com
```

Use a contact address appropriate for automated SEC access.

Do not commit a personal contact address that you do not want published.

The real value belongs in the local `.env` file.

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

### SEC management-research status

SEC company-identity collection currently exists as an internal collector/service capability.

It has not yet been exposed as a complete management-research CLI workflow.

Do not assume that a dedicated SEC management CLI command exists until one is explicitly implemented and documented.

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

## Current SEC behavior

The current SEC implementation provides company-identity collection using SEC company/ticker/exchange information.

Current responsibilities include:

- request identification through the configured SEC `User-Agent`
- ticker normalization
- HTTP error translation
- JSON/schema validation
- company-name extraction
- ticker extraction
- exchange extraction
- CIK normalization
- support for missing exchange values

The SEC collector returns provider-independent typed data rather than trusted SQLite records.

Trusted identity persistence is handled separately by:

```text
CompanyIdentityIngestionService
```

Current SEC functionality does **not yet** include:

- filing discovery
- raw filing download/storage
- filing-document parsing
- executive extraction
- management-event extraction
- candidate-evidence generation from filings

Those belong to upcoming milestones.

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

Financial example:

```text
FinancialDataCollector
    ↓
FMPFinancialDataCollector
```

SEC identity example:

```text
CompanyIdentityCollector
    ↓
SECCompanyIdentityCollector
```

Use the same principle for filing discovery, research agents, and future providers.

### Define interfaces before provider/network implementations

Do not begin a provider-specific network implementation until the application-facing contract is clear and tested.

The intended pattern is:

```text
Application-facing contract
    ↓
Provider implementation
    ↓
Provider tests
    ↓
Application/service integration
```

### Separate collection from trusted persistence

External collectors should not directly decide what becomes trusted application state.

Example:

```text
SECCompanyIdentityCollector
    ↓
CompanyIdentityDataset
    ↓
CompanyIdentityIngestionService
    ↓
Trusted CompanyIdentity / CompanyListing
```

### Keep external IDs separate from internal IDs

External identifiers such as SEC CIK belong to the source/provider domain.

Internal identifiers such as:

```text
CompanyId
CompanyListingId
ExecutiveId
ExecutiveRoleId
```

belong to Stock DD MAS.

Provider adapters should not invent internal application IDs.

### Keep raw data separate from normalized data

Raw external responses should be preserved where appropriate.

Normalization converts provider-specific content into application-level data.

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

Examples:

- do not invent January 1 for a year-only date
- do not invent an exchange when SEC provides none
- do not treat collection time as listing start time

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

Do not assume the provider's idea of identity is the same as the application's internal identity.

### Preserve temporal precision

Do not convert uncertain dates into fake exact dates.

### Do not silently overwrite conflicts

If newly collected information conflicts with trusted data, surface the conflict rather than automatically replacing the trusted value.

Future promotion/conflict-handling logic should make those decisions explicitly.

---

## Testing strategy

The project uses several layers of tests.

### Unit tests

Used for:

- validation logic
- calculations
- parsers
- normalizers
- service behavior

### Contract tests

Used to confirm structural compatibility with provider-independent protocols.

Examples include:

- collector protocols
- repository protocols

### Repository tests

Used to verify:

- round trips
- query behavior
- stable-ID upserts
- replacement semantics
- foreign keys
- partial dates
- relationship ordering

### HTTP adapter tests

Provider HTTP behavior is tested with mocked transports rather than depending on live services during normal CI.

This provides deterministic tests for:

- successful responses
- HTTP failures
- network failures
- malformed JSON
- malformed provider records
- unexpected provider schema

### Integration tests

Integration tests verify that separately tested components work together.

Current examples include:

```text
Management domain graph
    ↓
All SQLite repositories
    ↓
One transaction
    ↓
Database reopen
```

and:

```text
SEC collector output
    ↓
CompanyIdentityIngestionService
    ↓
Real SQLite repositories
    ↓
Database reopen
    ↓
Repeated ingestion
    ↓
Same internal IDs
```

Integration tests should not duplicate every unit test. They should prove important boundaries work together.

---

## Branch and collaboration workflow

Before starting a contribution:

1. Pull the latest target branch.
2. Read this README.
3. Read relevant files under `docs/`.
4. Inspect the current implementation and tests.
5. Confirm the next roadmap item.
6. Make a focused change.
7. Run local quality checks.
8. Review the diff before committing.

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
feat: add company identity ingestion service
fix: preserve company event relationship order
refactor: extract SQLite date helpers
test: add company identity ingestion integration coverage
docs: update collaborator setup
```

Before pushing code:

```powershell
python -m ruff format .
python -m ruff check .
python -m mypy
python -m pytest --cov=stock_dd --cov-branch --cov-report=term-missing
```

Then review:

```powershell
git status
git diff
```

Stage the intended files:

```powershell
git add <files>
```

Review staged changes:

```powershell
git diff --staged
```

Commit and push:

```powershell
git commit -m "..."
git push
```

Do not commit directly to `main` for normal collaborative feature work unless the maintainer explicitly requests it.

---

## Where a new collaborator should start

### Step 1: Pull the current branch

At the time of writing:

```powershell
git switch feature/management-research-foundation
git pull
```

### Step 2: Run the existing application

```powershell
python -m stock_dd offline --input data/samples/northstar_robotics.json
```

### Step 3: Run the quality checks

```powershell
python -m ruff format .
python -m ruff check .
python -m mypy
python -m pytest --cov=stock_dd --cov-branch --cov-report=term-missing
```

### Step 4: Read the management requirements

```text
docs/management-research-requirements.md
```

### Step 5: Inspect the management domain and persistence layer

```text
src/stock_dd/models/
src/stock_dd/repositories/
src/stock_dd/repositories/sqlite/
src/stock_dd/storage/sqlite_schema.py
src/stock_dd/storage/sqlite_connection.py
```

### Step 6: Inspect the SEC identity flow

```text
src/stock_dd/collectors/company_identity.py
src/stock_dd/collectors/sec.py
src/stock_dd/services/company_identity.py
```

Then review their tests under:

```text
tests/
```

### Step 7: Check the current roadmap item

At the time of writing:

- SQLite persistence is complete and integration-tested.
- The SEC company-identity collector is complete.
- Company-identity ingestion into SQLite is complete and integration-tested.
- The next engineering milestone is **SEC filing discovery**.

Initial target forms:

```text
DEF 14A
10-K
8-K
```

The first implementation step should define the provider-independent filing-discovery contract before adding SEC-specific network behavior.

### Step 8: Make a small, tested contribution

Avoid large cross-cutting architecture changes as a first contribution.

Prefer one contract, implementation, or test milestone at a time.

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
- [x] Persistence integration test

### Structured management research

- [x] Provider-independent company/SEC identity collection interface
- [x] SEC company identity collection
- [x] SEC company identity resolution
- [x] Company identity ingestion service
- [x] SQLite-backed identity ingestion integration test
- [ ] Provider-independent SEC filing discovery contract
- [ ] SEC filing discovery
- [ ] Raw SEC filing storage
- [ ] Structured management-data extraction

Initial filing-discovery targets:

- `DEF 14A`
- `10-K`
- `8-K`

Later:

- Forms `3`
- `4`
- `5`

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
    Contributor orientation, setup, architecture, current status, and roadmap.

docs/management-research-requirements.md
    Management-research requirements and design constraints.

pyproject.toml
    Package metadata, dependencies, Ruff, mypy, pytest, and coverage settings.

.env.example
    Supported environment variables without real secrets.

src/stock_dd/models/
    Typed application and management-domain models.

src/stock_dd/collectors/
    Provider-independent collection contracts and provider implementations.

src/stock_dd/collectors/company_identity.py
    Provider-independent company-identity collection types and contract.

src/stock_dd/collectors/sec.py
    SEC company-identity provider adapter.

src/stock_dd/services/
    Application/service orchestration that sits above provider and repository
    boundaries.

src/stock_dd/services/company_identity.py
    Trusted company/listing identity ingestion and resolution.

src/stock_dd/repositories/
    Provider-independent persistence contracts.

src/stock_dd/repositories/sqlite/
    Concrete SQLite repository implementations.

src/stock_dd/storage/sqlite_schema.py
    SQLite schema version and initialization.

src/stock_dd/storage/sqlite_connection.py
    SQLite connection and caller-owned transaction helpers.

src/stock_dd/normalizers/
    Provider-specific financial normalization.

src/stock_dd/pipeline.py
    Offline and live financial pipeline orchestration.

tests/
    Unit, contract, HTTP-adapter, repository, and integration tests.

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
- local project handoff files intended to remain private

Before pushing:

```powershell
git status
```

The repository currently ignores local SQLite database files and related WAL/SHM files.

`PROJECT_HANDOFF.md` is also intended to remain local and ignored by Git.

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
- repository protocols exist before persistence-specific application dependencies
- provider-independent interfaces are designed before provider network implementations
- SEC provider code does not directly create internal application identities
- application services coordinate trusted persistence
- scoring is deferred until collection/evidence boundaries are mature

---

## Milestone-completion checklist

Before declaring a substantial management-research milestone complete, review the full path:

```text
Domain model
    ↓
Application / repository / collector contract
    ↓
Provider or persistence boundary
    ↓
Concrete implementation
    ↓
Public export
    ↓
Tests
```

For integration-heavy work, also ask:

```text
Do the pieces work together through the real boundary?
```

For each public method and meaningful optional/error branch, map behavior to a test checklist.

A milestone should not be considered complete merely because the happy-path implementation exists.

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

---

## Next milestone

The next planned milestone is:

```text
Provider-independent SEC filing discovery
```

The first filing types to support are:

```text
DEF 14A
10-K
8-K
```

The provider-independent contract should be defined and tested before implementing SEC-specific HTTP discovery.

The filing-discovery layer should preserve important metadata such as:

- CIK/company identity
- accession number
- filing form
- filing date
- report date where available
- primary document
- source URL or document location
- relevant point-in-time information

Raw filing preservation and structured management extraction come after the filing-discovery boundary is established.