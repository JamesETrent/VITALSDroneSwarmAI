import PIL.Image
import PIL.ImageTk
import customtkinter
import tkintermapview
import ollama
import ast
from langChainMain import call_llm
from concurrent.futures import ThreadPoolExecutor


class Drone:
    def __init__(self, map_widget, drone_id, latitude, longitude, battery, icon_path):
        self.map_widget = map_widget
        self.id = drone_id
        self.position = (latitude, longitude)
        self.battery = battery
        self.icon = self._load_icon(icon_path)
        self.marker = self.map_widget.set_marker(
            self.position[0], self.position[1], icon=self.icon, text= drone_id
        )

    def _load_icon(self, path):
        image = PIL.Image.open(path)
        image = image.resize((50, 50))
        return PIL.ImageTk.PhotoImage(image)

    def move(self, lat_offset, lon_offset):
        new_lat = self.position[0] + lat_offset
        new_lon = self.position[1] + lon_offset
        self.position = (new_lat, new_lon)
        self.marker.set_position(new_lat, new_lon)

class Job:
    def __init__(self, start, waypoints, end, path_obj):
        self.start = start
        self.waypoints = waypoints
        self.end = end
        path_obj = path_obj

    
        


class ChatSidebar(customtkinter.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Set a fixed width for the chat sidebar
        self.configure(width=300)

        # Label for the chat sidebar
        chat_label = customtkinter.CTkLabel(self, text="Chat", font=("Arial", 20))
        chat_label.pack(pady=10)

        # Scrollable chat area
        self.chat_area = customtkinter.CTkTextbox(self, wrap="word", state="disabled", height=400)
        self.chat_area.pack(padx=10, pady=(0, 10), fill="both", expand=True)

        # Input frame for user messages
        input_frame = customtkinter.CTkFrame(self)
        input_frame.pack(fill="x", padx=10, pady=10)

        # Input field
        self.input_field = customtkinter.CTkEntry(input_frame, placeholder_text="Type a message...")
        self.input_field.pack(side="left", fill="x", expand=True, padx=(0, 10))

        # Load the send button icon
        send_icon = self._load_icon("./assets/send.png")

        # Send button with an icon
        send_button = customtkinter.CTkButton(
            input_frame, 
            image=send_icon, 
            text="",  # Remove text
            width=20, 
            height=20, 
            command=self.send_message
        )
        send_button.image = send_icon  # Keep a reference to avoid garbage collection
        send_button.pack(side="right")
    executor = ThreadPoolExecutor(max_workers=2)

    
        

    def _load_icon(self, path):
        """Load and resize an icon."""
        image = PIL.Image.open(path)
        image = image.resize((20, 20))  # Resize the icon
        return customtkinter.CTkImage(image)
    


    def send_message(self):
        
        # Get user input
        user_message = self.input_field.get()

        # Clear the input field
        self.input_field.delete(0, "end")

        if user_message.strip():
            # Append the message to the chat area
            self.chat_area.configure(state="normal")  # Enable text widget
            self.chat_area.insert("end", f"You: {user_message}\n")
            self.chat_area.configure(state="disabled")  # Disable text widget to prevent user edits
            self.chat_area.see("end")  # Scroll to the bottom of the chat area
        
        # Call the LLM with the user message
        # get reference to the map page
        polygon_points = self.master.get_polygon_points()
        drones = self.master.get_drones()
        #get polygon points
        
        def on_complete(future):
            response = future.result()
            #print(response)
            self.chat_area.configure(state="normal")
            self.chat_area.insert("end", f"LLM: {response}\n")
            self.chat_area.configure(state="disabled")
            self.chat_area.see("end")
            available_functions = {'create_drone_job': self.master.create_drone_job}
            for tool in response.tool_calls or []:
                function_to_call = available_functions.get(tool.function.name)
                if function_to_call:
                    function_to_call(**tool.function.arguments)
                else:
                    print(f"Function {tool.function_name} not found")
            
        
        future= self.executor.submit(call_llm, user_message, polygon_points, drones )
        future.add_done_callback(on_complete)
        

        # response = call_llm(user_message, polygon_points, [  {"id": "drone_001", "battery": 80, "lat": 28.6036612, "lon": -81.2014693},
        #                                                     {"id": "drone_002", "battery": 35, "lat": 28.6031997, "lon": -81.1986154}])

    
    






class MapPage(customtkinter.CTkFrame):
    def __init__(self, parent, switch_to_home, **kwargs):
        super().__init__(parent, **kwargs)

        self.switch_to_home = switch_to_home
        self.polygons = []
        self.drones = []
        self.polygon_points = []
        self.jobs = []
        self.first_polygon_point = False
        self.editing_polygon = False

        # Left sidebar
        self.sidebar = customtkinter.CTkFrame(self)
        self.sidebar.grid(row=0, column=0, sticky="nsw")
        self.sidebar.grid_columnconfigure(0, weight=1)

        sidebar_title = customtkinter.CTkLabel(
            self.sidebar, text="VITALS", font=("Arial", 20)
        )
        sidebar_title.grid(row=0, column=0, pady=10, padx=20, sticky="w")

        move_drone_test_button = customtkinter.CTkButton(
            self.sidebar, text="Move Drone Test", command=self.move_marker
        )
        move_drone_test_button.grid(row=1, column=0, pady=10, padx=20, sticky="w")

        self.start_polygon_button = customtkinter.CTkButton(
            self.sidebar, text="Start Creating Polygon", command=self.start_creating_polygon
        )
        self.start_polygon_button.grid(row=2, column=0, pady=10, padx=20, sticky="w")

        self.checkbox = customtkinter.CTkCheckBox(self.sidebar, text="Show Mission Area")
        self.checkbox.grid(row=3, column=0, pady=10, padx=20, sticky="w")

        self.create_job_button = customtkinter.CTkButton(
        self.sidebar, text="Create Test Job", command=self.create_test_job
        )
        self.create_job_button.grid(row=4, column=0, pady=10, padx=20, sticky="w")

        for index, drone in enumerate(self.drones):
            drone_label = customtkinter.CTkLabel(self.sidebar, text=f"Drone {drone['id']}")
            drone_label.grid(row=5+index, column=0, pady=10, padx=20, sticky="w")

        # Map frame
        self.map_frame = customtkinter.CTkFrame(self)
        self.map_frame.grid(row=0, column=1, sticky="nsew")

        self.map_widget = tkintermapview.TkinterMapView(
            self.map_frame, width=600, height=400, corner_radius=20
        )
        self.map_widget.pack(fill="both", expand=True, padx=20, pady=20)
        self.map_widget.set_position(28.6026251, -81.1999887)
        self.map_widget.add_left_click_map_command(self.left_click_event)


        # Collapsible right sidebar
        self.collapsible_sidebar = ChatSidebar(self)
        self.collapsible_sidebar.grid(row=0, column=2, sticky="nsew")

        # Back button
        back_button = customtkinter.CTkButton(
            self.sidebar, text="Back to Home", command=self.switch_to_home
        )
        back_button.grid(row=3, column=0, pady=10, padx=20, sticky="w")

        # Grid configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Add drone
        test_drones = [{"id": "drone_001", "battery": 80, "lat": 28.6036612, "lon": -81.2014693}, 
        {"id": "drone_002", "battery": 35, "lat": 28.6031997, "lon": -81.1986154}]
        
        for drone in test_drones:
            self._add_drone(drone["id"], drone["lat"], drone["lon"], drone["battery"], "./assets/camera-drone.png")


    def _add_drone(self, id, lat, lon, battery, icon_path):
        newdrone = Drone(self.map_widget, id,  lat, lon, battery, icon_path)
        self.drones.append(newdrone)

    def left_click_event(self, coordinates_tuple):
        if self.first_polygon_point:
            self.polygon_points.append(coordinates_tuple)
            self.polygon = self.map_widget.set_polygon(self.polygon_points,)
            self.first_polygon_point = False
            
        elif self.editing_polygon:
            #self.polygon_points.append(coordinates_tuple)
            self.polygon.add_position(coordinates_tuple[0], coordinates_tuple[1])
        else:
            pass

    def move_marker(self):
        if self.drones:
            self.drones[0].move(0.0001, 0.0001)
    def create_drone_job(self, job_name, drone_id, waypoints, spacing=0):
        #convert waypoints to list of tuples
        list_of_tuples = [tuple(i) for i in ast.literal_eval(waypoints)]

        # draw path on map
        path_obj = self.map_widget.set_path(position_list = list_of_tuples, width=5, color="red")
        print("Job Created")
        # create job object
        job = Job(job_name, drone_id, list_of_tuples, path_obj)
        self.jobs.append(job)

    
    def start_creating_polygon(self):
        if self.editing_polygon:
            self.editing_polygon = False
            self.start_polygon_button.configure(text="Mission Area Created")
            self.start_polygon_button.configure(state="disabled")
            self.polygon.name = "Mission Area"
            print(self.polygon_points)
        else:
            self.first_polygon_point = True
            self.editing_polygon = True
            # change button text
            self.start_polygon_button.configure(text="Finish Creating Polygon")
    def create_test_job(self):
        job = Job((28.6037837, -81.2018019), [(28.6037837, -81.2018019), (28.6037931, -81.2008148), (28.6037366, -81.1983150)], (28.6037366, -81.1983150))
        print(job.start)
        print(job.waypoints)
        print(job.end)
        self.map_widget.set_path(position_list = job.waypoints, width=5, color="red")
        print("Job Created")
    def get_polygon_points(self):
        return self.polygon_points
    def get_drones(self):
        payload = []
        for drone in self.drones:
            payload.append({"id": drone.id, "battery": drone.battery, "lat": drone.position[0], "lon": drone.position[1]})
        return payload
            
        


class HomePage(customtkinter.CTkFrame):
    def __init__(self, parent, switch_to_map, **kwargs):
        super().__init__(parent, **kwargs)

        self.switch_to_map = switch_to_map

        label = customtkinter.CTkLabel(self, text="Welcome to VITALS!", font=("Arial", 24))
        label.pack(pady=20)

        switch_button = customtkinter.CTkButton(
            self, text="Start Mission", command=self.switch_to_map
        )
        mission_review_button = customtkinter.CTkButton(
            self, text="Mission Review",
        )
        switch_button.pack(pady=10)
        mission_review_button.pack(pady=10)


class VitalsApp:
    def __init__(self):
        self.app = customtkinter.CTk()
        self.app.title("VITALS DESKTOP APP")
        self.app.geometry("1280x720")

        self.container = customtkinter.CTkFrame(self.app)
        self.container.pack(fill="both", expand=True)

        # Create pages
        self.home_page = HomePage(self.container, self.show_map_page)
        self.map_page = MapPage(self.container, self.show_home_page)

        # Show the home page initially
        self.home_page.pack(fill="both", expand=True)

    def show_home_page(self):
        self.map_page.pack_forget()
        self.home_page.pack(fill="both", expand=True)

    def show_map_page(self):
        self.home_page.pack_forget()
        self.map_page.pack(fill="both", expand=True)

    def run(self):
        self.app.mainloop()


if __name__ == "__main__":
    app = VitalsApp()
    app.run()
