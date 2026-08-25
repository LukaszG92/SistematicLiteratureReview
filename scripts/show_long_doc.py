import re, sys
sys.path.insert(0, 'scripts')
from rewrite_metrics import TEXS, strip_tex
body = strip_tex(TEXS[0].read_text(encoding='utf-8', errors='replace'))
for s in re.split(r"(?<=[.!?])\s+", body):
    if len(s.split()) > 60:
        print(len(s.split()), '::', ' '.join(s.split())[:220])
        print('---')
