"""
Automated Parking Module
Handles autonomous parking maneuvers using ultrasonic sensors
"""

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    # Mock the GPIO library for non-Raspberry Pi systems
    class MockGPIO:
        BCM = OUT = IN = LOW = HIGH = None
        def setwarnings(self, *args, **kwargs): pass
        def setmode(self, *args, **kwargs): pass
        def setup(self, *args, **kwargs): pass
        def output(self, *args, **kwargs): pass
        def input(self, *args, **kwargs): return 0
        def cleanup(self, *args, **kwargs): pass
    GPIO = MockGPIO()

import time
from utils.logger import get_logger
from modules.control.motor_controller import MotorController
from config.gpio_config import GPIOConfig

logger = get_logger(__name__)

# Initialize GPIO and motor controller
config = GPIOConfig()
motor_controller = MotorController(config)

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# Setup LED indicator
GPIO.setup(config.LED_PIN, GPIO.OUT)
GPIO.output(config.LED_PIN, 1)

logger.info("🅿️ Parking module initialized")
time.sleep(5)

def measure_distance() -> float:
    """
    Measure distance using ultrasonic sensor.

    Returns:
        float: Distance in centimeters
    """
    try:
        GPIO.output(config.ULTRASONIC_TRIG, False)
        time.sleep(0.1)

        GPIO.output(config.ULTRASONIC_TRIG, True)
        time.sleep(0.00001)
        GPIO.output(config.ULTRASONIC_TRIG, False)

        while GPIO.input(config.ULTRASONIC_ECHO) == 0:
            GPIO.output(config.LED_PIN, False)
        pulse_start = time.time()

        while GPIO.input(config.ULTRASONIC_ECHO) == 1:
            GPIO.output(config.LED_PIN, False)
        pulse_end = time.time()
        pulse_duration = pulse_end - pulse_start

        distance = pulse_duration * 17150
        distance = round(distance, 2)
        return distance
    except Exception as e:
        logger.error(f"Distance measurement failed: {e}", exc_info=True)
        return 0.0

def perform_parking_maneuver() -> None:
    """
    Perform automated parking maneuver.
    Detects parking space and executes parking sequence.
    """
    try:
        parking_detected = False
        motor_controller.forward()

        while True:
            if parking_detected:
                motor_controller.stop()

                # Turn left
                now = time.time()
                while time.time() <= now + 1.2:
                    motor_controller.left()
                motor_controller.stop()

                # Back up
                now = time.time()
                while time.time() <= now + 0.7:
                    motor_controller.backward()

                logger.info('🅿️ Parking complete!')
                motor_controller.stop()
                break

            distance = measure_distance()

            if distance > 30:
                now = time.time()
                while time.time() <= now + 0.3:
                    distance = measure_distance()
                    logger.info(f"📏 Distance: {distance} cm")
                    if distance < 30:
                        parking_detected = False
                        break
                    parking_detected = True

    except Exception as e:
        logger.error(f"Parking maneuver failed: {e}", exc_info=True)
        motor_controller.stop()
    finally:
        motor_controller.cleanup()
        GPIO.cleanup()


if __name__ == "__main__":
    try:
        perform_parking_maneuver()
    except KeyboardInterrupt:
        logger.info("Parking interrupted by user")
        motor_controller.stop()
        motor_controller.cleanup()
        GPIO.cleanup()
    except Exception as e:
        logger.error(f"Parking system error: {e}", exc_info=True)
        motor_controller.stop()
        motor_controller.cleanup()
        GPIO.cleanup()
