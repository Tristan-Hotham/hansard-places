"""Step 4. Page files and the extra numbers the page, paper and blog quote.

Writes data/page/places.json, data/page/years.json, data/page/seats.json and adds page fields to data/results.json.
"""
import csv, gzip, json, os, re
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data")
R = json.load(open(os.path.join(OUT, "results.json")))
C = json.load(open(os.path.join(ROOT, "work", "analysis_cache.json")))
YA = json.load(open(os.path.join(ROOT, "work", "years_in.json")))
B = json.load(gzip.open("/home/claude/hist/_data18/hansard-places/hansard_places_bundle.json.gz"))
Y0 = 1909

rows, crow = C["rows"], C["crow"]
pl = []
for r in rows:
    pl.append({"t": r["term"], "la": round(r["lat"], 3), "lo": round(r["lon"], 3), "n": r["nation"], "pop": r["pop"] if r.get("pop_src") else None, "ps": "Census 2021" if r.get("pop_src") == "ONS BUA 2021" else ("GeoNames" if r.get("pop_src") else ""),
               "m": r["in_2005_2025"], "ml": r["in_1909_2025"], "a": r["any_2005_2025"], "af": r["any_flag"] if not r["flag"] else "",
               "per100k": r["per100k"], "res": r["resid"], "py": r["peak_year"], "pc": r["peak_count"], "pr": r["peak_ratio"],
               "f": r["flag"], "w": r["why"]})
pl.sort(key=lambda p: -p["m"])
json.dump(pl, open(os.path.join(OUT, "page", "places.json"), "w"), separators=(",", ":"), ensure_ascii=False)
json.dump({p["t"]: YA[p["t"]] for p in pl}, open(os.path.join(OUT, "page", "years.json"), "w"), separators=(",", ":"), ensure_ascii=False)
se = [{"n": c["seat"], "la": c["lat"], "lo": c["lon"], "na": c["nation"], "s": c["start"], "e": c["end"], "k": c["n_members"], "a": c["any"], "o": c["own"],
       "mf": c["member_for"], "py": c["per_year"], "os": c["own_share"], "ap": c["also_place"], "pf": c["place_flag"]} for c in crow]
json.dump(se, open(os.path.join(OUT, "page", "seats.json"), "w"), separators=(",", ":"), ensure_ascii=False)

# numbers for the text
prec = {w: d for w, d in B["prec"].items() if d.get("n")}
R["n_words_checked"] = len(prec)
eg = []
for w in ("Bath", "Wells", "Reading", "Sale"):
    d = prec[w]
    eg.append(f"{w} {round(100 * d['cs'] / d['n'])}% of {d['n']}")
R["prec_eg"] = "; ".join(eg)
R["prec_pct"] = {w: round(100 * d["cs"] / d["n"]) for w, d in prec.items()}
R["prec_n"] = {w: d["n"] for w, d in prec.items()}
R["word_excluded"] = [r["term"] for r in rows if r["flag"] == "word"]
R["prec_table"] = {w: [d["cs"], d["n"]] for w, d in sorted(prec.items())}
R["n_queries"] = 2 * len(B["places"]) + 2 * len(B["cons"]) + len(B["spans"])
# from a check query run with the harvest (Hansard API timeline statistics, "Tellers for the Ayes", Commons, Spoken)
R["tellers_check"] = {"2000": 355, "2004": 184, "2005": 0, "2006": 0, "2007": 0, "2008": 1, "2010": 1}
R["tellers_note"] = "the phrase “Tellers for the Ayes” is found in 355 spoken contributions in 2000 and 184 in 2004, but in at most one a year from 2005"
R["den"] = [R["den_by_year"][str(y)] for y in range(Y0, 2027)]
R["time_ref"] = 500
R["seat_ref"] = 218

# histogram of own-member share
ok = [c for c in crow if c["any"] >= 20 and c["years"] >= 1 and not c["place_flag"]]
edges = list(range(0, 105, 5))
cnt, _ = np.histogram([100 * c["own_share"] for c in ok], bins=edges)
R["own_hist"] = {"edges": edges, "counts": [int(x) for x in cnt]}
R["n_seats_hist"] = len(ok)

R["den"] = [R["den_by_year"][str(y)] for y in range(Y0, 2027)]
# spike cards with debate titles (series: mentions per 10,000 town mentions that year)
cards = []
for s in R["spikes"][:16]:
    t = B["titles"].get(f"{s['term']}|{s['year']}")
    titles = [re.sub(r"\s*[\u2014\u2013]+\s*", ": ", re.sub(r"\s+", " ", x[0])).strip() for x in (t or {}).get("top", [])[:2] if x[1] >= 2]
    cards.append({**s, "titles": titles, "series": [round(1e4 * c / d, 1) if d else 0 for c, d in zip(YA[s["term"]][:2025 - Y0 + 1], R["den"])]})
R["spike_cards"] = cards

# ambiguous names table
amb = []
for r in csv.DictReader(open(os.path.join(OUT, "ambiguous_names.csv"), encoding="utf-8")):
    if r["flag"]:
        how = {"shared": "left out (shared name)", "namesake": "left out (namesake)", "word": "left out (ordinary word)"}[r["flag"]]
    elif r["precision_factor"] and float(r["precision_factor"]) < 1:
        how = f"scaled by {round(100 * float(r['precision_factor']))}%"
    elif r["any_flag"] == "surname":
        how = "any-mention count marked (surname)"
    elif r["any_flag"] == "other":
        how = "any-mention count marked (other meanings)"
    else:
        how = "kept"
    why = r["why"] or {"surname": "also the surname of a member since 2005", "other": "few of its mentions are “in” phrases"}.get(r["any_flag"], "")
    amb.append([r["term"], how, why])
R["ambig"] = amb
R["n_ambig_listed"] = len(amb)

# over-mentioned towns whose seat has the same name: how much of the name's use came from the seat's own member
SB = {c["seat"]: c for c in crow}
R["over_seat_own"] = [[t, round(100 * SB[t]["own_share"]), SB[t]["any"]] for t, *_ in R["over_expected"] if t in SB and SB[t]["own_share"] is not None]
_sc = [v for k, v in R["nat_per100"]["Scotland"].items() if 1910 <= int(k) <= 1970]
R["scot_lo"], R["scot_hi"] = min(_sc), max(_sc)
R["mf_top"] = R["seat_top_mf_per_year"][0]
R["peak_of"] = {r["term"]: [r["peak_year"], r["peak_ratio"]] for r in rows if r["term"] in ("Rotherham", "York", "Taunton", "Harlow", "Stafford", "Kettering") and r["peak_year"]}

# stories for the map
UK = [[49.9, -8.4], [58.8, 1.8]]
P = {p["t"]: p for p in pl}
S = {c["seat"]: c for c in crow}
def box(t, d=0.9):
    p = P[t]
    return [[p["la"] - d, p["lo"] - d * 1.6], [p["la"] + d, p["lo"] + d * 1.6]]
oe = R["over_expected"][0]
st_ = S.get("Strangford", {})
stories = [
    dict(t="London first", d=f"{R['london']['share_2005_2025']}% of mentions since 2005", mode="count", b=UK, place="London",
         long=f"London was mentioned in {R['london']['in_2005_2025']:,} contributions from 2005 to 2025, {R['london']['share_2005_2025']}% of all the town and city mentions counted."),
    dict(t=oe[0], d=f"{oe[1]} times what its size predicts", mode="size", b=box(oe[0], 1.2), place=oe[0],
         long=f"{oe[0]} was mentioned {oe[3]:,} times from 2005 to 2025, {oe[1]} times what a place of {oe[2]:,} people would get on the national trend."),
    dict(t="1926", d="West Ham and the Guardians", mode="time", year=1926, b=[[51.0, -0.9], [51.9, 0.9]], place="West Ham",
         long="In 1926 West Ham's share of town mentions was the highest of any year, during the Boards of Guardians (Default) Bill."),
    dict(t="1936", d="Jarrow", mode="time", year=1936, b=box("Jarrow", 1.5), place="Jarrow", long="Jarrow's biggest year in the Commons was 1936."),
    dict(t="1981", d="Brixton", mode="time", year=1981, b=[[51.2, -0.6], [51.7, 0.3]], place="Brixton", long="Brixton's peak year was 1981, the year of the Scarman Report."),
    dict(t="2015", d="Redcar steelworks", mode="time", year=2015, b=box("Redcar", 1.0), place="Redcar", long="Redcar's peak year was 2015, with debates on the steel industry and the Redcar steelworks."),
    dict(t="2024", d="Port Talbot", mode="time", year=2024, b=box("Port Talbot", 1.0), place="Port Talbot", long="Port Talbot's peak year was 2024, with debates on the Port Talbot steelworks."),
    dict(t="Seats", d="Who names each seat", mode="seats", b=UK, seat="Strangford",
         long=f"Strangford is the seat most often named with \"Member for\": {st_.get('mf_per_year')} times a year. Tap any seat."),
]
R["stories"] = stories
json.dump(R, open(os.path.join(OUT, "results.json"), "w"), indent=1, ensure_ascii=False)
print("places", len(pl), "seats", len(se), "queries", R["n_queries"], R["prec_eg"])
for f in ("places.json", "years.json", "seats.json", "labels.json"):
    print(f, os.path.getsize(os.path.join(OUT, "page", f)))
