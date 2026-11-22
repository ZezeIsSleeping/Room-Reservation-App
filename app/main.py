from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database import engine, Base, SessionLocal
from app.models import User, Space
from app.auth import hash_password
from app.routers import auth_router, dashboard_router, spaces_router, reservations_router, reports_router

BASE_DIR = Path(__file__).resolve().parent.parent

try:
    Base.metadata.create_all(bind=engine)
    seed_initial_data()
except Exception as e:
    print(f"Database init warning: {e}")

def seed_initial_data():
    db = SessionLocal()
    try:
        # Buat 3 pilihan ruangan sesuai spesifikasi baru jika tabel spaces kosong
        if db.query(Space).count() == 0:
            db.add_all([
                Space(
                    nama_space="Essential",
                    tipe="Essential",
                    kapasitas=4,
                    harga_per_jam=50000,
                    fasilitas="Ukuran 3,5x3,5m, AC, Ruangan Kedap, WiFi 50Mb/s",
                    is_active=True
                ),
                Space(
                    nama_space="Premium",
                    tipe="Premium",
                    kapasitas=9,
                    harga_per_jam=100000,
                    fasilitas="Ukuran 6x6m, AC, Ruangan Kedap, Papan Tulis Kaca, View Danau, WiFi 80Mb/s",
                    is_active=True
                ),
                Space(
                    nama_space="Executive",
                    tipe="Executive",
                    kapasitas=9,
                    harga_per_jam=150000,
                    fasilitas="Ukuran 10x10m, AC, Ruangan Kedap, Smart Board Interactive, Speaker, Kursi Premium, View Danau, WiFi 100Mb/s",
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

assets_dir = BASE_DIR / "assets"
if assets_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app.include_router(auth_router.router)
app.include_router(dashboard_router.router)
app.include_router(spaces_router.router)
app.include_router(reservations_router.router)
app.include_router(reports_router.router)

@app.get("/")
def root():
    return RedirectResponse(url="/login", status_code=303)