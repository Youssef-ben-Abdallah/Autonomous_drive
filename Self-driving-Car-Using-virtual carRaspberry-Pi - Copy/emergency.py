"""Backward compatible entry point for the emergency services module."""

from autonomous_drive.safety.emergency import EmergencyServices


def main() -> None:
    """Demonstrate accident detection using simulated sensor data."""

    services = EmergencyServices()
    sample_data = {
        "imu": {
            "acceleration_x": 12.0,
            "acceleration_y": 3.5,
            "acceleration_z": 5.0,
            "gyro_x": 2.0,
            "gyro_y": 1.0,
            "gyro_z": 0.5,
        },
        "gps": {"speed": 2.0, "latitude": 0.0, "longitude": 0.0, "location": "Simulated"},
    }
    services.detect_accident(sample_data)


if __name__ == "__main__":
    main()
