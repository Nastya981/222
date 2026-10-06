from django.core.exceptions import ValidationError
from urllib.parse import urlparse


def validate_youtube_url(value):
    """Разрешает ссылки только на youtube.com."""
    if not value:
        return
    parsed = urlparse(value)
    host = parsed.netloc.lower()
    if host.startswith('www.'):
        host = host[4:]
    if host not in ('youtube.com', 'youtu.be', 'm.youtube.com'):
        raise ValidationError(
            'Ссылка должна вести только на youtube.com. '
            'Ссылки на сторонние ресурсы запрещены.'
        )