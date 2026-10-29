"""Step 6. header.png (1200 by 630) and the static figures for the blog (release/blog/b_*.png, 1520 px wide) and the
paper (release/paper/fig_*.png, the same images)."""
import csv, json, math, os, shutil, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from figlib import *

P = list(csv.DictReader(open(os.path.join(ROOT, "data", "places.csv"), encoding="utf-8")))
for p in P:
    for k in ("lat", "lon", "in_2005_2025", "in_1909_2025", "pop", "resid", "per100k"):
        p[k] = float(p[k]) if p[k] not in ("", None) else None
S = list(csv.DictReader(open(os.path.join(ROOT, "data", "constituencies.csv"), encoding="utf-8")))
YA = json.load(open(os.path.join(ROOT, "work", "years_in.json")))
BL = os.path.join(ROOT, "release", "blog"); PA = os.path.join(ROOT, "release", "paper")
os.makedirs(BL, exist_ok=True); os.makedirs(PA, exist_ok=True)
clean = [p for p in P if not p["flag"]]


def save(fig, name):
    fig.savefig(os.path.join(BL, "b_" + name + ".png"), dpi=160)
    plt.close(fig)
    shutil.copy(os.path.join(BL, "b_" + name + ".png"), os.path.join(PA, "fig_" + name + ".png"))


def bubbles(ax, scale=1.0, label_n=12, fs=10):
    pts = sorted(clean, key=lambda p: -p["in_2005_2025"])
    for p in pts:
        s = scale * p["in_2005_2025"] / 18243 * 2600
        ax.scatter(p["lon"], p["lat"], s=max(s, 1.2), c=res_col(p["resid"]) if p["resid"] is not None else "#8F8B80", alpha=.88 if p["resid"] is not None else .6,
                   edgecolors=BG, linewidths=.4, zorder=3)
    done = []
    for p in pts[:60]:
        if len(done) >= label_n:
            break
        if any(abs(p["lon"] + len(p["term"]) * .06 - q[0]) < (len(p["term"]) + q[2]) * .06 + .1 and abs(p["lat"] - q[1]) < .22 for q in done):
            continue
        done.append((p["lon"] + len(p["term"]) * .06, p["lat"], len(p["term"])))
        ax.text(p["lon"] + .12, p["lat"] + .1, p["term"], family=MONO, fontsize=fs, color=FG, zorder=5,
                path_effects=[__import__("matplotlib.patheffects", fromlist=["x"]).withStroke(linewidth=2.5, foreground=BG)])


# ---------- header ----------
fig = plt.figure(figsize=(12, 6.3), dpi=100)
fig.text(.045, .80, "Mentioned in", fontproperties=DISP, size=58, color=FG, va="bottom")
fig.text(.045, .665, "the House", fontproperties=DISP, size=58, color=HOT, va="bottom")
fig.text(.047, .54, "Which UK towns and cities do MPs\ntalk about? A century of Hansard,\ncounted place by place", family=SER, size=19, color=FG, va="top", linespacing=1.35)
fig.text(.047, .25, f"{R['in_total_1909_2025']:,} Commons mentions, 1909 to 2025", family=MONO, size=13, color=MUT)
fig.text(.047, .085, "maps.tristanhotham.com/hansard-places", family=MONO, size=12, color=MUT)
ax = fig.add_axes([.52, .02, .46, .96]); land(ax, ireland=True); bubbles(ax, scale=.75, label_n=7, fs=9); mapax(ax, -8.2, 2.0, 49.9, 58.7)
fig.savefig(os.path.join(ROOT, "header.png"), dpi=100)
plt.close(fig)

# ---------- 1. the map: mentions 2005 to 2025, coloured by mentions against population ----------
fig = plt.figure(figsize=(9.5, 11))
ax = fig.add_axes([0, .07, 1, .93]); land(ax); bubbles(ax, 1.0, 16, 11); mapax(ax, -8.3, 2.0, 49.8, 58.9)
lx = fig.add_axes([.06, .005, .88, .065]); lx.axis("off")
labs = ["under half", "", "about as expected", "", "over twice"]
for i, c in enumerate(RES):
    lx.add_patch(__import__("matplotlib.patches", fromlist=["x"]).Rectangle((i * .12, .45), .12, .4, fc=c, ec="none"))
lx.text(0, .05, "under half", family=MONO, fontsize=11, color=MUT); lx.text(.6, .05, "over twice", family=MONO, fontsize=11, color=MUT, ha="right")
lx.text(.3, .05, "as expected", family=MONO, fontsize=11, color=MUT, ha="center")
lx.text(.64, .62, "Colour: mentions against what population\npredicts (towns of 50,000 or more).\nGrey dots: smaller places. Circle area:\n\"in\" plus the name, 2005 to 2025.", family=MONO, fontsize=10, color=MUT, va="center")
lx.set_xlim(0, 1); lx.set_ylim(0, 1)
save(fig, "map")

# ---------- 2. top 20 ----------
fig, ax = plt.subplots(figsize=(9.5, 7.2))
top = R["top_in_2005_2025"][:20][::-1]
ax.barh([t for t, _ in top], [v for _, v in top], color=[HOT] * 19 + [HOT2], height=.7)
for i, (t, v) in enumerate(top):
    ax.text(v + 150, i, f"{v:,}", va="center", family=MONO, fontsize=11, color=FG)
ax.set_xlabel("Commons contributions containing \"in\" plus the name, 2005 to 2025", family=MONO, fontsize=11, color=MUT)
ax.tick_params(axis="y", labelsize=12.5); ax.tick_params(axis="x", labelsize=10)
ax.set_xlim(0, 21000); ax.xaxis.set_major_formatter(__import__("matplotlib.ticker", fromlist=["x"]).FuncFormatter(lambda v, _: f"{v:,.0f}")); fig.tight_layout()
save(fig, "top")

# ---------- 3. population and mentions ----------
fig, ax = plt.subplots(figsize=(9.5, 7))
ph = [p for p in P if p["per100k"] is not None]
ax.scatter([p["pop"] for p in ph], [max(p["in_2005_2025"], 3) for p in ph], c=[res_col(p["resid"]) for p in ph], s=34, edgecolors=BG, linewidths=.5, zorder=3)
xx = np.array([4e4, 1.2e7]); ax.plot(xx, 10 ** (R["fit_a"] + R["pop_elasticity"] * np.log10(xx)), ls="--", color=MUT, lw=1.3, zorder=2)
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("population", family=MONO, fontsize=11, color=MUT); ax.set_ylabel("mentions, 2005 to 2025", family=MONO, fontsize=11, color=MUT)
lab = {t for t, *_ in R["over_expected"][:6]} | {t for t, *_ in R["under_expected"][-3:]} | {t for t, _ in R["top_in_2005_2025"][:6]}
boxes = []
for p in sorted(ph, key=lambda p: -p["in_2005_2025"]):
    if p["term"] not in lab:
        continue
    x, y = math.log10(p["pop"]), math.log10(max(p["in_2005_2025"], 3))
    if any(abs(x - a) < .32 and abs(y - b) < .09 for a, b in boxes):
        continue
    boxes.append((x, y)); ax.annotate(p["term"], (p["pop"], max(p["in_2005_2025"], 3)), xytext=(5, 3), textcoords="offset points", family=MONO, fontsize=10.5, color=FG)
from matplotlib.ticker import FuncFormatter
fmtk = FuncFormatter(lambda v, _: f"{v / 1e6:g}m" if v >= 1e6 else (f"{v / 1e3:g}k" if v >= 1e3 else f"{v:g}"))
ax.xaxis.set_major_formatter(fmtk); ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
ax.set_ylim(3, 40000); ax.set_xlim(4e4, 1.3e7)
ax.grid(color=RULE, lw=.6, which="major"); fig.tight_layout()
save(fig, "scatter")

# ---------- 4. London share and the nations ----------
fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.5, 4.6))
d = R["london_share_by_decade"]; ks = list(d)
a1.bar(range(len(ks)), [d[k] for k in ks], color=HOT, width=.75)
a1.set_xticks(range(len(ks))); a1.set_xticklabels(["'" + k[2:] for k in ks], family=MONO, fontsize=9.5)
a1.set_ylabel("London's share of town mentions (%)", family=MONO, fontsize=10, color=MUT)
for i, k in enumerate(ks):
    if i % 2 == 0 or i == len(ks) - 1:
        a1.text(i, d[k] + .8, f"{d[k]:g}", ha="center", family=MONO, fontsize=9, color=FG)
for n, c in NATC.items():
    v = R["nat_per100"][n]
    a2.plot(range(len(ks)), [v[k] for k in ks], color=c, lw=2.2, marker="o", ms=3.5, label=n)
a2.set_xticks(range(len(ks))); a2.set_xticklabels(["'" + k[2:] for k in ks], family=MONO, fontsize=9.5)
a2.set_ylabel("nation mentions per 100 town mentions", family=MONO, fontsize=10, color=MUT)
a2.legend(frameon=False, prop={"family": MONO, "size": 9.5})
for a in (a1, a2):
    a.grid(axis="y", color=RULE, lw=.6); a.set_axisbelow(True)
fig.tight_layout()
save(fig, "decades")

# ---------- 5. spikes: small multiples ----------
cards = R["spike_cards"][:12]
fig, axs = plt.subplots(4, 3, figsize=(9.5, 9.2), sharex=True)
for ax, c in zip(axs.flat, cards):
    s = c["series"]; ys = list(range(1909, 1909 + len(s)))
    ax.fill_between(ys, s, color=HOT, alpha=.18, lw=0); ax.plot(ys, s, color=HOT, lw=1.2)
    ax.axvline(c["year"], color=OVER, lw=1, ls=":")
    ax.set_title(f"{c['term']}, {c['year']}", family=SER, fontsize=12.5, loc="left", color=FG, pad=3)
    ax.set_title(f"{c['ratio']:.0f}x", family=MONO, fontsize=10.5, loc="right", color=OVER, pad=3)
    ax.set_yticks([]); ax.spines["left"].set_visible(False)
    ax.tick_params(axis="x", labelsize=9.5)
    ax.set_xticks([1920, 1970, 2020])
fig.tight_layout(h_pad=1.2)
save(fig, "spikes")

# ---------- 6. seats: own-member share ----------
fig, ax = plt.subplots(figsize=(9.5, 4.8))
b = R["own_hist"]
ax.bar([e + 2.5 for e in b["edges"][:-1]], b["counts"], width=4.4, color=GREEN)
ax.axvline(R["seat_own_share_median"], color=FG, ls="--", lw=1.2)
ax.text(R["seat_own_share_median"] + 1.2, max(b["counts"]) * .92, f"median {R['seat_own_share_median']}%", family=MONO, fontsize=11, color=FG)
ax.set_xlabel("share of a seat's mentions spoken by its own MP (%)", family=MONO, fontsize=11, color=MUT)
ax.set_ylabel("seats", family=MONO, fontsize=11, color=MUT); ax.set_xlim(0, 100)
ax.grid(axis="y", color=RULE, lw=.6); ax.set_axisbelow(True); fig.tight_layout()
save(fig, "seats")
print("figures done")
