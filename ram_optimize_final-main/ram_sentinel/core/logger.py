from rich.console import Console
from rich.logging import RichHandler
import logging
from .config import settings

def setup_logger():
    logging.basicConfig(
        level="DEBUG" if settings.DEBUG_MODE else "INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    return logging.getLogger("ram_sentinel")

console = Console()
logger = setup_logger()
