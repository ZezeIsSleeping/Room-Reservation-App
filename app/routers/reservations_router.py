from datetime import datetime
from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.database import get_db
from app.models import Reservation, Space, User
from app.auth import require_user, require_admin

router = APIRouter(prefix="/reservations")

@router.post("/create")
def create_reservation(
    space_id: int = Form(...),
    tanggal: str = Form(...),
    jam_mulai: str = Form(...),
    jam_selesai: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_user)
):
    tgl = datetime.strptime(tanggal, "%Y-%m-%d").date()
    mulai = datetime.strptime(jam_mulai, "%H:%M").time()
    selesai = datetime.strptime(jam_selesai, "%H:%M").time()

    if selesai <= mulai:
        return RedirectResponse(url="/dashboard?err=Jam+selesai+harus+lebih+dari+jam+mulai", status_code=303)

    space = db.query(Space).filter(Space.id == space_id, Space.is_active == True).first()
    if not space:
        return RedirectResponse(url="/dashboard?err=Ruangan+tidak+tersedia", status_code=303)

    # Validasi Anti-Bentrok Jadwal
    bentrok = db.query(Reservation).filter(
        Reservation.space_id == space_id,
        Reservation.tanggal == tgl,
        Reservation.status != "cancelled",
        and_(Reservation.jam_mulai < selesai, Reservation.jam_selesai > mulai)
    ).first()

    if bentrok:
        return RedirectResponse(
            url="/dashboard?err=Jadwal+bentrok!+Ruangan+sudah+dipesan+pada+jam+tersebut",
            status_code=303
        )

    durasi_jam = (datetime.combine(tgl, selesai) - datetime.combine(tgl, mulai)).seconds / 3600
    total_bayar = round(durasi_jam * space.harga_per_jam, 2)

    booking = Reservation(
        user_id=user.id,
        space_id=space_id,
        tanggal=tgl,
        jam_mulai=mulai,
        jam_selesai=selesai,
        total_bayar=total_bayar,
        status="pending"
    )
    db.add(booking)
    db.commit()
    return RedirectResponse(url="/dashboard?msg=Reservasi+berhasil+dibuat,+menunggu+konfirmasi+admin", status_code=303)

@router.post("/{res_id}/status")
def update_status(
    res_id: int,
    status: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_user)
):
    booking = db.query(Reservation).filter(Reservation.id == res_id).first()
    if not booking:
        return RedirectResponse(url="/dashboard?err=Transaksi+tidak+ditemukan", status_code=303)

    # User hanya boleh membatalkan pesanannya sendiri
    if user.role != "admin":
        if booking.user_id != user.id or status != "cancelled":
            return RedirectResponse(url="/dashboard?err=Aksi+tidak+diizinkan", status_code=303)

    booking.status = status
    db.commit()
    return RedirectResponse(url=f"/dashboard?msg=Status+reservasi+diubah+menjadi+{status}", status_code=303)

@router.post("/{res_id}/delete")
def delete_reservation(
    res_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    booking = db.query(Reservation).filter(Reservation.id == res_id).first()
    if booking:
        db.delete(booking)
        db.commit()
    return RedirectResponse(url="/dashboard?msg=Data+transaksi+dihapus", status_code=303)