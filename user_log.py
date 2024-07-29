# Required packages:
# pip install fastapi
# pip install pydantic
# pip install google-cloud-firestore
# pip install google-cloud-storage
# pip install uvicorn


from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from pydantic import BaseModel, Field
from hashlib import sha256
from google.cloud import firestore, storage
import time


class User(BaseModel):
    username: str = Field(..., title="Username", max_length=100)
    password_hash: str = Field(..., title="Password Hash", max_length=64)
    log: str = Field(..., title="User Log")


app = FastAPI()

# setup Firestore server
cred_path = "path/to/serviceAccountKey.json"  # replace with icucatalogue google cloud key file path
firestore_client = firestore.Client.from_service_account_json(cred_path)
storage_client = storage.Client.from_service_account_json(cred_path)
bucket_name = "your-bucket-name"  # replace with icu catalogue google storage bucket
bucket = storage_client.bucket(bucket_name)


def hash_password(password: str) -> str:
    return sha256(password.encode()).hexdigest()


def get_user(username: str):
    doc_ref = firestore_client.collection("users").document(username)
    doc = doc_ref.get()
    if doc.exists:
        return User(**doc.to_dict())
    return None


def save_user(user: User):
    doc_ref = firestore_client.collection("users").document(user.username)
    doc_ref.set(user.dict())


def upload_to_storage(file: UploadFile, username: str):
    blob = bucket.blob(f"{username}/{file.filename}")
    blob.upload_from_file(file.file)
    blob.metadata = {"created_at": str(time.time())}
    blob.patch()
    return blob.public_url


def delete_old_files():
    now = time.time()
    cutoff = now - (365 * 86400)  # 1 year ago timestamp
    blobs = bucket.list_blobs()
    for blob in blobs:
        created_at = float(blob.metadata.get("created_at", "0"))
        if created_at < cutoff:
            blob.delete()


@app.post("/register/")
async def register(username: str = Form(), password: str = Form(), log: str = Form(default="")):
    if get_user(username):
        raise HTTPException(status_code=400, detail="Username already exists")

    password_hash = hash_password(password)
    user = User(username=username, password_hash=password_hash, log=log)
    save_user(user)
    return {"message": "User registered successfully"}


@app.post("/login/")
async def login(username: str = Form(), password: str = Form()):
    user = get_user(username)
    if user and user.password_hash == hash_password(password):
        return {"username": username, "log": user.log}
    else:
        raise HTTPException(status_code=401, detail="Incorrect username or password")


@app.post("/upload/")
async def upload_file(username: str = Form(), file: UploadFile = File(...)):
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_url = upload_to_storage(file, username)
    return {"filename": file.filename, "file_url": file_url}


@app.on_event("startup")
async def startup_event():
    delete_old_files()
