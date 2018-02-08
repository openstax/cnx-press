import os

from press.config import discover_set


def test_discover_set_with_env_var():
    s = {}
    s_name = 'baz'
    var = 'FOO'
    val = 'bar'
    os.environ[var] = val

    discover_set(s, s_name, var)

    assert s_name in s
    assert s[s_name] == val

    del os.environ[var]


def test_discover_set_without_env_var_or_default():
    s = {}
    s_name = 'baz'
    var = 'FOO'
    # val = 'bar'

    discover_set(s, s_name, var)

    assert s_name not in s


def test_discover_set_with_default():
    s = {}
    s_name = 'baz'
    var = 'FOO'
    # val = 'bar'
    default = 'smoo'

    discover_set(s, s_name, var, default=default)

    assert s_name in s
    assert s[s_name] == default


def test_discover_set_witout_env_var_and_keeps_existing():
    s_name = 'baz'
    var = 'FOO'
    val = 'bar'
    default = 'smoo'
    s = {s_name: val}

    discover_set(s, s_name, var, default=default)

    assert s_name in s
    assert s[s_name] == val


def test_discover_set_with_env_var_and_existing():
    s_name = 'baz'
    var = 'FOO'
    val = 'bar'
    default = 'smoo'
    s = {s_name: val}
    os.environ[var] = val

    discover_set(s, s_name, var, default=default)

    assert s_name in s
    assert s[s_name] == val

    del os.environ[var]


def test_discover_set_with_env_var_and_modifier():
    s = {}
    s_name = 'baz'
    var = 'FOO'
    val = 'bar'
    os.environ[var] = val

    discover_set(s, s_name, var, modifier=str.upper)

    assert s_name in s
    assert s[s_name] == val.upper()

    del os.environ[var]
