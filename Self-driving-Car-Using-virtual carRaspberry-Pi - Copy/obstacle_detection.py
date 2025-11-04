"""Backward compatible entry point for the object perception demo."""

from autonomous_drive.perception.obstacle_detection import ObjectPerceptionSystem


def main() -> None:
    """Launch the perception demo using the reorganised package."""

    ObjectPerceptionSystem().run()


if __name__ == "__main__":
    main()
