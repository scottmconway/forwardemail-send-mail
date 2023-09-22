# ForwardEmail Send Email 
A simple script to send email using ForwardEmail's API 

ForwardEmail requires that the sending alias exists (catch-all aliases don't count),
so this script will do the following if the sending alias does not exist:
* Read all aliases for the domain, and check for a catch-all rule
* If a catch-all rule exists, create the named sending alias with the same forwarding settings as the catch-all alias
* Send the email agian
* Delete the sending alias

If a catch-all rule does not exist for the sending domain, the program will exit without sending an email.

## Requirements
* python3
* see requirements.txt

## Quickstart
* Set up a domain with [ForwardEmail](https://forwardemail.net/)
* Configure the domain for [sending mail via SMTP](https://forwardemail.net/en/guides/send-email-with-custom-domain-smtp#smtp-instructions)
* Retrieve your API token from [My Account -> Security -> Developer Access](https://forwardemail.net/en/my-account/security)
* Enter your API token in `config.json`, using `config.json.example` as a template
* Configure logging as you wish
* Run `./send_email.py` with your preferred arguments

## Configuration Setup
See `config.json.example` for an example configuration file.

## Arguments
|Short Name|Long Name|Type|Description|
|-|-|-|-|
||`sending_address`|`str`|sender email address|
||`recipient_addresses`|`List[str]`|(one or more) recipient email addresses|
||`subject`|`str`|email subject|
||`text`|`str`|email text|
||`--config`|`str`|Path to config file - defaults to `./config.json`|
||`--api-token`|`str`|API token override if not specified in config file (or if no config is specified)|
