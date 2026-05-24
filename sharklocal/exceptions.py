"""Custom exceptions for the sharklocal library."""


class SharklocalError(Exception):
    """Base exception for all sharklocal errors."""


class ConnectError(SharklocalError):
    """Raised when a connection to the vacuum cannot be established."""


class CommandError(SharklocalError):
    """Raised when a command fails to execute or receives an error response."""


class ActionNotSupportedError(SharklocalError):
    """Raised when an action is not defined in the configured transport mapping."""


class MappingNotFoundError(SharklocalError):
    """Raised when a named mapping file cannot be located."""


class DecoderError(SharklocalError):
    """Raised when a response payload cannot be decoded."""
