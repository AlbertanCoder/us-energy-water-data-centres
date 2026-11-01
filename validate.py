"""Structural + syntax checks for energy_water.html (run: python validate.py)."""
import json
import re
import subprocess
import sys
from pathlib import Path

HTML = Path(__file__).with_name("energy_water.html")
JS = Path(__file__).with_name("_check.js")

src = HTML.read_text(encoding="utf-8")
problems = []

# 1. script blocks
blocks = re.findall(r"<script>(.*?)</script>", src, re.S)
print(f"script blocks: {len(blocks)}")
if len(blocks) != 1:
    problems.append("expected exactly one <script> block")
if src.count("<script") != src.count("</script>"):
    problems.append("unbalanced <script> tags")
if not src.strip().endswith("</html>"):
    problems.append("file does not end with </html>")

# 2. duplicate element ids
ids = re.findall(r'id="([^"]+)"', src)
dupes = sorted({i for i in ids if ids.count(i) > 1})
print(f"elements with id: {len(ids)} | duplicates: {dupes or 'none'}")
if dupes:
    problems.append(f"duplicate ids: {dupes}")

# 3. every id referenced by the JS must exist in the markup
js = blocks[0]
JS.write_text(js, encoding="utf-8")
refs = set(re.findall(r'getElementById\("([^"]+)"\)', js))
concats = re.findall(r'getElementById\("([^"]*)"\s*\+\s*(\w+)', js)
for prefix, _ in concats:
    # only expect the ids that exist for at least one chart (some lookups are guarded)
    present = [c for c in ("elec", "water", "bills") if f'id="{prefix}{c}"' in src]
    for c in present:
        refs.add(prefix + c)
missing = sorted(r for r in refs if f'id="{r}"' not in src)
print(f"ids referenced by JS: {len(refs)} | missing in markup: {missing or 'none'}")
if missing:
    problems.append(f"JS references missing elements: {missing}")

# 4. balanced braces/parens/brackets in the JS (cheap sanity check)
for open_c, close_c in ("{}", "()", "[]"):
    if js.count(open_c) != js.count(close_c):
        problems.append(f"unbalanced {open_c}{close_c} in JS "
                        f"({js.count(open_c)} vs {js.count(close_c)})")

# 5. no leftover mojibake / encoding damage
for bad in ("Ã", "Â", "â€"):
    if bad in src:
        problems.append(f"suspicious encoding artefact {bad!r} in file")

# 6. node syntax check
try:
    out = subprocess.run(["node", "--check", str(JS)], capture_output=True, text=True)
    if out.returncode == 0:
        print("node --check: OK")
    else:
        print("node --check: FAILED")
        print(out.stderr.strip()[:800])
        problems.append("JS syntax error")
except FileNotFoundError:
    print("node not found - skipped syntax check")

print()
if problems:
    print("PROBLEMS:")
    for p in problems:
        print(" -", p)
    sys.exit(1)

print("All checks passed.")
