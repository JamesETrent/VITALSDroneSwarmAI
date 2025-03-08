import PIL.Image
import PIL.ImageTk
import customtkinter
import tkintermapview
import ollama
import ast
import math
#from langChainMain import call_llm
from concurrent.futures import ThreadPoolExecutor


class Drone:
    
    def __init__(self, map_widget, info_container,job_container, drone_id, system_status):
        self.map_widget = map_widget
        self.info_container = info_container
        self.job_container = job_container
        self.id = drone_id
        self.system_status = system_status
        self.position = None
        self.marker = None
        self.heading_path = None
        self.altitude = None
        self.relative_altitude = None
        self.heading = None
        self.roll = None
        self.pitch = None
        self.yaw = None
        self.active_job = None
        self.job_list = []
        self.active_job_path = None
        self.active_job_start_pos = None
        self.id_of_job_with_path = None
        self.info_widget = DroneInfoBox(info_container, drone_id)
        self.job_info_container = jobInfoContainer(job_container, drone_id)

    
    def setPosition(self, lat, lon, altitude, relative_altitude, heading, vx, vy, vz):
        #convert lat and lon from 7 decimal int to float
        converted_lat = lat / 10000000
        converted_lon = lon / 10000000
        self.position = (converted_lat, converted_lon)
        self.altitude = altitude
        self.relative_altitude = relative_altitude
        converted_heading = heading/1e2
        self.vx = vx
        self.vy = vy
        self.vz = vz
        # set marker on map
        if self.marker is None:
            self.marker = self.map_widget.set_marker(converted_lat, converted_lon, icon_anchor ="center", text=f"Drone {self.id}", icon=self._load_icon("./assets/camera-drone.png"), font = ("Arial", 12, "bold"))
        else:
            self.marker.set_position(converted_lat, converted_lon)
        
        # create heading path on map
        #calculate 10m point based on heading
        heading_rad = math.radians(converted_heading)
        lat_offset = 0.0005 * math.cos(heading_rad)
        lon_offset = 0.0005 * math.sin(heading_rad)
        if self.heading_path is not None:
            self.heading_path.delete()
            self.heading_path = None
        self.heading_path = self.map_widget.set_path(position_list = [(converted_lat, converted_lon), (converted_lat + lat_offset, converted_lon + lon_offset)], width=2, color="red")

        # calculate velocity
        velocity = math.hypot(vx, vy)
        velocity = velocity * 0.01 # convert cm/s to m/s
        # update info widget
        self.info_widget.updatePos(self.position, self.relative_altitude, velocity, converted_heading)
        
    def setTelemetry(self, roll, pitch, yaw):
        self.roll = roll
        self.pitch = pitch
        self.yaw = yaw
    
    def setStatus(self, system_status):
        self.system_status = system_status
        self.info_widget.updateStatus(system_status)

    def _load_icon(self, path):
        image = PIL.Image.open(path)
        image = image.resize((50, 50))
        return PIL.ImageTk.PhotoImage(image)

    def move(self, lat_offset, lon_offset):
        new_lat = self.position[0] + lat_offset
        new_lon = self.position[1] + lon_offset
        self.position = (new_lat, new_lon)
        self.marker.set_position(new_lat, new_lon)
    
    def update_jobs(self, active_job, job_list):
        self.active_job = active_job
        self.job_list = job_list
        print(f"Active Job: {self.active_job}")
        print(f"Job List: {self.job_list}")

        # Step 1: Clear old widgets
        def clear_widgets():
            for widget in self.job_info_container.job_scrollable_frame.winfo_children():
                widget.destroy()
            
            
            # Step 2: Add new jobs only if they exist
            if active_job:
                jobInfoItem(self.job_info_container.job_scrollable_frame, active_job, 0, active=True)
                trimmed_path = []
                # add current position to path
                if self.active_job_start_pos is not None:
                    if self.id_of_job_with_path == active_job.job_id:
                        trimmed_path.append(self.position)
                    else:
                        self.active_job_start_pos = self.position
                        self.id_of_job_with_path = active_job.job_id
                        trimmed_path.append(self.position)
                        self.active_job_path.delete()
                else:
                    self.active_job_start_pos = self.position
                    self.id_of_job_with_path = active_job.job_id
                    trimmed_path.append(self.position)
                print(f"last visited waypoint: {active_job.last_waypoint}")
                for i in range(active_job.last_waypoint, len(active_job.waypoints)):
                    trimmed_path.append((active_job.waypoints[i][0], active_job.waypoints[i][1]))
                if self.active_job_path is not None:
                    self.active_job_path.delete()
                if len(trimmed_path) > 1:
                    self.active_job_path = self.map_widget.set_path(position_list = trimmed_path, width=5, color="green")
            else:
                self.active_job_path.delete()
                self.active_job_path = None
                self.active_job_start_pos = None
                self.id_of_job_with_path = None

            
            for i, job in enumerate(job_list):
                jobInfoItem(self.job_info_container.job_scrollable_frame, job, i + 1)

        # Use `after` to avoid accessing destroyed widgets immediately
        self.map_widget.after(100, clear_widgets)



class Job:
    def __init__(self, start, waypoints, end, path_obj):
        self.start = start
        self.waypoints = waypoints
        self.end = end
        path_obj = path_obj

class POI:
    def __init__(self, lat, lon, name, map_widget, info_container, poi_count):
        self.map_widget = map_widget
        self.info_container = info_container
        self.id = poi_count
        self.lat = lat
        self.lon = lon
        self.name = name
        self.marker = map_widget.set_marker(lat, lon, text=name, command=self.open_popup)
        self.info_widget = POIInfoBox(info_container, name, lat, lon, poi_count, popup_func=self.open_popup)
        
    
    def open_popup(self, event):
        # Create a new window
        self.popup = customtkinter.CTkToplevel(self.info_container)
        self.popup.title(self.name)
        self.popup.geometry("300x200")

        #push the popup to the front
        self.popup.lift()
        self.popup.focus_force()
        self.popup.grab_set()
        self.popup.protocol("WM_DELETE_WINDOW", self.popup.destroy)

        # Add content to the popup
        name_label = customtkinter.CTkLabel(self.popup, text=f"Name: {self.name}", font=("Arial", 12))
        name_label.pack(pady=10)
        coordinates_label = customtkinter.CTkLabel(self.popup, text=f"Coordinates: ({self.lat:.4f}, {self.lon:.4f})", font=("Arial", 12))
        coordinates_label.pack(pady=10)
        description_label = customtkinter.CTkLabel(self.popup, text="Description: This is a POI.", font=("Arial", 12))
        description_label.pack(pady=10)
        

        # Add a close button
        close_button = customtkinter.CTkButton(self.popup, text="Close", command=self.popup.destroy)
        close_button.pack(pady=10)

class POIInfoBox(customtkinter.CTkFrame):
    def __init__(self, parent, name, lat, lon, poi_count, popup_func):
        # Create the POI info frame
        self.poi_info =customtkinter.CTkFrame(parent, fg_color="#337ab7")  # Blue background
        self.poi_info.grid(row=poi_count, column=0, padx=10, pady=10, sticky="ew")
        self.poi_info.bind("<Button-1>", popup_func)
        

        # Add the POI name
        self.name_label = customtkinter.CTkLabel(self.poi_info, text=f"Name: {name}", font=("Arial", 12, "bold"), fg_color="#337ab7")
        self.name_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # Add the coordinates label
        self.coordinates_label = customtkinter.CTkLabel(self.poi_info, text=f"Coordinates: ({lat:.4f}, {lon:.4f})", font=("Arial", 10), fg_color="#337ab7")
        self.coordinates_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=5)
    
    


class ChatSidebar(customtkinter.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)

        # Set a fixed width for the chat sidebar
        self.configure(width=300)

        # Grid Configuration (Ensures Resizing Behavior)
        self.grid_columnconfigure(0, weight=1)  # Allows horizontal expansion
        self.grid_rowconfigure(1, weight=1)  # Chat area expands
        self.grid_rowconfigure(2, weight=0)  # Input area stays fixed

        # Label for the chat sidebar
        chat_label = customtkinter.CTkLabel(self, text="Chat", font=("Arial", 20))
        chat_label.grid(row=0, column=0, pady=10, padx=10, sticky="n")

        # Scrollable chat area (Expands with resizing)
        self.chat_area = customtkinter.CTkTextbox(self, wrap="word", state="disabled", height=400)
        self.chat_area.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

        # Input frame (Ensures input field stays visible)
        input_frame = customtkinter.CTkFrame(self)
        input_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")  # Forces it to be visible

        # Ensure input field expands horizontally
        input_frame.grid_columnconfigure(0, weight=1)

        # Input field
        self.input_field = customtkinter.CTkEntry(input_frame, placeholder_text="Type a message...")
        self.input_field.grid(row=0, column=0, sticky="ew", padx=(0, 10))  # Expands with resizing

        # Load the send button icon
        send_icon = self._load_icon("./assets/send.png")

        # Send button with an icon
        send_button = customtkinter.CTkButton(
            input_frame, 
            image=send_icon, 
            text="",  # Remove text
            width=20, 
            height=20, 
            command=None  # self.send_message
        )
        send_button.image = send_icon  # Keep a reference to avoid garbage collection
        send_button.grid(row=0, column=1)  # Place it on the right

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
            
        
        #future= self.executor.submit(call_llm, user_message, polygon_points, drones )
        #future.add_done_callback(on_complete)

class jobInfoContainer(customtkinter.CTkFrame):
    def __init__(self, parent, drone_id):
        # Create the drone info frame
        self.job_frame = customtkinter.CTkFrame(parent)
        self.job_frame.grid(row=0, column=drone_id-1, sticky="nsew", padx=10, pady=10)

        self.job_label = customtkinter.CTkLabel(
            self.job_frame, text=f"Drone {drone_id} Jobs", font=("Arial", 16, "bold")
        )
        self.job_label.pack(pady=5)

        self.job_scrollable_frame = customtkinter.CTkScrollableFrame(self.job_frame, width=200, height=200)
        self.job_scrollable_frame.pack(fill="both", expand=True)

class jobInfoItem(customtkinter.CTkFrame):
    def __init__(self, parent, job, row, active=False):
        # Create the job info frame
        if active:
            self.job_info = customtkinter.CTkFrame(parent, fg_color="#337ab7")
        else:
            self.job_info = customtkinter.CTkFrame(parent, fg_color="#5C5C5C")
        self.job_info.grid(row=row, column=0, padx=10, pady=10, sticky="ew")

        self.job_type_label = customtkinter.CTkLabel(self.job_info, text=job.job_type, font=("Arial", 12, "bold"))
        self.job_type_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        self.job_status_label = customtkinter.CTkLabel(self.job_info, text=job.job_status, font=("Arial", 10, "bold"))
        self.job_status_label.grid(row=1, column=1, sticky="e", padx=5, pady=5)

        self.num_waypoints_label = customtkinter.CTkLabel(self.job_info, text=f"Waypoints: {len(job.waypoints)}", font=("Arial", 10))
        self.num_waypoints_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5)

        self.last_waypoint_label = customtkinter.CTkLabel(self.job_info, text=f"Last Visited Waypoint: {job.last_waypoint}", font=("Arial", 10))
        self.last_waypoint_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=5)

        self.job_priority_label = customtkinter.CTkLabel(self.job_info, text=f"Priority: {job.job_priority}", font=("Arial", 10))
        self.job_priority_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=5)


        
        
class DroneInfoBox(customtkinter.CTkFrame):
    def __init__(self, parent, id, row=1):
        # Create the drone info frame
        self.drone_info =customtkinter.CTkFrame(parent, fg_color="#337ab7")  # Blue background
        self.drone_info.grid(row=id, column=0, padx=10, pady=10, sticky="ew")

        # Add the drone ID
        self.id_label = customtkinter.CTkLabel(self.drone_info, text=f"ID: {id}", font=("Arial", 12, "bold"), fg_color="#337ab7")
        self.id_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

        # Add the status label
        self.status_label = customtkinter.CTkLabel(self.drone_info, text="Active", font=("Arial", 10, "bold"), fg_color="green", padx=5, pady=2)
        self.status_label.grid(row=0, column=1, sticky="e", padx=5, pady=5)

        # Add the drone details
        self.position_label = customtkinter.CTkLabel(self.drone_info, text="Position: Unknown", font=("Arial", 10), fg_color="#337ab7")
        self.position_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=5)

        self.altitude_label = customtkinter.CTkLabel(self.drone_info, text="Altitude: Unknown", font=("Arial", 10), fg_color="#337ab7")
        self.altitude_label.grid(row=2, column=0, columnspan=2, sticky="w", padx=5)

        self.velocity_label = customtkinter.CTkLabel(self.drone_info, text="Velocity: Unknown", font=("Arial", 10), fg_color="#337ab7",)
        self.velocity_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=5)

        self.heading_label = customtkinter.CTkLabel(self.drone_info, text="Heading: Unknown", font=("Arial", 10), fg_color="#337ab7",)
        self.heading_label.grid(row=4, column=0, columnspan=2, sticky="w", padx=5)
    
    def updatePos(self, position, altitude, velocity, heading):
        self.position_label.configure(text=f"Position: {position}")
        self.altitude_label.configure(text=f"Altitude: {altitude / 1000} m")
        self.velocity_label.configure(text=f"Velocity: {velocity}")
        self.heading_label.configure(text=f"Heading: {heading}")
    
    def updateStatus(self, status):
        
        if status == 0:
            self.status_label.configure(text="UnInit", fg_color="gray")
        elif status == 1:
            self.status_label.configure(text="Boot", fg_color="gray")
        elif status == 2:
            self.status_label.configure(text="Calibrating", fg_color="yellow")
        elif status == 3:
            self.status_label.configure(text="Standby", fg_color="orange")
        elif status == 4:
            self.status_label.configure(text="Active", fg_color="green")
        elif status == 5:
            self.status_label.configure(text="Critical", fg_color="red")
        elif status == 6:
            self.status_label.configure(text="Emergency", fg_color="red")
        else:
            self.status_label.configure(text="Unknown", fg_color="gray")


class MapPage(customtkinter.CTkFrame):
    def __init__(self, parent, switch_to_home, gui_ref, **kwargs):
        super().__init__(parent, **kwargs)
        self.gui_ref = gui_ref
        self.switch_to_home = switch_to_home
        self.polygons = []
        self.drones = []
        self.polygon_points = []
        self.jobs = []
        self.pois = []
        self.first_polygon_point = False
        self.editing_polygon = False
        self.debug_window = None
        
        # Left sidebar
        self.sidebar = customtkinter.CTkFrame(self)
        self.sidebar.grid(row=0, column=0, sticky="nsw", rowspan=2)
        self.sidebar.grid_columnconfigure(0, weight=1)

        sidebar_title = customtkinter.CTkLabel(
            self.sidebar, text="VITALS", font=("Arial", 20)
        )
        sidebar_title.grid(row=0, column=0, pady=10, padx=20, sticky="w")

        # move_drone_test_button = customtkinter.CTkButton(
        #     self.sidebar, text="Move Drone Test", command=self.move_marker
        # )
        # move_drone_test_button.grid(row=1, column=0, pady=10, padx=20, sticky="w")

        self.start_polygon_button = customtkinter.CTkButton(
            self.sidebar, text="Start Creating Polygon", command=self.start_creating_polygon
        )
        self.start_polygon_button.grid(row=1, column=0, pady=10, padx=20, sticky="w")

        self.connect_button = customtkinter.CTkButton(
        self.sidebar, text="Connect to Mavlink", command=self.gui_ref.call_mavlink_connection
        )
        self.connect_button.grid(row=2, column=0, pady=10, padx=20, sticky="w")

        self.debug_button = customtkinter.CTkButton(
            self.sidebar, text="Debug Menu", command=self.open_debug_popup
        )
        self.debug_button.grid(row=3, column=0, pady=10, padx=20, sticky="w")

        # Back button
        back_button = customtkinter.CTkButton(
            self.sidebar, text="Back to Home", command=self.switch_to_home
        )
        back_button.grid(row=4, column=0, pady=10, padx=20, sticky="w")

        # drone info container
        self.drone_info_container = customtkinter.CTkFrame(self.sidebar)
        self.drone_info_container.grid(row=4, column=0, pady=10, padx=20, rowspan=8, sticky="nsew")
        self.drone_info_Label = customtkinter.CTkLabel(self.drone_info_container, text="Drones", font=("Arial", 20))
        self.drone_info_Label.grid(row=0, column=0, pady=10, padx=20, sticky="nsew")

        # Map frame
        self.map_frame = customtkinter.CTkFrame(self)
        self.map_frame.grid(row=0, column=1, sticky="nsew", rowspan=2)

        self.map_widget = tkintermapview.TkinterMapView(
            self.map_frame, width=600, height=600, corner_radius=20
        )
        self.map_widget.pack(fill="both", expand=False, padx=20, pady=20)
        self.map_widget.set_position(28.6026251, -81.1999887)
        self.map_widget.add_left_click_map_command(self.left_click_event)

        #bottom frame
        self.bottom_frame = customtkinter.CTkFrame(self)
        self.bottom_frame.grid(row=1, column=1, sticky="nsew")

        # Grid configuration for job lists
        self.bottom_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        # Grid configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=2)  # 2/3 height for map
        self.grid_rowconfigure(1, weight=1)  # 1/3 height for bottom frame

        #RightClick Menu
        self.map_widget.add_right_click_menu_command(label="Add Job Waypoint", command=self.gui_ref.add_job_waypoint, pass_coords=True)
        self.map_widget.add_right_click_menu_command(label="Create POI", command=self.create_test_poi, pass_coords=True)

        # Collapsible right sidebar
        self.collapsible_sidebar = ChatSidebar(self)
        self.collapsible_sidebar.grid(row=0, column=2, sticky="nsew")

        #POI Info Frame
        self.poi_info_container = customtkinter.CTkScrollableFrame(self, width=200, height=200)
        self.poi_info_container.grid(row=1, column=2, pady=10, padx=20, sticky="nsew")
        self.poi_info_Label = customtkinter.CTkLabel(self.poi_info_container, text="POIs", font=("Arial", 20))
        self.poi_info_Label.grid(row=0, column=0, pady=10, padx=20, sticky="nsew")

        # Grid configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

    def open_debug_popup(self):
        if self.debug_window is not None and self.debug_window.winfo_exists():
            self.debug_window.lift()  # Bring to front if already open
            return


        self.debug_window = customtkinter.CTkToplevel(self)
        self.debug_window.title("Debugging Menu")
        self.debug_window.geometry("300x600")
        self.debug_window.resizable(False, False)

        # Ensure the window does not close instantly
        self.debug_window.after(100, lambda: self.debug_window.focus_force())

        # Prevent accidental closure
        self.debug_window.protocol("WM_DELETE_WINDOW", self.close_debug_popup)
        #target drone input
        target_drone_label = customtkinter.CTkLabel(self.debug_window, text="Target Drone ID (1-4):")
        target_drone_label.pack(pady=10)

        self.target_drone_entry = customtkinter.CTkEntry(self.debug_window)
        self.target_drone_entry.pack(pady=10)

        #use waypoints input
        use_waypoints_label = customtkinter.CTkLabel(self.debug_window, text="Use Waypoints (1-4):")
        use_waypoints_label.pack(pady=10)
        self.use_waypoints_entry = customtkinter.CTkEntry(self.debug_window)
        self.use_waypoints_entry.pack(pady=10)
        #debugging tools

        debug_label = customtkinter.CTkLabel(self.debug_window, text="Debugging Tools", font=("Arial", 16, "bold"))
        debug_label.pack(pady=10)

        btn_test_move = customtkinter.CTkButton(self.debug_window, text="Test Move Drone", command=self.move_marker)
        btn_test_move.pack(pady=5)

        btn_test_arm = customtkinter.CTkButton(self.debug_window, text="Test Arm Drone", command=self.gui_ref.call_arm_mission)
        btn_test_arm.pack(pady=5)

        btn_test_takeoff = customtkinter.CTkButton(self.debug_window, text="Test Takeoff", command=self.gui_ref.call_takeoff_mission)
        btn_test_takeoff.pack(pady=5)

        btn_send_waypoints = customtkinter.CTkButton(self.debug_window, text="Send Waypoints", command=self.gui_ref.call_send_waypoints)
        btn_send_waypoints.pack(pady=5)

        btn_return_home = customtkinter.CTkButton(self.debug_window, text="Return to Launch", command=self.gui_ref.call_return_to_launch)
        btn_return_home.pack(pady=5)

        btn_request_mission_list = customtkinter.CTkButton(self.debug_window, text="Request Mission List", command=self.gui_ref.call_request_mission_list)
        btn_request_mission_list.pack(pady=5)

        btn_add_test_job = customtkinter.CTkButton(self.debug_window, text="Add Test Job", command=self.gui_ref.call_create_test_job)
        btn_add_test_job.pack(pady=5)

        btn_close = customtkinter.CTkButton(self.debug_window, text="Close", command=self.close_debug_popup)
        btn_close.pack(pady=10)
    
    def get_target_debug_drone(self):
        try:
            return int(self.target_drone_entry.get())
        except ValueError:
            return None
    def get_debug_waypoints(self):
        try:
            return int(self.use_waypoints_entry.get())
        except ValueError:
            return None


    def close_debug_popup(self):
        """Closes the debug popup properly"""
        if self.debug_window is not None:
            self.debug_window.destroy()
            self.debug_window = None



    def add_job(self, drone_id, job_text, inprogress=False):
        """
        Adds a new job to the scrollable frame for the given drone_id (1-4).
        """
        if inprogress:
            color = "#1F6AA5"
        else:
            color = "#5C5C5C"
        if 1 <= drone_id <= 4:
            job_frame = customtkinter.CTkFrame(self.job_lists[drone_id - 1], )
            job_frame.pack(fill="x", padx=5, pady=5)

            job_label = customtkinter.CTkLabel(job_frame, text=job_text, font=("Arial", 14), fg_color= color, text_color="white", corner_radius=4)
            job_label.pack(fill="both", expand=True, padx=5, pady=5)


    def _add_drone(self, drone_id, system_status):
        newdrone = Drone(self.map_widget, self.drone_info_container, self.bottom_frame, drone_id, system_status)
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
            self.gui_ref.sendMissionPolygon(self.polygon_points)
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
    
    def add_poi(self, lat, lon, name):
        poi_count = len(self.pois) + 1
        poi = POI(lat, lon, name, self.map_widget, self.poi_info_container, poi_count)
        self.pois.append(poi)
    
    def create_test_poi(self, coords):
        poi_count = len(self.pois) + 1
        self.add_poi(coords[0], coords[1], f"POI {poi_count}")
    

class HomePage(customtkinter.CTkFrame):
    def __init__(self, parent, switch_to_map, gui_ref, **kwargs):
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

class JobWaypoint:
    def __init__(self, lat, lon, waypointNum, map_widget):
        self.lat = lat
        self.lon = lon
        self.marker = map_widget.set_marker(lat, lon, text=waypointNum)


class GUI:
    def __init__(self):
        #self.missionState = missionState
        self.app = customtkinter.CTk()
        self.app.title("VITALS DESKTOP APP")
        self.app.geometry("1280x720")

        self.container = customtkinter.CTkFrame(self.app)
        self.container.pack(fill="both", expand=True)

        self.currentJobWaypoints = []
        self.currentJobPath = None

        # Create pages
        self.home_page = HomePage(self.container, self.show_map_page, self)
        self.map_page = MapPage(self.container, self.show_home_page, self)

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

    def link_mission_state(self, missionState):
        self.missionState = missionState

    def call_mavlink_connection(self):
        self.missionState.connect_to_mavlink()
    
    def get_polygon_points(self):
        return self.map_page.get_polygon_points()
    
    def sendMissionPolygon(self, polygon_points):
        self.missionState.addMissionPolygon(polygon_points)

    
    def updateDronePosition(self, drone_id, lat, lon, altitude, relative_altitude, heading, vx, vy, vz):
        drone = next((drone for drone in self.map_page.drones if drone.id == drone_id), None)
        if drone is not None:
            drone.setPosition(lat, lon, altitude, relative_altitude, heading, vx, vy, vz)

    def updateDroneTelemetry(self, drone_id, roll, pitch, yaw):
        drone = next((drone for drone in self.map_page.drones if drone.id == drone_id), None)
        if drone is not None:
            drone.setTelemetry(roll, pitch, yaw)

    def addDrone(self, drone_id, system_status):
        self.map_page._add_drone(drone_id, system_status)

    def updateDroneStatus(self, drone_id, system_status):
        drone = next((drone for drone in self.map_page.drones if drone.id == drone_id), None)
        if drone is not None:
            drone.setStatus(system_status)
    
    def updateJobs(self, drone_id, active_job, job_list):
        drone = next((drone for drone in self.map_page.drones if drone.id == drone_id), None)
        if drone is not None:
            drone.update_jobs(active_job, job_list)
    
    


    #Debugging Functions
    def call_takeoff_mission(self):
        target_drone = self.map_page.get_target_debug_drone()
        self.missionState.takeoff_mission(target_drone)
    
    def call_arm_mission(self):
        target_drone = self.map_page.get_target_debug_drone()
        self.missionState.arm_mission(target_drone)
    
    def call_send_waypoints(self):
        target_drone = self.map_page.get_target_debug_drone()
        debug_waypoints = self.map_page.get_debug_waypoints()
        self.missionState.send_waypoints(target_drone, debug_waypoints)
    
    def call_return_to_launch(self):
        target_drone = self.map_page.get_target_debug_drone()
        self.missionState.return_to_launch(target_drone)
    
    def call_request_mission_list(self):
        target_drone = self.map_page.get_target_debug_drone()
        self.missionState.send_mission_list_request(target_drone)
    
    def call_create_test_job(self):
        target_drone = self.map_page.get_target_debug_drone()
        debug_waypoints = self.map_page.get_debug_waypoints()
        self.missionState.test_add_job(target_drone, debug_waypoints)
    
    def add_job_waypoint(self, coords):
        if len(self.currentJobWaypoints) == 0:
            self.map_page.map_widget.add_right_click_menu_command(label="Finish Job", command=self.finish_creating_job)
        waypointNum = len(self.currentJobWaypoints) + 1
        waypoint = JobWaypoint(coords[0], coords[1], waypointNum, self.map_page.map_widget)
        self.currentJobWaypoints.append(waypoint)
        if len(self.currentJobWaypoints) >= 2:
            self.map_page.map_widget.delete_all_path()
            positions = []
            for waypoint in self.currentJobWaypoints:
                positions.append((waypoint.lat, waypoint.lon))
            path = self.map_page.map_widget.set_path(position_list = positions, width=5, color="red")

    def finish_creating_job(self):
        pass
    
    

    


if __name__ == "__main__":
    app = GUI()
    app.run()
