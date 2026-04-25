---
description: Generate and process a new PDF version of the TEP manuscript
---

Generate a new PDF version of the TEP-J0437 manuscript from the built site, with compression and metadata embedding.

## Quick Method (Universal Generator)
```bash
cd /Users/matthewsmawfield/www/TEP-J0437
python /Users/matthewsmawfield/www/TEP/scripts/generate_pdf_universal.py . --quality maximum --wait-time 5
```

## Manual Steps

1. **Build the static site** - Generate the latest static HTML with all components:
   ```bash
   cd site && node build.js
   ```

2. **Generate PDF from site** - Convert the built HTML to PDF using Playwright (maximum quality):
   ```bash
   python scripts/utils/generate_site_pdf.py --quality maximum --wait-time 5
   ```

3. **Process PDF with metadata** - Compress and embed academic metadata (DOI, abstract, keywords):
   ```bash
   python scripts/utils/process_pdf.py site/public/docs/Smawfield_2026_TEP-J0437_v0.1_Sintra.pdf --quality ebook
   ```

4. **Verify the output** - Check the final PDF exists and display its properties:
   ```bash
   ls -lh site/public/docs/Smawfield_2026_TEP-J0437_v0.1_Sintra.pdf && exiftool -Title -Author -Creator site/public/docs/Smawfield_2026_TEP-J0437_v0.1_Sintra.pdf 2>/dev/null | head -10
   ```
