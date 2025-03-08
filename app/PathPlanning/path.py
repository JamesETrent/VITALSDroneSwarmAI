import random
from GUI import GUI
from Dispatcher import Dispatcher
import asyncio
import threading
import heapq

# Define grid size and priorities

# Directions for moving up, down, left, right
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# Function to calculate the heuristic (Manhattan distance)
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# Function to make drones search a grid based on priority
def search_grid_with_drones(grid, tree, num_drones = 4):
    GRID_SIZE = len(grid)
    #get real drone  instead of randomizing
    drone_positions = [(random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)) for _ in range(num_drones)]
    visited = set()
    precomp_destinations = {x: [] for x in range(num_drones)}

    potential_search_areas = []
    #Inefficient, but works for now. 
    for i in range(len(grid)):
        for j in range(len(grid[0])):
            print(f"Test:({i},{j}) - InArea:{grid[i][j].in_searcharea}, Priority: {grid[i][j].contains_count}")
            if(not grid[i][j].in_searcharea or grid[i][j].total_count == 0):
                continue
            potential_search_areas.append((i,j))

    print(f"Potential Search Areas: {len(potential_search_areas)}")

    while(len(potential_search_areas) > 0):
        for drone_id in range(num_drones):
            if(len(potential_search_areas) == 0):
                break
            start = drone_positions[drone_id]
            highest_priority_cell = max(potential_search_areas, key=lambda x: grid[x[0]][x[1]].total_count*10 - heuristic(start, x))
            precomp_destinations[drone_id].append(highest_priority_cell)
            potential_search_areas.remove(highest_priority_cell)

    """
    while len(visited) < GRID_SIZE*GRID_SIZE:
        for drone_id in range(num_drones):
            start = drone_positions[drone_id]
            # Find the highest-priority cell
            visited.add(start)
            highest_priority_cell = max([(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE) if (i,j) not in visited and grid[i][j].in_searcharea], key=lambda x: grid[x[0]][x[1]].total_count*10 - heuristic(start, x))
            visited.add(highest_priority_cell)
            print(f"Drone {drone_id+1} starts at {start} and is going to {highest_priority_cell}.")

            precomp_destinations[drone_id].append(highest_priority_cell)
            #path = astar(grid, start, highest_priority_cell)

            # Mark the visited squares
            #for pos in path:
            #    visited.add(pos)
            #    print(f"Drone {drone_id+1} visited {pos} with priority {grid[pos[0]][pos[1]]}")

            # Mark the highest priority cell as visited for future drones
            #visited.add(highest_priority_cell)
            
            print(f"Drone {drone_id+1} completed its search.")"
    """
    for drone_id in range(num_drones):
<<<<<<< HEAD
        print(f"Drone ID: {drone_id}, Locations: {precomp_destinations[drone_id]}")
=======
        start = drone_positions[drone_id]
        # Find the highest-priority cell
        highest_priority_cell = (0,0)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                cost = heuristic(start, (i,j))
                total=
                
        distance = ()^(1/2)
        highest_priority_cell = max([(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE)], key=lambda x: grid[x[0]][x[1]].total_count - heuristic(start, x))
        print(f"Drone {drone_id+1} starts at {start} and is going to {highest_priority_cell}.")

        # Mark the visited squares
        #for pos in path:
        #    visited.add(pos)
        #    print(f"Drone {drone_id+1} visited {pos} with priority {grid[pos[0]][pos[1]]}")

        # Mark the highest priority cell as visited for future drones
        #visited.add(highest_priority_cell)
        
        print(f"Drone {drone_id+1} completed its search.")
>>>>>>> 0ba01055201f271765f57509b10f2521294f87e4
