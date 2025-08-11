# Helper functions for grid creation, coverage, scoring, greedy selection.

# utils.py
from shapely.geometry import Point, Polygon
import geopandas as gpd
import numpy as np
import math

def create_hex_grid(bounds, hex_radius, crs):

    minx, miny, maxx, maxy = bounds
    w = hex_radius * 2
    h = math.sqrt(3) * hex_radius
    # horizontal step: 1.5 * r
    dx = 1.5 * hex_radius
    dy = h

    cols = int((maxx - minx) / dx) + 3
    rows = int((maxy - miny) / dy) + 3

    polys = []
    centers = []
    for row in range(-1, rows + 1):
        for col in range(-1, cols + 1):
            cx = minx + col * dx
            cy = miny + row * dy
            # offset every other column
            if col % 2 == 0:
                cy += dy / 2.0
            # build hexagon
            angle = 0
            coords = []
            for i in range(6):
                ang = math.radians(60 * i + 30)
                x = cx + hex_radius * math.cos(ang)
                y = cy + hex_radius * math.sin(ang)
                coords.append((x, y))
            poly = Polygon(coords)
            polys.append(poly)
            centers.append((cx, cy))
    gdf = gpd.GeoDataFrame({"geometry": polys})
    gdf["center_x"] = [c[0] for c in centers]
    gdf["center_y"] = [c[1] for c in centers]
    gdf = gdf.set_crs(crs)
    return gdf

def compute_coverage(pop_gdf, station_gdf, coverage_m):

    buffers = station_gdf.copy()
    buffers["geometry"] = buffers.geometry.buffer(coverage_m)
    # union buffers for faster contains (optional)
    union = buffers.unary_union
    covered_mask = pop_gdf.geometry.apply(lambda p: union.contains(p))
    return covered_mask

def score_hexes(hex_gdf, pop_gdf, covered_mask):

    pop_gdf = pop_gdf.copy()
    pop_gdf["covered"] = covered_mask.values
    # spatial join: which hex each pop point is in
    joined = gpd.sjoin(pop_gdf, hex_gdf[["geometry"]], how="left", predicate="within")
    # group
    grp = joined[~joined["covered"]].groupby("index_right")["population"].sum()
    hex_gdf = hex_gdf.copy()
    hex_gdf["uncovered_pop"] = hex_gdf.index.map(lambda i: float(grp.get(i, 0.0)))
    return hex_gdf

def greedy_select(hex_gdf, pop_gdf, k, station_coverage):

    proposals = []
    pop = pop_gdf.copy()
    pop["covered"] = pop.get("covered", False)
    # build spatial index for hex centers -> polygon center points for distance checks
    for step in range(k):
        # compute uncovered pop per hex
        # for performance, rely on precomputed hex.uncovered_pop: recompute from pop points
        # map pop points to hex index
        joined = gpd.sjoin(pop[~pop["covered"]], hex_gdf[["geometry"]], how="left", predicate="within")
        grp = joined.groupby("index_right")["population"].sum()
        if grp.empty:
            break
        best_idx = grp.idxmax()
        best_pop = float(grp.max())
        if best_idx is None or best_pop <= 0:
            break
        # propose at hex center
        cx = hex_gdf.loc[best_idx, "center_x"]
        cy = hex_gdf.loc[best_idx, "center_y"]
        # mark pop points within station_coverage of (cx,cy) as covered
        center_point = Point(cx, cy)
        mask_new = pop.geometry.distance(center_point) <= station_coverage
        newly_covered_count = pop.loc[mask_new & ~pop["covered"], "population"].sum()
        pop.loc[mask_new, "covered"] = True
        proposals.append({"center_x": cx, "center_y": cy, "covered_population": newly_covered_count})
    return proposals
