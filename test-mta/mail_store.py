from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = "sqlite:///./emails.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Email table
class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(String, nullable=False)
    subject = Column(String, nullable=False)
    headers = Column(String, nullable=False)
    mail_from = Column(String, nullable=False)
    mail_to = Column(String, nullable=False)
    body = Column(Text, nullable=False)

# Create the database tables
Base.metadata.create_all(bind=engine)


class EmailBase(BaseModel):
    timestamp: str
    subject: str
    headers: str
    mail_from: str
    mail_to: str
    body: str

    class Config:
        from_attributes = True

class EmailRecord(EmailBase):
    id: int

    class Config:
        from_attributes = True


app = FastAPI(debug=True, description="Very simple email store")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API routes

@app.post("/emails/", response_model=dict)
def create_email(email: EmailBase, db: Session = Depends(get_db)):
    """
    Store an email in the database.
    """
    email = Email(timestamp=email.timestamp, subject=email.subject, headers=email.headers, mail_from=email.mail_from,
                  mail_to=email.mail_to, body=email.body)
    db.add(email)
    db.commit()
    db.refresh(email)
    return {"message": "Email stored successfully", "id": email.id}


@app.get("/emails/", response_model=List[EmailRecord])
def get_emails(db: Session = Depends(get_db)):
    """
    Retrieve all stored emails.
    """
    emails = db.query(Email).all()
    return emails


@app.get("/emails/{mail_id}", response_model=EmailRecord)
def get_email(mail_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific email by ID.
    """
    email = db.query(Email).filter(Email.id == mail_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return email