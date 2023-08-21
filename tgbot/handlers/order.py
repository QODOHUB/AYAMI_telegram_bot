import datetime
import uuid
from pprint import pprint

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import CallbackQuery, Message, inline_keyboard
from yookassa import Payment
from yookassa.domain.response import PaymentResponse

from tgbot.config import Config
from tgbot.keyboards import inline_keyboards, reply_keyboards
from tgbot.misc import states, messages, callbacks, reply_commands
from tgbot.services.database.models import TelegramUser, Product, OrderProduct, Order as DBOrder, Organization
from tgbot.services.iiko.api import Iiko
from tgbot.services.iiko.schemas import (DeliveryCreate, Order, OrderCustomer, OrderPayment, OrderItem,
                                         SuitableTerminalGroupsRequest, DeliveryAddress, CalculateCheckinRequest,
                                         DeliveryPoint, Address, Street)
from tgbot.services.utils import update_user_from_api, update_menu_from_api, update_organizations_from_api


async def customer_pickup(call: CallbackQuery):
    iiko: Iiko = call.bot.get('iiko')
    db = call.bot.get('database')

    async with db() as session:
        await update_organizations_from_api(session, iiko)
        organizations = await Organization.get_all(session)

    await call.message.delete()
    await call.message.answer(f'Для отмены нажмите кнопку "{reply_commands.cancel}"',
                              reply_markup=reply_keyboards.cancel)
    await call.message.answer('Из какого ресторана вам удобно сделать самовывоз?',
                              reply_markup=inline_keyboards.get_organizations_keyboard(organizations))
    await states.Order.finishing.set()
    await call.answer()


async def get_pickup_point(call: CallbackQuery, callback_data: dict, state: FSMContext):
    await state.update_data(organization=callback_data['id'])
    cur_date = datetime.datetime.now()
    start_date = cur_date + datetime.timedelta(hours=2)
    if cur_date.weekday() in (4, 5):
        end_date = datetime.datetime.combine(datetime.date.today(), datetime.time(23, 59)) + datetime.timedelta(
            minutes=1)
    else:
        end_date = datetime.datetime.combine(datetime.date.today(), datetime.time(23, 0))
    interval = 30

    await call.message.answer('К какому времени доставить заказ?',
                              reply_markup=inline_keyboards.get_time_keyboard(start_date, end_date, interval))
    await call.answer()


async def start_address_input(call: CallbackQuery, state: FSMContext):
    await call.message.answer('➡️ Введите название города/населенного пункта',
                              reply_markup=reply_keyboards.cancel)
    await call.message.delete()
    await states.Order.first()
    await state.update_data(delivery='1')
    await call.answer()


async def get_city(message: Message, state: FSMContext):
    city = message.text
    if len(city) > 60:
        await message.answer('Название города/населенного пункта должно быть короче')
        return

    await message.answer('➡️ Введите название улицы')
    await state.update_data(city=city)
    await states.Order.next()


async def get_street(message: Message, state: FSMContext):
    street = message.text
    if len(street) > 60:
        await message.answer('Название улицы должно быть короче')
        return

    await message.answer('➡️ Введите номер дома')
    await state.update_data(street=street)
    await states.Order.next()


async def get_house(message: Message, state: FSMContext):
    house = message.text
    if len(house) > 10:
        await message.answer('Номер дома должен быть короче')
        return

    iiko: Iiko = message.bot.get('iiko')
    db = message.bot.get('database')
    async with db() as session:
        tg_user = await session.get(TelegramUser, message.from_user.id)
        await session.refresh(tg_user, ['iiko_user'])
        await session.refresh(tg_user.iiko_user, ['cart_products'])

        payment_sum = 0
        for cart_product in tg_user.iiko_user.cart_products:
            await session.refresh(cart_product, ['product'])
            payment_sum += cart_product.product.price * cart_product.quantity

        organizations = await iiko.get_organizations(False, False)
        state_data = await state.get_data()
        suitable_terminals = await iiko.get_terminal_groups_for_delivery(SuitableTerminalGroupsRequest(
            organizationIds=[str(org.id) for org in organizations.organizations],
            deliveryAddress=DeliveryAddress(
                city=state_data['city'],
                streetName=state_data['street'],
                house=house
            ),
            isCourierDelivery=True,
            deliverySum=payment_sum
        ))

        if not suitable_terminals.allowedItems:
            config = message.bot.get('config')
            await message.answer(messages.bad_address_or_sum,
                                 reply_markup=inline_keyboards.get_delivery_zones_keyboard(config.iiko.map_url, True))
            await state.finish()
            return

        allowed_item = suitable_terminals.allowedItems[0]
        if allowed_item.deliveryServiceProductId:
            delivery_product = await session.get(Product, allowed_item.deliveryServiceProductId)
            delivery_price = delivery_product.price
        else:
            delivery_price = 0

    await message.answer(
        messages.good_address.format(delivery_cost=delivery_price, duration=allowed_item.deliveryDurationInMinutes),
        reply_markup=inline_keyboards.get_skip_keyboard('entrance')
    )
    await state.update_data(house=house,
                            delivery_product=allowed_item.deliveryServiceProductId,
                            organization=allowed_item.organizationId,
                            terminal_group=allowed_item.terminalGroupId)
    await states.Order.next()


async def skip(call: CallbackQuery, callback_data: dict):
    value = callback_data['value']

    if value == 'entrance':
        await call.message.edit_text('➡️ Введите этаж', reply_markup=inline_keyboards.get_skip_keyboard('floor'))
    elif value == 'floor':
        await call.message.edit_text('➡️ Введите номер квартиры',
                                     reply_markup=inline_keyboards.get_skip_keyboard('flat'))
    elif value == 'flat':
        await call.message.edit_text('➡️ Введите комментарий',
                                     reply_markup=inline_keyboards.get_skip_keyboard('comment'))
    elif value == 'comment':
        start_date = datetime.datetime.now() + datetime.timedelta(hours=2)
        end_date = datetime.datetime.combine(datetime.date.today(), datetime.time(22))
        interval = 30

        await call.message.edit_text('К какому времени доставить заказ?',
                                     reply_markup=inline_keyboards.get_time_keyboard(start_date, end_date, interval))

    await states.Order.next()
    await call.answer()


async def get_entrance(message: Message, state: FSMContext):
    entrance = message.text
    if len(entrance) > 10:
        await message.answer('Номер подъезда (входа) должен быть короче',
                             reply_markup=inline_keyboards.get_skip_keyboard('entrance'))
        return

    await message.answer('➡️ Введите этаж', reply_markup=inline_keyboards.get_skip_keyboard('floor'))
    await state.update_data(entrance=entrance)
    await states.Order.next()


async def get_floor(message: Message, state: FSMContext):
    floor = message.text
    if len(floor) > 10:
        await message.answer('Этаж должен быть короче', reply_markup=inline_keyboards.get_skip_keyboard('floor'))
        return

    await message.answer('➡️ Введите номер квартиры', reply_markup=inline_keyboards.get_skip_keyboard('flat'))
    await state.update_data(floor=floor)
    await states.Order.next()


async def get_flat(message: Message, state: FSMContext):
    flat = message.text
    if len(flat) > 10:
        await message.answer('Номер квартиры должен быть короче',
                             reply_markup=inline_keyboards.get_skip_keyboard('flat'))
        return

    await message.answer('➡️ Введите комментарий', reply_markup=inline_keyboards.get_skip_keyboard('comment'))
    await state.update_data(flat=flat)
    await states.Order.next()


async def get_comment(message: Message, state: FSMContext):
    comment = message.text
    if len(comment) > 200:
        await message.answer('Комментарий должен быть короче',
                             reply_markup=inline_keyboards.get_skip_keyboard('comment'))
        return

    cur_date = datetime.datetime.now()
    start_date = cur_date + datetime.timedelta(hours=2)
    if cur_date.weekday() in (4, 5):
        end_date = datetime.datetime.combine(datetime.date.today(), datetime.time(23, 59)) + datetime.timedelta(
            minutes=1)
    else:
        end_date = datetime.datetime.combine(datetime.date.today(), datetime.time(23, 0))
    interval = 30

    await message.answer('К какому времени доставить заказ?',
                         reply_markup=inline_keyboards.get_time_keyboard(start_date, end_date, interval))
    await state.update_data(comment=comment)
    await states.Order.next()


async def get_time(call: CallbackQuery, callback_data: dict, state: FSMContext):
    db = call.bot.get('database')

    async with db() as session:
        tg_user = await session.get(TelegramUser, call.from_user.id)
        await session.refresh(tg_user, ['iiko_user'])
        if tg_user.iiko_user.bonus_balance > 0:
            text = messages.pre_pay.format(bonus=tg_user.iiko_user.bonus_balance)
            keyboard = inline_keyboards.bonuses
        else:
            text = 'Выберите способ оплаты'
            keyboard = inline_keyboards.payment_type_choose

    await state.update_data(time=callback_data['time'])
    await call.message.edit_text(text, reply_markup=keyboard)
    await call.answer()


async def with_bonuses(call: CallbackQuery, state: FSMContext):
    db = call.bot.get('database')
    iiko = call.bot.get('iiko')
    async with db() as session:
        tg_user = await session.get(TelegramUser, call.from_user.id)
        await session.refresh(tg_user, ['iiko_user'])
        iiko_user = await update_user_from_api(session, iiko, tg_user.iiko_user.id)
        await session.refresh(iiko_user, ['cart_products'])

        payment_sum = 0
        for cart_product in iiko_user.cart_products:
            await session.refresh(cart_product, ['product'])
            payment_sum += cart_product.product.price * cart_product.quantity

        if iiko_user.bonus_balance >= payment_sum:
            await create_order(call, state)

    await state.update_data(bonuses='1')
    await call.message.edit_text('Выберите способ оплаты', reply_markup=inline_keyboards.payment_type_choose)
    await call.answer()


async def no_bonuses(call: CallbackQuery, state: FSMContext):
    await state.update_data(bonuses='')
    await call.message.edit_text('Выберите способ оплаты', reply_markup=inline_keyboards.payment_type_choose)
    await call.answer()


async def online_pay(call: CallbackQuery, state: FSMContext):
    config = call.bot.get('config')
    db = call.bot.get('database')
    iiko = call.bot.get('iiko')
    redis = call.bot.get('redis')

    state_data = await state.get_data()
    async with db() as session:
        revision = await update_menu_from_api(session, iiko, redis)

        tg_user = await session.get(TelegramUser, call.from_user.id)
        await session.refresh(tg_user, ['iiko_user'])
        iiko_user = await update_user_from_api(session, iiko, tg_user.iiko_user.id)
        await session.refresh(iiko_user, ['cart_products'])

        payment_sum = 0
        for cart_product in iiko_user.cart_products:
            await session.refresh(cart_product, ['product'])
            if cart_product.product.revision != revision:
                await call.message.answer(
                    'Некоторых товаров из корзины больше нет в меню! Проверьте корзину и оформите заказ заново',
                    reply_markup=reply_keyboards.order)
                await state.finish()
                return
            payment_sum += cart_product.product.price * cart_product.quantity

        if state_data.get('bonuses'):
            payment_sum -= iiko_user.bonus_balance

        if del_prod_id := state_data.get('delivery_product'):
            delivery_product = await session.get(Product, del_prod_id)
            payment_sum += delivery_product.price

    payment = Payment.create({
        'amount': {
            'value': payment_sum,
            'currency': 'RUB'
        },
        'confirmation': {
            'type': 'redirect',
            'return_url': config.yookassa.redirect_url
        },
        'capture': True,
        'description': 'Заказ в суши-баре AYAMI'
    }, uuid.uuid4())

    pay_url = payment.confirmation.confirmation_url
    await state.update_data(payment_id=payment.id)
    await call.message.edit_text(f'К оплате {payment_sum}₽\n\nОплатите заказ, затем нажмите "Проверить оплату"',
                                 reply_markup=inline_keyboards.get_pay_keyboard(pay_url, payment.id))
    await call.answer()


async def create_order(call, state, payment: PaymentResponse | None = None):
    state_data = await state.get_data()
    db = call.bot.get('database')
    config: Config = call.bot.get('config')
    iiko: Iiko = call.bot.get('iiko')
    async with db() as session:
        tg_user = await session.get(TelegramUser, call.from_user.id)
        await session.refresh(tg_user, ['iiko_user'])
        iiko_user = await update_user_from_api(session, iiko, tg_user.iiko_user.id)
        await session.refresh(iiko_user, ['cart_products'])

        if state_data.get('offline'):
            redis = call.bot.get('redis')
            revision = await update_menu_from_api(session, iiko, redis)

        items = list()
        payment_sum = 0
        for cart_product in iiko_user.cart_products:
            await session.refresh(cart_product, ['product'])

            if state_data.get('offline') and cart_product.product.revision != revision:
                await call.message.answer(
                    'Некоторых товаров из корзины больше нет в меню! Проверьте корзину и оформите заказ заново',
                    reply_markup=reply_keyboards.order)
                await state.finish()
                return

            payment_sum += cart_product.product.price

            items.append(
                OrderItem(
                    productId=str(cart_product.product.id),
                    type='Product',
                    amount=cart_product.quantity
                )
            )

        delivery_prod_id = state_data.get('delivery_product')

        if delivery_prod_id:
            delivery_product = await session.get(Product, delivery_prod_id)
            payment_sum += delivery_product.price
            items.append(
                OrderItem(
                    productId=delivery_prod_id,
                    type='Product',
                    amount=1
                )
            )

        if state_data.get('offline'):
            payment_type = config.iiko.payments.visa
            is_prepay = False
        else:

            is_prepay = True

        delivery_point = None
        service_type = 'DeliveryPickUp'
        if state_data.get('delivery'):
            service_type = 'DeliveryByCourier'
            delivery_point = DeliveryPoint(
                address=Address(
                    street=Street(
                        city=state_data['city'],
                        name=state_data['street']
                    ),
                    house=state_data['house'],
                    flat=state_data['flat'],
                    entrance=state_data['entrance'],
                    floor=state_data['floor']
                )
            )

        payments = list()
        if payment:
            payments.append(
                OrderPayment(
                    paymentTypeId=payment_type,
                    sum=payment.amount.value,
                    isPrepay=is_prepay,
                    isFiscalizedExternally=True,
                    isProcessedExternally=True,
                    paymentTypeKind='Card'
                )
            )

        if state_data.get('bonuses'):
            if not payment and payment_sum <= iiko_user.bonus_balance:
                await call.message.answer(
                    'У вас недостаточно бонусного баланса для оплаты! Оформите заказ заново',
                    reply_markup=reply_keyboards.order
                )
                await state.finish()
                return
            payments.append(
                OrderPayment(
                    paymentTypeId=config.iiko.payments.bonuses,
                    sum=iiko_user.bonus_balance
                )
            )

        order = Order(
            phone=iiko_user.phone,
            orderServiceType='DeliveryByCourier',
            customer=OrderCustomer(
                id=str(iiko_user.id),
                type='regular'
            ),
            items=items,
            payments=payments,
            deliveryPoint=delivery_point,
            comment=state_data['comment']
        )

        request = CalculateCheckinRequest(
            organizationId=state_data['organization'],
            terminalGroupId=state_data['terminal_group'],
            order=order,
            isLoyaltyTraceEnabled=True
        )

        pprint(request.model_dump())

        calculate_checkin = await iiko.calculate_checkin(request)

        pprint(calculate_checkin.model_dump())

        new_order = DeliveryCreate(
            organizationId=state_data['organization'],
            terminalGroupId=state_data['terminal_group'],
            order=order
        )

        # TODO: создать заказ iiko

        db_order = DBOrder(
            id=uuid.uuid4(),  # TODO: заменить на id из iiko
            iiko_user_id=iiko_user.id,
            payment_sum=payment.amount,
            bonuses=0  # TODO: считать бонусы откуда-то
        )
        session.add(db_order)

        for cart_product in iiko_user.cart_products:
            await session.refresh(cart_product, ['product'])

            db_product = OrderProduct(
                order_id=db_order.id,
                product_id=cart_product.product.id,
                quantity=cart_product.quantity
            )
            session.add(db_product)
            await session.delete(cart_product)

        await session.commit()


async def check_payment(call: CallbackQuery, callback_data: dict, state: FSMContext):
    payment = Payment.find_one(callback_data['id'])
    state_data = await state.get_data()
    if state_data['payment_id'] != callback_data['id']:
        await call.answer('Платёж не соответствует заказу!', show_alert=True)
        return
    if payment.status != 'succeeded':
        await call.answer('Оплата не подтверждена!', show_alert=True)
        return

    await create_order(call, state, payment)

    await call.answer()


async def offline_pay(call: CallbackQuery, state: FSMContext):
    await state.update_data(offline=True)
    await create_order(call, state)
    await call.answer()


def register_order(dp: Dispatcher):
    dp.register_callback_query_handler(start_address_input, text='delivery')
    dp.register_callback_query_handler(customer_pickup, text='pickup')

    dp.register_callback_query_handler(get_pickup_point, callbacks.organization.filter(), state=states.Order.finishing)

    dp.register_message_handler(get_city, state=states.Order.waiting_for_city)
    dp.register_message_handler(get_street, state=states.Order.waiting_for_street)
    dp.register_message_handler(get_house, state=states.Order.waiting_for_house)
    dp.register_message_handler(get_entrance, state=states.Order.waiting_for_entrance)
    dp.register_message_handler(get_floor, state=states.Order.waiting_for_floor)
    dp.register_message_handler(get_flat, state=states.Order.waiting_for_flat)
    dp.register_message_handler(get_comment, state=states.Order.waiting_for_comment)

    dp.register_callback_query_handler(skip, callbacks.skip.filter(), state=states.Order.all_states)

    dp.register_callback_query_handler(get_time, callbacks.time.filter(), state=states.Order.finishing)
    dp.register_callback_query_handler(with_bonuses, text='bonuses', state=states.Order.finishing)
    dp.register_callback_query_handler(no_bonuses, text='no_bonuses', state=states.Order.finishing)
    dp.register_callback_query_handler(online_pay, text='online', state=states.Order.finishing)

    dp.register_callback_query_handler(check_payment, callbacks.check.filter(), state=states.Order.finishing)
