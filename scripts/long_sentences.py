import re
from pathlib import Path
t = Path('TQE_Template/tqe.tex').read_text(encoding='utf-8', errors='replace')
lines = t.split('\n')
for i, l in enumerate(lines, 1):
    if l.lstrip().startswith('%'):
        continue
    body = re.sub(r'\\cite\{[^}]*\}', '[c]', l)
    body = re.sub(r'\\[a-zA-Z]+\*?(\[[^]]*\])?(\{[^{}]*\})?', ' ', body)
    body = re.sub(r'[{}$~&]', ' ', body)
    for s in re.split(r'(?<=[.!?])\s+', body):
        w = len(s.split())
        if w > 60:
            print(f'{i}: {w}w :: {s[:90]}')
