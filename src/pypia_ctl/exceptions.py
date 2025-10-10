"""Custom exceptions for :mod:`pypia_ctl`.

Purpose:
    Provide precise, typed exceptions instead of `RuntimeError`, so callers can
    distinguish missing executables, timeouts, or generic invocation failures.

Design:
    - Small inheritance tree with a single public base class.
    - No external dependencies; used across core runners and connect logic.

Classes:
    PiaCtlError: Base for all pypia_ctl errors.
    PiaCtlNotFound: `piactl` executable could not be located on PATH.
    PiaCtlInvocationFailed: `piactl` returned non-zero or subprocess failed.
    PiaConnectTimeout: Connection did not reach `Connected` in time.

Examples:
    ::
        >>> try:
        ...     raise PiaCtlNotFound("not on PATH")
        ... except PiaCtlError as e:
        ...     isinstance(e, PiaCtlNotFound)
        True
"""

from __future__ import annotations


class PiaCtlError(Exception):
    """Base error for :mod:`pypia_ctl` operations."""


class PiaCtlNotFound(PiaCtlError):
    """`piactl` executable not found on PATH."""


class PiaCtlInvocationFailed(PiaCtlError):
    """`piactl` returned non-zero or the subprocess/timeout failed."""


class PiaConnectTimeout(PiaCtlError):
    """Did not reach `Connected` within the polling window."""
