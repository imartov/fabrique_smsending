from datetime import datetime, timedelta
import asyncio, time

from django.core.mail import send_mail
from celery import shared_task
import pytz
import logging
from celery.result import AsyncResult

from config.celery import app
from .service import (serv_compare_time,
                      serv_create_message,
                      serv_get_clients,
                      serv_send)

logger = logging.getLogger('django')


@shared_task
def send(phone_number:str, message:str) -> tuple:
    datetime_send, status_send = serv_send(phone_number=phone_number, message=message)
    return datetime_send, status_send

@shared_task
def delay_send(send_id:int, client_id:int, phone_number:str, message:str) -> tuple:
    datetime_send, status_send = serv_send(phone_number=phone_number, message=message)
    create_message(datetime_send=datetime_send,
                   status_send=status_send,
                   sms_sending=send_id,
                   client=client_id)

@app.task
def now_countdown(send_id:int, clients:list, message:str) -> None:
    logger.info(f'{datetime.now()} | Sending to clients has begun.')
    clients_couter = 0
    for client in clients:
        now_tz = datetime.now().astimezone(client['timezone'])
        if now_tz > client['datetime_finish']:
            logger.info(f'''{datetime.now()} | Sending to clients was forcibly stopped because the sending time has expired.
                        Number of messages sent - {clients_couter}, not sent - {len(clients) - clients_couter}.''')
            break
        else:
            datetime_send, status_send = send(phone_number=client['phone_number'], message=message)
            logger.info(f'{datetime.now()} | result_values: {datetime_send} {status_send}.')
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
        delay_send.apply_async(kwargs={'send_id': send_id,
                                       'client_id': client['id'],
                                       'phone_number': client['phone_number'],
                                       'message': message}, eta=exec_time)
        logger.info(f'{datetime.now()} | Sending a message to the client - {client["phone_number"]} is scheduled for {exec_time}.')
    logger.info(f'{datetime.now()} | Sheduling for sending messages completed.')


@app.task
def get_clients(phone_code:int, tag:str) -> list:
    return serv_get_clients(phone_code=phone_code, tag=tag)


@app.task
def compare_time(clients:list,
                 datetime_run:datetime,
                 datetime_finish:datetime) -> list:
    return serv_compare_time(clients=clients,
                             datetime_run=datetime_run,
                             datetime_finish=datetime_finish)


@shared_task
def create_message(datetime_send:datetime,
                   status_send:int,
                   sms_sending:int,
                   client:int):
    serv_create_message(datetime_send=datetime_send,
                           status_send=status_send,
                           sms_sending=sms_sending,
                           client=client)


@app.task
def run(send_id:int, datetime_run:datetime,
        message:str, phone_code_filter:int,
        tag_filter:str, datetime_finish:datetime):
    logger.info(f'''{datetime.now()} | Sending object data got for Celery.
                id - {send_id}, datetime_run - {datetime_run}, message - {message},
                phone_code_filter - {phone_code_filter}, tag_filter - {tag_filter}, datetime_finish - {datetime_finish}''')
    
    clients = get_clients(phone_code=phone_code_filter, tag=tag_filter)

    now_clients_list, delay_clients_list = compare_time(clients=clients,
                                                        datetime_run=datetime_run,
                                                        datetime_finish=datetime_finish)
    if now_clients_list:
        now_countdown(send_id=send_id, clients=now_clients_list, message=message)
    if delay_clients_list:
        delay_countdown(send_id=send_id, clients=delay_clients_list, message=message)
