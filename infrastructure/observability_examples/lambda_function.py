"""
Example Lambda function demonstrating ADR-015 JSON logging integration
with CloudWatch observability infrastructure (ADR-018).

This example shows how to:
1. Configure JSON logging per ADR-015
2. Use the IAM role created by the observability infrastructure  
3. Log performance metrics for CloudWatch extraction
4. Handle errors with proper logging
"""

import json
import logging
import time
from typing import Any, Dict

# Configure JSON logging per ADR-015
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Example Lambda handler with proper observability integration.
    
    This function demonstrates:
    - Start/end timing for duration_in_seconds
    - Records processed counting for records_processed  
    - Error handling with structured logging
    - Correlation ID tracking
    """
    start_time = time.time()
    correlation_id = context.aws_request_id
    
    # Log job start
    logger.info(json.dumps({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "level": "INFO",
        "message": "Data pipeline job started",
        "job_name": "example_data_processor",
        "correlation_id": correlation_id,
        "function_name": context.function_name,
        "input_records": len(event.get("records", []))
    }))
    
    try:
        # Simulate data processing
        records = event.get("records", [])
        processed_records = process_data_records(records, correlation_id)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log successful completion with ADR-015 required fields
        logger.info(json.dumps({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": "INFO",
            "message": "Data pipeline job completed successfully",
            "job_name": "example_data_processor",
            "duration_in_seconds": round(duration, 3),
            "records_processed": len(processed_records),
            "correlation_id": correlation_id,
            "function_name": context.function_name
        }))
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Success",
                "records_processed": len(processed_records),
                "duration_seconds": round(duration, 3)
            })
        }
        
    except Exception as e:
        # Calculate duration for failed execution
        duration = time.time() - start_time
        
        # Log error with structured format
        logger.error(json.dumps({
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "level": "ERROR",
            "message": f"Data pipeline job failed: {str(e)}",
            "job_name": "example_data_processor",
            "duration_in_seconds": round(duration, 3),
            "records_processed": 0,  # No records processed due to failure
            "correlation_id": correlation_id,
            "function_name": context.function_name,
            "error_type": type(e).__name__
        }))
        
        # Re-raise to trigger Lambda error handling
        raise


def process_data_records(records: list, correlation_id: str) -> list:
    """
    Example data processing function with logging.
    
    Args:
        records: List of data records to process
        correlation_id: Correlation ID for tracing
        
    Returns:
        List of processed records
    """
    processed = []
    
    for i, record in enumerate(records):
        try:
            # Simulate record processing
            processed_record = {
                "id": record.get("id", f"record_{i}"),
                "processed_at": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "correlation_id": correlation_id
            }
            processed.append(processed_record)
            
            # Log progress for large batches
            if len(records) > 100 and (i + 1) % 50 == 0:
                logger.info(json.dumps({
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                    "level": "INFO", 
                    "message": f"Processing progress: {i + 1}/{len(records)} records",
                    "job_name": "example_data_processor",
                    "correlation_id": correlation_id,
                    "progress_percent": round(((i + 1) / len(records)) * 100, 1)
                }))
                
        except Exception as e:
            # Log record-level errors but continue processing
            logger.warning(json.dumps({
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
                "level": "WARNING",
                "message": f"Failed to process record {i}: {str(e)}",
                "job_name": "example_data_processor", 
                "correlation_id": correlation_id,
                "record_id": record.get("id", f"record_{i}")
            }))
    
    return processed


# Example Terraform configuration for this Lambda function
TERRAFORM_EXAMPLE = """
# Example Lambda function using the observability infrastructure

resource "aws_lambda_function" "example_data_processor" {
  filename         = "example_lambda.zip"
  function_name    = "hoopstat-haus-example-data-processor"
  role            = module.observability.lambda_logging_role_arn
  handler         = "lambda_function.lambda_handler"
  runtime         = "python3.12"
  timeout         = 900  # 15 minutes
  
  environment {
    variables = {
      LOG_LEVEL = "INFO"
    }
  }

  # CloudWatch logs configuration
  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  tags = {
    Environment = "production"
    Purpose     = "data-processing"
  }
}

# CloudWatch log group for this specific Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/hoopstat-haus-example-data-processor"
  retention_in_days = 30
  
  tags = {
    Lambda = aws_lambda_function.example_data_processor.function_name
  }
}

# Example usage of observability module
module "observability" {
  source = "./infrastructure/observability"
  
  aws_region   = "us-east-1"
  alert_email  = "alerts@example.com"
}
"""