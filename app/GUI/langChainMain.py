import requests
import json
import ollama



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

    