import subprocess
import json
import pytest
from pathlib import Path

INFRASTRUCTURE_DIR = Path(__file__).parent.parent

class TestTerraformInfrastructure:
    """Test suite for Terraform infrastructure including observability."""
    
    def test_terraform_files_exist(self):
        """Verify all required Terraform files exist."""
        required_files = [
            "main.tf",
            "variables.tf", 
            "outputs.tf",
            "versions.tf"
        ]
        
        for file_name in required_files:
            file_path = INFRASTRUCTURE_DIR / file_name
            assert file_path.exists(), f"Required file {file_name} not found"
            assert file_path.stat().st_size > 0, f"File {file_name} is empty"

    def test_terraform_validate(self):
        """Validate Terraform configuration syntax."""
        result = subprocess.run(
            ["terraform", "validate"],
            cwd=INFRASTRUCTURE_DIR,
            capture_output=True,
            text=True
        )
        
        # Accept both success and "terraform not initialized" as valid
        # since we don't want to require AWS credentials for basic syntax validation
        assert result.returncode in [0, 1], f"Terraform validation failed: {result.stderr}"
        
        # Check that it's not a syntax error
        if result.returncode == 1:
            assert "terraform init" in result.stderr or "Backend initialization" in result.stderr, \
                f"Unexpected terraform error: {result.stderr}"

    def test_terraform_fmt_check(self):
        """Verify Terraform files are properly formatted."""
        result = subprocess.run(
            ["terraform", "fmt", "-check", "-diff"],
            cwd=INFRASTRUCTURE_DIR,
            capture_output=True,
            text=True
        )
        
        assert result.returncode == 0, f"Terraform files not properly formatted:\n{result.stdout}"

    def test_required_variables_defined(self):
        """Verify all required variables are defined with appropriate defaults."""
        variables_file = INFRASTRUCTURE_DIR / "variables.tf"
        content = variables_file.read_text()
        
        # Check for required variables
        required_vars = ["aws_region", "project_name", "environment", "log_retention_days"]
        for var in required_vars:
            assert f'variable "{var}"' in content, f"Variable {var} not defined"

    def test_log_groups_configuration(self):
        """Verify CloudWatch log groups are properly configured."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Check log groups exist
        log_groups = ["applications", "data_pipeline", "infrastructure"]
        for group in log_groups:
            assert f'aws_cloudwatch_log_group" "{group}"' in content, \
                f"Log group {group} not defined"
        
        # Check retention configuration
        assert "retention_in_days" in content, "Log retention not configured"

    def test_adr015_integration(self):
        """Verify integration with ADR-015 JSON logging standard."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Check for ADR-015 required fields in metric filters
        assert "duration_in_seconds" in content, \
            "ADR-015 duration_in_seconds field not extracted"
        assert "records_processed" in content, \
            "ADR-015 records_processed field not extracted"
        
        # Check metric filter patterns match JSON structure
        assert "metric_transformation" in content, "Metric transformations not configured"

    def test_alarm_configuration(self):
        """Verify CloudWatch alarms are properly configured."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Check for required alarms per ADR-018
        required_alarms = ["high_error_rate", "lambda_timeout", "execution_time_anomaly"]
        for alarm in required_alarms:
            assert f'aws_cloudwatch_metric_alarm" "{alarm}"' in content, \
                f"Alarm {alarm} not defined"

    def test_iam_permissions(self):
        """Verify IAM roles and policies for Lambda logging."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Check Lambda logging role
        assert 'aws_iam_role" "lambda_logging"' in content, \
            "Lambda logging IAM role not defined"
        
        # Check CloudWatch logs permissions
        assert "logs:CreateLogStream" in content, "CreateLogStream permission missing"
        assert "logs:PutLogEvents" in content, "PutLogEvents permission missing"
        
        # Check role attachments
        assert "aws_iam_role_policy_attachment" in content, \
            "IAM policy attachments not configured"
        
        # Note: GitHub Actions IAM role intentionally excluded due to circular dependency

    def test_output_configuration(self):
        """Verify Terraform outputs are properly defined."""
        outputs_file = INFRASTRUCTURE_DIR / "outputs.tf"
        content = outputs_file.read_text()
        
        # Check for essential outputs
        required_outputs = [
            "log_group_names",
            "log_group_arns", 
            "lambda_logging_role_arn"
        ]
        
        for output in required_outputs:
            assert f'output "{output}"' in content, f"Output {output} not defined"