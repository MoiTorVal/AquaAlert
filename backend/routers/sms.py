"""Inbound Twilio SMS webhook: reply-to-log irrigation + alert feedback.

Auth on this route is the Twilio request signature (HMAC over the public
webhook URL + form params) — there is no cookie/JWT, the sender's verified
phone number identifies the account.
"""
import logging
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from xml.sax.saxutils import escape

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from backend import crud, models
from backend.config import settings
from backend.database import get_db
from backend.enums import AlertFeedback, IrrigationSource
from backend.schemas import IrrigationEventCreate
from backend.services import sms_service

router = APIRouter()
logger = logging.getLogger(__name__)

# Y/N replies attach to the user's newest alert, but only a recent one — a
# reply to a month-old alert would label the wrong conditions.
FEEDBACK_WINDOW_DAYS = 7

# "1" or "1 5000": bare 1 inherits the farm's usual gallons (ESTIMATED),
# explicit gallons log as USER_LOG. Bounded so it can't overflow Numeric(10,2).
_IRRIGATION_RE = re.compile(r"^1(?: ([1-9]\d{0,7}))?$")
_YES_WORDS = {"Y", "YES", "S", "SI", "SÍ"}
_NO_WORDS = {"N", "NO"}


def _twiml(body: str | None) -> Response:
    inner = f"<Message>{escape(body)}</Message>" if body else ""
    return Response(
        content=f'<?xml version="1.0" encoding="UTF-8"?><Response>{inner}</Response>',
        media_type="application/xml",
    )


def _resolve_farm(db: Session, user: models.User) -> models.Farm | None:
    """An SMS carries no farm context: a single farm is unambiguous, otherwise
    assume the reply concerns whichever farm was alerted most recently."""
    farms = crud.get_farms(db, user_id=user.id, limit=2)
    if len(farms) == 1:
        return farms[0]
    latest_alert = crud.get_latest_alert_for_user(db, user.id)
    if latest_alert is not None:
        return crud.get_farm(db, latest_alert.farm_id)
    return None


def _format_gallons(gallons: Decimal) -> str:
    return f"{gallons.normalize():f}"


def _log_irrigation(db: Session, user: models.User, gallons_text: str | None) -> str:
    farm = _resolve_farm(db, user)
    if farm is None:
        return sms_service.message(user.locale, "which_farm")
    today = date.today()
    if gallons_text is not None:
        event = crud.create_irrigation_event(
            db, farm.id,
            IrrigationEventCreate(event_date=today, gallons_applied=Decimal(gallons_text)),
        )
        return sms_service.message(
            user.locale, "logged",
            gallons=_format_gallons(event.gallons_applied), farm=farm.name, event_date=today.isoformat(),
        )
    last = crud.get_latest_irrigation_event(db, farm.id)
    if last is None:
        return sms_service.message(user.locale, "need_gallons", farm=farm.name)
    event = crud.create_irrigation_event(
        db, farm.id,
        IrrigationEventCreate(event_date=today, gallons_applied=last.gallons_applied),
        source=IrrigationSource.ESTIMATED,
    )
    return sms_service.message(
        user.locale, "logged_estimated",
        gallons=_format_gallons(event.gallons_applied), farm=farm.name, event_date=today.isoformat(),
    )


def _record_feedback(db: Session, user: models.User, feedback: AlertFeedback) -> str:
    since = datetime.now(timezone.utc) - timedelta(days=FEEDBACK_WINDOW_DAYS)
    alert = crud.get_latest_alert_for_user(db, user.id, since=since)
    if alert is None:
        return sms_service.message(user.locale, "no_recent_alert")
    crud.set_alert_feedback(db, alert, feedback)
    farm = crud.get_farm(db, alert.farm_id)
    return sms_service.message(user.locale, "feedback_thanks", farm=farm.name)


def _handle_reply(db: Session, user: models.User, body: str) -> str:
    normalized = " ".join(body.strip().upper().split())
    match = _IRRIGATION_RE.match(normalized)
    if match:
        return _log_irrigation(db, user, match.group(1))
    if normalized in _YES_WORDS:
        return _record_feedback(db, user, AlertFeedback.YES)
    if normalized in _NO_WORDS:
        return _record_feedback(db, user, AlertFeedback.NO)
    return sms_service.message(user.locale, "help")


@router.post("/webhook")
async def sms_webhook(request: Request, db: Session = Depends(get_db)):
    if not sms_service.is_configured() or settings.sms_webhook_url is None:
        raise HTTPException(status_code=503, detail="SMS is not configured")
    form = await request.form()
    params = {key: str(value) for key, value in form.items()}
    signature = request.headers.get("X-Twilio-Signature", "")
    if not sms_service.validate_signature(settings.sms_webhook_url, params, signature):
        logger.warning("Rejected SMS webhook call with invalid signature")
        raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    user = crud.get_user_by_phone(db, params.get("From", ""))
    if user is None:
        # 200 + empty TwiML: a 4xx would make Twilio retry, and any reply
        # body could leak which phone numbers have accounts.
        return _twiml(None)
    return _twiml(_handle_reply(db, user, params.get("Body", "")))
