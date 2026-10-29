# Reddit post

## Title

[OC] Which UK towns does Parliament talk about? 297,134 House of Commons mentions of 1,597 towns and cities in Hansard, 1909 to 2025: London's share fell from 48.8% to 11.2%

## Body

I counted how often MPs say "in" plus a town's name in the Commons, year by year, using Parliament's own Hansard search (counts only, no text downloaded). London still leads, with 16.1% of town mentions since 2005, but its share has fallen every few decades since the 1910s. Mentions grow faster than population, and some medium towns stand out: Kettering gets 6.47 times what its size predicts. Across seats since 2005, the median constituency's name is spoken by its own MP only 8.5% of the time; mostly it is other members saying "the hon. Member for". Caveat: names like Reading, Sale and Deal are also ordinary words, so I checked samples for capital letters and scaled or dropped them. Interactive map: https://maps.tristanhotham.com/hansard-places/

## Source comment

Source: UK Parliament Hansard API, timeline statistics and contribution search, House of Commons spoken contributions, and UK Parliament Members API (both Open Parliament Licence v3.0); ONS Census 2021 built-up areas and OS Open Names (Open Government Licence v3.0); GeoNames cities15000 (CC BY 4.0); constituency points from my Who Won Here? project.
Tools: Python (pandas, numpy, shapely, matplotlib), Leaflet for the interactive map.
Interactive map: https://maps.tristanhotham.com/hansard-places/
Blog post: https://blog.tristanhotham.com/2026/10/29/hansard-places/
Paper: https://doi.org/10.5281/zenodo.23761431
