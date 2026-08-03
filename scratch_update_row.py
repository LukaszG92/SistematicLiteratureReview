import csv, json, sys

CSV = "/Users/lukaszgajewski/PycharmProjects/SLR/data/p4_final_corpus_analyzed.csv"
PROG = "/private/tmp/claude-501/-Users-lukaszgajewski-PycharmProjects-SLR/9b3482db-73e6-4ce5-ada9-4907c783a149/scratchpad/progress.json"

payload = json.load(sys.stdin)
idx = payload["idx"]
fields = payload.get("fields", {})

with open(CSV, newline='', encoding='utf-8') as f:
    r = csv.DictReader(f); fn = r.fieldnames; rows = list(r)

row = rows[idx]
for k, v in fields.items():
    if k not in fn:
        print(f"WARN unknown field {k}"); continue
    row[k] = v

with open(CSV, 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fn, quoting=csv.QUOTE_ALL)
    w.writeheader(); w.writerows(rows)

with open(PROG) as f: prog = json.load(f)
prog[str(idx)]["status"] = "done"
prog[str(idx)]["changed"] = payload.get("changed", bool(fields))
prog[str(idx)]["note"] = payload.get("note", "")
with open(PROG, 'w') as f: json.dump(prog, f, indent=2)

done = sum(1 for p in prog.values() if p['status']=='done')
print(f"idx {idx} ({row['Title'][:45]}): saved. changed={prog[str(idx)]['changed']}. Progress {done}/139")
