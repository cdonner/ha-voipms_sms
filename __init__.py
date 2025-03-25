import logging
import aiohttp
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

# Define configuration schema
CONFIG_SCHEMA = vol.Schema({
    "account_user": cv.string,
    "api_password": cv.string,
    "sender_did": cv.string,
}, extra=vol.ALLOW_EXTRA)

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up VoIP.ms SMS from a config entry."""
    return await async_setup(hass, {entry.domain: entry.data})

async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the VoIP.ms SMS integration."""
    conf = config.get("voipms_sms", {})
    user = conf.get("account_user")
    password = conf.get("api_password")
    sender_did = conf.get("sender_did")

    if not user or not password or not sender_did:
        _LOGGER.error("Missing required configuration fields.")
        return False  # Explicit failure

    # Register the service correctly
    async def send_sms(call):
        """Send SMS using VoIP.ms API."""
        recipient = call.data.get("recipient")
        message = call.data.get("message")

        if not recipient or not message:
            _LOGGER.error("Recipient or message missing.")
            return

        params = {
            "api_username": user,
            "api_password": password,
            "did": sender_did,
            "dst": recipient,
            "method": "sendSMS",
            "message": message,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.voip.ms/api/v1/rest.php", params=params) as response:
                result = await response.text()
                if response.status == 200:
                    _LOGGER.info("SMS sent successfully: %s", result)
                else:
                    _LOGGER.error("Failed to send SMS. Status: %s, Response: %s", response.status, result)

    hass.services.async_register("voipms_sms", "send_sms", send_sms)

    _LOGGER.info("VoIP.ms SMS service registered successfully.")
    return True  # Explicit success
