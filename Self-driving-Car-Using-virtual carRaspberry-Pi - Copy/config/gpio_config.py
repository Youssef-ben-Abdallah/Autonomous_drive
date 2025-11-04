"""Legacy shim forwarding to :mod:`autonomous_drive.config.gpio_config`."""

from autonomous_drive.config.gpio_config import GPIOConfig, gpio_config

__all__ = ["GPIOConfig", "gpio_config"]
