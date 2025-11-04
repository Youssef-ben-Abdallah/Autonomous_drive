"""Automated parking helper built around ultrasonic distance measurements."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable

from autonomous_drive.control.motor_controller import MotorController
from autonomous_drive.config.gpio_config import GPIOConfig
from autonomous_drive.utils.logger import get_logger

try:  # pragma: no cover - mocked during tests
    import RPi.GPIO as GPIO  # type: ignore
except (ImportError, RuntimeError):  # pragma: no cover - running off-device
    class MockGPIO:
        BCM = OUT = IN = LOW = HIGH = None

        def setwarnings(self, *_, **__):
            pass

        def setmode(self, *_, **__):
            pass

        def setup(self, *_, **__):
            pass

        def output(self, *_, **__):
            pass

        def input(self, *_, **__):
            return 0

        def cleanup(self, *_, **__):
            pass

    GPIO = MockGPIO()

logger = get_logger(__name__)


@dataclass
class ParkingConfig:
    ultrasonic_trigger: int
    ultrasonic_echo: int
    indicator_pin: int
    detection_threshold_cm: float = 30.0
    confirm_duration_s: float = 1.0

    @classmethod
    def from_gpio(cls, config: GPIOConfig) -> "ParkingConfig":
        return cls(
            ultrasonic_trigger=config.ULTRASONIC_TRIG,
            ultrasonic_echo=config.ULTRASONIC_ECHO,
            indicator_pin=config.LED_PIN,
        )


class ParkingAssistant:
    """Encapsulates the original parking loop with additional documentation."""

    def __init__(self, motor_controller: MotorController | None = None, config: ParkingConfig | None = None) -> None:
        self.motor_controller = motor_controller or MotorController()
        self.gpio_config = config or ParkingConfig.from_gpio(GPIOConfig())
        self._setup_gpio()

    def _setup_gpio(self) -> None:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.gpio_config.ultrasonic_trigger, GPIO.OUT)
        GPIO.setup(self.gpio_config.ultrasonic_echo, GPIO.IN)
        GPIO.setup(self.gpio_config.indicator_pin, GPIO.OUT)
        GPIO.output(self.gpio_config.indicator_pin, 1)
        logger.info("🅿️ Parking assistant initialised")

    def measure_distance(self) -> float:
        """Return the current ultrasonic sensor distance in centimetres."""

        try:
            GPIO.output(self.gpio_config.ultrasonic_trigger, False)
            time.sleep(0.1)
            GPIO.output(self.gpio_config.ultrasonic_trigger, True)
            time.sleep(0.00001)
            GPIO.output(self.gpio_config.ultrasonic_trigger, False)

            while GPIO.input(self.gpio_config.ultrasonic_echo) == 0:
                GPIO.output(self.gpio_config.indicator_pin, False)
            pulse_start = time.time()

            while GPIO.input(self.gpio_config.ultrasonic_echo) == 1:
                GPIO.output(self.gpio_config.indicator_pin, False)
            pulse_end = time.time()

            pulse_duration = pulse_end - pulse_start
            distance = round(pulse_duration * 17150, 2)
            return distance
        except Exception as exc:  # pragma: no cover - hardware errors
            logger.error("Distance measurement failed: %s", exc, exc_info=True)
            return 0.0

    def perform_parking_manoeuvre(self) -> None:
        logger.info("Starting parking manoeuvre")
        parking_detected = False
        self.motor_controller.forward()

        try:
            while True:
                if parking_detected:
                    self.motor_controller.stop()
                    self._turn_left(duration=1.2)
                    self._reverse(duration=0.7)
                    logger.info("🅿️ Parking complete!")
                    break

                distance = self.measure_distance()
                if distance > self.gpio_config.detection_threshold_cm:
                    start = time.time()
                    while time.time() <= start + self.gpio_config.confirm_duration_s:
                        distance = self.measure_distance()
                        logger.info("📏 Distance: %s cm", distance)
                        if distance < self.gpio_config.detection_threshold_cm:
                            parking_detected = False
                            break
                        parking_detected = True
        except KeyboardInterrupt:
            logger.info("Parking interrupted by user")
        except Exception as exc:  # pragma: no cover - hardware errors
            logger.error("Parking manoeuvre failed: %s", exc, exc_info=True)
        finally:
            self.motor_controller.stop()
            self.motor_controller.cleanup()
            GPIO.cleanup()

    def _turn_left(self, duration: float) -> None:
        self._execute_for_duration(self.motor_controller.left, duration)

    def _reverse(self, duration: float) -> None:
        self._execute_for_duration(self.motor_controller.backward, duration)

    def _execute_for_duration(self, action: Callable[[], None], duration: float) -> None:
        start = time.time()
        while time.time() <= start + duration:
            action()
        self.motor_controller.stop()


__all__ = ["ParkingAssistant", "ParkingConfig"]
