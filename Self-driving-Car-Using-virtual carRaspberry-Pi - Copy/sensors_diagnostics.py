# sensors_diagnostics.py - SIMPLIFIED WORKING VERSION
import time
import numpy as np
import json
from datetime import datetime
import threading
import random
import cv2
import os


class CameraMonitor:
    def __init__(self):
        self.camera_working = False
        self.camera_blurred = False
        self.camera_dark = False
        self.camera_covered = False
        self.camera_frozen = False
        self.camera_fps = 0
        self.last_frame_time = 0
        self.last_frame = None
        self.consecutive_identical_frames = 0
        self.capture = None
        self.blur_threshold = 50
        self.dark_threshold = 30
        self.covered_threshold = 5  # Very low brightness = covered
        self.consecutive_failures = 0
        self.frame_counter = 0

    def check_camera_operation(self):
        """REAL camera detection"""
        try:
            if self.capture is None:
                print("📷 Initializing camera...")
                self.capture = cv2.VideoCapture(0)
                if not self.capture.isOpened():
                    # Try different camera indices
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

            # Analyze frame quality
            self._analyze_frame_quality(frame)

            # Check for frozen frame
            self._check_frozen_frame(frame)

            # Calculate FPS
            current_time = time.time()
            if self.last_frame_time > 0:
                time_diff = current_time - self.last_frame_time
                if time_diff > 0:
                    self.camera_fps = 1.0 / time_diff
            self.last_frame_time = current_time

            self.last_frame = frame.copy()

            return True

        except Exception as e:
            print(f"❌ Camera error: {e}")
            self.camera_working = False
            return False

    def _analyze_frame_quality(self, frame):
        """Analyze frame for quality issues"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Calculate Laplacian variance for blur detection
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()

            # Check brightness
            brightness = np.mean(gray)

            # Check if camera is covered (finger on lens)
            self.camera_covered = brightness < self.covered_threshold
            self.camera_blurred = laplacian_var < self.blur_threshold and not self.camera_covered
            self.camera_dark = brightness < self.dark_threshold and not self.camera_covered

            # Debug every 30 frames
            if self.frame_counter % 30 == 0:
                status = "COVERED" if self.camera_covered else "BLURRED" if self.camera_blurred else "DARK" if self.camera_dark else "OK"
                print(f"📊 Camera - Status: {status}, Blur: {laplacian_var:.1f}, Bright: {brightness:.1f}")

        except Exception as e:
            print(f"Frame analysis error: {e}")

    def _check_frozen_frame(self, current_frame):
        """Check if camera is frozen"""
        if self.last_frame is not None and current_frame.shape == self.last_frame.shape:
            diff = cv2.absdiff(current_frame, self.last_frame)
            non_zero_count = np.count_nonzero(diff)

            if non_zero_count < 1000:
                self.consecutive_identical_frames += 1
                self.camera_frozen = self.consecutive_identical_frames > 10
            else:
                self.consecutive_identical_frames = 0
                self.camera_frozen = False

    def get_camera_status(self):
        """Get camera status with priority: covered > frozen > blurred > dark > working"""
        if not self.camera_working:
            return "NOT_WORKING", "Camera not detected"
        elif self.camera_covered:
            return "COVERED", "Camera lens covered - remove obstruction"
        elif self.camera_frozen:
            return "FROZEN", "Camera image frozen - restart camera"
        elif self.camera_blurred:
            return "BLURRED", "Camera image blurred - clean lens"
        elif self.camera_dark:
            return "DARK", "Camera image too dark - check lighting"
        else:
            return "OK", f"Camera working - {self.camera_fps:.1f} FPS"

    def _reset_camera(self):
        """Reset camera connection"""
        try:
            if self.capture:
                self.capture.release()
                self.capture = None
            time.sleep(1)
        except:
            pass

    def cleanup(self):
        """Cleanup resources"""
        if self.capture:
            self.capture.release()
        cv2.destroyAllWindows()


class GPSMonitor:
    def __init__(self):
        self.latitude = 0.0
        self.longitude = 0.0
        self.city = "Unknown"
        self.road = "Unknown"
        self.country = "Unknown"

    def get_location(self):
        """Get location information - simplified without external dependencies"""
        try:
            # Simulate realistic locations without complex geocoding
            locations = [
                {"city": "New York", "road": "5th Avenue", "lat": 40.7128, "lon": -74.0060},
                {"city": "London", "road": "Oxford Street", "lat": 51.5074, "lon": -0.1278},
                {"city": "Paris", "road": "Champs-Élysées", "lat": 48.8566, "lon": 2.3522},
                {"city": "Tokyo", "road": "Shibuya Crossing", "lat": 35.6895, "lon": 139.6917},
                {"city": "Dubai", "road": "Sheikh Zayed Road", "lat": 25.2048, "lon": 55.2708},
                {"city": "Singapore", "road": "Orchard Road", "lat": 1.3521, "lon": 103.8198},
            ]

            # Pick a location and add some movement
            location = random.choice(locations)
            self.latitude = location["lat"] + random.uniform(-0.001, 0.001)
            self.longitude = location["lon"] + random.uniform(-0.001, 0.001)
            self.city = location["city"]
            self.road = location["road"]
            self.country = "Simulated"

            return True

        except Exception as e:
            print(f"GPS error: {e}")
            return False

    def get_formatted_location(self):
        """Get formatted location"""
        return f"{self.road}, {self.city}"


class SensorMonitor:
    def __init__(self):
        self.camera_monitor = CameraMonitor()
        self.gps_monitor = GPSMonitor()

        self.sensor_data = {
            'camera': {'status': 'INITIALIZING', 'fps': 0, 'message': 'Starting...', 'last_update': time.time()},
            'gps': {'status': 'NORMAL', 'location': 'Unknown', 'last_update': time.time()},
            'battery': {'status': 'NORMAL', 'charge_level': 85, 'last_update': time.time()},
            'lidar': {'status': 'NORMAL', 'distance': 0.0, 'last_update': time.time()},
            'ultrasonic': {'status': 'NORMAL', 'front_distance': 0.0, 'last_update': time.time()},
            'motors': {'status': 'NORMAL', 'temperature': 30.0, 'last_update': time.time()},
        }

        self.alerts = []
        self.alert_history = []
        self.is_monitoring = False
        self.monitor_thread = None

    def start_monitoring(self):
        """Start monitoring"""
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        print("🚗 Sensor monitoring started...")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        self.camera_monitor.cleanup()
        print("🛑 Sensor monitoring stopped")

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.is_monitoring:
            self.update_sensor_data()
            self.check_anomalies()
            time.sleep(1)

    def update_sensor_data(self):
        """Update all sensor data"""
        current_time = time.time()

        # Update camera
        self.camera_monitor.check_camera_operation()
        camera_status, camera_message = self.camera_monitor.get_camera_status()
        self.sensor_data['camera']['status'] = camera_status
        self.sensor_data['camera']['fps'] = self.camera_monitor.camera_fps
        self.sensor_data['camera']['message'] = camera_message
        self.sensor_data['camera']['last_update'] = current_time

        # Update GPS
        self.gps_monitor.get_location()
        self.sensor_data['gps']['location'] = self.gps_monitor.get_formatted_location()
        self.sensor_data['gps']['last_update'] = current_time

        # Update other sensors with simulated data
        self.sensor_data['battery']['charge_level'] = max(10, self.sensor_data['battery']['charge_level'] - 0.02)
        self.sensor_data['battery']['last_update'] = current_time

        self.sensor_data['lidar']['distance'] = random.uniform(1.0, 15.0)
        self.sensor_data['lidar']['last_update'] = current_time

        self.sensor_data['ultrasonic']['front_distance'] = random.uniform(0.5, 8.0)
        self.sensor_data['ultrasonic']['last_update'] = current_time

        self.sensor_data['motors']['temperature'] = 30.0 + random.uniform(0, 15)
        self.sensor_data['motors']['last_update'] = current_time

    def check_anomalies(self):
        """Check for anomalies"""
        # Clear previous camera alerts
        self._remove_camera_alerts()

        # Check camera
        camera_status = self.sensor_data['camera']['status']
        camera_message = self.sensor_data['camera']['message']

        if camera_status != "OK":
            if camera_status == "NOT_WORKING":
                self._add_alert('CAMERA', camera_message, 'CRITICAL')
            elif camera_status == "COVERED":
                self._add_alert('CAMERA', camera_message, 'WARNING')
            elif camera_status in ["FROZEN", "BLURRED", "DARK"]:
                self._add_alert('CAMERA', camera_message, 'WARNING')

        # Check battery
        if self.sensor_data['battery']['charge_level'] < 20:
            self._add_alert('BATTERY', f"Low battery: {self.sensor_data['battery']['charge_level']:.0f}%", 'WARNING')
        elif self.sensor_data['battery']['charge_level'] < 10:
            self._add_alert('BATTERY', f"Critical battery: {self.sensor_data['battery']['charge_level']:.0f}%",
                            'CRITICAL')

        # Check motor temperature
        if self.sensor_data['motors']['temperature'] > 70:
            self._add_alert('MOTORS', f"High temperature: {self.sensor_data['motors']['temperature']:.1f}°C", 'WARNING')

    def _remove_camera_alerts(self):
        """Remove camera alerts"""
        self.alerts = [alert for alert in self.alerts if alert['sensor'] != 'CAMERA']

    def _add_alert(self, sensor, message, level):
        """Add alert"""
        alert = {
            'timestamp': datetime.now().strftime("%H:%M:%S"),
            'sensor': sensor,
            'message': message,
            'level': level,
            'acknowledged': False
        }

        # Check if alert already exists
        existing = False
        for a in self.alerts:
            if a['sensor'] == sensor and a['message'] == message and not a['acknowledged']:
                existing = True
                break

        if not existing:
            self.alerts.append(alert)
            self.alert_history.append(alert.copy())
            print(f"🚨 [{level}] {sensor}: {message}")

    def acknowledge_alert(self, sensor, message):
        """Acknowledge alert"""
        for alert in self.alerts:
            if alert['sensor'] == sensor and alert['message'] == message:
                alert['acknowledged'] = True
        self.alerts = [a for a in self.alerts if not a['acknowledged']]

    def get_active_alerts(self):
        """Get active alerts"""
        return [alert for alert in self.alerts if not alert['acknowledged']]

    def get_critical_alerts(self):
        """Get critical alerts"""
        return [alert for alert in self.alerts if alert['level'] == 'CRITICAL' and not alert['acknowledged']]

    def get_all_sensor_data(self):
        """Get all sensor data"""
        return self.sensor_data.copy()

    def get_gps_location(self):
        """Get GPS location"""
        return self.sensor_data['gps']['location']

    def export_logs(self, filename='sensor_logs.json'):
        """Export logs"""
        with open(filename, 'w') as f:
            json.dump(self.alert_history, f, indent=2)
        print(f"📄 Logs exported to {filename}")


class OnboardDisplay:
    def __init__(self, sensor_monitor):
        self.sensor_monitor = sensor_monitor
        self.display_width = 800
        self.display_height = 480

    def start_display(self):
        """Start display"""
        try:
            print("📺 Starting display...")

            while True:
                # Create simple console display instead of OpenCV to avoid memory issues
                self._console_display()
                time.sleep(2)

        except KeyboardInterrupt:
            print("\n🛑 Display stopped")

    def _console_display(self):
        """Console-based display"""
        os.system('cls' if os.name == 'nt' else 'clear')

        print("=" * 80)
        print("🚗 AUTONOMOUS VEHICLE SENSOR MONITOR")
        print("=" * 80)

        sensor_data = self.sensor_monitor.get_all_sensor_data()
        alerts = self.sensor_monitor.get_active_alerts()

        # Display GPS location
        print(f"\n📍 LOCATION: {self.sensor_monitor.get_gps_location()}")

        # Display sensor status
        print("\nSENSOR STATUS:")
        print("-" * 40)
        for sensor, data in sensor_data.items():
            status = data['status']
            if status == 'OK' or status == 'NORMAL':
                icon = "🟢"
            elif status == 'NOT_WORKING':
                icon = "🔴"
            else:
                icon = "🟡"

            if sensor == 'camera':
                info = f"{data['fps']:.1f} FPS" if data['fps'] > 0 else "No signal"
            elif sensor == 'battery':
                info = f"{data['charge_level']:.0f}%"
            elif sensor == 'lidar':
                info = f"{data['distance']:.1f}m"
            elif sensor == 'motors':
                info = f"{data['temperature']:.1f}°C"
            else:
                info = ""

            print(f"  {icon} {sensor.upper():12} : {status:15} {info}")

        # Display alerts
        print(f"\n🚨 ACTIVE ALERTS ({len(alerts)}):")
        print("-" * 40)
        if alerts:
            for alert in alerts:
                level_icon = "🔴" if alert['level'] == 'CRITICAL' else "🟡"
                print(f"  {level_icon} [{alert['timestamp']}] {alert['sensor']}: {alert['message']}")
        else:
            print("  ✅ All systems normal")

        print(f"\n💡 Tips:")
        print("  - Cover camera lens to test obstruction detection")
        print("  - Move camera to test blur detection")
        print("  - Press Ctrl+C to exit")
        print("=" * 80)


def main():
    """Main function"""
    print("🚗 Starting Autonomous Vehicle Sensor Monitoring System...")

    # Initialize monitor
    sensor_monitor = SensorMonitor()

    # Start monitoring
    sensor_monitor.start_monitoring()

    # Start display
    display = OnboardDisplay(sensor_monitor)

    try:
        display.start_display()
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        sensor_monitor.stop_monitoring()
        sensor_monitor.export_logs()


if __name__ == "__main__":
    main()