import pytz
from rest_framework import serializers
from .models import *
from django.db.models import Count




class ClientSerializer(serializers.ModelSerializer):
    timezone = serializers.ChoiceField(choices=pytz.all_timezones)
    read_only_fields = ('id',)
    class Meta:
        model = Client
        fields = ('phone_number', 'phone_code', 'tag', 'timezone', 'notificate_from', 'notificate_to')

class SendingSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()
    class Meta:
        model = Sending
        fields = ['id', 'datetime_run', 'message', 'phone_code_filter', 'tag_filter', 'datetime_finish', 'messages']

    def get_messages(self, obj):
        all_count = Message.objects.filter(sms_sending=obj).count()
        if all_count == 0:
            return "No sended messages"
        group_status = Message.objects.filter(sms_sending=obj).values('status_send').annotate(count=Count('status_send'))
        return {
            "count": all_count,
            "status_detail": group_status
        }

class SendingDetailSerializer(SendingSerializer):
    messages = serializers.SerializerMethodField()
    class Meta:
        model = Sending
        fields = ['id', 'datetime_run', 'message', 'phone_code_filter', 'tag_filter', 'datetime_finish', 'messages']
    
    def get_messages(self, obj):
        all_count = Message.objects.filter(sms_sending=obj).count()
        if all_count == 0:
            return "No sended messages"
        messages = Message.objects.filter(sms_sending=obj).values('datetime_send', 'status_send', 'client')
        return {
            "count": all_count,
            "messages": messages,
        }

class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
