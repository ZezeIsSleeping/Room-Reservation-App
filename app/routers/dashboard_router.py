from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Space, Reservation
from app.auth import require_user

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/dashboard")
def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_user)
):
    if user.role == "admin":
        total_spaces = db.query(Space).count()
        total_users = db.query(User).filter(User.role == "user").count()
        total_transaksi = db.query(Reservation).count()
        total_pendapatan = db.query(func.coalesce(func.sum(Reservation.total_bayar), 0)).filter(
            Reservation.status == "confirmed"
        ).scalar()
        reservations = db.query(Reservation).order_by(Reservation.created_at.desc()).all()

        return templates.TemplateResponse("dashboard_admin.html", {
            "request": request,
            "user": user,
            "total_spaces": total_spaces,
            "total_users": total_users,
            "total_transaksi": total_transaksi,
            "total_pendapatan": total_pendapatan,
            "reservations": reservations
        })

    # Dashboard untuk Role User
    spaces = db.query(Space).filter(Space.is_active == True).all()
    my_reservations = db.query(Reservation).filter(
        Reservation.user_id == user.id
    ).order_by(Reservation.created_at.desc()).all()

    return templates.TemplateResponse("dashboard_user.html", {
        "request": request,
        "user": user,
        "spaces": spaces,
        "reservations": my_reservations
    })