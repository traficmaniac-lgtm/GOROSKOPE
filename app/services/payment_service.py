from __future__ import annotations

import abc
import logging

logger = logging.getLogger(__name__)


class PaymentService(abc.ABC):
    @abc.abstractmethod
    async def get_balance(self, telegram_id: int) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    async def create_purchase_intent(self, telegram_id: int) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    async def create_subscription_intent(self, telegram_id: int) -> str:
        raise NotImplementedError


class StubPaymentService(PaymentService):
    async def get_balance(self, telegram_id: int) -> str:  # pragma: no cover - stub
        logger.info("Balance requested for %s", telegram_id)
        return "Оплата скоро будет доступна"

    async def create_purchase_intent(self, telegram_id: int) -> str:  # pragma: no cover - stub
        logger.info("Purchase intent for %s", telegram_id)
        return "Скоро можно будет купить дополнительный запрос"

    async def create_subscription_intent(self, telegram_id: int) -> str:  # pragma: no cover - stub
        logger.info("Subscription intent for %s", telegram_id)
        return "Скоро можно будет оформить подписку"
