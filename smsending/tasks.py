from datetime import datetime

from django.core.mail import send_mail
from celery import shared_task
import pytz
import logging

from config.celery import app
import service

logger = logging.getLogger('django')

@shared_task
def send(phone_number:str, message:str) -> int:
    return datetime.now(), service.send(phone_number=phone_number, message=message)

@app.task
def now_countdown(send_id:int, clients:list, message:str) -> None:
    logger.info(f'{datetime.now()} | Sending to clients has begun.')
    clients_couter = 0
    for client in clients:
        now_tz = datetime.now().astimezone(client['timezone'])
        if now_tz > client['datetime_finish']:
            logger.info(f'{datetime.now()} | Sending to clients was forcibly stopped because the sending time has expired.\n/
                        Number of messages sent - {clients_couter}, not sent - {len(clients) - clients_couter}.')
            break
        else:
            datetime_send, status_send = send(phone_number=client['phone_number'], message=message)
            clients_couter += 1
            create_message(datetime_send=datetime_send,
                           status_send=status_send,
                           sms_sending=send_id,
                           client=client['id'])
    logger.info(f'{datetime.now()} | Sending to clients completed.')

@app.task
def delay_countdown(send_id:int, clients:list, message:str) -> None:
    logger.info(f'{datetime.now()} | Sheduling for sending messages has begun.')
    for client in clients:
        exec_time = client['datetime_run'].astimezone(pytz.utc)
        datetime_send, status_send = send.apply_async(args=[client["phone_number"], message], eta=exec_time)
        logger.info(f'{datetime.now()} | Sending a message to the client is scheduled for {exec_time}.')
        create_message(datetime_send=datetime_send,
                       status_send=status_send,
                       sms_sending=send_id,
                       client=client['id'])
    logger.info(f'{datetime.now()} | Sheduling for sending messages completed.')

@app.task
def get_clients(phone_code:int, tag:str) -> list:
    return service.get_clients(phone_code=phone_code, tag=tag)

@app.task
def compare_time(clients:list,
                 datetime_run:datetime,
                 datetime_finish:datetime) -> list:
    return service.compare_time(clients=clients,
                                datetime_run=datetime_run,
                                datetime_finish=datetime_finish)

@shared_task
def create_message(datetime_send:datetime,
                   status_send:int,
                   sms_sending:int,
                   client:int):
    service.create_message(datetime_send=datetime_send,
                           status_send=status_send,
                           sms_sending=sms_sending,
                           client=client)

@app.task
def run(send_id:int, datetime_run:datetime,
        message:str, phone_code_filter:int,
        tag_filter:str, datetime_finish:datetime):
    logger.info(f'{datetime.now()} | Sending object data got for Celery.\n/
                id - {send_id}, datetime_run - {datetime_run}, message - {message},/
                phone_code_filter - {phone_code_filter}, tag_filter - {tag_filter}, datetime_finish - {datetime_finish}')
    
    clients = get_clients(phone_code=phone_code_filter, tag=tag_filter)

    now_clients_list, delay_clients_list = compare_time(clients=clients,
                                                        datetime_run=datetime_run,
                                                        datetime_finish=datetime_finish)
    now_countdown(send_id=send_id, clients=now_clients_list, message=message)
    delay_countdown(send_id=send_id, clients=delay_clients_list, message=message)

    