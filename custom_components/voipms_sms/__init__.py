import logging
import aiohttp
import asyncio
import base64
import os
import mimetypes
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# Define configuration schema
CONFIG_SCHEMA = vol.Schema({
    "account_user": cv.string,
    "api_password": cv.string,
    "sender_did": cv.string,
}, extra=vol.ALLOW_EXTRA)

REST_ENDPOINT = "https://voip.ms/api/v1/rest.php"

async def get_base64_data(image_path):
    def encode():
        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        with open(image_path, 'rb') as f:
            encoded = base64.b64encode(f.read()).decode()
        return f"data:{mime_type};base64,{encoded}"
    return await asyncio.to_thread(encode)

async def async_setup_entry(hass: HomeAssistant, entry):
    """Set up VoIP.ms SMS from a config entry."""
    return await async_setup(hass, {entry.domain: entry.data})

# ...existing imports...

async def send_sms(hass, user, password, sender_did, call):
    """Send SMS using VoIP.ms API."""
    _LOGGER = logging.getLogger(__name__)
    recipient = call.data.get("recipient")
    message = call.data.get("message")

    if not recipient or not message:
        _LOGGER.error("Recipient or message missing.")
        return

    data = {
        "api_username": user,
        "api_password": password,
        "did": sender_did,
        "dst": recipient,
        "method": "sendSMS",
        "message": message,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(REST_ENDPOINT, data=data) as response:
            result = await response.text()
            if response.status == 200:
                _LOGGER.info("voipms_sms: SMS sent successfully: %s", result)
            else:
                _LOGGER.error("voipms_sms: Failed to send SMS. Status: %s, Response: %s", response.status, result)


async def send_mms(hass, user, password, sender_did, call):
    """Send MMS using VoIP.ms API."""
    _LOGGER = logging.getLogger(__name__)
    recipient = call.data.get("recipient")
    message = call.data.get("message")
    image_path = call.data.get("image_path")

    if not recipient or not message or not image_path:
        _LOGGER.error("voipms_sms: Required parameter missing (Recipient or message or image path)")
        return

    if not os.path.exists(image_path):
        _LOGGER.error("voipms_sms: Image file not found: %s", image_path)
        return

    media_data = await get_base64_data(image_path)

    form_data = {
        'api_username': str(user), 
        'api_password': str(password),
        'did': str(sender_did),
        'dst': str(recipient),
        'message': str(message),
        'method': str('sendMMS'),
        'media1': str(media_data)
    }

    async with aiohttp.ClientSession() as session:
        with aiohttp.MultipartWriter("form-data") as mp:
            for key, value in form_data.items():
                part = mp.append(value)
                part.set_content_disposition('form-data', name=key)

        async with session.post(REST_ENDPOINT, data=mp) as response:
            response_text = await response.text()
            if response.status == 200:
                _LOGGER.info("voipms_sms: MMS sent successfully: %s", response_text)
            else:
                _LOGGER.error("voipms_sms: Failed to send MMS. Status: %s, Response: %s", response.status, response_text)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the VoIP.ms SMS integration."""
    conf = config.get("voipms_sms", {})
    user = conf.get("account_user")
    password = conf.get("api_password")
    sender_did = conf.get("sender_did")

    if not user or not password or not sender_did:
        _LOGGER.error("Missing required configuration fields.")
        return False  # Explicit failure

    async def handle_send_sms(call):
        await send_sms(hass, user, password, sender_did, call)

    async def handle_send_mms(call):
        await send_mms(hass, user, password, sender_did, call)

    hass.services.async_register(
        "voipms_sms", "send_sms", handle_send_sms
    )
    hass.services.async_register(
        "voipms_sms", "send_mms", handle_send_mms
    )

    _LOGGER.info("voipms_sms: VoIP.ms SMS/MMS services registered successfully.")
    return True  # Explicit success