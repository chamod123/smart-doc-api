from pydantic import BaseModel, EmailStr

# --- User Schemas ---

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Document Schemas ---

class DocumentOut(BaseModel):
    id: int
    filename: str
    content: str
    owner_id: int

    class Config:
        from_attributes = True  # ✅ Pydantic v2 update

# --- QnA Schemas ---

class QnABase(BaseModel):
    question: str
    answer: str

class QnACreate(BaseModel):
    question: str
    document_id: int

class QnAOut(QnABase):
    id: int
    user_id: int
    document_id: int

    class Config:
        from_attributes = True  # ✅ Pydantic v2 update
