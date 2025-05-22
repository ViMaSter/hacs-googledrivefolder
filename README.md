# Google Drive Folder Sensor
[HACS](https://www.hacs.xyz/) component that adds a sensor to Home Assistant that monitors the amount of files in a Google Drive folder.

> [!NOTE]
> Currently limited to the root folder of the Google Drive account.

## Installation
1. Clone this repository
2. Copy the contents of `custom_components` into your Home Assistant `config/custom_components` directory
3. Restart Home Assistant

### Home Assistant
1. Open `Settings`/`Devices & services`/`Add integration`
2. Search for and select `Google Drive Folder Sensor`
   > [!NOTE]
   > During the next step, you will encounter the [unverified app screen](https://support.google.com/cloud/answer/7454865#unverified-app-screen), as you're using your own credentials and accessing all files in your Google Drive. ([more info](https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification#exceptions))
3. Follow the prompts to authenticate with your Google account
4. Click `Submit`
5. Open `Settings`/`Automations & scenes`/`Create automation`
6. Select `Create new automation`
7. Under `When`, select `+ Add trigger`
8. Select the directory you want to monitor