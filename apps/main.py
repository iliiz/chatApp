from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from fastapi import FastAPI, Request, Form, Depends, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker
from passlib.context import CryptContext
import uvicorn

from .models import Base, User, Message
from .email import generate_otp, send_otp_email

# ── Database ───────────────────────────────────────────────────────────────────
# Relative path — db file lands next to wherever you run uvicorn from.
# Change to an absolute path if needed: "sqlite:///C:/data/app.db"
DATABASE_URL = "sqlite:///F:/download/DataBase/sqlite-tools-win-x64-3530100/app.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ── Password hashing ───────────────────────────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

# ── OTP store ─────────────────────────────────────────────────────────────────
pending_users: dict[str, dict] = {}
OTP_LIFETIME_MINUTES = 10

# ── Lifespan ───────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    # ── Seed: ensure at least one admin account exists ────────────────────────
    # On first run this creates admin / admin@station.local with password "admin".
    # CHANGE THE PASSWORD immediately after first login via /profile → edit.
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.is_admin == True).first():
            seed = User(
                username="admin",
                email="admin@station.local",
                password=hash_password("admin"),
                is_admin=True,
            )
            db.add(seed)
            db.commit()
            print("[startup] Admin account created — username: admin  password: admin")
            print("[startup] !! Change this password immediately after first login !!")
    finally:
        db.close()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

templates = Jinja2Templates(directory="templates")

# ── Helpers ────────────────────────────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session) -> User | None:
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    try:
        return db.get(User, int(user_id))
    except (ValueError, TypeError):
        return None

def require_user(request: Request, db: Session) -> User:
    """Return the current user or raise 401."""
    user = get_current_user(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not logged in")
    return user

def require_admin(request: Request, db: Session) -> User:
    """Return the current user only if they are an admin, else raise 403."""
    user = get_current_user(request, db)
    # FIX 1: original logic was `if not current_user or current_user.is_admin` which
    # BLOCKED admins and let everyone else through — completely inverted.
    # FIX 2: `HTTPExeption` typo → `HTTPException`
    if not user or not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return user

# ── Page routes ────────────────────────────────────────────────────────────────

@app.get("/")
def read_root(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    return templates.TemplateResponse(request, "Home.html", {"user": user})

@app.get("/chat")
def read_chat(request: Request, receiver_id: int | None = None, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    if receiver_id is None:
        return RedirectResponse("/contact", status_code=302)

    receiver_user = db.get(User, receiver_id)
    if not receiver_user:
        raise HTTPException(status_code=404, detail="User not found")

    messages = (
        db.query(Message)
        .filter(
            ((Message.sender_id == user.id) & (Message.receiver_id == receiver_id))
            | ((Message.sender_id == receiver_id) & (Message.receiver_id == user.id))
        )
        .order_by(Message.created_at)
        .all()
    )

    return templates.TemplateResponse(
        request, "chatPage.html",
        {"user": user, "receiver_user": receiver_user, "messages": messages},
    )

@app.get("/login")
def read_login(request: Request, db: Session = Depends(get_db)):
    if get_current_user(request, db):
        return RedirectResponse("/contact", status_code=302)
    return templates.TemplateResponse(request, "Login.html")

@app.get("/signup")
def read_signup(request: Request, db: Session = Depends(get_db)):
    if get_current_user(request, db):
        return RedirectResponse("/contact", status_code=302)
    return templates.TemplateResponse(request, "signUp.html")

@app.get("/profile")
def read_profile(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(request, "profile.html", {"user": user})

@app.get("/edit")
def read_edit(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    return templates.TemplateResponse(request, "edit.html", {"user": user})

@app.get("/contact")
def read_contact(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=302)
    users = db.query(User).filter(User.id != user.id).all()
    return templates.TemplateResponse(request, "contact.html", {"users": users, "user": user})

@app.get("/admin")
def admin_panel(request: Request, db: Session = Depends(get_db)):
    # FIX: uses require_admin which correctly checks is_admin == True
    current_user = require_admin(request, db)

    all_users = db.query(User).order_by(User.id.desc()).all()

    chart_labels, chart_user_data, chart_msg_data = [], [], []
    for i in range(6, -1, -1):
        target_date = (datetime.now(timezone.utc) - timedelta(days=i)).date()
        date_str = target_date.strftime("%Y-%m-%d")
        chart_labels.append(target_date.strftime("%b %d"))
        chart_user_data.append(
            db.query(User).filter(func.strftime("%Y-%m-%d", User.created_at) <= date_str).count()
        )
        chart_msg_data.append(
            db.query(Message).filter(func.strftime("%Y-%m-%d", Message.created_at) <= date_str).count()
        )

    return templates.TemplateResponse(
        request, "admin.html",
        {
            "current_user": current_user,
            "users": all_users,
            "chart_labels": chart_labels,
            "chart_user_data": chart_user_data,
            "chart_msg_data": chart_msg_data,
        },
    )

# ── Auth API ───────────────────────────────────────────────────────────────────

@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"success": False, "message": "Invalid username or password"},
        )
    resp = JSONResponse(content={"success": True, "message": "Login successful", "is_admin": user.is_admin})
    resp.set_cookie(key="user_id", value=str(user.id), httponly=True, samesite="lax")
    return resp

@app.post("/signup")
def signup(
    username: str = Form(...),
    password: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    if db.query(User).filter(User.username == username).first():
        return JSONResponse(status_code=409, content={"success": False, "message": "Username already exists"})
    if db.query(User).filter(User.email == email).first():
        return JSONResponse(status_code=409, content={"success": False, "message": "Email already registered"})

    otp = generate_otp()
    if not send_otp_email(email, otp):
        return JSONResponse(status_code=500, content={"success": False, "message": "Failed to send verification email."})

    pending_users[email] = {
        "username": username,
        "password": hash_password(password),
        "otp": otp,
        "expires_at": datetime.now(timezone.utc) + timedelta(minutes=OTP_LIFETIME_MINUTES),
    }
    return JSONResponse(content={"success": True, "message": f"Verification code sent to {email}"})

@app.post("/verify-otp")
def verify_otp(
    email: str = Form(...),
    code: str = Form(...),
    db: Session = Depends(get_db),
):
    entry = pending_users.get(email)
    if not entry:
        return JSONResponse(status_code=400, content={"success": False, "message": "No pending signup found. Please start over."})
    if datetime.now(timezone.utc) > entry["expires_at"]:
        del pending_users[email]
        return JSONResponse(status_code=400, content={"success": False, "message": f"Code expired ({OTP_LIFETIME_MINUTES} min limit). Please sign up again."})
    if entry["otp"] != code.strip():
        return JSONResponse(status_code=401, content={"success": False, "message": "Incorrect code. Please try again."})

    db.add(User(username=entry["username"], password=entry["password"], email=email))
    db.commit()
    del pending_users[email]
    return JSONResponse(content={"success": True, "message": "Account created! Redirecting to login…"})

# ── Chat API ───────────────────────────────────────────────────────────────────

@app.post("/chat")
def chat(
    request: Request,
    message: str = Form(...),
    receiver_id: int = Form(...),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    if not db.get(User, receiver_id):
        raise HTTPException(status_code=404, detail="Receiver not found")

    msg = Message(content=message.strip(), sender_id=user.id, receiver_id=receiver_id)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return JSONResponse(content={
        "success": True,
        "message": "Message sent",
        "message_id": msg.id,
        "created_at": msg.created_at.strftime("%H:%M"),
    })

@app.post("/chat/delete")
def delete_message(
    request: Request,
    message_id: int = Form(...),
    receiver_id: int = Form(...),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    msg = db.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.sender_id != user.id or msg.receiver_id != receiver_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    db.delete(msg)
    db.commit()
    return JSONResponse(content={"success": True})

@app.patch("/chat/edit")
def edit_message(
    request: Request,
    message_id: int = Form(...),
    new_content: str = Form(...),
    receiver_id: int = Form(...),
    db: Session = Depends(get_db),
):
    user = require_user(request, db)
    msg = db.get(Message, message_id)
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    if msg.sender_id != user.id or msg.receiver_id != receiver_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    clean = new_content.strip()
    if msg.content == clean:
        return JSONResponse(status_code=400, content={"success": False, "message": "No changes."})
    msg.content = clean
    db.commit()
    return JSONResponse(content={"success": True})

# ── Profile edit ───────────────────────────────────────────────────────────────

@app.patch("/edit")
def edit_profile(
    request: Request,
    username: str = Form(None),
    password: str = Form(None),
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)
    if not user:
        return JSONResponse(status_code=401, content={"success": False, "message": "Not authenticated."})

    if username and username.strip() and username.strip() != user.username:
        if db.query(User).filter(User.username == username.strip()).first():
            return JSONResponse(status_code=409, content={"success": False, "message": "Username already taken."})
        user.username = username.strip()

    if password and password.strip():
        user.password = hash_password(password)

    db.commit()
    return JSONResponse(content={"success": True, "message": "Profile updated."})

# ── Admin API ──────────────────────────────────────────────────────────────────
# FIX: both endpoints now call require_admin so only admins can use them

@app.post("/admin/delete-user")
def admin_delete_user(
    request: Request,
    user_id: int = Form(...),
    db: Session = Depends(get_db),
):
    admin = require_admin(request, db)  # FIX: was checking only if logged in, not if admin
    if user_id == admin.id:
        return JSONResponse(status_code=400, content={"success": False, "message": "Cannot delete your own account."})
    target = db.get(User, user_id)
    if not target:
        return JSONResponse(status_code=404, content={"success": False, "message": "User not found."})
    db.delete(target)
    db.commit()
    return JSONResponse(content={"success": True})

@app.post("/admin/edit-user")
def admin_edit_user(
    request: Request,
    user_id: int = Form(...),
    new_username: str = Form(...),
    new_email: str = Form(...),
    db: Session = Depends(get_db),
):
    require_admin(request, db)  # FIX: same — was open to any logged-in user
    target = db.get(User, user_id)
    if not target:
        return JSONResponse(status_code=404, content={"success": False, "message": "User not found."})
    if db.query(User).filter(User.username == new_username.strip(), User.id != user_id).first():
        return JSONResponse(status_code=409, content={"success": False, "message": "Username already taken."})
    if db.query(User).filter(User.email == new_email.strip(), User.id != user_id).first():
        return JSONResponse(status_code=409, content={"success": False, "message": "Email already in use."})
    target.username = new_username.strip()
    target.email = new_email.strip()
    db.commit()
    return JSONResponse(content={"success": True})

# ── Logout ─────────────────────────────────────────────────────────────────────

@app.post("/logout")
def logout():
    resp = RedirectResponse("/login", status_code=302)
    resp.delete_cookie("user_id")
    return resp

# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("apps.main:app", host="127.0.0.1", port=8000)