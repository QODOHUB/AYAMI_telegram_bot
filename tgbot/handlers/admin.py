from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, MediaGroup, ContentType

from tgbot.keyboards import reply_keyboards
from tgbot.misc import states
from tgbot.services.broadcasters.message_with_media_group import MessageBroadcasterWithMediaGroup
from tgbot.services.database.models import TelegramUser


async def start_mailing(message: Message):
    db = message.bot.get('database')
    async with db() as session:
        tg_user = await session.get(TelegramUser, message.from_id)
        if not tg_user.is_admin:
            await message.answer('Вы не админ!')
            return

    await message.answer('Отправьте сообщение для рассылки.\nОно будет отправлено всем пользователям бота',
                         reply_markup=reply_keyboards.cancel)
    await states.Mailing.first()


async def get_message(message: Message, state: FSMContext, album: list[Message]):
    db = message.bot.get('database')
    async with db() as session:
        telegram_users = await TelegramUser.get_all(session)

    telegram_ids = [tg_user.telegram_id for tg_user in telegram_users]

    if album:
        medias = []
        caption = ''
        for ind, obj in enumerate(album):
            if obj.caption:
                caption = obj.parse_entities()

            if obj.photo:
                file_id = obj.photo[-1].file_id
            else:
                file_id = obj[obj.content_type].file_id
            medias.append({"media": file_id, "type": obj.content_type})

        medias[0]['caption'] = caption
        media_group = MediaGroup()
        media_group.attach_many(*medias)
    else:
        media_group = None

    await MessageBroadcasterWithMediaGroup(
        chats=telegram_ids,
        message=message,
        media_group=media_group
    ).run()

    await message.answer('Сообщение разослано!', reply_markup=reply_keyboards.main_menu)
    await state.finish()


def register_admin(dp: Dispatcher):
    dp.register_message_handler(start_mailing, commands=['post', 'mail', 'mailing'])
    dp.register_message_handler(get_message, state=states.Mailing.waiting_for_message, content_types=[ContentType.ANY])
