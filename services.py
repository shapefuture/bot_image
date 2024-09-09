import logging
import datetime

from pytz import timezone

import sqldb
import keyboards as kb
from app import bot


# Schedules notifications once a day
def shcedule_notifications():
    logging.info("SERVICE shcedule_notifications starts")
    users = sqldb.User.select()

    for user in users:
        sqldb.Notifications.create_new_notifications(user)


# Checks notifications to send every 2 minutes
async def send_notifications():
    logging.info("SERVICE send_notifications starts")

    notifications = sqldb.Notifications.get_notifications_to_send()

    for notification in notifications:
        user = sqldb.User.get_or_none(chat_id=notification.chat_id)
        if user:
            current_time = datetime.datetime.now(timezone(user.timezone)).time()
            if isinstance(notification.time, str):
                notif_time = datetime.datetime.strptime(notification.time, '%H:%M:%S').time()
            else:
                notif_time = notification.time

            day_current_time = datetime.datetime(year=2024, month=1, day=1, hour=current_time.hour, minute=current_time.minute)
            day_notif_time = datetime.datetime(year=2024, month=1, day=1, hour=notif_time.hour, minute=notif_time.minute)

            if day_current_time < day_notif_time:
                diff = 24*60 - (day_current_time - day_notif_time).seconds/60
            else:
                diff = (day_notif_time - day_current_time).seconds/60

            if diff < 3:
                try:
                    msg = await bot.send_photo(chat_id=notification.chat_id, photo=notification.img_tg_id, reply_markup=kb.Notification(not_id=notification.id))
                    notif = sqldb.Notifications.get_or_none(id=notification.id)
                    notif.status = 'SENT'
                    notif.msg_id = msg.message_id
                    notif.save()
                except:
                    logging.error(f"ERROR {notification.chat_id} - send_notifications ")


async def send_notifications_():
    await send_notifications()


async def shcedule_notifications_():
    shcedule_notifications()
