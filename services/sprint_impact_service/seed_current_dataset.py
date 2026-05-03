#!/usr/bin/env python3
"""
seed_current_dataset.py
────────────────────────────────────────────────────────────────────────────────
Seed script with CURRENT/ACTIVE sprints for testing and development.

Project: TechCorp AI Platform
Team size: 6 developers
Duration per sprint: 2 weeks (10 working days)
Focus hours per dev per day: 6h
Total raw capacity per sprint: 6 devs × 10 days × 6h = 360h
Average hours per SP: 6h → raw SP capacity = 60 SP
Stability buffer: 20% → planned at 80% = 48 SP per sprint

Sprint history:
  Sprint 1 — Completed — 45 SP planned, 42 SP done
  Sprint 2 — Completed — 48 SP planned, 46 SP done
  Sprint 3 — Completed — 45 SP planned, 43 SP done
  Sprint 4 — Active    — 48 SP planned, currently mid-sprint ~24 SP done
  Sprint 5 — Planned   — 48 SP planned, not yet started

Unresolved items from completed sprints sit in backlog as unassigned items.

Usage:
  cd services/sprint_impact_service
  python seed_current_dataset.py

  Or with explicit MongoDB URI:
  MONGODB_URI=mongodb://localhost:27017 python seed_current_dataset.py
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
    "name": "TechCorp AI Platform — Next-Gen Intelligence Suite",
    "description": (
        "TechCorp AI Platform is an enterprise AI/ML SaaS solution providing "
        "large language model API orchestration, fine-tuning workflows, "
        "vector database integration, and real-time inference optimization "
        "for Fortune 500 companies. The platform abstracts provider complexity, "
        "manages token spending across OpenAI/Anthropic/Groq, and delivers "
        "compliance-first features for HIPAA/SOC2 regulated industries."
    ),
    "max_assignees": 7,
    "focus_hours_per_day": 6.0,
    "risk_appetite": "Standard",
    "created_at": days_ago(60),
    "updated_at": days_ago(60),
}


# ══════════════════════════════════════════════════════════════════════════════
# SPRINTS — 3 completed + 1 active + 1 planned
# Each sprint: start_date, end_date, assignee_count, planned SP, actual done SP
# ══════════════════════════════════════════════════════════════════════════════

# Sprint 1: days 56–42 ago
# Sprint 2: days 42–28 ago
# Sprint 3: days 28–14 ago
# Sprint 4: days 7 ago → days 7 from now  (active, mid-sprint)
# Sprint 5: days 8 from now → days 22 from now (planned, not started)

SPRINTS_META = [
    {
        "name": "Sprint 1 — Multi-Provider LLM Integration",
        "goal": (
            "Establish the core LLM provider abstraction layer supporting OpenAI GPT-4, "
            "Anthropic Claude, and Groq Mixtral APIs. Implement request routing, prompt "
            "caching, token counting, and fallback mechanisms. Build provider credential "
            "management with secure vault integration and token spend tracking."
        ),
        "duration_type": "2 Weeks",
        "start_date": fmt(days_ago(56)),
        "end_date":   fmt(days_ago(42)),
        "status": "Completed",
        "assignee_count": 6,
        "assignees": [1, 2, 3, 4, 5, 6],
    },
    {
        "name": "Sprint 2 — Vector Database & RAG Pipeline",
        "goal": (
            "Integrate Pinecone and Weaviate vector databases for semantic search. Build "
            "the Retrieval-Augmented Generation (RAG) pipeline with document ingestion, "
            "chunking, embedding generation, and retrieval ranking. Implement similarity "
            "search with metadata filtering and hybrid BM25+semantic search."
        ),
        "duration_type": "2 Weeks",
        "start_date": fmt(days_ago(42)),
        "end_date":   fmt(days_ago(28)),
        "status": "Completed",
        "assignee_count": 6,
        "assignees": [1, 2, 3, 4, 5, 6],
    },
    {
        "name": "Sprint 3 — Fine-Tuning & Model Management",
        "goal": (
            "Implement fine-tuning workflows for custom model adaptation. Build dataset "
            "preparation tools, training job orchestration, evaluation metrics, and model "
            "versioning. Support OpenAI fine-tuning API and Hugging Face model hosting. "
            "Create model registry with A/B testing capabilities."
        ),
        "duration_type": "2 Weeks",
        "start_date": fmt(days_ago(28)),
        "end_date":   fmt(days_ago(14)),
        "status": "Completed",
        "assignee_count": 6,
        "assignees": [1, 2, 3, 4, 5, 6],
    },
    {
        "name": "Sprint 4 — API Gateway, Monitoring & Cost Optimization",
        "goal": (
            "Deliver rate-limiting API gateway with per-customer token budgets, request "
            "logging, and analytics. Build comprehensive monitoring dashboard with latency, "
            "error rate, and token spend metrics. Implement intelligent request batching "
            "and cache layer to reduce API costs by 30%."
        ),
        "duration_type": "2 Weeks",
        "start_date": fmt(days_ago(7)),
        "end_date":   fmt(days_from_now(7)),
        "status": "Active",
        "assignee_count": 6,
        "assignees": [1, 2, 3, 4, 5, 6],
    },
    {
        "name": "Sprint 5 — Security Hardening & Compliance",
        "goal": (
            "Achieve SOC 2 Type II and HIPAA compliance. Implement data encryption at rest "
            "and in transit, audit logging, RBAC, and PII redaction pipelines. Add compliance "
            "reporting and security event alerting. Conduct penetration testing and remediate "
            "findings."
        ),
        "duration_type": "2 Weeks",
        "start_date": fmt(days_from_now(8)),
        "end_date":   fmt(days_from_now(22)),
        "status": "Planned",
        "assignee_count": 6,
        "assignees": [1, 2, 3, 4, 5, 6],
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# BACKLOG ITEMS PER SPRINT
#
# Capacity rule:
#   Planned SP per sprint ≈ 48 (80% of 60 SP raw capacity)
#   Done SP:
#     Sprint 1: 42/45 (3 SP not done — 1 item carried)
#     Sprint 2: 46/48 (100% — all done)
#     Sprint 3: 43/45 (2 SP not done — 1 item carried)
#     Sprint 4: Active — 6 items Done (24 SP), rest in various states
#     Sprint 5: Planned — all items To Do
#
# story_points range: 3–13 (enforced by model Field ge=3 le=15)
# ══════════════════════════════════════════════════════════════════════════════

ITEMS_BY_SPRINT_INDEX = {

    # ── Sprint 1: Multi-Provider LLM Integration ────────────────────────────────
    # Planned: 45 SP | Done: 42 SP | Carried: 1 item (3 SP)
    0: [
        {
            "title": "Implement OpenAI API client with GPT-4 and GPT-4 Turbo support",
            "description": (
                "Create OpenAI provider adapter using official openai-python library. "
                "Support /chat/completions and /embeddings endpoints with streaming. "
                "Implement token counting via tiktoken. Add request/response logging, "
                "retry logic with exponential backoff, and timeout handling. Support "
                "function calling and vision capabilities for multimodal requests."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Implement Anthropic Claude API integration",
            "description": (
                "Build Anthropic provider adapter supporting Claude 3 Opus/Sonnet/Haiku. "
                "Implement streaming text generation, batch processing, and vision API. "
                "Add prompt caching for long context windows. Implement cost tracking "
                "with input/output token differentiation. Add fallback to GPT-4 on errors."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Implement Groq Mixtral fast inference API client",
            "description": (
                "Build Groq provider adapter for high-speed Mixtral 8x7B inference. "
                "Implement request queueing for batch processing. Add latency monitoring "
                "and speed benchmarking. Support context window up to 32k tokens. "
                "Configure cost-optimized routing for non-critical requests."
            ),
            "type": "Story", "priority": "Medium", "story_points": 8, "status": "Done",
        },
        {
            "title": "Build provider abstraction layer with unified interface",
            "description": (
                "Create abstract BaseProvider class defining unified interface: complete(), "
                "embed(), count_tokens(), get_cost(). Implement provider factory pattern "
                "for runtime selection. Add request transformation/response normalization "
                "across OpenAI/Anthropic/Groq response formats. Ensure error handling "
                "consistency across all providers."
            ),
            "type": "Story", "priority": "High", "story_points": 13, "status": "Done",
        },
        {
            "title": "Implement credential management with HashiCorp Vault integration",
            "description": (
                "Build secure credential storage using HashiCorp Vault. Implement API key "
                "rotation, expiry tracking, and access logging. Add per-tenant API key "
                "isolation. Implement rate limiting per API key. Support emergency revocation "
                "and audit trails. Handle credential refresh transparently."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Add fallback and load balancing across multiple providers",
            "description": (
                "Implement health check polling for all providers. Build circuit breaker "
                "pattern: automatically switch to backup provider on repeated failures. "
                "Add weighted round-robin load balancing. Track provider availability "
                "metrics and adjust routing based on latency/error rates. This item had "
                "lower priority and was deferred."
            ),
            "type": "Task", "priority": "Low", "story_points": 3, "status": "To Do",
            # CARRIED: deprioritised to focus on core integrations in Sprint 2
        },
    ],

    # ── Sprint 2: Vector Database & RAG Pipeline ───────────────────────────────
    # Planned: 48 SP | Done: 46 SP | Carried: 0
    1: [
        {
            "title": "Implement Pinecone vector database integration",
            "description": (
                "Build Pinecone client with index management, vector insertion, and "
                "semantic search. Implement namespace isolation per tenant. Add metadata "
                "filtering with key-value and structured filters. Support vector upserting "
                "with collision handling. Implement batch operations for 100k+ vector "
                "ingestion. Add monitoring for index size and query latency."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Implement Weaviate vector store as alternative backend",
            "description": (
                "Build Weaviate client for on-premise vector storage option. Implement "
                "schema definition, class creation, and object insertion. Add GraphQL query "
                "support for semantic search. Configure HNSW algorithm parameters. Implement "
                "backup/restore workflows. Ensure feature parity with Pinecone integration."
            ),
            "type": "Story", "priority": "Medium", "story_points": 8, "status": "Done",
        },
        {
            "title": "Build document chunking and embedding pipeline",
            "description": (
                "Create document parser supporting PDF, DOCX, markdown, and plain text. "
                "Implement chunking strategies: fixed-size with overlap, semantic-aware "
                "chunking using sentence boundaries. Generate embeddings using OpenAI "
                "text-embedding-3-large. Batch embed requests for cost efficiency. "
                "Implement idempotent ingestion with deduplication."
            ),
            "type": "Story", "priority": "High", "story_points": 13, "status": "Done",
        },
        {
            "title": "Implement RAG query pipeline with reranking",
            "description": (
                "Build retrieval pipeline: user query → embedding → vector search (top 10) "
                "→ reranking with semantic-ranking or cross-encoder model → context assembly. "
                "Implement context window optimization to fit retrieved documents within "
                "model's max tokens. Add result citation tracking with source documents. "
                "Support hybrid search combining BM25 and semantic similarity."
            ),
            "type": "Story", "priority": "High", "story_points": 13, "status": "Done",
        },
        {
            "title": "Add advanced RAG features: citations, confidence scores, and feedback",
            "description": (
                "Enhance RAG with source attribution and confidence scoring. Implement "
                "human-in-the-loop feedback collection for relevance scoring. Build "
                "feedback aggregation to improve retrieval over time. Add A/B testing "
                "framework to compare retrieval strategies. Track and log all queries "
                "for quality auditing."
            ),
            "type": "Task", "priority": "Medium", "story_points": 4, "status": "Done",
        },
    ],

    # ── Sprint 3: Fine-Tuning & Model Management ──────────────────────────────
    # Planned: 45 SP | Done: 43 SP | Carried: 1 item (2 SP)
    2: [
        {
            "title": "Build OpenAI fine-tuning job orchestration service",
            "description": (
                "Implement fine-tuning workflow: dataset validation → format conversion → "
                "job submission → status polling → model promotion to staging. Support "
                "hyperparameter tuning (learning rate, epochs, batch size). Implement "
                "training monitoring with loss graphs. Add rollback capability to previous "
                "model version. Track training costs and ROI metrics."
            ),
            "type": "Story", "priority": "High", "story_points": 13, "status": "Done",
        },
        {
            "title": "Create dataset preparation and validation toolkit",
            "description": (
                "Build dataset validator for fine-tuning: format checking, token counting, "
                "balance analysis for classification tasks. Implement data cleaning: "
                "remove duplicates, filter profanity/PII, normalize formatting. Support "
                "data augmentation for low-resource languages. Generate dataset quality "
                "report with recommendations for improvement."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Implement model registry and versioning system",
            "description": (
                "Build centralized model registry tracking all deployed models and versions. "
                "Store metadata: provider, base model, fine-tune parameters, deployment date, "
                "performance metrics. Implement semantic versioning (major.minor.patch). "
                "Add release notes and change tracking. Support rollback to previous versions. "
                "Integrate with Git for model artifact versioning."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Build evaluation framework with custom metrics",
            "description": (
                "Implement evaluation pipeline for model quality assessment. Support metrics: "
                "BLEU, ROUGE, semantic similarity (via embeddings), user satisfaction "
                "(from feedback). Create benchmark datasets for regression testing. "
                "Build comparison dashboard showing performance across model versions. "
                "Add threshold-based alerts for quality degradation."
            ),
            "type": "Task", "priority": "Medium", "story_points": 8, "status": "Done",
        },
        {
            "title": "Implement A/B testing framework for model comparison",
            "description": (
                "Build A/B testing infrastructure for comparing base vs fine-tuned models, "
                "or different model providers. Route traffic based on experiment configuration. "
                "Track metrics: latency, cost, user satisfaction, completion quality. "
                "Implement statistical significance testing. Auto-promotion of winning model. "
                "This item had lower priority and was carried forward."
            ),
            "type": "Task", "priority": "Low", "story_points": 2, "status": "To Do",
            # CARRIED: lower priority than core features
        },
    ],

    # ── Sprint 4: API Gateway, Monitoring & Cost Optimization (ACTIVE) ──────────
    # Planned: 48 SP | Day 7 of 14 | Done: ~24 SP | Rest in progress/todo
    3: [
        {
            "title": "Build rate-limiting API gateway with Kong",
            "description": (
                "Deploy Kong API gateway with request rate limiting per API key and "
                "customer tier. Implement sliding window rate limiting: standard tier 1000 "
                "req/min, enterprise 10000 req/min. Add token bucket algorithm for burst "
                "handling. Log all requests to analytics database. Implement request "
                "authentication with JWT validation. Add request/response transformation "
                "plugins for header injection and response formatting."
            ),
            "type": "Story", "priority": "High", "story_points": 13, "status": "Done",
        },
        {
            "title": "Implement token budget tracking and cost allocation per customer",
            "description": (
                "Create billing service tracking token consumption per customer per model. "
                "Implement token quota system: enforce hard limits, soft warnings at 80%, "
                "soft cap mode (reduced performance at quota). Support cost allocation across "
                "multiple projects. Generate usage reports and cost projections. Implement "
                "webhook alerts for quota threshold breach. Support custom pricing per customer."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Build comprehensive observability stack with Prometheus/Grafana",
            "description": (
                "Instrument API gateway and inference services with Prometheus metrics: "
                "request latency histogram, error rate counter, token consumption gauge, "
                "cost per request histogram. Build Grafana dashboards: latency by model, "
                "error rate by provider, cost trends, token consumption. Create alerts: "
                "p99 latency > 5s, error rate > 5%, cost spike detection. Add custom metrics "
                "for model-specific insights."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "Done",
        },
        {
            "title": "Implement request caching and response deduplication",
            "description": (
                "Build request cache with semantic similarity matching (not exact match). "
                "Cache key: embedding of request hash + model + temperature. Support TTL "
                "configuration per customer. Implement LRU eviction policy. Track cache "
                "hit rate and savings. Add cache invalidation triggers. Store cache in "
                "Redis with cross-region replication for disaster recovery."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "In Progress",
        },
        {
            "title": "Build cost optimization dashboard with insights and recommendations",
            "description": (
                "Create analytics dashboard showing: spend by provider/model, cost per "
                "customer, token efficiency trends, cache hit rates, API latency percentiles. "
                "Implement ML-based cost optimization recommendations: switch to cheaper model "
                "for non-critical requests, batch similar requests, enable caching. Show "
                "projected savings with one-click enable. Track cost optimization wins."
            ),
            "type": "Task", "priority": "Medium", "story_points": 5, "status": "In Progress",
        },
        {
            "title": "Implement intelligent request batching to reduce API costs",
            "description": (
                "Build batching service that groups similar requests and submits in batches "
                "to reduce API overhead. Support configurable batch window (0.5-5 seconds). "
                "Use embeddings to find semantically similar requests for batch optimization. "
                "Track cost savings from batching. This is still in design phase and requires "
                "deeper architecture discussions."
            ),
            "type": "Task", "priority": "Medium", "story_points": 6, "status": "To Do",
        },
    ],

    # ── Sprint 5: Security Hardening & Compliance (PLANNED) ─────────────────────
    # Planned: 48 SP | Not yet started | All To Do
    4: [
        {
            "title": "Implement end-to-end encryption for data in transit and at rest",
            "description": (
                "Enable TLS 1.3 for all API endpoints. Implement AES-256 encryption for "
                "data at rest in PostgreSQL using encrypted columns. Use AWS KMS for key "
                "management with automatic rotation. Implement field-level encryption for "
                "sensitive data: API keys, user credentials. Add key derivation with "
                "per-customer keys for multi-tenancy isolation."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "To Do",
        },
        {
            "title": "Build comprehensive audit logging system for SOC 2 compliance",
            "description": (
                "Implement append-only audit log capturing all: API calls (user, action, "
                "resource, timestamp, IP), data access patterns, configuration changes, "
                "admin actions, authentication events. Use tamper-evident logging with "
                "blockchain-style hash chaining. Archive logs to immutable S3 buckets. "
                "Support compliance report generation for auditors. Implement log retention "
                "policies per regulatory requirement (7 years for financial)."
            ),
            "type": "Story", "priority": "High", "story_points": 13, "status": "To Do",
        },
        {
            "title": "Implement RBAC with granular permission model",
            "description": (
                "Build role-based access control supporting: Admin, Manager, Developer, "
                "Viewer roles with customizable permissions. Implement resource-level "
                "permissions: can_list_models, can_deploy_models, can_view_costs, "
                "can_manage_users. Add attribute-based access control (ABAC) for project-level "
                "isolation. Support service accounts for CI/CD. Add audit logging for all "
                "permission changes."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "To Do",
        },
        {
            "title": "Add PII detection and redaction for HIPAA compliance",
            "description": (
                "Implement PII detection using pattern matching and ML models. Detect: "
                "SSN, credit card numbers, medical record numbers, PHI. Support automatic "
                "redaction in logs and analytics. Implement masking strategies: tokenization, "
                "anonymization, differential privacy. Add PII compliance reporting. Support "
                "data subject access requests (DSAR) with automated PII extraction."
            ),
            "type": "Story", "priority": "High", "story_points": 8, "status": "To Do",
        },
        {
            "title": "Conduct security penetration testing and remediate findings",
            "description": (
                "Hire third-party penetration testing firm to conduct full security audit. "
                "Areas: API security, authentication/authorization, data encryption, "
                "injection vulnerabilities, CSRF/XSS. Build remediation plan with priority "
                "scores. Implement fixes and verify resolution. Generate compliance report "
                "for SOC 2 Type II certification evidence."
            ),
            "type": "Task", "priority": "High", "story_points": 3, "status": "To Do",
        },
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# BACKLOG ITEMS (unassigned — orphaned from sprint overruns + new items)
# ══════════════════════════════════════════════════════════════════════════════

UNASSIGNED_BACKLOG = [
    # Carried from Sprint 1
    {
        "title": "Add fallback and load balancing across multiple providers",
        "description": (
            "Implement health check polling for all providers. Build circuit breaker "
            "pattern: automatically switch to backup provider on repeated failures. "
            "Add weighted round-robin load balancing. Track provider availability "
            "metrics and adjust routing based on latency/error rates. Prioritized "
            "for Sprint 2 but deferred due to higher-priority RAG work."
        ),
        "type": "Task", "priority": "Medium", "story_points": 3,
    },
    # Carried from Sprint 3
    {
        "title": "Implement A/B testing framework for model comparison",
        "description": (
            "Build A/B testing infrastructure for comparing base vs fine-tuned models, "
            "or different model providers. Route traffic based on experiment configuration. "
            "Track metrics: latency, cost, user satisfaction, completion quality. "
            "Implement statistical significance testing. Auto-promotion of winning model. "
            "Deferred as lower priority than core fine-tuning features."
        ),
        "type": "Task", "priority": "Medium", "story_points": 2,
    },
    # New backlog items for future sprints
    {
        "title": "Implement multi-modal LLM support for image and audio inputs",
        "description": (
            "Add support for vision-enabled models (GPT-4 Vision, Claude 3 Vision). "
            "Implement image preprocessing and encoding. Add speech-to-text and "
            "text-to-speech capabilities. Support audio file uploads and streaming. "
            "Implement multimodal embeddings for cross-modal search. High value for "
            "customer use cases but requires significant implementation effort."
        ),
        "type": "Story", "priority": "High", "story_points": 13,
    },
    {
        "title": "Build marketplace for model finetunes and custom models",
        "description": (
            "Create internal marketplace where customers can share fine-tuned models. "
            "Implement model discovery, ratings, and usage tracking. Support model "
            "licensing (free, paid, private). Build revenue sharing for model creators. "
            "Implement model quality certification process. Enable community-driven "
            "model improvements."
        ),
        "type": "Story", "priority": "Medium", "story_points": 13,
    },
    {
        "title": "Implement serverless inference with AWS Lambda and ECS Fargate",
        "description": (
            "Build serverless inference layer for cost optimization. Deploy model "
            "inference on Lambda for synchronous requests, Fargate for batch jobs. "
            "Implement auto-scaling based on queue depth. Add cold-start optimization "
            "with model preloading. Integrate with API Gateway for request routing. "
            "Track cost improvements vs managed inference."
        ),
        "type": "Story", "priority": "Medium", "story_points": 8,
    },
    {
        "title": "Add customer analytics and usage insights dashboard",
        "description": (
            "Build customer-facing analytics dashboard showing: API usage over time, "
            "top used models, feature adoption, cost trends. Implement usage alerts "
            "and quota warnings. Add comparative analytics: how usage compares to peers. "
            "Build usage forecasting with ML. Support custom metric definitions. "
            "Enable customers to export usage data for their own analysis."
        ),
        "type": "Story", "priority": "Medium", "story_points": 8,
    },
    {
        "title": "Implement model versioning with canary deployments",
        "description": (
            "Build safe model deployment with canary releases: deploy new model version "
            "to 5% of traffic, monitor metrics, gradually increase to 100%. Implement "
            "automatic rollback on error rate threshold. Track deployment history and "
            "rollback reasons. Support multi-version serving (run 2 versions simultaneously). "
            "Add feature flags for per-customer model versions."
        ),
        "type": "Story", "priority": "Medium", "story_points": 8,
    },
]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN SEED FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

async def seed():
    print("\n" + "=" * 70)
    print("TechCorp AI Platform — Current Dataset Seed")
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
            "created_at":     NOW - timedelta(days=60 - i * 14),
            "updated_at":     NOW - timedelta(days=45 - i * 14) if sprint_meta["status"] == "Completed" else NOW,
        }
        await db.sprints.insert_one(sprint_doc)
        sprint_id_str = str(sprint_doc["_id"])
        sprint_ids.append(sprint_id_str)

        # Insert items for this sprint
        items = ITEMS_BY_SPRINT_INDEX.get(i, [])
        done_sp = 0
        total_sp = 0
        item_count = 0

        for item in items:
            item_status = item["status"]
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
                "created_at":   NOW - timedelta(days=60 - i * 14),
                "updated_at":   NOW - timedelta(days=45 - i * 14),
            }
            await db.backlog_items.insert_one(item_doc)
            item_count += 1
            total_sp += item["story_points"]
            if item_status == "Done":
                done_sp += item["story_points"]

        sprint_stats.append({
            "name": sprint_meta["name"],
            "planned_sp": total_sp,
            "done_sp": done_sp,
            "status": sprint_meta["status"],
            "item_count": item_count,
        })
        print(f"  Sprint {i+1}: {sprint_meta['name']}")
        print(f"    Status: {sprint_meta['status']} | Items: {item_count} | Planned: {total_sp} SP | Done: {done_sp} SP")

    # ── Create unassigned backlog items ──────────────────────────────────────
    print("\n[4/5] Creating unassigned backlog items...")
    backlog_count = 0
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
            "sprint_id":    None,  # Unassigned items have no sprint
            "created_at":   NOW - timedelta(days=5),
            "updated_at":   NOW - timedelta(days=5),
        }
        await db.backlog_items.insert_one(item_doc)
        backlog_count += 1
    print(f"  ✓ Created {backlog_count} unassigned backlog items")

    # ── Summary ───────────────────────────────────────────────────────────────
    print("\n[5/5] Seed completed successfully!")
    print("\nSprint Summary:")
    for stat in sprint_stats:
        print(f"  {stat['name']}")
        print(f"    Status: {stat['status']} | Items: {stat['item_count']} | Planned: {stat['planned_sp']} SP | Done: {stat['done_sp']} SP")

    print(f"\nBacklog Summary:")
    print(f"  Unassigned items: {backlog_count}")

    print("\n" + "=" * 70)
    print("Ready to test! The active sprint (Sprint 4) has:")
    print("  - Start date: 7 days ago")
    print("  - End date: 7 days from now")
    print("  - 24 SP already completed (mid-sprint)")
    print("  - Additional items in progress and pending")
    print("=" * 70 + "\n")

    await client.close()


if __name__ == "__main__":
    asyncio.run(seed())
