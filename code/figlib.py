"""Shared look for the header, the paper and blog figures, and the collage."""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
F = "/tmp/claude-0/-home-claude/c232619d-81e0-53f3-9de6-41e973630753/scratchpad/fonts/"
for f in ["FrauncesVar.ttf", "IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf", "SourceSerif4-Regular.ttf", "SourceSerif4-Semibold.ttf", "SourceSerif4-It.ttf"]:
    if os.path.exists(F + f):
        fm.fontManager.addfont(F + f)
DISP = fm.FontProperties(fname=F + "FrauncesVar.ttf", weight=900) if os.path.exists(F + "FrauncesVar.ttf") else fm.FontProperties(family="serif", weight="bold")
SER, MONO = "Source Serif 4", "IBM Plex Mono"
BG, FG, MUT, RULE, HOT, HOT2, GREEN, OVER, UNDER, LAND = "#F6F4EE", "#1A1C22", "#626570", "#D9D5C8", "#1F4F8B", "#14365F", "#2E6B4E", "#C0561B", "#5E7BA6", "#E6E2D6"
RES = ["#3E5F8F", "#7F98BE", "#C9C6BC", "#E3A06E", "#C0561B"]
NATC = {"England": "#8A5A2B", "Scotland": "#1F4F8B", "Wales": "#2E6B4E", "Northern Ireland": "#B23A48"}
plt.rcParams.update({"font.family": SER, "font.size": 13, "axes.edgecolor": MUT, "axes.labelcolor": FG, "xtick.color": MUT, "ytick.color": MUT,
                     "axes.spines.top": False, "axes.spines.right": False, "figure.facecolor": BG, "axes.facecolor": BG, "savefig.facecolor": BG})
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
NAT = json.load(open(os.path.join(ROOT, "data", "nations.geojson")))


def res_col(r):
    if r is None:
        return "#B4B0A6"
    b = [-.3, -.1, .1, .3]
    k = 0
    while k < 4 and r >= b[k]:
        k += 1
    return RES[k]


def land(ax, fc=LAND, ec="#9C9788", lw=.5, ireland=True):
    from matplotlib.patches import Polygon
    for f in NAT["features"]:
        if not ireland and f["properties"]["nation"] == "Ireland":
            continue
        g = f["geometry"]
        polys = g["coordinates"] if g["type"] == "MultiPolygon" else [g["coordinates"]]
        for poly in polys:
            ax.add_patch(Polygon(poly[0], closed=True, fc=fc, ec=ec, lw=lw, zorder=1))


def mapax(ax, x0=-8.3, x1=2.0, y0=49.8, y1=59.0):
    import math
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect(1 / math.cos(math.radians(54.5)))
    ax.axis("off")
