from celery import shared_task
from django.core.mail import send_mail
from .models import Order


@shared_task
def order_created(order_id):
    """
    Задание по отправке уведомлений по почте
     при успешном создании заказа
    """
    order = Order.objects.get(id=order_id)
    subject = f'Заказ номер: {order.id}'
    message = f' {order.first_name},\n\n' \
              f'Вы успешно оформили заказ.'
    mail_sent = send_mail(subject,
                          message,
                          'oenygina@gmail.com',
                          [order.email])
    return mail_sent