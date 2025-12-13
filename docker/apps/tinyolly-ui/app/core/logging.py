"""Logging configuration"""

import logging
import sys
import os

from ..config import settings


def setup_logging():
    """Configure logging with stdout handler"""
    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout
        ]
    )


logger = logging.getLogger(__name__)
