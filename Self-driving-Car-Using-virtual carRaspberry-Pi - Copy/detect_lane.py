"""Backward compatible entry point for lane navigation demo."""

from autonomous_drive.perception.lane_navigation import LaneNavigationSystem


def main() -> None:
    """Launch the lane navigation demo using the reorganised package."""

    LaneNavigationSystem().run()


if __name__ == "__main__":
    main()
