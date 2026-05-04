"""
Complex Dataset: Cloud-Native Microservices Platform Migration & Optimization
Project: Distributed Async Task Processing System with Real-time Monitoring
6 Sprints (5 completed + 1 active) with realistic backlog items, varied completion rates
Updated: Today is May 4, 2026 - All dates aligned to current timeline
"""

import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

# MongoDB Connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
client = MongoClient(MONGODB_URI)
db = client["sprint_impact_db"]

def clear_existing_data():
    """Clear existing data for fresh seed"""
    db.spaces.delete_many({})
    db.sprints.delete_many({})
    db.backlog_items.delete_many({})
    print("✓ Cleared existing data")

def seed_space():
    """Create the project space"""
    space = {
        "_id": "space_cloud_migrate",
        "name": "Cloud-Native Microservices Platform",
        "description": "Enterprise migration of monolithic platform to distributed microservices architecture with Kubernetes orchestration, service mesh implementation, and real-time event-driven data pipeline. Focus on horizontal scalability, fault tolerance, and cost optimization through containerization and auto-scaling mechanisms.",
        "team_size": 8,
        "avg_velocity": 45,
        "created_at": datetime(2025, 11, 1),
    }
    db.spaces.insert_one(space)
    print(f"✓ Created space: {space['name']}")
    return space["_id"]

def seed_sprints(space_id):
    """Create 6 sprints (5 completed, 1 active)"""
    
    # Sprint 1: Foundation & Containerization (4 weeks ago, COMPLETED with 93% completion)
    sprint_1 = {
        "_id": "sprint_001",
        "space_id": space_id,
        "sprint_number": 1,
        "name": "Sprint 1 - Foundation & Docker Containerization",
        "goal": "Containerize core monolith, establish CI/CD pipeline, set up Docker registry and implement health check endpoints for service discovery in Kubernetes cluster.",
        "start_date": datetime(2026, 3, 17),
        "end_date": datetime(2026, 3, 31),
        "sprint_velocity": 48,
        "items_committed": 9,
        "items_completed": 8,
        "capacity_hours": 320,
        "hours_burned": 298,
        "status": "completed",
    }
    
    # Sprint 2: Service Mesh & Observability (3 weeks ago, COMPLETED with 96% completion)
    sprint_2 = {
        "_id": "sprint_002",
        "space_id": space_id,
        "sprint_number": 2,
        "name": "Sprint 2 - Istio Service Mesh & Distributed Tracing",
        "goal": "Implement Istio service mesh for inter-service communication, deploy Jaeger for distributed tracing, establish traffic management policies with mTLS encryption for secure service-to-service communication.",
        "start_date": datetime(2026, 4, 1),
        "end_date": datetime(2026, 4, 15),
        "sprint_velocity": 52,
        "items_committed": 8,
        "items_completed": 8,
        "capacity_hours": 320,
        "hours_burned": 315,
        "status": "completed",
    }
    
    # Sprint 3: Database Sharding & Event Streaming (2 weeks ago, COMPLETED with 94% completion)
    sprint_3 = {
        "_id": "sprint_003",
        "space_id": space_id,
        "sprint_number": 3,
        "name": "Sprint 3 - PostgreSQL Sharding & Apache Kafka Integration",
        "goal": "Implement horizontal database sharding strategy using hash partitioning, migrate event sourcing to Apache Kafka with topic-based routing, establish exactly-once semantics for critical transactions.",
        "start_date": datetime(2026, 4, 16),
        "end_date": datetime(2026, 4, 30),
        "sprint_velocity": 50,
        "items_committed": 10,
        "items_completed": 9,
        "capacity_hours": 320,
        "hours_burned": 302,
        "status": "completed",
    }
    
    # Sprint 4: API Gateway & Rate Limiting (1 week+ ago, COMPLETED with 78% completion - POORLY COMPLETED)
    sprint_4 = {
        "_id": "sprint_004",
        "space_id": space_id,
        "sprint_number": 4,
        "name": "Sprint 4 - Kong API Gateway & Advanced Rate Limiting",
        "goal": "Implement Kong API Gateway with JWT authentication, multi-tier rate limiting per API key/user tier, implement circuit breaker patterns and API versioning strategy for backward compatibility.",
        "start_date": datetime(2026, 5, 1),
        "end_date": datetime(2026, 5, 8),
        "sprint_velocity": 42,
        "items_committed": 9,
        "items_completed": 7,
        "capacity_hours": 320,
        "hours_burned": 268,
        "status": "completed_with_carryover",
        "carryover_count": 2,
    }
    
    # Sprint 5: Metrics & Autoscaling (8 days ago, COMPLETED with 91% completion)
    sprint_5 = {
        "_id": "sprint_005",
        "space_id": space_id,
        "sprint_number": 5,
        "name": "Sprint 5 - Prometheus Metrics & Horizontal Pod Autoscaling",
        "goal": "Instrument all microservices with Prometheus metrics, implement custom HPA policies using CPU/memory/custom metrics, set up Grafana dashboards for real-time cluster monitoring and alerting via PagerDuty.",
        "start_date": datetime(2026, 4, 9),
        "end_date": datetime(2026, 4, 23),
        "sprint_velocity": 48,
        "items_committed": 8,
        "items_completed": 8,
        "capacity_hours": 320,
        "hours_burned": 310,
        "status": "completed",
    }
    
    # Sprint 6: ACTIVE SPRINT - Cost Optimization & Security Hardening (ACTIVE - Today is May 4, 2026)
    # Started 7 days ago, ends in 7 days (middle of sprint)
    sprint_6 = {
        "_id": "sprint_006",
        "space_id": space_id,
        "sprint_number": 6,
        "name": "Sprint 6 - Cost Optimization & Security Hardening",
        "goal": "Implement Spot instance management and resource optimization algorithms, perform security audit of container images and secrets management, establish network policies and Pod Security Standards for production hardening.",
        "start_date": datetime(2026, 4, 27),  # 7 days ago
        "end_date": datetime(2026, 5, 11),   # 7 days from now
        "sprint_velocity": 46,
        "items_committed": 9,
        "items_completed": 4,
        "capacity_hours": 320,
        "hours_burned": 155,
        "status": "active",
    }
    
    sprints = [sprint_1, sprint_2, sprint_3, sprint_4, sprint_5, sprint_6]
    for sprint in sprints:
        db.sprints.insert_one(sprint)
    print(f"✓ Created {len(sprints)} sprints")
    return sprints

def seed_backlog_items(space_id, sprints):
    """Create backlog items for each sprint"""
    
    items = []
    
    # SPRINT 1: Foundation & Docker Containerization (8/9 completed)
    sprint_1_items = [
        {"sprint_id": "sprint_001", "title": "Create base Docker image from Alpine Linux", "description": "Optimize base image size to <150MB, implement multi-stage builds for production-ready container images, add security scanning layer to prevent vulnerable dependencies.", "status": "done", "sp": 5, "assigned_to": ["DevOps-Lead", "Container-Engineer"], "hours": 16},
        {"sprint_id": "sprint_001", "title": "Set up Docker registry with Harbor", "description": "Deploy Harbor container registry with image scanning using Trivy, implement RBAC for registry access control, configure image retention policies and disaster recovery backup strategy.", "status": "done", "sp": 8, "assigned_to": ["DevOps-Lead", "Platform-Engineer"], "hours": 24},
        {"sprint_id": "sprint_001", "title": "Implement CI/CD pipeline with GitLab CI", "description": "Build multi-stage GitLab CI/CD pipeline with linting, unit tests, security scanning (SAST), container build, push to Harbor, and staging deployment. Implement approval gates for production.", "status": "done", "sp": 13, "assigned_to": ["DevOps-Lead", "DevOps-Engineer-1", "DevOps-Engineer-2"], "hours": 40},
        {"sprint_id": "sprint_001", "title": "Containerize authentication microservice", "description": "Refactor auth service for 12-factor app compliance, implement graceful shutdown handling, add structured JSON logging, create health check endpoints for Kubernetes liveness/readiness probes.", "status": "done", "sp": 8, "assigned_to": ["Backend-Engineer-1", "DevOps-Engineer-1"], "hours": 24},
        {"sprint_id": "sprint_001", "title": "Containerize payment processing service", "description": "Isolate payment logic into standalone container, implement request idempotency for payment retries, add database connection pooling with configurable timeouts, secure API keys via environment variables.", "status": "done", "sp": 8, "assigned_to": ["Backend-Engineer-2", "DevOps-Engineer-1"], "hours": 24},
        {"sprint_id": "sprint_001", "title": "Containerize inventory management service", "description": "Extract inventory service from monolith, implement event-driven updates via message queue hooks, add distributed caching with Redis, set up database schema versioning for future migrations.", "status": "done", "sp": 5, "assigned_to": ["Backend-Engineer-1"], "hours": 16},
        {"sprint_id": "sprint_001", "title": "Create Kubernetes manifests for initial deployment", "description": "Write Deployments, Services, ConfigMaps, and Secrets manifests for three core services, implement resource requests/limits for CPU/memory, create namespace for development environment.", "status": "done", "sp": 8, "assigned_to": ["Platform-Engineer", "DevOps-Lead"], "hours": 24},
        {"sprint_id": "sprint_001", "title": "Set up local development with Docker Compose", "description": "Create docker-compose.yml for local development stack including PostgreSQL, Redis, Kafka, and all microservices, implement hot-reload for Python/Node services, add debugging support with VSCode Dev Containers.", "status": "done", "sp": 5, "assigned_to": ["DevOps-Engineer-2"], "hours": 16},
        {"sprint_id": "sprint_001", "title": "Document containerization runbooks and troubleshooting guides", "description": "Write detailed documentation for container deployment, create troubleshooting guides for common issues, implement logging strategy and error reporting patterns, set up wiki for team reference.", "status": "todo", "sp": 3, "assigned_to": ["Technical-Writer"], "hours": 8},
    ]
    
    # SPRINT 2: Istio Service Mesh & Observability (8/8 completed)
    sprint_2_items = [
        {"sprint_id": "sprint_002", "title": "Install and configure Istio control plane", "description": "Deploy Istio 1.18+ with minimal profile, configure ingress gateway with TLS termination, implement sidecar auto-injection for workload namespaces, enable strict mTLS mode across cluster.", "status": "done", "sp": 8, "assigned_to": ["Platform-Engineer", "DevOps-Lead"], "hours": 28},
        {"sprint_id": "sprint_002", "title": "Implement traffic management with VirtualServices", "description": "Create VirtualService and DestinationRule configs for weighted routing (canary/blue-green deployments), implement retry policies with exponential backoff, set connection timeouts based on SLOs.", "status": "done", "sp": 8, "assigned_to": ["Platform-Engineer", "Backend-Engineer-1"], "hours": 26},
        {"sprint_id": "sprint_002", "title": "Deploy Jaeger distributed tracing infrastructure", "description": "Install Jaeger all-in-one (dev) and production mode with Elasticsearch backend, configure trace sampling rate (1:1000 for baseline), integrate with Istio for automatic trace collection and correlation IDs.", "status": "done", "sp": 8, "assigned_to": ["DevOps-Engineer-1", "Observability-Engineer"], "hours": 28},
        {"sprint_id": "sprint_002", "title": "Instrument services with OpenTelemetry SDK", "description": "Add OpenTelemetry instrumentation to Python/Node services, implement custom spans for critical business transactions (payment processing, inventory updates), configure exporters for Jaeger backend.", "status": "done", "sp": 8, "assigned_to": ["Backend-Engineer-1", "Backend-Engineer-2", "Backend-Engineer-3"], "hours": 30},
        {"sprint_id": "sprint_002", "title": "Establish mTLS for service-to-service communication", "description": "Enable strict mTLS mode in Istio, implement certificate rotation with cert-manager, validate TLS handshakes in logs, test that unencrypted traffic is rejected at egress.", "status": "done", "sp": 5, "assigned_to": ["Platform-Engineer", "Security-Engineer"], "hours": 18},
        {"sprint_id": "sprint_002", "title": "Create Kiali visualization dashboard", "description": "Deploy Kiali console for service mesh visualization, configure RBAC access controls per namespace, create custom dashboards showing traffic flow and topology, set up alerting for mesh anomalies.", "status": "done", "sp": 5, "assigned_to": ["Observability-Engineer", "DevOps-Engineer-2"], "hours": 15},
        {"sprint_id": "sprint_002", "title": "Implement circuit breaker and bulkhead patterns", "description": "Configure Istio OutlierDetection for automatic failover, implement bulkhead isolation with connection pool limits, set circuit breaker thresholds based on error rate/latency percentiles (p99).", "status": "done", "sp": 5, "assigned_to": ["Platform-Engineer", "Backend-Engineer-1"], "hours": 16},
        {"sprint_id": "sprint_002", "title": "Test service mesh resilience under failure scenarios", "description": "Perform chaos engineering with network delays (latency injection), packet loss simulation, and pod failures, validate that circuit breakers trigger and fallback mechanisms work, document SLO achievements.", "status": "done", "sp": 8, "assigned_to": ["QA-Engineer", "Platform-Engineer"], "hours": 24},
    ]
    
    # SPRINT 3: Database Sharding & Event Streaming (9/10 completed)
    sprint_3_items = [
        {"sprint_id": "sprint_003", "title": "Design and implement consistent hashing for database shards", "description": "Implement hash-based sharding strategy for PostgreSQL, use user_id as shard key for even distribution, implement rebalancing algorithm for future shard additions, create routing layer to direct queries to correct shard.", "status": "done", "sp": 13, "assigned_to": ["Database-Architect", "Backend-Engineer-1", "Backend-Engineer-2"], "hours": 40},
        {"sprint_id": "sprint_003", "title": "Deploy Apache Kafka cluster with 3+ brokers", "description": "Set up Kafka 3.6 cluster on Kubernetes with StatefulSet, configure broker replication factor 3, implement topic auto-creation disabled policy, set up broker-level monitoring and alert thresholds.", "status": "done", "sp": 8, "assigned_to": ["DevOps-Engineer-1", "Platform-Engineer"], "hours": 26},
        {"sprint_id": "sprint_003", "title": "Migrate event sourcing to Kafka topics", "description": "Create Kafka topics for order events, payment events, inventory updates with 5+ partitions, implement producer idempotence for exactly-once semantics, set up topic retention policies (7 days hot, 30 days archive).", "status": "done", "sp": 8, "assigned_to": ["Backend-Engineer-3", "Data-Engineer"], "hours": 26},
        {"sprint_id": "sprint_003", "title": "Implement Kafka consumers for event processing", "description": "Build consumer groups with partition assignment strategy, implement dead-letter topic for failed events, add Consumer lag monitoring via Burrow, implement graceful shutdown with consumer group rebalancing.", "status": "done", "sp": 8, "assigned_to": ["Backend-Engineer-1", "Backend-Engineer-2"], "hours": 28},
        {"sprint_id": "sprint_003", "title": "Set up distributed transaction coordination with Saga pattern", "description": "Implement choreography-based saga for multi-service transactions (order -> payment -> inventory), add compensation logic for rollback scenarios, log saga state for debugging and replay capabilities.", "status": "done", "sp": 13, "assigned_to": ["Backend-Architect", "Backend-Engineer-3"], "hours": 40},
        {"sprint_id": "sprint_003", "title": "Create database schema versioning framework", "description": "Implement Flyway for schema migrations across shards, create version control for stored procedures, establish idempotent migration strategy, test rollback procedures for each migration.", "status": "done", "sp": 5, "assigned_to": ["Database-Engineer"], "hours": 16},
        {"sprint_id": "sprint_003", "title": "Implement read replicas and replication lag monitoring", "description": "Configure PostgreSQL streaming replication to read-only replicas in different zones, set up replication lag alerts, implement read pool for analytics queries, create slot management for logical decoding.", "status": "done", "sp": 8, "assigned_to": ["Database-Engineer", "DevOps-Engineer-2"], "hours": 24},
        {"sprint_id": "sprint_003", "title": "Set up Kafka monitoring with Confluent Control Center", "description": "Deploy Confluent Control Center for Kafka cluster monitoring, create dashboards for throughput/latency/consumer lag, set up alerting for broker failures and topic replica issues, document SLOs for message latency.", "status": "done", "sp": 5, "assigned_to": ["Observability-Engineer", "Platform-Engineer"], "hours": 16},
        {"sprint_id": "sprint_003", "title": "Implement cross-shard query patterns with federation", "description": "Build query federation layer for analytics queries spanning multiple shards, implement MapReduce-style aggregation, cache federation results with TTL, validate query correctness with test suite.", "status": "done", "sp": 8, "assigned_to": ["Backend-Engineer-1", "Data-Engineer"], "hours": 26},
        {"sprint_id": "sprint_003", "title": "Create disaster recovery plan for Kafka cluster", "description": "Document backup strategy for Kafka topics, test recovery from cluster failure, implement automated snapshot mechanism, establish RTO/RPO targets (RTO: 4hrs, RPO: 1hr), create runbooks for common failure scenarios.", "status": "todo", "sp": 5, "assigned_to": ["DevOps-Lead"], "hours": 12},
    ]
    
    # SPRINT 4: Kong API Gateway & Rate Limiting (7/9 completed - CARRYOVER 2 items)
    sprint_4_items = [
        {"sprint_id": "sprint_004", "title": "Deploy Kong API Gateway with PostgreSQL backend", "description": "Install Kong 3.4 in Kubernetes, configure Kong database with separate PostgreSQL instance, set up Kong admin API for declarative configuration, implement Kong Manager UI for API management dashboard.", "status": "done", "sp": 8, "assigned_to": ["Platform-Engineer", "DevOps-Engineer-1"], "hours": 28},
        {"sprint_id": "sprint_004", "title": "Implement JWT authentication plugin", "description": "Configure Kong JWT plugin with RS256 algorithm, integrate with identity provider for token generation, implement token validation and claims verification, set up token refresh mechanism with 1hr expiry.", "status": "done", "sp": 8, "assigned_to": ["Backend-Engineer-2", "Security-Engineer"], "hours": 26},
        {"sprint_id": "sprint_004", "title": "Configure multi-tier rate limiting per API key", "description": "Implement rate limiting plugin with sliding window counter algorithm, create consumer-based rate limiting (Basic:100/min, Pro:1000/min, Enterprise:10000/min), integrate with Redis for distributed rate limit state.", "status": "done", "sp": 8, "assigned_to": ["Backend-Engineer-1", "Platform-Engineer"], "hours": 26},
        {"sprint_id": "sprint_004", "title": "Implement API versioning strategy (v1/v2/v3)", "description": "Create Kong routes for multiple API versions with header-based routing, implement deprecation warnings in response headers, set up sunset date for deprecated endpoints, create migration guide for API consumers.", "status": "done", "sp": 5, "assigned_to": ["Backend-Engineer-3"], "hours": 16},
        {"sprint_id": "sprint_004", "title": "Set up circuit breaker plugin in Kong", "description": "Install circuit breaker plugin to upstream services, configure failure thresholds (5 failures/30 sec triggers open), implement exponential backoff retry strategy, test with chaos engineering to validate behavior.", "status": "todo", "sp": 8, "assigned_to": ["QA-Engineer", "Platform-Engineer"], "hours": 24},
        {"sprint_id": "sprint_004", "title": "Implement request/response transformation plugins", "description": "Add request transformer plugin for header injection/removal, implement response transformer for status code mapping, add correlation ID generation for request tracing, validate transformations with Postman test suite.", "status": "todo", "sp": 5, "assigned_to": ["Backend-Engineer-1"], "hours": 16},
        {"sprint_id": "sprint_004", "title": "Create Kong analytics dashboard with real-time metrics", "description": "Set up monitoring for Kong metrics (request count, error rate, latency p99), integrate with Prometheus for scraping, create Grafana dashboards for API traffic patterns, set up alerting for high error rates.", "status": "done", "sp": 8, "assigned_to": ["Observability-Engineer", "DevOps-Engineer-2"], "hours": 28},
        {"sprint_id": "sprint_004", "title": "Implement API request logging and audit trail", "description": "Configure syslog plugin for request/response logging, implement request signing for payment APIs, create audit log table with 1-year retention, set up log analysis for fraud detection patterns.", "status": "done", "sp": 5, "assigned_to": ["Security-Engineer", "Backend-Engineer-2"], "hours": 16},
        {"sprint_id": "sprint_004", "title": "Create API documentation with OpenAPI/Swagger", "description": "Generate OpenAPI 3.0 specs for all Kong routes, publish Swagger UI for developer portal, implement request/response examples, create getting-started guide for API consumers with auth samples.", "status": "done", "sp": 5, "assigned_to": ["Technical-Writer"], "hours": 12},
    ]
    
    # SPRINT 5: Prometheus Metrics & Autoscaling (8/8 completed)
    sprint_5_items = [
        {"sprint_id": "sprint_005", "title": "Install Prometheus server with HA setup", "description": "Deploy Prometheus 2.50+ in HA mode with remote storage (S3 or Thanos), configure scrape configs for all Kubernetes targets, set retention policy to 15 days hot + archive to S3, implement RBAC for metrics access.", "status": "done", "sp": 8, "assigned_to": ["Observability-Engineer", "DevOps-Engineer-1"], "hours": 28},
        {"sprint_id": "sprint_005", "title": "Instrument services with Prometheus client libraries", "description": "Add Prometheus Python/Node client libraries to microservices, implement custom metrics for business logic (transaction count, revenue, user signups), expose /metrics endpoint on port 9090, set up metric cardinality monitoring.", "status": "done", "sp": 8, "assigned_to": ["Backend-Engineer-1", "Backend-Engineer-2", "Backend-Engineer-3"], "hours": 32},
        {"sprint_id": "sprint_005", "title": "Deploy Grafana with curated dashboards", "description": "Install Grafana with Prometheus datasource, create system dashboard (CPU/memory/disk/network), create application dashboard (request rate/latency/errors), create business dashboard (orders/revenue/users), set up dashboard templating.", "status": "done", "sp": 8, "assigned_to": ["Observability-Engineer", "DevOps-Engineer-2"], "hours": 28},
        {"sprint_id": "sprint_005", "title": "Implement custom HPA using memory and custom metrics", "description": "Configure HPA with memory requests (target: 70%), implement custom metrics for queue length (from Kafka), scale auth service on memory + custom queue metric, test scaling behavior under load simulation.", "status": "done", "sp": 8, "assigned_to": ["Platform-Engineer", "Backend-Engineer-1"], "hours": 28},
        {"sprint_id": "sprint_005", "title": "Set up Prometheus alerting rules and AlertManager", "description": "Create alert rules for critical metrics (high error rate >1%, latency p99 >1s, pod restart loops), configure AlertManager for email/Slack notifications, implement alert routing based on severity and team ownership.", "status": "done", "sp": 8, "assigned_to": ["Observability-Engineer"], "hours": 24},
        {"sprint_id": "sprint_005", "title": "Integrate PagerDuty for incident on-call rotation", "description": "Configure AlertManager to send critical alerts to PagerDuty, set up escalation policies for unacknowledged alerts (5 min escalation), implement on-call schedule rotation weekly, integrate runbooks in alerts for quick resolution.", "status": "done", "sp": 5, "assigned_to": ["Observability-Engineer", "DevOps-Lead"], "hours": 16},
        {"sprint_id": "sprint_005", "title": "Implement performance baseline and SLO tracking", "description": "Define SLOs for error rate (99.5%), latency p99 (<500ms), availability (99.9%), create SLO dashboards tracking burndown, set up SLI calculations from metrics, document SLO philosophy and error budgets.", "status": "done", "sp": 8, "assigned_to": ["Observability-Engineer"], "hours": 24},
        {"sprint_id": "sprint_005", "title": "Test autoscaling under load with k6 performance testing", "description": "Create k6 load test script simulating realistic user behavior, generate 10K concurrent users, monitor autoscaling decisions and pod spinup times, validate HPA triggers correct scaling within 60s, document findings.", "status": "done", "sp": 5, "assigned_to": ["QA-Engineer", "Performance-Engineer"], "hours": 16},
    ]
    
    # SPRINT 6: ACTIVE SPRINT - Cost Optimization & Security (4/9 completed + 5 in progress)
    sprint_6_items = [
        {"sprint_id": "sprint_006", "title": "Implement Spot instance management for cost optimization", "description": "Configure Karpenter for automated Spot/On-demand provisioning, set up interruption handling with graceful node drains, implement cost tracking per namespace, target 60% cost reduction through Spot usage while maintaining SLAs.", "status": "done", "sp": 13, "assigned_to": ["Platform-Engineer", "Cloud-Architect", "DevOps-Lead"], "hours": 38},
        {"sprint_id": "sprint_006", "title": "Perform comprehensive security audit of container images", "description": "Scan all container images with Trivy for vulnerabilities, implement image signing with cosign, remove hardcoded secrets and rotate leaked credentials, update base images to latest secure version (Alpine 3.19+).", "status": "done", "sp": 8, "assigned_to": ["Security-Engineer", "DevOps-Engineer-1"], "hours": 28},
        {"sprint_id": "sprint_006", "title": "Implement secrets management with HashiCorp Vault", "description": "Deploy Vault in HA mode with Consul backend, migrate secrets from Kubernetes Secrets to Vault, implement Vault Agent for automatic secret injection into pods, set up audit logging for secret access.", "status": "done", "sp": 8, "assigned_to": ["Security-Engineer", "Platform-Engineer"], "hours": 28},
        {"sprint_id": "sprint_006", "title": "Establish Pod Security Standards and network policies", "description": "Enforce Pod Security Standard restricted policy (non-root users, read-only filesystem), implement Cilium network policies for zero-trust networking, restrict egress to approved domains only, test policy enforcement.", "status": "done", "sp": 8, "assigned_to": ["Security-Engineer", "Platform-Engineer"], "hours": 28},
        {"sprint_id": "sprint_006", "title": "Implement resource optimization with Kubecost analytics", "description": "Deploy Kubecost for real-time cloud cost monitoring, break down costs by namespace/pod/service, identify idle resources and over-provisioned workloads, generate cost optimization recommendations report.", "status": "in_progress", "sp": 8, "assigned_to": ["DevOps-Engineer-2", "Cloud-Architect"], "hours": 20},
        {"sprint_id": "sprint_006", "title": "Configure image registry scanning with automated remediation", "description": "Enable automatic image rescanning on Harbor registry, implement policy enforcement to block vulnerable images (CVSS >7), set up automated remediation for non-critical vulnerabilities, create SLA for critical patch deployment.", "status": "in_progress", "sp": 5, "assigned_to": ["Security-Engineer"], "hours": 12},
        {"sprint_id": "sprint_006", "title": "Implement RBAC and audit logging for cluster access", "description": "Configure Kubernetes RBAC with least-privilege service accounts, implement audit logging to capture all API calls, set up webhook to analyze suspicious access patterns, integrate with SIEM for security monitoring.", "status": "in_progress", "sp": 8, "assigned_to": ["Security-Engineer", "Platform-Engineer"], "hours": 24},
        {"sprint_id": "sprint_006", "title": "Set up backup and disaster recovery procedures", "description": "Implement Velero for cluster backup (daily snapshots to S3), test recovery procedures monthly, document RTO (4hrs) and RPO (24hrs) targets, create runbooks for disaster recovery scenarios, implement backup retention (7 days + monthly archive).", "status": "in_progress", "sp": 8, "assigned_to": ["DevOps-Engineer-1", "DevOps-Lead"], "hours": 24},
        {"sprint_id": "sprint_006", "title": "Create security hardening documentation and training", "description": "Document security best practices (container scanning, secret rotation, RBAC), create training materials for development teams, establish security checklist for deployment pipeline, implement pre-deployment security validation step.", "status": "todo", "sp": 5, "assigned_to": ["Security-Engineer", "Technical-Writer"], "hours": 12},
    ]
    
    all_items = sprint_1_items + sprint_2_items + sprint_3_items + sprint_4_items + sprint_5_items + sprint_6_items
    
    for idx, item in enumerate(all_items):
        item["_id"] = f"item_{idx+1:03d}"
        item["created_at"] = datetime.now()
        db.backlog_items.insert_one(item)
    
    print(f"✓ Created {len(all_items)} backlog items across 6 sprints")
    return all_items

def main():
    """Main seed function"""
    print("\n🌱 Seeding Complex Dataset: Cloud-Native Microservices Platform\n")
    
    clear_existing_data()
    space_id = seed_space()
    sprints = seed_sprints(space_id)
    items = seed_backlog_items(space_id, sprints)
    
    print(f"\n✅ Dataset seeded successfully!")
    print(f"   Space: Cloud-Native Microservices Platform")
    print(f"   Sprints: {len(sprints)} (5 completed, 1 active)")
    print(f"   Backlog Items: {len(items)} total")
    print(f"   Total Story Points: {sum(item.get('sp', 0) for item in items)} SP")
    print(f"   Active Sprint (Sprint 6): April 27 - May 11, 2026 (Currently mid-sprint)")
    print(f"\n🚀 Dataset ready for sprint impact prediction testing!\n")

if __name__ == "__main__":
    main()
