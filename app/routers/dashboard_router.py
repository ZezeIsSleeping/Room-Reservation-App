from datetime import date
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User, Space, Reservation
from app.auth import require_user
from app.routers.reservations_router import get_max_stock

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

        return templates.TemplateResponse(
            request=request,
            name="dashboard_admin.html",
            context={
                "user": user,
                "total_spaces": total_spaces,
                "total_users": total_users,
                "total_transaksi": total_transaksi,
                "total_pendapatan": total_pendapatan,
                "reservations": reservations
            }
        )

    spaces = db.query(Space).filter(Space.is_active == True).all()
    my_reservations = db.query(Reservation).filter(
        Reservation.user_id == user.id
    ).order_by(Reservation.created_at.desc()).all()

    # Hitung sisa stok hari ini dari pesanan yang sudah di-ACC admin (status == 'confirmed')
    today = date.today()
    stock_map = {}
    for sp in spaces:
        booked_confirmed = db.query(Reservation).filter(
            Reservation.space_id == sp.id,
            Reservation.tanggal == today,
            Reservation.status == "confirmed"
        ).count()
        stock_map[sp.id] = max(0, get_max_stock(sp) - booked_confirmed)

    return templates.TemplateResponse(
        request=request,
        name="dashboard_user.html",
        context={
            "user": user,
            "spaces": spaces,
            "reservations": my_reservations,
            "stock_map": stock_map
        }
    )