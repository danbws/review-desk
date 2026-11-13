from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.gateway.deps import current_user, get_db
from app.models import User
from app.schemas import CheckoutIn, CheckoutOut, PlanOut, UsageOut
from app.services import billing

router = APIRouter(prefix="/api", tags=["billing"])


@router.get("/plans", response_model=list[PlanOut])
def plans():
    return [PlanOut(**p.__dict__) for p in billing.PLANS.values()]


@router.get("/usage", response_model=UsageOut)
def usage(request: Request, user: User = Depends(current_user), db: Session = Depends(get_db)):
    return billing.usage_summary(db, request.app.state.cache, user)


@router.post("/billing/checkout", response_model=CheckoutOut)
def checkout(
    body: CheckoutIn,
    request: Request,
    user: User = Depends(current_user),
    db: Session = Depends(get_db),
):
    if body.plan not in billing.PLANS:
        raise HTTPException(status_code=422, detail="Unknown plan")
    provider = request.app.state.payments
    result = billing.change_plan(db, provider, user, body.plan)
    return CheckoutOut(plan=body.plan, provider=provider.name, **result)
