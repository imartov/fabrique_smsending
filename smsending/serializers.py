import pytz
from rest_framework import serializers
from .models import *
from django.db.models import Count




class ClientSerializer(serializers.ModelSerializer):
    timezone = serializers.ChoiceField(choices=pytz.all_timezones)
    read_only_fields = ('id',)
    class Meta:
        model = Client
        fields = ('id', 'phone_number', 'phone_code', 'tag', 'timezone', 'notificate_from', 'notificate_to')

    def validate(self, data):
        if data['notificate_from'] and data['notificate_to']:
            if data['notificate_from'] > data['notificate_to']:
                raise serializers.ValidationError("The notifications end time must occur after the notifications start time")
        return data

class SendingSerializer(serializers.ModelSerializer):
    messages = serializers.SerializerMethodField()
    read_only_fields = ('id', 'created_date', 'updated_date')
    class Meta:
        model = Sending
        fields = ['id', 'datetime_run', 'message', 'phone_code_filter', 'tag_filter',
                  'datetime_finish', 'messages', 'created_date', 'updated_date']

    def validate(self, data):
        if data['datetime_run'] and data['datetime_finish']:
            if data['datetime_run'] > data['datetime_finish']:
                raise serializers.ValidationError("The data and time end sending must occur after the data and time start sending")
        return data

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
