# -*- coding: utf-8 -*-
import os
import logging
import sqlite3 as sq
import pytz
import random

from peewee import *
import datetime

db = SqliteDatabase(r'bot_db.db', pragmas={'journal_mode': 'wal', 'foreign_keys': "on",'wal_autocheckpoint': 10})


class BaseModel(Model):
    class Meta:
        database = db


class User(BaseModel):
    chat_id = BigAutoField(primary_key=True)
    user_type = TextField(default='user')
    timezone = TextField(null=True)
    created_at = DateTimeField(formats="%d.%m.%y %H:%M:%S", default=datetime.datetime.now())


    @staticmethod
    def basic_auth(chat_id):
        return User.get_or_none(chat_id=chat_id)

    @staticmethod
    def create_new(chat_id):
        new_user = User.create(chat_id=chat_id)
        new_user.save()
        return User.get_or_none(chat_id=chat_id)


class Settings(BaseModel):
    id = AutoField(primary_key=True)
    chat_id = BigIntegerField()
    interval = TextField()
    start_time = TimeField(formats='%H:%M:%S')
    end_time = TimeField(formats='%H:%M:%S')
    no_intervals_count = IntegerField(default=0)
    created_at = DateTimeField(formats="%d.%m.%y %H:%M:%S", default=datetime.datetime.now())

    @staticmethod
    def set_settings(chat_id: str, interval: str, start_time: str, end_time: str):
        logging.info(f"start_time - {start_time}")

        query = Settings.select().where((Settings.chat_id == chat_id)&(Settings.interval == interval))
        for row in query:
            row.delete_instance()
        # start_time = '09:00'

        start_time = datetime.datetime.strptime(f"{start_time}:00:00", '%H:%M:%S').time()
        end_time = datetime.datetime.strptime(f"{end_time}:00:00", '%H:%M:%S').time()
        Settings.get_or_create(chat_id=chat_id, interval=interval, start_time=start_time, end_time=end_time)
        Intervals.set_interval(
            chat_id=chat_id,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            no_intervals_count=0,
            delete=True
        )
        


class Intervals(BaseModel):
    id = AutoField(primary_key=True)
    chat_id = BigIntegerField()
    interval = TextField()
    time = TimeField(formats='%H:%M:%S')
    feedback = BooleanField(default=True)
    created_at = DateTimeField(formats="%d.%m.%y %H:%M:%S", default=datetime.datetime.now())


    @staticmethod
    def set_interval(chat_id: [str, BigAutoField], interval: str, start_time: datetime.time, end_time: datetime.time, no_intervals_count: float, delete: bool = True):
        if delete:
            intervals = Intervals.select().where((Intervals.chat_id == chat_id) & (Intervals.interval == interval))
            for i in intervals:
                i.delete_instance()

        time_intervals = []
        start_time = datetime.datetime(year=2024, month=1, day=1, hour=start_time.hour, minute=start_time.minute, second=start_time.second)
        if end_time.hour == 0:
            end_time = datetime.datetime(year=2024, month=1, day=2, hour=end_time.hour, minute=end_time.minute, second=end_time.second)
        else:
            end_time = datetime.datetime(year=2024, month=1, day=1, hour=end_time.hour, minute=end_time.minute, second=end_time.second)

        timedelta = 30 / 2 ** no_intervals_count
        minutes = timedelta // 1
        seconds = timedelta % 1 * 60

        time_ = start_time - datetime.timedelta(minutes=minutes, seconds=seconds)
        while time_ < end_time:
            time_ = time_ + datetime.timedelta(minutes=minutes, seconds=seconds)
            time_.time()
            time_intervals.append(time_.time())

        for not_time in time_intervals:
            data_intervals = {'chat_id': chat_id, 'interval': interval, 'time': not_time}
            Intervals.get_or_create(**data_intervals)


    @staticmethod
    def get_random_time(user: User, interval: str):
        user = user

        time_ = list(Intervals
                     .select()
                     .where((Intervals.feedback == True) &
                            (Intervals.chat_id == user.chat_id) &
                            (Intervals.interval == interval))
                     .dicts())
        print(time_)

        if time_:
            return random.choice(time_)
        else:
            user_settings = Settings.get_or_none(chat_id=user.chat_id, interval=interval)
            if not user_settings:
                return None

            no_intervals_count = user_settings.no_intervals_count + 1
            user_settings.no_intervals_count += 1
            user_settings.save()

            start_time = datetime.datetime.strptime(user_settings.start_time, '%H:%M:%S').time()
            end_time = datetime.datetime.strptime(user_settings.end_time, '%H:%M:%S').time()

            Intervals.set_interval(
                chat_id=user.chat_id,
                interval=interval,
                start_time=start_time,
                end_time=end_time,
                no_intervals_count=no_intervals_count,
                delete=False
            )

            time_ = list(Intervals
                         .select()
                         .where((Intervals.feedback == True) &
                                (Intervals.chat_id == user.chat_id) &
                                (Intervals.interval == interval))
                         .dicts())
            if time_:
                return random.choice(time_)
            else:
                return None


class Notifications(BaseModel):
    id = AutoField(primary_key=True)
    chat_id = BigIntegerField()
    interval = TextField()
    time = TimeField(formats='%H:%M:%S')
    img_tg_id = TextField()
    feedback = TextField(null=True)
    status = TextField(default='TO_SEND')
    msg_id = IntegerField(null=True)
    created_at = DateTimeField(formats="%d.%m.%y %H:%M:%S", default=datetime.datetime.now())


    @staticmethod
    def create_new_notifications(user):
        intervals = ['morning', 'noon', 'evening']
        for interval in intervals:
            time = Intervals.get_random_time(user, interval)
            img_tg_id = Images.get_random_img(user, interval)
            if time and img_tg_id:
                time = time['time']
                img_tg_id = img_tg_id['img_tg_id']
                Images.update_sent_image(img_tg_id)
                data = {'chat_id': user.chat_id, 'interval': interval, 'time': time, 'img_tg_id': img_tg_id, 'status': 'TO_SEND'}
                Notifications.get_or_create(**data)

    @staticmethod
    def get_notifications_to_send():
        notifications = Notifications.select().where(Notifications.status == 'TO_SEND')
        return notifications

    @staticmethod
    def handle_feedback(feedback, not_id):
        notif = Notifications.get_or_none(id=not_id)
        notif.feedback = feedback
        notif.save()

        interval = (Intervals
                    .select()
                    .where((Intervals.chat_id == notif.chat_id) & (Intervals.interval == notif.interval) & (Intervals.time == notif.time))
                    .dicts()
                    .first())

        interval = Intervals.get_or_none(id=interval['id'])
        interval.feedback = False if feedback == 'BAD' else True
        interval.save()


class Images(BaseModel):
    id = AutoField(primary_key=True)
    chat_id = BigIntegerField()
    interval = TextField()
    img_tg_id = TextField()
    last_notification_time = DateTimeField(formats="%d.%m.%y %H:%M:%S", null=True)
    created_at = DateTimeField(formats="%d.%m.%y %H:%M:%S", default=datetime.datetime.now())


    @staticmethod
    def add_image(user, data):
        data['last_notification_time'] = datetime.datetime.now(tz=pytz.timezone(user.timezone)) - datetime.timedelta(days=30)
        Images.get_or_create(**data)

    @staticmethod
    def delete_all_images(user, interval):
        query = Images.select().where((Images.chat_id == user.chat_id) & (Images.interval == interval))
        for row in query:
            row.delete_instance()


    @staticmethod
    def update_sent_image(img_tg_id):
        image = Images.get_or_none(img_tg_id=img_tg_id)
        user = User.get_or_none(chat_id=image.chat_id)
        image.last_notification_time = datetime.datetime.now(tz=pytz.timezone(user.timezone))
        image.save()



    @staticmethod
    def get_random_img(user, interval):
        imgs = list(Images
                    .select()
                    .where((Images.chat_id == user.chat_id) & (Images.interval == interval))
                    .order_by(Images.last_notification_time)
                    .dicts())
        if imgs:
            num_to_get = len(imgs)//2 + 1
            imgs = imgs[:num_to_get]
            return random.choice(imgs)
        else:
            None







# class NotificationsTimesheet(BaseModel):
#     id = AutoField(primary_key=True)
#     chat_id = BigIntegerField()
#     time = TimeField(formats='%H:%M')
#     img_tg_id = TextField()
#     status = TextField()



def create_tables():
    db.create_tables([User, Settings, Intervals, Notifications, Images])
    # Tasks.base_init()


def close_conn():
    db.close()

