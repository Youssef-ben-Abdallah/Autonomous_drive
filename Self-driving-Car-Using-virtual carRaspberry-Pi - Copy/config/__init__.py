"""Legacy configuration namespace forwarding to ``autonomous_drive.config``."""

from autonomous_drive.config import ConfigLoader, GPIOConfig, config, gpio_config

__all__ = ["ConfigLoader", "GPIOConfig", "config", "gpio_config"]
