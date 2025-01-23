from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import Column, Integer, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# Database setup
DATABASE_URL = "sqlite:///./emails.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Email table
class Email(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    header = Column(String, nullable=False)
    email_from = Column(String, nullable=False)
    email_to = Column(String, nullable=False)
    body = Column(Text, nullable=False)

# Create the database tables
Base.metadata.create_all(bind=engine)

# FastAPI app
app = FastAPI()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API routes

@app.post("/emails/", response_model=dict)
def create_email(title: str, header: str, email_from: str, email_to: str, body: str, db: Session = Depends(get_db)):
    """
    Store an email in the database.
    """
    email = Email(title=title, header=header, email_from=email_from, email_to=email_to, body=body)
    db.add(email)
    db.commit()
    db.refresh(email)
    return {"message": "Email stored successfully", "id": email.id}


@app.get("/emails/", response_model=list)
def get_emails(db: Session = Depends(get_db)):
    """
    Retrieve all stored emails.
    """
    emails = db.query(Email).all()
    return emails

@app.get("/emails/{email_id}", response_model=dict)
def get_email(email_id: int, db: Session = Depends(get_db)):
    """
    Retrieve a specific email by ID.
    """
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    return {
        "id": email.id,
        "title": email.title,
        "header": email.header,
        "email_from": email.email_from,
        "email_to": email.email_to,
        "body": email.body
    }
