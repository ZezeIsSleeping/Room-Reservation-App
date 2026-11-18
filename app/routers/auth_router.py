from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.auth import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/login")
def login_page(request: Request, user: User | None = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={"user": None})

@router.post("/login")
def login_submit(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        return RedirectResponse(url="/login?err=Email+atau+password+salah", status_code=303)

    token = create_access_token({"sub": str(user.id), "role": user.role})
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True, max_age=43200)
    return response

@router.get("/register")
def register_page(request: Request, user: User | None = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse(request=request, name="register.html", context={"user": None})

@router.post("/register")
def register_submit(
    nama: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return RedirectResponse(url="/register?err=Email+sudah+terdaftar", status_code=303)

    new_user = User(
        nama=nama,
        email=email,
        password_hash=hash_password(password),
        role="user"
    )
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/login?msg=Registrasi+berhasil,+silakan+login", status_code=303)

@router.get("/logout")
def logout():
    response = RedirectResponse(url="/login?msg=Berhasil+logout", status_code=303)
    response.delete_cookie("access_token")
    return response