from django.db import models
from django.core.exceptions import ValidationError
from django.dispatch import receiver
from timezone_field import TimeZoneField


def phone_number_validator(value):
    """
    Custom validator to enforce a strong phone format.
    Format: 7XXXXXXXXXX
    """
    if len(value) != 11:
        raise ValidationError('The phone number must consist of 11 digits')
    if value[0] != "7":
        raise ValidationError('The phone number must start with 7')
    

class Sending(models.Model):
    datetime_run = models.DateTimeField()
    message = models.TextField()
    phone_code_filter = models.IntegerField()
    tag_filter = models.CharField(max_length=255)
    datetime_finish = models.DateTimeField()

    def __str__(self):
        return self.message[:10]


class Client(models.Model):
    phone_number = models.CharField(max_length=255, unique=True, validators=(phone_number_validator,))
    phone_code = models.IntegerField()
    tag = models.CharField(max_length=255)
    timezone = TimeZoneField(default='Europe/Moscow')
    notificate_from = models.TimeField(blank=True, null=True, verbose_name='Notificate from')
    notificate_to = models.TimeField(blank=True, null=True, verbose_name='Notificate to')

    def __str__(self):
        return f'{self.phone_number}-{self.tag}-{self.timezone}'


class Message(models.Model):
    datetime_send = models.DateTimeField(blank=True, null=True)
    status_send = models.IntegerField(blank=True, null=True)
    sms_sending = models.ForeignKey(Sending, on_delete=models.SET_NULL, null=True, related_name="smsending")
    client = models.ForeignKey(Client, on_delete=models.SET_NULL, null=True, related_name="client")

    def __str__(self):
        return f'{self.datetime_send}-{self.status_send}'