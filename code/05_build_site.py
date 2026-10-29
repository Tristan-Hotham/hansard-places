"""Step 5. Fill code/page_template.html from data/results.json to make index.html.
{{path.to.value}} and {{path|int}} placeholders take numbers from results.json; /*R*/ gets the summary the page uses."""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R = json.load(open(os.path.join(ROOT, "data", "results.json")))
T = open(os.path.join(ROOT, "code", "page_template.html"), encoding="utf-8").read()


def get(path):
    x = R
    for p in path.split("."):
        x = x[int(p)] if isinstance(x, list) else x[p]
    return x


def fill(mo):
    path, _, f = mo.group(1).partition("|")
    v = get(path.strip())
    if f == "int":
        return f"{int(round(v)):,}"
    return str(v)


T = re.sub(r"\{\{([^}]+)\}\}", fill, T)
keys = ["top_in_2005_2025", "top_in_1909_2025", "over_expected", "under_expected", "london_share_by_decade", "nat_per100", "own_hist",
        "seat_own_share_median", "spike_cards", "ambig", "stories", "den", "time_ref", "seat_ref", "fit_a", "pop_elasticity"]
small = {k: R[k] for k in keys}
T = T.replace("/*R*/", json.dumps(small, separators=(",", ":"), ensure_ascii=False))
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(T)
print("index.html", len(T))
