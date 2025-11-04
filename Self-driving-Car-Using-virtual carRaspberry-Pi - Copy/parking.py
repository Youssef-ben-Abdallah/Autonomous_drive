"""Backward compatible entry point for the automated parking demo."""

from autonomous_drive.planning.parking import ParkingAssistant


def main() -> None:
    """Launch the parking assistant using the reorganised package."""

    ParkingAssistant().perform_parking_manoeuvre()


if __name__ == "__main__":
    main()
