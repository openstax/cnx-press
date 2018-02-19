import logging.config
import uuid

import structlog


def _create_id(request):
    """Request attribute factory for creating a unique id."""
    return str(uuid.uuid4())


def _create_logger(request):
    """Request attribute factory to give access to the logger."""
    logger = structlog.get_logger("press.request")
    logger = logger.bind(request_id=request.id)
    return logger


def includeme(config):
    """Configure logging for the application"""
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'NOTSET',
                'stream': 'ext://sys.stdout',
            },
        },
        'root': {
            'level': config.registry.settings.get('logging.level', 'INFO'),
            'handlers': ['console'],
        },
    })

    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M.%S",
                                             utc=False),
            structlog.processors.KeyValueRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )

    logger = structlog.get_logger('press.logging')
    logger.info('logging configuration initialized')
    logger.debug('debug logging enabled')

    # Give every request a unique identifier.
    config.add_request_method(_create_id, name="id", reify=True)

    # Add a log method to every request.
    config.add_request_method(_create_logger, name="log", reify=True)
