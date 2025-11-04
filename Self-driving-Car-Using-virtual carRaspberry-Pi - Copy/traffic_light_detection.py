"""Backward compatible entry point for the traffic light monitor demo."""

from autonomous_drive.perception.traffic_light_monitor import TrafficLightMonitor


def main() -> None:
    """Launch the traffic light detection demo using the reorganised package."""

    TrafficLightMonitor().run()


if __name__ == "__main__":
    main()
