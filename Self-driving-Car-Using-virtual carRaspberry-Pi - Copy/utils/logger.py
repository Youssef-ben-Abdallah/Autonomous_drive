"""Legacy shim forwarding to :mod:`autonomous_drive.utils.logger`."""

from autonomous_drive.utils.logger import VehicleLogger, get_logger

__all__ = ["VehicleLogger", "get_logger"]
