"""Sensor diagnostics utilities for the autonomous vehicle prototype."""

import json
import os
import random
import threading
import time
from datetime import datetime
from typing import Dict, Tuple

import cv2
import numpy as np


class CameraMonitor:
    """Monitor camera health including brightness, blur and frame freezes."""

    def __init__(self) -> None:
        self.camera_working = False
        self.camera_blurred = False
        self.camera_dark = False
        self.camera_covered = False
        self.camera_frozen = False
        self.camera_fps = 0.0
        self.last_frame_time = 0.0
        self.last_frame = None
        self.consecutive_identical_frames = 0
        self.capture = None
        self.blur_threshold = 50
        self.dark_threshold = 30
        self.covered_threshold = 5
        self.consecutive_failures = 0
        self.frame_counter = 0

    def check_camera_operation(self) -> bool:
        """Attempt to read from the camera and update health indicators."""

        try:
            if self.capture is None:
                print("📷 Initializing camera...")
                self.capture = cv2.VideoCapture(0)
                if not self.capture.isOpened():
                    for i in range(1, 4):
                        self.capture = cv2.VideoCapture(i)
                        if self.capture.isOpened():
                            print(f"✅ Camera found at index {i}")
                            break
                    else:
                        print("❌ No camera found")
                        self.camera_working = False
                        return False

                self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                time.sleep(1)

            ret, frame = self.capture.read()
            if not ret or frame is None or frame.size == 0:
                self.consecutive_failures += 1
                if self.consecutive_failures > 3:
                    self.camera_working = False
                    self._reset_camera()
                return False

            self.consecutive_failures = 0
            self.camera_working = True
            self.frame_counter += 1

            self._analyze_frame_quality(frame)
            self._check_frozen_frame(frame)

            current_time = time.time()
            if self.last_frame_time > 0:
                time_diff = current_time - self.last_frame_time
                if time_diff > 0:
                    self.camera_fps = 1.0 / time_diff
            self.last_frame_time = current_time

            self.last_frame = frame.copy()
            return True
        except Exception as exc:  # pragma: no cover - hardware specific
            print(f"❌ Camera error: {exc}")
            self.camera_working = False
            return False

    def _analyze_frame_quality(self, frame: np.ndarray) -> None:
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            brightness = np.mean(gray)

            self.camera_covered = brightness < self.covered_threshold
            self.camera_blurred = laplacian_var < self.blur_threshold and not self.camera_covered
            self.camera_dark = brightness < self.dark_threshold and not self.camera_covered

            if self.frame_counter % 30 == 0:
                status = (
                    "COVERED"
                    if self.camera_covered
                    else "BLURRED"
                    if self.camera_blurred
                    else "DARK"
                    if self.camera_dark
                    else "OK"
                )
                print(
                    f"📊 Camera - Status: {status}, Blur: {laplacian_var:.1f}, Bright: {brightness:.1f}"
                )
        except Exception as exc:  # pragma: no cover
            print(f"Frame analysis error: {exc}")

    def _check_frozen_frame(self, current_frame: np.ndarray) -> None:
        if self.last_frame is not None and current_frame.shape == self.last_frame.shape:
            diff = cv2.absdiff(current_frame, self.last_frame)
            non_zero_count = np.count_nonzero(diff)

            if non_zero_count < 1000:
                self.consecutive_identical_frames += 1
                self.camera_frozen = self.consecutive_identical_frames > 10
            else:
                self.consecutive_identical_frames = 0
                self.camera_frozen = False

    def get_camera_status(self) -> Tuple[str, str]:
        if not self.camera_working:
            return "NOT_WORKING", "Camera not detected"
        if self.camera_covered:
            return "COVERED", "Camera lens covered - remove obstruction"
        if self.camera_frozen:
            return "FROZEN", "Camera image frozen - restart camera"
        if self.camera_blurred:
            return "BLURRED", "Camera image blurred - clean lens"
        if self.camera_dark:
            return "DARK", "Camera image too dark - check lighting"
        return "OK", f"Camera working - {self.camera_fps:.1f} FPS"

    def _reset_camera(self) -> None:
        try:
            if self.capture:
                self.capture.release()
                self.capture = None
            time.sleep(1)
        except Exception:  # pragma: no cover
            pass

    def cleanup(self) -> None:
        if self.capture:
            self.capture.release()
        cv2.destroyAllWindows()


class GPSMonitor:
    """Return simulated GPS readings to avoid external dependencies."""

    def __init__(self) -> None:
        self.latitude = 0.0
        self.longitude = 0.0
        self.city = "Unknown"
        self.road = "Unknown"
        self.country = "Unknown"

    def get_location(self) -> bool:
        try:
            locations = [
                {"city": "New York", "road": "5th Avenue", "lat": 40.7128, "lon": -74.0060},
                {"city": "London", "road": "Oxford Street", "lat": 51.5074, "lon": -0.1278},
                {"city": "Paris", "road": "Champs-Élysées", "lat": 48.8566, "lon": 2.3522},
                {"city": "Tokyo", "road": "Shibuya Crossing", "lat": 35.6895, "lon": 139.6917},
                {"city": "Dubai", "road": "Sheikh Zayed Road", "lat": 25.2048, "lon": 55.2708},
                {"city": "Singapore", "road": "Orchard Road", "lat": 1.3521, "lon": 103.8198},
            ]

            location = random.choice(locations)
            self.latitude = location["lat"] + random.uniform(-0.001, 0.001)
            self.longitude = location["lon"] + random.uniform(-0.001, 0.001)
            self.city = location["city"]
            self.road = location["road"]
            self.country = "Simulated"
            return True
        except Exception as exc:  # pragma: no cover
            print(f"GPS error: {exc}")
            return False

    def get_formatted_location(self) -> str:
        return f"{self.road}, {self.city}"


class SensorMonitor:
    """Aggregate diagnostics from multiple simulated vehicle sensors."""

    def __init__(self) -> None:
        self.camera_monitor = CameraMonitor()
        self.gps_monitor = GPSMonitor()
        self.sensor_data = {
            "imu": {
                "acceleration_x": 0.0,
                "acceleration_y": 0.0,
                "acceleration_z": 9.8,
                "gyro_x": 0.0,
                "gyro_y": 0.0,
                "gyro_z": 0.0,
            },
            "gps": {
                "latitude": 0.0,
                "longitude": 0.0,
                "speed": 0.0,
                "location": "Unknown",
            },
            "battery": {"charge_level": 100},
            "motors": {"temperature": 35.0, "status": "OK"},
            "camera": {"status": "OK"},
            "lidar": {"obstacles_detected": 0},
            "ultrasonic": {"front_distance": 0.0, "rear_distance": 0.0},
        }
        self.log_file = "sensor_logs.json"
        self.log_lock = threading.Lock()

    def update_sensors(self) -> Dict[str, Dict[str, float]]:
        self._simulate_imu_data()
        self._update_gps_data()
        self._simulate_battery()
        self._simulate_motor_temperature()
        self._simulate_ultrasonic()
        self._simulate_lidar()
        self._log_sensor_data()
        return self.sensor_data

    def _simulate_imu_data(self) -> None:
        self.sensor_data["imu"]["acceleration_x"] = round(random.uniform(-2, 2), 2)
        self.sensor_data["imu"]["acceleration_y"] = round(random.uniform(-2, 2), 2)
        self.sensor_data["imu"]["acceleration_z"] = round(9.8 + random.uniform(-0.5, 0.5), 2)
        self.sensor_data["imu"]["gyro_x"] = round(random.uniform(-5, 5), 2)
        self.sensor_data["imu"]["gyro_y"] = round(random.uniform(-5, 5), 2)
        self.sensor_data["imu"]["gyro_z"] = round(random.uniform(-5, 5), 2)

    def _update_gps_data(self) -> None:
        if self.gps_monitor.get_location():
            self.sensor_data["gps"]["latitude"] = round(self.gps_monitor.latitude, 6)
            self.sensor_data["gps"]["longitude"] = round(self.gps_monitor.longitude, 6)
            self.sensor_data["gps"]["location"] = self.gps_monitor.get_formatted_location()
            self.sensor_data["gps"]["speed"] = round(random.uniform(0, 80), 1)

    def _simulate_battery(self) -> None:
        self.sensor_data["battery"]["charge_level"] = max(
            0, self.sensor_data["battery"]["charge_level"] - random.uniform(0.1, 0.5)
        )

    def _simulate_motor_temperature(self) -> None:
        temperature = self.sensor_data["motors"]["temperature"] + random.uniform(-0.5, 0.5)
        temperature = min(max(temperature, 30.0), 75.0)
        self.sensor_data["motors"]["temperature"] = round(temperature, 2)
        if temperature > 65:
            self.sensor_data["motors"]["status"] = "WARNING"
        else:
            self.sensor_data["motors"]["status"] = "OK"

    def _simulate_ultrasonic(self) -> None:
        self.sensor_data["ultrasonic"]["front_distance"] = round(random.uniform(0.5, 5.0), 2)
        self.sensor_data["ultrasonic"]["rear_distance"] = round(random.uniform(0.5, 5.0), 2)

    def _simulate_lidar(self) -> None:
        self.sensor_data["lidar"]["obstacles_detected"] = random.randint(0, 3)

    def _log_sensor_data(self) -> None:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "sensors": self.sensor_data,
        }
        with self.log_lock:
            if not os.path.exists(self.log_file):
                with open(self.log_file, "w", encoding="utf-8") as handle:
                    json.dump([log_entry], handle, indent=2)
            else:
                with open(self.log_file, "r", encoding="utf-8") as handle:
                    data = json.load(handle)
                data.append(log_entry)
                with open(self.log_file, "w", encoding="utf-8") as handle:
                    json.dump(data[-100:], handle, indent=2)

    def get_status_report(self) -> Dict[str, Dict[str, float]]:
        camera_status = self.camera_monitor.get_camera_status()
        self.sensor_data["camera"]["status"] = camera_status[0]
        report = {
            "camera": {
                "status": camera_status[0],
                "message": camera_status[1],
                "fps": self.camera_monitor.camera_fps,
            },
            "motors": self.sensor_data["motors"],
            "battery": self.sensor_data["battery"],
            "gps": self.sensor_data["gps"],
            "ultrasonic": self.sensor_data["ultrasonic"],
            "lidar": self.sensor_data["lidar"],
        }
        return report

    def shutdown(self) -> None:
        self.camera_monitor.cleanup()


__all__ = ["CameraMonitor", "GPSMonitor", "SensorMonitor"]
