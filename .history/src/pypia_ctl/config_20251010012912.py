"""Settings for :mod:`pypia_ctl` (Pydantic v2, env/.env aware).

Purpose:
    Centralize configuration with a single, typed settings object loaded from:
    OS env vars (highest) → local ``.env`` (middle) → defaults (fallback).

Design:
    - Pydantic v2 :class:`~pydantic_settings.BaseSettings` with:
      * ``env_prefix="PIA_"`` so keys start with ``PIA_...``.
      * ``env_nested_delimiter="__"`` to map nested models, e.g.
        ``PIA_PROXY__USERNAME`` → ``proxy.username``.
      * Non-strict types with validators for user-friendly inputs.
    - Small composable submodels (proxy, filters).
    - No network or heavyweight operations.

Attributes:
    ENV_PREFIX (str): The environment prefix used for settings (``"PIA_"``).

Examples:
    ::
        >>> from pypia_ctl.config import PiaSettings
        >>> s = PiaSettings()  # loads OS env/.env
        >>> s.protocol in {"wireguard", "openvpn"}
        True
        >>> s.proxy.kind in {"socks5", "http"}
        True
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX: str = "PIA_"


class RegionFilters(BaseModel):
    """Filters applied when choosing regions.

    Args:
        include_streaming: Allow slugs containing ``-streaming-optimized``.
        include_countries: Keep slugs that start with any of these prefixes
            e.g. ``["us-","ca-"]`` (empty ⇒ no restriction).
        exclude_countries: Exclude slugs that start with any of these prefixes.
    """

    include_streaming: bool = False
    include_countries: list[str] = Field(default_factory=list)
    exclude_countries: list[str] = Field(default_factory=list)

    @field_validator("include_countries", "exclude_countries", mode="before")
    @classmethod
    def _split_csv(cls, v: object) -> list[str]:
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return list(v)


class ProxyPrefs(BaseModel):
    """Proxy preferences used by adapters.

    Args:
        kind: Proxy scheme (``"socks5"`` or ``"http"``).
        host: Proxy host name or IP.
        port: Proxy port number.
        username: Username for proxy auth (optional).
        password: Password for proxy auth (optional).
    """

    kind: Literal["socks5", "http"] = "socks5"
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None

    @field_validator("port")
    @classmethod
    def _valid_port(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if not (0 < v < 65536):
            raise ValueError("port must be in 1..65535")
        return v


class PiaSettings(BaseSettings):
    """User preferences & runtime knobs.

    Args:
        protocol: ``"wireguard"`` (default) or ``"openvpn"``.
        default_region: Fallback region slug, e.g. ``"auto"``.
        preferred_regions: Comma or list. First available wins in "preferred".
        randomize_region: If True, allow random choice among eligible regions.
        subprocess_timeout_sec: Timeout (s) for individual ``piactl`` calls.
        monitor_line_timeout_sec: Timeout (s) per line for monitor.
        plugins: Comma or list of fully-qualified plugin class paths.
        region_filters: Rules to constrain region selection.
        proxy: Proxy configuration for adapters.

    Environment:
        - ``PIA_PROTOCOL`` (``wireguard``|``openvpn``)
        - ``PIA_DEFAULT_REGION`` (e.g. ``auto``)
        - ``PIA_PREFERRED_REGIONS`` (CSV)
        - ``PIA_RANDOMIZE_REGION`` (true/false)
        - ``PIA_SUBPROCESS_TIMEOUT_SEC`` (int)
        - ``PIA_MONITOR_LINE_TIMEOUT_SEC`` (int)
        - ``PIA_PLUGINS`` (CSV)
        - ``PIA_REGION_FILTERS__include_streaming`` (bool)
        - ``PIA_REGION_FILTERS__include_countries`` (CSV)
        - ``PIA_REGION_FILTERS__exclude_countries`` (CSV)
        - ``PIA_PROXY__KIND`` (``socks5``|``http``)
        - ``PIA_PROXY__HOST``, ``PIA_PROXY__PORT`` (int)
        - ``PIA_PROXY__USERNAME``, ``PIA_PROXY__PASSWORD``

    Examples:
        ::
            >>> import os
            >>> os.environ["PIA_PREFERRED_REGIONS"] = "us-new-york,ca-ontario"
            >>> s = PiaSettings()
            >>> s.preferred_regions[:2]
            ['us-new-york', 'ca-ontario']
    """

    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    protocol: Literal["wireguard", "openvpn"] = "wireguard"
    default_region: str = "auto"
    preferred_regions: list[str] = Field(default_factory=list)
    randomize_region: bool = True
    subprocess_timeout_sec: int = Field(default=6, gt=0)
    monitor_line_timeout_sec: int = Field(default=15, gt=0)
    plugins: list[str] = Field(default_factory=list)
    region_filters: RegionFilters = Field(default_factory=RegionFilters)
    proxy: ProxyPrefs = Field(default_factory=ProxyPrefs)

    @field_validator("preferred_regions", "plugins", mode="before")
    @classmethod
    def _csv_to_list(cls, v: object) -> list[str]:
        if v is None or v == "":
            return []
        if isinstance(v, str):
            return [t.strip() for t in v.split(",") if t.strip()]
        return list(v)

    @field_validator("default_region")
    @classmethod
    def _normalize_region_slug(cls, v: str) -> str:
        return v.strip().lower()
