"""r/dataisbeautiful collage: reddit/mentioned_in_the_house.png (2400 by 3000). Run: python3 reddit/collage.py"""
import csv, json, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "code"))
from figlib import *
import matplotlib.patheffects as pe
from matplotlib.patches import Rectangle

BG2, FG2, MUT2, INK, GRN = "#EEF1EA", "#17201B", "#5C665F", "#1F4F8B", "#2E6B4E"
LAND2 = "#DCE2D6"
P = list(csv.DictReader(open(os.path.join(ROOT, "data", "places.csv"), encoding="utf-8")))
for p in P:
    for k in ("lat", "lon", "in_2005_2025", "resid"):
        p[k] = float(p[k]) if p[k] not in ("", None) else None
clean = sorted([p for p in P if not p["flag"]], key=lambda p: -p["in_2005_2025"])
L = R["london"]; D = R["london_share_by_decade"]; OE = R["over_expected"]; cards = {c["term"]: c for c in R["spike_cards"]}

fig = plt.figure(figsize=(12, 15), dpi=200, facecolor=BG2)
fig.text(.045, .968, "Which towns does Parliament talk about?", fontproperties=DISP, fontsize=33, color=FG2, va="top")
fig.text(.047, .924, f"A century of Hansard, counted place by place: {R['in_total_1909_2025']:,} House of Commons speeches that say \"in\" plus\none of {R['n_clean']:,} UK town and city names, 1909 to 2025. Circles: mentions 2005 to 2025.",
         family=SER, fontsize=15, color=FG2, va="top", linespacing=1.35)

# hero map
ax = fig.add_axes([.0, .27, .62, .62])
land(ax, fc=LAND2, ec="#9DA89F", lw=.45)
for p in clean[::-1]:
    s = p["in_2005_2025"] / L["in_2005_2025"] * 5200
    col = res_col(p["resid"]) if p["resid"] is not None else "#8C948D"
    ax.scatter(p["lon"], p["lat"], s=max(s, 1.5), c=col, alpha=.9 if p["resid"] is not None else .6, edgecolors=BG2, linewidths=.5, zorder=3)
lab = {"London": (1.0, -.55), "Glasgow": (-1.9, .35), "Edinburgh": (.35, .3), "Birmingham": (-2.35, -.35), "Manchester": (-2.4, .3), "Cardiff": (-1.65, -.4),
       "Belfast": (-1.55, .35), "York": (.3, .2), OE[0][0]: (.45, .2), "Liverpool": (-2.1, -.2)}
for t, (dx, dy) in lab.items():
    p = next(q for q in clean if q["term"] == t)
    ax.annotate(t, (p["lon"], p["lat"]), xytext=(p["lon"] + dx, p["lat"] + dy), family=MONO, fontsize=11, color=FG2, zorder=6,
                arrowprops=dict(arrowstyle="-", color=FG2, lw=.6), path_effects=[pe.withStroke(linewidth=3, foreground=BG2)])
mapax(ax, -8.3, 2.0, 49.8, 58.8)
# legend
lx = fig.add_axes([.05, .262, .5, .03]); lx.axis("off"); lx.set_xlim(0, 1); lx.set_ylim(0, 1)
for i, c in enumerate(RES):
    lx.add_patch(Rectangle((i * .1, .55), .1, .45, fc=c, ec="none"))
lx.text(0, 0, "under half", family=MONO, fontsize=10, color=MUT2); lx.text(.5, 0, "over twice", family=MONO, fontsize=10, color=MUT2, ha="right")
lx.text(.54, .5, "mentions against what population predicts\n(towns of 50,000+; grey: smaller places)", family=MONO, fontsize=10, color=MUT2, va="center")

# big numbers
tx = fig.add_axes([.62, .3, .36, .565]); tx.axis("off")
items = [
    (f"{L['share_2005_2025']}%", "INK", f"of all town and city mentions since 2005\nare of London, down from {D['1910']}% in the 1910s"),
    (f"{OE[0][1]}x", "OVER", f"{OE[0][0]}: mentioned {OE[0][1]} times what a town\nof its size gets, the most of any town"),
    (f"{round(cards['West Ham']['ratio'])}x", "OVER", f"West Ham's share of mentions in {cards['West Ham']['year']}, against\nits usual year: the Boards of Guardians Bill"),
    (f"{R['seat_own_share_median']}%", "GRN", "of the speeches naming a seat come from\nits own MP (median seat, 2005 to 2026)"),
]
cmap = {"INK": INK, "OVER": OVER, "GRN": GRN}
y = .99
for big, c, small in items:
    tx.text(0, y, big, fontproperties=DISP, fontsize=46, color=cmap[c], va="top", transform=tx.transAxes)
    tx.text(0, y - .1, small, family=SER, fontsize=13.5, color=FG2, va="top", transform=tx.transAxes, linespacing=1.3)
    y -= .25

# bottom row: four peaks and London's share
fig.text(.047, .242, "ONE BIG YEAR: SHARE OF ALL TOWN MENTIONS, 1909 TO 2025", family=MONO, fontsize=11, color=MUT2)
pk = ["Jarrow", "Omagh", "Redcar", "Port Talbot"]
for i, t in enumerate(pk):
    YA = json.load(open(os.path.join(ROOT, "data", "page", "years.json")))
    pr = next(q for q in P if q["term"] == t)
    c = {"year": int(pr["peak_year"]), "series": [1e4 * v / d if d else 0 for v, d in zip(YA[t][:2025 - 1909 + 1], R["den"])]}
    a = fig.add_axes([.047 + i * .145, .115, .125, .105])
    s = c["series"]; ys = np.arange(1909, 1909 + len(s))
    a.fill_between(ys, s, color=INK, alpha=.18, lw=0); a.plot(ys, s, color=INK, lw=1.3)
    a.axvline(c["year"], color=OVER, lw=1, ls=":")
    a.set_title(f"{t}, {c['year']}", family=SER, fontsize=12.5, loc="left", color=FG2, pad=4)
    a.set_yticks([]); a.set_xticks([1920, 2020]); a.tick_params(axis="x", labelsize=10, colors=MUT2)
    for sp in ("left", "top", "right"):
        a.spines[sp].set_visible(False)
    a.spines["bottom"].set_color(MUT2); a.set_facecolor(BG2)
a = fig.add_axes([.64, .115, .32, .105]); a.set_facecolor(BG2)
ks = list(D)
a.bar(range(len(ks)), [D[k] for k in ks], color=INK, width=.75)
a.set_title("London's share of town mentions, by decade", family=SER, fontsize=12.5, loc="left", color=FG2, pad=4)
a.set_xticks([0, len(ks) - 1]); a.set_xticklabels([ks[0] + "s", ks[-1] + "s"], fontsize=10, color=MUT2)
a.text(0, D[ks[0]] + 1.5, f"{D[ks[0]]}%", ha="center", family=MONO, fontsize=10, color=FG2)
a.text(len(ks) - 1, D[ks[-1]] + 1.5, f"{D[ks[-1]]}%", ha="center", family=MONO, fontsize=10, color=FG2)
a.set_yticks([]); a.set_ylim(0, 58)
for sp in ("left", "top", "right"):
    a.spines[sp].set_visible(False)
a.spines["bottom"].set_color(MUT2)

fig.text(.047, .064, "Counts of spoken House of Commons contributions containing \"in\" plus the name. Shared names, namesakes abroad and ordinary words\n"
         "with low precision are left out; other ordinary-word names are scaled by a capital-letter check. Counts of words, not judgements.",
         family=MONO, fontsize=9.5, color=MUT2, linespacing=1.45)
fig.text(.047, .012, "Data: UK Parliament Hansard API and Members API (Open Parliament Licence v3.0); ONS Census 2021 built-up areas, OS Open Names\n"
         "(Open Government Licence v3.0); GeoNames (CC BY 4.0). Analysis and chart: Tristan Hotham, with Python and matplotlib.\n"
         "Interactive map: maps.tristanhotham.com/hansard-places",
         family=MONO, fontsize=9.5, color=MUT2, linespacing=1.45)
out = os.path.join(HERE, "mentioned_in_the_house.png")
fig.savefig(out, dpi=200, facecolor=BG2)
print(out)
