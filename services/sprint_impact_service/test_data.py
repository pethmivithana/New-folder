"""
Comprehensive test data seeding script for Sprint Impact Analyzer.

This module generates realistic, production-like data for evaluating sprint
planning optimization algorithms, risk quantification models, and capacity
forecasting heuristics. The generated datasets include multiple projects with
varying organizational complexity, historical velocity patterns, and stakeholder
impact dynamics.

Features:
- Realistic Agile project portfolios with multi-sprint histories
- Velocity variance patterns (team scaling, environmental factors, domain complexity)
- Complex backlog items spanning feature development, technical debt, and incident response
- Sprint lifecycle metadata with temporal progression
- Dynamic capacity calculations based on assignee distribution and historical performance
"""

import asyncio
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncClient, AsyncDatabase
from models import (
    RiskAppetite, BacklogType, Priority, Status, SprintStatus, DurationType
)


class TestDataSeeder:
    """
    Orchestrates generation and persistence of comprehensive test datasets
    for sprint planning evaluation and ML model validation.
    """

    def __init__(self, db: AsyncDatabase):
        self.db = db
        self.timestamp_now = datetime.utcnow()

    async def seed_all(self):
        """Execute complete seeding pipeline with cascading data dependencies."""
        await self.clear_collections()
        
        # Seed Project 1: E-Commerce Platform Modernization
        space_1_id = await self.seed_ecommerce_platform()
        
        # Seed Project 2: SaaS Analytics Dashboard Implementation
        space_2_id = await self.seed_saas_analytics()
        
        # Seed Project 3: Microservices Infrastructure Refactoring
        space_3_id = await self.seed_infrastructure_migration()
        
        print("✓ All test data seeded successfully")
        print(f"  - Project 1 (E-Commerce): {space_1_id}")
        print(f"  - Project 2 (SaaS Analytics): {space_2_id}")
        print(f"  - Project 3 (Infrastructure): {space_3_id}")

    async def clear_collections(self):
        """Purge existing test data to ensure idempotency."""
        await self.db.spaces.delete_many({})
        await self.db.sprints.delete_many({})
        await self.db.backlog_items.delete_many({})
        print("✓ Cleared existing collections")

    async def seed_ecommerce_platform(self) -> str:
        """
        Seed Space 1: E-Commerce Platform Modernization
        
        Organizational Context:
        - Distributed team across 3 timezones with asynchronous standups
        - Mix of senior platform engineers and junior full-stack developers
        - Legacy codebase with technical debt accumulation (35% of velocity reserved)
        - Business pressure for feature velocity (2 major releases/quarter)
        """
        space_data = {
            "name": "E-Commerce Platform Modernization Initiative",
            "description": (
                "Strategic project to modernize legacy e-commerce platform with cloud-native "
                "microservices architecture. Encompasses comprehensive API redesign, database "
                "schema evolution, and gradual client-side SPA migration. Cross-functional "
                "coordination required with payments, logistics, and analytics stakeholders."
            ),
            "max_assignees": 8,
            "focus_hours_per_day": 6.5,
            "risk_appetite": RiskAppetite.STANDARD,
            "created_at": self.timestamp_now - timedelta(days=120),
            "updated_at": self.timestamp_now,
        }
        result = await self.db.spaces.insert_one(space_data)
        space_id = str(result.inserted_id)

        # Historical Sprint Data (Completed)
        completed_sprints = [
            {
                "name": "Sprint 1: API Gateway Foundation",
                "goal": (
                    "Establish foundational API gateway infrastructure with request routing, "
                    "authentication middleware, and circuit breaker patterns for downstream services."
                ),
                "duration_type": DurationType.TWO_WEEKS,
                "start_date": (self.timestamp_now - timedelta(days=113)).strftime('%Y-%m-%d'),
                "end_date": (self.timestamp_now - timedelta(days=99)).strftime('%Y-%m-%d'),
                "space_id": space_id,
                "status": SprintStatus.COMPLETED,
                "assignees": [4],
                "created_at": self.timestamp_now - timedelta(days=113),
                "updated_at": self.timestamp_now - timedelta(days=99),
            },
            {
                "name": "Sprint 2: User Service Extraction & Domain Modeling",
                "goal": (
                    "Decouple user authentication and profile management from monolithic core. "
                    "Implement domain-driven design patterns for identity and access control (IAC)."
                ),
                "duration_type": DurationType.TWO_WEEKS,
                "start_date": (self.timestamp_now - timedelta(days=99)).strftime('%Y-%m-%d'),
                "end_date": (self.timestamp_now - timedelta(days=85)).strftime('%Y-%m-%d'),
                "space_id": space_id,
                "status": SprintStatus.COMPLETED,
                "assignees": [5],
                "created_at": self.timestamp_now - timedelta(days=99),
                "updated_at": self.timestamp_now - timedelta(days=85),
            },
            {
                "name": "Sprint 3: Product Catalog Refactoring & Elasticsearch Integration",
                "goal": (
                    "Refactor product catalog data layer with read-write splitting. Integrate "
                    "Elasticsearch for advanced full-text search, faceted navigation, and real-time "
                    "inventory synchronization with CDN invalidation strategies."
                ),
                "duration_type": DurationType.TWO_WEEKS,
                "start_date": (self.timestamp_now - timedelta(days=85)).strftime('%Y-%m-%d'),
                "end_date": (self.timestamp_now - timedelta(days=71)).strftime('%Y-%m-%d'),
                "space_id": space_id,
                "status": SprintStatus.COMPLETED,
                "assignees": [6],
                "created_at": self.timestamp_now - timedelta(days=85),
                "updated_at": self.timestamp_now - timedelta(days=71),
            },
            {
                "name": "Sprint 4: Payment Orchestration & PCI-DSS Compliance",
                "goal": (
                    "Implement tokenized payment processing with multi-gateway support (Stripe, "
                    "PayPal, Square). Achieve PCI-DSS Level 1 compliance through encryption, "
                    "audit logging, and vulnerability scanning automation."
                ),
                "duration_type": DurationType.TWO_WEEKS,
                "start_date": (self.timestamp_now - timedelta(days=71)).strftime('%Y-%m-%d'),
                "end_date": (self.timestamp_now - timedelta(days=57)).strftime('%Y-%m-%d'),
                "space_id": space_id,
                "status": SprintStatus.COMPLETED,
                "assignees": [5],
                "created_at": self.timestamp_now - timedelta(days=71),
                "updated_at": self.timestamp_now - timedelta(days=57),
            },
            {
                "name": "Sprint 5: Distributed Caching & Session Management",
                "goal": (
                    "Deploy Redis cluster for distributed session storage, cache-aside patterns, "
                    "and rate limiting. Implement session affinity through consistent hashing and "
                    "graceful connection pooling with circuit breaker integration."
                ),
                "duration_type": DurationType.TWO_WEEKS,
                "start_date": (self.timestamp_now - timedelta(days=57)).strftime('%Y-%m-%d'),
                "end_date": (self.timestamp_now - timedelta(days=43)).strftime('%Y-%m-%d'),
                "space_id": space_id,
                "status": SprintStatus.COMPLETED,
                "assignees": [4],
                "created_at": self.timestamp_now - timedelta(days=57),
                "updated_at": self.timestamp_now - timedelta(days=43),
            },
        ]
        await self.db.sprints.insert_many(completed_sprints)

        # Active Sprint
        active_sprint_data = {
            "name": "Sprint 6: Order Management System Decomposition",
            "goal": (
                "Extract order fulfillment logic into dedicated microservice. Implement event-driven "
                "architecture with Kafka topics for order state transitions. Design compensating "
                "transactions for distributed saga pattern implementation across payment and inventory services."
            ),
            "duration_type": DurationType.TWO_WEEKS,
            "start_date": (self.timestamp_now - timedelta(days=43)).strftime('%Y-%m-%d'),
            "end_date": (self.timestamp_now + timedelta(days=-29)).strftime('%Y-%m-%d'),
            "space_id": space_id,
            "status": SprintStatus.ACTIVE,
            "assignees": [6],
            "created_at": self.timestamp_now - timedelta(days=43),
            "updated_at": self.timestamp_now,
        }
        active_sprint_result = await self.db.sprints.insert_one(active_sprint_data)
        active_sprint_id = str(active_sprint_result.inserted_id)

        # Backlog Items
        backlog_items = [
            {
                "title": "Implement distributed transaction coordinator with two-phase commit",
                "description": (
                    "Design and implement transaction coordination layer for cross-service consistency. "
                    "Evaluate Seata framework vs. custom implementation with PostgreSQL XA support. "
                    "Include failure recovery mechanisms and audit trail generation."
                ),
                "type": BacklogType.STORY,
                "priority": Priority.CRITICAL,
                "story_points": 13,
                "space_id": space_id,
                "sprint_id": active_sprint_id,
                "status": Status.IN_PROGRESS,
                "created_at": self.timestamp_now - timedelta(days=10),
                "updated_at": self.timestamp_now,
            },
            {
                "title": "Refactor authentication middleware with JWT refresh token rotation",
                "description": (
                    "Implement secure token rotation strategy with sliding window expiration. "
                    "Add blacklist mechanism for token revocation. Integrate with IdP (Azure AD/Okta) "
                    "for OIDC compliance and MFA support."
                ),
                "type": BacklogType.TASK,
                "priority": Priority.HIGH,
                "story_points": 8,
                "space_id": space_id,
                "sprint_id": active_sprint_id,
                "status": Status.IN_PROGRESS,
                "created_at": self.timestamp_now - timedelta(days=8),
                "updated_at": self.timestamp_now,
            },
            {
                "title": "Optimize database query performance with query plan analysis and indexing",
                "description": (
                    "Conduct comprehensive database profiling using EXPLAIN ANALYZE. Implement "
                    "missing indexes on frequently accessed columns. Evaluate query rewriting opportunities "
                    "and materialized view candidates for aggregation queries."
                ),
                "type": BacklogType.TASK,
                "priority": Priority.HIGH,
                "story_points": 5,
                "space_id": space_id,
                "sprint_id": None,
                "status": Status.TODO,
                "created_at": self.timestamp_now - timedelta(days=20),
                "updated_at": self.timestamp_now,
            },
            {
                "title": "Build real-time order status notification system with WebSocket implementation",
                "description": (
                    "Implement WebSocket server for bidirectional communication. Design subscription "
                    "model for order status updates. Include reconnection logic, message queuing for "
                    "offline clients, and compression for bandwidth optimization."
                ),
                "type": BacklogType.STORY,
                "priority": Priority.HIGH,
                "story_points": 13,
                "space_id": space_id,
                "sprint_id": None,
                "status": Status.TODO,
                "created_at": self.timestamp_now - timedelta(days=25),
                "updated_at": self.timestamp_now,
            },
            {
                "title": "Resolve critical memory leak in GraphQL subscription handler",
                "description": (
                    "Investigate and fix memory leak causing OOM crashes in production. Implement "
                    "proper cleanup of subscription observers. Add memory usage monitoring with "
                    "heap snapshots for verification."
                ),
                "type": BacklogType.BUG,
                "priority": Priority.CRITICAL,
                "story_points": 5,
                "space_id": space_id,
                "sprint_id": None,
                "status": Status.TODO,
                "created_at": self.timestamp_now - timedelta(days=3),
                "updated_at": self.timestamp_now,
            },
            {
                "title": "Reduce Docker image size through multi-stage builds and layer optimization",
                "description": (
                    "Analyze current image layers for unnecessary dependencies. Implement multi-stage "
                    "Dockerfile for compiled artifacts. Optimize base image selection (Alpine vs. Distroless). "
                    "Target 60% size reduction."
                ),
                "type": BacklogType.TASK,
                "priority": Priority.MEDIUM,
                "story_points": 3,
                "space_id": space_id,
                "sprint_id": None,
                "status": Status.TODO,
                "created_at": self.timestamp_now - timedelta(days=30),
                "updated_at": self.timestamp_now,
            },
        ]
        await self.db.backlog_items.insert_many(backlog_items)

        return space_id

    async def seed_saas_analytics(self) -> str:
        """
        Seed Space 2: SaaS Analytics Dashboard Implementation
        
        Organizational Context:
        - Startup-phase team with high growth expectations
        - Emphasis on rapid feature delivery and A/B testing
        - Limited infrastructure expertise, heavy reliance on managed services
        - Executive pressure for product parity with enterprise competitors
        """
        space_data = {
            "name": "SaaS Analytics Dashboard Implementation",
            "description": (
                "Development of comprehensive analytics dashboard platform providing real-time metrics, "
                "custom visualization widgets, and predictive analytics capabilities. Integrates with "
                "Segment CDP, HubSpot CRM, and multiple data warehouse solutions (Snowflake, BigQuery). "
                "Requires implementation of role-based access control, audit logging, and compliance "
                "features for HIPAA/SOC2 certification."
            ),
            "max_assignees": 6,
            "focus_hours_per_day": 7.0,
            "risk_appetite": RiskAppetite.LENIENT,
            "created_at": self.timestamp_now - timedelta(days=90),
            "updated_at": self.timestamp_now,
        }
        result = await self.db.spaces.insert_one(space_data)
        space_id = str(result.inserted_id)

        # Historical Sprints
        completed_sprints = [
            {
                "name": "Sprint 1: Data Pipeline & ETL Foundation",
                "goal": "Build Kafka-based event streaming pipeline with schema registry and exactly-once delivery guarantees.",
                "duration_type": DurationType.ONE_WEEK,
                "start_date": (self.timestamp_now - timedelta(days=84)).strftime('%Y-%m-%d'),
                "end_date": (self.timestamp_now - timedelta(days=77)).strftime('%Y-%m-%d'),
                "space_id": space_id,
                "status": SprintStatus.COMPLETED,
                "assignees": [3],
                "created_at": self.timestamp_now - timedelta(days=84),
                "updated_at": self.timestamp_now - timedelta(days=77),
            },
            {
                "name": "Sprint 2: Frontend Dashboard UI Components",
                "goal": "Develop reusable React component library with TypeScript types and Storybook documentation.",
                "duration_type": DurationType.ONE_WEEK,
                "start_date": (self.timestamp_now - timedelta(days=77)).strftime('%Y-%m-%d'),
                "end_date": (self.timestamp_now - timedelta(days=70)).strftime('%Y-%m-%d'),
                "space_id": space_id,
                "status": SprintStatus.COMPLETED,
                "assignees": [4],
                "created_at": self.timestamp_now - timedelta(days=77),
                "updated_at": self.timestamp_now - timedelta(days=70),
            },
            {
                "name": "Sprint 3: Authentication & Multi-tenancy Layer",
                "goal": "Implement OAuth 2.0 with RBAC matrix and tenant isolation at database row level.",
                "duration_type": DurationType.TWO_WEEKS,
                "start_date": (self.timestamp_now - timedelta(days=70)).strftime('%Y-%m-%d'),
                "end_date": (self.timestamp_now - timedelta(days=56)).strftime('%Y-%m-%d'),
                "space_id": space_id,
                "status": SprintStatus.COMPLETED,
                "assignees": [3],
                "created_at": self.timestamp_now - timedelta(days=70),
                "updated_at": self.timestamp_now - timedelta(days=56),
            },
        ]
        await self.db.sprints.insert_many(completed_sprints)

        # Active Sprint
        active_sprint_data = {
            "name": "Sprint 4: Advanced Analytics & ML Integration",
            "goal": (
                "Integrate predictive models for anomaly detection and trend forecasting. "
                "Implement Jupyter notebook embedding for exploratory analysis."
            ),
            "duration_type": DurationType.TWO_WEEKS,
            "start_date": (self.timestamp_now - timedelta(days=56)).strftime('%Y-%m-%d'),
            "end_date": (self.timestamp_now + timedelta(days=-42)).strftime('%Y-%m-%d'),
            "space_id": space_id,
            "status": SprintStatus.ACTIVE,
            "assignees": [4],
            "created_at": self.timestamp_now - timedelta(days=56),
            "updated_at": self.timestamp_now,
        }
        active_sprint_result = await self.db.sprints.insert_one(active_sprint_data)
        active_sprint_id = str(active_sprint_result.inserted_id)

        # Backlog Items
        backlog_items = [
            {
                "title": "Integrate scikit-learn model serving with FastAPI inference endpoints",
                "description": (
                    "Deploy pre-trained models for customer churn prediction and LTV forecasting. "
                    "Implement model versioning, A/B testing framework, and online learning pipeline."
                ),
                "type": BacklogType.STORY,
                "priority": Priority.HIGH,
                "story_points": 13,
                "space_id": space_id,
                "sprint_id": active_sprint_id,
                "status": Status.IN_PROGRESS,
                "created_at": self.timestamp_now - timedelta(days=10),
                "updated_at": self.timestamp_now,
            },
            {
                "title": "Build custom visualization library for geospatial heat maps and time-series analysis",
                "description": (
                    "Develop D3.js-based custom visualizations with WebGL rendering for large datasets. "
                    "Include interactive drill-down capabilities and cross-filter synchronization."
                ),
                "type": BacklogType.STORY,
                "priority": Priority.HIGH,
                "story_points": 13,
                "space_id": space_id,
                "sprint_id": None,
                "status": Status.TODO,
                "created_at": self.timestamp_now - timedelta(days=20),
                "updated_at": self.timestamp_now,
            },
            {
                "title": "Fix race condition in real-time metric aggregation service",
                "description": (
                    "Investigate and resolve data consistency issues in windowed aggregations. "
                    "Implement proper locking mechanisms and idempotency keys for deduplication."
                ),
                "type": BacklogType.BUG,
                "priority": Priority.CRITICAL,
                "story_points": 5,
                "space_id": space_id,
                "sprint_id": None,
                "status": Status.TODO,
                "created_at": self.timestamp_now - timedelta(days=5),
                "updated_at": self.timestamp_now,
            },
        ]
        await self.db.backlog_items.insert_many(backlog_items)

        return space_id

    async def seed_infrastructure_migration(self) -> str:
        """
        Seed Space 3: Microservices Infrastructure Refactoring
        
        Organizational Context:
        - Enterprise with legacy on-prem infrastructure
        - Complex compliance requirements (PCI-DSS, HIPAA, SOC2)
        - Risk-averse decision-making with extensive stakeholder alignment
        - Limited DevOps expertise requiring external consulting
        """
        space_data = {
            "name": "Microservices Infrastructure Refactoring",
            "description": (
                "Enterprise-scale migration from monolithic on-premises architecture to cloud-native "
                "Kubernetes infrastructure. Encompasses comprehensive service discovery, distributed tracing, "
                "observability stack implementation (Prometheus, ELK, Jaeger), and disaster recovery automation. "
                "Requires synchronized coordination across networking, security, and platform teams with "
                "minimal production downtime (RTO < 1hr, RPO < 15min)."
            ),
            "max_assignees": 10,
            "focus_hours_per_day": 5.5,
            "risk_appetite": RiskAppetite.STRICT,
            "created_at": self.timestamp_now - timedelta(days=150),
            "updated_at": self.timestamp_now,
        }
        result = await self.db.spaces.insert_one(space_data)
        space_id = str(result.inserted_id)

        # Historical Sprints
        completed_sprints = [
            {
                "name": "Sprint 1: Kubernetes Cluster Provisioning & CNI Selection",
                "goal": (
                    "Deploy production-grade Kubernetes clusters across 3 AZs. Evaluate and implement "
                    "container networking interface (Calico vs. Flannel) with network policies."
                ),
                "duration_type": DurationType.THREE_WEEKS,
                "start_date": (self.timestamp_now - timedelta(days=144)).strftime('%Y-%m-%d'),
                "end_date": (self.timestamp_now - timedelta(days=123)).strftime('%Y-%m-%d'),
                "space_id": space_id,
                "status": SprintStatus.COMPLETED,
                "assignees": [5],
                "created_at": self.timestamp_now - timedelta(days=144),
                "updated_at": self.timestamp_now - timedelta(days=123),
            },
            {
                "name": "Sprint 2: Service Mesh Implementation with Istio",
                "goal": (
                    "Deploy Istio service mesh for traffic management, security policies, and observability. "
                    "Implement mTLS enforcement and JWT token validation."
                ),
                "duration_type": DurationType.THREE_WEEKS,
                "start_date": (self.timestamp_now - timedelta(days=123)).strftime('%Y-%m-%d'),
                "end_date": (self.timestamp_now - timedelta(days=102)).strftime('%Y-%m-%d'),
                "space_id": space_id,
                "status": SprintStatus.COMPLETED,
                "assignees": [6],
                "created_at": self.timestamp_now - timedelta(days=123),
                "updated_at": self.timestamp_now - timedelta(days=102),
            },
            {
                "name": "Sprint 3: Observability Stack & Distributed Tracing",
                "goal": (
                    "Deploy Prometheus for metrics, ELK stack for logging, Jaeger for distributed tracing. "
                    "Implement custom Grafana dashboards with alerting rules."
                ),
                "duration_type": DurationType.FOUR_WEEKS,
                "start_date": (self.timestamp_now - timedelta(days=102)).strftime('%Y-%m-%d'),
                "end_date": (self.timestamp_now - timedelta(days=74)).strftime('%Y-%m-%d'),
                "space_id": space_id,
                "status": SprintStatus.COMPLETED,
                "assignees": [5],
                "created_at": self.timestamp_now - timedelta(days=102),
                "updated_at": self.timestamp_now - timedelta(days=74),
            },
        ]
        await self.db.sprints.insert_many(completed_sprints)

        # Active Sprint
        active_sprint_data = {
            "name": "Sprint 4: Stateful Services & Data Persistence",
            "goal": (
                "Deploy StatefulSets for database and cache clusters. Implement persistent volume "
                "strategies and backup automation with cross-region replication."
            ),
            "duration_type": DurationType.FOUR_WEEKS,
            "start_date": (self.timestamp_now - timedelta(days=74)).strftime('%Y-%m-%d'),
            "end_date": (self.timestamp_now + timedelta(days=-46)).strftime('%Y-%m-%d'),
            "space_id": space_id,
            "status": SprintStatus.ACTIVE,
            "assignees": [6],
            "created_at": self.timestamp_now - timedelta(days=74),
            "updated_at": self.timestamp_now,
        }
        active_sprint_result = await self.db.sprints.insert_one(active_sprint_data)
        active_sprint_id = str(active_sprint_result.inserted_id)

        # Backlog Items
        backlog_items = [
            {
                "title": "Implement multi-region failover with automated DNS switching and data replication",
                "description": (
                    "Design and implement active-passive failover mechanism across regions. Implement "
                    "cross-region database replication with RPO/RTO validation. Include automated DNS "
                    "updates through Route53 health checks."
                ),
                "type": BacklogType.STORY,
                "priority": Priority.CRITICAL,
                "story_points": 13,
                "space_id": space_id,
                "sprint_id": active_sprint_id,
                "status": Status.IN_PROGRESS,
                "created_at": self.timestamp_now - timedelta(days=15),
                "updated_at": self.timestamp_now,
            },
            {
                "title": "Audit and remediate RBAC configurations for principle of least privilege",
                "description": (
                    "Conduct comprehensive RBAC audit across all services. Implement fine-grained "
                    "service accounts with minimal permissions. Document trust boundaries and "
                    "implement access request workflow."
                ),
                "type": BacklogType.TASK,
                "priority": Priority.CRITICAL,
                "story_points": 8,
                "space_id": space_id,
                "sprint_id": None,
                "status": Status.TODO,
                "created_at": self.timestamp_now - timedelta(days=25),
                "updated_at": self.timestamp_now,
            },
            {
                "title": "Performance testing and optimization of network throughput under load",
                "description": (
                    "Execute load testing with sustained traffic of 50k req/s. Profile network latency "
                    "and bandwidth utilization. Optimize TCP buffer sizes and connection pooling."
                ),
                "type": BacklogType.TASK,
                "priority": Priority.HIGH,
                "story_points": 8,
                "space_id": space_id,
                "sprint_id": None,
                "status": Status.TODO,
                "created_at": self.timestamp_now - timedelta(days=30),
                "updated_at": self.timestamp_now,
            },
        ]
        await self.db.backlog_items.insert_many(backlog_items)

        return space_id


async def main():
    """Initialize MongoDB connection and execute seeding."""
    mongodb_url = "mongodb://localhost:27017"
    client = AsyncClient(mongodb_url)
    db = client["sprint_impact_db"]
    
    seeder = TestDataSeeder(db)
    await seeder.seed_all()
    
    client.close()


if __name__ == "__main__":
    asyncio.run(main())
