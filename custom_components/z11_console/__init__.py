"""Z11 Console Integration for Home Assistant.

Transforms the Z11 Smart Home Console into a 100% native Home Assistant integration,
running directly inside Home Assistant's event loop and aiohttp server, with zero
external Docker containers needed and full same-origin immersion.
"""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DATA_DIR_NAME, DEFAULT_ICON, DEFAULT_TITLE, DEFAULT_URL_PATH, DOMAIN
from .home_console_server.app import create_app

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Z11 Console native component."""
    _LOGGER.info("Starting Z11 Console native integration...")

    # Data directory in Home Assistant config: /config/z11_data
    data_dir = Path(hass.config.path(DATA_DIR_NAME))
    data_dir.mkdir(parents=True, exist_ok=True)

    # Static assets directory: custom_components/z11_console/dist
    static_dir = Path(__file__).parent / "dist"

    conf = config.get(DOMAIN, {}) if isinstance(config, dict) else {}
    custom_token = conf.get("token")

    # Create Z11 aiohttp sub-application
    subapp = create_app(data_dir=data_dir, static_dir=static_dir)
    console = subapp["console"]

    # Pre-configure localhost connection if token provided or default settings missing
    settings = console.store.settings
    if not settings.ha_url:
        settings.ha_url = "http://127.0.0.1:8123"
        settings.data_source = "live"
    if custom_token:
        console.store.set_token(custom_token)
        settings.data_source = "live"
        console.store.save_settings()

    # Mount subapp onto Home Assistant's main aiohttp server
    # Routes /z11 and /z11/* directly to Z11 Console subapp
    hass.http.app.add_subapp("/z11", subapp)

    # Initialize subapp lifecycle
    await subapp.startup()

    # Register cleanup on Home Assistant stop
    async def async_on_ha_stop(_event):
        _LOGGER.info("Gracefully stopping Z11 Console subapp...")
        await subapp.shutdown()
        await subapp.cleanup()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_on_ha_stop)

    # Register sidebar panel in Home Assistant frontend
    async_register_built_in_panel(
        hass,
        component_name="iframe",
        sidebar_title=DEFAULT_TITLE,
        sidebar_icon=DEFAULT_ICON,
        frontend_url_path=DEFAULT_URL_PATH,
        config={"url": "/z11/"},
        require_admin=False,
    )

    _LOGGER.info("Z11 Console successfully loaded and mounted at /z11/ !")
    return True
