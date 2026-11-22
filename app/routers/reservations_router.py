from datetime import date, time, datetime
from fastapi import APIRouter, Depends, Form
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Space, Reservation, User
from app.auth import require_user, require_admin

router = APIRouter()


# Helper untuk menentukan batas maksimal stok per tipe ruangan
def get_max_stock(space: Space) -> int:
    tipe = (space.tipe or "").lower()
    nama = (space.nama_space or "").lower()
    if "executive" in tipe or "executive" in nama or space.harga_per_jam >= 150000:
        return 3
    if "premium" in tipe or "premium" in nama or space.harga_per_jam >= 100000:
        return 7
    return 10  # Essential


# Endpoint API real-time untuk mengecek sisa stok ruangan berdasarkan tanggal & jam
@router.get("/api/spaces/stock")
def get_remaining_stock(
    tanggal: date,
    jam_mulai: time,
    jam_selesai: time,
    db: Session = Depends(get_db)
):
    spaces = db.query(Space).filter(Space.is_active == True).all()
    result = {}

    for sp in spaces:
        booked_count = db.query(Reservation).filter(
            Reservation.space_id == sp.id,
            Reservation.tanggal == tanggal,
            Reservation.status == "confirmed",
            and_(Reservation.jam_mulai < jam_selesai, Reservation.jam_selesai > jam_mulai)
        ).count()

        result[str(sp.id)] = max(0, get_max_stock(sp) - booked_count)

    return JSONResponse(result)


@router.post("/reservations/create")
def create_reservation(
    space_id: int = Form(...),
    tanggal: str = Form(...),
    jam_mulai: str = Form(...),
    jam_selesai: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_user)
):
    try:
        tgl = datetime.strptime(tanggal, "%Y-%m-%d").date()
        mulai = datetime.strptime(jam_mulai, "%H:%M").time()
        selesai = datetime.strptime(jam_selesai, "%H:%M").time()
    except ValueError:
        return RedirectResponse(url="/dashboard?err=Format+tanggal+atau+jam+tidak+valid", status_code=303)

    # Validasi anti-tanggal kemarin & jam yang sudah lewat hari ini
    now = datetime.now()
    if tgl < now.date():
        return RedirectResponse(
            url="/dashboard?err=Tidak+bisa+booking+untuk+tanggal+yang+sudah+lewat",
            status_code=303
        )

    if datetime.combine(tgl, mulai) < now:
        return RedirectResponse(
            url="/dashboard?err=Jam+mulai+sudah+terlewat,+pilih+jadwal+berikutnya",
            status_code=303
        )

    if selesai <= mulai:
        return RedirectResponse(url="/dashboard?err=Jam+selesai+harus+lebih+dari+jam+mulai", status_code=303)

    space = db.query(Space).filter(Space.id == space_id, Space.is_active == True).first()
    if not space:
        return RedirectResponse(url="/dashboard?err=Ruangan+tidak+tersedia", status_code=303)

    # Validasi kuota stok yang sudah terkonfirmasi pada tanggal & jam yang sama
    booked_count = db.query(Reservation).filter(
        Reservation.space_id == space_id,
        Reservation.tanggal == tgl,
        Reservation.status == "confirmed",
        and_(Reservation.jam_mulai < selesai, Reservation.jam_selesai > mulai)
    ).count()

    if booked_count >= get_max_stock(space):
        return RedirectResponse(
            url="/dashboard?err=Stok+ruangan+penuh!+Semua+unit+sudah+dipesan+pada+jam+tersebut",
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


@router.post("/reservations/{res_id}/status")
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

    # Validasi kuota stok sebelum admin meng-ACC (confirmed)
    if status == "confirmed" and booking.status != "confirmed":
        confirmed_count = db.query(Reservation).filter(
            Reservation.id != booking.id,
            Reservation.space_id == booking.space_id,
            Reservation.tanggal == booking.tanggal,
            Reservation.status == "confirmed",
            and_(Reservation.jam_mulai < booking.jam_selesai, Reservation.jam_selesai > booking.jam_mulai)
        ).count()

        if confirmed_count >= get_max_stock(booking.space):
            return RedirectResponse(
                url="/dashboard?err=Gagal+konfirmasi!+Stok+ruangan+pada+jadwal+tersebut+sudah+penuh",
                status_code=303
            )

    booking.status = status
    db.commit()
    return RedirectResponse(url=f"/dashboard?msg=Status+reservasi+diubah+menjadi+{status}", status_code=303)


@router.post("/reservations/{res_id}/delete")
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