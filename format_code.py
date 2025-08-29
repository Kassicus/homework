#!/usr/bin/env python3
"""
Code formatting script that runs isort and black in the correct order
to prevent conflicts between the two tools.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and return success status"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            if result.stdout.strip():
                print(result.stdout)
            return True
        else:
            print(f"❌ {description} failed:")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    """Main formatting function"""
    print("🎨 Starting code formatting...")
    print("📁 Working directory:", os.getcwd())
    
    # Step 1: Run isort first to organize imports
    if not run_command("python3 -m isort app/", "Import sorting with isort"):
        print("❌ Import sorting failed. Please fix import issues first.")
        sys.exit(1)
    
    # Step 2: Run black to format code
    if not run_command("python3 -m black app/", "Code formatting with black"):
        print("❌ Code formatting failed. Please fix formatting issues first.")
        sys.exit(1)
    
    # Step 3: Run isort again to ensure imports are still properly formatted
    if not run_command("python3 -m isort app/", "Final import sorting check"):
        print("❌ Final import sorting failed.")
        sys.exit(1)
    
    # Step 4: Run flake8 to check for any remaining issues
    if not run_command("python3 -m flake8 app/ --max-line-length=120 --extend-ignore=E203,W503,E501,E722", "Linting with flake8"):
        print("⚠️  Linting found some issues. Please review and fix them.")
        # Don't exit on flake8 failures, just warn
    
    print("\n🎉 Code formatting completed!")
    print("💡 If you still have conflicts, try running this script again.")
    print("🔧 You can also run individual commands:")
    print("   python3 -m isort app/")
    print("   python3 -m black app/")

if __name__ == "__main__":
    main()
