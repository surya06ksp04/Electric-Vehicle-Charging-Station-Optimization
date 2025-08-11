# main.py
import argparse
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point
from utils import create_hex_grid, compute_coverage, score_hexes, greedy_select
import matplotlib.pyplot as plt
import numpy as np

def load_csv_points(path, lon_col="longitude", lat_col="latitude", extra_cols=None):
    df = pd.read_csv(path)
    extra_cols = extra_cols or []
    gdf = gpd.GeoDataFrame(df[[lon_col, lat_col] + extra_cols].copy(),
                           geometry=gpd.points_from_xy(df[lon_col], df[lat_col]),
                           crs="EPSG:4326")
    return gdf

def project_to_meters(gdf):
    # Web Mercator for simple distance calculations (meters approx)
    return gdf.to_crs(epsg=3857)

def main(args):
    # Loading CSVs
    stations = load_csv_points(args.stations)
    pop = load_csv_points(args.pop, extra_cols=["population"])

    # Project to metric CRS for buffers/distances
    stations_m = project_to_meters(stations)
    pop_m = project_to_meters(pop)

    # choosing coverage radius (meters) for a charger (e.g., 3000 m driving+walking)
    coverage_m = args.coverage_m

    # computing which population points are currently covered
    covered_mask = compute_coverage(pop_m, stations_m, coverage_m)
    pop_m["covered"] = covered_mask

    # Building hex grid covering bounding box of pop points (expanded a bit)
    bounds = pop_m.total_bounds  # minx, miny, maxx, maxy (in meters)
    pad = 5000  # 5 km pad
    minx, miny, maxx, maxy = bounds
    bounds_padded = (minx - pad, miny - pad, maxx + pad, maxy + pad)

    hex_radius = args.hex_radius_m  # e.g., 3000 meters
    hex_gdf = create_hex_grid(bounds_padded, hex_radius, crs="EPSG:3857")

    # Score hexes by uncovered population inside them
    hex_scored = score_hexes(hex_gdf, pop_m, covered_mask)

    # Picking top N hexes (k new stations) using greedy placement to account for overlapping coverage
    proposals = greedy_select(hex_scored, pop_m, args.k, station_coverage=coverage_m)

    # Saving proposals to CSV
    out_df = pd.DataFrame(proposals)
    out_df.to_csv(args.out, index=False)
    print(f"Saved proposals to {args.out}")

    # Visualization
    fig, ax = plt.subplots(1, 1, figsize=(10, 10))
    base = hex_scored.to_crs(epsg=3857).plot(column="uncovered_pop", cmap="OrRd", ax=ax, alpha=0.6, edgecolor="k", linewidth=0.1)
    pop_m.plot(ax=base, markersize=2, column="covered", categorical=True, legend=True)
    stations_m.plot(ax=base, color="blue", marker="^", label="Existing stations", markersize=40)
    # plot proposals
    if not out_df.empty:
        prop_pts = gpd.GeoDataFrame(out_df, geometry=gpd.points_from_xy(out_df.center_x, out_df.center_y), crs="EPSG:3857")
        prop_pts.plot(ax=base, color="green", marker="X", markersize=80, label="Proposed stations")

    plt.legend()
    plt.title("EV Charging: uncovered pop by hex (darker = more uncovered)")
    plt.savefig("coverage_map.png", dpi=150)
    print("Saved coverage_map.png")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="EV Charging Station Optimization")
    parser.add_argument("--stations", default="stations.csv", help="CSV of existing stations (longitude,latitude)")
    parser.add_argument("--pop", default="pop_points.csv", help="CSV of population points (longitude,latitude,population)")
    parser.add_argument("--out", default="proposals.csv", help="Output CSV for proposed stations")
    parser.add_argument("--k", type=int, default=10, help="Maximum number of new stations to propose")
    parser.add_argument("--coverage_m", type=float, default=3000.0, help="Coverage radius in meters for a station")
    parser.add_argument("--hex_radius_m", type=float, default=3000.0, help="Hex grid radius in meters")
    args = parser.parse_args()
    main(args)
