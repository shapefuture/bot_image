# -*- coding: utf-8 -*-
import os
import sys
import logging
import asyncio
import datetime
import typing
import multiprocessing

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats
from aiogram.utils import executor
import sqldb
from load_bot import bot, dp

import admin_panel

scheduler = AsyncIOScheduler()

#BOT_TOKEN = '7142277719:AAGZpilGW-cz94yNm9t3ATF4eo27s8KRkBU'

def general_commands() -> typing.List[BotCommand]:
    RESTART = BotCommand("start", 'Перезапуск')

    return [RESTART]


async def on_startup(dp):
    await bot.set_my_commands(commands=general_commands(), scope=BotCommandScopeAllPrivateChats())
    sqldb.create_tables()
    logging.info('Bot loaded')


async def on_shutdown(dp):
    logging.info('Shutting down..')
    sqldb.close_conn()
    await dp.storage.close()
    logging.info("DB Connection closed")


if __name__ == "__main__":
    project_root = os.path.dirname(os.path.realpath(__file__))
    templates_root = os.path.join(project_root, 'templates/')

    sys.path.insert(0, project_root)
    sys.path.insert(0, templates_root)

    from handlers import client
    from services import send_notifications_, shcedule_notifications_

    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    filename = os.path.join(logs_dir, datetime.date.today().strftime("%d_%m_%Y") + "_log.log")
    logging.basicConfig(level=logging.INFO,
                        # filename=filename, filemode="a",
                        format='[%(asctime)s] %(filename)s [LINE:%(lineno)d] #%(levelname)-8s %(message)s')

    scheduler.start()
    scheduler.add_job(send_notifications_, "interval", minutes=2)
    scheduler.add_job(shcedule_notifications_, "cron", hour=1)

    _admin = multiprocessing.Process(target=admin_panel.run, name="Admin_panel", daemon=True)
    _admin.start()

    client.reg_handlers_client(dp)
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup, on_shutdown=on_shutdown)
