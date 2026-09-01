import json
import sys
from pathlib import Path

level_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
agents_dir = level_dir / "agents"
total_acc = total_rej = 0
for d in sorted(agents_dir.iterdir()):
    rp = d / "result.json"
    if not rp.is_file():
        print(f"{d.name}: pending")
        continue
    r = json.loads(rp.read_text())
    acc = r.get("accepted_count", 0)
    rej = r.get("rejected_count", 0)
    total_acc += acc
    total_rej += rej
    flag = "  <-- LOW" if acc < 4 else ""
    print(f"{d.name}: accepted={acc} rejected={rej}{flag}")
print(f"\nTOTAL: accepted={total_acc} rejected={total_rej}")
