"""
Services package - бизнес-логика
Enterprise CRM Services
"""

from services.logger_service import (
    log_to_channel,
    log_new_user,
    log_new_order,
    log_payment,
    log_order_status,
    log_error,
    log_file_received,
    log_terms_accepted,
    LOG_CHANNEL_ID,
)

from services.transaction_service import (
    add_transaction,
    deposit,
    pay_for_order,
    refund,
    add_bonus,
    get_user_balance,
    get_user_transactions,
    calculate_total_spent,
    calculate_total_deposited,
    InsufficientBalanceError,
    UserNotFoundError,
)

__all__ = [
    # Logger Service
    "log_to_channel",
    "log_new_user",
    "log_new_order",
    "log_payment",
    "log_order_status",
    "log_error",
    "log_file_received",
    "log_terms_accepted",
    "LOG_CHANNEL_ID",
    # Transaction Service
    "add_transaction",
    "deposit",
    "pay_for_order",
    "refund",
    "add_bonus",
    "get_user_balance",
    "get_user_transactions",
    "calculate_total_spent",
    "calculate_total_deposited",
    "InsufficientBalanceError",
    "UserNotFoundError",
]
