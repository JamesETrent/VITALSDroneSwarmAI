from .geometry_utils import find_extreme_coordinates, rectangle_side_lengths, add_meters_to_latitude, add_meters_to_longitude, Tile
from .osmnx_handler import osmnx_load_rtree
from .postgis_handler import query_osm_features, postgis_load_rtree
from .visualization import plot_postGIS_data, plot_search_area
from rtree import index
from shapely import Polygon
import osmnx as ox
import socket
import pandas as pd

def has_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False
    
def get_features(rtree_index, useOSMNX: bool, osmnx_points, postGIS_points, search_tags):

    if useOSMNX:
        print("Getting information from OSMNX")
        if not has_internet():
            useOSMNX = False
            print("No Internet! Attempting to use PostGIS database")
        if useOSMNX:
            #Will cause an error if nothing is gotten from it!
            #osmnx._errors.InsufficientResponseError: No matching features. Check query location, tags, and log.
            results = ox.features_from_bbox(osmnx_points,search_tags)
            results.plot()
            print(len(results))
            osmnx_load_rtree(rtree_index,search_tags, results)
            return True

    if not useOSMNX:
        print("Getting information from PostGIS database")
        info =  query_osm_features(search_tags, postGIS_points)
        
        #Failed to get information from the POSTGIS database, we screwed. 
        if info is None:
            return False
        if info:
            plot_postGIS_data(info)
        print(len(info))
        postgis_load_rtree(rtree_index, info)


    #Should return False if no internet, and failed to connect to the POSTGIS database.
    return True
    


def create_search_area(polygon_points, search_tags, useOSMX = True,maximum_square_size = 60, minimum_grid_size = 8):
    extremes = find_extreme_coordinates(polygon_points)

    top_left = (extremes["highest_latitude"],extremes["leftmost_longitude"])
    bottom_right = (extremes["lowest_latitude"], extremes["rightmost_longitude"])

    # Calculate grid size
    width, height = rectangle_side_lengths(top_left[0],top_left[1], bottom_right[0], bottom_right[1])
    print(f"Rectangle width: {width:.2f} meters")
    print(f"Rectangle height: {height:.2f} meters")

    # Use the max dimension for the grid cell size
    size = max(width, height)
    temp = size
    level_count = 0

    #The thing is that if temp > maximum_square_size, it won't split at all. I should set a minimum. 
    #If the search area is < 8* maximum_square_size, override and turn the grid into an 8x8.
    if size >= minimum_grid_size*maximum_square_size:
        #Length wise, how long in meters should each square on the grid be? Right now it's 60
        while temp > maximum_square_size:  # Ensuring tile size is reasonable
            level_count += 1
            temp /= 2
        
        grid_length = 2 ** level_count
    else:
        temp = size/minimum_grid_size
        grid_length = minimum_grid_size

    grid = [[Tile() for _ in range(grid_length)] for _ in range(grid_length)]

    square_size = temp

    print(f"Square Size (in metters): {square_size}")


    bottom_left, top_right = (extremes["lowest_latitude"],extremes["leftmost_longitude"]),(extremes["highest_latitude"],extremes["rightmost_longitude"])

    osmnx_points = (*bottom_left[::-1], *top_right[::-1])
    postGIS_points = [(lat,lon) for lon,lat in polygon_points]
    #gather the data from osmnx
    #results = ox.features_from_bbox(points,search_tags)
    #results.plot()
    rtree_index = index.Index()
    #osmnx_load_rtree(rtree_index,search_tags,results)
    success = get_features(rtree_index, useOSMX, osmnx_points,postGIS_points, search_tags)

    if not success:
        print("unable to create a search area")
        return None,None

    fill_grid_data(rtree_index, grid, top_left, square_size, search_tags, postGIS_points)

    return rtree_index, grid
    # Generate tiles and fetch OSM features


def fill_grid_data(rtree_index, grid, top_left, square_size, search_tags,postGIS_points):
    #Note. I need to make it so that if a square doesn't intersect with the search area, that it's marked as Unavailable. 
    #This will let the drone know that although this grid is here, it's not part of the search area, and thus shouldn't be explored. 
    count = 0
    t_left = [0,0]
    b_right = [0,0]
    actual_search_area = Polygon(postGIS_points)
    for i in range(len(grid)):
        t_left[0] = top_left[0] if i == 0 else add_meters_to_latitude(top_left[0],(i*(-square_size)))
        b_right[0] = add_meters_to_latitude(top_left[0],((i+1)*(-square_size)))
        for j in range(len(grid)):
            t_left[1] = top_left[1] if j == 0 else add_meters_to_longitude(t_left[0], top_left[1], j*square_size)
            b_right[1] = add_meters_to_longitude(b_right[0], top_left[1], (j+1)*square_size)
            #'28.6178539,-81.2237312,#00FF00,marker,"Point # T_L"'
            
            b_left = [b_right[0], t_left[1]]
            t_right = [t_left[0],b_right[1]]
            
            #minx, miny, maxx, maxy
            #minLongitude, minLatitude, MaxLongitude, MaxLatitude
            search_bb = (b_left[1],b_left[0],t_right[1],t_right[0])
            result = list(rtree_index.intersection(search_bb,objects=True))
            grid[i][j].contains_count = {tag: 0 for tag in search_tags}
            grid[i][j].contains = {tag: [] for tag in search_tags}
            for r in result:
                data = r.object
                for tag in search_tags:
                        if tag not in data:
                            continue
                        if not pd.isna(data[tag]):
                            #Only increase to the count, and add to the contains if it wasn't nan
                            grid[i][j].contains_count[tag] += 1
                            grid[i][j].contains[tag].append(data["geometry"])

            flipped_coordinates = [(lon, lat) for lat, lon in [t_left,t_right,b_right,b_left]]
            grid[i][j].polygon = Polygon(flipped_coordinates)
            grid[i][j].in_searcharea = actual_search_area.intersects(grid[i][j].polygon)
            count+= 1
            #print(f'{t_left[0]},{t_left[1]},#00FF00,marker,"Point #{i},{j} T_L"')
            #print(f'{b_right[0]},{b_right[1]},#00FF00,marker,"Point #{i},{j} B_R"')