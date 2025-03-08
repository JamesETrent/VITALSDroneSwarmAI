from GUI import GUI
from Dispatcher import Dispatcher
import asyncio
import threading
from TerrainPreProcessing.missionState import create_job
from TerrainPreProcessing.visualization import addMissionPolygon
import heapq

# Define grid size and priorities
GRID_SIZE = 10
PRIORITY_GRID = [[random.randint(1, 10) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

# Directions for moving up, down, left, right
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

# Function to calculate the heuristic (Manhattan distance)
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

# A* Search algorithm
def astar(grid, start, goal):
    open_list = []
    heapq.heappush(open_list, (0 + heuristic(start, goal), 0, start))  # f = g + h
    came_from = {}
    g_costs = {start: 0}
    
    while open_list:
        _, current_g, current = heapq.heappop(open_list)
        
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            return path
        
        for dx, dy in DIRECTIONS:
            neighbor = (current[0] + dx, current[1] + dy)
            if 0 <= neighbor[0] < GRID_SIZE and 0 <= neighbor[1] < GRID_SIZE:
                tentative_g = current_g + grid[neighbor[0]][neighbor[1]]
                
                if neighbor not in g_costs or tentative_g < g_costs[neighbor]:
                    came_from[neighbor] = current
                    g_costs[neighbor] = tentative_g
                    f_cost = tentative_g + heuristic(neighbor, goal)
                    heapq.heappush(open_list, (f_cost, tentative_g, neighbor))
    
    return []  # No path found

# Function to make drones search a grid based on priority
def search_grid_with_drones(grid, num_drones=4):
    drone_positions = [(random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1)) for _ in range(num_drones)]
    visited = set()

    for drone_id in range(num_drones):
        start = drone_positions[drone_id]
        # Find the highest-priority cell
        highest_priority_cell = max([(i, j) for i in range(GRID_SIZE) for j in range(GRID_SIZE)], key=lambda x: grid[x[0]][x[1]])
        print(f"Drone {drone_id+1} starts at {start} and is going to {highest_priority_cell}.")

        # Use A* to find the path
        path = astar(grid, start, highest_priority_cell)

        # Mark the visited squares
        for pos in path:
            visited.add(pos)
            print(f"Drone {drone_id+1} visited {pos} with priority {grid[pos[0]][pos[1]]}")

        # Mark the highest priority cell as visited for future drones
        visited.add(highest_priority_cell)
        
        print(f"Drone {drone_id+1} completed its search.")

# Run the drone search on the grid
search_grid_with_drones(PRIORITY_GRID)
