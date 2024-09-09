import typing
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.callback_data import CallbackData


from msg_text import BUTTON_TEXT


class MainMenu(ReplyKeyboardMarkup):
    def __init__(self, ):
        super().__init__(resize_keyboard=True, row_width=2)
        self.b1 = KeyboardButton(text=BUTTON_TEXT.notification_settings)
        self.b2 = KeyboardButton(text=BUTTON_TEXT.new_timezone)

        self.add(self.b1, self.b2)


class ChooseSettings(InlineKeyboardMarkup):
    def __init__(self):
        super().__init__(row_width=1)
        self.b1 = InlineKeyboardButton(BUTTON_TEXT.notification_settings_time, callback_data=self.CallbackData.CB.new(TYPE="INTS"))
        self.b2 = InlineKeyboardButton(BUTTON_TEXT.notification_settings_imgs, callback_data=self.CallbackData.CB.new(TYPE="IMGS"))

        self.add(self.b1, self.b2)

    class CallbackData:
        CB = CallbackData("CHSET", "TYPE")


class IntervalChoose(InlineKeyboardMarkup):
    def __init__(self, mode: str):
        super().__init__(row_width=3)
        self.b1 = InlineKeyboardButton(BUTTON_TEXT.morning, callback_data=self.CallbackData.CB.new(TYPE="morning", ACTION=mode))
        self.b2 = InlineKeyboardButton(BUTTON_TEXT.noon, callback_data=self.CallbackData.CB.new(TYPE="noon", ACTION=mode))
        self.b3 = InlineKeyboardButton(BUTTON_TEXT.evening, callback_data=self.CallbackData.CB.new(TYPE="evening", ACTION=mode))

        self.add(self.b1, self.b2, self.b3)

    class CallbackData:
        CB = CallbackData("INTS", "TYPE", "ACTION")


class TimeIntStart(InlineKeyboardMarkup):
    def __init__(self, interval):
        super().__init__(row_width=4)
        interval_dict = {'morning': ['6:00', '7:00', '8:00', '9:00'],
                         "noon": ['12:00', '13:00', '14:00', '15:00'],
                         "evening": ['17:00', '18:00', '19:00', '20:00']}

        for time in interval_dict[interval]:
            button = InlineKeyboardButton(time, callback_data=self.CallbackData.CB.new(TYPE=time.split(':')[0]))
            self.insert(button)

    class CallbackData:
        CB = CallbackData("TINTS", "TYPE")


class TimeIntEnd(InlineKeyboardMarkup):
    def __init__(self, interval):
        super().__init__(row_width=4)
        interval_dict = {'morning': ['9:00', '10:00', '11:00', '12:00'],
                         "noon": ['15:00', '16:00', '17:00', '18:00'],
                         "evening": ['21:00', '22:00', '23:00', '00:00']}

        for time in interval_dict[interval]:
            button = InlineKeyboardButton(time, callback_data=self.CallbackData.CB.new(TYPE=time.split(':')[0]))
            self.insert(button)

    class CallbackData:
        CB = CallbackData("TINTE", "TYPE")


class NextImgs(InlineKeyboardMarkup):
    def __init__(self):
        super().__init__(row_width=1)
        self.b1 = InlineKeyboardButton(BUTTON_TEXT.next_b, callback_data=self.CallbackData.CB.new(TYPE="NEXT"))

        self.add(self.b1)

    class CallbackData:
        CB = CallbackData("IMGS", "TYPE")


class Notification(InlineKeyboardMarkup):
    def __init__(self, not_id: str, type: str = None):
        super().__init__(row_width=2)
        self.b1 = InlineKeyboardButton(BUTTON_TEXT.feedback_good, callback_data=self.CallbackData.CB.new(TYPE="GOOD", NOT_ID=not_id))
        self.b2 = InlineKeyboardButton(BUTTON_TEXT.feedback_bad, callback_data=self.CallbackData.CB.new(TYPE="BAD", NOT_ID=not_id))
        self.b3 = InlineKeyboardButton(BUTTON_TEXT.feedback_good_done, callback_data=self.CallbackData.CB.new(TYPE='', NOT_ID=not_id))
        self.b4 = InlineKeyboardButton(BUTTON_TEXT.feedback_bad_done, callback_data=self.CallbackData.CB.new(TYPE='', NOT_ID=not_id))

        if type == 'GOOD':
            self.add(self.b3, self.b2)
        elif type == 'BAD':
            self.add(self.b1, self.b4)
        else:
            self.add(self.b1, self.b2)

    class CallbackData:
        CB = CallbackData("NTFC", "TYPE", "NOT_ID")


cancel_kb = InlineKeyboardMarkup()
cancel_button = InlineKeyboardButton('❌ Отмена', callback_data='cancel_call_b')
cancel_kb.add(cancel_button)
