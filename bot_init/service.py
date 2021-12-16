import requests
import csv
from datetime import datetime
from django.conf import settings
from loguru import logger
from progressbar import progressbar as pbar
from telebot.apihelper import ApiException

from bot_init.models import AdminMessage, Message, Subscriber, SubscriberAction
from bot_init.schemas import SUBSCRIBER_ACTIONS
from bot_init.services.answer import Answer
from bot_init.utils import get_subscriber_by_chat_id, get_tbot_instance, save_message
from prayers.models import Prayer

log = logger.bind(task="app")
tbot = get_tbot_instance()


def registration_subscriber(chat_id: int):
    """Логика сохранения подписчика."""
    subscriber, created = Subscriber.objects.get_or_create(tg_chat_id=chat_id)
    ...


def check_user_status_by_typing(chat_id: int):
    """Проверить подписан ли пользователь на бота."""
    sub = get_subscriber_by_chat_id(chat_id)
    try:
        tbot.send_chat_action(sub.tg_chat_id, 'typing')
        if not sub.is_active:
            sub.is_active = True
            sub.save(update_fields=['is_active'])
        return True
    except Exception as e:
        service_api_exception(e)


def count_active_users():
    """Подсчет кол-ва активных пользователей."""
    count = 0
    for sub in pbar(Subscriber.objects.all()):
        if check_user_status_by_typing(sub.tg_chat_id):
            count += 1
    return count


def service_api_exception(exception, sub):
    """Обработка исключения API телеграма."""
    if ('bot was blocked by the user' in str(exception) or 'user is deactivated' in str(exception)) and sub.is_active:
        _subscriber_unsubscribed(sub.tg_chat_id)


def send_answer(answer: Answer, chat_id):
    """Отправить ответ."""
    tbot.send_message(chat_id, Answer.text)


def do_mailing(data: dict):
    """Сделать рассылку."""
    for chat_id, text in data.items():
        try:
            answer = Answer(text)
            message_instance = send_answer(answer, chat_id)
            save_message(message_instance)
        except ApiException as e:
            service_api_exception(e)


def _create_action(subscriber: Subscriber, action: str):
    """Создаем запись в БД о подписке, отписке или реактивации бота пользователем."""
    SubscriberAction.objects.create(subscriber=subscriber, action=action)


def update_webhook(host=f'{settings.TG_BOT.webhook_host}/{settings.TG_BOT.token}'):
    """Обновляем webhook."""
    try:
        tbot.remove_webhook()
        res = tbot.set_webhook(host)
        log.info("webhook updated successfully")
    except ApiException as e:
        log.error(e)


def send_message_to_admin(message_text: str) -> Message:
    """Отправляем сообщение админу."""
    answer = Answer(message_text)
    for admin_tg_chat_id in settings.TG_BOT.admins:
        message_instance = send_answer(answer, admin_tg_chat_id)
    return message_instance


def _subscriber_unsubscribed(chat_id: int):
    """Действия, выполняемые при блокировке бота пользователем."""
    subscriber = Subscriber.objects.get(tg_chat_id=chat_id)
    subscriber.is_active = False
    subscriber.save()
    _create_action(subscriber, SUBSCRIBER_ACTIONS[1][0])


def _not_created_subscriber_service(subscriber: Subscriber):
    """Фунция вызывается если пользователь, который уже существует отправил команду /start."""
    if subscriber.is_active:
        # Пользователь уже подписан
        return Answer(...)
    # Пользователь отписался и подписался вновь
    _create_action(subscriber, SUBSCRIBER_ACTIONS[2][0])
    subscriber.is_active = True
    subscriber.save(update_fields=['is_active'])
    return Answer(...)


def _created_subscriber_service(subscriber: Subscriber) -> Answer:
    """Функция обрабатывает и генерирует ответ для нового подписчика."""
    start_message_text = AdminMessage.objects.get(key='start').text  # TODO создать это сообщение с миграцией
    _create_action(subscriber, SUBSCRIBER_ACTIONS[0][0])
    send_message_to_admin(
        'Зарегестрировался новый пользователь',
    )
    answers = ...
    return answers


def reformat_date(source_date):
    '''Возварщет объект datetime'''
    try:
        date_time_obj = datetime.strptime(source_date, '%d-%m-%Y')
        answer = f'Дата: {date_time_obj.date()}'
    except ValueError:
        answer = 'Повторите ввод'
    return answer


def download_namaztimecsv():
    '''Скачивает время намазма в формате csv'''
    url = 'https://dumrt.ru/netcat_files/482/640/Kazan.csv'
    req = requests.get(url)
    # with open('bot_init/services/namaztime.csv', 'wb') as file:
    csv_file = req.content.decode('utf-8').splitlines()
    reader = csv.reader(csv_file)
    for row in reader:
        row = row[0].split(';')
        _create_prayer(row)


def _create_prayer(raw_datetime):
    """Doc.
    
    raw_datetime: Приходит данные типа ['12.03.2021', '12:30',...]
    """
    prayer_names = ['Утренний', 'Восход', 'Обеденный', 'Послеобеденный', 'Закат', 'Ночной']
    prayer_time_indexes = [1, 3, 4, 6, 7, 8]
    for i in range(6):
        prayer_time_index = prayer_time_indexes[i]
        prayer_name = prayer_names[i]
        date = datetime.strptime(raw_datetime[0], '%d.%m.%Y')
        hour, minutes = _parse_time(raw_datetime[prayer_time_index])
        morning_time = date.replace(hour=hour, minute=minutes)
        Prayer.objects.create(name=prayer_name, date_time=morning_time)



def _parse_time(time):
    """Doc.
    
    >>> _parse_time('05:43')
    ... (5, 43)
    """
    hour, minutes = time.split(':')
    return int(hour), int(minutes)


def pars_csv():
    with open('bot_init/services/namaztime.csv', newline='') as fp:
        reader = csv.reader(fp)
        for row in reader:
            print(row[0])

# pars_csv()
