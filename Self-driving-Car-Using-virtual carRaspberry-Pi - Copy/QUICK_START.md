# Quick Start Guide

## Getting Started with the Enhanced Autonomous Vehicle Project

### Prerequisites
- Python 3.7+
- Raspberry Pi (optional, for hardware)
- pip package manager

---

## Installation (5 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Environment
```bash
# Create .env file with your settings
cp .env .env.local

# Edit .env.local with your Gmail credentials
# GMAIL_ADDRESS=your_email@gmail.com
# GMAIL_PASSWORD=your_app_password
```

### Step 3: Create Logs Directory
```bash
mkdir -p logs
```

### Step 4: Verify Installation
```bash
python -c "from utils.logger import get_logger; logger = get_logger('test'); logger.info('✅ Setup complete!')"
```

---

## Basic Usage

### 1. Using the Logger
```python
from utils.logger import get_logger

logger = get_logger(__name__)
logger.info("Application started")
logger.warning("This is a warning")
logger.error("An error occurred")
```

### 2. Using Configuration
```python
from config import config

# Get values
max_speed = config.get("vehicle.max_speed", 50)
confidence = config.get("vision.object_detection.confidence_threshold", 0.5)

# Set values
config.set("vehicle.max_speed", 60)

# Get all configuration
all_config = config.get_all()
```

### 3. Using Motor Controller
```python
from modules.control import MotorController

motor = MotorController()

# Move forward
motor.forward(speed=30)

# Turn left
motor.left(speed=20)

# Stop
motor.stop()

# Get status
status = motor.get_status()
print(f"Current action: {status['action']}, Speed: {status['speed']}")

# Cleanup
motor.cleanup()
```

### 4. Using Validators
```python
from utils import Validator, ValidationError

try:
    Validator.validate_speed(50)
    Validator.validate_gpio_pin(17)
    Validator.validate_confidence(0.85)
    print("✅ All validations passed")
except ValidationError as e:
    print(f"❌ Validation failed: {e}")
```

### 5. Using Emergency Services
```python
from emergency import EmergencyServices

emergency = EmergencyServices()

# Simulate sensor data
sensor_data = {
    'imu': {
        'acceleration_x': 0,
        'acceleration_y': 0,
        'acceleration_z': 9.8,
        'gyro_x': 0,
        'gyro_y': 0,
        'gyro_z': 0
    },
    'gps': {
        'speed': 30,
        'latitude': 0,
        'longitude': 0
    }
}

# Detect accident
if emergency.detect_accident(sensor_data):
    print("🚨 Accident detected!")
```

---

## Configuration Files

### .env File
```bash
# Gmail Configuration
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_PASSWORD=your_app_password

# Emergency Contact
EMERGENCY_EMAIL=emergency@example.com
EMERGENCY_PHONE=+1234567890

# Vehicle Settings
VEHICLE_MAX_SPEED=50
VEHICLE_MIN_DISTANCE_THRESHOLD=0.3

# Safety Thresholds
ACCELERATION_THRESHOLD=8.0
IMPACT_THRESHOLD=15.0
ROLLOVER_THRESHOLD=6.0
```

### config/config.yaml
```yaml
vehicle:
  max_speed: 50
  min_distance_threshold: 0.3

vision:
  lane_detection:
    enabled: true
    interval: 5
  object_detection:
    enabled: true
    confidence_threshold: 0.5

sensors:
  ultrasonic:
    enabled: true
    timeout: 1.0

motors:
  speeds:
    forward: 30
    backward: 20
    turn: 20

safety:
  emergency:
    acceleration_threshold: 8.0
    impact_threshold: 15.0
```

---

## Common Tasks

### Task 1: Run Lane Detection
```python
from detect_lane import FastYOLONavigation

try:
    nav = FastYOLONavigation()
    # Use navigation system
except Exception as e:
    print(f"Error: {e}")
```

### Task 2: Detect Obstacles
```python
from obstacle_detection import *
import cv2

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Process frame
    results = model.predict(frame)
    
    # Handle detections
    if results:
        forward()
    else:
        stop()
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### Task 3: Perform Parking
```python
from parking import perform_parking_maneuver

try:
    perform_parking_maneuver()
except KeyboardInterrupt:
    print("Parking interrupted")
```

### Task 4: Monitor Sensors
```python
from sensors_diagnostics import CameraMonitor

monitor = CameraMonitor()
monitor.start_monitoring()
```

---

## Troubleshooting

### Issue: "Module not found" error
**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: GPIO errors on non-Raspberry Pi
**Solution**: GPIO is automatically mocked for non-RPi systems
```python
# This will work on any system
from modules.control import MotorController
motor = MotorController()  # Uses mock GPIO
```

### Issue: Configuration file not found
**Solution**: Create config/config.yaml
```bash
# The system will use defaults if file is missing
# Create the file for custom configuration
```

### Issue: Logging not working
**Solution**: Create logs directory
```bash
mkdir -p logs
```

### Issue: Email not sending
**Solution**: Check .env file
```bash
# Verify GMAIL_ADDRESS and GMAIL_PASSWORD are set
# Use Gmail App Password, not regular password
# Enable 2-Factor Authentication on Gmail
```

---

## File Structure

```
project/
├── .env                          # Environment variables
├── requirements.txt              # Dependencies
├── config/
│   ├── config.yaml              # YAML configuration
│   ├── gpio_config.py           # GPIO pins
│   └── config_loader.py         # Config loader
├── utils/
│   ├── logger.py                # Logging
│   └── validators.py            # Validation
├── modules/
│   └── control/
│       └── motor_controller.py  # Motor control
├── logs/                        # Log files
├── detect_lane.py               # Lane detection
├── obstacle_detection.py        # Obstacle detection
├── traffic_light_detection.py   # Traffic lights
├── parking.py                   # Parking
├── emergency.py                 # Emergency services
└── sensors_diagnostics.py       # Sensor monitoring
```

---

## Next Steps

1. **Read Documentation**
   - `IMPLEMENTATION_SUMMARY.md` - Overview
   - `PHASE_1_COMPLETION.md` - Foundation details
   - `PHASE_2_COMPLETION.md` - Quality improvements

2. **Explore Code**
   - Check `config/config.yaml` for configuration options
   - Review `utils/validators.py` for validation examples
   - Study `modules/control/motor_controller.py` for motor control

3. **Run Examples**
   - Test motor controller
   - Test configuration loading
   - Test validators
   - Test logging

4. **Customize**
   - Edit `.env` with your settings
   - Modify `config/config.yaml` for your needs
   - Add custom validators if needed

---

## Support

### Documentation
- `QUICK_START.md` - This file
- `IMPLEMENTATION_SUMMARY.md` - Project overview
- `PHASE_1_COMPLETION.md` - Phase 1 details
- `PHASE_2_COMPLETION.md` - Phase 2 details

### Code Examples
- Check docstrings in each module
- Review type hints for function signatures
- Look at validation examples in `utils/validators.py`

### Logging
- Logs are saved to `logs/vehicle_YYYYMMDD.log`
- Console output shows INFO level and above
- File output includes DEBUG level and above

---

## Tips & Tricks

### Tip 1: Use Configuration for Easy Changes
```python
# Instead of hardcoding values
speed = config.get("motors.speeds.forward", 30)
```

### Tip 2: Always Validate Input
```python
# Validate before using
try:
    Validator.validate_speed(user_input)
except ValidationError as e:
    logger.error(f"Invalid input: {e}")
```

### Tip 3: Use Logger Instead of Print
```python
# Good
logger.info("Motor started")

# Avoid
print("Motor started")
```

### Tip 4: Handle Exceptions Gracefully
```python
try:
    motor.forward()
except Exception as e:
    logger.error(f"Motor error: {e}", exc_info=True)
    motor.stop()
```

---

**Happy coding! 🚗**

