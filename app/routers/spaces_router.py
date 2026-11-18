from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models import Space, User
from app.auth import require_admin

router = APIRouter(prefix="/spaces")
templates = Jinja2Templates(directory="templates")

@router.get("")
def list_spaces(
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    spaces = db.query(Space).order_by(Space.id.asc()).all()
    return templates.TemplateResponse(
        request=request,
        name="spaces_list.html",
        context={
            "user": admin,
            "spaces": spaces
        }
    )

@router.post("/create")
def create_space(
    nama_space: str = Form(...),
    tipe: str = Form(...),
    kapasitas: int = Form(...),
    harga_per_jam: float = Form(...),
    fasilitas: str = Form(...),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    space = Space(
        nama_space=nama_space,
        tipe=tipe,
        kapasitas=kapasitas,
        harga_per_jam=harga_per_jam,
        fasilitas=fasilitas,
        is_active=True
    )
    db.add(space)
    db.commit()
    return RedirectResponse(url="/spaces?msg=Space+berhasil+ditambahkan", status_code=303)

@router.get("/{space_id}/edit")
def edit_space_page(
    space_id: int,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    space = db.query(Space).filter(Space.id == space_id).first()
    if not space:
        return RedirectResponse(url="/spaces?err=Space+tidak+ditemukan", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="space_edit.html",
        context={
            "user": admin,
            "space": space
        }
    )

@router.post("/{space_id}/edit")
def edit_space_submit(
    space_id: int,
    nama_space: str = Form(...),
    tipe: str = Form(...),
    kapasitas: int = Form(...),
    harga_per_jam: float = Form(...),
    fasilitas: str = Form(...),
    is_active: str | None = Form(None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    space = db.query(Space).filter(Space.id == space_id).first()
    if space:
        space.nama_space = nama_space
        space.tipe = tipe
        space.kapasitas = kapasitas
        space.harga_per_jam = harga_per_jam
        space.fasilitas = fasilitas
        space.is_active = True if is_active == "on" else False
        db.commit()
    return RedirectResponse(url="/spaces?msg=Data+space+berhasil+diperbarui", status_code=303)

@router.post("/{space_id}/delete")
def delete_space(
    space_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin)
):
    space = db.query(Space).filter(Space.id == space_id).first()
    if space:
        try:
            db.delete(space)
            db.commit()
            return RedirectResponse(url="/spaces?msg=Space+berhasil+dihapus", status_code=303)
        except IntegrityError:
            db.rollback()
            space.is_active = False
            db.commit()
            return RedirectResponse(
                url="/spaces?err=Space+memiliki+riwayat+transaksi,+status+diubah+menjadi+Nonaktif",
                status_code=303
            )
    return RedirectResponse(url="/spaces", status_code=303)