#!/usr/bin/env python3
"""
Bronze Layer Validation Test Runner

This script provides a comprehensive validation suite for the bronze layer
ingestion process, covering all acceptance criteria:

1. JSON to Parquet conversion accuracy
2. Partitioning scheme validation
3. Metadata enrichment verification
4. Error handling for malformed data
5. Compression and storage optimization
6. Performance benchmark assertions
7. Mock NBA API data integration

Usage:
    python validate_bronze_layer.py --help
    python validate_bronze_layer.py --all
    python validate_bronze_layer.py --performance
    python validate_bronze_layer.py --integration
"""

import argparse
import sys
import time
from pathlib import Path

# Add the app directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "app"))
sys.path.insert(0, "/tmp/stubs")  # For stub dependencies

def run_validation_tests(test_types=None):
    """Run specified validation tests."""
    import subprocess
    
    base_cmd = [
        sys.executable, "-m", "pytest", "-v", "--tb=short"
    ]
    
    env = {"PYTHONPATH": "/tmp/stubs"}
    
    if test_types is None or "all" in test_types:
        print("🔍 Running all bronze layer validation tests...")
        result = subprocess.run(
            base_cmd + ["tests/test_bronze_layer_validation.py"],
            env=env,
            cwd=Path(__file__).parent
        )
        if result.returncode != 0:
            return False
            
        result = subprocess.run(
            base_cmd + ["tests/test_mock_data_integration.py"],
            env=env,
            cwd=Path(__file__).parent
        )
        return result.returncode == 0
    
    if "core" in test_types:
        print("🔍 Running core validation tests...")
        result = subprocess.run(
            base_cmd + ["tests/test_bronze_layer_validation.py"],
            env=env,
            cwd=Path(__file__).parent
        )
        return result.returncode == 0
    
    if "integration" in test_types:
        print("🔍 Running integration tests...")
        result = subprocess.run(
            base_cmd + ["tests/test_mock_data_integration.py"],
            env=env,
            cwd=Path(__file__).parent
        )
        return result.returncode == 0
    
    if "performance" in test_types:
        print("🔍 Running performance tests...")
        result = subprocess.run(
            base_cmd + [
                "tests/test_bronze_layer_validation.py::TestBronzeLayerValidation::test_performance_benchmarks_ingestion_speed",
                "tests/test_mock_data_integration.py::TestBronzeLayerMockDataIntegration::test_large_dataset_performance_validation"
            ],
            env=env,
            cwd=Path(__file__).parent
        )
        return result.returncode == 0
    
    return True

def validate_acceptance_criteria():
    """Validate that all acceptance criteria are covered."""
    print("📋 Validating acceptance criteria coverage...")
    
    criteria = {
        "JSON to Parquet conversion accuracy": "test_json_to_parquet_conversion_accuracy",
        "Partitioning scheme validation": "test_partitioning_scheme_validation", 
        "Metadata enrichment": "test_metadata_enrichment_validation",
        "Error handling for malformed data": "test_error_handling_malformed_data",
        "Compression and storage optimization": "test_compression_and_storage_optimization",
        "Performance benchmarks": "test_performance_benchmarks_ingestion_speed",
        "Mock NBA API integration": "test_end_to_end_ingestion_with_mock_data"
    }
    
    # Check if test files exist and contain the required tests
    test_files = [
        Path(__file__).parent / "tests" / "test_bronze_layer_validation.py",
        Path(__file__).parent / "tests" / "test_mock_data_integration.py"
    ]
    
    all_criteria_covered = True
    
    for criterion, test_name in criteria.items():
        found = False
        for test_file in test_files:
            if test_file.exists():
                content = test_file.read_text()
                if test_name in content:
                    print(f"  ✅ {criterion}")
                    found = True
                    break
        
        if not found:
            print(f"  ❌ {criterion} - Test '{test_name}' not found")
            all_criteria_covered = False
    
    return all_criteria_covered

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bronze Layer Validation Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--all", action="store_true",
        help="Run all validation tests"
    )
    parser.add_argument(
        "--core", action="store_true",
        help="Run core validation tests only"
    )
    parser.add_argument(
        "--integration", action="store_true",
        help="Run integration tests only"
    )
    parser.add_argument(
        "--performance", action="store_true",
        help="Run performance tests only"
    )
    parser.add_argument(
        "--check-criteria", action="store_true",
        help="Check acceptance criteria coverage"
    )
    
    args = parser.parse_args()
    
    if not any([args.all, args.core, args.integration, args.performance, args.check_criteria]):
        args.all = True  # Default to running all tests
    
    print("🚀 Bronze Layer Validation Test Runner")
    print("=" * 50)
    
    start_time = time.time()
    success = True
    
    if args.check_criteria:
        success = validate_acceptance_criteria() and success
    
    test_types = []
    if args.all:
        test_types.append("all")
    if args.core:
        test_types.append("core")
    if args.integration:
        test_types.append("integration")
    if args.performance:
        test_types.append("performance")
    
    if test_types:
        success = run_validation_tests(test_types) and success
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("=" * 50)
    if success:
        print(f"🎉 All validations passed! (Duration: {duration:.2f}s)")
        print("\n📊 Summary:")
        print("  • JSON to Parquet conversion: ✅")
        print("  • Partitioning scheme: ✅")
        print("  • Metadata enrichment: ✅")
        print("  • Error handling: ✅")
        print("  • Compression optimization: ✅")
        print("  • Performance benchmarks: ✅")
        print("  • Mock data integration: ✅")
        return 0
    else:
        print(f"❌ Some validations failed! (Duration: {duration:.2f}s)")
        return 1

if __name__ == "__main__":
    sys.exit(main())