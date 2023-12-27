from datetime import datetime, timedelta
import uuid, json, numpy, requests

from django.core.mail import send_mail
from .models import *
from .serializers import MessageSerializer
import logging
import environ

logger = logging.getLogger('django')
env = environ.Env()
environ.Env.read_env()


def serv_send(phone_number:str, message:str) -> int:
    uniqid = get_uniq_id()
    url_send_mes = f'https://probe.fbrq.cloud/v1/send/{uniqid}'
    json_params = {
        "id": uniqid,
        "phone": int(phone_number),
        'text': message
    }
    headers = {
        'Authorization': env('API_TOKEN')
    }
    logger.info(f'''{datetime.now()} | Sending a message to a clients:
                id of message - {uniqid}, phone - {phone_number}''')
    logger.info(f'''{datetime.now()} | Sending an API request to url - {url_send_mes} and waiting a response.''')
    datetime_send = datetime.now()
    # response = requests.post(url=url_send_mes, json=json_params, headers=headers)
    # logger.info(f'{datetime.now()} | Response received. Status code of API request - {response.json()["code"]}.')
    logger.info(f'{datetime.now()} | Response received. Status code of API request - 200.')
    # return datetime_send, response.json()["code"]
    return datetime_send, 200

def serv_get_clients(phone_code:int, tag:str) -> list:
    logger.info(f'''{datetime.now()} | Client acquisition started by next filters:
                phone_code - {phone_code}, tag - {tag}.''')
    clients = list(Client.objects.filter(phone_code=phone_code).filter(tag=tag)\
    .values('id', 'phone_number', 'timezone'))
    logger.info(f'{datetime.now()} | Client acquisition completed. Count - {len(clients)}.')
    return clients

def serv_compare_time(send_id:int,
                      clients:list,
                      datetime_run:datetime,
                      datetime_finish:datetime) -> tuple:
    logger.info(f'{datetime.now()} | Sorting of clients has begun.')
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
    logger.info(f'''{datetime.now()} | Sorting of clients completed.
                Number of clients to whom messages will be sent now - {len(now_clients_list)}.
                Number of clients to whom messages will be scheduled to be sent - {len(delay_clients_list)}.''')
    if remove_list:
        now_clients_list = remove_clients(remove_list=remove_list, clients=now_clients_list)
        delay_clients_list = remove_clients(remove_list=remove_list, clients=delay_clients_list)
    return now_clients_list, delay_clients_list

def get_uniq_id() -> int:
    uniqint = uuid.uuid4().int & (1<<40)-1
    return numpy.int64(uniqint)

def serv_create_message(datetime_send:datetime,
                        status_send:int,
                        sms_sending:int,
                        client:int):
    logger.info(f'''{datetime.now()} | The creation of the Messages object and adding to the database has begun.
                 datetime_send - {datetime_send}, status_send - {status_send}, sms_sending_id - {sms_sending}, client_id - {client}.''')
    object_data = {
        'datetime_send': datetime_send,
        'status_send': status_send,
        'sms_sending': sms_sending,
        'client': client
    }
    serializer = MessageSerializer(data=object_data)

    if serializer.is_valid():
        serializer.save()
        logger.info(f'{datetime.now()} | The Messages object was successfully created and saved.')
    else:
        logger.info(f'''{datetime.now()} | Something went wrong while creating the object.
                    Validation failed:\n{serializer.errors}.''')
        
def check_bussines_interval(client_id:int, datetime_run:datetime, datetime_finish:datetime) -> tuple:
    logger.info(f'{datetime.now()} | Client ID - {client_id} | Start checking the client business intervals')
    # temp
    datetime_run, datetime_finish = get_sending(id=2)

    new_datetime_run = datetime_run
    new_datetime_finish = datetime_finish
    client = list(Client.objects.filter(id=client_id).values_list('notificate_from', 'notificate_to'))[0]    
    if client[0]:
        logger.info(f'{datetime.now()} | Client ID - {client_id} | The client has a business interval, the initial notification time - {client[0].strftime("%H:%M:%S")}.')
        if client[0] >= datetime_run.time():
            logger.info(f'''{datetime.now()} | Client ID - {client_id} | The start time of seinding is less than the business interval for starting notifications.
                        The sending start time for the client was successfully updated to {client[0].strftime("%H:%M:%S")}.''')
            new_datetime_run = datetime_run.replace(hour=client[0].hour, minute=client[0].minute)
            if new_datetime_run.time() < datetime_run.time() or new_datetime_run.time() > datetime_finish.time():
                logger.info(f'''{datetime.now()} | Client ID - {client_id} | The updated start time of sending is less than the original start time or greather than the sending end time.
                            The client will be removed from the list of recipients.''')
                new_datetime_run = None
    if not new_datetime_run:
        return new_datetime_run, new_datetime_finish
    if client[1]:
        logger.info(f'{datetime.now()} | Client ID - {client_id} | The client has a business interval, notification end time - {client[1].strftime("%H:%M:%S")}.')
        if client[1] <= datetime_finish.time():
            logger.info(f'''{datetime.now()} | Client ID - {client_id} | The business notification end interval is less than or equal to the sending end time.
                        The sending end time for the client was successfully updated to {client[1].strftime("%H:%M:%S")}.''')
            new_datetime_finish = datetime_finish.replace(hour=client[1].hour, minute=client[1].minute)
            if new_datetime_finish.time() > datetime_finish.time() or new_datetime_finish.time() < datetime_run.time():
                logger.info(f'''{datetime.now()} | Client ID - {client_id} | The updated end time of the sending is greather than original end time or less than the start time of the sending.
                            The client will be removed from the list of recipients..''')
                new_datetime_finish = None
    return new_datetime_run, new_datetime_finish

def remove_clients(send_id:int, remove_list:list, clients:list) -> list:
    logger.info(f'{datetime.now()} | Sending ID - {send_id} | Removing from the mailing list clients with ID {remove_list}.')
    new_clients = []
    for client in clients:
        if client['id'] not in remove_list:
            new_clients.append(client)
    logger.info(f'{datetime.now()} | Sending ID - {send_id} | Removal completed successfully.')
    return new_clients


# temp test
def get_sending(id:int) -> None:
    sending = list(Sending.objects.filter(id=id).values_list('datetime_run', 'datetime_finish'))[0]
    return sending


def main():
    pass

if __name__ == "__main__":
    main()