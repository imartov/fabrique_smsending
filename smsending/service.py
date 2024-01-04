from datetime import datetime, timedelta

from django.db.models import Q
from .models import *
from .serializers import MessageSerializer
import logging
import environ
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from redmail import gmail

sending_logger = logging.getLogger('sending')
message_logger = logging.getLogger('message')
client_logger = logging.getLogger('client')

env = environ.Env()
environ.Env.read_env()


def serv_send(client_id:int, send_id:int, phone_number:str, message:str) -> int:

    client_logger.info(f'Client ID - {client_id} | Sending ID - {send_id} | Start sending a message.')
    sending_logger.info(f'Sending ID - {send_id} | Client ID - {client_id} | Start sending a message.')

    message_id = serv_create_message_and_get_id(datetime_send=datetime.now(), status_send=000,
                                                send_id=send_id, client_id=client_id)
    url_send_mes = f'https://probe.fbrq.cloud/v1/send/{message_id}'
    json_params = {
        "id": message_id,
        "phone": int(phone_number),
        'text': message
    }
    headers = {
        'Authorization': env('API_TOKEN')
    }

    sending_logger.info(f'Sending ID - {send_id} | Client ID - {client_id} | Sending an API request and waiting for a response.')
    client_logger.info(f'Client ID - {client_id} | Sending ID - {send_id} | Sending an API request and waiting for a response.')

    datetime_send = datetime.now()
    # response = requests.post(url=url_send_mes, json=json_params, headers=headers)

    sending_logger.info(f'Sending ID - {send_id} | Client ID - {client_id} | Response received successfully: status code - 200.')
    client_logger.info(f'Client ID - {client_id} | Sending ID - {send_id} | Response received successfully: status code - 200.')

    # return datetime_send, response.json()["code"]
    serv_update_message(message_id=message_id, datetime_send=datetime_send, status_send=200)
    return datetime_send, 200


def serv_get_clients(send_id:int, phone_code:int, tag:str) -> list:
    sending_logger.info(f'Sending ID - {send_id} | Retrieving a list of clients matching filters: phone_code - {phone_code}, tag - {tag}.')
    clients = list(Client.objects.filter(phone_code=phone_code).filter(tag=tag)\
    .values('id', 'phone_number', 'timezone'))
    sending_logger.info(f'Sending ID - {send_id} | Client list retrieved successfully. Number of clients - {len(clients)}.')
    return clients


def serv_compare_time(send_id:int, clients:list,
                      datetime_run:datetime, datetime_finish:datetime) -> tuple:
    sending_logger.info(f'Sending ID - {send_id} | Sorting of clients has begun.')
    now_clients_list = []
    delay_clients_list = []
    remove_list = []
    for client in clients:
        datetime_run_tz = datetime_run.replace(tzinfo=client['timezone'])
        datetime_finish_tz = datetime_finish.replace(tzinfo=client['timezone'])
        datetime_run_tz, datetime_finish_tz = check_bussines_interval(client_id=client['id'],
                                                                      datetime_run=datetime_run_tz,
                                                                      datetime_finish=datetime_finish_tz)
        if not datetime_run_tz or not datetime_finish_tz:
            remove_list.append(client['id'])

        client['datetime_run'] = datetime_run_tz
        client['datetime_finish'] = datetime_finish_tz
        now_tz = datetime.now().astimezone(client['timezone'])
        if now_tz >= datetime_run_tz and now_tz <= datetime_finish_tz:
            now_clients_list.append(client)
        elif datetime_run_tz > now_tz:
            delay_clients_list.append(client)
    sending_logger.info(f''' Sending ID - {send_id} | Sorting of clients completed.
                Number of clients to whom messages will be sent now - {len(now_clients_list)}.
                Number of clients to whom messages will be scheduled to be sent - {len(delay_clients_list)}.''')
    if remove_list:
        now_clients_list = remove_clients(remove_list=remove_list, clients=now_clients_list)
        delay_clients_list = remove_clients(remove_list=remove_list, clients=delay_clients_list)
    return now_clients_list, delay_clients_list


def serv_create_message_and_get_id(datetime_send:datetime, status_send:int,
                                   send_id:int, client_id:int):
    message_logger.info(f'Сreating a message object. Sending ID - {send_id} | Client ID - {client_id}.')
    object_data = {
        'datetime_send': datetime_send,
        'status_send': status_send,
        'sms_sending': send_id,
        'client': client_id
    }
    serializer = MessageSerializer(data=object_data)

    if serializer.is_valid():
        instance = serializer.save()
        created_message_id = instance.id
        message_logger.info(f'Message ID - {created_message_id} | Message object successfully created and saved.')
        return created_message_id
    else:
        message_logger.error(f'The message object was not created because it received invalid data.')
    

def serv_update_message(message_id:int, datetime_send:datetime, status_send:int) -> None:
    message_logger.info(f'Message ID - {message_id} | Update the message object. Adding data: datetime_send - {datetime_send}, status_send - {status_send}.')
    instance = Message.objects.get(id=message_id)
    instance.datetime_send = datetime_send
    instance.status_send = status_send
    instance.save()
    message_logger.info(f'Message ID - {message_id} | Message object successfully updated.')


def check_bussines_interval(client_id:int, datetime_run:datetime, datetime_finish:datetime) -> tuple:
    client_logger.info(f'Client ID - {client_id} | Start checking the client business intervals')
    # temp
    # datetime_run, datetime_finish = get_sending(id=2)

    new_datetime_run = datetime_run
    new_datetime_finish = datetime_finish
    client = list(Client.objects.filter(id=client_id).values_list('notificate_from', 'notificate_to'))[0]    
    if client[0]:
        client_logger.info(f'{datetime.now()} | Client ID - {client_id} | The client has a business interval, the initial notification time - {client[0].strftime("%H:%M:%S")}.')
        if client[0] >= datetime_run.time():
            client_logger.info(f'''{datetime.now()} | Client ID - {client_id} | The start time of seinding is less than the business interval for starting notifications.
                                The sending start time for the client was successfully updated to {client[0].strftime("%H:%M:%S")}.''')
            new_datetime_run = datetime_run.replace(hour=client[0].hour, minute=client[0].minute)
            if new_datetime_run.time() < datetime_run.time() or new_datetime_run.time() > datetime_finish.time():
                client_logger.info(f'''{datetime.now()} | Client ID - {client_id} | The updated start time of sending is less than the original start time or greather than the sending end time.
                                    The client will be removed from the list of recipients.''')
                new_datetime_run = None
    if not new_datetime_run:
        return new_datetime_run, new_datetime_finish
    if client[1]:
        client_logger.info(f'{datetime.now()} | Client ID - {client_id} | The client has a business interval, notification end time - {client[1].strftime("%H:%M:%S")}.')
        if client[1] <= datetime_finish.time():
            client_logger.info(f'''{datetime.now()} | Client ID - {client_id} | The business notification end interval is less than or equal to the sending end time.
                                The sending end time for the client was successfully updated to {client[1].strftime("%H:%M:%S")}.''')
            new_datetime_finish = datetime_finish.replace(hour=client[1].hour, minute=client[1].minute)
            if new_datetime_finish.time() > datetime_finish.time() or new_datetime_finish.time() < datetime_run.time():
                client_logger.info(f'''{datetime.now()} | Client ID - {client_id} | The updated end time of the sending is greather than original end time or less than the start time of the sending.
                                    The client will be removed from the list of recipients..''')
                new_datetime_finish = None
    return new_datetime_run, new_datetime_finish


def remove_clients(send_id:int, remove_list:list, clients:list) -> list:
    sending_logger.info(f'| Sending ID - {send_id} | Removing from the mailing list clients with ID {remove_list}.')
    new_clients = []
    for client in clients:
        if client['id'] not in remove_list:
            new_clients.append(client)
    sending_logger.info(f'{datetime.now()} | Sending ID - {send_id} | Removal completed successfully.')
    return new_clients


class SendStat:
    def __init__(self) -> None:
        pass

    def get_stat(self, by_date=datetime.now() - timedelta(days=1)) -> dict:
        time_slots = {
            "Ночь": {
                "from": datetime.strptime("00:01", "%H:%M"),
                "to": datetime.strptime("07:59", "%H:%M"),
            },
            "Утро": {
                "from": datetime.strptime("08:00", "%H:%M"),
                "to": datetime.strptime("09:59", "%H:%M"),
            },
            "Позднее утро": {
                "from": datetime.strptime("10:00", "%H:%M"),
                "to": datetime.strptime("11:59", "%H:%M"),
            },
            "Обед": {
                "from": datetime.strptime("12:00", "%H:%M"),
                "to": datetime.strptime("13:59", "%H:%M"),
            },
            "Поздний обед": {
                "from": datetime.strptime("14:00", "%H:%M"),
                "to": datetime.strptime("16:59", "%H:%M"),
            },
            "Вечер": {
                "from": datetime.strptime("17:00", "%H:%M"),
                "to": datetime.strptime("20:59", "%H:%M"),
            },
            "Поздний вечер": {
                "from": datetime.strptime("21:00", "%H:%M"),
                "to": datetime.strptime("23:59", "%H:%M"),
            },
        }

        count_time_slots = {"Ночь": 0, "Утро": 0, "Позднее утро": 0, "Обед": 0, "Поздний обед": 0, "Вечер": 0, "Поздний вечер": 0}

        created_sendings_count = Sending.objects.filter(created_date__date=by_date).count()
        sent_messages_count = Message.objects.filter(datetime_send__date=by_date).count()
        success_sent_messages_count = Message.objects.filter(datetime_send__date=by_date).filter(status_send=200).count()

        if success_sent_messages_count and sent_messages_count:
            success_precent = success_sent_messages_count / sent_messages_count * 100
        else:
            success_precent = "No sent messages"

        datetime_sent_messages = list(Message.objects.filter(datetime_send__date=by_date).values_list('datetime_send'))
        for datetime_message in datetime_sent_messages:
            datetime_message = datetime_message[0].time()
            if datetime_message >= time_slots["Ночь"]['from'].time() and datetime_message <= time_slots["Ночь"]['to'].time():
                count_time_slots["Ночь"] += 1
            if datetime_message >= time_slots["Утро"]['from'].time() and datetime_message <= time_slots["Утро"]['to'].time():
                count_time_slots["Утро"] += 1
            if datetime_message >= time_slots["Позднее утро"]['from'].time() and datetime_message <= time_slots["Позднее утро"]['to'].time():
                count_time_slots["Позднее утро"] += 1
            if datetime_message >= time_slots["Обед"]['from'].time() and datetime_message <= time_slots["Обед"]['to'].time():
                count_time_slots["Обед"] += 1
            if datetime_message >= time_slots["Поздний обед"]['from'].time() and datetime_message <= time_slots["Поздний обед"]['to'].time():
                count_time_slots["Поздний обед"] += 1
            if datetime_message >= time_slots["Вечер"]['from'].time() and datetime_message <= time_slots["Вечер"]['to'].time():
                count_time_slots["Вечер"] += 1
            if datetime_message >= time_slots["Поздний вечер"]['from'].time() and datetime_message <= time_slots["Поздний вечер"]['to'].time():
                count_time_slots["Поздний вечер"] += 1

        max_key_count = max(count_time_slots, key=count_time_slots.get)
        if count_time_slots[max_key_count]:
            time_slots_precent = count_time_slots[max_key_count] / sent_messages_count * 100
        else:
            time_slots_precent = "No sent messages"

        context_data = {
            "created_sendings_count": created_sendings_count,
            "sent_messages_count": sent_messages_count,
            "success_precent": success_precent
        }
        time_slot = {
            "label": max_key_count,
            "time_slot_from": time_slots[max_key_count]["from"].strftime("%H:%M"),
            "time_slot_to": time_slots[max_key_count]["to"].strftime("%H:%M"),
            "precent": time_slots_precent
        }
        return context_data, time_slot

    def get_sended_and_sheduled_messages(self, sendings:dict) -> tuple:
        sended_messages = []
        sheduled_messages = []
        for sending in sendings:
            send_messages = list(Message.objects.filter(sms_sending=sending['id']).filter(~Q(status_send=000))\
                .values('id', 'datetime_send', 'status_send', 'client'))
            if send_messages:
                sended_messages.append(
                    {
                    "sending_id": sending['id'],
                    "messages": send_messages
                    }
                )
            shed_messages = list(Message.objects.filter(sms_sending=sending['id']).filter(status_send=000)\
                .values('id', 'datetime_send', 'status_send', 'client'))
            if shed_messages:
                sheduled_messages.append(
                    {
                        "sending_id": sending['id'],
                        "messages": shed_messages
                    }
                )
        if not sended_messages:
            sended_messages = "No sended messages"
        if not sheduled_messages:
            sheduled_messages = "No sheduled messages"
        return sended_messages, sheduled_messages

    def get_sent_messages(self, datetime_send=datetime.now().date()) -> dict:
        today_sent_messages = list(Message.objects.filter(datetime_send__date=datetime_send).values('datetime_send', 'status_send', 'sms_sending', 'client'))
        new_today_sent_messages = []
        for message in today_sent_messages:
            sending = list(Sending.objects.filter(Q(created_date__date__lt=datetime_send) | Q(updated_date__date__lt=datetime_send))\
                .filter(id=message['sms_sending']).values('id', 'message','created_date', 'updated_date'))[0]
            if sending:
                message["sending"] = {
                    "send_id": sending['id'],
                    "message": sending['message'],
                    "created_date": sending['created_date'],
                    "updated_date": sending['updated_date'],
                }
                new_today_sent_messages.append(message)
            return new_today_sent_messages if new_today_sent_messages else "No messages"

    def send_redmail(self, context_data:dict, time_slot:dict) -> None:
        gmail.username = env('DEFAULT_FROM_EMAIL')
        gmail.password = env('EMAIL_HOST_PASSWORD')
        with open('smsending\\templates\\stat_cid_rmail.html', 'r', encoding='utf-8') as file:
            html_content = file.read()
        gmail.send(
            subject="Fabrique | Daily statistics on Sendings",
            receivers=[env('DEFAULT_FROM_EMAIL')],
            html=html_content,
            body_images={
                "corp_logo": "smsending\\templates\\static\\img\\corplogo_2.png",
                "inst_icon": "smsending\\templates\\static\\img\\instagram-icon.png",
                "link_icon": "smsending\\templates\\static\\img\\linkedin-icon.png",
                "site_icon": "smsending\\templates\\static\\img\\site-icon.png",
            },
            body_params={
                "context_data": context_data,
                "time_slot": time_slot,
            }
        )

    def run(self) -> None:
        context_data, time_slot = self.get_stat()
        self.send_redmail(context_data, time_slot)


def main():
    pass

if __name__ == "__main__":
    main()