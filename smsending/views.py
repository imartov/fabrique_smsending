from datetime import datetime

from django.shortcuts import render
from rest_framework import generics, viewsets
from rest_framework.response import Response
from .models import *
from .serializers import *
from .service import ApiSending
# from .tasks import run_sending, delay_run
from .tasks import run
import logging

logger = logging.getLogger('django')


# client object
class ClientCreateView(generics.CreateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

class ClientUpdateView(generics.UpdateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

class ClientDeleteView(generics.DestroyAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

# sending object
class SendingListView(generics.ListAPIView):
    queryset = Sending.objects.all()
    serializer_class = SendingSerializer

class SendingDetailView(generics.RetrieveAPIView):
    queryset = Sending.objects.all()
    serializer_class = SendingDetailSerializer
    
class SendingViewSet(viewsets.ModelViewSet):
    queryset = Sending.objects.all()
    serializer_class = SendingSerializer

    # temp func
    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return response
    
    def perform_create(self, serializer):
        logger.info(f'{datetime.now()} | Request has been sent to create Sending object.\n/
                    Method: POST, url: http://127.0.0.1:8000/sending/create/.')
        instance = serializer.save()
        logger.info(f'{datetime.now()} | Sending object saved.\n/
                    Id - {instance.id}, datetime_run - {instance.datetime_run},/
                    message - {instance.message}, phone_code_filter - {instance.phone_code_filter},/
                    tag_filter - {instance.tag_filter}, datetime_finish - {instance.datetime_finish}')
        run.delay(send_id=instance.id,
                  datetime_run=instance.datetime_run,
                  message=instance.message,
                  phone_code_filter=instance.phone_code_filter,
                  tag_filter=instance.tag_filter,
                  datetime_finish=instance.datetime_finish)
        instance.save()
        return Response(serializer.data)


class SendingUpdateView(generics.UpdateAPIView):
    queryset = Sending.objects.all()
    serializer_class = SendingSerializer

class SendingDeleteView(generics.DestroyAPIView):
    queryset = Sending.objects.all()
    serializer_class = SendingSerializer

# message object
class MessageCreateView(generics.CreateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer