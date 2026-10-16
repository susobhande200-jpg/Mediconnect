from django.urls import path
from . import views
urlpatterns = [
    path("book/", views.book, name="appointment_book"),
    path("<int:pk>/cancel/", views.cancel, name="appointment_cancel"),
    path("<int:pk>/action/<str:action>/", views.staff_appointment_action, name="staff_appointment_action"),
    path("<int:pk>/chat/", views.chat, name="appointment_chat"),
    path("<int:pk>/clinical-note/", views.clinical_note, name="clinical_note"),
    path("<int:pk>/prescription/", views.create_prescription, name="create_prescription"),
    path("<int:pk>/payment/", views.request_payment, name="request_payment"),
    path("payments/<int:pk>/<str:action>/", views.payment_action, name="payment_action"),
    path("<int:pk>/razorpay/", views.razorpay_checkout, name="razorpay_checkout"),
    path("razorpay/webhook/", views.razorpay_webhook, name="razorpay_webhook"),
]
