import logging.config
from unittest import mock

import pretend
import pytest
import structlog
from pyramid import testing as pyramid_testing

from press import logging as press_logging
from press.logging import includeme


class FauxTimeStamper(object):

    def __new__(cls, fmt=None, utc=True, key="timestamp"):

        def stamper(self, _, __, event_dict):
            event_dict[key] = 'round and round'
            return event_dict

        return type("TimeStamper", (object,), {"__call__": stamper})()


@pytest.fixture
def mock_timestamper(request):
    """Create a fake timestamper for easier assertions"""
    from press.logging import structlog as x_structlog
    original = x_structlog.processors.TimeStamper

    def reset_TimeStamper():
        setattr(x_structlog.processors, 'TimeStamper', original)

    request.addfinalizer(reset_TimeStamper)
    x_structlog.processors.TimeStamper = FauxTimeStamper


def test_init(capsys, mock_timestamper):
    logger = structlog.get_logger()

    # Configure pyramid app
    with pyramid_testing.testConfig() as config:
        config.include(includeme)
        # Create some log messages
        logger.info('info msg')
        logger.debug('debug msg')
        logger.error('error msg')

    # Check for results
    captured = capsys.readouterr()
    expected = (
        "event='logging configuration initialized' logger='press.logging'"
        " level='info' timestamp='round and round'"
        "\n"
        "event='info msg' logger='tests.unit.test_logging'"
        " level='info' timestamp='round and round'"
        "\n"
        "event='error msg' logger='tests.unit.test_logging'"
        " level='error' timestamp='round and round'"
        "\n"
    )
    assert captured.out == expected
    assert captured.err == ''


def test_init_with_debug(capsys, mock_timestamper):
    logger = structlog.get_logger()

    # Configure pyramid app
    settings = {'logging.level': 'DEBUG'}
    with pyramid_testing.testConfig(settings=settings) as config:
        config.include(includeme)
        # Create some log messages
        logger.info('info msg')
        logger.debug('debug msg')
        logger.error('error msg')

    # Check for results
    captured = capsys.readouterr()
    expected = (
        "event='logging configuration initialized' logger='press.logging'"
        " level='info' timestamp='round and round'"
        "\n"
        "event='debug logging enabled' logger='press.logging'"
        " level='debug' timestamp='round and round'"
        "\n"
        "event='info msg' logger='tests.unit.test_logging'"
        " level='info' timestamp='round and round'"
        "\n"
        "event='debug msg' logger='tests.unit.test_logging'"
        " level='debug' timestamp='round and round'"
        "\n"
        "event='error msg' logger='tests.unit.test_logging'"
        " level='error' timestamp='round and round'"
        "\n"
    )
    assert captured.out == expected
    assert captured.err == ''


def test_includeme(monkeypatch):
    dict_config = pretend.call_recorder(lambda c: None)
    monkeypatch.setattr(logging.config, 'dictConfig', dict_config)

    structlog_configure = pretend.call_recorder(lambda **kw: None)
    monkeypatch.setattr(structlog, 'configure', structlog_configure)

    settings = {}
    add_request_method = pretend.call_recorder(lambda fn, name, reify: None)
    config = pretend.stub(
        registry=pretend.stub(settings=settings),
        add_request_method=add_request_method,
    )

    # Call the target includeme
    includeme(config)

    expected_level = 'INFO'
    assert dict_config.calls == [
        pretend.call({
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
                'level': expected_level,
                'handlers': ['console'],
            },
        }),
    ]

    assert structlog_configure.calls == [
        pretend.call(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                mock.ANY,  # specific test to follow
                mock.ANY,
                structlog.processors.format_exc_info,
                mock.ANY,
                mock.ANY,  # specific test to follow
            ],
            logger_factory=mock.ANY,  # specific test to follow
            wrapper_class=structlog.stdlib.BoundLogger,
        ),
    ]
    # Check the first set of logging configuration features that mimic stdlib.
    assert isinstance(
        structlog_configure.calls[0].kwargs['processors'][3],
        structlog.stdlib.PositionalArgumentsFormatter,
    )

    # Check the second set of logging configuration features.
    assert isinstance(
        structlog_configure.calls[0].kwargs['processors'][7],
        structlog.processors.KeyValueRenderer,
    )

    assert isinstance(
        structlog_configure.calls[0].kwargs['logger_factory'],
        structlog.stdlib.LoggerFactory,
    )

    # Check for request method registration
    assert config.add_request_method.calls == [
        pretend.call(press_logging._create_id, name='id', reify=True),
        pretend.call(press_logging._create_logger, name='log', reify=True),
    ]


def test_request_id(monkeypatch):
    monkeypatch.setattr(press_logging.uuid, 'uuid4', lambda: '<uuid>')
    assert press_logging._create_id(None) == '<uuid>'


def test_request_log(monkeypatch):
    bound_logger = pretend.stub()
    logger_bind = pretend.call_recorder(lambda **kw: bound_logger)
    logger = pretend.stub(bind=logger_bind)
    monkeypatch.setattr(structlog, 'get_logger', lambda n: logger)

    expected_id = '<uuid>'
    request = pretend.stub(id=expected_id)
    # Check the function creates a bound_logger
    assert press_logging._create_logger(request) == bound_logger
    # Check the logger called the bind with a request id.
    assert logger_bind.calls == [pretend.call(request_id=expected_id)]
