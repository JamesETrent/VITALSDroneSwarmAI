import requests
import json
import ollama



def call_llm(prompt, mission_area, drones, pois):
    
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

    def create_poi_investigate_job(poi_id, drone_id, priority = 5):
        """
        Calls the drone to investigate a point of interest
        Args:
        poi_id (int): The id of the point of interest
        drone_id (str): The id of the drone
        priority (int): The priority of the job(can be 5,6,7, 5 is default)

        Returns:
        Job: A Job object
        """
        return Job(f"Investigate POI {poi_id}", drone_id, [(poi_id.lat, poi_id.lon)], priority)

    def call_return_to_launch(drone_id):
        """
        Calls the drone to return to launch
        Args:
        drone_id (str): The id of the drone

        Returns:
        Job: A Job object
        """
        return Job(f"Return to Launch", drone_id, [(0, 0)])
    system_prompt = f"""
    You are a drone flight planner. 
    We have a mission polygon: {mission_area}
    We have these drones: {drones}
    We have these points of interest: {pois}

    The user says: "{prompt}"

    You will use the available tools to coplete the task.
    if you dont have the tool to complete the task, you will say "I dont have the tool to complete this task"
    You absolutely must respond with a short message to the user telling them what you did.
    
    """


    response = ollama.chat(
        model="llama3.2",
        messages=[{
            "role": "user",
            "content": system_prompt
        }],
        tools=[create_poi_investigate_job, call_return_to_launch]
    )
    return response.message

    