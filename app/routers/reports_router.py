import csv
import io
from datetime import datetime
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Reservation, Space, User
from app.auth import require_admin

router = APIRouter(prefix="/reports")
templates = Jinja2Templates(directory="templates")

def _filter_transactions(db: Session, start_date: str | None, end_date: str | None):
    query = db.query(Reservation).order_by(Reservation.tanggal.desc(), Reservation.jam_mulai.asc())
    if start_date:
        query = query.filter(Reservation.tanggal >= datetime.strptime(start_date, "%Y-%m-%d").date())
    if end_date:
        query = query.filter(Reservation.tanggal <= datetime.strptime(end_date, "%Y-%m-%d").date())
    return query.all()

@router.get("")
def report_page(
    request: Request,
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    transaksi = _filter_transactions(db, start_date, end_date)
    spaces = db.query(Space).all()

    rekap_spaces = []
    for sp in spaces:
        sp_trx = [t for t in transaksi if t.space_id == sp.id and t.status == "confirmed"]
        total_jam = sum(
            (datetime.combine(t.tanggal, t.jam_selesai) - datetime.combine(t.tanggal, t.jam_mulai)).seconds / 3600
            for t in sp_trx
        )
        total_rp = sum(t.total_bayar for t in sp_trx)
        rekap_spaces.append({
            "nama_space": sp.nama_space,
            "tipe": sp.tipe,
            "jumlah_booking": len(sp_trx),
            "total_jam": round(total_jam, 1),
            "total_pendapatan": total_rp
        })

    grand_total = sum(t.total_bayar for t in transaksi if t.status == "confirmed")

    return templates.TemplateResponse(
        request=request,
        name="reports.html",
        context={
            "user": admin,
            "transaksi": transaksi,
            "rekap_spaces": rekap_spaces,
            "grand_total": grand_total,
            "start_date": start_date or "",
            "end_date": end_date or ""
        }
    )

@router.get("/export-csv")
def export_csv(
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    transaksi = _filter_transactions(db, start_date, end_date)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["ID Booking", "Nama Penyewa", "Email", "Nama Space", "Tipe", "Tanggal", "Jam Mulai", "Jam Selesai", "Total Bayar", "Status"])

    for t in transaksi:
        writer.writerow([
            t.id,
            t.user.nama,
            t.user.email,
            t.space.nama_space,
            t.space.tipe,
            t.tanggal,
            t.jam_mulai.strftime("%H:%M"),
            t.jam_selesai.strftime("%H:%M"),
            t.total_bayar,
            t.status
        ])

    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=laporan_reservasi_coworking.csv"}
    )