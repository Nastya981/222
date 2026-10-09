import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def send_telegram_message(chat_id: str, text: str) -> bool:
    """Отправка сообщения в Telegram через Bot API."""
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token:
        logger.warning('TELEGRAM_BOT_TOKEN не задан в настройках')
        return False

    if not chat_id:
        logger.warning('chat_id пустой')
        return False

    url = f'https://api.telegram.org/bot{token}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
    }

    # Отключаем системные прокси (иначе requests пытается использовать SOCKS)
    no_proxy = {'http': None, 'https': None}

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=10,
            proxies=no_proxy,
        )
        if response.status_code == 200:
            return True
        logger.error('Telegram API error: %s %s', response.status_code, response.text)
        return False
    except requests.RequestException as exc:
        logger.exception('Ошибка при запросе к Telegram: %s', exc)
        return False