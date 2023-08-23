import datetime
from pprint import pprint

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message

from tgbot.keyboards import reply_keyboards, inline_keyboards
from tgbot.misc import callbacks, states, messages
from tgbot.services.database.models import IikoUser
from tgbot.services.iiko.api import Iiko
from tgbot.services.iiko.schemas import CreateReserveRequest, Customer, OrderCustomer, Guests


async def start_reserve_table(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await call.message.answer('➡️ Введите кол-во человек', reply_markup=reply_keyboards.cancel)
    await states.ReserveTable.first()
    await state.update_data(organization=callback_data['id'])
    await call.answer()


async def get_guests_count(message: Message, state: FSMContext):
    guests_count = message.text
    if not guests_count.isdigit():
        await message.answer('Кол-во человек должно быть числом')
        return

    await message.answer('➡️ Введите дату бронирования (например, "22.08.2023")')
    await state.update_data(guests_count=guests_count)
    await states.ReserveTable.next()


async def get_date(message: Message, state: FSMContext):
    date = message.text
    try:
        date = datetime.datetime.strptime(date, '%d.%m.%Y')
    except ValueError:
        await message.answer('➡️ Введите корректную дату (например, "22.08.2023")')
        return

    now = datetime.datetime.now()
    if date.date() < now.date() or date > now + datetime.timedelta(days=90):
        await message.answer('➡️ Введите корректную дату (например, "22.08.2023")')
        return

    if date.weekday() in (4, 5):
        end_date = datetime.datetime.combine(date.today(), datetime.time(22, 0))
    else:
        end_date = datetime.datetime.combine(date.today(), datetime.time(21, 0))
    interval = 30

    if now.date() == date.date():
        start_date = now + datetime.timedelta(hours=2)
    else:
        start_date = datetime.datetime.combine(date.today(), datetime.time(9, 0))

    keyboard = inline_keyboards.get_time_keyboard(start_date, end_date, interval, 'res')
    await message.answer('Выберите время бронирования', reply_markup=keyboard)
    await state.update_data(date=date.date().isoformat())
    await states.ReserveTable.next()


async def get_time(call: CallbackQuery, callback_data: dict, state: FSMContext):
    [hour, minute] = callback_data['time'].split('-')
    state_data = await state.get_data()
    date = datetime.date.fromisoformat(state_data['date'])
    reserve_date = datetime.datetime.combine(date, datetime.time(int(hour), int(minute)))

    now = datetime.datetime.now()
    if reserve_date < now or reserve_date > now + datetime.timedelta(days=90):
        await call.message.edit_text('➡️ Введите корректную дату (например, "22.08.2023")')
        await states.ReserveTable.waiting_for_date.set()
        return

    db = call.bot.get('database')
    async with db() as session:
        iiko_user = await IikoUser.get_by_telegram_id(session, call.from_user.id)

    iiko: Iiko = call.bot.get('iiko')
    print(state_data['organization'])
    terminal_groups = await iiko.get_terminal_groups([state_data['organization']])
    pprint(terminal_groups.model_dump())
    terminal_group_id = terminal_groups.terminalGroups[0].items[0].id

    tables = await iiko.get_available_tables([str(terminal_group_id)], False)
    section_ids = list()
    all_tables = set()
    for section in tables.restaurantSections:
        section_ids.append(str(section.id))
        for table in section.tables:
            all_tables.add(str(table.id))

    reserves = await iiko.get_reserves(
        section_ids,
        reserve_date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
        (reserve_date + datetime.timedelta(minutes=120)).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    )

    reserved_tables = set()
    for reserve in reserves.reserves:
        for table in reserve.tableIds:
            reserved_tables.add(str(table))

    available_tables = all_tables - reserved_tables
    if not available_tables:
        await call.message.answer('На выбранную дату и время нет свободных мест!', reply_markup=reply_keyboards.main_menu)
        await call.answer()
        await state.finish()
        return

    table = available_tables.pop()

    request = CreateReserveRequest(
        organizationId=state_data['organization'],
        terminalGroupId=str(terminal_group_id),
        customer=OrderCustomer(
            id=str(iiko_user.id),
            type='regular'
        ),
        phone='+' + iiko_user.phone,
        comment='Из бота',
        durationInMinutes=120,
        shouldRemind=True,
        tableIds=[table],
        estimatedStartTime=reserve_date.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
        guests=Guests(
            count=int(state_data.get('guests_count'))
        )
    )

    pprint(request.model_dump())

    print('NO IIKO')

    # created_reserve = await iiko.create_reserve(request)

    print('NO IIKO')

    await call.message.answer(messages.reserve_created, reply_markup=reply_keyboards.main_menu)
    await state.finish()
    await call.answer()


def register_reserve(dp: Dispatcher):
    dp.register_callback_query_handler(start_reserve_table, callbacks.organization.filter(action='res'))

    dp.register_message_handler(get_guests_count, state=states.ReserveTable.waiting_for_guests_count)
    dp.register_message_handler(get_date, state=states.ReserveTable.waiting_for_date)

    dp.register_callback_query_handler(get_time, callbacks.time.filter(action='res'), state=states.ReserveTable.finishing)
