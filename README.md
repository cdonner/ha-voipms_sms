# voipms_sms
Home Assistant custom integration for sending SMS (text) and MMS (photo snapshot) messages via [Voip.ms](https://voip.ms/) REST Api 

## Prerequisites
- Voip.ms account with a DID that has SMS turned on
- API configuration set in the Voip.ms portal
  - API password set
  - API enabled
  - External IP address of your HA site, or DNS domain (sender whitelist)
  - Bearer token (optional, not needed for sending)
- Home Assistant running

## How to install the integration

### Manually

Create a folder structure on your HA server and deploy the three files.
Make sure that the folder name matches the service domain - voipms_sms:

```
/config/custom_components/voipms_sms/
  ├── __init__.py
  ├── manifest.json
  ├── services.yaml
```  

### Using HACS

When you are looking at the HACS page for the Voip.ms integration in Home Assistant, it displays a "Download" button at the botton.
Click on it, then proceed with the configuration steps.

### Configuration

Update `configuration.yml` and add the following section:

```
voipms_sms:
  account_user: !secret voipms_user
  api_password: !secret voipms_password
  sender_did: "9999999999"
```

Use your Voip.ms login email and the 10 digit DID phone number for the sender_did value, without punctuation.

Add the user and password secrets to your `secrets.yml`:

```
api_password: "your_voipms_api_password"
voipms_user: "your_voipms_account_user"
```

Validate your configuration:

```
ha core check
```

Restart HA:

```
ha core restart
```

## Verify

Verify that that are no errors in the log from registering the service. 
Make sure that `VoIP.ms SMS` shows up in the list of loaded integrations:

![alt text](custom-integration.png)


## Using the integration

To send a test message, navigate to `Developer Tools > Actions`, select VoIP.ms SMS: Send SMS (or Send MMS) in HA and enter your mobile phone number in the recipient field:

![alt text](developer-tools.png)

When testing MMS, make sure you enter the full local path to an existing image, e.g.
```
 image_path: /config/www/porch_snapshot.jpg
```

If you do not receive a text message, consult your logs for errors.

I use the services in flows, e.g. with Node Red as an Action node:

![alt text](node-red.png)

## FAQ

Q: Are there plans for adding other API functions to the integration, for example to receive text messages?

A: Not at this time.

Q: Can I send to multiple phone numbers at a time, i.e. is there support for group messages?

A: No, the Voip.ms API only accepts a single recipient.


## Planned enhancements (with no target date):

- Home-Assistantify, i.e. publish through HACS and make the installation easier.
