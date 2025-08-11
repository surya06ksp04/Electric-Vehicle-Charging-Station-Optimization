# sample_data.py
import pandas as pd
import numpy as np

def create_dummy_stations(path="stations.csv", n=8, seed=0):
    np.random.seed(seed)
    # cluster around two centers to mimic urban/suburban
    centers = [(77.6, 12.97), (77.2, 13.02)]  # lon, lat roughly Bangalore-like
    pts = []
    for i in range(n):
        c = centers[i % len(centers)]
        lon = c[0] + np.random.normal(scale=0.08)
        lat = c[1] + np.random.normal(scale=0.05)
        pts.append({"id": f"S{i+1}", "longitude": lon, "latitude": lat})
    pd.DataFrame(pts).to_csv(path, index=False)
    print(f"Saved {path}")

def create_dummy_pop(path="pop_points.csv", n=500, seed=1):
    np.random.seed(seed)
    # generate population points in a bounding box
    lons = np.random.uniform(77.0, 78.0, size=n)
    lats = np.random.uniform(12.6, 13.3, size=n)
    pop = np.random.poisson(lam=300, size=n)  # people per point
    df = pd.DataFrame({"longitude": lons, "latitude": lats, "population": pop})
    df.to_csv(path, index=False)
    print(f"Saved {path}")

if __name__ == "__main__":
    create_dummy_stations()
    create_dummy_pop()
