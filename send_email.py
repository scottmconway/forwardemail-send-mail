#!/usr/bin/env python3

# Simple script to send an email with ForwardEmail
#
# If the sending alias does not exist,
# this script will attempt to create it, send mail with it, and delete it.
#
# The sending domain must have a catch-all rule configured
# so that we can specify a valid "recipient" parameter for the new alias.

import argparse
import json
import logging

import requests
from requests.adapters import HTTPAdapter, Retry
from requests.exceptions import HTTPError

APP_NAME = "forward_email_send_email"

parser = argparse.ArgumentParser()
parser.add_argument("sending_address", type=str, help="sender email address")
parser.add_argument(
    "recipient_addresses", nargs="+", type=str, help="(one or more) recipient email addresses"
)
parser.add_argument("subject", type=str, help="email subject")
parser.add_argument("text", type=str, help="email text")
parser.add_argument(
    "--config",
    type=str,
    default="config.json",
    help="Path to config file - defaults to ./config.json",
)
parser.add_argument(
    "--api-token",
    type=str,
    help="API token override if not specified in config file (or if no config is specified)",
)
args = parser.parse_args()

try:
    with open(args.config, "r") as f:
        config = json.load(f)
except:
    config = dict()

logger = logging.getLogger(APP_NAME)
logging_conf = config.get("logging", dict())
logger.setLevel(logging_conf.get("log_level", logging.INFO))
if "gotify" in logging_conf:
    from gotify_handler import GotifyHandler

    logger.addHandler(GotifyHandler(**logging_conf["gotify"]))

forward_email_session = requests.Session()
forward_email_session.auth = (
    (args.api_token, "") if args.api_token else (config.get("api_token", ""), "")
)

forward_email_session.mount(
    "https://",
    HTTPAdapter(
        max_retries=Retry(
            total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
        )
    ),
)


def send_email(from_address: str, to_addresses: list[str], subject: str, text: str):
    return forward_email_session.post(
        "https://api.forwardemail.net/v1/emails",
        data={
            "from": from_address,
            "to": to_addresses,
            "subject": subject,
            "text": text,
        },
    )


def main():
    send_res = send_email(args.from_email, [args.to_email], args.subject, args.text)
    logger.debug(f"send_email - {send_res.status_code}")

    if send_res.json().get("message", "") == "Alias does not exist on the domain.":
        sending_username = args.from_email.split("@")[:-1]
        sending_domain = args.from_email.split("@")[-1]
        try:
            aliases_res = forward_email_session.get(
                f"https://api.forwardemail.net/v1/domains/{sending_domain}/aliases"
            )
            aliases_res.raise_for_status()
        except HTTPError:
            logger.exception("HTTPError listing aliases, exiting")
            return

        catchall_alias = None
        for alias in aliases_res.json():
            if alias["name"] == "*":
                catchall_alias = alias
                break

        if not catchall_alias:
            logger.error(
                f"Alias does not exist and no catch-all alias exsits for domain {sending_domain}, exiting"
            )
            return

        else:
            # create a new alias with the config of the catchall under the sending_email's username
            alias_create_res = forward_email_session.post(
                f"https://api.forwardemail.net/v1/domains/{sending_domain}/aliases",
                data={
                    "name": sending_username,
                    "recipients": catchall_alias["recipients"],
                    "description": "auto-generated alias created by send_email",
                    "labels": [
                        label
                        for label in catchall_alias["labels"]
                        if label != "catch-all"
                    ],
                    "has_recipient_verification": catchall_alias[
                        "has_recipient_verification"
                    ],
                    "is_enabled": True,
                },
            )
            try:
                alias_create_res.raise_for_status()
            except HTTPError:
                logger.exception("HTTPError creating alias, exiting")
                return

            # send email
            send_res = send_email(
                args.from_email, [args.to_email], args.subject, args.text
            )
            logger.debug(f"send_email - {send_res.status_code}")
            try:
                send_res.raise_for_status()
            except HTTPError:
                logger.exception("HTTPError sending email, exiting")
                return

            # delete alias
            delete_res = forward_email_session.delete(
                f"https://api.forwardemail.net/v1/domains/{sending_domain}/aliases/{alias_create_res.json()['id']}"
            )
            try:
                delete_res.raise_for_status()
            except HTTPError:
                logger.warning(f'HTTPError deleting alias "{args.from_email}"')

    else:
        try:
            send_res.raise_for_status()
        except HTTPError:
            logger.exception("HTTPError sending email, exiting")


if __name__ == "__main__":
    main()
