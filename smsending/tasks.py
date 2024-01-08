from datetime import datetime, timedelta
import time

from django.core.mail import send_mail
from celery import shared_task
import pytz
import logging

from config.celery import app
from .service import (serv_compare_time, serv_get_clients, serv_send, SendStat,
                      check_update_delete_sending, check_datetime_finish)

sending_logger = logging.getLogger('sending')
client_logger = logging.getLogger('client')
celery_logger = logging.getLogger('celery')
message_logger = logging.getLogger('message')


@shared_task
def send(send_id:int, client_id:int, phone_number:str,
         datetime_run:datetime, datetime_finish:datetime, datetime_finish_tz:datetime, message:str,
         phone_code_filter:int, tag_filter:str, message_id=None, delay_if_error=30) -> None:
    if not check_datetime_finish(client_id=client_id, datetime_finish=datetime_finish_tz):
        return
    if not check_update_delete_sending(send_id=send_id, datetime_run=datetime_run, datetime_finish=datetime_finish,
                                        message=message, phone_code_filter=phone_code_filter, tag_filter=tag_filter,
                                        client_id=client_id):
        return
    
    result_send = serv_send(send_id=send_id, client_id=client_id,
                            phone_number=phone_number, message=message,
                            message_id=message_id)
    if not result_send[0]:
        message_logger.info(f'Message ID - {result_send[1]} | Data validation completed, data is incorrect, request will be delayed for {delay_if_error} seconds.')
        exec_time = datetime.now().astimezone(pytz.utc) + timedelta(seconds=delay_if_error)
        send.apply_async(args=(send_id, client_id, phone_number, datetime_run, datetime_finish, datetime_finish_tz, message,
                               phone_code_filter, tag_filter, result_send[1], delay_if_error), eta=exec_time)


@app.task
def now_countdown(send_id:int, datetime_run:datetime, datetime_finish:datetime, clients:list,
                  message:str, phone_code_filter:int, tag_filter:str) -> None:
    sending_logger.info(f'Sending ID - {send_id} | The current mass sending to clients has begun.')
    celery_logger.info(f'Sending ID - {send_id} | Celery started executing the current sending.')
    clients_couter = 0
    for client in clients:
        send(send_id=send_id, client_id=client['id'], phone_number=client['phone_number'], datetime_run=datetime_run,
             datetime_finish=datetime_finish, datetime_finish_tz=client['datetime_finish'], message=message,
             phone_code_filter=phone_code_filter, tag_filter=tag_filter)
        clients_couter += 1
    celery_logger.info(f'Sending ID - {send_id} | Celery finished executing the current sending.')
    sending_logger.info(f'Sending ID - {send_id} | The current mass sending to clients has ended.')


@app.task
def delay_countdown(send_id:int, datetime_run:datetime, datetime_finish:datetime,
                    message:str, phone_code_filter:int, tag_filter:str, clients:list) -> None:
    for client in clients:
        exec_time = client['datetime_run'].astimezone(pytz.utc)
        send.apply_async(kwargs={"send_id": send_id, "client_id": client['id'], "phone_number": client['phone_number'],
                                 "datetime_finish_tz": client['datetime_finish'], "datetime_run": datetime_run, "datetime_finish": datetime_finish,
                                 "message": message, "phone_code_filter": phone_code_filter, "tag_filter": tag_filter}, eta=exec_time)       
        client_logger.info(f'Client ID - {client["id"]} | Sending ID - {send_id} | The message to the client is scheduled to be sent on {exec_time}.')
        sending_logger.info(f'Sending ID - {send_id} | Client ID - {client["id"]} | The message to the client is scheduled to be sent on {exec_time}.')

@app.task
def send_and_shedule_messages(send_id:int, datetime_run:datetime, datetime_finish:datetime,
                              message:str, phone_code_filter:int, tag_filter:str):
    try:
        celery_logger.info(f'Sending ID - {send_id} | Сelery received Sending object.')
        clients = serv_get_clients(send_id=send_id, phone_code=phone_code_filter, tag=tag_filter)
        now_clients_list, delay_clients_list = serv_compare_time(send_id=send_id, clients=clients,
                                                                datetime_run=datetime_run,
                                                                datetime_finish=datetime_finish)
        if now_clients_list:
            now_countdown(send_id=send_id, datetime_run=datetime_run, datetime_finish=datetime_finish,
                        clients=now_clients_list, message=message, phone_code_filter=phone_code_filter, tag_filter=tag_filter)
        if delay_clients_list:
            delay_countdown(send_id=send_id, datetime_run=datetime_run, datetime_finish=datetime_finish,
                            clients=delay_clients_list, message=message, phone_code_filter=phone_code_filter, tag_filter=tag_filter)
        celery_logger.info(f'Sending ID - {send_id} | The main task - "run" for the Sending object is completed.')
    except Exception as ex:
        sending_logger.error(f'Sending ID - {send_id} | Error:\n{ex}')


@app.task
def send_stat() -> None:
    try:
        sendstat = SendStat()
        sendstat.run()
    except Exception as ex:
        sending_logger.error(f'Error:\n{ex}')