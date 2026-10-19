#!/usr/bin/env python3
"""swipe.py - rank collected videos by how far each beat its OWN channel, then name the formula.

    python3 swipe.py collected.json
    python3 swipe.py collected.json --min 2.0 --json

Input is a list you collected - one object per video:

    [{"channel":"Some Channel","title":"...","views":412000,"url":"...","duration":613}, ...]

Raw view counts rank channel size, not ideas. A 400k video on a 2M-subscriber channel is a normal
Tuesday; a 400k video on a channel whose median is 30k is the thing worth studying. So every video
is scored as a MULTIPLE OF ITS OWN CHANNEL'S MEDIAN, which needs at least four videos per channel
to mean anything - the tool says so rather than quietly ranking on noise.

The formula comes from skills/yt-script/hooks.json, matched against the TITLE. It is a judgement
about the words on screen, not a claim about why the video worked.
"""
import json, os, re, statistics, sys

HERE = os.path.dirname(os.path.abspath(__file__))
FORMULAS = json.load(open(os.path.join(HERE, "..", "yt-script", "hooks.json")))["hooks"]

def classify(title):
    scored = []
    for f in FORMULAS:
        n = sum(1 for p in f["match"] if re.search(p, title, re.I))
        if n: scored.append((n, f["name"]))
    scored.sort(reverse=True)
    return scored[0][1] if scored else "Unclassified"

def main():
    a = sys.argv[1:]
    if "-h" in a or "--help" in a:
        print(__doc__ or "Ajuda não disponível.")
        return
    as_json = "--json" in a; a = [x for x in a if x != "--json"]
    lo = 1.5
    if "--min" in a:
        i = a.index("--min")
        if i + 1 >= len(a) or a[i + 1].startswith("--"):
            print("Erro: --min exige um número finito não negativo.", file=sys.stderr)
            sys.exit(2)
        try:
            lo = float(a[i + 1])
        except ValueError:
            print("Erro: --min exige um número finito não negativo.", file=sys.stderr)
            sys.exit(2)
        if not (0 <= lo < float("inf")):
            print("Erro: --min exige um número finito não negativo.", file=sys.stderr)
            sys.exit(2)
    files = [x for x in a if not x.startswith("--") and not re.match(r"^[\d.]+$", x)]
    if not files or not os.path.exists(files[0]): print(__doc__); sys.exit(1)
    rows = json.load(open(files[0]))
    if isinstance(rows, dict): rows = rows.get("videos", [])
    by = {}
    for r in rows: by.setdefault(r.get("channel", "?"), []).append(r)
    out, thin = [], []
    for ch, vids in by.items():
        views = [float(v.get("views", 0) or 0) for v in vids]
        med = statistics.median(views) if views else 0
        if len(vids) < 4:
            thin.append((ch, len(vids)))
            continue
        for v in vids:
            m = (float(v.get("views", 0) or 0) / med) if med else 0
            out.append({"channel": ch, "title": v.get("title", ""), "views": int(v.get("views", 0) or 0),
                        "median": int(med), "multiple": round(m, 2),
                        "formula": classify(v.get("title", "")), "url": v.get("url", "")})
    out = [r for r in out if r["multiple"] >= lo]
    out.sort(key=lambda r: -r["multiple"])
    if as_json: print(json.dumps({"outliers": out, "skipped_thin_channels": thin}, indent=1)); return
    print(f"\n  {len(rows)} videos across {len(by)} channels, outliers at {lo}x or better\n")
    for r in out[:25]:
        print(f"    {r['multiple']:5.2f}x  {r['views']:>9,}  vs {r['median']:>9,} median   {r['channel'][:22]:<22} {r['title'][:52]}")
        print(f"            {r['formula']}")
    if not out: print("    nothing cleared the threshold - collect more per channel or lower --min")
    if thin:
        print(f"\n  skipped {len(thin)} channel(s) with under 4 videos collected - a median off one or")
        print( "  two videos is not a median: " + ", ".join(f"{c} ({n})" for c, n in thin[:6]))
    counts = {}
    for r in out: counts[r["formula"]] = counts.get(r["formula"], 0) + 1
    if counts:
        print("\n  formulas among the outliers")
        for f, n in sorted(counts.items(), key=lambda x: -x[1]):
            print(f"    {n:2d}x  {f}")
    print()

if __name__ == "__main__":
    main()
