import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_stripe_product(name: str) -> stripe.Product:
    """Создать продукт в Stripe."""
    return stripe.Product.create(name=name)


def create_stripe_price(product_id: str, amount: int) -> stripe.Price:
    """Создать цену в Stripe. amount — в копейках."""
    return stripe.Price.create(
        product=product_id,
        unit_amount=amount,
        currency='rub',
    )


def create_stripe_session(price_id: str, success_url: str) -> stripe.checkout.Session:
    """Создать checkout-сессию для оплаты.
    Параметр payment_method_types убран — Stripe берёт настройки из дашборда.
    """
    return stripe.checkout.Session.create(
        line_items=[{'price': price_id, 'quantity': 1}],
        mode='payment',
        success_url=success_url,
    )


def retrieve_stripe_session(session_id: str) -> stripe.checkout.Session:
    """Получить данные о сессии по id."""
    return stripe.checkout.Session.retrieve(session_id)