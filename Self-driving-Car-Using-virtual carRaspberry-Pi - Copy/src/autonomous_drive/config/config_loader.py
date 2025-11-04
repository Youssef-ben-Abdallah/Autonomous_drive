"""
Configuration Loader Module
Loads and manages YAML configuration files
"""

import os
from typing import Any, Dict

import yaml

from autonomous_drive.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigLoader:
    """
    Loads and manages YAML configuration files.
    Provides easy access to configuration values with defaults.
    """
    
    _instance = None
    _config = {}
    
    def __new__(cls):
        """Singleton pattern - only one instance."""
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize configuration loader."""
        if not self._config:
            self.load_config()
    
    def load_config(self, config_file: str = "config/config.yaml") -> None:
        """
        Load configuration from YAML file.
        
        Args:
            config_file (str): Path to configuration file
        
        Raises:
            FileNotFoundError: If config file not found
            yaml.YAMLError: If YAML parsing fails
        """
        try:
            if not os.path.exists(config_file):
                logger.warning(f"Config file not found: {config_file}")
                logger.info("Using default configuration")
                self._config = self._get_default_config()
                return
            
            with open(config_file, 'r') as f:
                self._config = yaml.safe_load(f)
            
            logger.info(f"✅ Configuration loaded from {config_file}")
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}", exc_info=True)
            self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}", exc_info=True)
            self._config = self._get_default_config()
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key (str): Configuration key (e.g., "vehicle.max_speed")
            default (Any): Default value if key not found
        
        Returns:
            Any: Configuration value or default
        
        Example:
            >>> config = ConfigLoader()
            >>> max_speed = config.get("vehicle.max_speed", 50)
        """
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                    if value is None:
                        return default
                else:
                    return default
            
            return value if value is not None else default
        except Exception as e:
            logger.warning(f"Error getting config key '{key}': {e}")
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value using dot notation.
        
        Args:
            key (str): Configuration key (e.g., "vehicle.max_speed")
            value (Any): Value to set
        
        Example:
            >>> config = ConfigLoader()
            >>> config.set("vehicle.max_speed", 60)
        """
        try:
            keys = key.split('.')
            config = self._config
            
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            config[keys[-1]] = value
            logger.debug(f"Configuration updated: {key} = {value}")
        except Exception as e:
            logger.error(f"Error setting config key '{key}': {e}", exc_info=True)
    
    def get_all(self) -> Dict[str, Any]:
        """
        Get entire configuration dictionary.
        
        Returns:
            Dict: Complete configuration
        """
        return self._config.copy()
    
    def reload(self, config_file: str = "config/config.yaml") -> None:
        """
        Reload configuration from file.
        
        Args:
            config_file (str): Path to configuration file
        """
        logger.info(f"Reloading configuration from {config_file}")
        self._config = {}
        self.load_config(config_file)
    
    @staticmethod
    def _get_default_config() -> Dict[str, Any]:
        """
        Get default configuration.
        
        Returns:
            Dict: Default configuration values
        """
        return {
            'vehicle': {
                'max_speed': 50,
                'min_distance_threshold': 0.3,
                'emergency_stop_distance': 0.2
            },
            'vision': {
                'lane_detection': {'enabled': True, 'interval': 5},
                'object_detection': {'enabled': True, 'confidence_threshold': 0.5},
                'traffic_light': {'enabled': True}
            },
            'sensors': {
                'ultrasonic': {'enabled': True, 'timeout': 1.0},
                'camera': {'enabled': True}
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/vehicle.log'
            },
            'safety': {
                'emergency': {
                    'acceleration_threshold': 8.0,
                    'impact_threshold': 15.0,
                    'rollover_threshold': 6.0
                }
            }
        }


# Create singleton instance
config = ConfigLoader()

