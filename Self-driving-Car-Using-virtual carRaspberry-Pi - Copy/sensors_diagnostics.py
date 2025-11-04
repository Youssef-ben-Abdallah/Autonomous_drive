"""Backward compatible entry point for the sensor diagnostics demo."""

from autonomous_drive.diagnostics.sensors import SensorMonitor


def main() -> None:
    """Run a single update cycle of the sensor monitor for demonstration."""

    monitor = SensorMonitor()
    monitor.update_sensors()
    print(monitor.get_status_report())
    monitor.shutdown()


if __name__ == "__main__":
    main()
