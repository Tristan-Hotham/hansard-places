# Mentioned in the House: which places does Parliament talk about?

Which UK towns and cities do MPs talk about in the House of Commons, and which do they hardly mention? This study counts place mentions in Hansard, year by year from 1909 to 2025, for 1,661 place names, and for every Commons seat in use from 2005 to October 2026 counts how often its name is said, and by whom. No speech text was downloaded: the UK Parliament Hansard API returns counts.

**Interactive version:** https://maps.tristanhotham.com/hansard-places/

**Paper:** https://doi.org/10.5281/zenodo.23761431

This repository holds the interactive page, the datasets, the computed results and the analysis code for a data study by Dr Tristan Hotham (Independent researcher).

## Headline results

- 297,134 Commons contributions from 1909 to 2025 contain "in" plus one of 1,597 unambiguous UK town and city names.
- London took 16.1% of town and city mentions from 2005 to 2025 (18,243 contributions), down from 48.8% in the 1910s and 28.4% in the 1950s to 11.2% in the 2020s. Glasgow, Birmingham, Manchester and Edinburgh follow.
- Mentions grow faster than population (elasticity 1.34, correlation 0.75 on log scales, 175 towns of 50,000 or more). Kettering was mentioned 6.47 times what its population predicts, then Rotherham (4.14), York (3.78) and Taunton (3.56).
- The strongest single-year peaks: West Ham in 1926 (Boards of Guardians (Default) Bill), Jarrow in 1936, Skelmersdale in 1976, Streatham in 2020, Omagh in 1998, Redcar in 2015 and Port Talbot in 2024.
- "In Northern Ireland" rose from 10.1 to 44.0 mentions per 100 town mentions between the 1960s and the 1970s; Scotland fell from 49.0 to 59.0 per 100 (1910s to 1970s) to 19.7 in the 2000s.
- Across 946 seat names (2005 to 2026), the seat's own MP spoke 10.9% of the contributions naming it (median seat 8.5%). 423,109 of 625,965 contain "Member for".
- Where a town and its seat share a name, the seat's own MP spoke 41% of the contributions naming Kettering, 35% for Harlow and 9% for Rotherham.

## Files

- `index.html`: the interactive page (map with mentions, for-its-size, year-by-year and seats views, Map layers panel, place search, charts, ambiguous-name table). Loads `data/page/` and `data/nations.geojson`.
- `header.png`: social card (1200 by 630).
- `data/places.csv`: one row per place term (1,661): point, nation, population and its source, "in" mentions 1909 to 2025 and 2005 to 2025, any mentions 2005 to 2025, ratio, per 100,000, ratio to the population trend (log10), peak year, peak count and ratio, ambiguity flags and the precision factor.
- `data/place_years.csv`: raw counts per term and year (as returned by the API, before scaling and prefix subtraction): "in" mentions from 1900 and any mentions from 2005.
- `data/constituencies.csv`: one row per seat name (946): point, years in use from 2005, number of members, mentions, mentions by its own members, by others, own share, "Member for" mentions, mentions a year.
- `data/ambiguous_names.csv`: every name that was flagged, scaled or marked, with the reason and the capital-letter sample.
- `data/results.json`: every number used on the page, in the paper, the blog post and the collage.
- `data/nations.geojson`, `data/page/`: map outlines and compact files for the page (`places.json`, `years.json` with yearly counts after scaling, `seats.json`, `labels.json`).
- `code/`: the analysis, run in order (below).
- `release/`: the paper (PDF, LaTeX source and figures), the blog post and figures, and the Zenodo files.
- `reddit/`: the collage, its script and the post text.

## How to rerun

1. `code/00_harvest_browser.js` is run in a web browser tab on https://hansard-api.parliament.uk/ (the API answers same-origin requests from there). It runs the timeline searches and saves `hansard_places_bundle.json.gz` (counts only, about 0.6 MB; retrieved 29 October 2026). The capital-letter samples and the peak-year debate titles were gathered in the same session with the contribution search, as described in the paper.
2. Then, with the bundle in `/home/claude/hist/_data18/hansard-places/` (or edit the path in `code/03_analyse.py`):

```
python3 code/01_places.py        # place list (GeoNames, OS Open Names)
python3 code/02_geo.py           # nation outlines and map labels
python3 code/03_analyse.py       # flags, measures, rankings, seats; data/*.csv and results.json
python3 code/04_page_data.py     # page files and extra numbers
python3 code/05_build_site.py    # index.html from code/page_template.html
python3 code/06_figures.py       # header.png and the blog and paper figures
python3 release/paper/build_paper.py
python3 release/build_release.py
python3 reddit/collage.py
```

It needs Python 3 with numpy, pandas, shapely and matplotlib, and xelatex for the paper. `01_places.py` and `03_analyse.py` read GeoNames `cities15000.zip`, OS Open Names, and the Census 2021 built-up area table from the Beeching cuts project; `03_analyse.py` reads constituency points from the Who Won Here? project.

## Method in brief

- **Measure**: Commons contributions of type Spoken containing the quoted phrase "in" plus the place name, per year (Hansard API timeline statistics). It avoids the "hon. Member for" formula, surnames and division lists. Any-mention counts are used only from 2005, because until 2004 the API files division lists (with members' seats in brackets) as spoken contributions.
- **Ambiguity**: shared names (26) and namesakes (29) are left out of rankings; 59 ordinary-word names were checked for capital letters in samples of up to 40 contributions and scaled by that precision, or left out below 60% (9); longer names that begin with a shorter one are subtracted from it (35 pairs).
- **Size**: log mentions against log population for real towns of 50,000 or more (Census 2021 built-up areas in England and Wales, GeoNames elsewhere).
- **Seats**: members since 2005 and their seats from the Members API; own mentions are those a member spoke while holding the seat.
- **Limits**: search counts depend on Parliament's index and on older scanned volumes; the "in" phrase is a sample of mentions; small precision samples; mixed population sources; today's UK only (Irish towns before 1922 are not counted); Lords, written questions and committees not included. Counts of words, not judgements of anyone's work.

## Sources and licences

- Hansard, House of Commons, via the UK Parliament Hansard API (https://hansard-api.parliament.uk/). Contains Parliamentary information licensed under the Open Parliament Licence v3.0.
- UK Parliament Members API (https://members-api.parliament.uk/), Open Parliament Licence v3.0.
- GeoNames cities15000, CC BY 4.0.
- OS Open Names (contains OS data © Crown copyright and database right 2026), ONS Census 2021 built-up areas and ONS county outlines, Open Government Licence v3.0. Natural Earth, public domain.
- Constituency points from Who Won Here? (https://doi.org/10.5281/zenodo.23761425; Wikidata CC0 and OS Open Names).
- Base map and hill shading tiles on the page © Esri.

Licence: data and text CC BY 4.0; code MIT (see LICENSE).

## Citation

Hotham, T. (2026) Mentioned in the House: which places does Parliament talk about? Place mentions in House of Commons debates, 1909 to 2026. https://doi.org/10.5281/zenodo.23761431

Blog post: https://blog.tristanhotham.com/2026/10/29/hansard-places/

I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped prepare the analysis code. I reviewed and checked all text and results.
