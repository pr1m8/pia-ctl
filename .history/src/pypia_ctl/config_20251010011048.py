# src/pypia_ctl/config.py
"""Configuration (env-driven) for :mod:`pypia_ctl`.

Purpose:
    Centralize preferences using :mod:`pydantic_settings` with prefix ``PIA_``.
    You can place values in a local ``.env`` near your project root.

Key Ideas:
    - Single source of truth for protocol/regions/timeouts/plugins.
    - Composable filters to constrain randomization (e.g., only "ca-" & "us-").
    - Proxy preferences for the adapters (SOCKS5/HTTP, host/port/creds).

Attributes:
    ENV_PREFIX (str): Environment prefix (``"PIA_"``).
"""

from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_PREFIX: str = "PIA_"


class RegionFilters(BaseModel):
    """Filters applied when choosing a region.

    Args:
        include_streaming: Allow slugs containing ``-streaming-optimized``.
        include_countries: Keep slugs that start with any of these prefixes
            (e.g., ``"us-"``, ``"ca-"``). Empty means no restriction.
        exclude_countries: Exclude slugs starting with any of these prefixes.
    """
    include_streaming: bool = False
    include_countries: list[str] = Field(default_factory=list)
    exclude_countries: list[str] = Field(default_factory=list)


class ProxyPrefs(BaseModel):
    """Default proxy preferences for adapter helpers.

    Args:
        kind: ``"socks5"`` or ``"http"``.
        host: Proxy hostname.
        port: Proxy port.
        username: Optional username for proxy auth.
        password: Optional password for proxy auth.
    """
    kind: Literal["socks5", "http"] = "socks5"
    host: str | None = None
    port: int | None = None
    username: str | None = None
    password: str | None = None


class PiaSettings(BaseSettings):
    """User preferences & runtime knobs for PIA control.

    Args:
        protocol: ``"wireguard"`` (default) or ``"openvpn"``.
        default_region: Fallback region slug (default ``"auto"``).
        preferred_regions: Ordered shortlist for the “preferred” strategy.
        randomize_region: If True, allow random choice among filtered regions.
        subprocess_timeout_sec: Timeout (s) for each `piactl` call.
        monitor_line_timeout_sec: Timeout (s) per line for monitor().
        plugins: Comma-separated import paths to plugin classes.
        region_filters: Filters constraining eligible regions.
        proxy: Default proxy preferences for adapters.

    Environment:
        All keys use prefix ``PIA_``. Notable ones:
          - ``PIA_PROTOCOL`` (wireguard|openvpn)
          - ``PIA_DEFAULT_REGION`` (e.g., auto)
          - ``PIA_PREFERRED_REGIONS`` (comma list)
          - ``PIA_RANDOMIZE_REGION`` (true/false)
          - ``PIA_REGION_FILTERS__include_streaming`` (true/false)
          - ``PIA_PROXY_KIND`` (socks5|http)
          - ``PIA_PROXY_HOST``, ``PIA_PROXY_PORT``
          - ``PIA_PROXY_USERNAME``, ``PIA_PROXY_PASSWORD``
          - ``PIA_PLUGINS`` (comma list of fully-qualified classes)
    """
    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    protocol: Literal["wireguard", "openvpn"] = "wireguard"
    default_region: str = "auto"
    preferred_regions: list[str] = Field(default_factory=list)
    randomize_region: bool = True
    subprocess_timeout_sec: Annotated[int, Field(gt=0)] = 6
    monitor_line_timeout_sec: Annotated[int, Field(gt=0)] = 15
    plugins: list[str] = Field(default_factory=list)
    region_filters: RegionFilters = Field(default_factory=RegionFilters)
    proxy: ProxyPrefs = Field(default_factory=ProxyPrefs)
