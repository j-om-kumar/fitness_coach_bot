import os
from datetime import date, datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Date, DateTime, Text, ForeignKey, Numeric
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]  # e.g. postgresql+asyncpg://coach:coachpass@localhost:5432/coachdb

Base = declarative_base()
engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_user_id = Column(BigInteger, unique=True, nullable=False)
    chat_id = Column(BigInteger, nullable=False)
    timezone = Column(String(64), default="Asia/Kolkata")
    
    # Registration/Onboarding fields
    registration_completed = Column(Integer, default=0, nullable=False)  # 0=not started, 1=in progress, 2=completed
    height_cm = Column(Numeric(5, 2), nullable=True)
    initial_weight_kg = Column(Numeric(5, 2), nullable=True)
    target_weight_kg = Column(Numeric(5, 2), nullable=True)  # User's weight goal
    goal = Column(String(64), nullable=True)  # e.g., "weight_loss", "muscle_gain", "maintenance"
    activity_level = Column(String(32), nullable=True)  # e.g., "sedentary", "lightly_active", etc.
    
    # Daily nutrition targets
    daily_calorie_target = Column(Integer, nullable=True)  # Calculated target calories
    daily_protein_target = Column(Integer, nullable=True)  # Target protein in grams
    daily_carbs_target = Column(Integer, nullable=True)    # Target carbs in grams
    daily_fats_target = Column(Integer, nullable=True)     # Target fats in grams
    daily_fiber_target = Column(Integer, nullable=True)    # Target fiber in grams
    
    created_at = Column(DateTime, default=datetime.utcnow)

    days = relationship("DailyLog", back_populates="user")




class DailyLog(Base):
    __tablename__ = "daily_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    log_date = Column(Date, default=date.today, nullable=False)

    weight_kg = Column(Numeric(5, 2), nullable=True)
    steps = Column(Integer, nullable=True)
    
    # Photo tracking
    body_photo_file_id = Column(Text, nullable=True)
    weight_scale_photo_file_id = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="days")
    meals = relationship("Meal", back_populates="day")


class Meal(Base):
    __tablename__ = "meals"
    id = Column(Integer, primary_key=True)
    daily_log_id = Column(Integer, ForeignKey("daily_logs.id"), nullable=False)

    meal_type = Column(String(16), nullable=False)  # breakfast/lunch/dinner/snack
    description = Column(Text, nullable=True)

    # Nutritional information
    calories_kcal = Column(Integer, nullable=True)
    protein_g = Column(Integer, nullable=True)
    carbs_g = Column(Integer, nullable=True)
    fats_g = Column(Integer, nullable=True)
    fiber_g = Column(Integer, nullable=True)

    photo_file_id = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


    day = relationship("DailyLog", back_populates="meals")
