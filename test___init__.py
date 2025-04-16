import pytest
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from homeassistant.core import HomeAssistant, ServiceCall
from __init__ import async_setup, send_sms, send_mms
import contextlib

@pytest.fixture
def hass():
    hass_mock = MagicMock(spec=HomeAssistant)
    hass_mock.services = MagicMock()
    hass_mock.services.async_register = MagicMock()
    return hass_mock

@pytest.fixture
def config():
    return {
        "voipms_sms": {
            "account_user": "test_user",
            "api_password": "test_password",
            "sender_did": "1234567890",
        }
    }

@pytest.fixture
def service_call_sms(hass):
    return ServiceCall(
        hass=hass,
        domain="voipms_sms",
        service="send_sms",
        data={"recipient": "9876543210", "message": "Test SMS"},
    )

@pytest.fixture
def service_call_mms(hass, tmp_path):
    image_path = tmp_path / "test_image.jpg"
    image_path.write_text("fake_image_data")
    return ServiceCall(
        hass=hass,
        domain="voipms_sms",
        service="send_mms",
        data={"recipient": "9876543210", "message": "Test MMS", "image_path": str(image_path)},
    )

@pytest.mark.asyncio
async def test_send_sms_success(hass, config, service_call_sms):
    await async_setup(hass, config)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="Success")

    with patch("aiohttp.ClientSession") as mock_session:
        mock_session_instance = mock_session.return_value
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.get.return_value = contextlib.nullcontext(mock_response)

        await send_sms(hass, "test_user", "test_password", "1234567890", service_call_sms)

        mock_session_instance.get.assert_called_once_with(
            "https://voip.ms/api/v1/rest.php",
            params={
                "api_username": "test_user",
                "api_password": "test_password",
                "did": "1234567890",
                "dst": "9876543210",
                "method": "sendSMS",
                "message": "Test SMS",
            },
        )
        # Ensure the mocked response text is awaited
        await mock_response.text()

@pytest.mark.asyncio
async def test_send_sms_failure(hass, config, service_call_sms):
    await async_setup(hass, config)
    mock_response = AsyncMock()
    mock_response.status = 400
    mock_response.text = AsyncMock(return_value="Error")

    with patch("aiohttp.ClientSession") as mock_session:
        mock_session_instance = mock_session.return_value
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.get.return_value = contextlib.nullcontext(mock_response)

        await send_sms(hass, "test_user", "test_password", "1234567890", service_call_sms)

        mock_session_instance.get.assert_called_once()
        # Ensure the mocked response text is awaited
        await mock_response.text()

@pytest.mark.asyncio
async def test_send_mms_success(hass, config, service_call_mms):
    await async_setup(hass, config)
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text = AsyncMock(return_value="Success")

    with patch("aiohttp.ClientSession") as mock_session:
        mock_session_instance = mock_session.return_value
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.post.return_value = contextlib.nullcontext(mock_response)

        with patch("__init__.get_base64_data", new_callable=AsyncMock) as mock_base64:
            mock_base64.return_value = "base64_image_data"
            await send_mms(hass, "test_user", "test_password", "1234567890", service_call_mms)

            mock_session_instance.post.assert_called_once()
            # Ensure the mocked response text is awaited
            await mock_response.text()

@pytest.mark.asyncio
async def test_send_mms_missing_image(hass, config, service_call_mms):
    modified_service_call = ServiceCall(
        hass=service_call_mms.hass,
        domain=service_call_mms.domain,
        service=service_call_mms.service,
        data={**service_call_mms.data, "image_path": "/nonexistent/path.jpg"},
    )

    await async_setup(hass, config)

    with patch("aiohttp.ClientSession") as mock_session:
        mock_session_instance = mock_session.return_value
        mock_session_instance.__aenter__.return_value = mock_session_instance
        mock_session_instance.post.return_value = contextlib.nullcontext(Mock())

        await send_mms(hass, "test_user", "test_password", "1234567890", modified_service_call)

        mock_session_instance.post.assert_not_called()