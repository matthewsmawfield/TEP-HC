#!/usr/bin/env python3
"""
Generate PDF from TEP-HC Site
==============================

Generates a high-quality PDF from the built TEP-HC site static HTML.

Usage:
    python scripts/generate_site_pdf.py
    python scripts/generate_site_pdf.py --output 14-TEP-HC-v0.1-Geneva.pdf
"""

import argparse
import subprocess
import sys
from pathlib import Path


def generate_pdf(output_path=None):
    """Generate PDF from built site."""
    base_dir = Path(__file__).parent.parent
    site_dir = base_dir / "site" / "dist"
    
    if not site_dir.exists():
        print("⚠️  Site not built. Running build.js first...")
        build_script = base_dir / "site" / "build.js"
        result = subprocess.run(
            ["node", str(build_script)],
            cwd=base_dir / "site",
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"❌ Build failed: {result.stderr}")
            return False
        print("✓ Site built successfully")
    
    # Determine output filename
    if output_path is None:
        output_path = base_dir / "14-TEP-HC-v0.1-Geneva.pdf"
    else:
        output_path = Path(output_path)
    
    index_html = site_dir / "index.html"
    
    # Try using Playwright if available
    try:
        import asyncio
        from playwright.async_api import async_playwright
        
        async def convert():
            async with async_playwright() as p:
                browser = await p.chromium.launch()
                page = await browser.new_page()
                await page.goto(f"file://{index_html.absolute()}")
                await page.pdf(
                    path=str(output_path),
                    format="A4",
                    margin={
                        "top": "20mm",
                        "right": "20mm", 
                        "bottom": "20mm",
                        "left": "20mm"
                    },
                    print_background=True
                )
                await browser.close()
        
        asyncio.run(convert())
        print(f"✓ PDF generated: {output_path}")
        return True
        
    except ImportError:
        print("⚠️  Playwright not installed. Trying wkhtmltopdf...")
        
        # Fallback to wkhtmltopdf
        try:
            subprocess.run(
                ["wkhtmltopdf", "--enable-local-file-access", 
                 str(index_html), str(output_path)],
                check=True
            )
            print(f"✓ PDF generated: {output_path}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ No PDF converter available")
            print("   Install one of:")
            print("   - pip install playwright && playwright install chromium")
            print("   - brew install wkhtmltopdf (macOS)")
            print("   - apt-get install wkhtmltopdf (Linux)")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Generate PDF from TEP-HC site"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output PDF path (default: 14-TEP-HC-v0.1-Geneva.pdf)"
    )
    args = parser.parse_args()
    
    success = generate_pdf(args.output)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
