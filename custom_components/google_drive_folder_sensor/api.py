"""API for Google Drive bound to Home Assistant OAuth."""

from __future__ import annotations

from typing import Any

from aiohttp import ClientSession, ClientTimeout, StreamReader
from aiohttp.client_exceptions import ClientError, ClientResponseError
from google_drive_api.api import AbstractAuth, GoogleDriveApi

from homeassistant.components.backup import AgentBackup, suggested_filename
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
)
from homeassistant.helpers import config_entry_oauth2_flow

_UPLOAD_AND_DOWNLOAD_TIMEOUT = 12 * 3600

class AsyncConfigEntryAuth(AbstractAuth):
    """Provide Google Drive authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        websession: ClientSession,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ) -> None:
        """Initialize AsyncConfigEntryAuth."""
        super().__init__(websession)
        self._oauth_session = oauth_session

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        try:
            await self._oauth_session.async_ensure_token_valid()
        except ClientError as ex:
            if (
                self._oauth_session.config_entry.state
                is ConfigEntryState.SETUP_IN_PROGRESS
            ):
                if isinstance(ex, ClientResponseError) and 400 <= ex.status < 500:
                    raise ConfigEntryAuthFailed(
                        "OAuth session is not valid, reauth required"
                    ) from ex
                raise ConfigEntryNotReady from ex
            if hasattr(ex, "status") and ex.status == 400:
                self._oauth_session.config_entry.async_start_reauth(
                    self._oauth_session.hass
                )
            raise HomeAssistantError(ex) from ex
        return str(self._oauth_session.token[CONF_ACCESS_TOKEN])


class AsyncConfigFlowAuth(AbstractAuth):
    """Provide authentication tied to a fixed token for the config flow."""

    def __init__(
        self,
        websession: ClientSession,
        token: str,
    ) -> None:
        """Initialize AsyncConfigFlowAuth."""
        super().__init__(websession)
        self._token = token

    async def async_get_access_token(self) -> str:
        """Return a valid access token."""
        return self._token


class DriveFolderClient:
    """Google Drive client."""

    def __init__(
        self,
        ha_instance_id: str,
        auth: AbstractAuth,
    ) -> None:
        """Initialize Google Drive client."""
        self._ha_instance_id = ha_instance_id
        self._api = GoogleDriveApi(auth)

    async def async_get_email_address(self) -> str:
        """Get email address of the current user."""
        res = await self._api.get_user(params={"fields": "user(emailAddress)"})
        return str(res["user"]["emailAddress"])

    async def async_trash(self, file_id: str) -> None:
        """Move file to trash."""
        body_value = {"trashed": True}
        await self._api.update_file(file_id, body=body_value)

    async def async_download(self, file_id: str) -> StreamReader:
        """Download a file."""
        resp = await self._api.get_file_content(
            file_id, timeout=ClientTimeout(total=_UPLOAD_AND_DOWNLOAD_TIMEOUT)
        )
        return resp.content

    async def async_list_folder(
        self, folder_id: str = "root"
    ) -> list[tuple[str, str, str]]:
        """Get all files and folders in a folder (or root by default) as a list of tuples."""
        query = "trashed=false"
        if folder_id != "root":
            query = f"'{folder_id}' in parents and {query}"
        params = {
            "q": query,
            "fields": "files(id, name, mimeType)",
        }
        res = await self._api.list_files(params=params)
        return [
            (
                file["id"],
                file["name"],
                "folder" if file["mimeType"] == "application/vnd.google-apps.folder" else "file",
            )
            for file in res.get("files", [])
        ]
