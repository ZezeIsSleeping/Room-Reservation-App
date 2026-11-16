from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.database import engine, Base, SessionLocal
from app.models import User, Space
from app.auth import hash_password
from app.routers import auth_router, dashboard_router, spaces_router, reservations_router, reports_router

def seed_initial_data():
    db = SessionLocal()
    try:
        # Buat akun Admin & User bawaan jika belum ada
        if not db.query(User).filter(User.email == "admin@coworking.com").first():
            db.add(User(
                nama="Administrator",
                email="admin@coworking.com",
                password_hash=hash_password("admin123"),
                role="admin"
            ))
        if not db.query(User).filter(User.email == "user@coworking.com").first():
            db.add(User(
                nama="Budi Santoso",
                email="user@coworking.com",
                password_hash=hash_password("user123"),
                role="user"
            ))

        # Buat 3 contoh ruangan jika tabel spaces kosong
        if db.query(Space).count() == 0:
            db.add_all([
                Space(
                    nama_space="Alpha Hot Desk",
                    tipe="Hot Desk",
                    kapasitas=1,
                    harga_per_jam=25000,
                    fasilitas="WiFi 100Mbps, Stopkontak, Free Kopi/Teh",
                    is_active=True
                ),
                Space(
                    nama_space="Nusantara Meeting Room",
                    tipe="Meeting Room",
                    kapasitas=8,
                    harga_per_jam=120000,
                    fasilitas="Smart TV 55\", Whiteboard, AC, WiFi",
                    is_active=True
                ),
                Space(
                    nama_space="Garuda Private Office",
                    tipe="Private Office",
                    kapasitas=4,
                    harga_per_jam=90000,
                    fasilitas="Ruang Kedap Suara, Meja Eksekutif, Loker",
                    is_active=True
                ),
            ])
        db.commit()
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_initial_data()
    yield

app = FastAPI(title="Co-Working Space Reservation", lifespan=lifespan)

app.include_router(auth_router.router)
app.include_router(dashboard_router.router)
app.include_router(spaces_router.router)
app.include_router(reservations_router.router)
app.include_router(reports_router.router)

@app.get("/")
def root():
    return RedirectResponse(url="/login", status_code=303)