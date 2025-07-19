# CloudWatch Log Groups for different application types
resource "aws_cloudwatch_log_group" "applications" {
  name              = "/hoopstat-haus/applications"
  retention_in_days = var.log_retention_days.applications

  tags = {
    LogType = "applications"
    Purpose = "General application logging"
  }
}

resource "aws_cloudwatch_log_group" "data_pipeline" {
  name              = "/hoopstat-haus/data-pipeline"
  retention_in_days = var.log_retention_days.data_pipeline

  tags = {
    LogType = "data-pipeline"
    Purpose = "Data processing job logs with performance metrics"
  }
}

resource "aws_cloudwatch_log_group" "infrastructure" {
  name              = "/hoopstat-haus/infrastructure"
  retention_in_days = var.log_retention_days.infrastructure

  tags = {
    LogType = "infrastructure"
    Purpose = "System and infrastructure logs"
  }
}

# Metric filters to extract performance metrics from JSON logs per ADR-015
resource "aws_cloudwatch_log_metric_filter" "execution_duration" {
  name           = "execution-duration"
  log_group_name = aws_cloudwatch_log_group.data_pipeline.name
  pattern        = "[timestamp, level, message, job_name, duration_in_seconds = *, records_processed, ...]"

  metric_transformation {
    name      = "ExecutionDuration"
    namespace = "HoopstatHaus/DataPipeline"
    value     = "$duration_in_seconds"
    unit      = "Seconds"
  }
}

resource "aws_cloudwatch_log_metric_filter" "records_processed" {
  name           = "records-processed"
  log_group_name = aws_cloudwatch_log_group.data_pipeline.name
  pattern        = "[timestamp, level, message, job_name, duration_in_seconds, records_processed = *, ...]"

  metric_transformation {
    name      = "RecordsProcessed"
    namespace = "HoopstatHaus/DataPipeline"
    value     = "$records_processed"
    unit      = "Count"
  }
}

resource "aws_cloudwatch_log_metric_filter" "error_count" {
  name           = "error-count"
  log_group_name = aws_cloudwatch_log_group.applications.name
  pattern        = "[timestamp, level=\"ERROR\", ...]"

  metric_transformation {
    name      = "ErrorCount"
    namespace = "HoopstatHaus/Applications"
    value     = "1"
    unit      = "Count"
  }
}