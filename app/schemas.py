from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# --- Base Schema Configuration ---
class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

# --- Admin Schemas ---
class AdminBase(BaseSchema):
    username: str

class AdminCreate(AdminBase):
    password: str

class AdminLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None


# --- Profile / Meta Identity Schemas ---
class ProfileBase(BaseSchema):
    name: str
    role: str
    stat1: Optional[str] = None
    stat2: Optional[str] = None
    stat3: Optional[str] = None
    stat4: Optional[str] = None
    photoFile: Optional[str] = None
    resumeFile: Optional[str] = None

class ProfileUpdate(ProfileBase):
    pass

class ProfileOut(ProfileBase):
    id: int


# --- Project Schemas ---
class ProjectBase(BaseSchema):
    title: str
    desc: str
    category: str
    tags: Optional[List[str]] = []
    githubUrl: Optional[str] = None
    demoUrl: Optional[str] = None
    projectImage: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectOut(ProjectBase):
    id: int


# --- Certificate Schemas ---
class CertificateBase(BaseSchema):
    title: str
    issuer: str
    date: str
    skillTag: Optional[str] = None
    certImage: Optional[str] = None
    certFile: Optional[str] = None
    certFileName: Optional[str] = None
    certMime: Optional[str] = None

class CertificateCreate(CertificateBase):
    pass

class CertificateOut(CertificateBase):
    id: int


# --- Skill Schemas ---
class SkillBase(BaseSchema):
    name: str
    icon: Optional[str] = None
    category: str  # "frontend", "tools", "others"

class SkillCreate(SkillBase):
    pass

class SkillOut(SkillBase):
    id: int
