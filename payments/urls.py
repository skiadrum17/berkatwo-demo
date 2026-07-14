from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('dashboard/invoices/', views.invoice_list_view, name='invoice_list'),
    path('dashboard/create/', views.create_invoice_view, name='create_invoice'),
    path('dashboard/edit-info/', views.edit_info_view, name='edit_info'),
    path('dashboard/invoice/<str:nomor_invoice>/', views.admin_invoice_view, name='admin_invoice'),
    path('dashboard/invoice/<str:nomor_invoice>/print/', views.print_invoice_view, name='print_invoice'),
    path('invoice/<str:nomor_invoice>/', views.client_portal_view, name='client_portal'),
]
