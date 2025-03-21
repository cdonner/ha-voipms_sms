import asyncio
import logging
import requests
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

DOMAIN = "voipms_sms"

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the VoIP.ms SMS integration asynchronously."""
    conf = config.get(DOMAIN)

    if conf is None:
        return False

    hass.data[DOMAIN] = {
        "email": conf["email"],
        "api_password": conf["api_password"],
        "sender_did": conf["sender_did"],
    }

    async def async_send_sms_service(call):
        """Send an SMS using VoIP.ms API."""
        recipient = call.data.get("recipient")
        message = call.data.get("message")

        if not recipient or not message:
            _LOGGER.error("Recipient and message must be provided.")
            return

        payload = {
            "api_username": hass.data[DOMAIN]["email"],
            "api_password": hass.data[DOMAIN]["api_password"],
            "method": "sendSMS",
            "did": hass.data[DOMAIN]["sender_did"],
            "dst": recipient,
            "message": message,
        }

        try:
            response = await hass.async_add_executor_job(
                requests.get, "https://www.voip.ms/api/v1/rest.php", payload
            )
            result = response.json()
            if result.get("status") != "success":
                _LOGGER.error("Failed to send SMS: %s", result.get("status"))
            else:
                _LOGGER.info("SMS sent successfully to %s", recipient)
        except requests.RequestException as e:
            _LOGGER.error("Error sending SMS: %s", e)

    hass.services.async_register(DOMAIN, "send_sms", async_send_sms_service)

    _LOGGER.info("VoIP.ms SMS service registered.")
    return True

