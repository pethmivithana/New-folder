"""
Comprehensive MongoDB Seeding Script for Agile Sprint Impact Analyzer.

Generates realistic, production-grade datasets across three enterprise projects
with complex velocity patterns, regulatory constraints, and distributed team dynamics.
All dates stored as ISO-formatted strings to prevent serialization issues.
"""

import os
import sys
from datetime import datetime, timedelta
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "agile-tool")

def connect_mongodb():
    """Establish synchronous MongoDB connection."""
    try:
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        db = client[DATABASE_NAME]
        print(f"✓ Connected to MongoDB: {MONGODB_URI}")
        return client, db
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        sys.exit(1)

def clear_collections(db):
    """Clear existing data."""
    for collection in ['spaces', 'sprints', 'backlog_items']:
        count = db[collection].delete_many({}).deleted_count
        print(f"  ✓ {collection}: cleared {count} documents")

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 1: FinTech Payment Orchestration
# ─────────────────────────────────────────────────────────────────────────────

def seed_fintech(db):
    """Fintech Payment Platform with high regulatory constraints."""
    print("\n" + "="*80)
    print("PROJECT 1: FinTech Payment Orchestration Platform")
    print("="*80)
    
    space_doc = {
        "name": "FinTech Payment Orchestration Platform",
        "description": "Distributed payment gateway with blockchain settlement and multi-currency support",
        "max_assignees": 6,
        "focus_hours_per_day": 6.5,
        "risk_appetite": "Strict",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    space = db.spaces.insert_one(space_doc)
    space_id = str(space.inserted_id)
    print(f"✓ Space: {space_id}")
    
    # Sprint 1: Cryptographic Foundation (28 SP)
    now = datetime.now()
    sprint1_start = now - timedelta(days=45)
    sprint1_end = sprint1_start + timedelta(days=14)
    
    sprint1 = {
        "name": "Sprint 1: Cryptographic Foundation & Compliance Framework",
        "goal": "Establish NIST-compliant cryptographic infrastructure for payment transaction signing",
        "duration_type": "2 Weeks",
        "start_date": sprint1_start.strftime('%Y-%m-%d'),
        "end_date": sprint1_end.strftime('%Y-%m-%d'),
        "space_id": space_id,
        "status": "Completed",
        "assignees": [],
        "created_at": sprint1_start,
        "updated_at": now,
    }
    s1 = db.sprints.insert_one(sprint1).inserted_id
    
    items1 = [
        {
            "title": "Implement HMAC-SHA256 Signature Generation Engine",
            "description": "Develop cryptographic signature engine for transaction verification with hardware security module integration",
            "type": "Task",
            "priority": "Critical",
            "story_points": 8,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s1),
            "created_at": sprint1_start,
            "updated_at": now,
        },
        {
            "title": "Configure PCI-DSS Level 1 Compliance Audit",
            "description": "Execute security audit framework compliant with Payment Card Industry Data Security Standards Level 1",
            "type": "Task",
            "priority": "Critical",
            "story_points": 5,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s1),
            "created_at": sprint1_start,
            "updated_at": now,
        },
        {
            "title": "Deploy Key Rotation & Escrow Management System",
            "description": "Establish automated cryptographic key lifecycle management with secure escrow protocols",
            "type": "Task",
            "priority": "High",
            "story_points": 8,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s1),
            "created_at": sprint1_start,
            "updated_at": now,
        },
        {
            "title": "Implement OAuth 2.0 Authorization Code Flow",
            "description": "Build secure authentication framework with JWT token generation and refresh token rotation",
            "type": "Task",
            "priority": "High",
            "story_points": 7,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s1),
            "created_at": sprint1_start,
            "updated_at": now,
        },
    ]
    db.backlog_items.insert_many(items1)
    print(f"  Sprint 1 (28 SP completed): {len(items1)} items")
    
    # Sprint 2: Microservices Architecture (35 SP)
    sprint2_start = now - timedelta(days=30)
    sprint2_end = sprint2_start + timedelta(days=14)
    
    sprint2 = {
        "name": "Sprint 2: Microservices Architecture & Service Orchestration",
        "goal": "Decompose monolithic payment system into resilient microservices with event-driven messaging",
        "duration_type": "2 Weeks",
        "start_date": sprint2_start.strftime('%Y-%m-%d'),
        "end_date": sprint2_end.strftime('%Y-%m-%d'),
        "space_id": space_id,
        "status": "Completed",
        "assignees": [],
        "created_at": sprint2_start,
        "updated_at": now,
    }
    s2 = db.sprints.insert_one(sprint2).inserted_id
    
    items2 = [
        {
            "title": "Architect API Gateway with Request Throttling & Rate Limiting",
            "description": "Design Kong/Envoy-based API gateway with circuit breaker pattern for fault isolation",
            "type": "Story",
            "priority": "Critical",
            "story_points": 13,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s2),
            "created_at": sprint2_start,
            "updated_at": now,
        },
        {
            "title": "Develop Payment Processing Microservice with Saga Pattern",
            "description": "Implement distributed transaction coordination using choreography-based saga pattern",
            "type": "Story",
            "priority": "Critical",
            "story_points": 13,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s2),
            "created_at": sprint2_start,
            "updated_at": now,
        },
        {
            "title": "Deploy Message Queue Infrastructure (RabbitMQ/Kafka)",
            "description": "Configure high-throughput asynchronous messaging with event sourcing capabilities",
            "type": "Task",
            "priority": "High",
            "story_points": 9,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s2),
            "created_at": sprint2_start,
            "updated_at": now,
        },
    ]
    db.backlog_items.insert_many(items2)
    print(f"  Sprint 2 (35 SP completed): {len(items2)} items")
    
    # Sprint 3: Observability (20 SP)
    sprint3_start = now - timedelta(days=15)
    sprint3_end = sprint3_start + timedelta(days=14)
    
    sprint3 = {
        "name": "Sprint 3: Observability & Distributed Tracing Infrastructure",
        "goal": "Implement comprehensive observability stack with distributed tracing for microservices",
        "duration_type": "2 Weeks",
        "start_date": sprint3_start.strftime('%Y-%m-%d'),
        "end_date": sprint3_end.strftime('%Y-%m-%d'),
        "space_id": space_id,
        "status": "Completed",
        "assignees": [],
        "created_at": sprint3_start,
        "updated_at": now,
    }
    s3 = db.sprints.insert_one(sprint3).inserted_id
    
    items3 = [
        {
            "title": "Deploy Prometheus & Grafana Monitoring Stack",
            "description": "Configure metrics collection with custom dashboards for transaction volume, latency percentiles",
            "type": "Task",
            "priority": "High",
            "story_points": 8,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s3),
            "created_at": sprint3_start,
            "updated_at": now,
        },
        {
            "title": "Integrate OpenTelemetry for End-to-End Distributed Tracing",
            "description": "Implement X-Ray/Jaeger tracing to track payment request flow across microservices",
            "type": "Task",
            "priority": "High",
            "story_points": 8,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s3),
            "created_at": sprint3_start,
            "updated_at": now,
        },
        {
            "title": "Establish Alerting Rules for Payment Anomalies",
            "description": "Create anomaly detection rules for transaction failures, latency spikes, fraud indicators",
            "type": "Task",
            "priority": "Medium",
            "story_points": 4,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s3),
            "created_at": sprint3_start,
            "updated_at": now,
        },
    ]
    db.backlog_items.insert_many(items3)
    print(f"  Sprint 3 (20 SP completed): {len(items3)} items")
    
    # Sprint 4: Active (32 SP planned, 26 SP allocated)
    sprint4_start = now - timedelta(days=3)
    sprint4_end = sprint4_start + timedelta(days=11)
    
    sprint4 = {
        "name": "Sprint 4: Blockchain Settlement Integration & Smart Contracts",
        "goal": "Integrate Ethereum/Polygon for decentralized settlement with automated smart contract execution",
        "duration_type": "2 Weeks",
        "start_date": sprint4_start.strftime('%Y-%m-%d'),
        "end_date": sprint4_end.strftime('%Y-%m-%d'),
        "space_id": space_id,
        "status": "Active",
        "assignees": [],
        "created_at": now,
        "updated_at": now,
    }
    s4 = db.sprints.insert_one(sprint4).inserted_id
    
    items4 = [
        {
            "title": "Develop Smart Contract for Multi-Currency Settlement",
            "description": "Engineer Solidity smart contracts with atomic swap capability for cross-chain token exchanges",
            "type": "Story",
            "priority": "Critical",
            "story_points": 13,
            "status": "In Progress",
            "space_id": space_id,
            "sprint_id": str(s4),
            "created_at": sprint4_start,
            "updated_at": now,
        },
        {
            "title": "Implement Web3.js Integration for Blockchain Connectivity",
            "description": "Build library for interacting with blockchain nodes, transaction signing, and receipt verification",
            "type": "Task",
            "priority": "Critical",
            "story_points": 8,
            "status": "To Do",
            "space_id": space_id,
            "sprint_id": str(s4),
            "created_at": sprint4_start,
            "updated_at": now,
        },
        {
            "title": "Setup Gas Optimization & Cost Estimation Engine",
            "description": "Develop gas fee calculation and optimization strategies for mainnet deployments",
            "type": "Task",
            "priority": "High",
            "story_points": 5,
            "status": "To Do",
            "space_id": space_id,
            "sprint_id": str(s4),
            "created_at": sprint4_start,
            "updated_at": now,
        },
    ]
    db.backlog_items.insert_many(items4)
    print(f"  Sprint 4 (26 SP active, 6 SP free): {len(items4)} items")
    
    # Backlog
    backlog_items = [
        {
            "title": "Implement Liquidity Pool Integration for DEX Swaps",
            "description": "Connect to Uniswap V3 liquidity pools with slippage protection mechanisms",
            "type": "Story",
            "priority": "Medium",
            "story_points": 13,
            "status": "To Do",
            "space_id": space_id,
            "sprint_id": None,
            "created_at": now,
            "updated_at": now,
        },
        {
            "title": "Refactor Legacy Settlement Engine (Technical Debt)",
            "description": "Modernize deprecated payment settlement logic with event-sourcing patterns",
            "type": "Task",
            "priority": "Low",
            "story_points": 8,
            "status": "To Do",
            "space_id": space_id,
            "sprint_id": None,
            "created_at": now,
            "updated_at": now,
        },
    ]
    db.backlog_items.insert_many(backlog_items)
    print(f"  Backlog: {len(backlog_items)} items")
    
    return space_id

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 2: Enterprise Identity Management
# ─────────────────────────────────────────────────────────────────────────────

def seed_identity(db):
    """Enterprise SaaS Identity Platform."""
    print("\n" + "="*80)
    print("PROJECT 2: Enterprise Identity Management Platform")
    print("="*80)
    
    space_doc = {
        "name": "Enterprise Identity Management Platform",
        "description": "Multi-tenant identity provider with federation, SSO, and granular access control",
        "max_assignees": 5,
        "focus_hours_per_day": 6.0,
        "risk_appetite": "Standard",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    space = db.spaces.insert_one(space_doc)
    space_id = str(space.inserted_id)
    print(f"✓ Space: {space_id}")
    
    now = datetime.now()
    
    # Sprint 1: SAML/OIDC Federation (30 SP)
    sprint1_start = now - timedelta(days=45)
    sprint1_end = sprint1_start + timedelta(days=14)
    
    sprint1 = {
        "name": "Sprint 1: SAML/OIDC Federation Framework",
        "goal": "Implement industry-standard identity federation protocols for enterprise integrations",
        "duration_type": "2 Weeks",
        "start_date": sprint1_start.strftime('%Y-%m-%d'),
        "end_date": sprint1_end.strftime('%Y-%m-%d'),
        "space_id": space_id,
        "status": "Completed",
        "assignees": [],
        "created_at": sprint1_start,
        "updated_at": now,
    }
    s1 = db.sprints.insert_one(sprint1).inserted_id
    
    items1 = [
        {
            "title": "Develop SAML 2.0 Service Provider with Assertion Validation",
            "description": "Build SP implementation with XML digital signature verification and encryption",
            "type": "Story",
            "priority": "Critical",
            "story_points": 13,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s1),
            "created_at": sprint1_start,
            "updated_at": now,
        },
        {
            "title": "Implement OpenID Connect Authorization Code Flow",
            "description": "Build OIDC provider with JWT token issuance and claims mapping",
            "type": "Task",
            "priority": "Critical",
            "story_points": 10,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s1),
            "created_at": sprint1_start,
            "updated_at": now,
        },
        {
            "title": "Create IdP-Initiated SSO Workflow",
            "description": "Implement deep linking and session management for seamless single sign-on",
            "type": "Task",
            "priority": "High",
            "story_points": 7,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s1),
            "created_at": sprint1_start,
            "updated_at": now,
        },
    ]
    db.backlog_items.insert_many(items1)
    print(f"  Sprint 1 (30 SP completed): {len(items1)} items")
    
    # Sprint 2: Multi-Tenancy (32 SP)
    sprint2_start = now - timedelta(days=30)
    sprint2_end = sprint2_start + timedelta(days=14)
    
    sprint2 = {
        "name": "Sprint 2: Multi-Tenancy & Data Isolation",
        "goal": "Implement tenant isolation with segregated databases and encryption at rest",
        "duration_type": "2 Weeks",
        "start_date": sprint2_start.strftime('%Y-%m-%d'),
        "end_date": sprint2_end.strftime('%Y-%m-%d'),
        "space_id": space_id,
        "status": "Completed",
        "assignees": [],
        "created_at": sprint2_start,
        "updated_at": now,
    }
    s2 = db.sprints.insert_one(sprint2).inserted_id
    
    items2 = [
        {
            "title": "Architect Database Sharding Strategy for Tenant Isolation",
            "description": "Design horizontal partitioning scheme with hash-based distribution across shards",
            "type": "Story",
            "priority": "Critical",
            "story_points": 13,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s2),
            "created_at": sprint2_start,
            "updated_at": now,
        },
        {
            "title": "Implement Encryption at Rest (TDE/AES-256)",
            "description": "Configure transparent data encryption for all tenant data with key rotation",
            "type": "Task",
            "priority": "High",
            "story_points": 8,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s2),
            "created_at": sprint2_start,
            "updated_at": now,
        },
        {
            "title": "Build Row-Level Security Policies (RLS) for Tenants",
            "description": "Implement database-level RLS to prevent cross-tenant data leakage",
            "type": "Task",
            "priority": "High",
            "story_points": 5,
            "status": "In Progress",
            "space_id": space_id,
            "sprint_id": str(s2),
            "created_at": sprint2_start,
            "updated_at": now,
        },
        {
            "title": "Create Multi-Tenant API Rate Limiting",
            "description": "Implement per-tenant quota management with token bucket algorithm",
            "type": "Task",
            "priority": "Medium",
            "story_points": 6,
            "status": "To Do",
            "space_id": space_id,
            "sprint_id": str(s2),
            "created_at": sprint2_start,
            "updated_at": now,
        },
    ]
    db.backlog_items.insert_many(items2)
    print(f"  Sprint 2 (32 SP completed, with spillover): {len(items2)} items")
    
    # Sprint 3: Active (28 SP planned, 18 SP allocated)
    sprint3_start = now - timedelta(days=3)
    sprint3_end = sprint3_start + timedelta(days=11)
    
    sprint3 = {
        "name": "Sprint 3: Audit Logging & Compliance Reporting",
        "goal": "Build comprehensive audit trails with SOC 2 Type II compliance and forensic analysis",
        "duration_type": "2 Weeks",
        "start_date": sprint3_start.strftime('%Y-%m-%d'),
        "end_date": sprint3_end.strftime('%Y-%m-%d'),
        "space_id": space_id,
        "status": "Active",
        "assignees": [],
        "created_at": now,
        "updated_at": now,
    }
    s3 = db.sprints.insert_one(sprint3).inserted_id
    
    items3 = [
        {
            "title": "Implement Immutable Audit Log Storage (Write-Once)",
            "description": "Design append-only event log with WORM (Write Once Read Many) storage",
            "type": "Story",
            "priority": "Critical",
            "story_points": 13,
            "status": "In Progress",
            "space_id": space_id,
            "sprint_id": str(s3),
            "created_at": sprint3_start,
            "updated_at": now,
        },
        {
            "title": "Build Real-Time Compliance Dashboard",
            "description": "Create executive dashboard with real-time compliance metrics and violation alerts",
            "type": "Task",
            "priority": "High",
            "story_points": 5,
            "status": "To Do",
            "space_id": space_id,
            "sprint_id": str(s3),
            "created_at": sprint3_start,
            "updated_at": now,
        },
    ]
    db.backlog_items.insert_many(items3)
    print(f"  Sprint 3 (18 SP active, 10 SP free): {len(items3)} items")
    
    return space_id

# ─────────────────────────────────────────────────────────────────────────────
# PROJECT 3: Healthcare Data Analytics
# ─────────────────────────────────────────────────────────────────────────────

def seed_healthcare(db):
    """HIPAA-compliant Healthcare Analytics Platform."""
    print("\n" + "="*80)
    print("PROJECT 3: Healthcare Data Analytics Platform")
    print("="*80)
    
    space_doc = {
        "name": "Healthcare Data Analytics Platform",
        "description": "HIPAA-compliant analytics platform with HL7/FHIR interoperability",
        "max_assignees": 4,
        "focus_hours_per_day": 5.5,
        "risk_appetite": "Strict",
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }
    space = db.spaces.insert_one(space_doc)
    space_id = str(space.inserted_id)
    print(f"✓ Space: {space_id}")
    
    now = datetime.now()
    
    # Sprint 1: HL7/FHIR Ingestion (25 SP)
    sprint1_start = now - timedelta(days=45)
    sprint1_end = sprint1_start + timedelta(days=14)
    
    sprint1 = {
        "name": "Sprint 1: HL7/FHIR Data Ingestion Pipeline",
        "goal": "Build interoperable data ingestion from healthcare systems using FHIR standards",
        "duration_type": "2 Weeks",
        "start_date": sprint1_start.strftime('%Y-%m-%d'),
        "end_date": sprint1_end.strftime('%Y-%m-%d'),
        "space_id": space_id,
        "status": "Completed",
        "assignees": [],
        "created_at": sprint1_start,
        "updated_at": now,
    }
    s1 = db.sprints.insert_one(sprint1).inserted_id
    
    items1 = [
        {
            "title": "Develop FHIR Resource Parsers (Patient, Observation, Medication)",
            "description": "Build parsers for core FHIR resources with schema validation",
            "type": "Task",
            "priority": "Critical",
            "story_points": 10,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s1),
            "created_at": sprint1_start,
            "updated_at": now,
        },
        {
            "title": "Create HL7v2 to FHIR Transformation Engine",
            "description": "Build transformation pipelines converting legacy HL7v2 messages to FHIR resources",
            "type": "Task",
            "priority": "High",
            "story_points": 8,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s1),
            "created_at": sprint1_start,
            "updated_at": now,
        },
        {
            "title": "Implement Data Quality Validation Rules",
            "description": "Build validation framework for data completeness, consistency, and clinical accuracy",
            "type": "Task",
            "priority": "High",
            "story_points": 7,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s1),
            "created_at": sprint1_start,
            "updated_at": now,
        },
    ]
    db.backlog_items.insert_many(items1)
    print(f"  Sprint 1 (25 SP completed): {len(items1)} items")
    
    # Sprint 2: De-identification (18 SP)
    sprint2_start = now - timedelta(days=30)
    sprint2_end = sprint2_start + timedelta(days=14)
    
    sprint2 = {
        "name": "Sprint 2: De-identification & Privacy-Preserving Analytics",
        "goal": "Implement HIPAA de-identification with differential privacy for population analytics",
        "duration_type": "2 Weeks",
        "start_date": sprint2_start.strftime('%Y-%m-%d'),
        "end_date": sprint2_end.strftime('%Y-%m-%d'),
        "space_id": space_id,
        "status": "Completed",
        "assignees": [],
        "created_at": sprint2_start,
        "updated_at": now,
    }
    s2 = db.sprints.insert_one(sprint2).inserted_id
    
    items2 = [
        {
            "title": "Build HIPAA Safe Harbor De-identification Engine",
            "description": "Implement automated removal of 18 protected health identifiers per HIPAA",
            "type": "Task",
            "priority": "Critical",
            "story_points": 8,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s2),
            "created_at": sprint2_start,
            "updated_at": now,
        },
        {
            "title": "Implement Differential Privacy Algorithms",
            "description": "Add noise/perturbation to aggregated results to prevent individual re-identification",
            "type": "Task",
            "priority": "High",
            "story_points": 8,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s2),
            "created_at": sprint2_start,
            "updated_at": now,
        },
        {
            "title": "Create Data Governance Consent Management",
            "description": "Build consent tracking and policy enforcement for research data usage",
            "type": "Task",
            "priority": "Medium",
            "story_points": 2,
            "status": "Done",
            "space_id": space_id,
            "sprint_id": str(s2),
            "created_at": sprint2_start,
            "updated_at": now,
        },
    ]
    db.backlog_items.insert_many(items2)
    print(f"  Sprint 2 (18 SP completed): {len(items2)} items")
    
    # Sprint 3: Active (30 SP planned, 24 SP allocated)
    sprint3_start = now - timedelta(days=3)
    sprint3_end = sprint3_start + timedelta(days=11)
    
    sprint3 = {
        "name": "Sprint 3: Analytics Engine & Clinical Reporting",
        "goal": "Build query engine for population health analytics with physician-ready reports",
        "duration_type": "2 Weeks",
        "start_date": sprint3_start.strftime('%Y-%m-%d'),
        "end_date": sprint3_end.strftime('%Y-%m-%d'),
        "space_id": space_id,
        "status": "Active",
        "assignees": [],
        "created_at": now,
        "updated_at": now,
    }
    s3 = db.sprints.insert_one(sprint3).inserted_id
    
    items3 = [
        {
            "title": "Develop Federated Query Engine (Apache Iceberg)",
            "description": "Build query engine for distributed clinical data with ACID transactions",
            "type": "Story",
            "priority": "Critical",
            "story_points": 13,
            "status": "In Progress",
            "space_id": space_id,
            "sprint_id": str(s3),
            "created_at": sprint3_start,
            "updated_at": now,
        },
        {
            "title": "Create Clinical Outcomes Report Builder",
            "description": "Build templated reporting system for physician-ready clinical insights",
            "type": "Task",
            "priority": "High",
            "story_points": 8,
            "status": "To Do",
            "space_id": space_id,
            "sprint_id": str(s3),
            "created_at": sprint3_start,
            "updated_at": now,
        },
        {
            "title": "Implement Cohort Definition DSL",
            "description": "Create domain-specific language for defining patient cohorts for clinical trials",
            "type": "Task",
            "priority": "High",
            "story_points": 3,
            "status": "To Do",
            "space_id": space_id,
            "sprint_id": str(s3),
            "created_at": sprint3_start,
            "updated_at": now,
        },
    ]
    db.backlog_items.insert_many(items3)
    print(f"  Sprint 3 (24 SP active, 6 SP free): {len(items3)} items")
    
    return space_id

# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    print("\n" + "="*80)
    print("MONGODB TEST DATA SEEDING - SPRINT IMPACT ANALYZER")
    print("="*80)
    
    client, db = connect_mongodb()
    
    print("\nClearing collections...")
    clear_collections(db)
    
    try:
        id1 = seed_fintech(db)
        id2 = seed_identity(db)
        id3 = seed_healthcare(db)
        
        print("\n" + "="*80)
        print("✓ SEEDING COMPLETE")
        print("="*80)
        print(f"\n✓ Spaces: {db.spaces.count_documents({})}")
        print(f"✓ Sprints: {db.sprints.count_documents({})}")
        print(f"✓ Backlog Items: {db.backlog_items.count_documents({})}")
        print(f"\nProject Space IDs:")
        print(f"  1. FinTech: {id1}")
        print(f"  2. Identity: {id2}")
        print(f"  3. Healthcare: {id3}")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        client.close()
        print("\n✓ Connection closed\n")

if __name__ == "__main__":
    main()
