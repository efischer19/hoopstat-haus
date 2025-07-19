# SNS Topics for different alert severities
resource "aws_sns_topic" "critical_alerts" {
  name = "${var.project_name}-critical-alerts"

  tags = {
    Severity = "critical"
    Purpose  = "Immediate response alerts"
  }
}

resource "aws_sns_topic" "warning_alerts" {
  name = "${var.project_name}-warning-alerts"

  tags = {
    Severity = "warning"
    Purpose  = "24-hour response alerts"
  }
}

# SNS Topic subscriptions (only if email is provided)
resource "aws_sns_topic_subscription" "critical_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.critical_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

resource "aws_sns_topic_subscription" "warning_email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.warning_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# CloudWatch Alarms for critical monitoring
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "ErrorCount"
  namespace           = "HoopstatHaus/Applications"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors application error rate"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]

  tags = {
    Severity = "critical"
    Type     = "error-rate"
  }
}

resource "aws_cloudwatch_metric_alarm" "lambda_timeout" {
  alarm_name          = "lambda-timeouts"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Maximum"
  threshold           = "900000"  # 15 minutes in milliseconds
  alarm_description   = "This metric monitors Lambda function timeouts"
  alarm_actions       = [aws_sns_topic.critical_alerts.arn]

  tags = {
    Severity = "critical"
    Type     = "timeout"
  }
}

resource "aws_cloudwatch_metric_alarm" "execution_time_anomaly" {
  alarm_name          = "execution-time-anomaly"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "ExecutionDuration"
  namespace           = "HoopstatHaus/DataPipeline"
  period              = "600"
  statistic           = "Average"
  threshold           = "300"  # 5 minutes
  alarm_description   = "This metric monitors unusually long data pipeline execution times"
  alarm_actions       = [aws_sns_topic.warning_alerts.arn]

  tags = {
    Severity = "warning"
    Type     = "performance"
  }
}