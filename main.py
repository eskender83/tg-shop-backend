import asyncio
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo
import uvicorn

# --- КОНФИГУРАЦИЯ ---
# Токен получаем у @BotFather. Для безопасности на сервере лучше использовать os.getenv("BOT_TOKEN")
BOT_TOKEN = "9147138196:AAEh2phGNWgKwrC7aBcvKMOpwYXLpggS12k"
# Ссылка на вашу витрину (после загрузки на GitHub Pages)
WEBAPP_URL = "https://eskender83.github.io/my-telegram_shop/"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

# Разрешаем фронтенду отправлять запросы на наш сервер
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- СТРУКТУРА ДАННЫХ ЗАКАЗА ---


class CartItem(BaseModel):
    id: int
    title: str
    price: float
    quantity: int


class Order(BaseModel):
    user_id: int
    user_name: str
    items: list[CartItem]
    total_price: float

# --- КОМАНДЫ БОТА ---


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    # Создаем кнопку, которая откроет сайт прямо внутри Telegram
    ikb = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text="Открыть магазин 🛍️",
                web_app=WebAppInfo(url=WEBAPP_URL)
            )
        ]
    ])
    await message.answer(
        f"Привет, {message.from_user.first_name}! Добро пожаловать в наш магазин.\n"
        "Нажми на кнопку ниже, чтобы перейти к покупкам:",
        reply_markup=ikb
    )

# --- API ДЛЯ ПРИЕМА ЗАКАЗОВ ---


@app.post("/api/order")
async def create_order(order: Order):
    try:
        # Формируем красивый чек для отправки пользователю
        goods_text = ""
        for item in order.items:
            goods_text += f"• {item.title} (x{item.quantity}) — {item.price * item.quantity} руб.\n"

        message_text = (
            f"🎉 **Заказ успешно оформлен!**\n\n"
            f"👤 **Покупатель:** {order.user_name} (ID: {order.user_id})\n\n"
            f"📦 **Состав заказа:**\n{goods_text}\n"
            f"💰 **Итого к оплате:** {order.total_price} руб.\n\n"
            f" Менеджер уже собирает ваш заказ!"
        )

        # Отправляем сообщение пользователю через бота
        await bot.send_message(chat_id=order.user_id, text=message_text, parse_mode="Markdown")
        return {"status": "success", "detail": "Заказ обработан"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ЗАПУСК ---


async def start_bot():
    asyncio.create_task(dp.start_polling(bot))


@app.on_event("startup")
async def on_startup():
    await start_bot()

if __name__ == "__main__":
    # Порт динамически берется из среды сервера (для Render.com) или ставится 8000
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
