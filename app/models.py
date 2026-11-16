from datetime import datetime, date, time
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Date, Time, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

# FILE MASTER 1: USERS (Role: admin & user)
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nama: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="user")  # admin | user

    reservations: Mapped[list["Reservation"]] = relationship(back_populates="user", cascade="all, delete-orphan")

# FILE MASTER 2: SPACES (Ruangan Co-Working)
class Space(Base):
    __tablename__ = "spaces"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nama_space: Mapped[str] = mapped_column(String(100))
    tipe: Mapped[str] = mapped_column(String(50))  # Hot Desk | Meeting Room | Private Office
    kapasitas: Mapped[int] = mapped_column(Integer)
    harga_per_jam: Mapped[float] = mapped_column(Float)
    fasilitas: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    reservations: Mapped[list["Reservation"]] = relationship(back_populates="space")

# FILE TRANSAKSI: RESERVATIONS
class Reservation(Base):
    __tablename__ = "reservations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    space_id: Mapped[int] = mapped_column(ForeignKey("spaces.id"))
    tanggal: Mapped[date] = mapped_column(Date)
    jam_mulai: Mapped[time] = mapped_column(Time)
    jam_selesai: Mapped[time] = mapped_column(Time)
    total_bayar: Mapped[float] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending | confirmed | cancelled
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    user: Mapped["User"] = relationship(back_populates="reservations")
    space: Mapped["Space"] = relationship(back_populates="reservations")