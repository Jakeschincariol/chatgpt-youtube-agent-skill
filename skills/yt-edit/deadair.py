#!/usr/bin/env python3
"""deadair.py - an edit decision list from a timestamped transcript.

    python3 deadair.py transcript.srt            # or .vtt, or whisper .json
    python3 deadair.py transcript.srt --floor 0.35 --json

Finds three things and prints the cuts as a list you can act on, newest problem first:
  DEAD    gaps between spoken cues longer than the floor
  FILLER  cues that are only filler ("um", "so yeah", "basically")
  REPEAT  a sentence restarted - the second take of the same opening

WHAT IT DOES NOT DO. It does not cut the file. It prints an EDL, the total it would remove, and the
runtime you would land on, and you apply it in whatever editor you use. Nothing here touches media.
"""
import json, os, re, sys

FILLER_ONLY = re.compile(r"^[\s,.-]*((um+|uh+|er+|ah+|so|okay|ok|right|yeah|like|anyway|basically|"
                         r"actually|you know|i mean|let me see|hold on)[\s,.-]*)+$", re.I)

def parse_ts(s):
    s = s.strip().replace(",", ".")
    p = s.split(":")
    return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2]) if len(p) == 3 else int(p[0]) * 60 + float(p[1])

def total_removed(cuts):
    intervals = sorted(
        (float(c["start"]), float(c["end"]))
        for c in cuts
        if float(c["end"]) > float(c["start"])
    )
    if not intervals:
        return 0.0

    total = 0.0
    start, end = intervals[0]

    for next_start, next_end in intervals[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end

    return total + end - start


def load(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        raw = f.read()
    if path.endswith(".json"):
        d = json.loads(raw)
        if isinstance(d, dict):
            segs = d.get("segments", [])
        elif isinstance(d, list):
            segs = d
        else:
            raise ValueError("O JSON deve conter uma lista de segmentos ou um objeto com a chave 'segments'.")
        if not isinstance(segs, list):
            raise ValueError("A chave 'segments' deve conter uma lista.")
        return [(float(s["start"]), float(s["end"]), (s.get("text") or "").strip()) for s in segs]
    cues, cur = [], None
    for line in raw.splitlines():
        m = re.match(r"\s*(\d[\d:.,]+)\s*-->\s*(\d[\d:.,]+)", line)
        if m:
            cur = [parse_ts(m.group(1)), parse_ts(m.group(2)), []]
            cues.append(cur)
        elif cur is not None and line.strip() and not line.strip().isdigit():
            cur[2].append(line.strip())
    return [(a, b, " ".join(t)) for a, b, t in cues if t]

def norm(t): return re.sub(r"[^a-z ]", "", t.lower()).split()

def main():
    a = sys.argv[1:]
    if "-h" in a or "--help" in a:
        print(__doc__ or "Ajuda não disponível.")
        return
    as_json = "--json" in a; a = [x for x in a if x != "--json"]
    floor = 0.45
    if "--floor" in a:
        i = a.index("--floor")
        if i + 1 >= len(a) or a[i + 1].startswith("--"):
            print("Erro: --floor exige um valor numérico positivo.", file=sys.stderr); sys.exit(2)
        try: floor = float(a[i + 1])
        except ValueError: print("Erro: --floor deve ser um número positivo e finito.", file=sys.stderr); sys.exit(2)
        if not (0 < floor < float("inf")): print("Erro: --floor deve ser um número positivo e finito.", file=sys.stderr); sys.exit(2)
    a = [x for x in a if not x.startswith("--") and not re.match(r"^[\d.]+$", x)]
    if not a or not os.path.exists(a[0]): print(__doc__); sys.exit(1)
    try:
        cues = load(a[0])
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Erro: não foi possível ler a transcrição: {exc}", file=sys.stderr)
        sys.exit(2)
    if not cues: print("no cues found - is this an srt, vtt or whisper json?"); sys.exit(1)
    dur = cues[-1][1]
    cuts = []
    for i, (s, e, t) in enumerate(cues):
        if FILLER_ONLY.match(t):
            cuts.append({"kind": "FILLER", "start": s, "end": e, "why": t.strip()[:48]})
        if i:
            gap = s - cues[i - 1][1]
            if gap > floor:
                keep = floor / 2
                cuts.append({"kind": "DEAD", "start": round(cues[i - 1][1] + keep, 3),
                             "end": round(s - keep, 3), "why": f"{gap:.2f}s gap"})
        # A restart is compared against the last cue that was actually SPEECH. Comparing against
        # the literal previous cue misses every retake with an "um" between the two attempts, which
        # is most of them.
        if t.strip() and not FILLER_ONLY.match(t):
            j = i - 1
            while j >= 0 and (FILLER_ONLY.match(cues[j][2]) or not cues[j][2].strip()): j -= 1
            if j >= 0:
                a1, b1 = norm(cues[j][2])[:5], norm(t)[:5]
                if len(a1) >= 3 and a1 == b1:
                    cuts.append({"kind": "REPEAT", "start": cues[j][0], "end": cues[j][1],
                                 "why": f'restart of "{" ".join(a1)}"'})
    cuts = [c for c in cuts if c["end"] > c["start"]]
    cuts.sort(key=lambda c: c["start"])
    removed = total_removed(cuts)
    if as_json:
        print(json.dumps({"source": a[0], "duration": dur, "cuts": cuts,
                          "removed": round(removed, 3), "out": round(dur - removed, 3)}, indent=1)); return
    print(f"\n  {a[0]}   {dur:.2f}s in, {len(cues)} cues, dead-air floor {floor}s\n")
    for c in cuts:
        print(f"    {c['kind']:<7} {c['start']:8.2f} -> {c['end']:8.2f}   {c['end']-c['start']:5.2f}s   {c['why']}")
    print(f"\n  {len(cuts)} cuts, {removed:.2f}s removed, {dur - removed:.2f}s out "
          f"({removed / dur * 100:.1f}% shorter)\n")

if __name__ == "__main__":
    main()
