#!/usr/bin/env python3
"""
Bundle Size Analyzer

Analyzes frontend bundle size and provides optimization recommendations.
"""

import json
import subprocess
import sys
from pathlib import Path


def analyze_bundle():
    """Analyze Next.js build output"""
    frontend_dir = Path("frontend")
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return
    
    print("📦 Analyzing bundle size...\n")
    
    # Build the frontend
    print("Building frontend...")
    result = subprocess.run(
        ["npm", "run", "build"],
        cwd=frontend_dir,
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print(f"❌ Build failed: {result.stderr}")
        return
    
    # Analyze .next directory
    next_dir = frontend_dir / ".next"
    if not next_dir.exists():
        print("❌ Build output not found")
        return
    
    # Find bundle files
    bundle_files = []
    for file_path in next_dir.rglob("*.js"):
        if file_path.is_file():
            size = file_path.stat().st_size
            bundle_files.append({
                'path': str(file_path.relative_to(next_dir)),
                'size': size,
                'size_mb': size / (1024 * 1024)
            })
    
    # Sort by size
    bundle_files.sort(key=lambda x: x['size'], reverse=True)
    
    print("📊 Bundle Analysis:\n")
    print(f"{'File':<50} {'Size (MB)':<15} {'Size (KB)':<15}")
    print("-" * 80)
    
    total_size = 0
    for file_info in bundle_files[:20]:  # Top 20 files
        size_kb = file_info['size'] / 1024
        print(f"{file_info['path']:<50} {file_info['size_mb']:<15.2f} {size_kb:<15.2f}")
        total_size += file_info['size']
    
    print("-" * 80)
    print(f"{'Total (top 20)':<50} {total_size / (1024 * 1024):<15.2f} {total_size / 1024:<15.2f}")
    
    # Recommendations
    print("\n💡 Recommendations:\n")
    
    large_files = [f for f in bundle_files if f['size_mb'] > 0.5]
    if large_files:
        print("⚠️  Large files detected (>500KB):")
        for file_info in large_files[:5]:
            print(f"   - {file_info['path']}: {file_info['size_mb']:.2f} MB")
        print("\n   Consider:")
        print("   - Code splitting")
        print("   - Dynamic imports")
        print("   - Tree shaking unused code")
        print("   - Lazy loading routes")
    
    if total_size > 5 * 1024 * 1024:  # > 5MB
        print("\n⚠️  Total bundle size is large (>5MB)")
        print("   Consider:")
        print("   - Analyzing with webpack-bundle-analyzer")
        print("   - Removing unused dependencies")
        print("   - Using smaller alternatives")
        print("   - Implementing code splitting")
    
    # Check for common large dependencies
    package_json = frontend_dir / "package.json"
    if package_json.exists():
        with open(package_json) as f:
            data = json.load(f)
            deps = {**data.get('dependencies', {}), **data.get('devDependencies', {})}
            
            large_deps = [
                'recharts', 'moment', 'lodash', 'axios', '@supabase/supabase-js'
            ]
            
            found_large = [dep for dep in large_deps if dep in deps]
            if found_large:
                print("\n📦 Large dependencies detected:")
                for dep in found_large:
                    print(f"   - {dep}")
                print("\n   Consider:")
                print("   - Using lighter alternatives")
                print("   - Tree shaking unused exports")
                print("   - Dynamic imports for heavy libraries")


def install_bundle_analyzer():
    """Install webpack-bundle-analyzer"""
    frontend_dir = Path("frontend")
    
    print("Installing webpack-bundle-analyzer...")
    result = subprocess.run(
        ["npm", "install", "--save-dev", "webpack-bundle-analyzer"],
        cwd=frontend_dir,
        capture_output=True
    )
    
    if result.returncode == 0:
        print("✅ Installed webpack-bundle-analyzer")
        print("\n💡 Add to package.json scripts:")
        print('   "analyze": "ANALYZE=true next build"')
    else:
        print("❌ Failed to install webpack-bundle-analyzer")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze bundle size")
    parser.add_argument("--install-analyzer", action="store_true",
                       help="Install webpack-bundle-analyzer")
    
    args = parser.parse_args()
    
    if args.install_analyzer:
        install_bundle_analyzer()
    else:
        analyze_bundle_size()
