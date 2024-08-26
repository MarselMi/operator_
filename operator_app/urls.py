from django.urls import path, re_path
from operator_app import views


urlpatterns = [
    # Вход-Выход
    path('login/', views.login_view, name='login'),
    re_path(r'^authmanager/', views.redirect_from_superadmin, name='auth_redirect'),
    path('logout/', views.logout, name='logout'),

    # Основные данные по клиенту, поиск и история действий
    path('history/', views.history_view, name='history'),
    path('charges/', views.charges_view, name='charges'),
    path('', views.main_search_view, name='general'),
    path('client/<int:client_id>/', views.client_page_view, name='client'),

    # Для обработки входящих звонков
    # re_path(r'^phone-call/', incoming_call_view, name='phone_call'),
    # path('call-send', socket_send_msg, name='call_send'),
]

handler404 = 'operator_app.views.page_not_found'
handler500 = 'operator_app.views.handler500'
handler501 = 'operator_app.views.handler501'
