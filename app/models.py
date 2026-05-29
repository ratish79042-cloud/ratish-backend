from sqlalchemy import Column, Integer, String, Text, JSON
from app.core.database import Base

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    stat1 = Column(String(50), nullable=True)
    stat2 = Column(String(50), nullable=True)
    stat3 = Column(String(50), nullable=True)
    stat4 = Column(String(50), nullable=True)
    photoFile = Column(Text, nullable=True)  # Stores base64 or URL
    resumeFile = Column(Text, nullable=True) # Stores base64 or URL

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    desc = Column(Text, nullable=False)      # Maps to 'desc' on frontend
    category = Column(String(100), nullable=False)
    tags = Column(JSON, nullable=True)       # Stores List[str] e.g., ["React", "CSS"]
    githubUrl = Column(String(512), nullable=True)
    demoUrl = Column(String(512), nullable=True)
    projectImage = Column(Text, nullable=True) # Stores base64 or URL

class Certificate(Base):
    __tablename__ = "certificates"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    issuer = Column(String(255), nullable=False)
    date = Column(String(100), nullable=False)
    skillTag = Column(String(100), nullable=True)
    certImage = Column(Text, nullable=True)     # Stores base64 or URL
    certFile = Column(Text, nullable=True)      # Stores base64 or URL
    certFileName = Column(String(255), nullable=True)
    certMime = Column(String(100), nullable=True)

class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    icon = Column(Text, nullable=True)
    category = Column(String(50), index=True, nullable=False)  # "frontend", "tools", "others"
