import os

from fastapi import FastAPI, HTTPException # type: ignore
from sqlalchemy import create_engine, Column, Integer, String, Text, DECIMAL, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv
from urllib.parse import quote_plus

# Load environment variables from .env
load_dotenv()


# Database Configuration
username = os.getenv("DB_USERNAME", "your_default_username")
password = quote_plus(os.getenv("DB_PASSWORD", "your_default_password"))
host = os.getenv("DB_HOST", "localhost")
port = os.getenv("DB_PORT", "5432")
database = os.getenv("DB_NAME", "employee_db")
DATABASE_URL = f"postgresql://{username}:{password}@{host}:{port}/{database}"

# SQLAlchemy Setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# Database Models
class EmployeeDetails(Base):
    __tablename__ = "employee_details"
    employee_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    work = relationship("EmployeeWork", back_populates="employee", uselist=False)

class EmployeeWork(Base):
    __tablename__ = "employee_work"
    work_id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employee_details.employee_id"))
    role = Column(String)
    department = Column(String)
    office_location = Column(String)
    projects = Column(Text)  # Consider using a JSON type if needed
    number_of_projects_completed = Column(Integer)
    rating = Column(DECIMAL)
    performance_summary = Column(Text)
    employee = relationship("EmployeeDetails", back_populates="work")

# Create tables in the database (run once)
Base.metadata.create_all(bind=engine)

# FastAPI Application Setup
app = FastAPI()



# API Endpoint to fetch employee info
@app.get("/employee/{employee_id}")
def get_employee(employee_id: int):
    session = SessionLocal()
    employee = session.query(EmployeeDetails).filter(EmployeeDetails.employee_id == employee_id).first()
    employee_2 = session.query(EmployeeWork).filter(EmployeeWork.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    work_info = employee.work
    work_info+=employee_2.work
    # Build the prompt using retrieved employee data
    prompt = (
        f"Employee: {employee.first_name} {employee.last_name}, Email: {employee.email}, Phone: {employee.phone}. "
    )
    if work_info:
        prompt += (
            f"Role: {work_info.role}, Department: {work_info.department}, "
            f"Office Location: {work_info.office_location}, Projects: {work_info.projects}, "
            f"Projects Completed: {work_info.number_of_projects_completed}, Rating: {work_info.rating}, "
            f"Performance Summary: {work_info.performance_summary}."
        )
    else:
        prompt += "No work information available."

    print("Prompt:", prompt)  # Debug print of the built prompt

    # Generate a summary using the OpenAI API
    summary = generate_summary(prompt)
    return {"summary": summary, "details": prompt}
