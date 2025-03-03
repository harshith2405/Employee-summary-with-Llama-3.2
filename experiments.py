from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, Column, Integer, String, Text, DECIMAL, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from dotenv import load_dotenv
import os
import requests
from urllib.parse import quote_plus
from fastapi.middleware.cors import CORSMiddleware

# FastAPI Application Setup
app = FastAPI()

# Allow frontend from port 5500
origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allow requests from 5500
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Load environment variables from .env
load_dotenv()

# Database Configuration
username = os.getenv("DB_USERNAME", "your_default_username")
password = quote_plus(os.getenv("DB_PASSWORD", "your_default_password"))
host = os.getenv("DB_HOST", "localhost")
port = os.getenv("DB_PORT", "5432")
database = os.getenv("DB_NAME", "employee_db")
DATABASE_URL = f"postgresql://{username}:{password}@{host}:{port}/{database}"

# Groq API Config
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = os.getenv("GROQ_API_URL")

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
    projects = Column(Text)
    number_of_projects_completed = Column(Integer)
    rating = Column(DECIMAL)
    performance_summary = Column(Text)
    employee = relationship("EmployeeDetails", back_populates="work")

# Create tables in the database (run once)
Base.metadata.create_all(bind=engine)

# Function to call Groq API
def call_groq_llama(input_text):
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "system", "content": "You are an AI assistant that summarizes employee performance based on their details and achievements."},
            {"role": "user", "content": f"Summarize the employee's performance and praise them based on the following details: {input_text}. Provide a detailed and positive summary including their contributions, strengths, and impact on the team."}
        ]
    }

    print("Prompt I'm sending: ", input_text)
    
    response = requests.post(GROQ_API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {response}"

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# API Endpoint to fetch employee info
@app.get("/employee/{query}")
def get_employees(query: str, db: Session = Depends(get_db)):
    # Extracting the prompt and ids from the query string
    try:
        prompt, ids_string = query.split("&ids=")
        employee_ids = ids_string.split(",")  # Split by comma to get employee IDs
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid query format.")

    # Fetch employee details for each employee ID
    employees_data = []
    for employee_id in employee_ids:
        employee = db.query(EmployeeDetails).filter(EmployeeDetails.employee_id == int(employee_id)).first()
        employee_2 = db.query(EmployeeWork).filter(EmployeeWork.employee_id == int(employee_id)).first()
        
        if employee and employee_2:
            employee_info = {
                "first_name": employee.first_name,
                "role": employee_2.role,
                "department": employee_2.department,
                "projects": employee_2.projects,
                "number_of_projects_completed": employee_2.number_of_projects_completed,
                "rating": employee_2.rating,
                "performance_summary": employee_2.performance_summary
            }
            employees_data.append(employee_info)
        else:
            employees_data.append({"error": f"Employee {employee_id} not found"})

    # Get summary from Groq
    summaries = []

    for employee_info in employees_data:
        if "error" not in employee_info:
            work_details = (
                f"Employee Name: {employee_info['first_name']}, "
                f"Role: {employee_info['role']}, "
                f"Department: {employee_info['department']}, "
                f"Projects Completed: {employee_info['number_of_projects_completed']}, "
                f"Rating: {employee_info['rating']}, "
                f"Performance Summary: {employee_info['performance_summary']}"
            )
            summary = call_groq_llama(work_details)  # Call your Groq summarization
            summaries.append({"employee": employee_info["first_name"], "summary": summary})
        else:
            summaries.append({"error": employee_info["error"]})

    combined_summary = " ".join([summary["summary"] for summary in summaries if "summary" in summary])

    # Return all employee summaries and details
    return {"summaries": combined_summary, "details": employees_data}
