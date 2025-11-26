"""
Хендлеры воронки заказа
FSM для оформления заказа
"""

from pathlib import Path

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, FSInputFile
from aiogram.fsm.context import FSMContext

from bot.states.order import OrderForm
from bot.keyboards.inline import (
    get_work_types_kb,
    get_deadline_kb,
    get_main_menu_kb,
    WORK_TYPES,
    DEADLINES,
)

router = Router(name="order")

# Путь к изображениям
ASSETS_DIR = Path(__file__).parent.parent.parent.parent / "assets"
ORDER_START_IMAGE = ASSETS_DIR / "order_start.jpg"


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
    Обработка голосового сообщения (заглушка)
    В будущем можно добавить распознавание через Whisper API
    """
    # Пока сохраняем как заглушку
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
# ШАГ 4: Обработка выбора дедлайна
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

    # Получаем все данные для сводки
    data = await state.get_data()

    # Формируем сводку заказа
    summary = f"""✅ <b>Отлично, партнёр! Вот твой заказ:</b>

📋 <b>Тип работы:</b> {data.get('work_type_name', '—')}
📚 <b>Тема:</b> {data.get('subject', '—')[:150]}
⏰ <b>Срочность:</b> {deadline_name}

➖➖➖➖➖➖➖➖➖➖

🔜 <b>Следующий шаг:</b> загрузка материалов (методичка, примеры).

<i>Эта функция будет добавлена в следующем обновлении.</i>
<i>Пока что заказ сохранён как черновик.</i>"""

    # Пока что завершаем здесь (в будущем продолжим воронку)
    await state.clear()

    try:
        await callback.message.edit_text(
            text=summary,
            parse_mode="HTML",
            reply_markup=get_main_menu_kb(),
        )
    except Exception:
        await callback.message.delete()
        await callback.message.answer(
            text=summary,
            parse_mode="HTML",
            reply_markup=get_main_menu_kb(),
        )


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
