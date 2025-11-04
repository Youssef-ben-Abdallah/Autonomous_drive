"""Emergency services integration for the autonomous vehicle prototype."""

from __future__ import annotations

import json
import smtplib
import ssl
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict


@dataclass
class SMTPConfig:
    server: str = "smtp.gmail.com"
    port: int = 587
    sender_email: str = "your.email@gmail.com"
    sender_password: str = "your_app_password"


class EmergencyServices:
    """Detect severe incidents and trigger emergency notifications."""

    def __init__(self) -> None:
        self.emergency_contacts = {
            "email": "mohamedazizzouari2@gmail.com",
            "phone": "+21699910672",
        }
        self.smtp_config = SMTPConfig()
        self.acceleration_threshold = 8.0
        self.impact_threshold = 15.0
        self.rollover_threshold = 6.0
        self.accident_detected = False
        self.last_emergency_call = 0.0
        self.cooldown_period = 300.0

    def detect_accident(self, sensor_data: Dict[str, Dict[str, float]]) -> bool:
        try:
            imu_data = sensor_data.get("imu", {})
            gps_data = sensor_data.get("gps", {})

            acceleration_x = abs(imu_data.get("acceleration_x", 0))
            acceleration_y = abs(imu_data.get("acceleration_y", 0))
            acceleration_z = abs(imu_data.get("acceleration_z", 0) - 9.8)
            total_acceleration = (acceleration_x ** 2 + acceleration_y ** 2 + acceleration_z ** 2) ** 0.5

            gyro_x = abs(imu_data.get("gyro_x", 0))
            gyro_y = abs(imu_data.get("gyro_y", 0))
            gyro_z = abs(imu_data.get("gyro_z", 0))
            total_rotation = (gyro_x ** 2 + gyro_y ** 2 + gyro_z ** 2) ** 0.5

            current_speed = gps_data.get("speed", 0)
            sudden_stop = current_speed < 5 and total_acceleration > self.acceleration_threshold

            crash_impact = total_acceleration > self.impact_threshold
            rollover = total_rotation > self.rollover_threshold
            accident = crash_impact or rollover or sudden_stop

            if accident and not self.accident_detected:
                self.accident_detected = True
                self.trigger_emergency_protocol(sensor_data)
                return True

            if self.accident_detected and total_acceleration < 2 and total_rotation < 1:
                self.accident_detected = False

            return False
        except Exception as exc:  # pragma: no cover
            print(f"Accident detection error: {exc}")
            return False

    def trigger_emergency_protocol(self, sensor_data: Dict[str, Dict[str, float]]) -> None:
        print("🚨 ACCIDENT DETECTED! Initiating emergency protocol...")
        location = self._get_emergency_location(sensor_data)
        vehicle_status = self._get_vehicle_status(sensor_data)

        emergency_thread = threading.Thread(
            target=self._send_emergency_notifications,
            args=(location, vehicle_status),
            daemon=True,
        )
        emergency_thread.start()

        self._log_emergency_incident(location, vehicle_status)
        self._activate_safety_measures()

    def _get_emergency_location(self, sensor_data: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        gps_data = sensor_data.get("gps", {})
        return {
            "latitude": gps_data.get("latitude", 0),
            "longitude": gps_data.get("longitude", 0),
            "speed": gps_data.get("speed", 0),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "address": gps_data.get("location", "Unknown location"),
        }

    def _get_vehicle_status(self, sensor_data: Dict[str, Dict[str, float]]) -> Dict[str, float]:
        return {
            "battery_level": sensor_data.get("battery", {}).get("charge_level", 0),
            "motor_temperature": sensor_data.get("motors", {}).get("temperature", 0),
            "camera_status": sensor_data.get("camera", {}).get("status", "Unknown"),
            "obstacles_detected": sensor_data.get("lidar", {}).get("obstacles_detected", 0),
            "front_distance": sensor_data.get("ultrasonic", {}).get("front_distance", 0),
        }

    def _send_emergency_notifications(self, location: Dict[str, float], vehicle_status: Dict[str, float]) -> None:
        current_time = time.time()
        if current_time - self.last_emergency_call < self.cooldown_period:
            print("⚠️ Emergency call cooldown active")
            return

        self.last_emergency_call = current_time
        email_success = self._send_real_emergency_email(location, vehicle_status)
        phone_success = self._simulate_emergency_call(location)

        if email_success:
            print("✅ REAL emergency email sent successfully!")
        else:
            print("❌ Failed to send emergency email")
        if phone_success:
            print("📞 Simulated emergency phone call placed")

    def _send_real_emergency_email(self, location: Dict[str, float], vehicle_status: Dict[str, float]) -> bool:
        try:
            if (
                self.smtp_config.sender_email == "your.email@gmail.com"
                or self.smtp_config.sender_password == "your_app_password"
            ):
                print("❌ Please configure your Gmail SMTP credentials first!")
                print("   Update sender_email and sender_password in the configuration")
                return False

            subject = "🚨 VEHICLE ACCIDENT ALERT 🚨"
            message = f"""
EMERGENCY ALERT - VEHICLE ACCIDENT DETECTED

🚗 VEHICLE STATUS:
• Location: {location['address']}
• Coordinates: {location['latitude']:.6f}, {location['longitude']:.6f}
• Speed at impact: {location['speed']:.1f} km/h
• Time: {location['timestamp']}

📊 VEHICLE CONDITION:
• Battery Level: {vehicle_status['battery_level']:.0f}%
• Motor Temperature: {vehicle_status['motor_temperature']:.1f}°C
• Camera Status: {vehicle_status['camera_status']}
• Obstacles Detected: {vehicle_status['obstacles_detected']}
• Front Distance: {vehicle_status['front_distance']:.1f}m

🆘 IMMEDIATE ACTION REQUIRED:
1. Check driver status immediately
2. Contact emergency services if needed
3. Dispatch assistance to the location
4. Verify vehicle safety systems

📍 LOCATION MAP:
https://maps.google.com/?q={location['latitude']},{location['longitude']}

This is an automated emergency alert from the vehicle's safety system.
Please respond immediately.

⚠️ URGENT ATTENTION REQUIRED ⚠️
"""

            msg = MIMEMultipart()
            msg["From"] = self.smtp_config.sender_email
            msg["To"] = self.emergency_contacts["email"]
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain"))

            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_config.server, self.smtp_config.port) as server:
                server.starttls(context=context)
                server.login(self.smtp_config.sender_email, self.smtp_config.sender_password)
                server.send_message(msg)

            return True
        except Exception as exc:  # pragma: no cover - network failures
            print(f"Email sending failed: {exc}")
            return False

    def _simulate_emergency_call(self, location: Dict[str, float]) -> bool:
        print("📞 Simulating emergency phone call...")
        print(
            f"Contacting emergency services at {self.emergency_contacts['phone']} "
            f"with location {location['address']}"
        )
        return True

    def _log_emergency_incident(self, location: Dict[str, float], vehicle_status: Dict[str, float]) -> None:
        incident = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "location": location,
            "vehicle_status": vehicle_status,
        }
        try:
            with open("emergency_incidents.json", "a", encoding="utf-8") as handle:
                handle.write(json.dumps(incident) + "\n")
        except Exception as exc:  # pragma: no cover
            print(f"Failed to log emergency incident: {exc}")

    def _activate_safety_measures(self) -> None:
        print("Activating safety measures:")
        print("1. Unlocking doors")
        print("2. Switching on hazard lights")
        print("3. Notifying nearby vehicles")
        print("4. Preparing emergency braking system")


__all__ = ["EmergencyServices", "SMTPConfig"]
