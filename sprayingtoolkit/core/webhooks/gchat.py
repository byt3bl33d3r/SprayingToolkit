import requests
import logging

# https://developers.google.com/hangouts/chat/quickstart/incoming-bot-python
def gchat(webhook_url, target, sprayer):
    logging.debug('notifying gchat webhook of popped account(s)')

    bot_message = {
        'text': f'Popped {len(sprayer.valid_accounts)} {str(sprayer)} accounts! (Target: {target})'
    }

    message_headers = {'Content-Type': 'application/json; charset=UTF-8'}

    requests.post(webhook_url, headers=message_headers, json=bot_message)
