from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    password = Column(String(128), nullable=False)

    documents = relationship("Document", back_populates="owner")
    qna_history = relationship("QnA", back_populates="user", cascade="all, delete-orphan")  # NEW


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="documents")
    qna_history = relationship("QnA", back_populates="document", cascade="all, delete-orphan")  # NEW


class QnA(Base):
    __tablename__ = "qna"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(Integer, ForeignKey("documents.id"))

    user = relationship("User", back_populates="qna_history")
    document = relationship("Document", back_populates="qna_history")
