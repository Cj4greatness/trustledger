from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from datetime import datetime, timezone

from database import engine, SessionLocal, Base
import models
import auth_config
import bcrypt
from chatbot import interpret_message
from invoice import generate_invoice_pdf
from forex import get_usd_to_ngn_rate
from fastapi.responses import StreamingResponse

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=auth_config.SECRET_KEY)
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

OVERDUE_DAYS = 3

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user

class ChatMessage(BaseModel):
    message: str

def get_owned_transaction_or_404(transaction_id: int, owner_id: int, db: Session):
    t = db.query(models.Transaction).filter(
        models.Transaction.id == transaction_id,
        models.Transaction.owner_id == owner_id
    ).first()
    if not t:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return t

def check_overdue(t):
    if t.delivery_status == "shipped" and t.shipped_at:
        shipped_at = t.shipped_at
        if shipped_at.tzinfo is None:
            shipped_at = shipped_at.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - shipped_at).days >= OVERDUE_DAYS
    return False

def log_event(db: Session, transaction_id: int, event_type: str, note: str = None):
    event = models.TransactionEvent(transaction_id=transaction_id, event_type=event_type, note=note)
    db.add(event)
    db.commit()

@app.get("/")
def read_root():
    return {"status": "TrustLedger API is running"}

@app.get("/signup")
def signup_page(request: Request):
    return templates.TemplateResponse(request, "signup.html", {"error": None})

@app.post("/signup")
def signup_submit(
    request: Request,
    business_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        return templates.TemplateResponse(request, "signup.html", {"error": "An account with that email already exists."})

    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    new_user = models.User(business_name=business_name, email=email, password_hash=password_hash)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    request.session["user_id"] = new_user.id
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})

@app.post("/login")
def login_submit(request: Request, email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == email).first()
    if user and bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        request.session["user_id"] = user.id
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(request, "login.html", {"error": "Invalid email or password"})

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)

@app.get("/settings")
def settings_page(request: Request, user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse(request, "settings.html", {"user": user, "message": None, "error": None})

@app.post("/settings")
def settings_update(
    request: Request,
    business_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(""),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    existing = db.query(models.User).filter(models.User.email == email, models.User.id != user.id).first()
    if existing:
        return templates.TemplateResponse(request, "settings.html", {"user": user, "message": None, "error": "That email is already in use by another account."})

    user.business_name = business_name
    user.email = email
    if password:
        user.password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    db.commit()
    db.refresh(user)
    return templates.TemplateResponse(request, "settings.html", {"user": user, "message": "Settings updated successfully.", "error": None})

@app.get("/dashboard")
def dashboard(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    transactions = db.query(models.Transaction).filter(models.Transaction.owner_id == user.id).all()
    for t in transactions:
        t.is_overdue = check_overdue(t)
    usd_rate = get_usd_to_ngn_rate()
    return templates.TemplateResponse(request, "dashboard.html", {"transactions": transactions, "user": user, "usd_rate": usd_rate})

@app.get("/wallet")
def wallet(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    base_q = db.query(models.Transaction).filter(models.Transaction.owner_id == user.id)
    total_confirmed = base_q.filter(models.Transaction.payment_status == "confirmed").with_entities(func.sum(models.Transaction.amount)).scalar() or 0
    count_confirmed = base_q.filter(models.Transaction.payment_status == "confirmed").count()
    total_pending = base_q.filter(models.Transaction.payment_status == "pending").with_entities(func.sum(models.Transaction.amount)).scalar() or 0
    count_pending = base_q.filter(models.Transaction.payment_status == "pending").count()

    wallets = [{
        "business_name": user.business_name,
        "total_confirmed": total_confirmed,
        "count_confirmed": count_confirmed,
        "total_pending": total_pending,
        "count_pending": count_pending
    }]
    return templates.TemplateResponse(request, "wallet.html", {"wallets": wallets, "user": user})

@app.get("/chat")
def chat_page(request: Request, user: models.User = Depends(get_current_user)):
    return templates.TemplateResponse(request, "chat.html", {"user": user})

@app.post("/chat/send")
def chat_send(chat: ChatMessage, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    result = interpret_message(chat.message)
    action = result.get("action")
    params = result.get("params", {})
    reply = result.get("reply", "")

    if action == "create_transaction":
        try:
            new_transaction = models.Transaction(
                business_name=user.business_name,
                owner_id=user.id,
                customer_contact=params["customer_contact"],
                item_description=params["item_description"],
                amount=float(params["amount"])
            )
            db.add(new_transaction)
            db.commit()
            db.refresh(new_transaction)
            log_event(db, new_transaction.id, "created", "Created via assistant")
            reply += f" (Transaction No. {new_transaction.id:06d} created.)"
        except (KeyError, ValueError):
            reply = "I couldn't create that transaction — missing or invalid details."

    elif action in ("confirm_payment", "mark_shipped", "confirm_delivery", "check_status"):
        t = db.query(models.Transaction).filter(
            models.Transaction.id == params.get("transaction_id"),
            models.Transaction.owner_id == user.id
        ).first()
        if not t:
            reply = "I couldn't find that transaction on your account."
        elif action == "confirm_payment":
            t.payment_status = "confirmed"
            db.commit()
            log_event(db, t.id, "payment_confirmed", "Confirmed via assistant")
            reply += f" (Payment confirmed for No. {t.id:06d}.)"
        elif action == "mark_shipped":
            if t.payment_status == "confirmed":
                t.delivery_status = "shipped"
                t.shipped_at = datetime.now(timezone.utc)
                db.commit()
                log_event(db, t.id, "shipped", "Marked shipped via assistant")
                reply += f" (No. {t.id:06d} marked as shipped.)"
            else:
                reply = "Can't mark that as shipped — payment hasn't been confirmed yet."
        elif action == "confirm_delivery":
            if t.delivery_status == "shipped":
                t.delivery_status = "delivered"
                t.overall_status = "closed"
                db.commit()
                log_event(db, t.id, "delivered", "Delivery confirmed via assistant")
                reply += f" (No. {t.id:06d} delivered and closed.)"
            else:
                reply = "That item hasn't been marked as shipped yet."
        elif action == "check_status":
            reply = f"No. {t.id:06d} — payment: {t.payment_status}, delivery: {t.delivery_status}, overall: {t.overall_status}."

    return {"reply": reply}

@app.post("/transactions/new")
def create_transaction_from_form(
    customer_contact: str = Form(...),
    item_description: str = Form(...),
    amount: float = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    new_transaction = models.Transaction(
        business_name=user.business_name,
        owner_id=user.id,
        customer_contact=customer_contact,
        item_description=item_description,
        amount=amount
    )
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    log_event(db, new_transaction.id, "created", "Created from dashboard")
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/transactions/{transaction_id}/invoice")
def download_invoice(transaction_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    t = get_owned_transaction_or_404(transaction_id, user.id, db)
    events = db.query(models.TransactionEvent).filter(models.TransactionEvent.transaction_id == t.id).order_by(models.TransactionEvent.created_at.asc()).all()
    pdf_buffer = generate_invoice_pdf(t, user, events)
    filename = f"invoice_{t.id:06d}.pdf"
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})

@app.get("/transactions/{transaction_id}/view")
def transaction_detail(transaction_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    t = get_owned_transaction_or_404(transaction_id, user.id, db)
    t.is_overdue = check_overdue(t)
    events = db.query(models.TransactionEvent).filter(
        models.TransactionEvent.transaction_id == t.id
    ).order_by(models.TransactionEvent.created_at.asc()).all()
    return templates.TemplateResponse(request, "detail.html", {"t": t, "user": user, "events": events})

@app.post("/transactions/{transaction_id}/confirm-payment")
def confirm_payment(transaction_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    t = get_owned_transaction_or_404(transaction_id, user.id, db)
    t.payment_status = "confirmed"
    db.commit()
    log_event(db, t.id, "payment_confirmed", "Confirmed from dashboard")
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/transactions/{transaction_id}/mark-shipped")
def mark_shipped(transaction_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    t = get_owned_transaction_or_404(transaction_id, user.id, db)
    if t.payment_status != "confirmed":
        raise HTTPException(status_code=400, detail="Cannot ship before payment is confirmed")
    t.delivery_status = "shipped"
    t.shipped_at = datetime.now(timezone.utc)
    db.commit()
    log_event(db, t.id, "shipped", "Marked shipped from dashboard")
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/transactions/{transaction_id}/confirm-delivery")
def confirm_delivery(transaction_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    t = get_owned_transaction_or_404(transaction_id, user.id, db)
    if t.delivery_status != "shipped":
        raise HTTPException(status_code=400, detail="Item has not been marked as shipped yet")
    t.delivery_status = "delivered"
    t.overall_status = "closed"
    db.commit()
    log_event(db, t.id, "delivered", "Delivery confirmed from dashboard")
    return RedirectResponse(url="/dashboard", status_code=303)
