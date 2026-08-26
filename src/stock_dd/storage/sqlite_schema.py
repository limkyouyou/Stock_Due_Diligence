"""SQLite schema initialization for normalized Stock DD data."""

import sqlite3

SCHEMA_VERSION = 1


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Create the current normalized-data schema if it does not exist."""

    connection.executescript(_SCHEMA_SQL)


_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_metadata (
    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
    schema_version INTEGER NOT NULL CHECK (schema_version >= 1)
);

INSERT OR IGNORE INTO schema_metadata (
    singleton,
    schema_version
)
VALUES (1, 1);


CREATE TABLE IF NOT EXISTS companies (
    company_id TEXT PRIMARY KEY,
    legal_name TEXT NOT NULL,
    cik TEXT NOT NULL UNIQUE,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1))
);


CREATE TABLE IF NOT EXISTS company_alternate_names (
    company_id TEXT NOT NULL,
    name_order INTEGER NOT NULL
        CHECK (name_order >= 0),
    alternate_name TEXT NOT NULL,

    PRIMARY KEY (company_id, name_order),
    UNIQUE (company_id, alternate_name),

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
        ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS company_listings (
    listing_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    exchange TEXT NOT NULL,
    security_name TEXT,
    valid_from TEXT,
    valid_to TEXT,
    is_active INTEGER NOT NULL DEFAULT 1
        CHECK (is_active IN (0, 1)),

    CHECK (
        valid_from IS NULL
        OR valid_to IS NULL
        OR valid_from <= valid_to
    ),

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
);

CREATE INDEX IF NOT EXISTS idx_company_listings_company
    ON company_listings(company_id);

CREATE INDEX IF NOT EXISTS idx_company_listings_ticker_exchange
    ON company_listings(
        ticker COLLATE NOCASE,
        exchange COLLATE NOCASE
    );


CREATE TABLE IF NOT EXISTS evidence_sources (
    source_id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,
    title TEXT NOT NULL,
    publisher TEXT NOT NULL,
    retrieved_at TEXT NOT NULL,
    published_on TEXT,
    url TEXT,
    external_id TEXT,
    filing_form TEXT,
    raw_file_path TEXT,
    sha256 TEXT,
    language TEXT NOT NULL DEFAULT 'en'
);

CREATE INDEX IF NOT EXISTS idx_evidence_sources_external_id
    ON evidence_sources(external_id, source_type);

    
CREATE TABLE IF NOT EXISTS executives (
    executive_id TEXT PRIMARY KEY,
    full_name TEXT NOT NULL
); 

CREATE TABLE IF NOT EXISTS executive_alternate_names (
    executive_id TEXT NOT NULL,
    name_order INTEGER NOT NULL
        CHECK (name_order >= 0),
    alternate_name TEXT NOT NULL,

    PRIMARY KEY (executive_id, name_order),
    UNIQUE (executive_id, alternate_name),

    FOREIGN KEY (executive_id)
        REFERENCES executives(executive_id)
        ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS executive_citations (
    executive_id TEXT NOT NULL,
    citation_order INTEGER NOT NULL
        CHECK (citation_order >= 0),
    source_id TEXT NOT NULL,
    supporting_excerpt TEXT,
    location TEXT,

    PRIMARY KEY (executive_id, citation_order),

    FOREIGN KEY (executive_id)
        REFERENCES executives(executive_id)
        ON DELETE CASCADE,

    FOREIGN KEY (source_id)
        REFERENCES evidence_sources(source_id)
);


CREATE TABLE IF NOT EXISTS executive_roles (
    role_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    executive_id TEXT NOT NULL,
    role_type TEXT NOT NULL,
    reported_title TEXT NOT NULL,

    started_year INTEGER,
    started_month INTEGER,
    started_day INTEGER,

    ended_year INTEGER,
    ended_month INTEGER,
    ended_day INTEGER,

    appointment_announced_on TEXT,
    departure_announced_on TEXT,

    is_interim INTEGER NOT NULL DEFAULT 0
        CHECK (is_interim IN (0, 1)),

    CHECK (
        (
            started_year IS NULL
            AND started_month IS NULL
            AND started_day IS NULL
        )
        OR
        (
            started_year IS NOT NULL
            AND (
                started_month IS NULL
                OR started_month BETWEEN 1 AND 12
            )
            AND (
                started_day IS NULL
                OR (
                    started_month IS NOT NULL
                    AND started_day BETWEEN 1 AND 31
                )
            )
        )
    ),

    CHECK (
        (
            ended_year IS NULL
            AND ended_month IS NULL
            AND ended_day IS NULL
        )
        OR
        (
            ended_year IS NOT NULL
            AND (
                ended_month IS NULL
                OR ended_month BETWEEN 1 AND 12
            )
            AND (
                ended_day IS NULL
                OR (
                    ended_month IS NOT NULL
                    AND ended_day BETWEEN 1 AND 31
                )
            )
        )
    ),

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id),

    FOREIGN KEY (executive_id)
        REFERENCES executives(executive_id)
);

CREATE INDEX IF NOT EXISTS idx_executive_roles_executive
    ON executive_roles(executive_id);

CREATE INDEX IF NOT EXISTS idx_executive_roles_company_type
    ON executive_roles(company_id, role_type);


CREATE TABLE IF NOT EXISTS executive_role_citations (
    role_id TEXT NOT NULL,
    citation_order INTEGER NOT NULL
        CHECK (citation_order >= 0),
    source_id TEXT NOT NULL,
    supporting_excerpt TEXT,
    location TEXT,

    PRIMARY KEY (role_id, citation_order),

    FOREIGN KEY (role_id)
        REFERENCES executive_roles(role_id)
        ON DELETE CASCADE,

    FOREIGN KEY (source_id)
        REFERENCES evidence_sources(source_id)
);


CREATE TABLE IF NOT EXISTS career_positions (
    position_id TEXT PRIMARY KEY,
    executive_id TEXT NOT NULL,
    employer_name TEXT NOT NULL,
    reported_title TEXT NOT NULL,
    employer_company_id TEXT,

    started_year INTEGER,
    started_month INTEGER,
    started_day INTEGER,

    ended_year INTEGER,
    ended_month INTEGER,
    ended_day INTEGER,

    CHECK (
        (
            started_year IS NULL
            AND started_month IS NULL
            AND started_day IS NULL
        )
        OR
        (
            started_year IS NOT NULL
            AND (
                started_month IS NULL
                OR started_month BETWEEN 1 AND 12
            )
            AND (
                started_day IS NULL
                OR (
                    started_month IS NOT NULL
                    AND started_day BETWEEN 1 AND 31
                )
            )
        )
    ),

    CHECK (
        (
            ended_year IS NULL
            AND ended_month IS NULL
            AND ended_day IS NULL
        )
        OR
        (
            ended_year IS NOT NULL
            AND (
                ended_month IS NULL
                OR ended_month BETWEEN 1 AND 12
            )
            AND (
                ended_day IS NULL
                OR (
                    ended_month IS NOT NULL
                    AND ended_day BETWEEN 1 AND 31
                )
            )
        )
    ),

    FOREIGN KEY (executive_id)
        REFERENCES executives(executive_id),

    FOREIGN KEY (employer_company_id)
        REFERENCES companies(company_id)
);

CREATE INDEX IF NOT EXISTS idx_career_positions_executive
    ON career_positions(executive_id);

CREATE INDEX IF NOT EXISTS idx_career_positions_employer
    ON career_positions(employer_company_id);


CREATE TABLE IF NOT EXISTS career_position_citations (
    position_id TEXT NOT NULL,
    citation_order INTEGER NOT NULL
        CHECK (citation_order >= 0),
    source_id TEXT NOT NULL,
    supporting_excerpt TEXT,
    location TEXT,

    PRIMARY KEY (position_id, citation_order),

    FOREIGN KEY (position_id)
        REFERENCES career_positions(position_id)
        ON DELETE CASCADE,

    FOREIGN KEY (source_id)
        REFERENCES evidence_sources(source_id)
);


CREATE TABLE IF NOT EXISTS company_events (
    event_id TEXT PRIMARY KEY,
    company_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    announced_on TEXT,

    occurred_year INTEGER,
    occurred_month INTEGER,
    occurred_day INTEGER,

    CHECK (
        announced_on IS NOT NULL
        OR occurred_year IS NOT NULL
    ),

    CHECK (
        (
            occurred_year IS NULL
            AND occurred_month IS NULL
            AND occurred_day IS NULL
        )
        OR
        (
            occurred_year IS NOT NULL
            AND (
                occurred_month is NULL
                OR occurred_month BETWEEN 1 AND 12
            )
            AND (
                occurred_day IS NULL
                OR (
                    occurred_month IS NOT NULL
                    AND occurred_day BETWEEN 1 AND 31
                )
            )
        )
    ),

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id)
);

CREATE INDEX IF NOT EXISTS idx_company_events_company_type
    ON company_events(company_id, event_type);

    
CREATE TABLE IF NOT EXISTS company_event_citations (
    event_id TEXT NOT NULL,
    citation_order INTEGER NOT NULL
        CHECK (citation_order >= 0),
    source_id TEXT NOT NULL,
    supporting_excerpt TEXT,
    location TEXT,

    PRIMARY KEY (event_id, citation_order),

    FOREIGN KEY (event_id)
        REFERENCES company_events(event_id)
        ON DELETE CASCADE,

    FOREIGN KEY (source_id)
        REFERENCES evidence_sources(source_id)
);


CREATE TABLE IF NOT EXISTS company_event_executives (
    event_id TEXT NOT NULL,
    executive_order INTEGER NOT NULL
        CHECK (executive_order >= 0),
    executive_id TEXT NOT NULL,

    PRIMARY KEY (event_id, executive_order),
    UNIQUE (event_id, executive_id),

    FOREIGN KEY (event_id)
        REFERENCES company_events(event_id)
        ON DELETE CASCADE,

    FOREIGN KEY (executive_id)
        REFERENCES executives(executive_id)
);

CREATE INDEX IF NOT EXISTS idx_company_event_executives_executive
    ON company_event_executives(executive_id);


CREATE TABLE IF NOT EXISTS company_event_roles (
    event_id TEXT NOT NULL,
    role_order INTEGER NOT NULL
        CHECK (role_order >= 0),
    role_id TEXT NOT NULL,

    PRIMARY KEY (event_id, role_order),
    UNIQUE (event_id, role_id),

    FOREIGN KEY (event_id)
        REFERENCES company_events(event_id)
        ON DELETE CASCADE,

    FOREIGN KEY (role_id)
        REFERENCES executive_roles(role_id)
);

CREATE INDEX IF NOT EXISTS idx_company_event_roles_role
    ON company_event_roles(role_id);


CREATE TABLE IF NOT EXISTS candidate_evidence (
    candidate_id TEXT PRIMARY KEY, 

    subject_type TEXT NOT NULL,
    subject_name TEXT NOT NULL,
    claim_type TEXT NOT NULL,

    extracted_value_type TEXT NOT NULL,
    extracted_value_json TEXT NOT NULL,

    source_id TEXT NOT NULL,
    citation_supporting_excerpt TEXT,
    citation_location TEXT,

    extraction_method TEXT NOT NULL,
    extracted_at TEXT NOT NULL,

    verification_status TEXT NOT NULL,
    extraction_confidence REAL,
    rejection_reason TEXT,

    company_id TEXT,
    executive_id TEXT,

    CHECK (
        extraction_confidence IS NULL
        OR extraction_confidence BETWEEN 0.0 AND 1.0
    ),

    CHECK (
        (
            verification_status = 'rejected'
            AND rejection_reason IS NOT NULL
            AND length(trim(rejection_reason)) > 0
        )
        OR
        (
            verification_status <> 'rejected'
            AND rejection_reason IS NULL
        )
    ),

    FOREIGN KEY (source_id)
        REFERENCES evidence_sources(source_id),

    FOREIGN KEY (company_id)
        REFERENCES companies(company_id),

    FOREIGN KEY (executive_id)
        REFERENCES executives(executive_id)
);

CREATE INDEX IF NOT EXISTS idx_candidate_evidence_company_status
    ON candidate_evidence(company_id, verification_status);

CREATE INDEX IF NOT EXISTS idx_candidate_evidence_executive_status
    ON candidate_evidence(executive_id, verification_status);

CREATE INDEX IF NOT EXISTS idx_candidate_evidence_status
    ON candidate_evidence(verification_status);
"""
