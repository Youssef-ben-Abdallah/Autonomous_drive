"""Object and traffic perception utilities built around YOLOv8.

The original ``obstacle_detection.py`` script mixed model initialisation,
utility functions and the main event loop in a single file.  This module keeps
all behavioural logic but organises it into small, well documented classes so
that perception can be reused from tests or higher level applications.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import cv2
import numpy as np
import time

from ultralytics import YOLO

from autonomous_drive.control.motor_controller import MotorController
from autonomous_drive.utils.logger import get_logger

# ---------------------------------------------------------------------------
# Logging helper used across the module
# ---------------------------------------------------------------------------

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Action logging utilities
# ---------------------------------------------------------------------------


def log_action(action: str, speed: int) -> None:
    """Persist a human readable action log with timestamps.

    The original implementation wrote to ``car_actions.log`` and the behaviour is
    preserved to ensure downstream tooling keeps working.
    """

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with Path("car_actions.log").open("a", encoding="utf-8") as handle:
        handle.write(f"{timestamp} - {action} at {speed} km/h\n")


# ---------------------------------------------------------------------------
# Motor action helpers (used by :class:`CarController`)
# ---------------------------------------------------------------------------


class MotorActions:
    """Small wrapper that proxies driving commands to ``MotorController``."""

    def __init__(self, controller: Optional[MotorController] = None) -> None:
        self.controller = controller or MotorController()

    def stop(self) -> None:
        logger.info("[MOTORS] 🛑 STOPPING - Speed: 0 km/h")
        self.controller.stop()
        log_action("STOP", 0)

    def forward(self, speed: int = 30) -> None:
        logger.info("[MOTORS] 🚗 MOVING FORWARD - Speed: %s km/h", speed)
        self.controller.forward(speed)
        log_action("FORWARD", speed)

    def left(self, speed: int = 20) -> None:
        logger.info("[MOTORS] ↪️ TURNING LEFT - Speed: %s km/h", speed)
        self.controller.left(speed)
        log_action("LEFT", speed)

    def right(self, speed: int = 20) -> None:
        logger.info("[MOTORS] ↩️ TURNING RIGHT - Speed: %s km/h", speed)
        self.controller.right(speed)
        log_action("RIGHT", speed)

    def slow_down(self, speed: int = 10) -> None:
        logger.info("[MOTORS] 🐢 SLOWING DOWN - Speed: %s km/h", speed)
        self.controller.forward(speed)
        log_action("SLOW DOWN", speed)


# ---------------------------------------------------------------------------
# Perception helpers reused by ``ObjectPerceptionSystem``
# ---------------------------------------------------------------------------


class TrafficLightDetector:
    """Specialised detector that extracts light colour from YOLO boxes."""

    def __init__(self) -> None:
        self.traffic_light_class_id = 9
        self.last_detection_time = 0.0
        self.current_light_state = "UNKNOWN"

    def detect(self, frame: np.ndarray, results) -> List[Dict[str, object]]:
        traffic_lights: List[Dict[str, object]] = []
        for box in results.boxes:
            cls_id = int(box.cls[0])
            if cls_id != self.traffic_light_class_id:
                continue

            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            if confidence <= 0.5:
                continue

            roi = frame[y1:y2, x1:x2]
            traffic_lights.append(
                {
                    "bbox": (x1, y1, x2, y2),
                    "color": self._analyse_colour(roi),
                    "confidence": confidence,
                }
            )
        return traffic_lights

    def _analyse_colour(self, roi: np.ndarray) -> str:
        if roi.size == 0:
            return "UNKNOWN"

        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        red_ranges = [((0, 150, 100), (10, 255, 255)), ((170, 150, 100), (180, 255, 255))]
        yellow_range = ((20, 150, 150), (30, 255, 255))
        green_range = ((45, 100, 100), (85, 255, 255))

        red_pixels = sum(cv2.countNonZero(cv2.inRange(hsv, lower, upper)) for lower, upper in red_ranges)
        yellow_pixels = cv2.countNonZero(cv2.inRange(hsv, *yellow_range))
        green_pixels = cv2.countNonZero(cv2.inRange(hsv, *green_range))

        min_pixels = 20
        if red_pixels > max(yellow_pixels, green_pixels) and red_pixels > min_pixels:
            return "RED"
        if yellow_pixels > max(green_pixels, red_pixels) and yellow_pixels > min_pixels:
            return "YELLOW"
        if green_pixels > min_pixels:
            return "GREEN"
        return "UNKNOWN"


class DistanceEstimator:
    """Approximate object distance based on bounding box width."""

    def __init__(self, known_widths: Optional[Dict[str, float]] = None) -> None:
        self.known_widths = known_widths or {
            "person": 0.5,
            "bicycle": 0.75,
            "car": 1.8,
            "motorcycle": 0.8,
            "bus": 2.5,
            "truck": 2.5,
            "traffic light": 0.3,
            "stop sign": 0.6,
            "cat": 0.3,
            "dog": 0.4,
            "bird": 0.2,
        }
        self.focal_length = 1000

    def calculate(self, object_width_pixels: int, object_type: str = "car") -> float:
        if object_width_pixels <= 0:
            return float("inf")
        known_width = self.known_widths.get(object_type, 1.5)
        distance = (known_width * self.focal_length) / object_width_pixels
        return round(distance, 1) if distance <= 50 else float("inf")


class SpeedEstimator:
    """Track per-object movement between frames to approximate speed."""

    def __init__(self) -> None:
        self.previous_positions: Dict[str, Dict[str, float]] = {}
        self.previous_time = time.time()
        self.vehicle_speed = 0
        self.speed_history: List[int] = []

    def estimate(self, current_objects: Dict[str, Dict[str, object]], frame_width: int) -> Dict[str, float]:
        current_time = time.time()
        time_elapsed = current_time - self.previous_time
        speeds: Dict[str, float] = {}

        if time_elapsed < 0.1:
            return speeds

        for obj_id, info in current_objects.items():
            if obj_id not in self.previous_positions:
                self.previous_positions[obj_id] = info
                continue

            prev = self.previous_positions[obj_id]
            pixel_distance = np.hypot(info["center_x"] - prev["center_x"], info["center_y"] - prev["center_y"])
            meters_per_pixel = 2.3 / frame_width
            speed_mps = (pixel_distance * meters_per_pixel) / time_elapsed
            speed_kmh = speed_mps * 3.6

            if 1.0 < speed_kmh < 100:
                speeds[obj_id] = round(speed_kmh, 1)

            self.previous_positions[obj_id] = info

        self.previous_time = current_time
        return speeds

    def update_vehicle_speed(self, action: str, previous_action: str) -> int:
        acceleration_rate = 5
        deceleration_rate = 10

        if action == "STOP":
            self.vehicle_speed = max(0, self.vehicle_speed - deceleration_rate)
        elif action == "SLOW DOWN":
            self.vehicle_speed = max(0, self.vehicle_speed - int(deceleration_rate * 0.7))
        elif action == "FORWARD":
            self.vehicle_speed = min(60, self.vehicle_speed + acceleration_rate if previous_action == "FORWARD" else 30)
        elif action in {"LEFT", "RIGHT"}:
            self.vehicle_speed = min(30, self.vehicle_speed)

        self.speed_history.append(self.vehicle_speed)
        if len(self.speed_history) > 10:
            self.speed_history.pop(0)
        return self.vehicle_speed


class EnvironmentDetector:
    """Estimate coarse environmental conditions from the current frame."""

    def __init__(self) -> None:
        self.current_conditions = {
            "time_of_day": "DAY",
            "weather": "CLEAR",
            "brightness": 0.5,
        }

    def detect(self, frame: np.ndarray) -> Dict[str, object]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        brightness = float(np.mean(gray) / 255.0)
        self.current_conditions["brightness"] = brightness

        if brightness < 0.3:
            self.current_conditions["time_of_day"] = "NIGHT"
        elif brightness < 0.5:
            self.current_conditions["time_of_day"] = "DUSK/DAWN"
        else:
            self.current_conditions["time_of_day"] = "DAY"

        colour_variance = float(np.var(frame) / (255 ** 2))
        if colour_variance < 0.05:
            self.current_conditions["weather"] = "FOGGY"
        elif brightness > 0.8:
            self.current_conditions["weather"] = "SUNNY"
        elif brightness < 0.4:
            self.current_conditions["weather"] = "OVERCAST"
        else:
            self.current_conditions["weather"] = "CLEAR"

        return dict(self.current_conditions)


class CarController:
    """Decision making layer that transforms perception into motor commands."""

    def __init__(self, motor_actions: Optional[MotorActions] = None) -> None:
        self.motor_actions = motor_actions or MotorActions()
        self.traffic_light_state = "UNKNOWN"
        self.last_action = "STOP"
        self.current_speed = 0
        self.environment_conditions: Dict[str, object] = {}

    def update_environment(self, conditions: Dict[str, object]) -> None:
        self.environment_conditions = conditions

    def _adjust_speed(self, base_speed: int) -> int:
        multiplier = 1.0
        time_of_day = self.environment_conditions.get("time_of_day")
        weather = self.environment_conditions.get("weather")

        if time_of_day == "NIGHT":
            multiplier *= 0.7
        elif time_of_day == "DUSK/DAWN":
            multiplier *= 0.8

        if weather == "FOGGY":
            multiplier *= 0.5
        elif weather == "OVERCAST":
            multiplier *= 0.9

        return int(base_speed * multiplier)

    def decide_action(
        self,
        traffic_lights: Sequence[Dict[str, object]],
        closest_distance: float,
        closest_type: str,
        object_speeds: Dict[str, float],
    ) -> Tuple[str, int, str]:
        if traffic_lights:
            main_light = max(traffic_lights, key=lambda x: x["confidence"])
            self.traffic_light_state = str(main_light["color"])
        else:
            self.traffic_light_state = "UNKNOWN"

        if self.traffic_light_state == "RED":
            base_speed, action, reason = 0, "STOP", "Red traffic light detected"
        elif self.traffic_light_state == "YELLOW":
            if self.last_action == "FORWARD" and closest_distance > 5.0:
                base_speed, action, reason = 20, "SLOW DOWN", "Yellow light – proceeding with caution"
            else:
                base_speed, action, reason = 0, "STOP", "Yellow light – preparing to stop"
        elif self.traffic_light_state == "GREEN":
            if closest_distance > 8.0:
                base_speed, action, reason = 40, "FORWARD", "Green light – clear path"
            elif closest_distance > 4.0:
                base_speed, action, reason = 25, "SLOW DOWN", "Green light – obstacle ahead"
            else:
                base_speed, action, reason = 0, "STOP", "Green light – obstacle too close"
        elif closest_distance <= 2.0:
            base_speed, action, reason = 0, "STOP", f"Emergency stop: {closest_type} too close"
        elif closest_distance <= 4.0:
            base_speed = 15
            if any(speed > 10 for speed in object_speeds.values()):
                action, reason = "STOP", f"Moving object approaching: {closest_type}"
            else:
                action = "LEFT" if self.last_action != "LEFT" else "RIGHT"
                reason = f"Avoiding {closest_type}"
        elif closest_distance <= 6.0:
            base_speed, action, reason = 20, "SLOW DOWN", f"Approaching {closest_type}"
        else:
            base_speed, action, reason = 50, "FORWARD", "Clear path – normal driving"

        final_speed = self._adjust_speed(base_speed)
        return action, final_speed, reason

    def execute(self, action: str, speed: int, reason: str) -> Tuple[str, int]:
        logger.info("[DECISION] %s at %s km/h – %s", action, speed, reason)

        if action == "STOP":
            self.motor_actions.stop()
        elif action == "FORWARD":
            self.motor_actions.forward(speed)
        elif action == "LEFT":
            self.motor_actions.left(speed)
        elif action == "RIGHT":
            self.motor_actions.right(speed)
        elif action == "SLOW DOWN":
            self.motor_actions.slow_down(speed)

        self.last_action = action
        self.current_speed = speed
        return action, speed


# ---------------------------------------------------------------------------
# Top level perception system
# ---------------------------------------------------------------------------


@dataclass
class FrameContext:
    """Information extracted from a frame for visualisation purposes."""

    environment: Dict[str, object]
    traffic_lights: List[Dict[str, object]]
    closest_distance: float
    closest_type: str
    object_speeds: Dict[str, float]
    action: str
    action_speed: int
    reason: str
    vehicle_speed: int


class ObjectPerceptionSystem:
    """High level orchestrator that ties all helper classes together."""

    def __init__(self, model_path: str = "yolov8n.pt") -> None:
        self.logger = logger
        self.model_path = model_path
        self.model = self._load_model(model_path)
        self.traffic_detector = TrafficLightDetector()
        self.distance_estimator = DistanceEstimator()
        self.speed_estimator = SpeedEstimator()
        self.environment_detector = EnvironmentDetector()
        self.controller = CarController()

    def _load_model(self, model_path: str) -> YOLO:
        model = YOLO(model_path)
        self.logger.info("YOLOv8 model loaded: %s", model_path)
        return model

    # ------------------------------------------------------------------
    # Frame processing
    # ------------------------------------------------------------------

    def process_frame(self, frame: np.ndarray, frame_count: int) -> FrameContext:
        frame_height, frame_width = frame.shape[:2]

        environment = self.environment_detector.detect(frame)
        self.controller.update_environment(environment)

        results = self.model(frame)[0]
        traffic_lights = self.traffic_detector.detect(frame, results)

        closest_distance = float("inf")
        closest_type = "none"
        current_objects: Dict[str, Dict[str, object]] = {}

        for idx, box in enumerate(results.boxes):
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            label = str(self.model.names[cls_id])
            if label == "traffic light":
                continue

            obj_id = f"{label}_{idx}_{frame_count}"
            current_objects[obj_id] = {
                "center_x": (x1 + x2) // 2,
                "center_y": (y1 + y2) // 2,
                "label": label,
                "bbox": (x1, y1, x2, y2),
                "width": x2 - x1,
            }

            distance = self.distance_estimator.calculate(x2 - x1, label)
            if distance < closest_distance and distance > 0.5:
                closest_distance = distance
                closest_type = label

        object_speeds = self.speed_estimator.estimate(current_objects, frame_width)
        action, speed, reason = self.controller.decide_action(
            traffic_lights, closest_distance, closest_type, object_speeds
        )
        previous_action = self.controller.last_action
        executed_action, executed_speed = self.controller.execute(action, speed, reason)
        vehicle_speed = self.speed_estimator.update_vehicle_speed(executed_action, previous_action)

        return FrameContext(
            environment=environment,
            traffic_lights=traffic_lights,
            closest_distance=closest_distance,
            closest_type=closest_type,
            object_speeds=object_speeds,
            action=executed_action,
            action_speed=executed_speed,
            reason=reason,
            vehicle_speed=vehicle_speed,
        )

    # ------------------------------------------------------------------
    # Visualisation helpers
    # ------------------------------------------------------------------

    def draw_overlay(self, frame: np.ndarray, context: FrameContext) -> np.ndarray:
        frame_height, frame_width = frame.shape[:2]
        info_y = 30
        line_height = 25

        env_info = f"Time: {context.environment['time_of_day']} | Weather: {context.environment['weather']}"
        cv2.putText(frame, env_info, (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        if context.traffic_lights:
            main_light = max(context.traffic_lights, key=lambda x: x["confidence"])
            light_colour = {"RED": (0, 0, 255), "YELLOW": (0, 255, 255), "GREEN": (0, 255, 0)}
            cv2.putText(
                frame,
                f"TRAFFIC LIGHT: {main_light['color']} 🚦",
                (10, info_y + line_height),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                light_colour.get(str(main_light["color"]), (255, 255, 255)),
                2,
            )
            x1, y1, x2, y2 = main_light["bbox"]
            cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 0), 3)
            cv2.putText(frame, "TRAFFIC LIGHT", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)

        cv2.putText(
            frame,
            f"Vehicle Speed: {context.vehicle_speed} km/h",
            (10, info_y + line_height * 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        closest_text = f"Closest: {context.closest_type}"
        if context.closest_distance != float("inf"):
            closest_text += f" ({context.closest_distance}m)"
        cv2.putText(
            frame,
            closest_text,
            (10, info_y + line_height * 3),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
        )

        for idx, speed in enumerate(context.object_speeds.values()):
            cv2.putText(
                frame,
                f"Object {idx + 1}: {speed} km/h",
                (10, info_y + line_height * (4 + idx)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (255, 255, 255),
                1,
            )

        cv2.putText(
            frame,
            f"ACTION: {context.action} at {context.action_speed} km/h",
            (10, info_y + line_height * 6),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 0),
            2,
        )
        cv2.putText(
            frame,
            f"Reason: {context.reason}",
            (10, info_y + line_height * 7),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.4,
            (255, 255, 255),
            1,
        )

        status_bar_height = 40
        status_colour = {
            "STOP": (0, 0, 255),
            "SLOW DOWN": (0, 165, 255),
            "FORWARD": (0, 255, 0),
            "LEFT": (255, 165, 0),
            "RIGHT": (255, 165, 0),
        }.get(context.action, (100, 100, 100))
        cv2.rectangle(frame, (0, frame_height - status_bar_height), (frame_width, frame_height), status_colour, -1)
        status_text = (
            f"{context.action} | {context.vehicle_speed} km/h | "
            f"{context.environment['time_of_day']} | {context.environment['weather']}"
        )
        cv2.putText(
            frame,
            status_text,
            (10, frame_height - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        return frame

    # ------------------------------------------------------------------
    # Execution helper
    # ------------------------------------------------------------------

    def run(self, camera_index: int = 0) -> None:
        cap = cv2.VideoCapture(camera_index)
        frame_count = 0

        print("🚗 Starting Enhanced Traffic Navigation System")
        print("=" * 50)

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1
                context = self.process_frame(frame, frame_count)
                annotated_frame = self.draw_overlay(frame, context)
                cv2.imshow("Enhanced Traffic Navigation System", annotated_frame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
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


__all__ = [
    "ObjectPerceptionSystem",
    "MotorActions",
    "TrafficLightDetector",
    "DistanceEstimator",
    "SpeedEstimator",
    "EnvironmentDetector",
    "CarController",
    "FrameContext",
]
