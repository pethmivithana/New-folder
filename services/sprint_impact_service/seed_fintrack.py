#!/usr/bin/env python3
"""
seed_fintrack.py
────────────────────────────────────────────────────────────────────────────────
Seed script for FinTrack Pro — a financial data intelligence platform.

Project: FinTrack Pro
Team size: 5 developers (max_assignees = 6 in space, 5 assigned per sprint)
Duration per sprint: 2 weeks (10 working days)
Focus hours per dev per day: 6h
Total raw capacity per sprint: 5 devs × 10 days × 6h = 300h
Average hours per SP: 6h → raw SP capacity = 50 SP
Stability buffer: 20% → planned at 80% = 40 SP per sprint

Sprint history:
  Sprint 1 — Completed — 40 SP planned, 38 SP done (2 SP unfinished, carried to backlog)
  Sprint 2 — Completed — 40 SP planned, 40 SP done (full completion)
  Sprint 3 — Completed — 42 SP planned (slight overload), 34 SP done (8 SP unfinished)
  Sprint 4 — Completed — 38 SP planned, 38 SP done (full completion)
  Sprint 5 — Completed — 40 SP planned, 35 SP done (5 SP unfinished, carried to backlog)
  Sprint 6 — Active    — 40 SP planned, currently day 5 of 14, ~20 SP done so far

Unresolved items from completed sprints sit in backlog as unassigned items.

Usage:
  cd services/sprint_impact_service
  python seed_fintrack.py

  Or with explicit MongoDB URI:
  MONGODB_URI=mongodb://localhost:27017 python seed_fintrack.py
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "agile-tool"

NOW = datetime.utcnow()


def days_ago(n):
    return NOW - timedelta(days=n)


def days_from_now(n):
    return NOW + timedelta(days=n)


def fmt(dt):
    """Format datetime as YYYY-MM-DD string for storage."""
    return dt.strftime("%Y-%m-%d")


# ══════════════════════════════════════════════════════════════════════════════
# SPACE
# ══════════════════════════════════════════════════════════════════════════════

SPACE = {
    "name": "FinTrack Pro — Financial Intelligence Platform",
    "description": (
        "FinTrack Pro is a B2B SaaS platform that provides real-time financial "
        "data aggregation, risk scoring, and regulatory compliance reporting for "
        "mid-market lending institutions. The platform ingests transaction streams "
        "from multiple banking APIs, normalises data across schemas, and surfaces "
        "risk dashboards and automated Basel III compliance reports to credit "
        "analysts and compliance officers."
    ),
    "max_assignees": 6,
    "focus_hours_per_day": 6.0,
    "risk_appetite": "Standard",
    "created_at": days_ago(90),
    "updated_at": days_ago(90),
}


# ══════════════════════════════════════════════════════════════════════════════
# SPRINTS — 5 completed + 1 active
# Each sprint: start_date, end_date, assignee_count, planned SP, actual done SP
# ══════════════════════════════════════════════════════════════════════════════

# Sprint 1: days 84–70 ago
# Sprint 2: days 70–56 ago
# Sprint 3: days 56–42 ago
# Sprint 4: days 42–28 ago
# Sprint 5: days 28–14 ago
# Sprint 6: days 9 ago → days 5 from now  (active, day 5 of 14)

SPRINTS_META = [
    {
        "name": "Sprint 1 — Data Ingestion Foundation",
        "goal": (
            "Establish the core data ingestion pipeline capable of connecting to three "
            "banking API providers (Plaid, Yodlee, MX), normalising raw transaction "
            "records into the FinTrack canonical schema, and persisting them to the "
            "time-series datastore with idempotency guarantees."
        ),
        "duration_type": "2 Weeks",
        "start_date": fmt(days_ago(84)),
        "end_date":   fmt(days_ago(70)),
        "status": "Completed",
        "assignee_count": 5,
        "assignees": [1, 2, 3, 4, 5],
    },
    {
        "name": "Sprint 2 — Risk Scoring Engine v1",
        "goal": (
            "Implement the first version of the real-time risk scoring engine that "
            "calculates a composite credit risk score per account using transaction "
            "velocity, balance volatility, and overdraft frequency signals. Expose "
            "the score via a low-latency REST endpoint with p99 < 200ms."
        ),
        "duration_type": "2 Weeks",
        "start_date": fmt(days_ago(70)),
        "end_date":   fmt(days_ago(56)),
        "status": "Completed",
        "assignee_count": 5,
        "assignees": [1, 2, 3, 4, 5],
    },
    {
        "name": "Sprint 3 — Compliance Reporting Module",
        "goal": (
            "Build the Basel III regulatory reporting module that aggregates daily "
            "position data, applies the standardised approach risk weight calculations, "
            "and generates downloadable PDF and XBRL reports on a configurable schedule. "
            "Reports must pass validation against the EBA taxonomy v3.2."
        ),
        "duration_type": "2 Weeks",
        "start_date": fmt(days_ago(56)),
        "end_date":   fmt(days_ago(42)),
        "status": "Completed",
        "assignee_count": 5,
        "assignees": [1, 2, 3, 4, 5],
    },
    {
        "name": "Sprint 4 — Analyst Dashboard & Alerting",
        "goal": (
            "Deliver the credit analyst dashboard with real-time risk score feeds, "
            "account drill-down views, trend charts over configurable time windows, "
            "and a rule-based alerting system that sends email and Slack notifications "
            "when risk scores breach user-defined thresholds."
        ),
        "duration_type": "2 Weeks",
        "start_date": fmt(days_ago(42)),
        "end_date":   fmt(days_ago(28)),
        "status": "Completed",
        "assignee_count": 5,
        "assignees": [1, 2, 3, 4, 5],
    },
    {
        "name": "Sprint 5 — Multi-Tenant Architecture & Audit Logging",
        "goal": (
            "Migrate the single-tenant data layer to a full multi-tenant architecture "
            "using schema-per-tenant isolation in PostgreSQL, implement tenant "
            "onboarding and offboarding workflows, and add a tamper-evident audit log "
            "for all data access and report generation events to satisfy SOC 2 Type II "
            "evidence requirements."
        ),
        "duration_type": "2 Weeks",
        "start_date": fmt(days_ago(28)),
        "end_date":   fmt(days_ago(14)),
        "status": "Completed",
        "assignee_count": 5,
        "assignees": [1, 2, 3, 4, 5],
    },
    {
        "name": "Sprint 6 — Advanced Risk Models & API Gateway",
        "goal": (
            "Integrate machine learning-based anomaly detection for fraud signal "
            "identification in transaction streams, implement a unified API gateway "
            "with OAuth 2.0 client credentials flow, rate limiting per tenant, and "
            "a developer portal with auto-generated OpenAPI documentation."
        ),
        "duration_type": "Custom",
        "start_date": fmt(days_ago(5)),
        "end_date":   fmt(days_from_now(9)),
        "status": "Active",
        "assignee_count": 5,
        "assignees": [1, 2, 3, 4, 5],
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# BACKLOG ITEMS PER SPRINT
#
# Capacity rule:
#   Planned SP per sprint ≈ 40 (80% of 50 SP raw capacity)
#   Done SP:
#     Sprint 1: 38/40 (2 SP not done — 1 item carried)
#     Sprint 2: 40/40 (100% — all done)
#     Sprint 3: 34/42 (slight overload, 8 SP not done — 2 items carried)
#     Sprint 4: 38/38 (100% — all done)
#     Sprint 5: 35/40 (5 SP not done — 1 item carried)
#     Sprint 6: Active — 5 items Done (20 SP), rest in various states
#
# story_points range: 3–13 (enforced by model Field ge=3 le=15)
# ══════════════════════════════════════════════════════════════════════════════

ITEMS_BY_SPRINT_INDEX = {

    # ── Sprint 1: Data Ingestion Foundation ─────────────────────────────────
    # Planned: 40 SP | Done: 38 SP | Carried: 1 item (3 SP)
    0: [
        {
            "title": "Implement Plaid API OAuth 2.0 connection and token refresh",
            "description": (
                "Integrate the Plaid Link SDK for OAuth 2.0 authorisation flow. "
                "Implement access token acquisition, refresh token rotation, and secure "
                "storage of credentials in AWS Secrets Manager. Handle Plaid error codes "
                "ITEM_LOGIN_REQUIRED and INVALID_ACCESS_TOKEN with automatic re-auth prompts. "
                "Scope: /transactions/get, /accounts/get, /identity/get endpoints only."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Implement Yodlee FastLink 4.0 connection flow",
            "description": (
                "Integrate Yodlee FastLink 4.0 widget for account aggregation. Configure "
                "ContentServiceId for UK and EU banking institutions. Implement webhook "
                "listener for DATA_UPDATES events to trigger incremental sync. Store "
                "cobSessionToken and userSessionToken securely with 30-minute TTL refresh."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Build canonical transaction schema and normalisation layer",
            "description": (
                "Define the FinTrack canonical transaction schema using Avro with fields: "
                "transaction_id, account_id, tenant_id, amount_minor_units, currency_iso4217, "
                "merchant_category_code, posted_date, value_date, description_raw, "
                "description_clean, source_provider, ingest_timestamp. "
                "Implement normalisation functions for Plaid and Yodlee response shapes. "
                "Register schema in Confluent Schema Registry with compatibility mode FORWARD."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Set up TimescaleDB hypertable for time-series transaction storage",
            "description": (
                "Create transactions hypertable partitioned by posted_date with chunk interval "
                "of 7 days. Add composite index on (tenant_id, account_id, posted_date DESC). "
                "Configure data retention policy to compress chunks older than 90 days. "
                "Implement idempotent upsert using ON CONFLICT (transaction_id, tenant_id) DO NOTHING "
                "to prevent duplicates during re-sync."
            ),
            "type": "Task", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Write integration tests for Plaid and Yodlee ingestion pipeline",
            "description": (
                "Create pytest integration test suite using Plaid sandbox environment and "
                "Yodlee FastLink test credentials. Test happy path transaction sync, "
                "re-authentication flow, network timeout handling (mock with responses library), "
                "and schema validation for edge cases: negative amounts, multi-currency, "
                "missing merchant codes. Target: 85% branch coverage on ingestion module."
            ),
            "type": "Task", "priority": "Medium", "story_points": 5, "status": "Done",
        },
        {
            "title": "Add MX Technologies API connection (Connect widget)",
            "description": (
                "Integrate MX Connect widget for account linking. Implement /users, /members, "
                "and /transactions endpoints. Map MX transaction type codes to FinTrack "
                "canonical category codes. This was lower priority as Plaid and Yodlee cover "
                "90% of the target bank coverage — carry forward if time runs short."
            ),
            "type": "Story", "priority": "Low", "story_points": 3, "status": "To Do",
            # CARRIED: this item was NOT done in Sprint 1 — will be in backlog
        },
    ],

    # ── Sprint 2: Risk Scoring Engine v1 ─────────────────────────────────────
    # Planned: 40 SP | Done: 40 SP | Carried: 0
    1: [
        {
            "title": "Design and implement transaction velocity feature extractor",
            "description": (
                "Build a feature extraction service that computes rolling window statistics "
                "over transaction streams: 24h, 7d, and 30d transaction count and volume per "
                "account. Use Redis sorted sets with ZADD/ZRANGEBYSCORE for O(log N) window "
                "queries. Features: tx_count_24h, tx_volume_24h, tx_count_7d, tx_volume_7d, "
                "tx_count_30d, tx_volume_30d, weekend_tx_ratio, night_tx_ratio."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Implement balance volatility and overdraft frequency signals",
            "description": (
                "Calculate daily end-of-day balance from transaction stream using running sum. "
                "Compute balance_std_dev_30d, balance_min_30d, overdraft_count_30d (days where "
                "EOD balance < 0), and consecutive_negative_days. Store computed signals in "
                "PostgreSQL risk_signals table with (account_id, computed_date) primary key. "
                "Backfill 90 days of historical signals on account onboarding."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Build composite risk score calculator with configurable weights",
            "description": (
                "Implement RiskScoreCalculator class that combines velocity, volatility, and "
                "overdraft signals into a single 0–1000 composite score using weighted sum. "
                "Weights must be configurable per tenant via JSON config in PostgreSQL. "
                "Score bands: 0–299 High Risk, 300–599 Medium Risk, 600–799 Low Risk, "
                "800–1000 Very Low Risk. Emit risk_score_computed event to Kafka topic."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Expose risk score REST endpoint with p99 < 200ms SLA",
            "description": (
                "Create GET /v1/accounts/{account_id}/risk-score endpoint on FastAPI. "
                "Response includes: current_score, score_band, component_scores, last_updated, "
                "signal_freshness_seconds. Add Redis caching with 60-second TTL. "
                "Add Prometheus histogram metric fintrack_risk_score_latency_seconds. "
                "Load test with Locust: 500 concurrent users, verify p99 < 200ms."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Set up Prometheus metrics and Grafana dashboard for risk engine",
            "description": (
                "Instrument risk scoring service with Prometheus client: score computation "
                "duration histogram, cache hit/miss counter, Kafka consumer lag gauge, "
                "error rate counter by error type. Create Grafana dashboard with panels for "
                "p50/p95/p99 latency, throughput (scores/minute), cache hit rate, and "
                "consumer lag with 5-minute alert threshold."
            ),
            "type": "Task", "priority": "Medium", "story_points": 8, "status": "Done",
        },
    ],

    # ── Sprint 3: Compliance Reporting Module ─────────────────────────────────
    # Planned: 42 SP (slight overload) | Done: 34 SP | Carried: 2 items (8 SP)
    2: [
        {
            "title": "Implement Basel III standardised approach risk weight calculator",
            "description": (
                "Build RiskWeightCalculator applying CRR Article 114–134 standardised approach "
                "exposure categories. Map each transaction counterparty to exposure class using "
                "LEI lookup against GLEIF API. Apply risk weights: sovereign 0%, institution "
                "20%, corporate 100%, retail 75%, residential mortgage 35%. "
                "Output: exposure_value, risk_weight, risk_weighted_asset per position."
            ),
            "type": "Story", "priority": "High", "story_points": 13, "status": "Done",
        },
        {
            "title": "Build daily position aggregation job using Apache Airflow",
            "description": (
                "Create Airflow DAG daily_position_aggregation that runs at 23:55 UTC. "
                "Tasks: extract_eod_balances → compute_exposure_values → calculate_risk_weights "
                "→ aggregate_capital_ratios → persist_regulatory_snapshot. "
                "Add SLA miss alert (>15 min runtime) and data quality checks: "
                "zero-balance accounts, missing LEI codes, currency mismatches."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Generate Basel III PDF report with ReportLab",
            "description": (
                "Implement PDFReportGenerator using ReportLab platypus. Report sections: "
                "executive summary table, capital ratios (CET1, Tier 1, Total Capital), "
                "exposure breakdown by asset class, top 20 counterparties by RWA, "
                "reconciliation to prior period. Apply tenant white-labelling: logo, "
                "colour scheme, and registered entity name from tenant config."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Implement XBRL report generation compliant with EBA taxonomy v3.2",
            "description": (
                "Generate XBRL instance documents using python-xbrl library. Map FinTrack "
                "data model to FINREP/COREP EBA taxonomy v3.2 concepts. Validate output "
                "against XBRL International validator and EBA XBRL Filing Rules v6.2. "
                "Known complexity: handling period context for flow vs stock items. "
                "Requires deep taxonomy expertise — descope if timeline is tight."
            ),
            "type": "Story", "priority": "Medium", "story_points": 5, "status": "To Do",
            # CARRIED: XBRL specialist task, not completed in sprint 3
        },
        {
            "title": "Add configurable report scheduling via cron expression UI",
            "description": (
                "Build report scheduling configuration: allow compliance officers to set "
                "custom cron expressions for report generation. Store in tenant_report_schedules "
                "table. Trigger via Celery Beat. Send email with PDF attachment and SFTP "
                "push to regulatory sandbox on schedule. Add retry with exponential backoff."
            ),
            "type": "Task", "priority": "Medium", "story_points": 3, "status": "To Do",
            # CARRIED: deprioritised due to XBRL complexity consuming bandwidth
        },
    ],

    # ── Sprint 4: Analyst Dashboard & Alerting ────────────────────────────────
    # Planned: 38 SP | Done: 38 SP | Carried: 0
    3: [
        {
            "title": "Build React risk dashboard with real-time WebSocket feed",
            "description": (
                "Create analyst dashboard SPA using React 18 + Vite. Main view: account "
                "risk heatmap (colour-coded by risk band), top 50 highest-risk accounts "
                "table sortable by score/band/change. Risk score updates arrive via "
                "WebSocket connection to /ws/risk-feed. Implement reconnection with "
                "exponential backoff. Use Recharts for trend visualisation."
            ),
            "type": "Story", "priority": "High", "story_points": 13, "status": "Done",
        },
        {
            "title": "Implement account drill-down view with transaction history",
            "description": (
                "Account detail page: risk score timeline chart (30/90/180 day), "
                "component score breakdown radar chart, transaction feed with search and "
                "category filter, overdraft event markers on timeline. "
                "Implement virtual scroll for transaction list (accounts may have 10k+ rows). "
                "Add export to CSV for compliance investigation workflow."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Implement rule-based alerting engine with threshold configuration",
            "description": (
                "Build AlertEngine that evaluates risk score events against user-defined "
                "threshold rules: score_below, score_above, score_change_pct, "
                "consecutive_high_risk_days. Support AND/OR logic between conditions. "
                "Store rules in alert_rules table with tenant_id, rule_config JSONB, "
                "is_active, created_by, notification_channels."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Integrate SendGrid email alerts and Slack webhook notifications",
            "description": (
                "Implement NotificationDispatcher with SendGrid and Slack webhook adapters. "
                "Email: HTML template with account name, current score, threshold breached, "
                "trend chart image (base64 embedded). Slack: Block Kit message with "
                "risk score badge colour, account link, and acknowledge button. "
                "Add rate limiting: max 10 alerts per account per hour to prevent spam."
            ),
            "type": "Task", "priority": "Medium", "story_points": 5, "status": "Done",
        },
        {
            "title": "Add end-to-end Playwright tests for dashboard alert workflow",
            "description": (
                "Write Playwright tests covering: login → set alert threshold → trigger "
                "mock risk score change → verify email received (Mailhog) → verify Slack "
                "message (mock Slack server) → verify alert appears in alert history table. "
                "Run tests in CI on every PR against staging environment."
            ),
            "type": "Task", "priority": "Medium", "story_points": 4, "status": "Done",
        },
    ],

    # ── Sprint 5: Multi-Tenant Architecture & Audit Logging ──────────────────
    # Planned: 40 SP | Done: 35 SP | Carried: 1 item (5 SP)
    4: [
        {
            "title": "Migrate database to schema-per-tenant isolation model",
            "description": (
                "Implement schema-per-tenant isolation in PostgreSQL: create tenant-specific "
                "schemas (tenant_{uuid}) containing transactions, accounts, risk_signals, "
                "alert_rules tables. Update SQLAlchemy connection pool to set search_path "
                "per request using middleware. Write Alembic migration that creates schemas "
                "for existing tenants and migrates data with zero downtime using blue-green "
                "table swap. Validate row counts pre/post migration."
            ),
            "type": "Story", "priority": "High", "story_points": 13, "status": "Done",
        },
        {
            "title": "Implement tenant onboarding workflow and provisioning API",
            "description": (
                "Build TenantProvisioningService: create PostgreSQL schema, seed default "
                "risk weight config, create Kafka topics (tenant.{id}.transactions, "
                "tenant.{id}.risk-events), provision Redis keyspace prefix, create IAM "
                "role and S3 bucket for report storage. Expose POST /v1/admin/tenants "
                "endpoint authenticated with admin service token. Emit tenant_provisioned "
                "event for downstream service configuration."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Build tamper-evident audit log for SOC 2 Type II compliance",
            "description": (
                "Implement append-only audit_log table with columns: event_id UUID, "
                "tenant_id, user_id, action_type ENUM, resource_type, resource_id, "
                "request_ip, user_agent, payload_hash SHA-256, previous_hash, "
                "created_at. Chain entries using previous_hash to detect tampering. "
                "Log all: data access, report generation, config changes, login events. "
                "Expose GET /v1/audit-log with date range and actor filters."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Implement tenant data offboarding and GDPR erasure workflow",
            "description": (
                "Build TenantOffboardingService: soft-delete tenant record, anonymise PII "
                "fields (account holder names, email addresses) in tenant schema using UPDATE "
                "with SHA-256 hash substitution, drop Kafka topics after 7-day retention "
                "window, delete S3 bucket contents, revoke IAM roles. Generate GDPR "
                "erasure confirmation report for data controller records."
            ),
            "type": "Story", "priority": "Medium", "story_points": 6, "status": "Done",
        },
        {
            "title": "Add row-level security policies to prevent cross-tenant data leaks",
            "description": (
                "Implement PostgreSQL row-level security (RLS) on all shared tables as "
                "defence-in-depth. Policy: USING (tenant_id = current_setting('app.tenant_id')). "
                "Enable RLS on: tenants, audit_log, global_report_templates tables. "
                "Write pen-test style integration tests that attempt cross-tenant queries "
                "with different search_path and verify zero rows returned."
            ),
            "type": "Task", "priority": "High", "story_points": 5, "status": "To Do",
            # CARRIED: discovered late in sprint that RLS conflicts with Alembic migrations
        },
    ],

    # ── Sprint 6: Advanced Risk Models & API Gateway (ACTIVE) ─────────────────
    # Planned: 40 SP | Day 5 of 14 | Done: ~20 SP | Rest in progress/todo
    5: [
        {
            "title": "Integrate Isolation Forest model for transaction anomaly detection",
            "description": (
                "Train scikit-learn IsolationForest on 6 months of historical transaction "
                "data using features: amount_zscore, time_since_last_tx, merchant_category_frequency, "
                "geo_distance_from_usual (if available), amount_vs_account_median. "
                "Serve model via FastAPI /v1/transactions/{tx_id}/anomaly-score endpoint. "
                "Model refresh pipeline: weekly retraining job in Airflow using rolling 6-month "
                "window. Store model artefacts in MLflow registry with staging/production stages."
            ),
            "type": "Story", "priority": "High", "story_points": 13, "status": "Done",
        },
        {
            "title": "Build fraud signal aggregator combining anomaly scores with rule-based signals",
            "description": (
                "Implement FraudSignalAggregator that combines: IsolationForest anomaly_score, "
                "velocity_spike_flag (tx amount > 3σ above 30d mean), new_merchant_flag "
                "(first transaction to this MCC in 90 days), round_amount_flag (amounts "
                "exactly divisible by 50 or 100), rapid_succession_flag (>3 transactions "
                "within 10 minutes). Output composite fraud_risk_score 0–100 and "
                "triggered_signals list for analyst review."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Implement API Gateway with Kong and OAuth 2.0 client credentials",
            "description": (
                "Deploy Kong Gateway 3.4 as the entry point for all external API traffic. "
                "Configure OAuth 2.0 client credentials plugin (RFC 6749 §4.4) with "
                "JWT access tokens signed with RS256. Implement per-tenant rate limiting: "
                "1000 req/min standard, 5000 req/min enterprise tier. Add request logging "
                "plugin forwarding to Elasticsearch. Configure health check routes and "
                "circuit breaker with 5-second timeout and 50% error rate threshold."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "In Progress",
        },
        {
            "title": "Build developer portal with auto-generated OpenAPI documentation",
            "description": (
                "Create developer portal using Docusaurus 3 with Redoc for OpenAPI rendering. "
                "Auto-generate OpenAPI spec from FastAPI /openapi.json on each deployment. "
                "Portal sections: getting started guide, authentication walkthrough, "
                "endpoint reference, code examples in Python/Node.js/curl, changelog. "
                "Deploy portal to GitHub Pages with custom domain api-docs.fintrack.io."
            ),
            "type": "Story", "priority": "Medium", "story_points": 5, "status": "In Progress",
        },
        {
            "title": "Add JWT token introspection endpoint and token revocation list",
            "description": (
                "Implement RFC 7662 token introspection endpoint POST /v1/auth/introspect "
                "for resource servers to validate tokens without shared secret. "
                "Add token revocation list (TRL) using Redis SET with TTL matching token "
                "expiry. Kong gateway checks TRL on each request via pre-auth plugin. "
                "Expose POST /v1/auth/revoke endpoint for explicit token invalidation."
            ),
            "type": "Task", "priority": "High", "story_points": 3, "status": "To Do",
        },
        {
            "title": "Write load tests for API Gateway tier using k6",
            "description": (
                "Create k6 load test scenarios: ramp-up to 1000 concurrent API clients "
                "over 5 minutes, sustained load for 10 minutes, ramp-down. Test endpoints: "
                "risk score GET (read-heavy), transaction ingest POST (write-heavy), "
                "report download GET (large payload). Assert: p99 < 500ms, error rate < 0.1%, "
                "no memory leaks in Kong (monitor via Admin API metrics endpoint)."
            ),
            "type": "Task", "priority": "Medium", "story_points": 3, "status": "To Do",
        },
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# BACKLOG ITEMS (unassigned — orphaned from sprint overruns + new items)
# ══════════════════════════════════════════════════════════════════════════════
# These are items that were never assigned to a sprint or were carried from
# completed sprints. They will appear in the Backlog section of the dashboard.

UNASSIGNED_BACKLOG = [
    # Carried from Sprint 1
    {
        "title": "Add MX Technologies API connection (Connect widget)",
        "description": (
            "Integrate MX Connect widget for account linking. Implement /users, /members, "
            "and /transactions endpoints. Map MX transaction type codes to FinTrack "
            "canonical category codes. MX covers ~15% of community bank connections "
            "not available in Plaid/Yodlee. Required to reach 95% UK bank coverage target."
        ),
        "type": "Story", "priority": "Medium", "story_points": 3,
    },
    # Carried from Sprint 3
    {
        "title": "Implement XBRL report generation compliant with EBA taxonomy v3.2",
        "description": (
            "Generate XBRL instance documents using python-xbrl library. Map FinTrack "
            "data model to FINREP/COREP EBA taxonomy v3.2 concepts. Validate output "
            "against XBRL International validator and EBA XBRL Filing Rules v6.2. "
            "This is a hard regulatory requirement for EU-licensed clients — blocks "
            "three enterprise deals currently in sales pipeline."
        ),
        "type": "Story", "priority": "High", "story_points": 5,
    },
    {
        "title": "Add configurable report scheduling via cron expression UI",
        "description": (
            "Allow compliance officers to configure report generation schedules using "
            "cron expressions (e.g. '0 23 * * 1-5' for weekday end-of-day). Store in "
            "tenant_report_schedules. Trigger via Celery Beat. Send PDF via email and "
            "SFTP push to regulatory submission sandbox on schedule."
        ),
        "type": "Task", "priority": "Medium", "story_points": 3,
    },
    # Carried from Sprint 5
    {
        "title": "Add row-level security policies to prevent cross-tenant data leaks",
        "description": (
            "Implement PostgreSQL RLS on all shared tables as defence-in-depth. "
            "Policy: USING (tenant_id = current_setting('app.tenant_id')). "
            "Enable on: tenants, audit_log, global_report_templates. "
            "Required for SOC 2 Type II penetration test scheduled in 3 weeks — "
            "this is on the critical path for the compliance certification."
        ),
        "type": "Task", "priority": "High", "story_points": 5,
    },
    # New items not yet scheduled
    {
        "title": "Implement GDPR data subject access request (DSAR) fulfilment workflow",
        "description": (
            "Build DSAR portal allowing data subjects to request export of all personal "
            "data held by FinTrack. Workflow: identity verification → cross-schema data "
            "extraction → PII aggregation → encrypted ZIP delivery to verified email "
            "within 30-day statutory deadline. Required for EU GDPR Article 15 compliance."
        ),
        "type": "Story", "priority": "High", "story_points": 8,
    },
    {
        "title": "Add support for Open Banking UK PSD2 consent re-authentication",
        "description": (
            "UK Open Banking regulations require re-authentication every 90 days. "
            "Implement consent expiry tracking: store consent_expiry_date per connection, "
            "send email/in-app reminder at T-14, T-7, T-1 days. Handle expired consent "
            "gracefully — mark accounts as consent_expired, pause data sync, "
            "resume automatically after user re-authenticates via FCA-approved ASPSP flow."
        ),
        "type": "Story", "priority": "High", "story_points": 8,
    },
    {
        "title": "Build transaction categorisation ML model using merchant name and MCC",
        "description": (
            "Train a multi-class classifier (FastText or DistilBERT fine-tuned) to "
            "assign FinTrack spending categories to transactions using raw description "
            "and MCC code as input. Categories: groceries, utilities, rent, salary, "
            "entertainment, travel, healthcare, investment. Training data: 200k labelled "
            "transactions from synthetic dataset. Accuracy target: 92% on held-out test set."
        ),
        "type": "Story", "priority": "Medium", "story_points": 13,
    },
    {
        "title": "Implement credit facility utilisation tracking and covenant monitoring",
        "description": (
            "For lending clients: track revolving credit facility drawdowns and repayments, "
            "calculate utilisation rate = outstanding_balance / facility_limit. Alert when "
            "utilisation breaches 75% and 90% thresholds. Monitor financial covenants "
            "(interest coverage ratio, debt-to-EBITDA) using connected accounting system data. "
            "Generate covenant breach notification with 5-day grace period tracking."
        ),
        "type": "Story", "priority": "Medium", "story_points": 8,
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN SEED FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

async def seed():
    print("\n" + "=" * 70)
    print("FinTrack Pro — Seed Data Population")
    print("=" * 70)
    print(f"MongoDB URI : {MONGODB_URI}")
    print(f"Database    : {DATABASE_NAME}")
    print(f"Seed time   : {NOW.strftime('%Y-%m-%d %H:%M UTC')}")
    print()

    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]

    # ── Connectivity check ────────────────────────────────────────────────────
    try:
        await client.admin.command("ping")
        print("✓ Connected to MongoDB")
    except Exception as e:
        print(f"✗ Cannot connect to MongoDB: {e}")
        print("  Make sure MongoDB is running and MONGODB_URI is correct.")
        sys.exit(1)

    # ── Clear existing data ───────────────────────────────────────────────────
    print("\n[1/5] Clearing existing collections...")
    for col in ["spaces", "sprints", "backlog_items", "recommendation_logs"]:
        result = await db[col].delete_many({})
        print(f"  Cleared {col}: {result.deleted_count} documents removed")

    # ── Create space ──────────────────────────────────────────────────────────
    print("\n[2/5] Creating project space...")
    space_doc = {**SPACE, "_id": ObjectId()}
    await db.spaces.insert_one(space_doc)
    space_id_str = str(space_doc["_id"])
    print(f"  ✓ Space: \"{SPACE['name']}\"")
    print(f"    ID: {space_id_str}")
    print(f"    max_assignees: {SPACE['max_assignees']} | focus_hours: {SPACE['focus_hours_per_day']}h/dev/day")

    # ── Create sprints and their items ────────────────────────────────────────
    print("\n[3/5] Creating sprints and backlog items...")
    sprint_ids = []
    sprint_stats = []

    for i, sprint_meta in enumerate(SPRINTS_META):
        sprint_doc = {
            "_id":            ObjectId(),
            "name":           sprint_meta["name"],
            "goal":           sprint_meta["goal"],
            "duration_type":  sprint_meta["duration_type"],
            "start_date":     sprint_meta["start_date"],
            "end_date":       sprint_meta["end_date"],
            "space_id":       space_id_str,
            "status":         sprint_meta["status"],
            "assignees":      sprint_meta["assignees"],
            "assignee_count": sprint_meta["assignee_count"],
            "created_at":     NOW - timedelta(days=85 - i * 14),
            "updated_at":     NOW - timedelta(days=70 - i * 14) if sprint_meta["status"] == "Completed" else NOW,
        }
        await db.sprints.insert_one(sprint_doc)
        sprint_id_str = str(sprint_doc["_id"])
        sprint_ids.append(sprint_id_str)

        # Insert items for this sprint
        items = ITEMS_BY_SPRINT_INDEX[i]
        done_sp = 0
        total_sp = 0
        item_count = 0

        for item in items:
            item_status = item["status"]

            # For completed sprints: items marked "To Do" in the definition
            # are the ones that DIDN'T finish. They get stored with their
            # original status so the sprint shows partial completion.
            # (The sprint is Completed even though some items weren't done.)

            item_doc = {
                "_id":          ObjectId(),
                "title":        item["title"],
                "description":  item["description"],
                "type":         item["type"],
                "priority":     item["priority"],
                "story_points": item["story_points"],
                "status":       item_status,
                "space_id":     space_id_str,
                "sprint_id":    sprint_id_str,
                "created_at":   NOW - timedelta(days=84 - i * 14),
                "updated_at":   NOW - timedelta(days=72 - i * 14) if item_status == "Done" else NOW,
            }
            await db.backlog_items.insert_one(item_doc)

            total_sp += item["story_points"]
            if item_status == "Done":
                done_sp += item["story_points"]
            item_count += 1

        sprint_stats.append({
            "name":       sprint_meta["name"][:45],
            "status":     sprint_meta["status"],
            "total_sp":   total_sp,
            "done_sp":    done_sp,
            "items":      item_count,
            "assignees":  sprint_meta["assignee_count"],
        })

        status_icon = "✅" if sprint_meta["status"] == "Completed" else "🔥"
        print(f"  {status_icon} {sprint_meta['name'][:50]}")
        print(f"     {sprint_meta['start_date']} → {sprint_meta['end_date']} | "
              f"{sprint_meta['assignee_count']} devs | "
              f"{done_sp}/{total_sp} SP done | {item_count} items")

    # ── Create unassigned backlog items ───────────────────────────────────────
    print("\n[4/5] Creating unassigned backlog items...")
    for item in UNASSIGNED_BACKLOG:
        item_doc = {
            "_id":          ObjectId(),
            "title":        item["title"],
            "description":  item["description"],
            "type":         item["type"],
            "priority":     item["priority"],
            "story_points": item["story_points"],
            "status":       "To Do",
            "space_id":     space_id_str,
            "sprint_id":    None,   # unassigned
            "created_at":   NOW - timedelta(days=2),
            "updated_at":   NOW - timedelta(days=2),
        }
        await db.backlog_items.insert_one(item_doc)
        print(f"  📋 [{item['priority']:8}] [{item['story_points']:2} SP] {item['title'][:60]}")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n[5/5] Verification summary")
    print("-" * 70)
    print(f"{'Sprint':<48} {'Status':<10} {'Done SP':>7} {'Total SP':>8} {'Util%':>6}")
    print("-" * 70)
    for s in sprint_stats:
        util = round(s["done_sp"] / s["total_sp"] * 100) if s["total_sp"] else 0
        flag = " ⚠" if util < 80 and s["status"] == "Completed" else ""
        print(f"{s['name']:<48} {s['status']:<10} {s['done_sp']:>7} {s['total_sp']:>8} {util:>5}%{flag}")

    print("-" * 70)
    print()

    # Count totals
    total_sprints = await db.sprints.count_documents({"space_id": space_id_str})
    total_items   = await db.backlog_items.count_documents({"space_id": space_id_str})
    unassigned    = await db.backlog_items.count_documents({"space_id": space_id_str, "sprint_id": None})

    print(f"  Space created       : 1")
    print(f"  Sprints created     : {total_sprints} (5 completed + 1 active)")
    print(f"  Backlog items total : {total_items}")
    print(f"  Unassigned (backlog): {unassigned}")
    print()
    print("=" * 70)
    print("✓ Seed complete. Start the backend and open the frontend to explore.")
    print(f"  Space name: \"{SPACE['name']}\"")
    print("=" * 70)
    print()

    client.close()


if __name__ == "__main__":
    asyncio.run(seed())