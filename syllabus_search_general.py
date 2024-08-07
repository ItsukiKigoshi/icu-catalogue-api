# seach for name_e, response for all course_info
from fastapi import FastAPI, Query, Depends
from sqlalchemy import create_engine, Column, Integer, String, select
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import List, Optional

# Create the FastAPI application
app = FastAPI()

# Database URL
DATABASE_URL = "sqlite:////Users/yifeicao/PycharmProjects/icucatl/uploaded_files/syllubus/syllabus.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the Course model
class Course(Base):
    __tablename__ = "courses"  # Table name
    id = Column(Integer, primary_key=True, index=True)
    registration_no = Column(String)
    term = Column(String)
    course_no = Column(String)
    major = Column(String)
    level = Column(String)
    language = Column(String)
    name_j = Column(String)
    name_e = Column(String, index=True)  # Search column
    period = Column(String)
    room = Column(String)
    instructor = Column(String)
    credit = Column(Integer)

# Ensure the database tables are created
Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Search endpoint
@app.get("/search", response_model=List[dict])
def search_courses(q: Optional[str] = Query(None, min_length=1), db: Session = Depends(get_db)):
    if q:
        results = db.execute(select(Course).where(Course.name_e.ilike(f"%{q}%"))).scalars().all()
    else:
        results = db.execute(select(Course)).scalars().all()
    return [{"id": course.id, "name_e": course.name_e, "registration_no": course.registration_no} for course in results]

# Run the application with: uvicorn syllabus_search:app --reload
# Access the search endpoint at: http://127.0.0.1:8000/search?q=keyword

