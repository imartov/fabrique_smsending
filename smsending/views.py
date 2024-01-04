from datetime import datetime

from django.shortcuts import render
from rest_framework import generics, viewsets, status
from rest_framework.response import Response
from django.shortcuts import redirect
from .models import *

from .serializers import *
from .tasks import run_send_and_sheduled_messages
from .service import SendStat
import logging

sending_logger = logging.getLogger('sending')
client_logger = logging.getLogger('client')


# client object
class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def perform_create(self, serializer):
        client_logger.info('Request has been sent to create Client object. Method: POST, url: http://127.0.0.1:8000/fabrique-smsending/api/v1/client/create/.')
        instance = serializer.save()
        client_logger.info(f'''Client ID - {instance.id} | The object was successfully created and saved.
                           {instance.phone_number} | {instance.phone_code} | {instance.tag} | {instance.timezone} | {instance.notificate_from} | {instance.notificate_to}''')
        return Response(serializer.data)

class ClientUpdateView(generics.UpdateAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def perform_update(self, serializer):
        instance = serializer.save()
        client_logger.info(f'Client ID - {instance.id} | Client object updated successfully.')
        return Response({"message": "Object updated successfully"})  

class ClientDeleteView(generics.DestroyAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        client_logger.info(f'Client ID - {instance.id} | Client object deleted successfully.')
        return Response({"detail": "Object deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

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
        sending_logger.info('Request has been sent to create Sending object. Method: POST, url: http://127.0.0.1:8000/fabrique-smsending/api/v1/sending/create/.')
        instance = serializer.save()
        sending_logger.info(f'''Sending ID - {instance.id} | Sending object saved.
                            {instance.datetime_run} | {instance.message} | {instance.phone_code_filter} | {instance.tag_filter} | {instance.datetime_finish}''')
        run_send_and_sheduled_messages.delay(send_id=instance.id,
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
                            {instance.datetime_run} | {instance.message} | {instance.phone_code_filter} | {instance.tag_filter} | {instance.datetime_finish}''')
        run_send_and_sheduled_messages.delay(send_id=instance.id,
                                             datetime_run=instance.datetime_run,
                                             message=instance.message,
                                             phone_code_filter=instance.phone_code_filter,
                                             tag_filter=instance.tag_filter,
                                             datetime_finish=instance.datetime_finish)
        return Response({"message": "Object updated successfully"})    

class SendingDeleteView(generics.DestroyAPIView):
    queryset = Sending.objects.all()
    serializer_class = SendingSerializer

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        sending_logger.info(f'Sending ID - {instance.id} | Sending object deleted successfully.')
        return Response({"detail": "Object deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# message object
class MessageCreateView(generics.CreateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer


def redirect_docs(request):
    return redirect("https://app.swaggerhub.com/apis/ALEXANDRKOSYREW/fabrique_smsending/2#/")