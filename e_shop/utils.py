import json
import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives

def generate_sslcommerz_payment(order, request):

    post_data = {
        'store_id': settings.SSLCOMMERZ_STORE_ID,
        'store_passwd': settings.SSLCOMMERZ_STORE_PASSWORD,
        'total_amount': float(order.get_total_cost()),
        'currency': 'BDT',
        'tran_id': str(order.id),

        'success_url': request.build_absolute_uri(f'/payment/success/{order.id}/'),
        'fail_url': request.build_absolute_uri(f'/payment/fail/{order.id}/'),
        'cancel_url': request.build_absolute_uri(f'/payment/cancel/{order.id}/'),

        'cus_name': f"{order.first_name} {order.last_name}",
        'cus_email': order.email,
        'cus_add1': order.address,
        'cus_city': order.city,
        'cus_postcode': order.postal_code,
        'cus_country': 'Bangladesh',

        'shipping_method': 'NO',

        'product_name': 'Products from our store',
        'product_category': 'General',
        'product_profile': 'general',
    }

    response = requests.post(
        settings.SSLCOMMERZ_PAYMENT_URL,
        data=post_data
    )
    print("STATUS:", response.status_code)
    print("BODY:", response.text)

    return response.json()

def send_order_confirmation_email(order):
    subject = f"Order Confirmation - Order #{order.id}"
    message = render_to_string(
        'e_shop/email/order_confirmation.html',
        {'order': order}
    )
    to = order.email

    email = EmailMultiAlternatives(subject, '', to=[to])
    email.attach_alternative(message, "text/html")
    email.send()

# def send_order_confirmation_email(order):
#     subject = f"Order Confirmation - Order #{order.id}"
#     message = render_to_string('e_shop/email/order_confirmation.html',{'order':order})
#     to = order.email
#     send_email = EmailMultiAlternatives(subject,'',to=[to])
#     send_email.attach_alternative(message,"text/html")
#     send_email.save()