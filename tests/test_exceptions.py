"""Tests for sharklocal.exceptions."""

import pytest

from sharklocal.exceptions import (
    ActionNotSupportedError,
    CommandError,
    ConnectError,
    DecoderError,
    MappingNotFoundError,
    SharklocalError,
)


_LEAF_EXCEPTIONS = [
    ConnectError,
    CommandError,
    ActionNotSupportedError,
    MappingNotFoundError,
    DecoderError,
]


@pytest.mark.parametrize("exc_class", _LEAF_EXCEPTIONS)
def test_leaf_is_subclass_of_base(exc_class):
    assert issubclass(exc_class, SharklocalError)


@pytest.mark.parametrize("exc_class", _LEAF_EXCEPTIONS)
def test_leaf_is_also_exception(exc_class):
    assert issubclass(exc_class, Exception)


@pytest.mark.parametrize("exc_class", _LEAF_EXCEPTIONS)
def test_raise_and_catch_as_base(exc_class):
    with pytest.raises(SharklocalError):
        raise exc_class("test message")


@pytest.mark.parametrize("exc_class", _LEAF_EXCEPTIONS)
def test_raise_and_catch_as_self(exc_class):
    with pytest.raises(exc_class):
        raise exc_class("test message")


@pytest.mark.parametrize("exc_class", _LEAF_EXCEPTIONS)
def test_message_preserved(exc_class):
    msg = f"specific {exc_class.__name__} message"
    exc = exc_class(msg)
    assert str(exc) == msg


def test_distinct_types_not_interchangeable():
    """Catching ConnectError does not catch CommandError."""
    with pytest.raises(CommandError):
        try:
            raise CommandError("cmd failed")
        except ConnectError:
            pass  # Should NOT catch it
