from datetime import datetime,timezone
from sqlalchemy import String,Integer,DateTime,ForeignKey,Boolean,Text,UniqueConstraint
from sqlalchemy.orm import Mapped,mapped_column,relationship
from .database import Base
def now(): return datetime.now(timezone.utc)
class User(Base):
    __tablename__="users"
    id:Mapped[int]=mapped_column(primary_key=True)
    telegram_id:Mapped[int]=mapped_column(unique=True,index=True)
    username:Mapped[str]=mapped_column(String(64),default="")
    display_name:Mapped[str]=mapped_column(String(40),default="Игрок")
    avatar_url:Mapped[str]=mapped_column(Text,default="")
    level:Mapped[int]=mapped_column(Integer,default=1)
    xp:Mapped[int]=mapped_column(Integer,default=0)
    coins:Mapped[int]=mapped_column(Integer,default=250)
    energy:Mapped[int]=mapped_column(Integer,default=100)
    last_daily:Mapped[str]=mapped_column(String(10),default="")
    hide_rating:Mapped[bool]=mapped_column(Boolean,default=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class GameItem(Base):
    __tablename__="game_items"
    id:Mapped[int]=mapped_column(primary_key=True)
    slug:Mapped[str]=mapped_column(String(80),unique=True,index=True)
    name:Mapped[str]=mapped_column(String(100))
    description:Mapped[str]=mapped_column(Text,default="")
    rarity:Mapped[str]=mapped_column(String(20),default="Обычный")
    collection:Mapped[str]=mapped_column(String(80),default="Cyber City")
    icon:Mapped[str]=mapped_column(String(20),default="◆")
    power:Mapped[int]=mapped_column(Integer,default=1)
class InventoryItem(Base):
    __tablename__="inventory_items"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    item_id:Mapped[int]=mapped_column(ForeignKey("game_items.id"),index=True)
    level:Mapped[int]=mapped_column(Integer,default=1)
    favorite:Mapped[bool]=mapped_column(Boolean,default=False)
    obtained_from:Mapped[str]=mapped_column(String(40),default="container")
    obtained_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
class Task(Base):
    __tablename__="tasks"
    id:Mapped[int]=mapped_column(primary_key=True)
    slug:Mapped[str]=mapped_column(String(80),unique=True)
    title:Mapped[str]=mapped_column(String(140))
    description:Mapped[str]=mapped_column(Text,default="")
    reward_coins:Mapped[int]=mapped_column(Integer,default=0)
    reward_xp:Mapped[int]=mapped_column(Integer,default=0)
    kind:Mapped[str]=mapped_column(String(30),default="general")
class UserTask(Base):
    __tablename__="user_tasks"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    task_id:Mapped[int]=mapped_column(ForeignKey("tasks.id"),index=True)
    progress:Mapped[int]=mapped_column(Integer,default=0)
    claimed:Mapped[bool]=mapped_column(Boolean,default=False)
    __table_args__=(UniqueConstraint("user_id","task_id",name="uq_user_task"),)
class Transaction(Base):
    __tablename__="transactions"
    id:Mapped[int]=mapped_column(primary_key=True)
    user_id:Mapped[int]=mapped_column(ForeignKey("users.id"),index=True)
    amount:Mapped[int]=mapped_column(Integer)
    balance_before:Mapped[int]=mapped_column(Integer)
    balance_after:Mapped[int]=mapped_column(Integer)
    operation:Mapped[str]=mapped_column(String(40))
    source:Mapped[str]=mapped_column(String(80),default="")
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=now)
