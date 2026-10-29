"""Step 2. Coastline, nation outlines and place labels for the page and figures.

Nations of the UK: simplified county outlines (ONS boundaries, OGL v3, as used in the How Roman is your road? and
Bread Rolls projects) dissolved to England, Wales, Scotland and Northern Ireland; Ireland from Natural Earth (public domain).
Labels: OS Open Names cities, towns and villages (OGL v3) and GeoNames towns for Northern Ireland and Ireland (CC BY 4.0).

Writes data/nations.geojson and data/page/labels.json
"""
import io, json, os, zipfile
import pandas as pd
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data")
os.makedirs(os.path.join(OUT, "page"), exist_ok=True)

g = json.load(open("/home/claude/hist/bread-rolls/data/counties.geojson"))
parts = {}
for f in g["features"]:
    parts.setdefault(f["properties"]["nation"], []).append(shape(f["geometry"]).buffer(0))
nat = {k: unary_union(v) for k, v in parts.items()}
ne = json.load(open("/home/claude/hist/_data3/ne/geojson/ne_10m_admin_0_countries.geojson"))
for f in ne["features"]:
    if f["properties"].get("ADM0_A3") == "IRL":
        nat["Ireland"] = shape(f["geometry"]).buffer(0)
feats = []
for k in ["England", "Wales", "Scotland", "Northern Ireland", "Ireland"]:
    s = nat[k].simplify(0.004, preserve_topology=True).buffer(0)
    geo = json.loads(json.dumps(mapping(s)), parse_float=lambda x: round(float(x), 3))
    feats.append({"type": "Feature", "properties": {"nation": k}, "geometry": geo})
json.dump({"type": "FeatureCollection", "features": feats}, open(os.path.join(OUT, "nations.geojson"), "w"), separators=(",", ":"))

osn = pd.read_csv("/home/claude/hist/osnames_gb.tsv", sep="\t", usecols=["name1", "name2", "lang2", "local_type", "lat", "lon", "county"], dtype=str)
osn = osn[osn.local_type.isin(["City", "Town", "Village"])]
rank = {"City": 3, "Town": 2, "Village": 0}
pl = []
for r in osn.itertuples():
    nm = r.name2 if isinstance(r.name2, str) and r.lang2 == "eng" else r.name1
    pl.append([nm, round(float(r.lon), 3), round(float(r.lat), 3), rank[r.local_type], r.county if isinstance(r.county, str) else ""])
with zipfile.ZipFile("/home/claude/hist/_data13/cities15000.zip") as z:
    for line in io.TextIOWrapper(z.open("cities15000.txt"), encoding="utf-8"):
        f = line.split("\t")
        if f[8] == "IE" or (f[8] == "GB" and f[10] == "NIR"):
            pl.append([f[1], round(float(f[5]), 3), round(float(f[4]), 3), 3 if int(f[14]) > 100000 else 2,
                       "Ireland" if f[8] == "IE" else "Northern Ireland"])
json.dump(pl, open(os.path.join(OUT, "page", "labels.json"), "w"), separators=(",", ":"), ensure_ascii=False)
print("labels", len(pl))
