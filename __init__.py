import logging
import aiohttp
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

_LOGGER = logging.getLogger(__name__)

# Define configuration schema
CONFIG_SCHEMA = vol.Schema(
    {
        "voipms_sms": vol.Schema(
            {
                vol.Required("account_user"): cv.string,
                vol.Required("api_password"): cv.string,
                vol.Required("sender_did"): cv.string,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

async def async_setup(hass: HomeAssistant, config: ConfigType):
    """Set up the VoIP.ms SMS integration."""
    conf = config.get("voipms_sms", {})
    user = conf.get("account_user")
    password = conf.get("api_password")
    sender_did = conf.get("sender_did")

    if not user or not password or not sender_did:
        _LOGGER.error("Missing required configuration fields.")
        return False

    async def send_sms(call: ServiceCall):
        """Send SMS using the VoIP.ms API."""
        recipient_number = call.data.get("recipient")
        message = call.data.get("message")

        if not recipient_number or not message:
            _LOGGER.error("Recipient or message missing.")
            return

        params = {
            "api_username": user,
            "api_password": password,
            "did": sender_did,
            "dst": recipient_number,
            "method": "sendSMS",
            "message": message,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url="https://www.voip.ms/api/v1/rest.php", params=params
                ) as response:
                    if response.status == 200:
                        result = await response.text()
                        _LOGGER.info("SMS sent successfully: %s", result)
                    else:
                        _LOGGER.error("Failed to send SMS. Status: %s", response.status)
                        result = await response.text()
                        _LOGGER.error("Error response: %s", result)
        except Exception as e:
            _LOGGER.error(f"Error sending SMS: {e}")

    # Correct async service registration
    hass.services.async_register("voipms_sms", "send_sms", send_sms)

    _LOGGER.info("VoIP.ms SMS service registered.")
    return True
