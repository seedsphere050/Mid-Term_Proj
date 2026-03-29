# ============================================================
# CHANGE: NEW FILE — care_reminders/services/sms.py
# Sends SMS via Twilio OR MSG91 (popular in India).
# Set SMS_PROVIDER=twilio or msg91 in your .env file.
# SMS only fires for CRITICAL alerts (2+ missed waterings).
# ============================================================
import os
import logging

logger = logging.getLogger(__name__)

SMS_PROVIDER       = os.environ.get('SMS_PROVIDER', 'twilio')
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN  = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_FROM_NUMBER = os.environ.get('TWILIO_FROM_NUMBER', '')
MSG91_AUTH_KEY     = os.environ.get('MSG91_AUTH_KEY', '')
MSG91_SENDER_ID    = os.environ.get('MSG91_SENDER_ID', 'SEDSPH')
MSG91_TEMPLATE_ID  = os.environ.get('MSG91_TEMPLATE_ID', '')


def send_critical_sms(to_number: str, message: str) -> bool:
    """
    Send a critical care alert SMS.
    Returns True if sent, False on failure.
    Called only when missed_waterings >= 2.
    """
    if not to_number or not message:
        return False
    try:
        if SMS_PROVIDER == 'twilio':
            return _send_twilio(to_number, message)
        elif SMS_PROVIDER == 'msg91':
            return _send_msg91(to_number, message)
        else:
            logger.warning(f'Unknown SMS_PROVIDER: {SMS_PROVIDER}')
            return False
    except Exception as e:
        logger.error(f'SMS send failed: {e}')
        return False


def _send_twilio(to: str, body: str) -> bool:
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(
            body=f'[SeedSphere Alert] {body}',
            from_=TWILIO_FROM_NUMBER,
            to=to,
        )
        logger.info(f'Twilio SMS sent: {msg.sid}')
        return True
    except Exception as e:
        logger.error(f'Twilio error: {e}')
        return False


def _send_msg91(to: str, body: str) -> bool:
    import requests as req
    try:
        # MSG91 expects number without leading +
        number = to.lstrip('+')
        payload = {
            'template_id': MSG91_TEMPLATE_ID,
            'short_url': '0',
            'realTimeResponse': '1',
            'recipients': [{'mobiles': number, 'var1': body[:140]}],
        }
        headers = {
            'accept': 'application/json',
            'content-type': 'application/json',
            'authkey': MSG91_AUTH_KEY,
        }
        resp = req.post('https://api.msg91.com/api/v5/flow/',
                        json=payload, headers=headers, timeout=8)
        resp.raise_for_status()
        logger.info(f'MSG91 SMS sent to {to}')
        return True
    except Exception as e:
        logger.error(f'MSG91 error: {e}')
        return False
