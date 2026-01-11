#!/usr/bin/env python3
"""
Test runner script for Home Inventory Application.
Run this to execute all tests with coverage reporting.
"""

import subprocess
import sys
import os

def main():
    # Change to backend directory
    backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
    os.chdir(backend_dir)

    # Run pytest with coverage
    result = subprocess.run([
        sys.executable, '-m', 'pytest',
        'tests/',
        '-v',
        '--cov=.',
        '--cov-report=term-missing',
        '--cov-report=html:../coverage_report',
        '--ignore=tests/__pycache__'
    ])

    if result.returncode == 0:
        print("\n" + "=" * 60)
        print("All tests passed!")
        print("Coverage report generated at: coverage_report/index.html")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("Some tests failed. Please review the output above.")
        print("=" * 60)

    return result.returncode

if __name__ == '__main__':
    sys.exit(main())
