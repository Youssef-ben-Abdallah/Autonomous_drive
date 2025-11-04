"""Autonomous vehicle prototype modules."""

from .perception import LaneNavigationSystem, ObjectPerceptionSystem, TrafficLightMonitor
from .control.motor_controller import MotorController

__all__ = [
    "LaneNavigationSystem",
    "ObjectPerceptionSystem",
    "TrafficLightMonitor",
    "MotorController",
]
