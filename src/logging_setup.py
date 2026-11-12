"""Logging of the bot: JSON lines with masked secrets.

Importing this module configures logging. src/variables.py imports it first, because it logs while it reads
the config, and registers the secrets in `masker` before its first log line.
"""

import logging
import os
import sys
from typing import IO

import structlog
from logmask import SecretsMasker, mask_secrets_processor, setup_logging

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def configure_logging(level: str, stream: IO[str] | None = None) -> SecretsMasker:
    levels = logging.getLevelNamesMapping()
    numeric_level = levels.get(level)
    if numeric_level is None:
        raise ValueError(f"LOG_LEVEL must be one of: {', '.join(levels)}.")

    # structlog does not route the standard-library loggers of web3, urllib3 and requests,
    # so the root logger gets the same stream and the same masker.
    masker = setup_logging({}, level=numeric_level, stream=stream or sys.stdout)

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
            # Last: it masks the rendered line, keys and JSON-escaped forms included.
            mask_secrets_processor(masker),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(numeric_level),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    return masker


masker = configure_logging(LOG_LEVEL)
