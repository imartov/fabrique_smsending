from datetime import datetime, timedelta

from django.core.mail import send_mail
from celery import shared_task
import pytz
import logging
from celery.result import AsyncResult
from .models import Sending

from config.celery import app
from .service import (serv_compare_time, serv_create_message_and_get_id,
                      serv_get_clients, serv_send, serv_update_message,
                      SendStat)

sending_logger = logging.getLogger('sending')
client_logger = logging.getLogger('client')
celery_logger = logging.getLogger('celery')


@shared_task
def send(client_id:int, send_id:int, phone_number:str, message:str) -> tuple:
    datetime_send, status_send = serv_send(client_id=client_id, send_id=send_id,
                                           phone_number=phone_number, message=message)
    return datetime_send, status_send

@shared_task
def delay_send(send_id:int, client_id:int, phone_number:str,
               message:str, datetime_run:datetime, phone_code_filter:int,
               tag_filter:str, datetime_finish: datetime) -> tuple:
    
    celery_logger.info(f'Sending ID - {send_id} | Client ID - {client_id} | Celery has started sending the scheduled message.')
    sending_logger.info(f'Sending ID - {send_id} | Client ID - {client_id} | Send a scheduled message.')
    client_logger.info(f'Client ID - {client_id} | Sending ID - {send_id} | Send a scheduled message.')

    if datetime.now().astimezone(pytz.utc) > datetime_finish:
        sending_logger.info(f'Sending ID - {send_id} | Client ID - {client_id} | Sheduled message sending was canceled because the sending time for the client has expired.')
        client_logger.info(f'Client ID - {client_id} | Sending ID - {send_id} | Sheduled message sending was canceled because the sending time for the client has expired.')
        return
    
    actual_sending = Sending.objects.values('datetime_run', 'message', 'phone_code_filter', 'tag_filter', 'datetime_finish').filter(id=send_id).exists()
    if actual_sending:
        actual_sending = list(Sending.objects.values('datetime_run', 'message', 'phone_code_filter', 'tag_filter', 'datetime_finish').filter(id=send_id))[0]
        if actual_sending['datetime_run'] != datetime_run or\
        actual_sending['message'] != message or\
        actual_sending['phone_code_filter'] != phone_code_filter or\
        actual_sending['tag_filter'] != tag_filter or\
        actual_sending['datetime_finish'] != datetime_finish:
        
            sending_logger.info(f'Sending ID - {send_id} | Client ID - {client_id} | Message sending was canceled because the Sending object was changed.')
            client_logger.info(f'Client ID - {client_id} | Sending ID - {send_id} | Message sending was canceled because the Sending object was changed.')
            return
        else:
            send(client_id=client_id, send_id=send_id,
                 phone_number=phone_number, message=message)
    else:
        sending_logger.info(f'Sending ID - {send_id} | Client ID - {client_id} | Message sending was canceled because the Sending object was deleted.')
        client_logger.info(f'Client ID - {client_id} | Sending ID - {send_id} | Message sending was canceled because the Sending object was deleted.')
        return

@app.task
def now_countdown(send_id:int, clients:list, message:str) -> None:
    sending_logger.info(f'Sending ID - {send_id} | The current mass sending to clients has begun.')
    celery_logger.info(f'Sending ID - {send_id} | Celery started executing the current sending.')
    clients_couter = 0
    for client in clients:
        now_tz = datetime.now().astimezone(client['timezone'])
        if now_tz > client['datetime_finish']:
            sending_logger.info(f'''Sending ID - {send_id} | Sending to clients was forcibly stopped because the sending time has expired.
                        Number of messages sent - {clients_couter}, not sent - {len(clients) - clients_couter}.''')
            break
        else:
            send(send_id=send_id, client_id=client['id'],
                 phone_number=client['phone_number'], message=message)
            clients_couter += 1
    celery_logger.info(f'Sending ID - {send_id} | Celery finished executing the current sending.')
    sending_logger.info(f'Sending ID - {send_id} | The current mass sending to clients has ended.')


@app.task
def delay_countdown(send_id:int, clients:list, message:str,
                    datetime_run:datetime, phone_code_filter:int,
                    tag_filter:str, datetime_finish:datetime) -> None:
    
    sending_logger.info(f'Sending ID - {send_id} | Sheduling to send messages has begun.')
    celery_logger.info(f'Sending ID - {send_id} | Celery started sheduling to send messages.')

    delay = 0
    for client in clients:
        exec_time = client['datetime_run'].astimezone(pytz.utc) + timedelta(seconds=delay)
        delay_send.apply_async(kwargs={'send_id': send_id, 'client_id': client['id'],
                                       'phone_number': client['phone_number'], 'message': message,
                                       'datetime_run': datetime_run, 'phone_code_filter': phone_code_filter,
                                       'tag_filter': tag_filter, 'datetime_finish': datetime_finish}, eta=exec_time)
        
        client_logger.info(f'Client ID - {client["id"]} | Sending ID - {send_id} | The message to the client is scheduled to be sent on {exec_time}.')
        sending_logger.info(f'Sending ID - {send_id} | Client ID - {client["id"]} | The message to the client is scheduled to be sent on {exec_time}.')
        delay += 0.5
    sending_logger.info(f'Sending ID - {send_id} | Sheduling for sending messages completed.')
    celery_logger.info(f'Sending ID - {send_id} | Sheduling for sending messages completed.')
    

@app.task
def run_send_and_sheduled_messages(send_id:int, datetime_run:datetime,
                                   message:str, phone_code_filter:int,
                                   tag_filter:str, datetime_finish:datetime):
    
    celery_logger.info(f'Sending ID - {send_id} | Сelery received Sending object.')
    
    if datetime.now().astimezone(pytz.utc) > datetime_finish:
        sending_logger.info(f'Sending ID - {send_id} | Sending end time has expired.')
        return
    
    clients = serv_get_clients(send_id=send_id, phone_code=phone_code_filter, tag=tag_filter)
    now_clients_list, delay_clients_list = serv_compare_time(send_id=send_id,
                                                             clients=clients,
                                                             datetime_run=datetime_run,
                                                             datetime_finish=datetime_finish)
    if now_clients_list:
        now_countdown(send_id=send_id, clients=now_clients_list, message=message)
    if delay_clients_list:
        datetime_run = datetime_run.astimezone(pytz.utc)
        datetime_finish = datetime_finish.astimezone(pytz.utc)
        delay_countdown(send_id=send_id, clients=delay_clients_list, message=message,
                        datetime_run=datetime_run, phone_code_filter=phone_code_filter,
                        tag_filter=tag_filter, datetime_finish=datetime_finish)
    celery_logger.info(f'Sending ID - {send_id} | The main task - "run" for the Sending object is completed.')

@app.task
def send_stat() -> None:
    sendstat = SendStat()
    sendstat.run()
