from django.urls import path
from .views import *


urlpatterns = [
    # client
    path('client/create/', ClientCreateView.as_view(), name='client-create'), # http://127.0.0.1:8000/client/create/
    path('client/update/<int:pk>/', ClientUpdateView.as_view(), name='client-update'), # http://127.0.0.1:8000/client/update/{clientId}/
    path('client/delete/<int:pk>/', ClientDeleteView.as_view(), name='client-delete'), # http://127.0.0.1:8000/client/delete/{clientId}/

    # sending
    path('sending/get/', SendingListView.as_view(), name='sending-get'), # http://127.0.0.1:8000/sending/get/
    path('sending/detail/<int:pk>/', SendingDetailView.as_view(), name='sending-detail'), # http://127.0.0.1:8000/sending/detail/{sendingId}/
    # path('sending/create/', SendingCreateView.as_view(), name='sending-create'), # http://127.0.0.1:8000/sending/create/
    path('sending/create/', SendingViewSet.as_view({'post': 'create',
                                                    'get': 'list'}), name='sending-create'), # http://127.0.0.1:8000/sending/create/
    path('sending/update/<int:pk>/', SendingUpdateView.as_view(), name='client-update'), # http://127.0.0.1:8000/sending/update/{sendingId}/
    path('sending/delete/<int:pk>/', SendingDeleteView.as_view(), name='client-delete'), # http://127.0.0.1:8000/sending/delete/{sendingId}/

    # message
    path('message/create/', MessageCreateView.as_view(), name='message-create'), # http://127.0.0.1:8000/message/create/
]