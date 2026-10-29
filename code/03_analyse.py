"""Step 3. From counts to findings.

Reads:
  /home/claude/hist/_data18/hansard-places/hansard_places_bundle.json.gz   (step 0; UK Parliament, Open Parliament Licence v3.0)
  work/places.csv                                                           (step 1)
  /home/claude/hist/elections-since-1832/data/contests.csv                  constituency points (sister project)

Two measures, both counts of Commons contributions (speeches and other spoken items) that contain a phrase:
  "in <place>"  place-phrase mentions. Available for every year from 1909 (the first year of the verbatim Official
                Report) and the headline measure: it is not inflated by division lists, by "the hon. Member for <seat>",
                by surnames or by titles such as "the Duchy of Lancaster".
  "<place>"     any mention. Only from 2005: until 2004 the Hansard API files division lists (names of members with
                their seats in brackets) as spoken contributions, which swamps the counts for smaller places.

Ambiguous names are handled in four ways, all listed in data/ambiguous_names.csv:
  shared      two listed UK places share the name (Newport, Bangor, Richmond...): kept on the map, left out of rankings
  namesake    a better-known place abroad or a county of the same name (Washington, Perth, Durham...): left out
  word        the name is an ordinary English word or name (Reading, Sale, Deal, Wells, Bath...): a sample of 40
              "in <name>" contributions was checked for a capital letter ("in Sale", not "in sale"); counts are
              multiplied by that precision, and the name is left out of rankings if precision is below 0.6
  other       for the any-mention measure only, names whose "in" share is far below the norm (surnames, titles,
              institutions), and names that are also the surname of a member since 2005
"""
import csv, gzip, json, math, os, re, statistics as st
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
H = "/home/claude/hist"
B = json.load(gzip.open(f"{H}/_data18/hansard-places/hansard_places_bundle.json.gz"))
OUT = os.path.join(ROOT, "data")
Y0, Y1 = 1909, 2025          # long view, full years
M0 = 2005                    # any-mention measure starts
R = {}                       # results.json

def tot(d, a, b):
    if not d:
        return 0
    return sum(v for y, v in d.items() if a <= int(y) <= b)

# ---------- places ----------
P = {r["term"]: r for r in csv.DictReader(open(os.path.join(ROOT, "work", "places.csv"), encoding="utf-8"))}
GN = {}
import io, zipfile
with zipfile.ZipFile(f"{H}/_data13/cities15000.zip") as z:
    for line in io.TextIOWrapper(z.open("cities15000.txt"), encoding="utf-8"):
        f = line.split("\t")
        if f[8] == "GB":
            GN.setdefault(f[1], (float(f[4]), float(f[5]), int(f[14]), {"ENG": "England", "SCT": "Scotland", "WLS": "Wales", "NIR": "Northern Ireland"}.get(f[10], "")))
EXTRA_PT = {  # extra search terms: the place they stand for (coordinates from the GeoNames or OS Open Names entry named)
    "Londonderry": "Derry", "Newcastle": "Newcastle upon Tyne", "Southend": "Southend-on-Sea", "Stockton": "Stockton-on-Tees",
    "Leamington": "Royal Leamington Spa", "Tunbridge Wells": "Royal Tunbridge Wells", "Wootton Bassett": "Royal Wootton Bassett",
    "Newark": "Newark on Trent", "Berwick": "Berwick-upon-Tweed", "Clacton": "Clacton-on-Sea", "Bexhill": "Bexhill-on-Sea",
    "Henley": "Henley-on-Thames", "Bognor": "Bognor Regis", "Merthyr": "Merthyr Tydfil", "Hull": "Kingston upon Hull",
    "Stoke": "Stoke-on-Trent"}
BOROUGHS = ["Ealing", "Enfield", "Hackney", "Lambeth", "Southwark", "Tower Hamlets", "Newham", "Lewisham", "Haringey",
            "Wandsworth", "Hammersmith", "Camden", "Westminster", "Gravesham"]
NATIONS = ["England", "Scotland", "Wales", "Northern Ireland", "Ulster", "Cornwall", "Yorkshire"]
# spelling variants that the search treats as the same words, or that duplicate a fuller name: keep the first
VARIANTS = {"Barrow in Furness": "Barrow-in-Furness", "Ashton in Makerfield": "Ashton-in-Makerfield", "Bishops Stortford": "Bishop's Stortford",
            "Kirkby in Ashfield": "Kirkby-in-Ashfield", "Newark on Trent": "Newark-on-Trent", "Newcastle under Lyme": "Newcastle-under-Lyme",
            "Lytham St Annes": "Lytham St Anne's", "Saint Andrews": "St Andrews", "Saint Ives": "St Ives", "Saint Neots": "St Neots",
            "Cwmbrân": "Cwmbran", "Abingdon-on-Thames": "Abingdon", "Droitwich Spa": "Droitwich", "Letchworth Garden City": "Letchworth",
            "Ellesmere Port Town": "Ellesmere Port", "Staines-upon-Thames": "Staines", "Londonderry County Borough": "Londonderry",
            "Kingston upon Hull": "Hull", "Stoke-on-Trent": "Stoke-on-Trent", "Manchester City Centre": "Manchester",
            "Brighton and Hove": "Brighton", "Amersham on the Hill": "Amersham", "Blaydon-on-Tyne": "Blaydon",
            "Royal Sutton Coldfield": "Sutton Coldfield", "Newcastle upon Tyne": "Newcastle upon Tyne", "Derry": "Londonderry",
            "Royal Leamington Spa": "Leamington", "Royal Tunbridge Wells": "Tunbridge Wells", "Royal Wootton Bassett": "Wootton Bassett",
            "Southend-on-Sea": "Southend", "Stockton-on-Tees": "Stockton", "Bognor Regis": "Bognor", "Clacton-on-Sea": "Clacton",
            "Bexhill-on-Sea": "Bexhill", "Henley-on-Thames": "Henley", "Merthyr Tydfil": "Merthyr"}
# Note: for towns usually called by a short form in speech (Southend, Stockton, Leamington...) the short term is the one
# counted, because the phrase "in Southend" also matches "in Southend-on-Sea" and so includes it. Both Derry and
# Londonderry are used in debate; the counts of the two terms are added (they never occur as the same phrase).
ADD = {"Londonderry": ["Derry"]}

SHARED_EXTRA = {"Newcastle": "Newcastle upon Tyne and Newcastle-under-Lyme (and Newcastle Emlyn, Newcastle in County Down)",
                "Hull": "the hull of a ship (lower case, checked)", "Stoke": "several Stokes; most mentions are Stoke-on-Trent",
                "Berwick": "Berwick-upon-Tweed and North Berwick", "Newport": "Newport (Wales), Newport (Isle of Wight), Newport (Shropshire)"}
NAMESAKE = {"Washington": "Washington DC", "Boston": "Boston, Massachusetts", "Perth": "Perth, Western Australia",
            "Wellington": "Wellington, New Zealand", "Christchurch": "Christchurch, New Zealand", "Alexandria": "Alexandria, Egypt",
            "Kimberley": "Kimberley, South Africa", "Hamilton": "Hamilton (Canada, New Zealand, Bermuda)", "Nelson": "Nelson, New Zealand",
            "Montgomery": "Montgomery, Alabama", "Durham": "County Durham", "Antrim": "County Antrim", "Louth": "County Louth, Ireland",
            "Westminster": "Parliament itself", "City of Westminster": "Parliament itself", "Lancaster": "the Duchy of Lancaster",
            "Windsor": "the Windsor Framework (from 2023)", "Plymouth": None, "Victoria": None, "Hastings": None,
            "Bethesda": "Bethesda, Maryland", "Clare": "County Clare, Ireland", "Armadale": None, "Shirley": None,
            "Hyde": "Hyde Park, London", "Kensington": None, "Brent": None, "Hampton": "Hampton Court", "Sandhurst": None,
            "Banff": "Banff, Canada", "Ulster": "the historic province", "Cambridge": None, "Oxford": None, "Paisley": None,
            "Stratford": "Stratford-upon-Avon and Stratford (London)", "Church": "the Church", "Fylde": None, "Mendip": None,
            "Queensferry": "North and South Queensferry, Queensferry in Flintshire", "Moreton": "several Moretons",
            "Seven Sisters": "the Seven Sisters cliffs", "Salisbury": "Salisbury, Rhodesia (now Harare), and Lord Salisbury",
            "Stanley": "Stanley, Falkland Islands", "Halifax": None, "Primrose Place": "a street name", "Queenstown": "Queenstown, New Zealand"}
NAMESAKE = {k: v for k, v in NAMESAKE.items() if v}
WORDS = set(B.get("prec", {}).keys())
MANUAL_WORD = {"March": "also the month (\"in March\" is almost always the month)", "Street": "too common a word to check",
               "Hook": "the check cannot separate Hook from Hook Norton", "Church": "\"in Church\" is mostly the Church"}

def label_of(t):
    return t

places = {}
for t, v in B["places"].items():
    if t in VARIANTS and VARIANTS[t] != t:
        continue
    places[t] = {"all": dict(v["all"] or {}), "in": dict(v["in"] or {}), "fail": v["all"] is None or v["in"] is None}
# longer names that begin with a shorter one: "in Bury" also matches "in Bury St Edmunds", so subtract the longer
# name's "in" counts (per year, floored at zero). A contribution naming both places is then undercounted for the shorter.
def _n(x):
    return re.sub(r"[^a-z0-9 ]", " ", x.lower()).split()
RAW = {t: _n(t) for t in B["places"]}
PREFIX = defaultdict(list)
for a, na in RAW.items():
    for b, nb in RAW.items():
        if len(nb) > len(na) and nb[:len(na)] == na and b not in VARIANTS:
            PREFIX[a].append(b)
R["prefix_pairs"] = sum(len(v) for v in PREFIX.values())
for a, bs in PREFIX.items():
    if a not in places:
        continue
    for b in bs:
        for y, c in (B["places"][b]["in"] or {}).items():
            if y in places[a]["in"]:
                places[a]["in"][y] = max(0, places[a]["in"][y] - c)
R["prefix_examples"] = sorted([[a, sorted(set(bs))[:4]] for a, bs in PREFIX.items() if a in places], key=lambda x: -len(x[1]))[:12]
for t, adds in ADD.items():
    for a in adds:
        if a in B["places"]:
            for k in ("all", "in"):
                for y, c in (B["places"][a][k] or {}).items():
                    places[t][k][y] = places[t][k].get(y, 0) + c

def coords(t):
    src = EXTRA_PT.get(t, t)
    for nm in (src, t):
        if nm in P:
            r = P[nm]
            return float(r["lat"]), float(r["lon"]), r["nation"], (int(r["pop"]) if r["pop"] else None), r["src"], r["shared"]
        if nm in GN:
            la, lo, pop, nat = GN[nm]
            return la, lo, nat, pop, "GeoNames", ""
    return None

# precision of "in <word>" from the capital-letter check
PREC = {}
for w, d in B.get("prec", {}).items():
    if d.get("n"):
        PREC[w] = d["cs"] / d["n"]

rows = []
for t, v in places.items():
    if t in NATIONS:
        continue
    c = coords(t)
    if not c:
        continue
    la, lo, nat, pop, src, shared = c
    if t in SHARED_EXTRA:
        shared = SHARED_EXTRA[t]
    flag, why, factor = "", "", 1.0
    if v["fail"]:
        flag, why = "word", "too common a word to count (the search timed out)"
    elif shared:
        flag, why = "shared", "name shared with " + shared
    elif t in NAMESAKE:
        flag, why = "namesake", "also " + NAMESAKE[t]
    elif t in MANUAL_WORD:
        flag, why = "word", MANUAL_WORD[t]
    elif t in PREC:
        factor = PREC[t]
        if factor < 0.6:
            flag, why = "word", f"ordinary word or name: {round(100 * factor)}% of sampled \"in {t}\" mentions were the place"
        else:
            why = f"ordinary word or name: counts scaled by {round(100 * factor)}%, the share of sampled \"in {t}\" mentions that were the place"
    i_long = tot(v["in"], Y0, Y1)
    i_mod = tot(v["in"], M0, Y1)
    a_mod = tot(v["all"], M0, Y1)
    rows.append(dict(term=t, lat=la, lon=lo, nation=nat, pop=pop, pop_src="", flag=flag, why=why, factor=round(factor, 3),
                     in_1909_2025=round(i_long * factor), in_2005_2025=round(i_mod * factor), any_2005_2025=a_mod,
                     in_ratio=round(i_mod / a_mod, 3) if a_mod else None))

# any-mention flags: far fewer "in" phrases than usual
ratios = [r["in_ratio"] for r in rows if r["in_ratio"] and r["any_2005_2025"] >= 200 and not r["flag"]]
med_ratio = st.median(ratios)
surn = set()
for m in B["members"].values():
    la = (m.get("listAs") or "").split(",")[0].strip()
    if la:
        surn.add(la)
for r in rows:
    af = ""
    if r["flag"]:
        af = r["flag"]
    elif r["in_ratio"] is not None and r["any_2005_2025"] >= 100 and r["in_ratio"] < med_ratio / 3:
        af = "other"
    elif r["term"] in PREC or r["term"] in MANUAL_WORD:
        af = "word"
    elif r["term"] in surn:
        af = "surname"
    r["any_flag"] = af
R["median_in_ratio"] = round(med_ratio, 3)
R["n_place_terms"] = len(rows)
R["n_flag"] = {k: sum(1 for r in rows if r["flag"] == k) for k in ("shared", "namesake", "word")}
R["n_scaled_words"] = sum(1 for r in rows if r["term"] in PREC and not r["flag"])
R["n_clean"] = sum(1 for r in rows if not r["flag"])

clean = [r for r in rows if not r["flag"]]
by_t = {r["term"]: r for r in rows}

# per-year totals of clean in-phrase mentions (denominator for shares)
years = list(range(Y0, 2027))
den = {y: sum(round(places[r["term"]]["in"].get(str(y), 0) * r["factor"]) for r in clean) for y in years}
R["in_total_1909_2025"] = sum(den[y] for y in years if y <= Y1)

# rankings
top_in = sorted(clean, key=lambda r: -r["in_2005_2025"])
R["top_in_2005_2025"] = [[r["term"], r["in_2005_2025"]] for r in top_in[:25]]
top_long = sorted(clean, key=lambda r: -r["in_1909_2025"])
R["top_in_1909_2025"] = [[r["term"], r["in_1909_2025"]] for r in top_long[:25]]
anyc = [r for r in rows if not r["any_flag"]]
R["top_any_2005_2025"] = [[r["term"], r["any_2005_2025"]] for r in sorted(anyc, key=lambda r: -r["any_2005_2025"])[:25]]
lon = by_t["London"]
R["london"] = dict(in_2005_2025=lon["in_2005_2025"], in_1909_2025=lon["in_1909_2025"],
                   share_2005_2025=round(100 * lon["in_2005_2025"] / sum(r["in_2005_2025"] for r in clean), 1),
                   share_1909_2025=round(100 * lon["in_1909_2025"] / R["in_total_1909_2025"], 1))
# London share per decade
dec = {}
for d0 in range(1910, 2030, 10):
    ys = [y for y in years if d0 <= y < d0 + 10 and y <= Y1]
    if not ys:
        continue
    tl = sum(round(places["London"]["in"].get(str(y), 0)) for y in ys)
    dd = sum(den[y] for y in ys)
    dec[d0] = round(100 * tl / dd, 1) if dd else None
R["london_share_by_decade"] = dec

# per head: places with population 50,000+ (GeoNames)
# per head only for real towns and cities: the name must be an OS Open Names City or Town within 8 km of the GeoNames
# point (this drops suburbs and districts whose GeoNames populations are not town populations), or a Northern Ireland town
OST = defaultdict(list)
for _r in csv.DictReader(open(f"{H}/osnames_gb.tsv", encoding="utf-8"), delimiter="\t"):
    if _r["type"] == "populatedPlace" and _r["local_type"] in ("City", "Town"):
        _nm = _r["name2"] if _r["lang2"] == "eng" and _r["name2"] else _r["name1"]
        OST[_nm.lower()].append((float(_r["lat"]), float(_r["lon"])))
NI_TOWNS = {"Belfast", "Londonderry", "Lisburn", "Newry", "Craigavon", "Newtownabbey", "Ballymena", "Newtownards", "Carrickfergus", "Coleraine", "Portadown", "Omagh", "Larne", "Banbridge", "Antrim"}
def is_town(r):
    if r["nation"] == "Northern Ireland":
        return r["term"] in NI_TOWNS
    src = EXTRA_PT.get(r["term"], r["term"])
    for nm in {r["term"], src}:
        for la, lo in OST.get(nm.lower(), []):
            if math.hypot((lo - r["lon"]) * 65.4, (la - r["lat"]) * 110.6) < 8:
                return True
    return False
# populations: Census 2021 built-up areas (ONS BUA22, England and Wales; table from the Beeching cuts project, OGL v3)
# where a built-up area of the same name lies within 8 km; otherwise GeoNames (Scotland, Northern Ireland, others)
BUA = defaultdict(list)
for _r in csv.DictReader(open(f"{H}/beeching-cuts/data/towns.csv", encoding="utf-8")):
    if _r["pop2021"]:
        BUA[_r["bua22"].lower()].append((float(_r["lat"]), float(_r["lon"]), int(float(_r["pop2021"]))))
for r in rows:
    r["is_town"] = is_town(r)
    src = EXTRA_PT.get(r["term"], r["term"])
    best = None
    for nm in {r["term"], src}:
        for la, lo, pp in BUA.get(nm.lower(), []):
            d = math.hypot((lo - r["lon"]) * 65.4, (la - r["lat"]) * 110.6)
            if d < 8 and (best is None or d < best[0]):
                best = (d, pp)
    if best:
        r["pop"], r["pop_src"] = best[1], "ONS BUA 2021"
    elif r["pop"]:
        r["pop_src"] = "GeoNames"
    if r["term"] == "Newcastle upon Tyne":
        r["is_town"] = False   # usually called "Newcastle" in debate, a name it shares
ph = [r for r in clean if r["pop"] and r["pop"] >= 50000 and r["is_town"]]
for r in ph:
    r["per100k"] = round(r["in_2005_2025"] / r["pop"] * 1e5, 1)
for r in rows:
    r.setdefault("per100k", None)
ph.sort(key=lambda r: -r["per100k"])
R["n_per_head"] = len(ph)
R["per_head_top"] = [[r["term"], r["per100k"], r["pop"], r["in_2005_2025"]] for r in ph[:20]]
R["per_head_bottom"] = [[r["term"], r["per100k"], r["pop"], r["in_2005_2025"]] for r in ph[-15:]]
R["per_head_median"] = st.median(r["per100k"] for r in ph)
# log-log fit of mentions on population, and residuals
import numpy as np
xs = np.log10([r["pop"] for r in ph]); ys_ = np.log10([max(r["in_2005_2025"], 0.5) for r in ph])
b, a = np.polyfit(xs, ys_, 1)
R["pop_elasticity"] = round(float(b), 2)
R["pop_r"] = round(float(np.corrcoef(xs, ys_)[0, 1]), 2)
R["fit_a"] = round(float(a), 4)
R["pop_ten"] = round(10 ** float(b), 1)
for r in ph:
    r["resid"] = round(float(np.log10(max(r["in_2005_2025"], .5)) - (a + b * np.log10(r["pop"]))), 3)
for r in rows:
    r.setdefault("resid", None)
over = sorted(ph, key=lambda r: -r["resid"])
R["over_expected"] = [[r["term"], round(10 ** r["resid"], 2), r["pop"], r["in_2005_2025"]] for r in over[:12]]
R["under_expected"] = [[r["term"], round(10 ** r["resid"], 2), r["pop"], r["in_2005_2025"]] for r in over[-10:]]

# nations: in-phrase mentions per decade
nat_dec = {}
for n in ["England", "Scotland", "Wales", "Northern Ireland"]:
    nat_dec[n] = {}
    for d0 in range(1910, 2030, 10):
        ys = [y for y in years if d0 <= y < d0 + 10 and y <= Y1]
        nat_dec[n][d0] = sum(places[n]["in"].get(str(y), 0) for y in ys)
R["nations_in_by_decade"] = nat_dec
R["nat_per100"] = {n: {d0: round(100 * nat_dec[n][d0] / max(1, sum(den[y] for y in years if d0 <= y < d0 + 10 and y <= Y1)), 1) for d0 in nat_dec[n]} for n in nat_dec}
R["nations_in_2005_2025"] = {n: tot(places[n]["in"], M0, Y1) for n in nat_dec}
R["nations_in_1909_2025"] = {n: tot(places[n]["in"], Y0, Y1) for n in nat_dec}

# spikes: the year each place was most talked about, relative to its own typical year
spikes = []
for r in clean:
    s = places[r["term"]]["in"]
    tl = r["in_1909_2025"]
    if tl < 150:
        continue
    sh = {y: round(s.get(str(y), 0) * r["factor"]) / den[y] for y in years if y <= Y1 and den[y]}
    med = st.median(sorted(sh.values()))
    if med <= 0:
        med = min(v for v in sh.values() if v > 0)
    yb = max(sh, key=sh.get)
    cnt = round(s.get(str(yb), 0) * r["factor"])
    if cnt < 25:
        continue
    spikes.append(dict(term=r["term"], year=yb, count=cnt, ratio=round(sh[yb] / med, 1)))
spikes.sort(key=lambda d: -d["ratio"])
R["spikes"] = spikes[:40]
for r in rows:
    sp = next((d for d in spikes if d["term"] == r["term"]), None)
    r["peak_year"] = sp["year"] if sp else None
    r["peak_count"] = sp["count"] if sp else None
    r["peak_ratio"] = sp["ratio"] if sp else None

# ---------- constituencies ----------
def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", s.lower().replace("&", "and"))).strip()

CP = {}
for r in csv.DictReader(open(f"{H}/elections-since-1832/data/contests.csv", encoding="utf-8")):
    if r["election"] in ("2005", "2010", "2015", "2017", "2019", "2024"):
        CP[norm(r["constituency"])] = (float(r["lat"]), float(r["lon"]), r["nation"], r["election"])
spans = B["spans"]
seat = defaultdict(lambda: {"start": "9999", "end": "0000", "own": defaultdict(int), "members": set()})
for s in spans:
    if s["end"] <= "2005-05-06":
        continue
    d = seat[s["cons"]]
    d["start"] = min(d["start"], s["start"]); d["end"] = max(d["end"], s["end"]); d["members"].add(s["id"])
    for y, c in (s.get("own") or {}).items():
        d["own"][y] += c
# seat names that are also ordinary words, first names or brands: their counts include other meanings
SEAT_AMBIG = {"Gordon": "first name", "Vauxhall": "brand", "Buckingham": "Buckingham Palace", "Barking": "word"}
crow = []
for name, d in seat.items():
    c = B["cons"].get(name)
    if not c:
        continue
    ya, yb = max(int(d["start"][:4]), M0), min(int(d["end"][:4]), 2026)
    yb_full = min(yb, Y1)
    nyears = (min(d["end"], "2026-10-28") > d["start"]) and (
        (min(__import__("datetime").date.fromisoformat(min(d["end"], "2026-10-28")), __import__("datetime").date(2026, 10, 28))
         - __import__("datetime").date.fromisoformat(max(d["start"], "2005-05-05"))).days / 365.25)
    allc = tot(c["all"], ya, yb)
    mf = tot(c["mf"], ya, yb)
    own = sum(v for y, v in d["own"].items() if ya <= int(y) <= yb)
    pt = CP.get(norm(name))
    pr = by_t.get(name)
    crow.append(dict(seat=name, start=d["start"], end=min(d["end"], "2026-10-28"), years=round(nyears, 2), n_members=len(d["members"]),
                     any=allc, member_for=mf, own=own, others=max(allc - own, 0),
                     own_share=round(own / allc, 3) if allc else None,
                     per_year=round(allc / nyears, 1) if nyears > 0.3 else None,
                     mf_per_year=round(mf / nyears, 1) if nyears > 0.3 else None,
                     lat=pt[0] if pt else None, lon=pt[1] if pt else None, nation=pt[2] if pt else "",
                     also_place=("yes" if pr else ""), place_flag=SEAT_AMBIG.get(name) or ((pr["flag"] or pr["any_flag"]) if pr else "")))
crow.sort(key=lambda r: r["seat"])
cur = [r for r in crow if r["end"] >= "2026-10-28"]
old = [r for r in crow if r["end"] < "2026-10-28"]
R["n_seats"] = len(crow)
R["n_seats_current"] = len(cur)
R["n_seats_with_point"] = sum(1 for r in crow if r["lat"] is not None)
R["n_members"] = len(B["members"])
R["n_spans"] = len([s for s in spans if s["end"] > "2005-05-06"])
ok = [r for r in crow if r["any"] >= 20 and r["years"] >= 1 and not r["place_flag"]]
R["seat_own_share_median"] = round(100 * st.median(r["own_share"] for r in ok), 1)
R["seat_own_share_iqr"] = [round(100 * float(np.percentile([r["own_share"] for r in ok], q)), 1) for q in (25, 75)]
R["seat_any_total"] = sum(r["any"] for r in crow)
R["seat_own_total"] = sum(r["own"] for r in crow)
R["seat_mf_total"] = sum(r["member_for"] for r in crow)
R["seat_own_share_overall"] = round(100 * R["seat_own_total"] / R["seat_any_total"], 1)
pr = [r for r in crow if r["per_year"] is not None and r["years"] >= 2 and not r["place_flag"] and not r["also_place"]]
R["n_seats_ranked"] = len(pr)
R["seat_top_per_year"] = [[r["seat"], r["per_year"], r["own_share"]] for r in sorted(pr, key=lambda r: -r["per_year"])[:15]]
R["seat_bottom_per_year"] = [[r["seat"], r["per_year"], r["own_share"]] for r in sorted(pr, key=lambda r: r["per_year"])[:10]]
R["seat_median_per_year"] = st.median(r["per_year"] for r in pr)
R["seat_top_mf_per_year"] = [[r["seat"], r["mf_per_year"]] for r in sorted(pr, key=lambda r: -r["mf_per_year"])[:10]]
R["seat_median_mf_per_year"] = st.median(r["mf_per_year"] for r in pr)
R["seat_most_own"] = [[r["seat"], r["own_share"], r["any"]] for r in sorted([r for r in pr if r["any"] >= 100], key=lambda r: -r["own_share"])[:10]]
R["seat_least_own"] = [[r["seat"], r["own_share"], r["any"]] for r in sorted([r for r in pr if r["any"] >= 100], key=lambda r: r["own_share"])[:10]]

# ---------- write ----------
with open(os.path.join(OUT, "places.csv"), "w", newline="", encoding="utf-8") as fh:
    cols = ["term", "lat", "lon", "nation", "pop", "pop_src", "in_1909_2025", "in_2005_2025", "any_2005_2025", "in_ratio", "per100k", "resid",
            "peak_year", "peak_count", "peak_ratio", "flag", "any_flag", "factor", "why"]
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader()
    for r in sorted(rows, key=lambda r: r["term"]):
        w.writerow(r)
with open(os.path.join(OUT, "place_years.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["term", "year", "in_mentions", "any_mentions"])
    for t in sorted(places):
        if t not in by_t and t not in NATIONS:
            continue
        v = places[t]
        for y in sorted(set(v["in"]) | set(v["all"])):
            if int(y) < 1900:
                continue
            w.writerow([t, y, v["in"].get(y, 0), v["all"].get(y, "") if int(y) >= M0 else ""])
with open(os.path.join(OUT, "ambiguous_names.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh); w.writerow(["term", "flag", "any_flag", "precision_factor", "sample_n", "why"])
    for r in sorted(rows, key=lambda r: r["term"]):
        if r["flag"] or r["any_flag"] or r["term"] in PREC:
            w.writerow([r["term"], r["flag"], r["any_flag"], r["factor"], B["prec"].get(r["term"], {}).get("n", ""), r["why"]])
with open(os.path.join(OUT, "constituencies.csv"), "w", newline="", encoding="utf-8") as fh:
    cols = ["seat", "nation", "lat", "lon", "start", "end", "years", "n_members", "any", "own", "others", "own_share", "member_for", "per_year", "mf_per_year", "also_place", "place_flag"]
    w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader()
    for r in crow:
        w.writerow(r)
R["den_by_year"] = {str(y): den[y] for y in years}
json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1, ensure_ascii=False)
json.dump({"rows": rows, "crow": crow, "years": years}, open(os.path.join(ROOT, "work", "analysis_cache.json"), "w"))
print(json.dumps({k: R[k] for k in R if k not in ("den_by_year", "nations_in_by_decade")}, indent=0, ensure_ascii=False)[:9000])

# yearly "in" counts per place after prefix subtraction and precision scaling, 1909 to 2026, for the page and figures
YA = {}
for r in rows:
    v = places[r["term"]]["in"]
    YA[r["term"]] = [round(v.get(str(y), 0) * r["factor"]) for y in range(Y0, 2027)]
for n in NATIONS:
    if n in places:
        YA[n] = [places[n]["in"].get(str(y), 0) for y in range(Y0, 2027)]
json.dump(YA, open(os.path.join(ROOT, "work", "years_in.json"), "w"), separators=(",", ":"))
