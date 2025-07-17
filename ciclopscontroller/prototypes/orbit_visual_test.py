import numpy as np
from sgp4.api import Satrec
import plotly.graph_objects as go
import os

# Example: Load TLEs from a text file (each TLE is 3 lines: name, line1, line2)
def load_tles(filename):
    tles = []
    with open(filename, 'r') as f:
        lines = f.readlines()
        for i in range(0, len(lines), 3):
            name = lines[i].strip()
            line1 = lines[i+1].strip()
            line2 = lines[i+2].strip()
            tles.append((name, line1, line2))
    return tles

# Propagate TLE to get position in ECI frame
def propagate_tle(satrec, tsince_min=0, minutes_span=90, step=10):
    jdsatepoch = satrec.jdsatepoch
    jdsatepochF = satrec.jdsatepochF
    positions = []
    for minute in range(tsince_min, minutes_span, step):
        e, r, v = satrec.sgp4(jdsatepoch, jdsatepochF + minute / 1440)  # minute since epoch
        if e == 0:
            positions.append(r)  # [x, y, z] in km
    return np.array(positions)

# Main visualization function
def visualize_orbits(tle_file):
    tles = load_tles(tle_file)
    fig = go.Figure()
    for name, line1, line2 in tles:
        satrec = Satrec.twoline2rv(line1, line2)
        pos = propagate_tle(satrec)
        if len(pos) > 0:
            fig.add_trace(
                go.Scatter3d(
                    x=pos[:,0], y=pos[:,1], z=pos[:,2],
                    mode='lines',
                    line=dict(width=1),
                    name=name
                )
            )
    # Add Earth sphere
    u, v = np.mgrid[0:2*np.pi:20j, 0:np.pi:10j]
    x = 6371 * np.cos(u) * np.sin(v)
    y = 6371 * np.sin(u) * np.sin(v)
    z = 6371 * np.cos(v)
    fig.add_trace(go.Surface(x=x, y=y, z=z, opacity=0.3, colorscale='Blues', showscale=False))
    fig.update_layout(scene=dict(
        xaxis_title='X (km)', yaxis_title='Y (km)', zaxis_title='Z (km)',
        aspectmode='data'
    ), title="Thousands of TLE Orbits")
    fig.show()

# Usage (assuming 'tle.txt' contains your TLEs)
visualize_orbits(os.path.join(os.path.dirname(__file__), 'tle.txt'))