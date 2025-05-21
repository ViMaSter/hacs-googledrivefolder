"""The Google Drive integration."""

from __future__ import annotations

import logging

from collections.abc import Callable

from google_drive_api.exceptions import GoogleDriveApiError

from time import time
from datetime import (timedelta, datetime)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import instance_id
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)
from typing import Final
from homeassistant.util.hass_dict import HassKey
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator
)
from homeassistant.helpers import instance_id

from .api import AsyncConfigEntryAuth, DriveFolderClient
from .const import (DOMAIN, DATA_COORDINATOR)
from .api import DriveFolderClient
import time

_LOGGER = logging.getLogger(__name__)

DEFAULT_UPDATE_INTERVAL: Final = timedelta(minutes=1)

DATA_BACKUP_AGENT_LISTENERS: HassKey[list[Callable[[], None]]] = HassKey(
    f"{DOMAIN}.backup_agent_listeners"
)

PLATFORMS = ["sensor"]

type GoogleDriveFolderConfigEntry = ConfigEntry[DriveFolderClient]

async def async_setup_entry(hass: HomeAssistant, entry: GoogleDriveFolderConfigEntry) -> bool:
    """Set up Google Drive from a config entry."""

    auth = AsyncConfigEntryAuth(
        async_get_clientsession(hass),
        OAuth2Session(
            hass, entry, await async_get_config_entry_implementation(hass, entry)
        ),
    )

    # Test we can refresh the token and raise ConfigEntryAuthFailed or ConfigEntryNotReady if not
    await auth.async_get_access_token()

    client = DriveFolderClient(await instance_id.async_get(hass), auth)
    entry.runtime_data = client

    coordinator = GoogleDriveFolderDataUpdateCoordinator(hass, entry=entry)

    # Test we can access Google Drive and raise if not
    try:
        folder_contents = await client.async_list_folder()
        if not isinstance(folder_contents, list):
            raise ConfigEntryNotReady("Expected a list of folder contents")
        _LOGGER.debug("Number of items in folder: %d", len(folder_contents))
    except GoogleDriveApiError as err:
        raise ConfigEntryNotReady from err
    
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {DATA_COORDINATOR: coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: GoogleDriveFolderConfigEntry
) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return True

class GoogleDriveFolderDataUpdateCoordinator(DataUpdateCoordinator):
    """Google Drive Folder Data Update Coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the Google Drive Folder hub."""
        self.entry = entry
        self.hass = hass
        self.api = entry.runtime_data

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=DEFAULT_UPDATE_INTERVAL)

    async def _async_update_data(self) -> dict:
        """Fetch data from Google Drive Folder."""
        files = await self.api.async_list_folder("root")
        _LOGGER.debug("Files fetched: %s", files)

        formatted_files = [
            f"{file[0]}: {file[2]} ({file[1]})"
            for file in files
        ]
        _LOGGER.debug("Folder files fetched: %s", formatted_files)

        return {
            "files": files,
            "lastSyncTimestampGMT": datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
        }
