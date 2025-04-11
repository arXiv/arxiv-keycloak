from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List
import requests
import re

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


@app.post("/emails/{mail_id}/verify")
def maybe_click_link(mail_id: int, db: Session = Depends(get_db)):
    email = db.query(Email).filter(Email.id == mail_id).one_or_none()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    body = email.body

    matched = re.search(r"https://[^\s]+", body)
    if matched:
        email_verify_link = matched.group(0)
        logger.info(f"stage 1 - The link {mail_id}: {email_verify_link}")

        try:
            response = requests.get(email_verify_link, verify=False)  # disable SSL verification for localhost
            logger.info(f"stage 1 - Clicked the link; {response.status_code}")
            webpage = response.text

        except requests.exceptions.RequestException as exc1:
            logger.info(f"stage 1 - Error making request: {exc1}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Calling verification failed") from exc1

        except Exception as exc2:
            logger.info(f"stage 1 - Error making request: {exc2}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc2)) from exc2

        matched_again = re.search(r"https://[^\s]+", webpage)
        if matched_again:
            confirm_link = matched.group(0)
            logger.info(f"stage 2 - The link {mail_id}: {confirm_link}")

            try:
                response = requests.get(confirm_link, verify=False)  # disable SSL verification for localhost
                logger.info(f"stage 2 - Clicked the confirm; {response.status_code}")

            except requests.exceptions.RequestException as exc3:
                logger.info(f"stage 2 - Error making request: {exc3}")
                raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                                    detail="Calling verification failed") from exc3

            except Exception as exc4:
                logger.info(f"stage 2 - Error making request: {exc4}")
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc4)) from exc4

    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email has no link")
    return
