from fastapi import FastAPI, Depends, HTTPException, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import os
import fitz  # PyMuPDF

from . import models, schemas, database, auth

# Initialize DB
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# Upload directory
UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Auth scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="signin")

# DB Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# === Auth ===

@app.post("/signup", response_model=schemas.Token)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        username=user.username,
        email=user.email,
        password=hashed_password
    )
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or Email already registered")

    token = auth.create_access_token({"sub": new_user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/signin", response_model=schemas.Token)
def signin(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    if not user or not auth.verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = auth.create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me")
def read_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = auth.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email
    }

# === Upload File ===

@app.post("/upload", response_model=schemas.DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = auth.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    allowed_extensions = [".txt", ".pdf"]
    if not any(file.filename.endswith(ext) for ext in allowed_extensions):
        raise HTTPException(status_code=400, detail="Only .txt and .pdf files are allowed")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    file_content = await file.read()
    with open(file_path, "wb") as f:
        f.write(file_content)

    if file.filename.endswith(".txt"):
        text = file_content.decode("utf-8")
    else:
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()

    document = models.Document(
        filename=file.filename,
        content=text,
        owner_id=user.id
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return document

# === Ask QnA ===

@app.post("/ask", response_model=schemas.QnAOut)
def ask_question(
    qna_in: schemas.QnACreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = auth.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    document = db.query(models.Document).filter(
        models.Document.id == qna_in.document_id,
        models.Document.owner_id == user.id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found or not owned by user")

    # Simulate AI response
    answer = f"Dummy answer to: {qna_in.question}"

    qna = models.QnA(
        question=qna_in.question,
        answer=answer,
        user_id=user.id,
        document_id=document.id
    )
    db.add(qna)
    db.commit()
    db.refresh(qna)

    return qna

# === QnA History ===

@app.get("/documents/{document_id}/qna", response_model=list[schemas.QnAOut])
def get_qna_history(
    document_id: int,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    payload = auth.decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(models.User).filter(models.User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    document = db.query(models.Document).filter(
        models.Document.id == document_id,
        models.Document.owner_id == user.id
    ).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found or not owned by user")

    qnas = db.query(models.QnA).filter(
        models.QnA.user_id == user.id,
        models.QnA.document_id == document.id
    ).all()

    return qnas
