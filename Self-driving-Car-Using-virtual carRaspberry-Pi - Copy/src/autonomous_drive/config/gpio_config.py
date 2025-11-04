"""
GPIO Configuration Module
Centralized GPIO pin definitions for Raspberry Pi
"""

from dataclasses import dataclass


@dataclass
class GPIOConfig:
    """
    Centralized GPIO pin configuration for the autonomous vehicle.
    All GPIO pins are defined here to avoid duplication and make reconfiguration easy.
    """
    
    # Ultrasonic Sensor Pins (HC-SR04)
    ULTRASONIC_TRIG: int = 17  # Trigger pin
    ULTRASONIC_ECHO: int = 27  # Echo pin
    
    # LED Indicator Pin
    LED_PIN: int = 22
    
    # Motor Control Pins (L293D Motor Driver)
    # Left Motor
    MOTOR_LEFT_FORWARD: int = 16
    MOTOR_LEFT_BACKWARD: int = 12
    
    # Right Motor
    MOTOR_RIGHT_FORWARD: int = 21
    MOTOR_RIGHT_BACKWARD: int = 20
    
    # PWM Pins (for speed control, if using PWM)
    PWM_FREQUENCY: int = 1000  # 1kHz
    
    @classmethod
    def get_all_pins(cls) -> dict:
        """
        Get all GPIO pins as a dictionary.
        
        Returns:
            dict: Dictionary of all GPIO pins with their purposes
        """
        return {
            'ultrasonic_trig': cls.ULTRASONIC_TRIG,
            'ultrasonic_echo': cls.ULTRASONIC_ECHO,
            'led': cls.LED_PIN,
            'motor_left_forward': cls.MOTOR_LEFT_FORWARD,
            'motor_left_backward': cls.MOTOR_LEFT_BACKWARD,
            'motor_right_forward': cls.MOTOR_RIGHT_FORWARD,
            'motor_right_backward': cls.MOTOR_RIGHT_BACKWARD,
        }
    
    @classmethod
    def get_output_pins(cls) -> list:
        """
        Get all output pins (pins that need to be set as GPIO.OUT).
        
        Returns:
            list: List of output pin numbers
        """
        return [
            cls.ULTRASONIC_TRIG,
            cls.LED_PIN,
            cls.MOTOR_LEFT_FORWARD,
            cls.MOTOR_LEFT_BACKWARD,
            cls.MOTOR_RIGHT_FORWARD,
            cls.MOTOR_RIGHT_BACKWARD,
        ]
    
    @classmethod
    def get_input_pins(cls) -> list:
        """
        Get all input pins (pins that need to be set as GPIO.IN).
        
        Returns:
            list: List of input pin numbers
        """
        return [cls.ULTRASONIC_ECHO]


# Create a singleton instance for easy import
gpio_config = GPIOConfig()

