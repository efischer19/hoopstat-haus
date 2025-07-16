"""
Python Application Template for Hoopstat Haus with AWS Integration.

This template demonstrates the standard project structure, tooling setup,
and AWS integration patterns for Python applications in the Hoopstat Haus project.
"""

import json
import os
from datetime import datetime
from app.aws_config import get_aws_config, S3DataManager, verify_aws_configuration


def greet(name: str = "World") -> str:
    """
    Generate a greeting message.

    Args:
        name: The name to greet. Defaults to "World".

    Returns:
        A greeting message string.
    """
    return f"Hello, {name}! Welcome to Hoopstat Haus!"


def demonstrate_aws_integration() -> None:
    """Demonstrate AWS integration capabilities."""
    print("\n🔍 AWS Integration Demonstration")
    print("=" * 50)
    
    # Verify AWS configuration
    if not verify_aws_configuration():
        print("❌ AWS configuration is not available. Skipping AWS demo.")
        return
    
    try:
        # Load AWS configuration
        config = get_aws_config()
        print(f"✅ AWS Region: {config.aws_region}")
        print(f"✅ Connected to S3 buckets:")
        print(f"   📁 Raw Data: {config.s3_bucket_raw_data}")
        print(f"   📁 Processed Data: {config.s3_bucket_processed_data}")
        print(f"   📁 Backup: {config.s3_bucket_backup}")
        
        # Demonstrate S3 operations
        s3_manager = S3DataManager()
        
        # Create sample data
        sample_data = {
            "application": "python-app-template",
            "timestamp": datetime.now().isoformat(),
            "message": "Hello from Hoopstat Haus!",
            "version": "1.0.0"
        }
        
        # Upload to raw data bucket
        key = f"template-demo/{datetime.now().strftime('%Y-%m-%d')}/sample.json"
        print(f"\n📤 Uploading sample data to S3...")
        print(f"   Key: {key}")
        
        s3_manager.upload_raw_data(
            key=key,
            data=json.dumps(sample_data, indent=2).encode(),
            content_type="application/json"
        )
        print("✅ Upload successful!")
        
        # Download the data back
        print(f"\n📥 Downloading data from S3...")
        downloaded_data = s3_manager.download_raw_data(key)
        parsed_data = json.loads(downloaded_data.decode())
        print(f"✅ Download successful! Message: {parsed_data['message']}")
        
        # List objects in the bucket
        print(f"\n📋 Listing objects in raw data bucket...")
        objects = s3_manager.list_objects("raw", prefix="template-demo/")
        print(f"✅ Found {len(objects)} objects in template-demo/ prefix")
        
        print(f"\n🎉 AWS integration demonstration completed successfully!")
        
    except Exception as e:
        print(f"❌ AWS integration error: {e}")


def demonstrate_configuration() -> None:
    """Demonstrate configuration loading and environment variables."""
    print("\n⚙️  Configuration Demonstration")
    print("=" * 50)
    
    # Show environment variables
    aws_env_vars = [
        "AWS_REGION",
        "AWS_S3_BUCKET_RAW_DATA",
        "AWS_S3_BUCKET_PROCESSED_DATA", 
        "AWS_S3_BUCKET_BACKUP",
        "AWS_ECR_REPOSITORY"
    ]
    
    print("Environment Variables:")
    for var in aws_env_vars:
        value = os.getenv(var, "Not Set")
        status = "✅" if value != "Not Set" else "❌"
        print(f"  {status} {var}: {value}")


def main() -> None:
    """Main entry point for the application."""
    print("🏀 Hoopstat Haus Python Application Template")
    print("=" * 60)
    
    # Basic greeting
    message = greet("Hoopstat Haus Developer")
    print(message)
    print("\nThis template demonstrates:")
    print("• Standard Python project structure")
    print("• AWS integration patterns")
    print("• Configuration management")
    print("• Docker containerization")
    print("• CI/CD integration")
    
    # Demonstrate configuration
    demonstrate_configuration()
    
    # Demonstrate AWS integration if available
    demonstrate_aws_integration()
    
    print(f"\n✨ Template demonstration completed!")
    print("🚀 Ready to build amazing basketball analytics applications!")


if __name__ == "__main__":
    main()
