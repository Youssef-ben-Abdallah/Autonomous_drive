"""Simplified traffic light colour detection using OpenCV heuristics.

This module is a tidied version of the legacy ``traffic_light_detection.py``
script.  It keeps the colour thresholds and control flow intact but organises the
code into a reusable :class:`TrafficLightMonitor` class with clear documentation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import cv2
import numpy as np

from autonomous_drive.control.motor_controller import MotorController
from autonomous_drive.utils.logger import get_logger

try:  # pragma: no cover - GPIO is not available in CI
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

        def cleanup(self, *_, **__):
            pass

    GPIO = MockGPIO()


logger = get_logger(__name__)


@dataclass(frozen=True)
class TrafficLightConfig:
    """GPIO pin configuration for the simple traffic light monitor."""

    TRIG: int = 17
    ECHO: int = 27
    LED: int = 22
    M11: int = 16
    M12: int = 12
    M21: int = 21
    M22: int = 20


class TrafficLightMonitor:
    """Detect red/green lights and proxy basic driving commands."""

    def __init__(self, config: TrafficLightConfig | None = None) -> None:
        self.config = config or TrafficLightConfig()
        self.motor_controller = MotorController()
        self._setup_gpio()

    # ------------------------------------------------------------------
    # GPIO helpers
    # ------------------------------------------------------------------

    def _setup_gpio(self) -> None:
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)

        GPIO.setup(self.config.TRIG, GPIO.OUT)
        GPIO.setup(self.config.ECHO, GPIO.IN)
        GPIO.setup(self.config.LED, GPIO.OUT)

        for pin in (self.config.M11, self.config.M12, self.config.M21, self.config.M22):
            GPIO.setup(pin, GPIO.OUT)

        logger.info("Traffic light monitor GPIO initialised")

    # ------------------------------------------------------------------
    # Motor proxies
    # ------------------------------------------------------------------

    def stop(self) -> None:
        logger.info("🛑 Stopping motors")
        self.motor_controller.stop()

    def forward(self) -> None:
        logger.info("🚗 Moving forward")
        self.motor_controller.forward()

    # ------------------------------------------------------------------
    # Computer vision helpers
    # ------------------------------------------------------------------

    def _extract_regions(self, frame: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        red_lower = np.array([136, 87, 111], np.uint8)
        red_upper = np.array([180, 255, 255], np.uint8)
        green_lower = np.array([66, 122, 129], np.uint8)
        green_upper = np.array([86, 255, 255], np.uint8)

        red_mask = cv2.inRange(hsv, red_lower, red_upper)
        green_mask = cv2.inRange(hsv, green_lower, green_upper)

        kernel = np.ones((5, 5), "uint8")
        red_mask = cv2.dilate(red_mask, kernel)
        green_mask = cv2.dilate(green_mask, kernel)

        red_result = cv2.bitwise_and(frame, frame, mask=red_mask)
        green_result = cv2.bitwise_and(frame, frame, mask=green_mask)
        return red_mask, green_mask, red_result, green_result

    def _handle_light(self, mask: np.ndarray, colour: str) -> bool:
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        for contour in contours:
            area = cv2.contourArea(contour)
            if area <= 300:
                continue

            x, y, w, h = cv2.boundingRect(contour)
            colour_bgr = (0, 0, 255) if colour == "RED" else (0, 255, 0)
            label = "RED" if colour == "RED" else "GREEN"
            logger.info("%s light detected", label)
            cv2.rectangle(self.current_frame, (x, y), (x + w, y + h), colour_bgr, 2)
            cv2.putText(self.current_frame, f"{label} light", (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, colour_bgr, 2)
            if colour == "RED":
                self.stop()
            else:
                self.forward()
            return True
        return False

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self, camera_index: int = 0) -> None:
        cap = cv2.VideoCapture(camera_index)
        self.forward()

        try:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                self.current_frame = frame[30:2000, 500:700]
                red_mask, green_mask, _, _ = self._extract_regions(self.current_frame)

                red_seen = self._handle_light(red_mask, "RED")
                green_seen = self._handle_light(green_mask, "GREEN")

                cv2.imshow("Traffic Light Monitor", self.current_frame)
                if cv2.waitKey(100) & 0xFF == ord("q"):
                    break

                if red_seen:
                    GPIO.output(self.config.LED, 0)
                elif green_seen:
                    GPIO.output(self.config.LED, 1)
        finally:
            GPIO.cleanup()
            cap.release()
            cv2.destroyAllWindows()


__all__ = ["TrafficLightMonitor", "TrafficLightConfig"]
