import os
from enum import Enum

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


class SlackColor(Enum):
    GOOD = "good"
    DANGER = "danger"
    WARNING = "warning"
    INFO = "info"
    DEFAULT = "default"


def send_slack_message(
    message, color=SlackColor.DEFAULT.value, channel_id="#kafka_kibisis"
):
    slack_token = os.getenv("SLACK_TOKEN")
    client = WebClient(token=slack_token)
    attachment = [{"text": message, "color": color}]

    try:
        response = client.chat_postMessage(channel=channel_id, attachments=attachment)
        print("Message sent successfully:", response["ts"])
    except SlackApiError as e:
        print(f"Error sending message to Slack: {e.response['error']}")
