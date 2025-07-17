# ---------------------------------------------------------------------
# webhook_utils.py
# app/services/scheduler/webhook_utils.py
# Execute Webhook trigger for expired messages
# ---------------------------------------------------------------------

import traceback

import requests

from app.utils.logging import log_error_message, log_info_message


# ---------------------------------------------------------------------
# execute_webhooks
# ---------------------------------------------------------------------
def execute_webhooks(message):
    """
    Send HTTP POST requests to all enabled webhooks linked to the given message.

    Args:
        message: The message object (should have .webhooks, .label, .id, .subject, .content).

    Logging:
        - log_info_message for delivery attempts and successes.
        - log_error_message for failures and exceptions.
    """
    try:
        log_info_message(
            f"Scheduler [ExecuteWebhooks] - Success - Executing Webhook(s) for message: {message.label}"
        )

        if not message.webhooks:
            log_info_message(
                f"Scheduler [ExecuteWebhooks] - Success - No webhooks linked to this message."
            )
            return

        for webhook in message.webhooks:
            if not webhook.enabled:
                continue

            log_info_message(
                f"Scheduler [ExecuteWebhooks] - Success - Sending webhook: {webhook.label} → {webhook.endpoint}"
            )

            try:
                payload = {
                    "message_id": message.id,
                    "label": message.label,
                    "subject": message.subject,
                    "content": message.content,
                }

                headers = {"User-Agent": "grylli-webhook"}

                response = requests.post(
                    webhook.endpoint,
                    json=payload,
                    headers=headers,
                    timeout=5,
                )

                if response.status_code == 200:
                    log_info_message(
                        f"Scheduler [ExecuteWebhooks] - Success - Webhook delivered: {webhook.label}"
                    )
                else:
                    log_error_message(
                        f"ERROR - Scheduler [ExecuteWebhooks] - Failure - Webhook [{webhook.label}] failed with status {response.status_code}: {response.text}"
                    )

            except Exception as e:
                log_error_message(
                    f"ERROR - Scheduler [ExecuteWebhooks] - Failure - Exception during webhook [{webhook.label}]: {e}\n{traceback.format_exc()}"
                )

    except Exception as e:
        log_error_message(
            f"ERROR - Scheduler [ExecuteWebhooks] - Failure - Unexpected error in execute_webhooks: {e}\n{traceback.format_exc()}"
        )
