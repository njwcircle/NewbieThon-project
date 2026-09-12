from datetime import date

from . import models


def effective_payment_status(payment: models.Payment, today: date | None = None) -> models.PaymentStatus:
    """PAID는 그대로 두고, 나머지는 오늘 날짜 기준으로 PENDING/OVERDUE를 즉시 계산한다.

    DB의 status 컬럼을 배치로 갱신하는 대신 조회 시점에 계산해서, 별도 스케줄러 없이도
    항상 정확한 상태를 보여준다.
    """
    if payment.status == models.PaymentStatus.PAID:
        return models.PaymentStatus.PAID
    today = today or date.today()
    if payment.due_date < today:
        return models.PaymentStatus.OVERDUE
    return models.PaymentStatus.PENDING
