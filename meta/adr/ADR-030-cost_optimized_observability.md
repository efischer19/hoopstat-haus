---
title: "ADR-030: Cost-Optimized Observability Strategy"
status: "Accepted"
date: "2025-12-27"
supersedes: "ADR-018"
tags:
  - "observability"
  - "cloudwatch"
  - "monitoring"
  - "cost-optimization"
---

## Context

* **Problem:** The CloudWatch observability strategy defined in ADR-018 includes metric filters and alarms that incur ongoing costs. For a side project in early development with limited usage, these costs represent a significant portion of the AWS bill without providing proportional value. The current usage patterns involve infrequent manual execution of data pipelines during development, making automated alerting less critical than initially anticipated.
* **Constraints:** Must maintain basic observability for debugging and issue resolution, minimize recurring AWS costs while preserving the option to scale up monitoring in production, continue to leverage CloudWatch Logs (which are already included with Lambda), align with the single production environment strategy (ADR-012) that still requires operational visibility.

## Decision

We will **remove CloudWatch metric filters and alarms** while retaining CloudWatch Logs for basic observability. This represents a shift from proactive automated monitoring to reactive log-based debugging.

## Considered Options

1. **Remove Metric Filters and Alarms (The Chosen One):** Eliminate CloudWatch metric filters and alarms while keeping CloudWatch Logs.
   * *Pros:* Eliminates recurring costs for metric filters and alarms, CloudWatch Logs remain available for debugging at no additional cost beyond Lambda execution, JSON logging format (ADR-015) still provides structured logs for manual analysis, can be re-enabled quickly if production usage scales up, aligns with current development-focused usage patterns
   * *Cons:* No automated alerting for critical issues (timeouts, errors, performance degradation), loss of historical metric trends and dashboards, requires manual log analysis to identify problems, slower incident response time, sacrifices visibility into execution patterns and performance trends

2. **Keep Full ADR-018 Implementation:** Maintain all metric filters, alarms, and dashboards.
   * *Pros:* Comprehensive automated monitoring and alerting, proactive issue detection, historical metrics for trend analysis, production-ready observability
   * *Cons:* Ongoing costs for metric filters (~$0.50-$2 per month per metric), ongoing costs for alarms (~$0.10 per alarm per month), costs not justified by current low-volume, development-stage usage, over-engineering for current needs

3. **Selective Metric Retention:** Keep only critical high-value metrics and alarms.
   * *Pros:* Reduces costs while maintaining some automated monitoring, retains alerting for truly critical issues
   * *Cons:* Still incurs ongoing costs, requires careful selection of "critical" metrics which may change, adds complexity in maintaining partial implementation, costs may not be significantly lower than full implementation

## Consequences

* **Positive:** Eliminates recurring CloudWatch costs for metric filters and alarms (estimated $2-5 per month savings), CloudWatch Logs remain available at no additional cost for debugging, JSON logging format (ADR-015) provides structured logs that can be manually analyzed, simplified infrastructure reduces maintenance burden, observability strategy can be upgraded when production usage justifies the cost.

* **Negative:** No automated alerting for Lambda timeouts, high error rates, or performance degradation, loss of automated metric extraction from logs (duration_in_seconds, records_processed, error rates), no historical metric trends or CloudWatch dashboards, incident detection requires manual log review or user-reported issues, slower mean time to detection (MTFD) for production issues, requires manual CloudWatch Logs Insights queries for analysis.

* **Future Implications:** CloudWatch Logs with JSON formatting (ADR-015) remain the foundation for future observability enhancements, metric filters and alarms can be re-introduced via Terraform when production usage scales or funding allows, applications should continue using structured JSON logging to maintain compatibility with potential future metric extraction, manual operational runbooks should document how to query CloudWatch Logs for common debugging scenarios, consider external monitoring tools (UptimeRobot, Pingdom) for critical user-facing endpoints when they exist.

## Migration Path

* **Immediate:** Remove CloudWatch metric filter and alarm resources from Terraform infrastructure
* **Retained:** CloudWatch Logs with 30-day retention for application logs, 90-day retention for data pipeline logs per ADR-018
* **Future Re-enablement:** All metric filters and alarms are defined in Terraform and can be re-enabled by reverting this decision and re-applying infrastructure

## Alternative Monitoring Approaches

For future consideration when production usage increases:

1. **Cost-Effective External Monitoring:** Use free tier of services like UptimeRobot or Pingdom for endpoint availability monitoring
2. **Sampling-Based Metrics:** Extract metrics from a sample of logs rather than all logs to reduce costs
3. **Budget Alerts:** Set AWS Budget alerts to notify when CloudWatch costs exceed thresholds
4. **Open Source Solutions:** Consider Grafana + Loki for log aggregation if self-hosting becomes viable
