from datetime import datetime

from django.shortcuts import render
from rest_framework import generics, viewsets
from rest_framework.response import Response
from .models import *
from .serializers import *
from .tasks import run
from .service import check_bussines_interval
import logging

sending_logger = logging.getLogger('sending')


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
        check_bussines_interval(client_id=19, datetime_finish='', datetime_run='')
        return response
    
    def perform_create(self, serializer):
        sending_logger.info('Request has been sent to create Sending object. Method: POST, url: http://127.0.0.1:8000/sending/create/.')
        instance = serializer.save()
        sending_logger.info(f'''Sending ID - {instance.id} | Sending object saved.
                            datetime_run - {instance.datetime_run}, message - {instance.message}, phone_code_filter - {instance.phone_code_filter}, tag_filter - {instance.tag_filter}, datetime_finish - {instance.datetime_finish}''')
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

    def perform_update(self, serializer):
        instance = serializer.save()
        sending_logger.info(f'''Sending ID - {instance.id} | Sending object updated.
                            datetime_run - {instance.datetime_run}, message - {instance.message}, phone_code_filter - {instance.phone_code_filter}, tag_filter - {instance.tag_filter}, datetime_finish - {instance.datetime_finish}''')
        run.delay(send_id=instance.id,
                  datetime_run=instance.datetime_run,
                  message=instance.message,
                  phone_code_filter=instance.phone_code_filter,
                  tag_filter=instance.tag_filter,
                  datetime_finish=instance.datetime_finish)
        return Response({"message": "Object updated successfully"})    

class SendingDeleteView(generics.DestroyAPIView):
    queryset = Sending.objects.all()
    serializer_class = SendingSerializer

# message object
class MessageCreateView(generics.CreateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer