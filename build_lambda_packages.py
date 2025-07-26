#!/usr/bin/env python3
"""
Lambda Package Builder for TechPulse Content Ingestion

This script builds deployment packages for the AWS Lambda functions
with the smart cleanup functionality integrated.

Usage:
    python build_lambda_packages.py
"""

import os
import shutil
import zipfile
import subprocess
import sys
from pathlib import Path

def create_lambda_package(source_file, package_name, dependencies=None):
    """
    Creates a Lambda deployment package with dependencies.
    
    Args:
        source_file (str): Path to the Lambda function source file
        package_name (str): Name of the output zip file
        dependencies (list): List of Python packages to include
    """
    print(f"\n🚀 Building Lambda package: {package_name}")
    
    # Create temporary build directory
    build_dir = Path("build") / package_name.replace('.zip', '')
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir(parents=True)
    
    try:
        # Copy the Lambda function source
        shutil.copy2(source_file, build_dir / Path(source_file).name)
        print(f"✅ Copied source file: {source_file}")
        
        # Install dependencies if specified
        if dependencies:
            print(f"📦 Installing dependencies: {', '.join(dependencies)}")
            subprocess.run([
                sys.executable, "-m", "pip", "install",
                "--target", str(build_dir),
                *dependencies
            ], check=True)
        
        # Create the ZIP package
        package_path = Path("lambda-packages") / package_name
        package_path.parent.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(build_dir):
                for file in files:
                    file_path = Path(root) / file
                    archive_name = file_path.relative_to(build_dir)
                    zipf.write(file_path, archive_name)
        
        print(f"✅ Created package: {package_path}")
        print(f"📊 Package size: {package_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        return package_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        return None
    except Exception as e:
        print(f"❌ Error creating package: {e}")
        return None
    finally:
        # Cleanup build directory
        if build_dir.exists():
            shutil.rmtree(build_dir)

def main():
    """
    Build Lambda deployment packages for TechPulse ingestion system.
    """
    print("🏗️  TechPulse Lambda Package Builder")
    print("=" * 50)
    
    # Ensure we're in the project root
    if not Path("src/lambdas").exists():
        print("❌ Error: Please run this script from the project root directory")
        sys.exit(1)
    
    # Package configurations
    packages = [
        {
            'source': 'src/lambdas/ingestion_orchestrator.py',
            'package': 'orchestrator.zip',
            'dependencies': ['psycopg2-binary', 'boto3']
        },
        {
            'source': 'src/lambdas/content_processor.py', 
            'package': 'processor.zip',
            'dependencies': ['psycopg2-binary', 'boto3', 'feedparser', 'requests']
        }
    ]
    
    success_count = 0
    
    for config in packages:
        if not Path(config['source']).exists():
            print(f"⚠️  Warning: Source file not found: {config['source']}")
            continue
            
        result = create_lambda_package(
            config['source'],
            config['package'],
            config['dependencies']
        )
        
        if result:
            success_count += 1
    
    print(f"\n🎉 Build completed!")
    print(f"✅ Successfully built {success_count}/{len(packages)} packages")
    
    if success_count == len(packages):
        print("\n📋 Next steps:")
        print("1. Upload the packages to your S3 bucket")
        print("2. Update your CloudFormation stack to deploy the new Lambda functions")
        print("3. The smart cleanup will run automatically with your hourly schedule")
        print("\n💡 The system will now:")
        print("   • Fetch fresh articles every hour")
        print("   • Automatically clean old articles when fresh content is available")
        print("   • Preserve user favorites regardless of article age")
        print("   • Prevent the website from becoming empty")

if __name__ == "__main__":
    main()
