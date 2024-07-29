# Required packages:
# pip install fastapi
# pip install pydantic
# pip install uvicorn
# pip install sqlalchemy

from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from hashlib import sha256
from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import time

# Database setup
DATABASE_URL = "sqlite:////Users/yifeicao/PycharmProjects/icucatl/user_log.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Models
class UserDB(Base):
    __tablename__ = "users"

    username = Column(String, primary_key=True, index=True)
    password_hash = Column(String, index=True)
    log = Column(Text, default="")


Base.metadata.create_all(bind=engine)

# App setup
app = FastAPI()

# Local file storage path
UPLOAD_DIR = "uploaded_files/"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def hash_password(password: str) -> str:
    return sha256(password.encode()).hexdigest()


def get_user(db, username: str):
    return db.query(UserDB).filter(UserDB.username == username).first()


def save_user(db, user: UserDB):
    db.add(user)
    db.commit()
    db.refresh(user)


def delete_old_files():
    now = time.time()
    cutoff = now - (30 * 86400)  # 30 days ago timestamp
    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.getmtime(file_path) < cutoff:
            os.remove(file_path)


@app.post("/register/")
async def register(username: str = Form(), password: str = Form(), log: str = Form(default="")):
    db = SessionLocal()
    try:
        if get_user(db, username):
            raise HTTPException(status_code=400, detail="Username already exists")

        password_hash = hash_password(password)
        user = UserDB(username=username, password_hash=password_hash, log=log)
        save_user(db, user)
        return {"message": "User registered successfully"}
    finally:
        db.close()


@app.post("/login/")
async def login(username: str = Form(), password: str = Form()):
    db = SessionLocal()
    try:
        user = get_user(db, username)
        if user and user.password_hash == hash_password(password):
            return {"username": username, "log": user.log}
        else:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
    finally:
        db.close()


@app.post("/upload/")
async def upload_file(username: str = Form(), file: UploadFile = File(...)):
    db = SessionLocal()
    try:
        user = get_user(db, username)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            buffer.write(file.file.read())

        return {"filename": file.filename, "file_url": f"/files/{file.filename}"}
    finally:
        db.close()


@app.get("/files/{filename}")
async def get_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    else:
        raise HTTPException(status_code=404, detail="File not found")


@app.on_event("startup")
async def startup_event():
    delete_old_files()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
