import sys

with open('dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if "}lse:" in line or "lse:" in line:
        new_lines.append('    }, position="sidebar")\n')
        skip = True
        continue
    if skip:
        # We need to stop skipping once we are past the bad block
        # The bad block ends at another "    }, position=\"sidebar\")"
        if "}, position=\"sidebar\")" in line:
            skip = False
        continue
        
    new_lines.append(line)

with open('dashboard.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
