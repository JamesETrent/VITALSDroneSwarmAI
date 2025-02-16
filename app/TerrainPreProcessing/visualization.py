from shapely.geometry import Point, Polygon, MultiPolygon
from .geometry_utils import haversine
import matplotlib.colors as mcolors
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt

def plot_postGIS_data(data, colors = []):
    gdf = gpd.GeoDataFrame(data, crs="EPSG:3857")
    gdf = gdf.to_crs(epsg=4326)
    # Define base colors in RGBA format

    def mix_colors(row):
        """Mix colors based on the categories present in the row."""
        present_colors = [colors[key] for key in colors if row.get(key) is not None]
        
        if not present_colors:
            #print("No color, default grey")
            return (0.5, 0.5, 0.5, 1)  # Default gray if no category is present

        # Convert to NumPy array and average across all present colors
        mixed_color = np.mean(np.array(present_colors), axis=0)
        
        return tuple(mixed_color)  # Return as RGBA tuple

    # Create a new 'color' column in the GeoDataFrame based on mixed colors
    gdf["color"] = gdf.apply(mix_colors, axis=1)

    # Convert RGBA to Hex for plotting
    gdf["color_hex"] = gdf["color"].apply(lambda rgba: mcolors.to_hex(rgba))

    # Plot the map
    ax = gdf.plot(color=gdf["color_hex"], figsize=(10, 6), edgecolor="black", alpha=0.7)
    ax.set_title("Blended Colors for Mixed Categories")

def plot_search_area(rtree_index, grid, polygon_points):
    if not rtree_index:
        print("Failed! Area probably too small!")
        return
        
    all_items = list(rtree_index.intersection(rtree_index.bounds, objects=True))
    preserved_polygons = []
    for r in all_items:
        data = r.object
        preserved_polygons.append(data["geometry"])

    gdf = gpd.GeoDataFrame(geometry=preserved_polygons)
    ax = gdf.plot(edgecolor='black', facecolor='blue')  # Default to blue
    #gdf.iloc[[2]].plot(ax=ax, edgecolor='black', facecolor='red')
    #Show the grids
    #overlay_gdf = gpd.GeoDataFrame(geometry=all_poly) 
    # Overlay the new polygons in red with transparency (alpha)
    #overlay_gdf.plot(ax=ax, edgecolor="black", facecolor="red", alpha=0.5)
    tile_length = None
    for i in range(len(grid)):
        for j in range(len(grid)):
            tile = grid[i][j]
            if tile_length is None:
                t_left = tile.polygon.exterior.coords[0]  # First point (top-left or bottom-left, depending on order)
                t_right = tile.polygon.exterior.coords[1]  # Second point (next in sequence)
                tile_length = haversine(t_left[1],t_left[0], t_right[1],t_right[0])
                print("OI!")
            centroid = tile.polygon.centroid
            # Annotate with the counts
            text = f"{tile.contains_count['building']},{tile.contains_count['water']}"

            if not tile.in_searcharea:
                text = "X"

            ax.annotate(text, (centroid.x, centroid.y), color='white', 
                        fontsize=6, ha='center', va='center', fontweight='bold')
            # Plot the polygon of each tile
            x, y = tile.polygon.exterior.xy  # Get the coordinates of the polygon
            ax.fill(x, y, edgecolor='black', facecolor='red', alpha=0.5, linewidth=1)
    
    print(f"Tile Length: {tile_length}")
    if tile_length:
        ax.text(0.05, 0.95, f"Tile Length: {tile_length:.2f} meters", 
        transform=ax.transAxes, color='black', fontsize=8, 
        ha='left', va='top', fontweight='bold', bbox=dict(facecolor='white', alpha=0.7))
 
    #Show the original area
    reversed_search_area = [(point[1], point[0]) for point in polygon_points]
    new_polygon = Polygon(reversed_search_area)
    new_polygon_gdf = gpd.GeoDataFrame(geometry=[new_polygon])
    new_polygon_gdf.plot(ax=ax, edgecolor="black", facecolor="green", alpha=0.3)


    plt.show()