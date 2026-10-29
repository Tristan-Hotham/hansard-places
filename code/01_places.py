"""Step 1. The list of places to count in Hansard.

Reads (in place):
  /home/claude/hist/_data13/cities15000.zip   GeoNames cities with 15,000+ people (CC BY 4.0): every UK place, with population
  /home/claude/hist/osnames_gb.tsv            OS Open Names (OGL v3): every City and Town in Great Britain
  /home/claude/hist/elections-since-1832/data/contests.csv  constituency names and centroids 2005 to 2024 (sister project)

Writes:
  work/places.csv      one row per search term (place name), with coordinates, nation, population where known
  work/terms.json      the search terms passed to the browser harvester (step 2)

A place name is a search term. Where two listed places share one name (Newport, Bangor, Richmond...), the term is kept
once and flagged "shared" because Hansard text cannot tell them apart.
"""
import csv, io, json, os, zipfile, math
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = "/home/claude/hist"
NATION = {"ENG": "England", "SCT": "Scotland", "WLS": "Wales", "NIR": "Northern Ireland"}

rows = []
z = zipfile.ZipFile(f"{H}/_data13/cities15000.zip")
for line in io.TextIOWrapper(z.open("cities15000.txt"), encoding="utf-8"):
    f = line.rstrip("\n").split("\t")
    if f[8] != "GB":
        continue
    if f[7] in ("PPLX",) and int(f[14]) < 15000:
        continue
    rows.append(dict(name=f[1], lat=float(f[4]), lon=float(f[5]), nation=NATION.get(f[10], ""),
                     pop=int(f[14]), fcode=f[7], src="GeoNames"))
print("GeoNames GB places", len(rows))

# OS Open Names cities and towns not already present (within 8 km under the same name)
def km(a, b):
    return math.hypot((a["lon"] - b["lon"]) * 111.32 * math.cos(math.radians(54)), (a["lat"] - b["lat"]) * 110.57)

by = defaultdict(list)
for r in rows:
    by[r["name"].lower()].append(r)
added = 0
with open(f"{H}/osnames_gb.tsv", encoding="utf-8") as fh:
    rd = csv.DictReader(fh, delimiter="\t")
    for r in rd:
        if r["type"] != "populatedPlace" or r["local_type"] not in ("City", "Town"):
            continue
        nm = r["name2"] if r["lang2"] == "eng" and r["name2"] else r["name1"]  # English form for Welsh towns
        d = dict(name=nm, lat=float(r["lat"]), lon=float(r["lon"]), nation=r["country"], pop=None,
                 fcode=r["local_type"], src="OS Open Names")
        if any(km(d, o) < 8 for o in by[d["name"].lower()]):
            continue
        rows.append(d); by[d["name"].lower()].append(d); added += 1
print("OS Open Names towns added", added)

# one term per name; flag shared names
terms = {}
for name, lst in by.items():
    if not lst:
        continue
    lst.sort(key=lambda r: -(r["pop"] or 0))
    main = lst[0]
    far = [o for o in lst[1:] if km(main, o) >= 8]
    terms[main["name"]] = dict(term=main["name"], lat=main["lat"], lon=main["lon"], nation=main["nation"],
                               pop=main["pop"], src=main["src"], fcode=main["fcode"],
                               shared="; ".join(sorted({f'{o["name"]} ({o["nation"]}, {o["lat"]:.2f},{o["lon"]:.2f})' for o in far})))
print("distinct place terms", len(terms))

with open(os.path.join(ROOT, "work", "places.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["term", "lat", "lon", "nation", "pop", "src", "fcode", "shared"])
    w.writeheader()
    for t in sorted(terms.values(), key=lambda r: r["term"]):
        w.writerow(t)

# constituency names 2005 to 2024 (sister project), for matching later
cons = set()
for r in csv.DictReader(open(f"{H}/elections-since-1832/data/contests.csv", encoding="utf-8")):
    if r["election"] in ("2005", "2010", "2015", "2017", "2019", "2024"):
        cons.add(r["constituency"])
print("constituency names 2005 to 2024", len(cons))
json.dump(sorted(terms), open(os.path.join(ROOT, "work", "terms.json"), "w"), ensure_ascii=False)
