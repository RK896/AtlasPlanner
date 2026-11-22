import logging

from rich.logging import RichHandler


def configure_logging(verbose: bool = False) -> None:
    """Send AtlasPlanner logs to the console; INFO with --verbose, else warnings only."""
    level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(
        level=logging.WARNING,
        format="%(message)s",
        handlers=[RichHandler(show_path=False, markup=False)],
    )
    logging.getLogger("atlas").setLevel(level)
