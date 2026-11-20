"""Fill report/README.tmpl.md: @@TABLE@@ takes the results table, and
@@BLOCK name@@ the block of blocks.md whose heading starts with name.

  python3 report/assemble.py report/README.tmpl.md table.md blocks.md README.md
"""
import re, sys
tmpl, table, blocks_md, out_path = sys.argv[1:5]
text = open(tmpl).read()
blocks, cur = {}, None
for line in open(blocks_md).read().splitlines():
    if line.startswith("### "):
        cur = line[4:].strip(); blocks[cur] = []
    elif cur is not None:
        blocks[cur].append(line)
def block(prefix):
    keys = [k for k in blocks if k.startswith(prefix)]
    if len(keys) != 1:
        sys.exit(f"block prefix {prefix!r} matches {keys}")
    return "\n".join(blocks[keys[0]]).strip()
text = text.replace("@@TABLE@@", open(table).read().strip())
text = re.sub(r"@@BLOCK (.+?)@@", lambda m: block(m.group(1)), text)
if "@@" in text:
    sys.exit("unresolved marker")
open(out_path, "w").write(text)
print("written", out_path, len(text.splitlines()), "lines")
