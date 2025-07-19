---
title: "ADR-018: AWS CloudWatch Observability Strategy"
status: "Accepted"
date: "2025-07-19"
tags:
  - "observability"
  - "cloudwatch"
  - "monitoring"
  - "alerting"
---

## Context

* **Problem:** With ADR-015 establishing JSON logging standards, we need a comprehensive observability strategy to collect, monitor, and alert on application logs and metrics. The single production environment strategy requires excellent observability to quickly identify and resolve issues.
* **Constraints:** Must integrate with ADR-015 JSON logging format, leverage AWS CloudWatch per ADR-009, use Terraform per ADR-010, provide cost-effective monitoring for small-scale operations, enable automated alerting for critical issues, and support future Lambda deployments.

## Decision

We will use **AWS CloudWatch as our primary observability platform** with automated log collection, metric extraction from JSON logs, and comprehensive alerting.

## Considered Options

1. **AWS CloudWatch (The Chosen One):** Native AWS monitoring and logging service.
   * *Pros:* Seamless integration with AWS Lambda and other services, built-in metric extraction from JSON logs, comprehensive alerting capabilities, cost-effective for small to medium scale, excellent Terraform support, native log aggregation without additional infrastructure
   * *Cons:* AWS vendor lock-in, limited advanced querying compared to specialized tools, costs can scale with log volume

2. **ELK Stack (Elasticsearch, Logstash, Kibana):** Popular open-source log analysis platform.
   * *Pros:* Powerful querying and visualization capabilities, open-source with no vendor lock-in, excellent for complex log analysis
   * *Cons:* Requires significant infrastructure management overhead, higher operational complexity, more expensive for small-scale operations, doesn't align with serverless-first approach

3. **External SaaS (Datadog, New Relic, etc.):** Third-party monitoring services.
   * *Pros:* Feature-rich monitoring and alerting, minimal operational overhead, advanced analytics capabilities
   * *Cons:* Additional vendor dependency, potentially expensive for growing log volumes, data privacy concerns with external services

## Implementation Strategy

### Log Groups and Retention
- **Application Logs:** 30-day retention for general application logging
- **Data Pipeline Logs:** 90-day retention for audit and debugging of data processing jobs
- **Infrastructure Logs:** 14-day retention for system-level events

### Metric Extraction
Automated CloudWatch metric filters will extract key metrics from JSON logs per ADR-015:
- `duration_in_seconds` → Custom metric for execution time monitoring
- `records_processed` → Custom metric for throughput monitoring
- Error rates from log levels (ERROR, CRITICAL)

### Default Alarms
- **High Error Rate:** >5% errors in 5-minute period
- **Job Execution Time:** >95th percentile of historical execution time
- **Lambda Timeouts:** Any Lambda function timeout events
- **Failed Job Count:** >3 failed data pipeline jobs in 1 hour

### Alert Routing
- **Critical:** SNS topic for immediate response (Lambda timeouts, high error rates)
- **Warning:** SNS topic for investigation within 24 hours (performance degradation)
- **Info:** CloudWatch dashboard visibility only (general metrics)

## Consequences

* **Positive:** Comprehensive monitoring aligned with existing AWS infrastructure, automated metric extraction from structured logs, cost-effective solution for current scale, seamless integration with Lambda deployments, enables proactive issue detection, supports correlation tracking across services.
* **Negative:** Vendor lock-in to AWS ecosystem, limited advanced analytics compared to specialized tools, potential cost increases with log volume growth, CloudWatch query capabilities are less powerful than dedicated log analysis platforms.
* **Future Implications:** All applications must implement ADR-015 JSON logging for metric extraction, Lambda functions will automatically send logs to designated CloudWatch log groups, alerting configuration must be maintained as new services are added, monitoring costs must be tracked and optimized as the platform scales.