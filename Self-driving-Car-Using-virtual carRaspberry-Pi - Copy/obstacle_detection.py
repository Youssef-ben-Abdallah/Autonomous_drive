"""
Obstacle Detection Module
Detects obstacles and traffic lights using YOLOv8
"""

import cv2
from ultralytics import YOLO
import time
import numpy as np
from datetime import datetime
import os
from utils.logger import get_logger

logger = get_logger(__name__)

# Load YOLOv8 pre-trained model with error handling
model = None
try:
    model_path = "yolov8n.pt"
    if not os.path.exists(model_path):
        logger.warning(f"Model file not found: {model_path}")
        logger.info("Attempting to download YOLOv8 model...")
    model = YOLO(model_path)
    logger.info("✅ YOLOv8 model loaded successfully")
except Exception as e:
    logger.error(f"❌ Failed to load YOLOv8 model: {e}", exc_info=True)
    logger.error("Please ensure ultralytics is installed: pip install ultralytics")
    model = None


# Motor simulation functions with speed control
def stop():
    logger.info("[MOTORS] 🛑 STOPPING - Speed: 0 km/h")
    log_action("STOP", 0)


def forward(speed=30):
    logger.info(f"[MOTORS] 🚗 MOVING FORWARD - Speed: {speed} km/h")
    log_action("FORWARD", speed)


def left(speed=20):
    logger.info(f"[MOTORS] ↪️ TURNING LEFT - Speed: {speed} km/h")
    log_action("LEFT", speed)


def right(speed=20):
    logger.info(f"[MOTORS] ↩️ TURNING RIGHT - Speed: {speed} km/h")
    log_action("RIGHT", speed)


def slow_down(speed=10):
    logger.info(f"[MOTORS] 🐢 SLOWING DOWN - Speed: {speed} km/h")
    log_action("SLOW DOWN", speed)


# Action logging
def log_action(action: str, speed: int) -> None:
    """
    Log vehicle action to file.

    Args:
        action (str): Action name
        speed (int): Speed in km/h
    """
    try:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        with open("car_actions.log", "a") as f:
            f.write(f"{timestamp} - {action} at {speed} km/h\n")
    except Exception as e:
        logger.error(f"Failed to log action: {e}", exc_info=True)


# Enhanced traffic light detection using YOLO
class TrafficLightDetector:
    def __init__(self):
        self.traffic_light_class_id = 9  # YOLO class ID for traffic light
        self.last_detection_time = 0
        self.current_light_state = "UNKNOWN"

    def detect_traffic_lights(self, frame, results):
        """Detect traffic lights only when traffic light objects are present"""
        traffic_lights = []

        for r in results.boxes:
            cls_id = int(r.cls[0])
            if cls_id == self.traffic_light_class_id:
                x1, y1, x2, y2 = map(int, r.xyxy[0])
                conf = float(r.conf[0])

                # Only consider high-confidence detections
                if conf > 0.5:
                    traffic_light_roi = frame[y1:y2, x1:x2]
                    light_color = self.analyze_traffic_light_color(traffic_light_roi)

                    traffic_lights.append({
                        'bbox': (x1, y1, x2, y2),
                        'color': light_color,
                        'confidence': conf
                    })

        return traffic_lights

    def analyze_traffic_light_color(self, traffic_light_roi):
        """Analyze the color of the traffic light within its bounding box"""
        if traffic_light_roi.size == 0:
            return "UNKNOWN"

        hsv = cv2.cvtColor(traffic_light_roi, cv2.COLOR_BGR2HSV)

        # Color ranges for traffic lights
        red_ranges = [((0, 150, 100), (10, 255, 255)), ((170, 150, 100), (180, 255, 255))]
        yellow_range = ((20, 150, 150), (30, 255, 255))
        green_range = ((45, 100, 100), (85, 255, 255))

        # Count pixels for each color
        red_pixels = 0
        for lower, upper in red_ranges:
            mask = cv2.inRange(hsv, lower, upper)
            red_pixels += cv2.countNonZero(mask)

        mask_yellow = cv2.inRange(hsv, yellow_range[0], yellow_range[1])
        yellow_pixels = cv2.countNonZero(mask_yellow)

        mask_green = cv2.inRange(hsv, green_range[0], green_range[1])
        green_pixels = cv2.countNonZero(mask_green)

        # Determine dominant color
        min_pixels = 20  # Minimum pixels to consider
        if red_pixels > min_pixels and red_pixels > yellow_pixels and red_pixels > green_pixels:
            return "RED"
        elif yellow_pixels > min_pixels and yellow_pixels > green_pixels:
            return "YELLOW"
        elif green_pixels > min_pixels:
            return "GREEN"
        else:
            return "UNKNOWN"


# PROPER Distance estimation class
class DistanceEstimator:
    def __init__(self, known_widths=None):
        # Realistic known widths in meters for common objects
        self.known_widths = known_widths or {
            'person': 0.5,
            'bicycle': 0.75,
            'car': 1.8,
            'motorcycle': 0.8,
            'bus': 2.5,
            'truck': 2.5,
            'traffic light': 0.3,
            'stop sign': 0.6,
            'cat': 0.3,
            'dog': 0.4,
            'bird': 0.2
        }
        # Focal length calibration (you may need to adjust this)
        self.focal_length = 1000  # This works better for webcams

    def calculate_distance(self, object_width_pixels, object_type="car"):
        """Calculate distance using the triangle similarity method"""
        if object_width_pixels <= 0:
            return float('inf')

        known_width = self.known_widths.get(object_type, 1.5)  # default 1.5m

        # Triangle similarity: distance = (known_width * focal_length) / perceived_width
        distance = (known_width * self.focal_length) / object_width_pixels

        # Add some realistic constraints
        if distance > 50:  # Max reasonable distance for webcam
            distance = float('inf')

        return round(distance, 1)


# PROPER Speed estimation class
class SpeedEstimator:
    def __init__(self):
        self.previous_positions = {}
        self.previous_time = time.time()
        self.vehicle_speed = 0  # km/h
        self.speed_history = []
        self.frame_count = 0

    def estimate_object_speed(self, current_objects, frame_width, frame_height):
        """Estimate speed of detected objects using proper tracking"""
        current_time = time.time()
        time_elapsed = current_time - self.previous_time
        object_speeds = {}

        if time_elapsed < 0.1:  # Wait for reasonable time difference
            return object_speeds

        for obj_id, obj_info in current_objects.items():
            current_center_x = obj_info['center_x']
            current_center_y = obj_info['center_y']
            obj_label = obj_info['label']

            if obj_id in self.previous_positions:
                prev_info = self.previous_positions[obj_id]
                prev_center_x = prev_info['center_x']
                prev_center_y = prev_info['center_y']

                # Calculate pixel movement (Euclidean distance)
                pixel_distance = np.sqrt(
                    (current_center_x - prev_center_x) ** 2 +
                    (current_center_y - prev_center_y) ** 2
                )

                # Convert pixels to meters (approximate calibration)
                # Assuming typical webcam: 60° FOV at 2m distance ≈ 2.3m width
                meters_per_pixel = 2.3 / frame_width
                meters_distance = pixel_distance * meters_per_pixel

                # Calculate speed in m/s, then convert to km/h
                speed_mps = meters_distance / time_elapsed
                speed_kmh = speed_mps * 3.6

                # Filter out noise (only consider meaningful movements)
                if speed_kmh > 1.0 and speed_kmh < 100:  # Reasonable speed range
                    object_speeds[obj_id] = round(speed_kmh, 1)

            # Update position for next frame
            self.previous_positions[obj_id] = {
                'center_x': current_center_x,
                'center_y': current_center_y,
                'label': obj_label
            }

        self.previous_time = current_time
        return object_speeds

    def update_vehicle_speed(self, action, previous_action):
        """Update vehicle speed based on current action with realistic physics"""
        # Realistic acceleration/deceleration
        acceleration_rate = 5  # km/h per decision cycle
        deceleration_rate = 10  # km/h per decision cycle

        if action == "STOP":
            self.vehicle_speed = max(0, self.vehicle_speed - deceleration_rate)
        elif action == "SLOW DOWN":
            self.vehicle_speed = max(0, self.vehicle_speed - deceleration_rate * 0.7)
        elif action == "FORWARD":
            if previous_action == "FORWARD":
                # Gradual acceleration
                self.vehicle_speed = min(60, self.vehicle_speed + acceleration_rate)
            else:
                self.vehicle_speed = 30  # Start at reasonable speed
        elif action in ["LEFT", "RIGHT"]:
            self.vehicle_speed = min(30, self.vehicle_speed)  # Slow down for turns

        self.speed_history.append(self.vehicle_speed)
        # Keep only last 10 readings
        if len(self.speed_history) > 10:
            self.speed_history.pop(0)

        return self.vehicle_speed


# Environment detection class
class EnvironmentDetector:
    def __init__(self):
        self.current_conditions = {
            'time_of_day': 'DAY',
            'weather': 'CLEAR',
            'brightness': 0.5
        }

    def detect_environment(self, frame):
        """Detect time of day and weather conditions"""
        # Convert to grayscale for brightness analysis
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Calculate average brightness
        brightness = np.mean(gray) / 255.0
        self.current_conditions['brightness'] = brightness

        # Determine time of day based on brightness
        if brightness < 0.3:
            self.current_conditions['time_of_day'] = 'NIGHT'
        elif brightness < 0.5:
            self.current_conditions['time_of_day'] = 'DUSK/DAWN'
        else:
            self.current_conditions['time_of_day'] = 'DAY'

        # Simple weather detection based on color variance and contrast
        color_variance = np.var(frame) / (255 ** 2)

        if color_variance < 0.05:
            self.current_conditions['weather'] = 'FOGGY'
        elif brightness > 0.8:
            self.current_conditions['weather'] = 'SUNNY'
        elif brightness < 0.4:
            self.current_conditions['weather'] = 'OVERCAST'
        else:
            self.current_conditions['weather'] = 'CLEAR'

        return self.current_conditions


# Enhanced car controller
class CarController:
    def __init__(self):
        self.traffic_light_state = "UNKNOWN"
        self.last_action = "STOP"
        self.current_speed = 0
        self.environment_conditions = {}

    def update_environment(self, conditions):
        """Update environment conditions and adjust behavior"""
        self.environment_conditions = conditions

    def adjust_speed_for_conditions(self, base_speed):
        """Adjust speed based on environmental conditions"""
        speed_multiplier = 1.0

        # Adjust for time of day
        if self.environment_conditions.get('time_of_day') == 'NIGHT':
            speed_multiplier *= 0.7  # Slow down at night
        elif self.environment_conditions.get('time_of_day') == 'DUSK/DAWN':
            speed_multiplier *= 0.8

        # Adjust for weather
        weather = self.environment_conditions.get('weather', 'CLEAR')
        if weather == 'FOGGY':
            speed_multiplier *= 0.5
        elif weather == 'OVERCAST':
            speed_multiplier *= 0.9
        elif weather == 'SUNNY':
            speed_multiplier *= 1.0

        return int(base_speed * speed_multiplier)

    def decide_action(self, traffic_lights, closest_object_distance, closest_object_type, object_speeds):
        """Make driving decisions considering all factors"""

        # Reset traffic light state if no traffic lights detected
        if not traffic_lights:
            self.traffic_light_state = "UNKNOWN"
        else:
            # Use the most confident traffic light detection
            main_light = max(traffic_lights, key=lambda x: x['confidence'])
            self.traffic_light_state = main_light['color']

        # PRIORITY 1: TRAFFIC LIGHTS (only when detected)
        if self.traffic_light_state == "RED":
            base_speed = 0
            action = "STOP"
            reason = "Red traffic light detected 🚦"

        elif self.traffic_light_state == "YELLOW":
            if self.last_action == "FORWARD" and closest_object_distance > 5.0:
                base_speed = 20
                action = "SLOW DOWN"
                reason = "Yellow light - Proceeding with caution 🚦"
            else:
                base_speed = 0
                action = "STOP"
                reason = "Yellow light - Preparing to stop 🚦"

        elif self.traffic_light_state == "GREEN":
            if closest_object_distance > 8.0:
                base_speed = 40
                action = "FORWARD"
                reason = "Green light - Clear path ahead 🚦"
            elif closest_object_distance > 4.0:
                base_speed = 25
                action = "SLOW DOWN"
                reason = "Green light - Obstacle ahead 🚦"
            else:
                base_speed = 0
                action = "STOP"
                reason = "Green light - Obstacle too close 🚦"

        # PRIORITY 2: OBSTACLE AVOIDANCE (when no traffic light detected)
        elif closest_object_distance <= 2.0:
            base_speed = 0
            action = "STOP"
            reason = f"Emergency stop! Too close to {closest_object_type}"

        elif closest_object_distance <= 4.0:
            base_speed = 15
            # Check if object is moving towards us
            object_moving_towards = any(speed > 10 for speed in object_speeds.values())
            if object_moving_towards:
                action = "STOP"
                reason = f"Moving object approaching: {closest_object_type}"
            else:
                action = "LEFT" if self.last_action != "LEFT" else "RIGHT"
                reason = f"Avoiding {closest_object_type}"

        elif closest_object_distance <= 6.0:
            base_speed = 20
            action = "SLOW DOWN"
            reason = f"Approaching {closest_object_type}"

        # PRIORITY 3: NORMAL DRIVING
        else:
            base_speed = 50
            action = "FORWARD"
            reason = "Clear path - Normal driving"

        # Adjust speed for environmental conditions
        final_speed = self.adjust_speed_for_conditions(base_speed)

        return action, final_speed, reason

    def execute_action(self, action, speed, reason):
        """Execute the decided action with appropriate speed"""
        print(f"\n[DECISION] {action} at {speed} km/h - {reason}")

        if action == "STOP":
            stop()
        elif action == "FORWARD":
            forward(speed)
        elif action == "LEFT":
            left(speed)
        elif action == "RIGHT":
            right(speed)
        elif action == "SLOW DOWN":
            slow_down(speed)

        self.last_action = action
        self.current_speed = speed
        return action, speed


# Initialize components
traffic_detector = TrafficLightDetector()
distance_estimator = DistanceEstimator()
speed_estimator = SpeedEstimator()
environment_detector = EnvironmentDetector()
car_controller = CarController()

cap = cv2.VideoCapture(0)  # webcam
frame_count = 0
object_id_counter = 0
current_objects = {}

print("🚗 Starting Enhanced Traffic Navigation System")
print("=" * 50)

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        frame_height, frame_width = frame.shape[:2]

        # Detect environment conditions
        environment = environment_detector.detect_environment(frame)
        car_controller.update_environment(environment)

        # Run YOLOv8 detection
        results = model(frame)[0]

        # Detect traffic lights only when traffic light objects are present
        traffic_lights = traffic_detector.detect_traffic_lights(frame, results)

        # Process detected objects and track them for speed estimation
        closest_distance = float('inf')
        closest_object_type = "none"
        current_objects = {}

        for i, r in enumerate(results.boxes):
            x1, y1, x2, y2 = map(int, r.xyxy[0])
            cls_id = int(r.cls[0])
            conf = float(r.conf[0])
            label = model.names[cls_id]

            # Skip traffic lights for obstacle detection
            if label == 'traffic light':
                continue

            # Calculate object center for tracking
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2

            # Create object ID for tracking
            obj_id = f"{label}_{i}_{frame_count}"
            current_objects[obj_id] = {
                'center_x': center_x,
                'center_y': center_y,
                'label': label,
                'bbox': (x1, y1, x2, y2),
                'width': x2 - x1
            }

            # Calculate PROPER distance
            obj_width = x2 - x1
            distance = distance_estimator.calculate_distance(obj_width, label)

            if distance < closest_distance and distance > 0.5:  # Filter very close false readings
                closest_distance = distance
                closest_object_type = f"{label}"

            # Draw bounding box and info
            color = (0, 255, 0) if distance > 6.0 else (0, 165, 255) if distance > 3.0 else (0, 0, 255)
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

            # Display distance info
            distance_text = f"{label} {distance}m" if distance != float('inf') else f"{label} far"
            cv2.putText(frame, distance_text, (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Estimate object speeds
        object_speeds = speed_estimator.estimate_object_speed(current_objects, frame_width, frame_height)

        # Make driving decision
        action, speed, reason = car_controller.decide_action(
            traffic_lights, closest_distance, closest_object_type, object_speeds
        )

        executed_action, executed_speed = car_controller.execute_action(action, speed, reason)

        # Update vehicle speed
        current_vehicle_speed = speed_estimator.update_vehicle_speed(executed_action, car_controller.last_action)

        # Display comprehensive information on frame
        info_y = 30
        line_height = 25

        # Environment info
        env_info = f"Time: {environment['time_of_day']} | Weather: {environment['weather']}"
        cv2.putText(frame, env_info, (10, info_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Traffic light info (only if detected)
        if traffic_lights:
            light_color = {"RED": (0, 0, 255), "YELLOW": (0, 255, 255), "GREEN": (0, 255, 0)}
            main_light = max(traffic_lights, key=lambda x: x['confidence'])
            cv2.putText(frame, f"TRAFFIC LIGHT: {main_light['color']} 🚦",
                        (10, info_y + line_height), cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                        light_color.get(main_light['color'], (255, 255, 255)), 2)

            # Draw traffic light bounding box
            x1, y1, x2, y2 = main_light['bbox']
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 3)
            cv2.putText(frame, "TRAFFIC LIGHT", (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

        # Object and speed info
        cv2.putText(frame, f"Vehicle Speed: {current_vehicle_speed} km/h",
                    (10, info_y + line_height * 2), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        closest_text = f"Closest: {closest_object_type}"
        if closest_distance != float('inf'):
            closest_text += f" ({closest_distance}m)"
        cv2.putText(frame, closest_text,
                    (10, info_y + line_height * 3), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Object speeds
        if object_speeds:
            for i, (obj_id, speed_val) in enumerate(object_speeds.items()):
                speed_text = f"Object {i + 1}: {speed_val} km/h"
                cv2.putText(frame, speed_text, (10, info_y + line_height * (4 + i)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # Action info
        cv2.putText(frame, f"ACTION: {executed_action} at {executed_speed} km/h",
                    (10, info_y + line_height * 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
        cv2.putText(frame, f"Reason: {reason}",
                    (10, info_y + line_height * 7), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        # Draw status bar
        status_bar_height = 40
        status_colors = {
            "STOP": (0, 0, 255),
            "SLOW DOWN": (0, 165, 255),
            "FORWARD": (0, 255, 0),
            "LEFT": (255, 165, 0),
            "RIGHT": (255, 165, 0)
        }
        cv2.rectangle(frame, (0, frame_height - status_bar_height),
                      (frame_width, frame_height), status_colors.get(executed_action, (100, 100, 100)), -1)

        status_text = f"{executed_action} | {current_vehicle_speed} km/h | {environment['time_of_day']} | {environment['weather']}"
        cv2.putText(frame, status_text, (10, frame_height - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow("Enhanced Traffic Navigation System", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("\n🛑 Exiting simulation...")
            break

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\n🛑 Simulation interrupted by user")

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("📹 Camera released")
    print("📝 Action log saved to 'car_actions.log'")
    print("🚗 Simulation ended")