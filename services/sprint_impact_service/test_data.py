#!/usr/bin/env python3
"""
Test Data Generator for Sprint Impact Service
Generates realistic project data for 2 spaces with:
- Multiple completed sprints (for velocity/burndown visualization)
- One active sprint (mid-sprint with items in various states)
- Realistic story points, priorities, and team assignments
- Fully descriptive titles and descriptions

Usage:
    python test_data.py
    
This will connect to MongoDB and populate test data.
"""

import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")
DATABASE_NAME = "agile-tool"

# Realistic project data for 2 spaces
SPACES = [
    {
        "name": "E-Commerce Platform Enhancement",
        "description": (
            "Build and enhance the e-commerce platform with modern payment integration, "
            "inventory management, and customer analytics. Focus on scalability and user experience."
        ),
        "max_assignees": 8,
        "focus_hours_per_day": 6.5,
        "risk_appetite": "Standard"
    },
    {
        "name": "Real-Time Analytics Dashboard",
        "description": (
            "Develop a real-time analytics dashboard for monitoring business metrics, "
            "generating insights, and creating data-driven reports for stakeholders."
        ),
        "max_assignees": 6,
        "focus_hours_per_day": 7.0,
        "risk_appetite": "Standard"
    }
]

# E-Commerce Platform sprints (4 completed + 1 active)
ECOMMERCE_SPRINTS = [
    {
        "name": "Sprint 1: Payment Gateway Integration",
        "goal": "Integrate Stripe and PayPal payment processors with full webhook support",
        "duration_type": "2 Weeks",
        "status": "Completed",
        "start_date": (datetime.now() - timedelta(days=70)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=56)).strftime("%Y-%m-%d"),
        "assignees": [1, 2, 3],
        "items": [
            {"title": "Design payment processing architecture", "description": "Create technical design document for payment flow with security best practices, PCI compliance requirements, and error handling mechanisms", "type": "Story", "priority": "High", "story_points": 8, "status": "Done"},
            {"title": "Implement Stripe API integration", "description": "Integrate Stripe SDK, implement checkout flow, handle payment confirmations, and set up error handling for declined cards", "type": "Story", "priority": "High", "story_points": 13, "status": "Done"},
            {"title": "Add PayPal payment support", "description": "Implement PayPal OAuth flow, handle payment confirmations, and ensure consistency with Stripe integration", "type": "Story", "priority": "High", "story_points": 10, "status": "Done"},
            {"title": "Setup webhook handlers for payment events", "description": "Create webhook endpoints for payment confirmations, refunds, disputes, and setup proper logging and monitoring", "type": "Task", "priority": "Medium", "story_points": 5, "status": "Done"},
            {"title": "Write payment integration tests", "description": "Create comprehensive unit and integration tests for payment flows, error scenarios, and webhook handling", "type": "Task", "priority": "Medium", "story_points": 5, "status": "Done"},
            {"title": "Fix race condition in payment confirmation", "description": "Resolve race condition where multiple webhook calls caused duplicate transaction entries in database", "type": "Bug", "priority": "High", "story_points": 3, "status": "Done"},
        ]
    },
    {
        "name": "Sprint 2: Inventory Management System",
        "goal": "Build complete inventory tracking with real-time stock updates and alerts",
        "duration_type": "2 Weeks",
        "status": "Completed",
        "start_date": (datetime.now() - timedelta(days=56)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=42)).strftime("%Y-%m-%d"),
        "assignees": [2, 3, 4, 5],
        "items": [
            {"title": "Design inventory database schema", "description": "Create normalized database schema for products, stock levels, warehouses, and inventory transactions with proper indexing", "type": "Story", "priority": "High", "story_points": 5, "status": "Done"},
            {"title": "Implement real-time inventory tracking", "description": "Build inventory update system with websocket support for live stock updates across all platforms", "type": "Story", "priority": "High", "story_points": 13, "status": "Done"},
            {"title": "Add low stock alert system", "description": "Create alert mechanism when stock falls below threshold, notify warehouse team, and integrate with order management", "type": "Story", "priority": "Medium", "story_points": 8, "status": "Done"},
            {"title": "Build inventory management dashboard", "description": "Create admin dashboard showing real-time inventory, stock movements, and warehouse distribution with filters and search", "type": "Story", "priority": "Medium", "story_points": 10, "status": "Done"},
            {"title": "Test inventory update performance", "description": "Load testing for concurrent inventory updates, verify data consistency, and optimize database queries", "type": "Task", "priority": "Medium", "story_points": 5, "status": "Done"},
        ]
    },
    {
        "name": "Sprint 3: User Recommendation Engine",
        "goal": "Implement AI-powered product recommendations based on browsing and purchase history",
        "duration_type": "2 Weeks",
        "status": "Completed",
        "start_date": (datetime.now() - timedelta(days=42)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d"),
        "assignees": [1, 2, 6],
        "items": [
            {"title": "Collect and normalize user behavior data", "description": "Build data pipeline to collect browsing history, click events, and purchase data with proper anonymization", "type": "Story", "priority": "High", "story_points": 8, "status": "Done"},
            {"title": "Develop recommendation algorithm", "description": "Implement collaborative filtering and content-based recommendation algorithms using scikit-learn and optimize for accuracy", "type": "Story", "priority": "High", "story_points": 13, "status": "Done"},
            {"title": "API endpoint for product recommendations", "description": "Create RESTful API that returns personalized product recommendations with relevance scores and explanation", "type": "Story", "priority": "Medium", "story_points": 8, "status": "Done"},
            {"title": "Frontend widget for recommendations", "description": "Build responsive recommendation widget for product pages showing top recommendations with images and ratings", "type": "Story", "priority": "Medium", "story_points": 8, "status": "Done"},
            {"title": "Monitor recommendation accuracy metrics", "description": "Setup tracking for click-through rates, conversion rates, and A/B test results for recommendation quality", "type": "Task", "priority": "Low", "story_points": 5, "status": "Done"},
        ]
    },
    {
        "name": "Sprint 4: Mobile App Optimization",
        "goal": "Optimize mobile app performance and improve user experience on slow networks",
        "duration_type": "2 Weeks",
        "status": "Completed",
        "start_date": (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d"),
        "assignees": [1, 4, 5, 7],
        "items": [
            {"title": "Implement image lazy loading and optimization", "description": "Add lazy loading for product images, implement responsive images, and optimize file sizes for mobile networks", "type": "Story", "priority": "High", "story_points": 8, "status": "Done"},
            {"title": "Setup service worker for offline support", "description": "Configure service worker to cache critical assets, enable offline browsing for previously viewed products", "type": "Story", "priority": "High", "story_points": 10, "status": "Done"},
            {"title": "Reduce app bundle size", "description": "Analyze and optimize JavaScript bundle, remove unused dependencies, implement code splitting and lazy routes", "type": "Story", "priority": "Medium", "story_points": 8, "status": "Done"},
            {"title": "Optimize database queries for mobile", "description": "Reduce number of queries, implement query batching, and add caching layer for frequently accessed data", "type": "Story", "priority": "Medium", "story_points": 5, "status": "Done"},
            {"title": "Performance monitoring on production", "description": "Setup Sentry and performance monitoring tools to track mobile app metrics and identify bottlenecks", "type": "Task", "priority": "Medium", "story_points": 5, "status": "Done"},
        ]
    },
    {
        "name": "Sprint 5: Cart and Checkout Improvements",
        "goal": "Reduce checkout abandonment and improve payment success rate",
        "duration_type": "2 Weeks",
        "status": "Active",
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "assignees": [2, 3, 5, 8],
        "items": [
            {
                "title": "Implement one-click checkout for returning customers",
                "description": (
                    "Enable stored payment methods and addresses for returning customers, "
                    "implement one-click checkout reducing checkout steps from 5 to 2, "
                    "and add Apple Pay and Google Pay support"
                ),
                "type": "Story",
                "priority": "High",
                "story_points": 13,
                "status": "In Progress"
            },
            {
                "title": "Add cart recovery email campaign",
                "description": (
                    "Create automated email campaign for abandoned carts sent at 1 hour and 24 hours, "
                    "include product images and personalized discount codes, and track recovery metrics"
                ),
                "type": "Story",
                "priority": "High",
                "story_points": 8,
                "status": "In Review"
            },
            {
                "title": "Implement real-time inventory checks during checkout",
                "description": (
                    "Verify product availability before payment processing, handle out-of-stock scenarios gracefully, "
                    "and prevent overselling with distributed locking"
                ),
                "type": "Story",
                "priority": "Medium",
                "story_points": 10,
                "status": "To Do"
            },
            {
                "title": "Add promo code application UI improvements",
                "description": (
                    "Create better UX for promo code application with real-time validation, "
                    "show discount amount before checkout, and suggest applicable promo codes"
                ),
                "type": "Story",
                "priority": "Medium",
                "story_points": 5,
                "status": "Done"
            },
            {
                "title": "Setup transaction logging and audit trail",
                "description": (
                    "Implement comprehensive logging for all transactions including failed attempts, "
                    "create audit trail for compliance, and setup alerts for suspicious patterns"
                ),
                "type": "Task",
                "priority": "High",
                "story_points": 8,
                "status": "In Progress"
            },
            {
                "title": "Fix payment timeout issue on slow networks",
                "description": (
                    "Resolve issue where payments timeout after 30 seconds on 3G networks, "
                    "implement retry logic with exponential backoff, and improve timeout messaging"
                ),
                "type": "Bug",
                "priority": "Critical",
                "story_points": 5,
                "status": "Done"
            },
        ]
    }
]

# Real-Time Analytics Dashboard sprints (4 completed + 1 active)
ANALYTICS_SPRINTS = [
    {
        "name": "Sprint 1: Data Aggregation Pipeline",
        "goal": "Build scalable data pipeline to collect and aggregate business metrics",
        "duration_type": "2 Weeks",
        "status": "Completed",
        "start_date": (datetime.now() - timedelta(days=70)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=56)).strftime("%Y-%m-%d"),
        "assignees": [1, 2, 9],
        "items": [
            {"title": "Setup Apache Kafka message queue", "description": "Configure Kafka cluster with proper partitioning, replication, and retention policies for high-throughput event streaming", "type": "Story", "priority": "High", "story_points": 10, "status": "Done"},
            {"title": "Create event schema and validation", "description": "Define Avro schemas for all business events (sales, users, inventory), implement schema registry, and add validation", "type": "Story", "priority": "High", "story_points": 5, "status": "Done"},
            {"title": "Build event producer service", "description": "Create service to emit events from main application with retry logic and dead letter queue handling", "type": "Story", "priority": "High", "story_points": 8, "status": "Done"},
            {"title": "Implement data transformation pipelines", "description": "Build Apache Spark jobs to transform raw events into cleaned data for analytics consumption", "type": "Story", "priority": "Medium", "story_points": 13, "status": "Done"},
            {"title": "Setup error handling and monitoring", "description": "Implement comprehensive logging, alerting for pipeline failures, and automatic recovery mechanisms", "type": "Task", "priority": "Medium", "story_points": 5, "status": "Done"},
        ]
    },
    {
        "name": "Sprint 2: Real-Time Dashboard Backend",
        "goal": "Create WebSocket API for real-time metric updates",
        "duration_type": "2 Weeks",
        "status": "Completed",
        "start_date": (datetime.now() - timedelta(days=56)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=42)).strftime("%Y-%m-%d"),
        "assignees": [2, 3, 10],
        "items": [
            {"title": "Design real-time metrics architecture", "description": "Create architecture for real-time metric calculation including aggregation windows and update frequencies", "type": "Story", "priority": "High", "story_points": 5, "status": "Done"},
            {"title": "Implement WebSocket server for metrics", "description": "Build Node.js/Python WebSocket server with connection pooling, message routing, and client subscriptions", "type": "Story", "priority": "High", "story_points": 13, "status": "Done"},
            {"title": "Create metric calculation engine", "description": "Implement engine for calculating KPIs like revenue, user count, conversion rate with rolling windows", "type": "Story", "priority": "High", "story_points": 10, "status": "Done"},
            {"title": "Add caching layer with Redis", "description": "Implement Redis caching for frequently accessed metrics to reduce database load and improve response time", "type": "Story", "priority": "Medium", "story_points": 8, "status": "Done"},
            {"title": "Implement access control and permissions", "description": "Add role-based access control so users see only metrics relevant to their department", "type": "Task", "priority": "Medium", "story_points": 5, "status": "Done"},
        ]
    },
    {
        "name": "Sprint 3: Frontend Dashboard UI",
        "goal": "Build responsive dashboard with interactive charts and filters",
        "duration_type": "2 Weeks",
        "status": "Completed",
        "start_date": (datetime.now() - timedelta(days=42)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d"),
        "assignees": [4, 5, 11],
        "items": [
            {"title": "Create React component library for charts", "description": "Build reusable chart components using D3.js and Recharts for line, bar, pie charts with animations", "type": "Story", "priority": "High", "story_points": 10, "status": "Done"},
            {"title": "Implement dashboard layout and grid system", "description": "Create responsive grid layout with draggable widgets allowing customization of dashboard appearance", "type": "Story", "priority": "High", "story_points": 8, "status": "Done"},
            {"title": "Add real-time metric visualization", "description": "Display real-time metrics with smooth updates, animated transitions, and color-coded KPI indicators", "type": "Story", "priority": "High", "story_points": 13, "status": "Done"},
            {"title": "Build time range and filter controls", "description": "Create date range picker, dimension filters, and saved view management for easy metric exploration", "type": "Story", "priority": "Medium", "story_points": 8, "status": "Done"},
            {"title": "Performance optimization for large datasets", "description": "Implement virtual scrolling, data sampling, and request debouncing for smooth interaction with large data", "type": "Task", "priority": "Medium", "story_points": 5, "status": "Done"},
        ]
    },
    {
        "name": "Sprint 4: Alerting and Notifications",
        "goal": "Implement intelligent alerting for anomalies and threshold violations",
        "duration_type": "2 Weeks",
        "status": "Completed",
        "start_date": (datetime.now() - timedelta(days=28)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d"),
        "assignees": [3, 6, 9, 10],
        "items": [
            {"title": "Design alert rule engine", "description": "Create rule engine supporting threshold, anomaly detection, and trend-based alerts with multiple condition types", "type": "Story", "priority": "High", "story_points": 13, "status": "Done"},
            {"title": "Implement anomaly detection using machine learning", "description": "Use isolation forests and statistical methods to detect unusual patterns in metrics automatically", "type": "Story", "priority": "High", "story_points": 10, "status": "Done"},
            {"title": "Add notification channels", "description": "Support multiple notification channels including email, Slack, PagerDuty, and SMS for alert delivery", "type": "Story", "priority": "Medium", "story_points": 8, "status": "Done"},
            {"title": "Create alert history and acknowledgment", "description": "Log all alerts, allow users to acknowledge alerts, and track alert resolution time", "type": "Story", "priority": "Medium", "story_points": 5, "status": "Done"},
            {"title": "Implement alert suppression and grouping", "description": "Group related alerts together and suppress duplicate alerts within time windows to reduce noise", "type": "Task", "priority": "Low", "story_points": 5, "status": "Done"},
        ]
    },
    {
        "name": "Sprint 6: Custom Reports and Exports",
        "goal": "Enable users to create custom reports and export data",
        "duration_type": "2 Weeks",
        "status": "Active",
        "start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
        "end_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
        "assignees": [1, 4, 11, 12],
        "items": [
            {
                "title": "Build custom report builder UI",
                "description": (
                    "Create intuitive report builder allowing selection of metrics, dimensions, filters, "
                    "visualization type, and save reports for reuse"
                ),
                "type": "Story",
                "priority": "High",
                "story_points": 13,
                "status": "In Progress"
            },
            {
                "title": "Implement data export to CSV and Excel",
                "description": (
                    "Support exporting dashboard data to CSV and Excel formats with proper formatting, "
                    "include headers and calculated totals"
                ),
                "type": "Story",
                "priority": "High",
                "story_points": 8,
                "status": "In Review"
            },
            {
                "title": "Create scheduled report generation",
                "description": (
                    "Enable scheduling reports to run daily, weekly, or monthly and deliver via email "
                    "with snapshots and comparisons to previous periods"
                ),
                "type": "Story",
                "priority": "Medium",
                "story_points": 10,
                "status": "To Do"
            },
            {
                "title": "Add PDF generation for reports",
                "description": (
                    "Implement server-side PDF generation with charts, tables, and branding, "
                    "support multiple page layouts"
                ),
                "type": "Story",
                "priority": "Medium",
                "story_points": 8,
                "status": "Done"
            },
            {
                "title": "Implement report versioning and history",
                "description": (
                    "Track changes to reports, maintain version history, and allow reverting to previous versions"
                ),
                "type": "Task",
                "priority": "Low",
                "story_points": 5,
                "status": "In Progress"
            },
            {
                "title": "Fix Excel export formatting for special characters",
                "description": (
                    "Resolve issue where special characters were not being encoded properly in Excel exports, "
                    "affecting data integrity and readability"
                ),
                "type": "Bug",
                "priority": "Medium",
                "story_points": 3,
                "status": "Done"
            },
        ]
    }
]


async def populate_test_data():
    """Connect to MongoDB and populate test data"""
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DATABASE_NAME]
    
    try:
        print("Connecting to MongoDB...")
        await client.admin.command('ping')
        print("✓ Connected to MongoDB")
        
        # Clear existing data
        print("\nClearing existing test data...")
        await db.spaces.delete_many({})
        await db.sprints.delete_many({})
        await db.backlog_items.delete_many({})
        print("✓ Cleared existing data")
        
        # Create spaces
        print("\nCreating spaces...")
        space_ids = []
        for space in SPACES:
            result = await db.spaces.insert_one({
                "name": space["name"],
                "description": space["description"],
                "max_assignees": space["max_assignees"],
                "focus_hours_per_day": space["focus_hours_per_day"],
                "risk_appetite": space["risk_appetite"],
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            })
            space_ids.append(result.inserted_id)
            print(f"  ✓ {space['name']}")
        
        # Create sprints and items for E-Commerce
        print("\nPopulating E-Commerce Platform sprints...")
        sprint_count = 0
        item_count = 0
        for sprint_data in ECOMMERCE_SPRINTS:
            items = sprint_data.pop("items")
            sprint_result = await db.sprints.insert_one({
                **sprint_data,
                "space_id": str(space_ids[0]),
                "assignees": sprint_data.get("assignees", []),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            })
            sprint_id = sprint_result.inserted_id
            sprint_count += 1
            
            # Create backlog items
            for item_data in items:
                await db.backlog_items.insert_one({
                    "title": item_data["title"],
                    "description": item_data["description"],
                    "type": item_data["type"],
                    "priority": item_data["priority"],
                    "story_points": item_data["story_points"],
                    "status": item_data["status"],
                    "space_id": str(space_ids[0]),
                    "sprint_id": str(sprint_id),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                })
                item_count += 1
            
            print(f"  ✓ {sprint_data['name']} ({len(items)} items)")
        
        # Create sprints and items for Analytics
        print("\nPopulating Analytics Dashboard sprints...")
        for sprint_data in ANALYTICS_SPRINTS:
            items = sprint_data.pop("items")
            sprint_result = await db.sprints.insert_one({
                **sprint_data,
                "space_id": str(space_ids[1]),
                "assignees": sprint_data.get("assignees", []),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            })
            sprint_id = sprint_result.inserted_id
            sprint_count += 1
            
            # Create backlog items
            for item_data in items:
                await db.backlog_items.insert_one({
                    "title": item_data["title"],
                    "description": item_data["description"],
                    "type": item_data["type"],
                    "priority": item_data["priority"],
                    "story_points": item_data["story_points"],
                    "status": item_data["status"],
                    "space_id": str(space_ids[1]),
                    "sprint_id": str(sprint_id),
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                })
                item_count += 1
            
            print(f"  ✓ {sprint_data['name']} ({len(items)} items)")
        
        # Print summary
        print("\n" + "="*60)
        print("TEST DATA POPULATION COMPLETE")
        print("="*60)
        print(f"Spaces created: {len(SPACES)}")
        print(f"Sprints created: {sprint_count}")
        print(f"Backlog items created: {item_count}")
        print("\nSpaces:")
        for i, space in enumerate(SPACES, 1):
            print(f"  {i}. {space['name']}")
        print("\nYou can now:")
        print("  1. Run the application (npm run dev)")
        print("  2. Navigate to each space to see velocity and burndown charts")
        print("  3. View active sprint with items in various states")
        print("  4. Test all system features with realistic data")
        print("="*60)
        
    except Exception as e:
        print(f"Error: {e}")
        raise
    finally:
        client.close()
        print("\nMongoDB connection closed")


if __name__ == "__main__":
    asyncio.run(populate_test_data())
