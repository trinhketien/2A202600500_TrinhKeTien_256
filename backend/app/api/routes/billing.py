"""
Billing Routes — Stripe subscription (code sẵn, kích hoạt khi có STRIPE_SECRET_KEY).

POST /api/billing/checkout  → Tạo Stripe Checkout Session
POST /api/billing/webhook   → Nhận webhook từ Stripe
GET  /api/billing/status    → Trạng thái subscription
POST /api/billing/cancel    → Hủy subscription
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from backend.app.config import settings
from backend.app.api.deps import get_db, get_current_user
from backend.app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["Billing"])


def _check_stripe():
    """Check Stripe key available."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(
            status_code=503,
            detail="Stripe chưa được cấu hình. Liên hệ admin.",
        )


@router.post("/checkout", summary="Tạo Stripe Checkout Session")
async def create_checkout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Redirect user sang Stripe để thanh toán."""
    _check_stripe()

    # Parse optional body
    target_tier = "pro"
    try:
        body = await request.json()
        target_tier = body.get("target_tier", "pro")
    except Exception:
        # No body = default auto-detect
        target_tier = "premium" if current_user.tier == "pro" else "pro"

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        # Price IDs từ Stripe Dashboard
        price_map = {
            "free": None,
            "pro": "price_pro_monthly",      # Thay bằng ID thực
            "premium": "price_premium_monthly",
        }

        price_id = price_map.get(target_tier)

        if not price_id:
            raise HTTPException(status_code=400, detail="Gói không hợp lệ")

        checkout_session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.FRONTEND_URL or 'http://localhost:3000'}/?payment=success",
            cancel_url=f"{settings.FRONTEND_URL or 'http://localhost:3000'}/?payment=cancel",
            client_reference_id=current_user.id,
            customer_email=current_user.email,
        )

        return {"checkout_url": checkout_session.url}

    except ImportError:
        raise HTTPException(status_code=503, detail="stripe SDK chưa install")
    except Exception as e:
        logger.error(f"[Billing] Checkout failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook", summary="Stripe Webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Nhận webhook từ Stripe — upgrade/downgrade tier."""
    _check_stripe()

    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY

        payload = await request.body()
        sig = request.headers.get("stripe-signature", "")

        # Verify webhook signature
        event = stripe.Webhook.construct_event(
            payload, sig, settings.STRIPE_WEBHOOK_SECRET,
        )

        if event["type"] == "checkout.session.completed":
            session_obj = event["data"]["object"]
            user_id = session_obj.get("client_reference_id")

            if user_id:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    # Parse tier từ line_items price_id
                    line_items = session_obj.get("line_items", {}).get("data", [])
                    price_id = line_items[0]["price"]["id"] if line_items else ""
                    tier_map = {
                        "price_pro_monthly": "pro",
                        "price_premium_monthly": "premium",
                    }
                    new_tier = tier_map.get(price_id, "pro")
                    user.tier = new_tier
                    db.commit()
                    logger.info(f"[Billing] User {user_id} upgraded to {new_tier}")

        elif event["type"] == "customer.subscription.deleted":
            data_obj = event["data"]["object"]
            customer_email = data_obj.get("customer_email", "")

            if customer_email:
                user = db.query(User).filter(User.email == customer_email).first()
                if user:
                    user.tier = "free"
                    db.commit()
                    logger.info(f"[Billing] User {user.email} downgraded to free")
            else:
                logger.warning("[Billing] Cannot find user for cancelled subscription")

        return {"received": True}

    except Exception as e:
        logger.error(f"[Billing] Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status", summary="Trạng thái subscription")
async def billing_status(current_user: User = Depends(get_current_user)):
    """Trạng thái subscription hiện tại."""
    return {
        "tier": current_user.tier or "free",
        "stripe_configured": bool(settings.STRIPE_SECRET_KEY),
    }


@router.post("/cancel", summary="Hủy subscription")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Hủy subscription — downgrade to free."""
    _check_stripe()

    # Reset tier
    current_user.tier = "free"
    db.commit()

    return {"message": "Đã hủy subscription. Tài khoản chuyển về gói Free."}
