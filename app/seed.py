from sqlalchemy.orm import Session
from app.models import Space  # Sesuaikan dengan path model Space Anda

def seed_coworking_spaces(db: Session):
    # Cek jika data sudah 20 ruangan, lewati agar tidak duplikat
    if db.query(Space).count() >= 20:
        return

    # Hapus data lama jika masih data dummy awal (opsional)
    db.query(Space).delete()

    spaces_data = []

    # 1. 10 Ruangan Essential (3,5x3,5m | Max 4 org | 50k/jam)
    for i in range(1, 11):
        spaces_data.append(Space(
            nama_space=f"Essential {i:02d}",
            tipe="Essential",
            kapasitas=4,
            fasilitas="Ukuran 3,5x3,5m • AC • Ruangan Kedap Suara • WiFi 50 Mbps",
            harga_per_jam=50000
        ))

    # 2. 7 Ruangan Premium (6x6m | Max 9 org | 100k/jam)
    for i in range(1, 8):
        spaces_data.append(Space(
            nama_space=f"Premium {i:02d}",
            tipe="Premium",
            kapasitas=9,
            fasilitas="Ukuran 6x6m • AC • Ruangan Kedap Suara • Papan Tulis Kaca • View Danau • WiFi 80 Mbps",
            harga_per_jam=100000
        ))

    # 3. 3 Ruangan Executive (10x10m | Max 9 org | 150k/jam)
    for i in range(1, 4):
        spaces_data.append(Space(
            nama_space=f"Executive {i:02d}",
            tipe="Executive",
            kapasitas=9,
            fasilitas="Ukuran 10x10m • AC • Ruangan Kedap Suara • Smart Board Interactive • Speaker • Kursi Premium • View Danau • WiFi 100 Mbps",
            harga_per_jam=150000
        ))

    db.add_all(spaces_data)
    db.commit()