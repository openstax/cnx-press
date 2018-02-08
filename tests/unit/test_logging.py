import pytest
import structlog
from pyramid import testing as pyramid_testing

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
