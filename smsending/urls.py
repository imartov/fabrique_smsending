from django.urls import path
from .views import *


urlpatterns = [
    # client
    path('client/create/', ClientViewSet.as_view({'post': 'create'}), name='client-create'), # http://127.0.0.1:8000/fabrique-smsending/api/v1/client/create/
    path('client/update/<int:pk>/', ClientUpdateView.as_view(), name='client-update'), # http://127.0.0.1:8000/fabrique-smsending/api/v1/client/update/{clientId}/
    path('client/delete/<int:pk>/', ClientDeleteView.as_view(), name='client-delete'), # http://127.0.0.1:8000/fabrique-smsending/api/v1/client/delete/{clientId}/

    # sending
    path('sendings/get/', SendingListView.as_view(), name='sending-get'), # http://127.0.0.1:8000/fabrique-smsending/api/v1/sendings/get/
    path('sending/detail/<int:pk>/', SendingDetailView.as_view(), name='sending-detail'), # http://127.0.0.1:8000/fabrique-smsending/api/v1/sending/detail/{sendingId}/
    # path('sending/create/', SendingCreateView.as_view(), name='sending-create'), # http://127.0.0.1:8000/fabrique-smsending/api/v1/sending/create/
    path('sending/create/', SendingViewSet.as_view({'post': 'create',
                                                    'get': 'list'}), name='sending-create'), # http://127.0.0.1:8000/fabrique-smsending/api/v1/sending/create/
    path('sending/update/<int:pk>/', SendingUpdateView.as_view(), name='client-update'), # http://127.0.0.1:8000/fabrique-smsending/api/v1/sending/update/{sendingId}/
    path('sending/delete/<int:pk>/', SendingDeleteView.as_view(), name='client-delete'), # http://127.0.0.1:8000/fabrique-smsending/api/v1/sending/delete/{sendingId}/

    # message
    path('message/create/', MessageCreateView.as_view(), name='message-create'), # http://127.0.0.1:8000/fabrique-smsending/api/v1/message/create/

    # docs
    path('docs/', redirect_docs, name='redirect-docs'), # http://127.0.0.1:8000/fabrique-smsending/api/v1/docs/
]