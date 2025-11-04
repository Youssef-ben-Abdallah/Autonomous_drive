# emergency_services.py
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import time
from datetime import datetime
import threading


class EmergencyServices:
    def __init__(self):
        self.emergency_contacts = {
            'email': 'mohamedazizzouari2@gmail.com',
            'phone': '+21699910672'
        }

        # Gmail SMTP Configuration
        self.smtp_config = {
            'server': 'smtp.gmail.com',
            'port': 587,
            'sender_email': 'your.email@gmail.com',  # CHANGE THIS to your sender email
            'sender_password': 'your_app_password'  # CHANGE THIS to your app password
        }

        # Accident detection thresholds
        self.acceleration_threshold = 8.0
        self.impact_threshold = 15.0
        self.rollover_threshold = 6.0

        self.accident_detected = False
        self.last_emergency_call = 0
        self.cooldown_period = 300

    def detect_accident(self, sensor_data):
        """Detect potential accident from sensor data"""
        try:
            imu_data = sensor_data.get('imu', {})
            gps_data = sensor_data.get('gps', {})

            # Check for sudden deceleration (crash)
            acceleration_x = abs(imu_data.get('acceleration_x', 0))
            acceleration_y = abs(imu_data.get('acceleration_y', 0))
            acceleration_z = abs(imu_data.get('acceleration_z', 0) - 9.8)

            total_acceleration = (acceleration_x ** 2 + acceleration_y ** 2 + acceleration_z ** 2) ** 0.5

            # Check for rollover (rapid rotation)
            gyro_x = abs(imu_data.get('gyro_x', 0))
            gyro_y = abs(imu_data.get('gyro_y', 0))
            gyro_z = abs(imu_data.get('gyro_z', 0))

            total_rotation = (gyro_x ** 2 + gyro_y ** 2 + gyro_z ** 2) ** 0.5

            # Check for sudden stop
            current_speed = gps_data.get('speed', 0)
            sudden_stop = current_speed < 5 and total_acceleration > self.acceleration_threshold

            # Accident conditions
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

        except Exception as e:
            print(f"Accident detection error: {e}")
            return False

    def trigger_emergency_protocol(self, sensor_data):
        """Execute emergency procedures"""
        print("🚨 ACCIDENT DETECTED! Initiating emergency protocol...")

        location = self._get_emergency_location(sensor_data)
        vehicle_status = self._get_vehicle_status(sensor_data)

        # Send REAL emergency notifications
        emergency_thread = threading.Thread(
            target=self._send_emergency_notifications,
            args=(location, vehicle_status)
        )
        emergency_thread.daemon = True
        emergency_thread.start()

        self._log_emergency_incident(location, vehicle_status)
        self._activate_safety_measures()

    def _get_emergency_location(self, sensor_data):
        """Extract location information for emergency services"""
        gps_data = sensor_data.get('gps', {})

        return {
            'latitude': gps_data.get('latitude', 0),
            'longitude': gps_data.get('longitude', 0),
            'speed': gps_data.get('speed', 0),
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'address': gps_data.get('location', 'Unknown location')
        }

    def _get_vehicle_status(self, sensor_data):
        """Get current vehicle status"""
        return {
            'battery_level': sensor_data.get('battery', {}).get('charge_level', 0),
            'motor_temperature': sensor_data.get('motors', {}).get('temperature', 0),
            'camera_status': sensor_data.get('camera', {}).get('status', 'Unknown'),
            'obstacles_detected': sensor_data.get('lidar', {}).get('obstacles_detected', 0),
            'front_distance': sensor_data.get('ultrasonic', {}).get('front_distance', 0)
        }

    def _send_emergency_notifications(self, location, vehicle_status):
        """Send REAL emergency notifications"""
        current_time = time.time()

        if current_time - self.last_emergency_call < self.cooldown_period:
            print("⚠️ Emergency call cooldown active")
            return

        self.last_emergency_call = current_time

        # Send REAL email
        email_success = self._send_real_emergency_email(location, vehicle_status)

        # Simulate phone call (can be upgraded to real service)
        phone_success = self._simulate_emergency_call(location)

        if email_success:
            print("✅ REAL emergency email sent successfully!")
        else:
            print("❌ Failed to send emergency email")

    def _send_real_emergency_email(self, location, vehicle_status):
        """Send REAL emergency email using Gmail SMTP"""
        try:
            # Check if SMTP credentials are configured
            if (self.smtp_config['sender_email'] == 'your.email@gmail.com' or
                    self.smtp_config['sender_password'] == 'your_app_password'):
                print("❌ Please configure your Gmail SMTP credentials first!")
                print("   Update sender_email and sender_password in the code")
                return False

            # Create email message
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

            # Create MIME message
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config['sender_email']
            msg['To'] = self.emergency_contacts['email']
            msg['Subject'] = subject
            msg.attach(MIMEText(message, 'plain'))

            # Create secure SSL context
            context = ssl.create_default_context()

            # Connect to Gmail SMTP server and send email
            with smtplib.SMTP(self.smtp_config['server'], self.smtp_config['port']) as server:
                server.starttls(context=context)  # Secure the connection
                server.login(self.smtp_config['sender_email'], self.smtp_config['sender_password'])
                server.send_message(msg)

            print(f"✅ REAL EMAIL SENT SUCCESSFULLY!")
            print(f"   To: {self.emergency_contacts['email']}")
            print(f"   From: {self.smtp_config['sender_email']}")
            print(f"   Subject: {subject}")
            return True

        except smtplib.SMTPAuthenticationError:
            print("❌ SMTP Authentication Failed!")
            print("   Please check your:")
            print("   - Email address and password")
            print("   - Gmail 'App Passwords' configuration")
            print("   - Less secure app access settings")
            return False

        except smtplib.SMTPException as e:
            print(f"❌ SMTP Error: {e}")
            return False

        except Exception as e:
            print(f"❌ Failed to send emergency email: {e}")
            return False

    def _simulate_emergency_call(self, location):
        """Simulate phone call (can be upgraded to Twilio)"""
        try:
            print(f"📞 EMERGENCY CALL SIMULATION:")
            print(f"   To: {self.emergency_contacts['phone']}")
            print(f"   Message: 'ACCIDENT at {location['address']}'")
            print(f"   Google Maps: https://maps.google.com/?q={location['latitude']},{location['longitude']}")
            return True
        except Exception as e:
            print(f"❌ Emergency call simulation failed: {e}")
            return False

    def _activate_safety_measures(self):
        """Activate vehicle safety measures"""
        print("🛡️ Activating safety measures...")
        safety_actions = [
            "Stopping motors immediately",
            "Activating hazard lights",
            "Unlocking doors for emergency access",
            "Isolating high-voltage systems",
            "Activating emergency lighting",
            "Displaying emergency contact information"
        ]
        for action in safety_actions:
            print(f"   • {action}")
            time.sleep(0.3)

    def _log_emergency_incident(self, location, vehicle_status):
        """Log emergency incident"""
        incident_data = {
            'timestamp': datetime.now().isoformat(),
            'location': location,
            'vehicle_status': vehicle_status,
            'emergency_contacts_notified': self.emergency_contacts,
            'safety_measures_activated': True
        }

        try:
            with open('emergency_incidents.json', 'a') as f:
                f.write(json.dumps(incident_data) + '\n')
            print("📝 Emergency incident logged")
        except Exception as e:
            print(f"❌ Failed to log emergency incident: {e}")

    def manual_emergency_trigger(self, sensor_data):
        """Manual emergency trigger"""
        print("🚨 MANUAL EMERGENCY TRIGGERED!")
        location = self._get_emergency_location(sensor_data)
        vehicle_status = self._get_vehicle_status(sensor_data)
        self._send_emergency_notifications(location, vehicle_status)

    def configure_email(self, sender_email, sender_password):
        """Configure email settings"""
        self.smtp_config['sender_email'] = sender_email
        self.smtp_config['sender_password'] = sender_password
        print("✅ Email configuration updated!")


# Test with real email
def test_real_email_system():
    """Test the REAL email system"""
    print("🧪 Testing REAL Emergency Email System...")
    print("=" * 60)

    # Create emergency system
    emergency = EmergencyServices()

    # Configure YOUR Gmail credentials here:
    # REPLACE WITH YOUR ACTUAL GMAIL CREDENTIALS
    YOUR_GMAIL = "mohamedazizzouari2@gmail.com"  # CHANGE THIS
    YOUR_APP_PASSWORD = "ygheycdamelrivpz"  # CHANGE THIS

    emergency.configure_email(YOUR_GMAIL, YOUR_APP_PASSWORD)

    # Test sensor data
    test_sensor_data = {
        'imu': {
            'acceleration_x': 22.5,
            'acceleration_y': 18.3,
            'acceleration_z': 12.7,
            'gyro_x': 8.9,
            'gyro_y': 7.2,
            'gyro_z': 4.5
        },
        'gps': {
            'latitude': 36.8065,
            'longitude': 10.1815,
            'speed': 52.0,
            'location': 'Tunis, Tunisia - Test Location'
        },
        'battery': {'charge_level': 76},
        'motors': {'temperature': 67.0},
        'camera': {'status': 'TEST MODE'},
        'lidar': {'obstacles_detected': 2},
        'ultrasonic': {'front_distance': 1.2}
    }

    print(f"\n📧 Testing REAL email to: {emergency.emergency_contacts['email']}")
    print(f"📞 And phone call to: {emergency.emergency_contacts['phone']}")
    print("\n⚠️  This will send a REAL email to Mohamed Aziz!")

    # Countdown
    for i in range(5, 0, -1):
        print(f"   Sending in {i} seconds... (Press Ctrl+C to cancel)")
        time.sleep(1)

    print("\n🚨 SENDING REAL EMERGENCY NOTIFICATION...")

    # Trigger emergency
    emergency.trigger_emergency_protocol(test_sensor_data)

    print("\n" + "=" * 60)
    print("✅ Test completed! Check your email inbox.")


def setup_instructions():
    """Print setup instructions for Gmail configuration"""
    print("\n🔧 GMAIL SETUP INSTRUCTIONS:")
    print("=" * 50)
    print("1. Enable 2-Factor Authentication on your Gmail account")
    print("2. Generate an 'App Password':")
    print("   - Go to Google Account settings")
    print("   - Security → 2-Step Verification → App passwords")
    print("   - Generate password for 'Mail'")
    print("   - Use the 16-character password in the code")
    print("3. Update these lines in the code:")
    print("   YOUR_GMAIL = 'your.actual.email@gmail.com'")
    print("   YOUR_APP_PASSWORD = 'your_16_digit_app_password'")
    print("4. Test the system with test_real_email_system()")
    print("=" * 50)


if __name__ == "__main__":
    setup_instructions()

    # Uncomment the line below to test REAL email after configuration
    test_real_email_system()

    print("\n💡 To test REAL emails:")
    print("   1. Follow the setup instructions above")
    print("   2. Update the Gmail credentials in test_real_email_system()")
    print("   3. Uncomment 'test_real_email_system()' at the bottom")
    print("   4. Run the script again")
    exit(0)