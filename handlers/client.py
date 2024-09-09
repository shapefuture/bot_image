import logging
import asyncio

from geopy.geocoders import Nominatim

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.utils.exceptions import MessageNotModified, MessageToDeleteNotFound, MessageCantBeDeleted
from contextlib import suppress

import sqldb
import utils
import states as st

import keyboards as kb
from load_bot import bot, dp
from msg_text import MSG_TEXT, BUTTON_TEXT


async def send_alert(message: [types.Message, types.CallbackQuery], text: str, time: int):
    msg = await bot.send_message(chat_id=message.from_user.id, text=text)
    await asyncio.sleep(time)
    await bot.delete_message(chat_id=message.from_user.id, message_id=msg.message_id)


async def command_start(message: types.Message, state: FSMContext):
    logging.info(f"{message.from_user.id} - start")
    user = sqldb.User.basic_auth(chat_id=message.from_user.id)

    await state.reset_state(with_data=False)

    if not isinstance(user, sqldb.User):
        user = sqldb.User.create_new(chat_id=message.from_user.id)
        msg = await bot.send_message(chat_id=message.from_user.id, text=MSG_TEXT.start_user_new)
        await st.AddTimezone.get_city.set()
        await state.update_data(start_MSGID=msg.message_id)

    else:
        msg = await bot.send_message(chat_id=message.from_user.id, text=MSG_TEXT.start_user_exist, reply_markup=kb.MainMenu())
        await state.update_data(start_MSGID=msg.message_id)


async def change_timezone(message: types.Message, state: FSMContext):
    logging.info(f"{message.from_user.id} - chanche_timezone")
    await message.delete()

    msg = await bot.send_message(chat_id=message.from_user.id, text=MSG_TEXT.new_timezone)
    await st.AddTimezone.get_city.set()
    await state.update_data(tz_MSGID=msg.message_id)


async def get_timezone(message: types.Message, state: FSMContext):
    logging.info(f"{message.from_user.id} - get_timezone")
    user_data = await state.get_data()
    await message.delete()

    user = sqldb.User.basic_auth(chat_id=message.from_user.id)
    city = message.text.strip()

    loc = Nominatim(user_agent='GetLoc', timeout=20)
    getLoc = loc.geocode(city)
    if getLoc:
        timezone = utils.get_timezone(getLoc.latitude, getLoc.longitude)

        user.timezone = timezone
        user.save()

        await send_alert(message, MSG_TEXT.data_done, 2)
        await state.reset_state(with_data=False)

        try:
            await bot.delete_message(chat_id=message.from_user.id, message_id=user_data['tz_MSGID'])
        except (MessageToDeleteNotFound, MessageCantBeDeleted, KeyError):
            await bot.delete_message(chat_id=message.from_user.id, message_id=user_data['start_MSGID'])
            msg = await bot.send_message(chat_id=message.from_user.id, text=MSG_TEXT.start_user_exist,reply_markup=kb.MainMenu())
            await state.update_data(start_MSGID=msg.message_id)
    else:
        return await send_alert(message, MSG_TEXT.error_location, 2)


async def choose_settings(message: types.Message, state: FSMContext):
    logging.info(f"{message.from_user.id} - choose_settings")
    await message.delete()
    await state.reset_state(with_data=False)

    msg = await bot.send_message(text=MSG_TEXT.choose_settings, reply_markup=kb.ChooseSettings(), chat_id=message.from_user.id )
    await state.update_data(intset_MSGID=msg.message_id)


async def choose_interval(call: types.Message, state: FSMContext):
    logging.info(f"{call.from_user.id} - choose_interval")
    await state.reset_state(with_data=False)

    user_data = await state.get_data()
    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=user_data['intset_MSGID'],
        text=MSG_TEXT.choose_interval,
        reply_markup=kb.IntervalChoose(mode='INTS')
    )

    await st.IntervalSettings.get_interval.set()


async def get_interval(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    logging.info(f"{call.from_user.id} - get_interval_settings_start {callback_data['TYPE']}")
    int_dict = {'morning': 'утро', 'noon': 'день', 'evening': 'вечер'}

    interval = callback_data['TYPE']
    await state.update_data(interval=interval)

    user_data = await state.get_data()
    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=user_data['intset_MSGID'],
        text=MSG_TEXT.choose_interval_lower.replace('_interval_', int_dict[interval]),
        reply_markup=kb.TimeIntStart(interval)
    )

    await st.IntervalSettings.next()


async def get_interval_start_time(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    logging.info(f"{call.from_user.id} - get_interval_start_time")
    int_dict = {'morning': 'утро', 'noon': 'день', 'evening': 'вечер'}

    start_time = callback_data['TYPE']
    await state.update_data(start_time=start_time)

    user_data = await state.get_data()
    interval = user_data['interval']
    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=user_data['intset_MSGID'],
        text=MSG_TEXT.choose_interval_upper.replace('_interval_', int_dict[interval]),
        reply_markup=kb.TimeIntEnd(user_data['interval'])
    )
    await st.IntervalSettings.next()


async def get_interval_end_time(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    logging.info(f"{call.from_user.id} - get_interval_end_time")

    end_time = callback_data['TYPE']
    await state.update_data(end_time=end_time)

    user_data = await state.get_data()
    interval = user_data['interval']
    start_time = user_data['start_time']
    end_time = end_time

    sqldb.Settings.set_settings(chat_id=call.from_user.id, interval=interval, start_time=start_time, end_time=end_time)

    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=user_data['intset_MSGID'],
        text=MSG_TEXT.choose_interval,
        reply_markup=kb.ChooseSettings()
    )
    await state.reset_state(with_data=False)
    await send_alert(call, MSG_TEXT.data_done, 2)


async def choose_interval_img(call: types.Message, state: FSMContext):
    logging.info(f"{call.from_user.id} - choose_interval_img")
    await state.reset_state(with_data=False)

    user_data = await state.get_data()
    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=user_data['intset_MSGID'],
        text=MSG_TEXT.choose_interval,
        reply_markup=kb.IntervalChoose(mode='IMGS')
    )

    await st.ImgsSettings.get_interval.set()


async def get_interval_imgs(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    logging.info(f"{call.from_user.id} - get_interval_imgs {callback_data['TYPE']}")
    int_dict = {'morning': 'утро', 'noon': 'день', 'evening': 'вечер'}

    user: sqldb.User = sqldb.User.basic_auth(call.from_user.id)
    interval = callback_data['TYPE']

    await state.update_data(interval=interval)

    sqldb.Images.delete_all_images(user=user, interval=interval)

    user_data = await state.get_data()
    msg_text = MSG_TEXT.send_imgs.replace('_interval_', int_dict[user_data['interval']])
    await bot.edit_message_text(chat_id=call.from_user.id, message_id=user_data['intset_MSGID'], text=msg_text, reply_markup=kb.NextImgs())

    await st.ImgsSettings.next()


async def receive_imgs(message: types.Message, state: FSMContext):
    logging.info(f"{message.from_user.id} - receive_imgs")

    await message.delete()
    user_data = await state.get_data()
    user: sqldb.User = sqldb.User.basic_auth(message.from_user.id)

    if message.photo:
        img_tg_id = message.photo[-1]['file_id']
        data_img = {'chat_id': user.chat_id, 'interval': user_data['interval'], 'img_tg_id': img_tg_id}
        sqldb.Images.add_image(user, data_img)


async def get_interval_imgs_done(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    logging.info(f"{call.from_user.id} - get_interval_imgs_done")

    user_data = await state.get_data()
    await bot.edit_message_text(
        chat_id=call.from_user.id,
        message_id=user_data['intset_MSGID'],
        text=MSG_TEXT.choose_interval,
        reply_markup=kb.ChooseSettings()
    )
    await send_alert(call, MSG_TEXT.data_done, 2)
    await state.reset_state(with_data=False)


async def handle_feedback(call: types.CallbackQuery, state: FSMContext, callback_data: dict):
    logging.info(f"{call.from_user.id} - handle_feedback")

    feedback = callback_data['TYPE']
    not_id = callback_data['NOT_ID']

    sqldb.Notifications.handle_feedback(feedback, not_id)
    notif = sqldb.Notifications.get_or_none(id=not_id)

    photo = types.InputMediaPhoto(media=notif.img_tg_id)
    await bot.edit_message_media(chat_id=call.from_user.id, message_id=notif.msg_id, media=photo, reply_markup=kb.Notification(not_id=notif.id, type=feedback))


def reg_handlers_client(dp: Dispatcher):
    dp.register_message_handler(command_start, commands=['start'], state="*")
    dp.register_message_handler(get_timezone, content_types=['text'], state=st.AddTimezone.get_city)

    dp.register_message_handler(choose_settings, Text(BUTTON_TEXT.notification_settings, ignore_case=True), state="*")
    dp.register_message_handler(change_timezone, Text(BUTTON_TEXT.new_timezone, ignore_case=True), state="*")

    dp.register_callback_query_handler(choose_interval, kb.ChooseSettings.CallbackData.CB.filter(TYPE="INTS"), state="*")
    dp.register_callback_query_handler(get_interval, kb.IntervalChoose.CallbackData.CB.filter(ACTION='INTS'), state="*")
    dp.register_callback_query_handler(get_interval_start_time, kb.TimeIntStart.CallbackData.CB.filter(), state="*")
    dp.register_callback_query_handler(get_interval_end_time, kb.TimeIntEnd.CallbackData.CB.filter(), state="*")

    dp.register_callback_query_handler(choose_interval_img, kb.ChooseSettings.CallbackData.CB.filter(TYPE="IMGS"), state="*")
    dp.register_callback_query_handler(get_interval_imgs, kb.IntervalChoose.CallbackData.CB.filter(ACTION='IMGS'),  state="*")
    dp.register_message_handler(receive_imgs, content_types=['photo'], state=st.ImgsSettings.get_imgs)
    dp.register_callback_query_handler(get_interval_imgs_done, kb.NextImgs.CallbackData.CB.filter(), state="*")

    dp.register_callback_query_handler(handle_feedback, kb.Notification.CallbackData.CB.filter(), state="*")

