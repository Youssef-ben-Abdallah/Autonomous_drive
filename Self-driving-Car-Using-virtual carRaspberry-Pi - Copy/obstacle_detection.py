"""Backward compatible entry point for the object perception demo."""

from pathlib import Path
import sys


def _ensure_src_on_path() -> None:
    """Add the repository's ``src`` directory to ``sys.path`` if needed."""

    project_root = Path(__file__).resolve().parent
    src_dir = project_root / "src"

    for path in (project_root, src_dir):
        if path.exists():
            str_path = str(path)
            if str_path not in sys.path:
                sys.path.insert(0, str_path)


_ensure_src_on_path()

from autonomous_drive.perception.obstacle_detection import ObjectPerceptionSystem


def main() -> None:
    """Launch the perception demo using the reorganised package."""

    ObjectPerceptionSystem().run()


if __name__ == "__main__":
    main()
