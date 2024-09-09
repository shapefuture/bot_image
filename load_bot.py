# -*- coding: utf-8 -*-
import os
import logging
import datetime
from dotenv import load_dotenv

from aiogram.utils import executor

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.redis import RedisStorage2

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')

REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT'))
REDIS_PASS = os.getenv('REDIS_PASS')

storage = RedisStorage2(REDIS_HOST, REDIS_PORT)
bot = Bot(BOT_TOKEN, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)
