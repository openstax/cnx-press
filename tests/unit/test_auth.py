from press.auth import (
    check_password,
    make_secret,
)


def test_check_password():
    passwd = b'{SSHA}3+8dzMtMDTkn2AdKzY0WCOkVZ2X9jQtg'  # abc123
    assert check_password(passwd, 'abc123') is True
    assert check_password(passwd, 'foobar') is False


def test_make_secret():
    assert check_password(make_secret('qwerty3'), 'qwerty3') is True
