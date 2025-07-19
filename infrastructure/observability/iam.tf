# IAM role for Lambda functions to write to CloudWatch logs
resource "aws_iam_role" "lambda_logging" {
  name = "${var.project_name}-lambda-logging"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Purpose = "Lambda CloudWatch logging permissions"
  }
}

# IAM policy for Lambda CloudWatch logging
resource "aws_iam_policy" "lambda_logging" {
  name        = "${var.project_name}-lambda-logging"
  description = "IAM policy for Lambda function CloudWatch logging"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = [
          "${aws_cloudwatch_log_group.applications.arn}:*",
          "${aws_cloudwatch_log_group.data_pipeline.arn}:*"
        ]
      }
    ]
  })
}

# Attach the policy to the role
resource "aws_iam_role_policy_attachment" "lambda_logging" {
  role       = aws_iam_role.lambda_logging.name
  policy_arn = aws_iam_policy.lambda_logging.arn
}

# Attach AWS managed basic execution role
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_logging.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}