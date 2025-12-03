from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command, ChatMemberUpdatedFilter, IS_NOT_MEMBER, IS_MEMBER
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from sqlmodel import Session, select
from .db import engine
from .models import User, Chat
from .reports import generate_excel_report
from .telegram_utils import is_bot_admin
from typing import Optional, List
from datetime import datetime
from worker.src.tasks import process_message # Импортируем задачу Celery напрямую

router = Router()

# ----------------------------------------------------------------------
# Хелперы для работы с БД
# ----------------------------------------------------------------------

def get_user_by_tg_id(tg_user_id: int) -> Optional[User]:
    """Получает пользователя по Telegram ID."""
    with Session(engine) as session:
        statement = select(User).where(User.telegram_user_id == tg_user_id)
        return session.exec(statement).first()

def register_user(tg_user_id: int) -> User:
    """Регистрирует нового пользователя."""
    with Session(engine) as session:
        user = User(telegram_user_id=tg_user_id)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user

def get_user_chats(tg_user_id: int) -> List[Chat]:
    """Получает все чаты, принадлежащие пользователю."""
    with Session(engine) as session:
        statement = select(Chat).where(Chat.owner_id == tg_user_id)
        return session.exec(statement).all()

def get_chat_by_tg_id(tg_chat_id: int) -> Optional[Chat]:
    """Получает чат по Telegram Chat ID."""
    with Session(engine) as session:
        statement = select(Chat).where(Chat.telegram_chat_id == tg_chat_id)
        return session.exec(statement).first()

# ----------------------------------------------------------------------
# Обработчики команд
# ----------------------------------------------------------------------

@router.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    """Обрабатывает команду /start (регистрация)."""
    tg_user_id = message.from_user.id
    user = get_user_by_tg_id(tg_user_id)
    
    if not user:
        user = register_user(tg_user_id)
        await message.answer(
            f"Добро пожаловать, {message.from_user.full_name}! "
            "Вы успешно зарегистрированы в системе. "
            "Ваш ID: {user.telegram_user_id}. "
            "Теперь добавьте меня в чаты, которые вы хотите парсить, как администратора."
        )
    else:
        await message.answer(
            f"С возвращением, {message.from_user.full_name}! "
            "Вы уже зарегистрированы. "
            "Используйте команду /chats, чтобы увидеть список чатов и настроить парсинг."
        )

@router.message(Command("chats"))
async def command_chats_handler(message: Message) -> None:
    """Обрабатывает команду /chats (список чатов)."""
    tg_user_id = message.from_user.id
    user = get_user_by_tg_id(tg_user_id)
    
    if not user:
        await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start.")
        return

    user_chats = get_user_chats(tg_user_id)
    
    if not user_chats:
        await message.answer("У вас пока нет чатов, добавленных для парсинга. Добавьте меня в чат как администратора.")
        return

    text = "Ваши чаты:\n\n"
    keyboard_buttons = []
    
    for chat in user_chats:
        status = "✅ Парсинг включен" if chat.is_parsing_enabled else "❌ Парсинг отключен"
        text += f"**{chat.title}** (ID: `{chat.telegram_chat_id}`)\nСтатус: {status}\n\n"
        
        if chat.is_parsing_enabled:
            keyboard_buttons.append([InlineKeyboardButton(text=f"Отключить парсинг в {chat.title}", callback_data=f"disable_chat_{chat.id}")])
        else:
            keyboard_buttons.append([InlineKeyboardButton(text=f"Включить парсинг в {chat.title}", callback_data=f"enable_chat_{chat.id}")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    await message.answer(text, reply_markup=keyboard, parse_mode="Markdown")


@router.message(Command("report"))
async def command_report_handler(message: Message) -> None:
    """Обрабатывает команду /report (формирование отчета)."""
    tg_user_id = message.from_user.id
    user = get_user_by_tg_id(tg_user_id)
    
    if not user:
        await message.answer("Пожалуйста, сначала зарегистрируйтесь, используя команду /start.")
        return

    try:
        # Генерация отчета
        excel_bytes = generate_excel_report(user_id=user.telegram_user_id)
        
        # Отправка файла
        excel_file = types.BufferedInputFile(excel_bytes, filename="sales_report.xlsx")
        await message.answer_document(
            excel_file,
            caption="Ваш отчет о сообщениях о продаже готов."
        )
        
    except ValueError as e:
        await message.answer(f"Не удалось сформировать отчет: {e}")
    except Exception as e:
        await message.answer(f"Произошла ошибка при генерации отчета: {e}")

# ----------------------------------------------------------------------
# Обработчик добавления/удаления бота из чата (MyChatMember)
# ----------------------------------------------------------------------

@router.my_chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def bot_added_to_chat(update: ChatMemberUpdated) -> None:
    """Обрабатывает событие, когда бот добавлен в чат."""
    chat_id = update.chat.id
    chat_title = update.chat.title
    user_id = update.from_user.id # Пользователь, который добавил бота
    
    user = get_user_by_tg_id(user_id)
    
    if not user:
        # Пользователь не зарегистрирован, игнорируем
        return

    with Session(engine) as session:
        # Проверяем, существует ли уже запись для этого чата и этого пользователя
        statement = select(Chat).where(
            Chat.telegram_chat_id == chat_id,
            Chat.owner_id == user_id
        )
        existing_chat = session.exec(statement).first()
        
        if existing_chat:
            existing_chat.title = chat_title
            session.add(existing_chat)
            session.commit()
            return

        # Создаем новую запись чата, привязанную к пользователю, с отключенным парсингом
        new_chat = Chat(
            telegram_chat_id=chat_id,
            owner_id=user_id,
            title=chat_title,
            is_parsing_enabled=False
        )
        session.add(new_chat)
        session.commit()
        session.refresh(new_chat)
        
        # Отправляем запрос на разрешение парсинга в ЛС
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Включить парсинг", callback_data=f"enable_chat_{new_chat.id}")],
            [InlineKeyboardButton(text="❌ Отключить парсинг", callback_data=f"disable_chat_{new_chat.id}")]
        ])
        
        await update.bot.send_message(
            chat_id=user_id,
            text=f"Вы добавили меня в чат **{chat_title}**. Хотите включить парсинг сообщений о продаже в этом чате?",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )

# ----------------------------------------------------------------------
# Обработчик Callback Query (Да/Нет, Включить/Отключить)
# ----------------------------------------------------------------------

@router.callback_query(F.data.startswith("enable_chat_") | F.data.startswith("disable_chat_"))
async def callback_chat_control(callback: CallbackQuery) -> None:
    """Обрабатывает нажатия кнопок для включения/отключения парсинга."""
    action, chat_db_id_str = callback.data.split("_", 2)
    chat_db_id = int(chat_db_id_str)
    tg_user_id = callback.from_user.id
    
    with Session(engine) as session:
        chat = session.get(Chat, chat_db_id)
        
        if not chat or chat.owner_id != tg_user_id:
            await callback.answer("Ошибка: Чат не найден или не принадлежит вам.", show_alert=True)
            return

        is_enabled = action == "enable_chat"
        chat.is_parsing_enabled = is_enabled
        session.add(chat)
        session.commit()
        session.refresh(chat)
        
        status = "включен" if is_enabled else "отключен"
        
        await callback.message.edit_text(
            f"Парсинг в чате **{chat.title}** успешно {status}.",
            parse_mode="Markdown"
        )
        await callback.answer(f"Парсинг {status}.")

# ----------------------------------------------------------------------
# Обработчик новых сообщений в чатах
# ----------------------------------------------------------------------

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def handle_group_message(message: Message) -> None:
    """Обрабатывает новые сообщения в группах и супергруппах."""
    tg_chat_id = message.chat.id
    
    # 1. Проверяем, есть ли этот чат в нашей БД и включен ли парсинг
    with Session(engine) as session:
        # Находим все записи чата, где включен парсинг (для всех владельцев)
        statement = select(Chat).where(
            Chat.telegram_chat_id == tg_chat_id,
            Chat.is_parsing_enabled == True
        )
        enabled_chats: List[Chat] = session.exec(statement).all()
        
        if not enabled_chats:
            # Парсинг не включен ни для одного из владельцев
            return

    # 2. Собираем данные для воркера
    text = message.text or message.caption or ""
    
    # Собираем информацию о медиафайлах
    media_files = []
    if message.photo:
        # Берем самое большое фото
        file_id = message.photo[-1].file_id
        media_files.append({"file_id": file_id, "file_extension": ".jpg"})
    elif message.video:
        file_id = message.video.file_id
        media_files.append({"file_id": file_id, "file_extension": ".mp4"})
    elif message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or ""
        ext = os.path.splitext(file_name)[1] or ".bin"
        media_files.append({"file_id": file_id, "file_extension": ext})

    # 3. Отправляем задачу в Celery для каждого владельца, включившего парсинг
    for chat_entry in enabled_chats:
        # Отправляем задачу в очередь
        process_message.delay(
            chat_id=tg_chat_id,
            message_id=message.message_id,
            author_id=message.from_user.id,
            text=text,
            timestamp=datetime.fromtimestamp(message.date).isoformat(),
            media_files=media_files
        )
        
        print(f"Task sent to Celery for chat {tg_chat_id} (Owner: {chat_entry.owner_id})")


