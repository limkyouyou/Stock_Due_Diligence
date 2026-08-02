# Stock DD MAS — Management Research Requirements

**Version:** 0.1
**Status:** Draft
**Initial scope:** US publicly traded companies
**Default research period:** Previous five completed fiscal years, plus the current fiscal year when relevant

## 1. Purpose

The management research component of Stock DD MAS shall collect and organize evidence needed to assess:

1. relevant executive experience;
2. management execution record;
3. capital-allocation decisions;
4. shareholder alignment;
5. management stability and governance risk.

The collected information will eventually contribute to a management-quality assessment and the overall company-quality score.

The management score shall not be calculated directly from executive biographies or from an agent’s unsupported opinion. It must be based on traceable facts, measurements, transactions, and events.

## 2. Research architecture

Management research shall use two collection lanes.

### 2.1 Structured-data lane

The structured-data lane shall collect information available in predictable machine-readable or consistently structured formats.

Examples include:

* company identifiers;
* financial statements;
* revenue, margins, and free cash flow;
* capital expenditures;
* debt issuance and repayment;
* dividends;
* share repurchases;
* share issuance;
* shares outstanding;
* SEC filing metadata;
* structured insider-ownership filings.

The SEC provides company submission histories and extracted XBRL facts through its public data APIs.

### 2.2 Unstructured-research lane

The unstructured-research lane shall search and extract information from narrative documents and webpages.

Examples include:

* executive biographies;
* employment history;
* company guidance;
* major milestones;
* major setbacks;
* explanations for executive departures;
* governance concerns;
* company announcements;
* independent reporting.

An agent may perform discovery and extraction, but its output shall initially be treated as candidate evidence rather than verified fact.

### 2.3 Shared evidence layer

Both collection lanes shall produce or reference evidence records.

The overall flow shall be:

```text
External source
    ↓
Raw source storage
    ↓
Structured parser or research agent
    ↓
Candidate evidence
    ↓
Validation and normalization
    ↓
Trusted management records
    ↓
Analysis and scoring
```

## 3. Initial coverage

Version 0.1 shall support:

* US domestic publicly traded companies;
* the current chief executive officer;
* the current chief financial officer;
* previous CEO and CFO appointments and departures within the research period;
* the previous five years of career history when disclosed;
* evidence available through SEC filings and public company materials.

The following may be included when relevant but are not required initially:

* president;
* chief operating officer;
* executive chair;
* lead independent director;
* founders with significant operational control.

Foreign private issuers, private companies, and companies without adequate public disclosures are outside the initial scope.

## 4. Point-in-time research requirement

Every research run shall have an explicit `as_of_date`.

The system must only use information that was publicly available on or before that date.

For example, a report evaluating a company as of December 31, 2024 must not use an executive appointment announced in 2025.

Each stored source shall preserve:

* publication or filing date;
* retrieval timestamp;
* effective date when stated;
* reporting period when applicable.

This requirement prevents future information from leaking into historical evaluations and backtests.

## 5. Company identity requirements

Each supported company shall have a stable internal identifier.

The company record shall contain:

* internal company ID;
* legal company name;
* ticker symbol;
* exchange;
* SEC Central Index Key, or CIK;
* reporting currency;
* fiscal year-end;
* active or inactive status;
* alternate or previous company names when known.

Ticker symbols shall not be used as permanent identifiers because tickers can change or be reused.

## 6. Executive identity requirements

Each executive shall have a stable internal identifier.

The executive record shall contain:

* internal executive ID;
* full legal or commonly reported name;
* alternate name forms when needed;
* current known professional status;
* source evidence supporting the identity.

The system shall not assume that two records refer to the same person based only on similar names.

Identity matching may consider:

* full name;
* middle name or initial;
* employer;
* role;
* employment dates;
* education or other distinguishing information.

Uncertain identity matches must remain separate or be flagged for human review.

## 7. Executive role requirements

Company employment and leadership roles shall be stored separately from executive identity.

Each executive role shall contain:

* executive ID;
* company ID;
* normalized title;
* title as written by the source;
* role category;
* start date;
* end date;
* whether the role is interim;
* whether the executive is currently active;
* appointment announcement date when available;
* departure announcement date when available;
* departure reason when explicitly disclosed;
* supporting evidence.

Required initial role categories are:

* chief executive officer;
* chief financial officer;
* president;
* chief operating officer;
* executive chair;
* other executive officer.

The system shall distinguish between:

* appointment announcement date;
* effective start date;
* resignation announcement date;
* effective departure date.

SEC Form 8-K Item 5.02 covers certain director and principal-officer appointments and departures and will be an important source for these records.

## 8. Career-position requirements

Each known previous position shall be stored as an individual career record.

A career-position record shall contain:

* executive ID;
* employer name;
* employer internal ID when matched to a known company;
* job title;
* normalized role category when possible;
* start date or year;
* end date or year;
* industry classification when known;
* whether the employer was publicly traded;
* whether the position was an executive leadership role;
* supporting evidence;
* data-quality status.

Approximate dates shall be marked as approximate rather than converted into invented exact dates.

The system shall collect employment history first. Measurements such as “years of relevant industry experience” shall be derived later using documented rules.

## 9. Relevant-experience assessment inputs

The following inputs may later be derived from executive and career records:

* total years of professional experience;
* total years in executive roles;
* previous CEO or CFO experience;
* previous public-company leadership experience;
* industry-relevant experience;
* current-company tenure;
* experience managing a similarly sized company;
* experience through different economic cycles;
* founder status;
* board experience.

These values shall not be treated as proof of management quality by themselves.

Education, awards, and professional qualifications may be collected as optional background information, but they shall initially receive no direct management-quality score.

## 10. Execution-record requirements

Management execution shall be evaluated through company outcomes occurring during a defined leadership period.

### 10.1 Financial measurements

The system shall make available, by fiscal period:

* revenue;
* revenue growth;
* operating income;
* operating margin;
* net income;
* operating cash flow;
* capital expenditure;
* free cash flow;
* debt;
* diluted shares outstanding.

These measurements may already exist in the financial research dataset and should be referenced rather than duplicated.

The system shall associate financial periods with executive tenure but shall not claim that an executive alone caused the results.

### 10.2 Guidance targets

Each management target or guidance statement shall be stored separately.

A guidance target shall contain:

* company ID;
* metric;
* target period;
* target type;
* exact target value or range;
* unit and currency;
* date announced;
* management wording;
* guidance status;
* related executive IDs when clearly identified;
* supporting evidence.

Supported guidance statuses shall include:

* original;
* maintained;
* raised;
* lowered;
* withdrawn;
* replaced;
* completed.

Examples of target types include:

* revenue;
* earnings per share;
* operating margin;
* capital expenditure;
* free cash flow;
* subscriber or customer count;
* production volume;
* store or facility openings.

### 10.3 Guidance evaluations

A guidance evaluation shall contain:

* guidance target ID;
* actual result;
* comparison date;
* result classification;
* numerical variance when calculable;
* evaluation method;
* confidence status.

Supported result classifications shall include:

* exceeded;
* met;
* partially met;
* missed;
* not comparable;
* unresolved.

The system shall not use a single company-wide `targets_met` boolean.

### 10.4 Company events

Milestones and setbacks shall be represented as dated company events.

Initial event types shall include:

* product launch;
* product discontinuation;
* facility opening;
* facility closure;
* geographic expansion;
* market exit;
* major contract win;
* major contract loss;
* acquisition;
* divestiture;
* restructuring;
* regulatory action;
* litigation development;
* cybersecurity incident;
* accounting restatement;
* executive appointment;
* executive departure;
* auditor change.

An event shall contain:

* internal event ID;
* company ID;
* event type;
* announcement date;
* effective or occurrence date;
* concise factual description;
* affected business area;
* related executive IDs when appropriate;
* related financial amount when known;
* source evidence;
* verification status.

The collection stage shall not automatically label an event as good, bad, successful, failed, or major unless the classification follows an explicit deterministic rule.

## 11. Capital-allocation requirements

Capital allocation shall be represented through dated financial records and transactions rather than permanent yes/no company attributes.

Initial capital-allocation categories shall include:

* capital expenditure;
* research and development;
* acquisition spending;
* proceeds from divestitures;
* debt issuance;
* debt repayment;
* share repurchases;
* dividends;
* share issuance.

Each capital-allocation record shall contain:

* company ID;
* category;
* reporting period or transaction date;
* amount;
* currency;
* cash-flow direction;
* related event ID when applicable;
* source evidence.

Derived analysis may later calculate:

* capital-allocation mix;
* acquisition spending as a percentage of free cash flow;
* repurchases relative to share issuance;
* net debt reduction;
* dividend coverage;
* changes in diluted share count;
* reinvestment intensity.

The term “reinvestment in the business” shall not be stored as one undifferentiated amount when more specific categories are available.

## 12. Shareholder-alignment requirements

Shareholder alignment shall be assessed from several underlying forms of evidence.

### 12.1 Executive ownership

Ownership snapshots shall contain:

* executive ID;
* company ID;
* ownership date;
* shares owned directly;
* shares owned indirectly;
* exercisable options when separately reported;
* ownership percentage when available;
* source evidence.

### 12.2 Insider transactions

Each insider transaction shall contain:

* executive or insider ID;
* company ID;
* transaction date;
* transaction code or normalized type;
* number of shares;
* transaction price;
* ownership following the transaction when reported;
* direct or indirect ownership;
* whether the transaction was related to compensation;
* whether a trading plan was disclosed;
* source evidence.

SEC Forms 3, 4, and 5 provide ownership and transaction information for officers, directors, and certain major beneficial owners. The SEC also publishes structured insider-transaction datasets.

An insider sale shall not automatically be classified as negative. Grants, option exercises, tax withholding, gifts, scheduled sales, and open-market purchases must be distinguished.

### 12.3 Executive compensation

Later versions may collect:

* base salary;
* annual cash incentive;
* stock awards;
* option awards;
* other compensation;
* total reported compensation;
* performance metrics;
* vesting periods;
* severance arrangements;
* change-of-control arrangements;
* compensation actually paid when available.

Executive compensation information can be located in proxy statements, annual reports, registration statements, and certain current reports. Proxy disclosure also explains the criteria used in compensation decisions and its relationship to performance.

Compensation collection is optional for the first implementation but required before a complete shareholder-alignment score is introduced.

## 13. Management stability requirements

The system shall preserve enough information to derive:

* CEO tenure;
* CFO tenure;
* number of CEO changes within the research period;
* number of CFO changes within the research period;
* frequency of interim appointments;
* unexplained executive departures;
* simultaneous departures of multiple senior executives;
* internal versus external succession;
* length of leadership vacancies.

A departure reason shall be stored only when explicitly disclosed.

Examples of acceptable values include:

* retirement;
* resignation;
* termination;
* role transition;
* health-related departure;
* acquisition-related departure;
* reason not disclosed.

“Reason not disclosed” shall not be interpreted as misconduct.

## 14. Governance requirements

Management and board governance shall be treated as related but distinct topics.

The initial governance dataset should eventually support:

* CEO and board-chair role combination;
* lead independent director;
* board size;
* independent director count;
* board independence ratio;
* audit committee composition;
* compensation committee composition;
* related-party transactions;
* controlling shareholders;
* succession-plan disclosures;
* code-of-ethics waivers;
* shareholder voting results;
* material weaknesses in internal controls.

Proxy and periodic disclosures commonly contain executive compensation, related-person transactions, director independence, governance matters, and officer or director ownership.

Board governance is not required for the first executive-profile implementation, but the architecture must not assume that executive information alone provides a complete governance assessment.

## 15. Governance-risk event requirements

The following events shall eventually be detectable:

* auditor resignation, dismissal, or replacement;
* financial-statement non-reliance;
* accounting restatement;
* material weakness;
* code-of-ethics amendment or waiver;
* change in company control;
* related-party transaction;
* executive suspension or termination;
* regulatory enforcement;
* unresolved material litigation.

Form 8-K includes distinct items for certifying-accountant changes, non-reliance on previous financial statements, changes in control, executive departures and appointments, and certain code-of-ethics changes.

Annual and quarterly reports also contain risk factors, controls and procedures, legal proceedings, and management discussion that may provide governance-risk evidence.

The presence of an event shall not automatically determine its severity. The system must preserve the facts and allow later analysis to consider context.

## 16. Evidence-source requirements

Every normalized factual record shall reference at least one evidence source unless it is a deterministic calculation from already sourced data.

Each evidence source shall contain:

* internal source ID;
* source type;
* publisher or filing entity;
* document title;
* URL or SEC accession number;
* filing form when applicable;
* publication or filing date;
* retrieval timestamp;
* local raw-file path;
* document hash when practical;
* language;
* accessibility status.

For extracted text, the evidence connection should also preserve:

* supporting excerpt;
* section or heading;
* page number when available;
* extraction method;
* extractor version;
* extraction confidence.

## 17. Source hierarchy

Sources shall be prioritized in this order:

1. regulator filings and official government records;
2. audited company filings;
3. company investor-relations documents;
4. official company announcements;
5. reputable independent reporting;
6. direct executive interviews or conference material;
7. discovery sources such as Wikipedia;
8. optional manually reviewed professional profiles.

A lower-ranked source may be useful for discovering a fact but should not replace an available primary source.

LinkedIn shall not be a required automated source.

## 18. Candidate-evidence requirements

Unstructured research shall first create candidate-evidence records.

A candidate-evidence record shall contain:

* candidate ID;
* subject type;
* subject identifier when known;
* claim type;
* extracted value;
* related company;
* related executives;
* source ID;
* supporting excerpt;
* extraction method;
* extraction confidence;
* verification status;
* rejection reason when rejected.

Supported verification statuses shall include:

* unreviewed;
* parser-confirmed;
* primary-source-confirmed;
* multiple-source-confirmed;
* disputed;
* rejected.

Research-agent confidence shall not be treated as factual certainty.

## 19. Conflicting-evidence requirements

When sources disagree, the system shall not silently overwrite an existing value.

It shall:

1. retain both claims;
2. preserve both sources;
3. prefer the most authoritative and current applicable source;
4. mark the conflict;
5. require human review when the conflict affects a material field.

Corrected, amended, or superseding filings must remain connected to the original source.

## 20. Missing-data requirements

The system shall distinguish between:

* known value;
* not disclosed;
* not found;
* not applicable;
* conflicting;
* insufficient evidence;
* outside research period.

Missing information shall not automatically reduce the management score.

For example, an unavailable appointment date is not evidence of poor management.

The final report shall show data coverage and identify important missing fields.

## 21. Confidence and coverage requirements

Every management assessment shall include:

* overall evidence confidence;
* structured-data coverage;
* unstructured-research coverage;
* number of primary sources;
* number of unresolved conflicts;
* important missing categories;
* latest source date.

A high management score based on weak coverage must be clearly distinguished from a high score based on strong evidence.

## 22. Agent-research reproducibility

Each unstructured research run shall preserve:

* research task;
* company identifier;
* requested research period;
* agent or model identifier;
* prompt version;
* enabled tools;
* run timestamp;
* visited source URLs;
* raw agent output;
* extraction version;
* execution status.

The system should be able to explain where a claim came from even when the same agent produces different results on a later run.

## 23. Attribution requirements

The system may state that an outcome occurred during an executive’s tenure.

It shall not state that the executive caused the outcome unless the evidence directly supports that conclusion.

Acceptable:

> Operating margin increased from 12% to 18% during the CEO’s first four completed fiscal years.

Not automatically acceptable:

> The CEO increased operating margin from 12% to 18%.

Management analysis shall distinguish correlation, timing, and supported causation.

## 24. Scoring restrictions

Version 0.1 shall collect evidence but shall not implement a final management-quality score.

Before scoring begins, the project must define:

* scoring categories;
* category weights;
* minimum evidence requirements;
* peer or industry benchmarks;
* treatment of missing data;
* treatment of conflicting evidence;
* confidence adjustments;
* rules preventing double counting.

The score must be accompanied by the underlying evidence and must not be presented as an objective fact.

## 25. Data-storage requirements

Raw data shall be stored as immutable or append-only files.

Examples include:

* FMP JSON;
* SEC JSON;
* SEC filing HTML;
* downloaded reports;
* extracted webpage text;
* raw agent research output.

Normalized records shall eventually be stored in SQLite and accessed through repository interfaces.

Application and analysis logic shall operate on typed Python domain objects rather than raw database rows.

The logical datasets are expected to include:

```text
companies
executives
executive_roles
career_positions
financial_metrics
guidance_targets
guidance_evaluations
capital_allocation_records
executive_ownership_snapshots
insider_transactions
compensation_records
company_events
governance_records
evidence_sources
candidate_evidence
```

Not all datasets must be implemented at once.

## 26. Initial implementation milestone

The first management-research implementation shall collect only:

* company identity;
* current CEO;
* current CFO;
* executive role titles;
* appointment or effective dates when disclosed;
* previous employers;
* previous job titles;
* previous-role dates when disclosed;
* appointment events;
* departure events;
* evidence source metadata.

The first implementation shall not yet:

* calculate a management score;
* classify executives as good or bad;
* determine whether milestones were successful;
* mine every possible website;
* evaluate compensation;
* interpret insider sales;
* assess full board governance;
* automatically change valuation assumptions.

## 27. Acceptance criteria for the first milestone

The first milestone is complete when Stock DD MAS can, for a supported company:

1. resolve the company to a stable company and SEC identifier;
2. identify the current CEO and CFO;
3. store each executive separately from their company role;
4. preserve known role start dates;
5. store available previous career positions;
6. record executive appointment and departure events;
7. connect every accepted fact to source evidence;
8. represent missing information without guessing;
9. store raw source documents separately from normalized records;
10. produce the same normalized result when processing the same saved raw input.

## 28. Deferred requirements

The following are intentionally deferred:

* full autonomous web research;
* product and expansion event mining;
* guidance extraction and evaluation;
* detailed capital-allocation analysis;
* compensation analysis;
* insider-transaction interpretation;
* board-governance scoring;
* peer comparison;
* management-quality scoring;
* integration with intrinsic-value assumptions;
* coverage of foreign and private companies.
