from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from bot.config import YOUR_ADMIN_ID

class AdminMiddleware(BaseMiddleware):
    """Middleware to check if user is admin."""

    def __init__(self, admin_ids: list[int]):
        super().__init__()
        self.admin_ids = admin_ids

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        if event.from_user.id not in self.admin_ids:
            if isinstance(event, Message):
                await event.answer("Доступ запрещён.")
            elif isinstance(event, CallbackQuery):
                await event.answer("Доступ запрещён.", show_alert=True)
            return
        return await handler(event, data)