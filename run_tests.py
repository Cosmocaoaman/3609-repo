#!/usr/bin/env python
"""
Test runner script for backend testing.

This script runs all tests and generates coverage reports to verify
that we meet the 85% coverage requirement for key backend files.
"""

import os
import sys
import subprocess
import django
from django.conf import settings
from django.test.utils import get_runner

def setup_django():
    """Setup Django environment."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject.settings')
    django.setup()

def run_tests():
    """Run all tests and generate coverage report."""
    print("Running backend tests...")
    
    # Run tests with coverage
    cmd = [
        'coverage', 'run', '--source=forum,api', 
        'manage.py', 'test', 'forum.tests', 'api.tests', 'api.serializer_tests',
        '--verbosity=2'
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        if result.returncode != 0:
            print("❌ Tests failed!")
            return False
        
        print("✅ All tests passed!")
        
        # Generate coverage report
        print("\n📊 Generating coverage report...")
        coverage_cmd = ['coverage', 'report', '--show-missing']
        coverage_result = subprocess.run(coverage_cmd, capture_output=True, text=True)
        print(coverage_result.stdout)
        
        # Generate HTML coverage report
        html_cmd = ['coverage', 'html']
        subprocess.run(html_cmd, capture_output=True)
        print("📁 HTML coverage report generated in htmlcov/")
        
        return True
        
    except FileNotFoundError:
        print("❌ Coverage tool not found. Installing coverage...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'coverage'])
        return run_tests()

def check_coverage_threshold():
    """Check if coverage meets the 85% threshold."""
    try:
        result = subprocess.run(['coverage', 'report'], capture_output=True, text=True)
        lines = result.stdout.split('\n')
        
        for line in lines:
            if 'TOTAL' in line:
                # Extract percentage from line like "TOTAL                   1234    123    90%"
                parts = line.split()
                if len(parts) >= 4:
                    percentage_str = parts[-1].replace('%', '')
                    try:
                        percentage = float(percentage_str)
                        if percentage >= 85.0:
                            print(f"✅ Coverage {percentage}% meets 85% threshold!")
                            return True
                        else:
                            print(f"❌ Coverage {percentage}% below 85% threshold!")
                            return False
                    except ValueError:
                        continue
        
        print("❌ Could not parse coverage percentage")
        return False
        
    except Exception as e:
        print(f"❌ Error checking coverage: {e}")
        return False

def main():
    """Main function."""
    print("Starting backend test suite...")
    
    # Setup Django
    setup_django()
    
    # Run tests
    if not run_tests():
        sys.exit(1)
    
    # Check coverage threshold
    if not check_coverage_threshold():
        print("\nCoverage below threshold. Consider adding more tests.")
        sys.exit(1)
    
    print("\nAll tests passed and coverage requirements met!")

if __name__ == '__main__':
    main()
