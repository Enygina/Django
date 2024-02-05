import uuid
from decimal import Decimal

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import reverse
from yookassa import Configuration, Payment

from cart.cart import Cart

from orders.forms import ShippingAddressForm
from orders.models import Order, OrderItem, ShippingAddress

# созданиие экземпляра yookassa
Configuration.account_id = settings.YOOKASSA_SHOP_ID
Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


def complete_order(request):
    if request.method == 'POST':
        payment_type = request.POST.get('yookassa-payment')

        name = request.POST.get('name')
        email = request.POST.get('email')
        street_address = request.POST.get('street_address')
        apartment_address = request.POST.get('apartment_address')
        country = request.POST.get('country')
        zip = request.POST.get('zip')
        cart = Cart(request)
        total_price = cart.get_total_price()

        shipping_address, _ = ShippingAddress.objects.get_or_create(
            user=request.user,
            defaults={
                'name': name,
                'email': email,
                'street_address': street_address,
                'apartment_address': apartment_address,
                'country': country,
                'zip': zip
            }
        )

    idempotence_key = uuid.uuid4()

    currency = 'RUB'
    description = 'Товары в корзине'
    payment = Payment.create({
        "amount": {
            "value": str(total_price * 93),
            "currency": currency
        },
        "confirmation": {
            "type": "redirect",
            "return_url": request.build_absolute_uri(reverse('payment:payment-success')),
        },
        "capture": True,
        "test": True,
        "description": description,
    }, idempotence_key)

    confirmation_url = payment.confirmation.confirmation_url

    if request.user.is_authenticated:
        order = Order.objects.create(
            user=request.user, shipping_address=shipping_address, amount=total_price)

        for item in cart:
            OrderItem.objects.create(
                order=order, product=item['product'], price=item['price'], quantity=item['qty'],
                user=request.user)

        return redirect(confirmation_url)

    else:
        order = Order.objects.create(
            shipping_address=shipping_address, amount=total_price)

        for item in cart:
            OrderItem.objects.create(
                order=order, product=item['product'], price=item['price'], quantity=item['qty'])


def payment_success(request):
    return render(request, 'payment/payment-success.html')


def payment_fail(request):
    return render(request, 'payment/payment-fail.html')
