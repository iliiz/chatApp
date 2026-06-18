from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base  # FIX: modern import

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String, unique=True, index=True, nullable=False)
    email      = Column(String, unique=True, index=True, nullable=False)
    password   = Column(String, nullable=False)
    is_admin   = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sent_messages     = relationship("Message", foreign_keys="Message.sender_id",
                                     back_populates="sender",   cascade="all, delete-orphan")
    received_messages = relationship("Message", foreign_keys="Message.receiver_id",
                                     back_populates="receiver", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', is_admin={self.is_admin})>"


class Message(Base):
    __tablename__ = "messages"

    id          = Column(Integer, primary_key=True, index=True)
    content     = Column(String, nullable=False)
    sender_id   = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at  = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    sender   = relationship("User", foreign_keys=[sender_id],   back_populates="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="received_messages")

    def __repr__(self):
        return f"<Message(id={self.id}, sender_id={self.sender_id}, receiver_id={self.receiver_id})>"