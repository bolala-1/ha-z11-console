"""Z11 Console Integration for Home Assistant.

Transforms the Z11 Smart Home Console into a 100% native Home Assistant integration,
running directly inside Home Assistant's event loop and aiohttp server, with zero
external Docker containers needed and full same-origin immersion.
"""
from __future__ import annotations

import logging
from pathlib import Path

from aiohttp import web
from homeassistant import config_entries
from homeassistant.components.frontend import async_register_built_in_panel
from homeassistant.components.http import StaticPathConfig
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DATA_DIR_NAME, DEFAULT_ICON, DEFAULT_TITLE, DEFAULT_URL_PATH, DOMAIN
from .home_console_server.app import create_app

_LOGGER = logging.getLogger(__name__)

DEFAULT_HA_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJhZjdiMGZjYjBiYjg0NWZjYjc5YjY4MmRjZjA1MDEyNCIsImlhdCI6MTc5MTE5MTMxNSwiZXhwIjoyMTA2NTUxMzE1fQ."
    "kZqSbTlijLPOIPiDpvB1WfIMQ22_6o3o8dTu8EZ806s"
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Z11 Console native component."""
    if DOMAIN in hass.data:
        return True

    _LOGGER.info("Starting Z11 Console native integration...")

    # Data directory in Home Assistant config: /config/z11_data
    data_dir = Path(hass.config.path(DATA_DIR_NAME))
    data_dir.mkdir(parents=True, exist_ok=True)

    # Static assets directory: custom_components/z11_console/dist
    static_dir = Path(__file__).parent / "dist"

    conf = config.get(DOMAIN, {}) if isinstance(config, dict) else {}
    custom_token = conf.get("token") or DEFAULT_HA_TOKEN

    # Create Z11 aiohttp application
    subapp = create_app(data_dir=data_dir, static_dir=static_dir)
    console = subapp["console"]

    # Pre-configure localhost connection if missing
    settings = console.store.settings
    if not settings.ha_url:
        settings.ha_url = "http://127.0.0.1:8123"
        settings.data_source = "live"
    if not console.store.token():
        console.store.set_token(custom_token)
        settings.data_source = "live"
        console.store.save_settings()

    # Start standalone AppRunner on port 8766 inside HA process
    runner = web.AppRunner(subapp)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8766)
    await site.start()
    _LOGGER.info("Z11 Console HTTP runner listening on 0.0.0.0:8766")

    # Register static path in Home Assistant HTTP server for panel wrapper
    try:
        await hass.http.async_register_static_paths([
            StaticPathConfig("/z11_static", str(static_dir), cache_headers=False)
        ])
    except Exception as err:
        _LOGGER.warning("Could not register static paths: %s", err)

    # Register cleanup on Home Assistant stop
    async def async_on_ha_stop(_event):
        _LOGGER.info("Gracefully stopping Z11 Console runner...")
        await runner.cleanup()

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, async_on_ha_stop)

    # Register sidebar panel in Home Assistant frontend
    async_register_built_in_panel(
        hass,
        component_name="iframe",
        sidebar_title=DEFAULT_TITLE,
        sidebar_icon=DEFAULT_ICON,
        frontend_url_path=DEFAULT_URL_PATH,
        config={"url": "/z11_static/panel.html"},
        require_admin=False,
    )

    hass.data[DOMAIN] = {
        "runner": runner,
        "console": console,
    }

    _LOGGER.info("Z11 Console successfully loaded! UI available on port 8766 and sidebar /z11")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Set up Z11 Console from a config entry."""
    return await async_setup(hass, {})


async def async_unload_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Unload a config entry."""
    if DOMAIN in hass.data:
        data = hass.data.pop(DOMAIN)
        runner = data.get("runner")
        if runner:
            await runner.cleanup()
    return True
