from datetime import date, datetime
from sqlalchemy import Integer, String, Date, DateTime, ForeignKey, Float
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    default_unit: Mapped[str] = mapped_column(String(32), default="раз")

    logs: Mapped[list["WorkoutLog"]] = relationship(back_populates="exercise", cascade="all, delete-orphan")

class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    log_date: Mapped[date] = mapped_column(Date, index=True)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("exercises.id"), index=True)
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[str] = mapped_column(String(32), default="раз")
    notes: Mapped[str | None] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    exercise: Mapped["Exercise"] = relationship(back_populates="logs")