from aiogram.dispatcher.filters.state import State, StatesGroup


class AddTimezone(StatesGroup):
    get_city = State()


class IntervalSettings(StatesGroup):
    get_interval = State()
    get_start_time = State()
    get_end_time = State()
    get_imgs = State()

class ImgsSettings(StatesGroup):
    get_interval = State()
    get_imgs = State()