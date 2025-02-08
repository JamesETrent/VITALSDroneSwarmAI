import requests
import json
import ollama


# Example data
mission_polygon = [
    (35.0, -120.0),
    (35.0, -120.1),
    (35.1, -120.1),
    (35.1, -120.0)
]
drones_status = [
  {"id": "drone_001", "battery": 80, "lat": 35.05, "lon": -120.05},
  {"id": "drone_002", "battery": 35, "lat": 35.06, "lon": -120.04}
]

class Job:
    def __init__(self, job_name, drone_id, waypoints):
        self.job_name = job_name
        self.drone_id = drone_id
        self.waypoints = waypoints
        
    def __repr__(self):
        return f"Job(job_name={self.job_name}, drone_id={self.drone_id}, waypoints={self.waypoints})"

def create_job(job_name, drone_id, waypoints):
    return Job(job_name, drone_id, waypoints)

# Optional coverage generation in Python
def generate_lawnmower_waypoints(polygon_coords, spacing_m=50, orientation='north_south'):
    # Stub. Replace with real coverage code or geometry library usage
    return [
        (polygon_coords[0][0], polygon_coords[0][1]),
        (polygon_coords[0][0] + 0.001, polygon_coords[0][1] + 0.001)
    ]

# --- Prepare your user command ---
user_command = "Send a drone to pass the entire area doing sweeps north to south spaced 50m apart"

# --- Build a prompt instructing Ollama to produce JSON ---
# We explicitly request JSON so it's easy to parse. 
# We tell the model: 
#   1) Summarize or interpret the user command
#   2) Decide which drone to use (based on battery)
#   3) Generate some waypoint list 
#   4) Return them as valid JSON
system_prompt = f"""
You are a drone flight planner. 
We have a mission polygon: {mission_polygon}
We have these drones: {drones_status}

The user says: "{user_command}"

1. Choose the best drone based on battery or other factors.
2. Generate a suitable set of waypoints to complete the users request.
3. You should only generate one job at a time.
3. Return ONLY valid JSON in this format:

{{
  "function_name": "create_job",
  "arguments": {{
    "job_name": "string",
    "drone_id": "string",
    "waypoints": [
      [lat, lon],
      [lat, lon]
    ]
  }}
}}

Ensure the JSON is valid. Do not include any extra text or explanations.
"""

# Send the prompt to Ollama
response = ollama.chat(
    model="llama3.2",
    messages=[{
        "role": "user",
        "content": system_prompt
    }]
)

print(response.message.content)

# The response is typically a JSON with a "completion" field containing the text
# if response.status_code == 200:
#     data = response.json()
#     # Depending on Ollama version, data might look like:
#     # {
#     #   "done": true,
#     #   "model": "my-model",
#     #   "completion": "...the actual text from the model..."
#     #   ...
#     # }
#     completion_text = data.get("completion", "")

#     # Try to parse the completion as JSON
#     try:
#         parsed = json.loads(completion_text)
#         # Expecting something like:
#         # {
#         #   "function_name": "create_job",
#         #   "arguments": {
#         #     "job_name": "...",
#         #     "drone_id": "...",
#         #     "waypoints": [...]
#         #   }
#         # }

#         if (
#             parsed.get("function_name") == "create_job" and 
#             "arguments" in parsed
#         ):
#             args = parsed["arguments"]
#             job_name = args["job_name"]
#             drone_id = args["drone_id"]
#             waypoints = args["waypoints"]
            
#             # Optionally, override the LLM's raw waypoints with your own coverage logic:
#             # waypoints = generate_lawnmower_waypoints(mission_polygon, 50, "north_south")

#             # Create the job
#             job = create_job(job_name, drone_id, waypoints)
#             print("Created job:", job)
#         else:
#             print("JSON does not match expected structure:", parsed)
#     except json.JSONDecodeError:
#         print("Could not parse completion as JSON:\n", completion_text)
# else:
#     print("Ollama request failed:", response.text)


def call_llm(prompt, mission_area, drones):
    
    def create_drone_job(job_name: str, drone_id:str, waypoints: list):
        """
        Creates a job with the given parameters

        Args:
        job_name (str): The name of the job
        drone_id (str): The id of the drone
        waypoints (list): A list of waypoints in the form [(lat, lon), (lat, lon)...]

        Returns:
        Job: A Job object
        """
        return Job(job_name, drone_id, waypoints)

    system_prompt = f"""
    You are a drone flight planner. 
    We have a mission polygon: {mission_area}
    We have these drones: {drones}

    The user says: "{prompt}"

    1. Choose the best drone based on battery or other factors.
    2. Generate a suitable set of waypoints to complete the users request. The waypoints should always be within the mission polygon.
    3. You should generate new coordinates for the drone to follow. Dont use the mission polygon coordinates as they define the perimeter of the area to be covered.
    4. You should only generate one job at a time.
    5. The drone_id should be one of the id's of the drones provided
    6. When you create a job, you should always call the function create_drone_job
    7. Waypoints should be a list of coordinates in the form [(lat, lon), (lat, lon)...]
    """


    response = ollama.chat(
        model="llama3.2",
        messages=[{
            "role": "user",
            "content": system_prompt
        }],
        tools=[create_drone_job]
    )

    return response.message

    