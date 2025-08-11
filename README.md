# EV Charging Station Optimization

Small Python project that identifies under-served areas for EV chargers and proposes new station locations.

Run:
1. (Optional) `python sample_data.py` to create dummy CSVs.
2. `python main.py --stations stations.csv --pop pop_points.csv --out plan.csv`

Outputs:
- CSV of proposed new station locations with estimated population covered.
- A PNG map (`coverage_map.png`) showing current coverage and proposed sites.

Dependencies: geopandas, pandas, shapely, rtree, matplotlib, numpy, scipy
