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
def search_grid_with_drones(grid, tree, num_drones):
    GRID_SIZE = grid.size()
    #get real drone  instead of randomizing
    drone_positions = [(random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)) for _ in range(num_drones)]
    visited = set()

    for drone_id in range(num_drones):
        start = drone_positions[drone_id]
        # Find the highest-priority cell
        highest_priority_cell = (0,0)
        for i in range(GRID_SIZE):
            for j in range(GRID_SIZE):
                cost = heuristic(start, (i,j))
                total=
                
        highest_priority_cell = max([(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE)], key=lambda x: grid[x[0]][x[1]])
        print(f"Drone {drone_id+1} starts at {start} and is going to {highest_priority_cell}.")

        
        path = astar(grid, start, highest_priority_cell)

        # Mark the visited squares
        for pos in path:
            visited.add(pos)
            print(f"Drone {drone_id+1} visited {pos} with priority {grid[pos[0]][pos[1]]}")

        # Mark the highest priority cell as visited for future drones
        visited.add(highest_priority_cell)
        
        print(f"Drone {drone_id+1} completed its search.")
