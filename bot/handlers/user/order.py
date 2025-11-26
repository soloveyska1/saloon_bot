"""
Хендлеры воронки заказа
FSM для оформления заказа
"""

import logging
from pathlib import Path

from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.order import OrderForm
from bot.keyboards.inline import (
    get_work_types_kb,
    get_deadline_kb,
    get_files_done_kb,
    get_order_summary_kb,
    get_main_menu_kb,
    WORK_TYPES,
    DEADLINES,
)
from database.models import Order, User
from config import config

router = Router(name="order")
logger = logging.getLogger(__name__)

# Путь к изображениям
ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets"
ORDER_START_IMAGE = ASSETS_DIR / "order_start.jpg"
ORDER_SUMMARY_IMAGE = ASSETS_DIR / "order_summary.jpg"


# =============================================================================
# ШАГ 1: Начало заказа - выбор типа работы
# =============================================================================

@router.callback_query(F.data == "order_work")
async def start_order(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Начало оформления заказа
    Callback: order_work
    """
    await callback.answer()

    # Сбрасываем предыдущее состояние (если было)
    await state.clear()

    # Инициализируем список файлов
    await state.update_data(file_ids=[])

    # Устанавливаем состояние ожидания выбора типа
    await state.set_state(OrderForm.waiting_for_type)

    caption = """📝 <b>Открываю новый бланк заказа...</b>

Так-так, партнёр, давай оформим всё как положено.

<b>Для начала выбери, что будем писать:</b> 👇"""

    keyboard = get_work_types_kb()

    # Отправляем с фото или без
    if ORDER_START_IMAGE.exists():
        photo = FSInputFile(ORDER_START_IMAGE)
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        await callback.message.delete()
        await callback.message.answer(
            text=caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )


# =============================================================================
# ШАГ 2: Обработка выбора типа работы -> запрос предмета/темы
# =============================================================================

@router.callback_query(OrderForm.waiting_for_type, F.data.startswith("type_"))
async def process_work_type(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработка выбора типа работы
    Callback: type_coursework, type_diploma, etc.
    """
    await callback.answer()

    # Получаем выбранный тип
    work_type_key = callback.data  # например "type_coursework"
    work_type_name = WORK_TYPES.get(work_type_key, "Неизвестный тип")

    # Сохраняем в состояние
    await state.update_data(
        work_type_key=work_type_key,
        work_type_name=work_type_name,
    )

    # Переходим к следующему шагу
    await state.set_state(OrderForm.waiting_for_subject)

    text = f"""✅ <b>Принято:</b> {work_type_name}

✍️ <b>Теперь напиши название предмета и тему работы.</b>

<i>Например: "Экономика предприятия. Анализ финансовой деятельности ООО Ромашка"</i>

💡 Можешь отправить текстом или голосовым сообщением."""

    # Редактируем или отправляем новое сообщение
    try:
        await callback.message.edit_caption(
            caption=text,
            parse_mode="HTML",
            reply_markup=None,  # Убираем клавиатуру, ждём текст
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
        )


# =============================================================================
# ШАГ 3: Обработка предмета/темы -> запрос дедлайна
# =============================================================================

@router.message(OrderForm.waiting_for_subject, F.text)
async def process_subject_text(message: Message, state: FSMContext) -> None:
    """
    Обработка текстового ввода предмета/темы
    """
    subject = message.text.strip()

    # Проверяем минимальную длину
    if len(subject) < 5:
        await message.answer(
            "⚠️ Слишком короткое описание, партнёр. Напиши хотя бы предмет и тему.",
            parse_mode="HTML",
        )
        return

    # Сохраняем тему
    await state.update_data(subject=subject)

    # Переходим к выбору дедлайна
    await state.set_state(OrderForm.waiting_for_deadline)

    text = f"""✅ <b>Тема записана!</b>

📋 <i>"{subject[:100]}{'...' if len(subject) > 100 else ''}"</i>

📅 <b>Когда нужно сдавать работу?</b>

Выбери срочность — от этого зависит цена:"""

    await message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=get_deadline_kb(),
    )


@router.message(OrderForm.waiting_for_subject, F.voice)
async def process_subject_voice(message: Message, state: FSMContext) -> None:
    """
    Обработка голосового сообщения
    """
    # Сохраняем голосовое сообщение
    await state.update_data(
        subject="[Голосовое сообщение — требуется расшифровка]",
        voice_file_id=message.voice.file_id,
    )

    await state.set_state(OrderForm.waiting_for_deadline)

    text = """✅ <b>Голосовое сообщение получено!</b>

🎙 Наш специалист прослушает его при обработке заказа.

📅 <b>Когда нужно сдавать работу?</b>

Выбери срочность — от этого зависит цена:"""

    await message.answer(
        text=text,
        parse_mode="HTML",
        reply_markup=get_deadline_kb(),
    )


# =============================================================================
# ШАГ 4: Обработка выбора дедлайна -> запрос файлов
# =============================================================================

@router.callback_query(OrderForm.waiting_for_deadline, F.data.startswith("deadline_"))
async def process_deadline(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработка выбора дедлайна
    Callback: deadline_week, deadline_medium, deadline_urgent
    """
    await callback.answer()

    # Получаем выбранный дедлайн
    deadline_key = callback.data
    deadline_info = DEADLINES.get(deadline_key)

    if deadline_info:
        deadline_name, deadline_code = deadline_info
    else:
        deadline_name = "Неизвестный срок"
        deadline_code = "unknown"

    # Сохраняем в состояние
    await state.update_data(
        deadline_key=deadline_key,
        deadline_name=deadline_name,
        deadline_code=deadline_code,
    )

    # Переходим к загрузке файлов
    await state.set_state(OrderForm.waiting_for_files)

    text = f"""✅ <b>Сроки понятны:</b> {deadline_name}

📂 <b>Теперь скинь методички, примеры или фото задания.</b>

Можешь отправить:
• 📄 Документы (PDF, DOCX, и т.д.)
• 🖼 Фото/скриншоты
• 📎 Любые файлы

<i>Отправляй по одному или несколько сразу. Когда закончишь — нажми кнопку «Готово».</i>"""

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_files_done_kb(),
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_files_done_kb(),
        )


# =============================================================================
# ШАГ 5: Обработка файлов
# =============================================================================

@router.message(OrderForm.waiting_for_files, F.photo)
async def process_file_photo(message: Message, state: FSMContext) -> None:
    """Обработка фото"""
    data = await state.get_data()
    file_ids = data.get("file_ids", [])

    # Берём самое большое фото (последнее в списке)
    file_id = message.photo[-1].file_id
    file_ids.append(f"photo:{file_id}")

    await state.update_data(file_ids=file_ids)

    await message.answer(
        f"📸 Фото принято! (всего файлов: {len(file_ids)})\n\n"
        "<i>Ещё? Или жми «Готово».</i>",
        parse_mode="HTML",
        reply_markup=get_files_done_kb(),
    )


@router.message(OrderForm.waiting_for_files, F.document)
async def process_file_document(message: Message, state: FSMContext) -> None:
    """Обработка документов"""
    data = await state.get_data()
    file_ids = data.get("file_ids", [])

    file_id = message.document.file_id
    file_name = message.document.file_name or "document"
    file_ids.append(f"doc:{file_id}:{file_name}")

    await state.update_data(file_ids=file_ids)

    await message.answer(
        f"📄 Документ «{file_name}» принят! (всего файлов: {len(file_ids)})\n\n"
        "<i>Ещё? Или жми «Готово».</i>",
        parse_mode="HTML",
        reply_markup=get_files_done_kb(),
    )


# =============================================================================
# ШАГ 6: Завершение загрузки файлов -> показ сводки
# =============================================================================

@router.callback_query(OrderForm.waiting_for_files, F.data.in_({"files_done", "files_skip"}))
async def process_files_done(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Завершение загрузки файлов
    Показ сводки заказа
    """
    await callback.answer()

    # Получаем все данные
    data = await state.get_data()
    file_ids = data.get("file_ids", [])
    files_count = len(file_ids)

    # Формируем сводку заказа
    summary = f"""📋 <b>КАРТОЧКА ЗАКАЗА</b>
➖➖➖➖➖➖➖➖➖➖

📝 <b>Тип работы:</b> {data.get('work_type_name', '—')}

📚 <b>Тема:</b>
<i>{data.get('subject', '—')[:200]}</i>

⏰ <b>Срочность:</b> {data.get('deadline_name', '—')}

📎 <b>Файлов прикреплено:</b> {files_count}

➖➖➖➖➖➖➖➖➖➖

<b>Всё верно?</b> Подтверди заказ, и Шеф получит уведомление! 🤠"""

    # Переходим к состоянию подтверждения
    await state.set_state(OrderForm.waiting_for_confirmation)

    # Отправляем сводку
    if ORDER_SUMMARY_IMAGE.exists():
        photo = FSInputFile(ORDER_SUMMARY_IMAGE)
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo,
            caption=summary,
            parse_mode="HTML",
            reply_markup=get_order_summary_kb(),
        )
    else:
        try:
            await callback.message.edit_text(
                text=summary,
                parse_mode="HTML",
                reply_markup=get_order_summary_kb(),
            )
        except Exception:
            await callback.message.delete()
            await callback.message.answer(
                text=summary,
                parse_mode="HTML",
                reply_markup=get_order_summary_kb(),
            )


# =============================================================================
# ШАГ 7: Подтверждение заказа -> сохранение в БД
# =============================================================================

@router.callback_query(F.data == "confirm_order")
async def confirm_order(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    user: User,
    bot: Bot,
) -> None:
    """
    Подтверждение и сохранение заказа в БД
    """
    await callback.answer("Оформляем заказ...")

    # Получаем данные из FSM
    data = await state.get_data()

    # Формируем строку file_ids
    file_ids_list = data.get("file_ids", [])
    file_ids_str = ",".join(file_ids_list) if file_ids_list else None

    # Создаём заказ в БД
    order = Order(
        user_id=user.id,
        work_type=data.get("work_type_key", "unknown"),
        work_type_name=data.get("work_type_name", "Неизвестный тип"),
        subject=data.get("subject", ""),
        deadline=data.get("deadline_code", "unknown"),
        deadline_name=data.get("deadline_name", "Неизвестный срок"),
        file_ids=file_ids_str,
        voice_file_id=data.get("voice_file_id"),
        status="new",
    )

    session.add(order)
    await session.flush()  # Получаем ID заказа

    order_id = order.id

    # Очищаем FSM
    await state.clear()

    # Отправляем подтверждение пользователю
    success_text = f"""🎉 <b>ЗАКАЗ №{order_id} ПРИНЯТ!</b>

Йо-хо, партнёр! Твоя заявка уже летит к Шефу на стол.

📋 <b>Что дальше:</b>
1. Шеф оценит объём работы
2. Ты получишь цену и сроки
3. После оплаты 50% — начнём работу

⏳ <i>Обычно отвечаем в течение часа (в рабочее время).</i>

<b>Номер заказа:</b> <code>#{order_id}</code>
<i>Сохрани его — пригодится для связи!</i>"""

    try:
        await callback.message.edit_text(
            text=success_text,
            parse_mode="HTML",
            reply_markup=get_main_menu_kb(),
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=success_text,
            parse_mode="HTML",
            reply_markup=get_main_menu_kb(),
        )

    # Отправляем уведомление админам
    await notify_admins_about_order(bot, order, user, len(file_ids_list))

    logger.info(f"Новый заказ #{order_id} от пользователя {user.telegram_id}")


async def notify_admins_about_order(
    bot: Bot,
    order: Order,
    user: User,
    files_count: int,
) -> None:
    """Отправка уведомления админам о новом заказе"""

    admin_text = f"""🔔 <b>НОВЫЙ ЗАКАЗ #{order.id}!</b>

👤 <b>Клиент:</b> {user.first_name} (@{user.username or 'без username'})
🆔 <b>Telegram ID:</b> <code>{user.telegram_id}</code>

📝 <b>Тип:</b> {order.work_type_name}
📚 <b>Тема:</b> {order.subject[:200]}
⏰ <b>Срочность:</b> {order.deadline_name}
📎 <b>Файлов:</b> {files_count}

🕐 <b>Статус:</b> Новый"""

    for admin_id in config.admin_ids:
        try:
            await bot.send_message(
                chat_id=admin_id,
                text=admin_text,
                parse_mode="HTML",
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")


# =============================================================================
# ОТМЕНА ЗАКАЗА
# =============================================================================

@router.callback_query(F.data == "cancel_order")
async def cancel_order(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Отмена оформления заказа
    Возврат в главное меню
    """
    await callback.answer("Заказ отменён")

    # Очищаем состояние
    await state.clear()

    text = """❌ <b>Заказ отменён.</b>

Ничего, партнёр, возвращайся когда будешь готов!

<i>Выбери действие в меню:</i> 👇"""

    try:
        await callback.message.edit_text(
            text=text,
            parse_mode="HTML",
            reply_markup=get_main_menu_kb(),
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=text,
            parse_mode="HTML",
            reply_markup=get_main_menu_kb(),
        )


# =============================================================================
# ОПЛАТА (заглушка)
# =============================================================================

@router.callback_query(F.data.startswith("pay_order_"))
async def process_payment(callback: CallbackQuery) -> None:
    """Заглушка оплаты для пользователя"""
    order_id = callback.data.split("_")[-1]
    await callback.answer(
        f"💳 Переход к оплате заказа №{order_id}...\n\n"
        f"Функция оплаты будет добавлена в следующем обновлении.\n"
        f"Свяжитесь с нами для оплаты.",
        show_alert=True,
    )
