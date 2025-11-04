"""
Motor Controller Module
Centralized motor control for the autonomous vehicle
"""

try:
    import RPi.GPIO as GPIO
except (ImportError, RuntimeError):
    # Mock GPIO for non-Raspberry Pi systems
    class MockGPIO:
        BCM = OUT = IN = LOW = HIGH = None
        
        def setwarnings(self, *args, **kwargs):
            pass
        
        def setmode(self, *args, **kwargs):
            pass
        
        def setup(self, *args, **kwargs):
            pass
        
        def output(self, *args, **kwargs):
            pass
        
        def input(self, *args, **kwargs):
            return 0
        
        def cleanup(self, *args, **kwargs):
            pass
    
    GPIO = MockGPIO()

from typing import Optional, Dict
from config.gpio_config import GPIOConfig
from utils.logger import get_logger
from utils.validators import Validator, ValidationError


class MotorController:
    """
    Centralized motor control class.
    Consolidates all motor operations into a single, reusable interface.
    """
    
    def __init__(self, config: GPIOConfig = None):
        """
        Initialize the motor controller.
        
        Args:
            config (GPIOConfig): GPIO configuration object
        """
        self.config = config or GPIOConfig()
        self.logger = get_logger(__name__)
        self.last_action = "STOP"
        self.current_speed = 0
        
        self._setup_gpio()
    
    def _setup_gpio(self):
        """Setup GPIO pins for motor control."""
        try:
            GPIO.setwarnings(False)
            GPIO.setmode(GPIO.BCM)
            
            # Setup output pins
            for pin in self.config.get_output_pins():
                GPIO.setup(pin, GPIO.OUT)
            
            # Setup input pins
            for pin in self.config.get_input_pins():
                GPIO.setup(pin, GPIO.IN)
            
            self.logger.info("GPIO setup completed successfully")
        except Exception as e:
            self.logger.error(f"GPIO setup failed: {e}")
    
    def forward(self, speed: int = 30) -> None:
        """
        Move the vehicle forward.

        Args:
            speed (int): Speed in km/h (0-100)

        Raises:
            ValidationError: If speed is invalid
        """
        try:
            Validator.validate_speed(speed, 0, 100)

            GPIO.output(self.config.MOTOR_LEFT_FORWARD, 1)
            GPIO.output(self.config.MOTOR_LEFT_BACKWARD, 0)
            GPIO.output(self.config.MOTOR_RIGHT_FORWARD, 1)
            GPIO.output(self.config.MOTOR_RIGHT_BACKWARD, 0)

            self.last_action = "FORWARD"
            self.current_speed = speed
            self.logger.info(f"🚗 Moving forward at {speed} km/h")
        except ValidationError as e:
            self.logger.error(f"Invalid speed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Forward motion failed: {e}")
    
    def backward(self, speed: int = 20) -> None:
        """
        Move the vehicle backward.
        
        Args:
            speed (int): Speed in km/h (0-100)
        """
        try:
            GPIO.output(self.config.MOTOR_LEFT_FORWARD, 0)
            GPIO.output(self.config.MOTOR_LEFT_BACKWARD, 1)
            GPIO.output(self.config.MOTOR_RIGHT_FORWARD, 0)
            GPIO.output(self.config.MOTOR_RIGHT_BACKWARD, 1)
            
            self.last_action = "BACKWARD"
            self.current_speed = speed
            self.logger.info(f"🔙 Moving backward at {speed} km/h")
        except Exception as e:
            self.logger.error(f"Backward motion failed: {e}")
    
    def left(self, speed: int = 20) -> None:
        """
        Turn the vehicle left.
        
        Args:
            speed (int): Speed in km/h (0-100)
        """
        try:
            GPIO.output(self.config.MOTOR_LEFT_FORWARD, 0)
            GPIO.output(self.config.MOTOR_LEFT_BACKWARD, 0)
            GPIO.output(self.config.MOTOR_RIGHT_FORWARD, 1)
            GPIO.output(self.config.MOTOR_RIGHT_BACKWARD, 0)
            
            self.last_action = "LEFT"
            self.current_speed = speed
            self.logger.info(f"↪️ Turning left at {speed} km/h")
        except Exception as e:
            self.logger.error(f"Left turn failed: {e}")
    
    def right(self, speed: int = 20) -> None:
        """
        Turn the vehicle right.
        
        Args:
            speed (int): Speed in km/h (0-100)
        """
        try:
            GPIO.output(self.config.MOTOR_LEFT_FORWARD, 1)
            GPIO.output(self.config.MOTOR_LEFT_BACKWARD, 0)
            GPIO.output(self.config.MOTOR_RIGHT_FORWARD, 0)
            GPIO.output(self.config.MOTOR_RIGHT_BACKWARD, 0)
            
            self.last_action = "RIGHT"
            self.current_speed = speed
            self.logger.info(f"↩️ Turning right at {speed} km/h")
        except Exception as e:
            self.logger.error(f"Right turn failed: {e}")
    
    def stop(self) -> None:
        """Stop all motors immediately."""
        try:
            GPIO.output(self.config.MOTOR_LEFT_FORWARD, 0)
            GPIO.output(self.config.MOTOR_LEFT_BACKWARD, 0)
            GPIO.output(self.config.MOTOR_RIGHT_FORWARD, 0)
            GPIO.output(self.config.MOTOR_RIGHT_BACKWARD, 0)
            
            self.last_action = "STOP"
            self.current_speed = 0
            self.logger.info("🛑 All motors stopped")
        except Exception as e:
            self.logger.error(f"Stop operation failed: {e}")
    
    def cleanup(self) -> None:
        """Clean up GPIO resources."""
        try:
            self.stop()
            GPIO.cleanup()
            self.logger.info("GPIO cleanup completed")
        except Exception as e:
            self.logger.error(f"GPIO cleanup failed: {e}")
    
    def get_status(self) -> dict:
        """
        Get current motor status.
        
        Returns:
            dict: Current action and speed
        """
        return {
            'action': self.last_action,
            'speed': self.current_speed
        }

