#!/usr/bin/env python3
"""
Test script to validate Lambda deployment infrastructure configuration.

This script validates that the Lambda functions are properly configured
without requiring AWS credentials.
"""

import json
import subprocess
import sys
import re
from typing import Dict, Any, List


def run_command(command: List[str], cwd: str = ".") -> Dict[str, Any]:
    """Run a command and return the result."""
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        return {
            "success": True,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "stdout": e.stdout,
            "stderr": e.stderr,
            "returncode": e.returncode
        }


def test_terraform_validation() -> bool:
    """Test that Terraform configuration is valid."""
    print("🔍 Testing Terraform validation...")
    
    # Test terraform fmt
    result = run_command(["terraform", "fmt", "-check"], "../")
    if not result["success"]:
        print(f"❌ Terraform formatting check failed: {result['stderr']}")
        return False
    
    # Test terraform validate  
    result = run_command(["terraform", "validate"], "../")
    if not result["success"]:
        print(f"❌ Terraform validation failed: {result['stderr']}")
        return False
    
    print("✅ Terraform configuration is valid")
    return True


def test_lambda_configuration_syntax() -> bool:
    """Test that Lambda functions are properly configured by examining files."""
    print("🔍 Testing Lambda function configuration syntax...")
    
    # Read the main.tf file and check for Lambda functions
    try:
        with open("../main.tf", "r") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ main.tf file not found")
        return False
    
    expected_functions = [
        "bronze_ingestion",
        "mcp_server"
    ]
    
    for function in expected_functions:
        if f'resource "aws_lambda_function" "{function}"' not in content:
            print(f"❌ Lambda function {function} not found in configuration")
            return False
    
    # Check for required Lambda configuration
    required_configs = [
        'package_type',
        "image_uri",
        "timeout",
        "memory_size",
        "environment",
        "logging_config"
    ]
    
    for config in required_configs:
        if config not in content:
            print(f"❌ Required Lambda configuration '{config}' not found")
            return False
    
    print("✅ All expected Lambda functions are configured with proper syntax")
    return True


def test_iam_roles_syntax() -> bool:
    """Test that IAM roles are properly configured by examining files."""
    print("🔍 Testing IAM role configuration syntax...")
    
    try:
        with open("../main.tf", "r") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ main.tf file not found")
        return False
    
    # Check for Lambda execution role
    if 'resource "aws_iam_role" "lambda_execution"' not in content:
        print("❌ Lambda execution role not found in configuration")
        return False
    
    # Check for required permissions
    required_permissions = [
        "logs:CreateLogStream",
        "logs:PutLogEvents",
        "s3:GetObject",
        "s3:PutObject", 
        "ecr:BatchGetImage",
        "ecr:GetAuthorizationToken"
    ]
    
    for permission in required_permissions:
        if permission not in content:
            print(f"❌ Required permission '{permission}' not found")
            return False
    
    print("✅ IAM roles are properly configured")
    return True


def test_cloudwatch_integration_syntax() -> bool:
    """Test CloudWatch integration configuration by examining files."""
    print("🔍 Testing CloudWatch integration syntax...")
    
    try:
        with open("../main.tf", "r") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ main.tf file not found")
        return False
    
    # Check for CloudWatch alarms
    required_alarms = [
        "lambda_errors",
        "lambda_duration", 
        "lambda_throttles"
    ]
    
    for alarm in required_alarms:
        if f'resource "aws_cloudwatch_metric_alarm" "{alarm}"' not in content:
            print(f"❌ CloudWatch alarm '{alarm}' not found")
            return False
    
    # Check for log group configuration
    if "logging_config" not in content or "log_group" not in content:
        print("❌ Lambda CloudWatch logging configuration not found")
        return False
    
    print("✅ CloudWatch integration is properly configured")
    return True


def test_variables_configuration() -> bool:
    """Test that variables are properly configured."""
    print("🔍 Testing variables configuration...")
    
    try:
        with open("../variables.tf", "r") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ variables.tf file not found")
        return False
    
    # Check for lambda_config variable
    if 'variable "lambda_config"' not in content:
        print("❌ lambda_config variable not found")
        return False
    
    # Check for required function configurations
    required_configs = [
        "bronze_ingestion", 
        "mcp_server"
    ]
    
    for config in required_configs:
        if config not in content:
            print(f"❌ Configuration for '{config}' not found in variables")
            return False
    
    print("✅ Variables are properly configured")
    return True


def test_outputs_configuration() -> bool:
    """Test that outputs are properly configured."""
    print("🔍 Testing outputs configuration...")
    
    try:
        with open("../outputs.tf", "r") as f:
            content = f.read()
    except FileNotFoundError:
        print("❌ outputs.tf file not found")
        return False
    
    # Check for Lambda function outputs
    if 'output "lambda_functions"' not in content:
        print("❌ lambda_functions output not found")
        return False
    
    if 'output "lambda_execution_role"' not in content:
        print("❌ lambda_execution_role output not found")
        return False
    
    print("✅ Outputs are properly configured")
    return True


def main():
    """Run all tests."""
    print("🚀 Starting Lambda deployment infrastructure tests...")
    print("=" * 60)
    
    tests = [
        test_terraform_validation,
        test_lambda_configuration_syntax, 
        test_iam_roles_syntax,
        test_cloudwatch_integration_syntax,
        test_variables_configuration,
        test_outputs_configuration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed > 0:
        print("❌ Some tests failed")
        sys.exit(1)
    else:
        print("✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()