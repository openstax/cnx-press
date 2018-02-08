import logging.config

import structlog


def includeme(config):
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
