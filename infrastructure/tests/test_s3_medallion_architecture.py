import subprocess
import json
from pathlib import Path

INFRASTRUCTURE_DIR = Path(__file__).parent.parent

class TestS3MedallionArchitecture:
    """Test suite for S3 Medallion Architecture (Bronze/Silver/Gold) implementation."""
    
    def test_medallion_buckets_defined(self):
        """Verify Bronze, Silver, and Gold S3 buckets are defined."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Check that all three medallion buckets are defined
        medallion_buckets = ["bronze", "silver", "gold"]
        for bucket in medallion_buckets:
            assert f'aws_s3_bucket" "{bucket}"' in content, \
                f"S3 bucket {bucket} not defined"
            
        # Check bucket tags include DataLayer
        assert 'DataLayer = "bronze"' in content, "Bronze bucket missing DataLayer tag"
        assert 'DataLayer = "silver"' in content, "Silver bucket missing DataLayer tag"
        assert 'DataLayer = "gold"' in content, "Gold bucket missing DataLayer tag"

    def test_bucket_encryption_configured(self):
        """Verify all medallion buckets have encryption configured."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Check encryption configuration for all medallion buckets
        medallion_buckets = ["bronze", "silver", "gold"]
        for bucket in medallion_buckets:
            assert f'aws_s3_bucket_server_side_encryption_configuration" "{bucket}"' in content, \
                f"Encryption not configured for {bucket} bucket"
            
        # Check AES256 encryption is used
        assert content.count('sse_algorithm = "AES256"') >= 4, \
            "AES256 encryption not configured for all buckets"
            
    def test_bucket_versioning_enabled(self):
        """Verify versioning is enabled for all medallion buckets."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Check versioning configuration for all medallion buckets
        medallion_buckets = ["bronze", "silver", "gold"]
        for bucket in medallion_buckets:
            assert f'aws_s3_bucket_versioning" "{bucket}"' in content, \
                f"Versioning not configured for {bucket} bucket"
                
        # Check versioning is enabled
        assert content.count('status = "Enabled"') >= 4, \
            "Versioning not enabled for all buckets"

    def test_public_access_blocked(self):
        """Verify public access is blocked for all medallion buckets."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Check public access block for all medallion buckets
        medallion_buckets = ["bronze", "silver", "gold"]
        for bucket in medallion_buckets:
            assert f'aws_s3_bucket_public_access_block" "{bucket}"' in content, \
                f"Public access block not configured for {bucket} bucket"
                
        # Check all public access settings are true
        assert content.count("block_public_acls       = true") >= 4, \
            "Public ACLs not blocked for all buckets"
        assert content.count("block_public_policy     = true") >= 4, \
            "Public policies not blocked for all buckets"

    def test_lifecycle_policies_configured(self):
        """Verify lifecycle policies are configured for cost optimization."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Check lifecycle configuration for all medallion buckets
        medallion_buckets = ["bronze", "silver", "gold"]
        for bucket in medallion_buckets:
            assert f'aws_s3_bucket_lifecycle_configuration" "{bucket}"' in content, \
                f"Lifecycle policy not configured for {bucket} bucket"
                
        # Check specific lifecycle rules exist
        assert "INTELLIGENT_TIERING" in content, "Intelligent Tiering not configured for Bronze"
        assert "STANDARD_IA" in content, "Standard IA transition not configured"
        assert "GLACIER" in content, "Glacier transition not configured"
        assert "abort_incomplete_multipart_upload" in content, \
            "Incomplete multipart upload cleanup not configured"

    def test_data_layer_iam_roles_defined(self):
        """Verify IAM roles are defined for each data layer."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Check data layer access roles
        expected_roles = [
            "bronze_layer_access",
            "silver_layer_access", 
            "gold_layer_access",
            "mcp_server_access"
        ]
        
        for role in expected_roles:
            assert f'aws_iam_role" "{role}"' in content, \
                f"IAM role {role} not defined"
            assert f'aws_iam_role_policy" "{role}"' in content, \
                f"IAM policy for {role} not defined"

    def test_least_privilege_access_policies(self):
        """Verify IAM policies follow least-privilege principle."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Bronze layer should only write to bronze bucket
        # Find the bronze layer policy section
        bronze_policy_start = content.find('${var.project_name}-bronze-layer-policy')
        bronze_policy_end = content.find('})', bronze_policy_start)
        bronze_policy = content[bronze_policy_start:bronze_policy_end] if bronze_policy_start != -1 else ""
        
        assert "s3:PutObject" in bronze_policy, "Bronze layer missing PutObject permission"
        assert "s3:GetObject" not in bronze_policy, "Bronze layer should not have GetObject permission"
        
        # Silver layer should read bronze, write silver
        silver_policy_start = content.find('${var.project_name}-silver-layer-policy')
        silver_policy_end = content.find('})', silver_policy_start)
        silver_policy = content[silver_policy_start:silver_policy_end] if silver_policy_start != -1 else ""
        
        assert "bronze.arn" in silver_policy, "Silver layer should read from Bronze bucket"
        assert "silver.arn" in silver_policy, "Silver layer should write to Silver bucket"
        
        # MCP server should be read-only on gold
        mcp_policy_start = content.find('${var.project_name}-mcp-server-policy')
        mcp_policy_end = content.find('})', mcp_policy_start)
        mcp_policy = content[mcp_policy_start:mcp_policy_end] if mcp_policy_start != -1 else ""
        
        assert "s3:GetObject" in mcp_policy, "MCP server missing GetObject permission"
        assert "s3:PutObject" not in mcp_policy, "MCP server should not have PutObject permission"

    def test_s3_access_logging_configured(self):
        """Verify S3 access logging is configured for monitoring."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Check access logs bucket exists
        assert 'aws_s3_bucket" "access_logs"' in content, \
            "S3 access logs bucket not defined"
            
        # Check logging configuration for all medallion buckets
        medallion_buckets = ["bronze", "silver", "gold"]
        for bucket in medallion_buckets:
            assert f'aws_s3_bucket_logging" "{bucket}"' in content, \
                f"Access logging not configured for {bucket} bucket"
                
        # Check log prefixes are different for each bucket
        assert "bronze-access-logs/" in content, "Bronze access log prefix not configured"
        assert "silver-access-logs/" in content, "Silver access log prefix not configured"  
        assert "gold-access-logs/" in content, "Gold access log prefix not configured"

    def test_cloudwatch_alarms_for_s3_monitoring(self):
        """Verify CloudWatch alarms are configured for S3 monitoring."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Check S3 error monitoring alarms
        expected_alarms = [
            "bronze-bucket-4xx-errors",
            "silver-bucket-4xx-errors",
            "gold-bucket-4xx-errors",
            "gold-bucket-high-request-rate"
        ]
        
        for alarm in expected_alarms:
            assert f'alarm_name          = "{alarm}"' in content, \
                f"CloudWatch alarm {alarm} not defined"
                
        # Check alarm uses S3 namespace
        assert 'namespace           = "AWS/S3"' in content, \
            "S3 CloudWatch alarms not using AWS/S3 namespace"

    def test_medallion_outputs_defined(self):
        """Verify Terraform outputs are defined for all medallion buckets."""
        outputs_file = INFRASTRUCTURE_DIR / "outputs.tf"
        content = outputs_file.read_text()
        
        # Check bucket outputs
        expected_bucket_outputs = [
            "bronze_bucket_name",
            "bronze_bucket_arn",
            "silver_bucket_name", 
            "silver_bucket_arn",
            "gold_bucket_name",
            "gold_bucket_arn",
            "access_logs_bucket_name",
            "access_logs_bucket_arn"
        ]
        
        for output in expected_bucket_outputs:
            assert f'output "{output}"' in content, f"Output {output} not defined"
            
        # Check IAM role outputs
        expected_role_outputs = [
            "bronze_layer_role_arn",
            "silver_layer_role_arn", 
            "gold_layer_role_arn",
            "mcp_server_role_arn"
        ]
        
        for output in expected_role_outputs:
            assert f'output "{output}"' in content, f"Output {output} not defined"

    def test_backward_compatibility_maintained(self):
        """Verify legacy bucket and outputs are maintained for backward compatibility."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        outputs_file = INFRASTRUCTURE_DIR / "outputs.tf"
        
        main_content = main_file.read_text()
        outputs_content = outputs_file.read_text()
        
        # Check legacy bucket still exists
        assert 'aws_s3_bucket" "main"' in main_content, \
            "Legacy main bucket not preserved"
        assert 'Status = "legacy"' in main_content, \
            "Legacy bucket not marked with legacy status"
            
        # Check legacy outputs still exist
        assert 'output "s3_bucket_name"' in outputs_content, \
            "Legacy s3_bucket_name output not preserved"
        assert 'output "s3_bucket_arn"' in outputs_content, \
            "Legacy s3_bucket_arn output not preserved"

    def test_terraform_syntax_validation(self):
        """Verify Terraform configuration has valid syntax."""
        main_file = INFRASTRUCTURE_DIR / "main.tf"
        content = main_file.read_text()
        
        # Basic syntax checks
        open_braces = content.count('{')
        close_braces = content.count('}')
        assert open_braces == close_braces, \
            f"Unmatched braces: {open_braces} open, {close_braces} close"
            
        # Check no obvious syntax errors
        assert 'resource "aws_s3_bucket"' in content, "S3 bucket resources not properly defined"
        assert 'resource "aws_iam_role"' in content, "IAM role resources not properly defined"
        assert 'jsonencode(' in content, "IAM policies not properly encoded"