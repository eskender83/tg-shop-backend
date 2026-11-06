import asyncio
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo
import uvicorn

# ⚠️ ВСТАВТЕ СВІЙ ТОКЕН СЮДИ
BOT_TOKEN = "ВАШ_ТОКЕН_БОТА"
# Цю посилання ми замінимо пізніше, після завантаження на GitHub Pages
WEBAPP_URL = "https://placeholder.com"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CartItem(BaseModel):
    id: int
    title: str
    price: float
    quantity: int


class Order(BaseModel):
    user_id: int
    user_name: str
    phone: str
    delivery: str
    items: list[CartItem]
    total_price: float


@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    ikb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(
            text="🛒 Відкрити каталог автозапчастин", web_app=WebAppInfo(url=WEBAPP_URL))]
    ])
    await message.answer(
        f"Вітаємо в автомагазині, {message.from_user.first_name}!\n"
        "У нас ви можете замовити деталі для ТО, оливи та автоаксесуари.\n"
        "Натисніть кнопку нижче для переходу до каталогу:",
        reply_markup=ikb
    )


@app.post("/api/order")
async def create_order(order: Order):
    try:
        goods_text = ""
        for item in order.items:
            goods_text += f"• {item.title} (x{item.quantity}) — {item.price * item.quantity} грн.\n"

        message_text = (
            f"🚘 **Нове замовлення автозапчастин!**\n\n"
            f"👤 **Клієнт:** {order.user_name} (ID: {order.user_id})\n"
            f"📞 **Телефон:** {order.phone}\n"
            f"📦 **Доставка:** {order.delivery}\n\n"
            f"📋 **Деталі замовлення:**\n{goods_text}\n"
            f"💰 **Сума до сплати:** {order.total_price} грн.\n\n"
            f"⏳ Менеджер вже перевіряє сумісність деталей за VIN-кодом і зателефонує вам!"
        )

        # Надсилаємо чек користувачу в чат
        await bot.send_message(chat_id=order.user_id, text=message_text, parse_mode="Markdown")
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def start_bot():
    asyncio.create_task(dp.start_polling(bot))


@app.on_event("startup")
async def on_startup():
    await start_bot()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
