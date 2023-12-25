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

def serv_compare_time(clients:list,
                      datetime_run:datetime,
                      datetime_finish:datetime) -> tuple:
    logger.info(f'{datetime.now()} | Sorting of clients has begun.')
    now_clients_list = []
    delay_clients_list = []
    for client in clients:
        datetime_run_tz = datetime_run.replace(tzinfo=client['timezone'])
        datetime_finish_tz = datetime_finish.replace(tzinfo=client['timezone'])
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

# temp func
def get_test_sending(self):
    sending = list(Sending.objects.filter(id=4).values('id', 'datetime_run', 'datetime_finish'))
    return sending

# temp func
def service_send(subject:str, message:str, email:str):
    send_mail(subject, message, 'pythontest285@gmail.com',
        [email], fail_silently=False)

def main():
    pass

if __name__ == "__main__":
    main()