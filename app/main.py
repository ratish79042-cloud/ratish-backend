from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from typing import List, Optional
import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt

from app.core.config import settings
from app.core.database import Base, engine, get_db, async_session
from app.models import Admin, Profile, Project, Certificate, Skill
from app.schemas import (
    AdminLogin, Token, ProfileOut, ProfileUpdate,
    ProjectOut, ProjectCreate, CertificateOut, CertificateCreate,
    SkillOut, SkillCreate
)

# Password hashing setup using direct native bcrypt
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

# Asynchronous Lifespan for FastAPI (automatic table creation and data seeding)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Create all tables in Neon
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    # 2. Seed Default Admin & Profile if not existing
    async with async_session() as session:
        async with session.begin():
            # Check and seed Admin
            admin_query = await session.execute(select(Admin).filter_by(username="Ratish"))
            admin = admin_query.scalars().first()
            if not admin:
                hashed_pw = get_password_hash("Ratish@302")
                db_admin = Admin(username="Ratish", hashed_password=hashed_pw)
                session.add(db_admin)
                
            # Check and seed Default Profile Core
            profile_query = await session.execute(select(Profile))
            profile = profile_query.scalars().first()
            if not profile:
                db_profile = Profile(
                    id=1,
                    name="Ratish G T",
                    role="Frontend Developer",
                    stat1="3+",
                    stat2="Good",
                    stat3="20+",
                    stat4="Good",
                    photoFile="",
                    resumeFile=""
                )
                session.add(db_profile)
    yield
    # Shutdown logic if any goes here

app = FastAPI(
    title="Ratish Portfolio Backend",
    description="Production-grade asynchronous database layer for Ratish Portfolio",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://ratish-gt.vercel.app/"],  # Allows all origins; can restrict to ["http://localhost:5173"] for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- UPTIME / HEALTH CHECK ---
@app.get("/api/health", tags=["System"])
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        # Perform a light query to verify postgres connection
        result = await db.execute(select(1))
        val = result.scalar()
        if val == 1:
            return {"status": "healthy", "database": "connected", "timestamp": datetime.utcnow()}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database connection error: {str(e)}"
        )


# --- AUTHENTICATION ---
@app.post("/api/auth/login", response_model=Token, tags=["Auth"])
@app.post("/api/login", response_model=Token, tags=["Auth"])
async def login(login_data: AdminLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Admin).filter_by(username=login_data.username))
    db_admin = result.scalars().first()
    if not db_admin or not verify_password(login_data.password, db_admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": db_admin.username})
    return {"access_token": access_token, "token_type": "bearer"}


# --- PROFILE IDENTITY METADATA ---
@app.get("/api/profile", response_model=ProfileOut, tags=["Identity"])
async def get_profile(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile))
    profile = result.scalars().first()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile meta values not initialized")
    return profile

@app.put("/api/profile", response_model=ProfileOut, tags=["Identity"])
async def update_profile(profile_data: ProfileUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Profile))
    db_profile = result.scalars().first()
    if not db_profile:
        # Initialize if missing
        db_profile = Profile(id=1)
        db.add(db_profile)
    
    # Update fields dynamically
    for key, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(db_profile, key, value)
        
    await db.commit()
    await db.refresh(db_profile)
    return db_profile


# --- PORTFOLIO PROJECTS ---
@app.get("/api/projects", response_model=List[ProjectOut], tags=["Projects"])
async def list_projects(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).order_by(Project.id.desc()))
    return result.scalars().all()

@app.post("/api/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED, tags=["Projects"])
async def create_project(project_data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    db_project = Project(**project_data.model_dump())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project

@app.delete("/api/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Projects"])
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).filter_by(id=project_id))
    db_project = result.scalars().first()
    if not db_project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    await db.delete(db_project)
    await db.commit()
    return None


# --- CREDENTIAL BADGES / CERTIFICATES ---
@app.get("/api/certificates", response_model=List[CertificateOut], tags=["Certificates"])
async def list_certificates(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Certificate).order_by(Certificate.id.desc()))
    return result.scalars().all()

@app.post("/api/certificates", response_model=CertificateOut, status_code=status.HTTP_201_CREATED, tags=["Certificates"])
async def create_certificate(cert_data: CertificateCreate, db: AsyncSession = Depends(get_db)):
    db_cert = Certificate(**cert_data.model_dump())
    db.add(db_cert)
    await db.commit()
    await db.refresh(db_cert)
    return db_cert

@app.delete("/api/certificates/{cert_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Certificates"])
async def delete_certificate(cert_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Certificate).filter_by(id=cert_id))
    db_cert = result.scalars().first()
    if not db_cert:
        raise HTTPException(status_code=404, detail=f"Certificate with ID {cert_id} not found")
    await db.delete(db_cert)
    await db.commit()
    return None


# --- SKILLS BOARD ---
@app.get("/api/skills", response_model=List[SkillOut], tags=["Skills"])
async def list_skills(category: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    if category:
        result = await db.execute(select(Skill).filter_by(category=category.lower()))
    else:
        result = await db.execute(select(Skill))
    return result.scalars().all()

# Direct collection queries backwards-compatibility endpoints
@app.get("/api/skills/frontend", response_model=List[SkillOut], tags=["Skills"])
async def list_skills_frontend(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).filter_by(category="frontend"))
    return result.scalars().all()

@app.get("/api/skills/tools", response_model=List[SkillOut], tags=["Skills"])
async def list_skills_tools(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).filter_by(category="tools"))
    return result.scalars().all()

@app.get("/api/skills/others", response_model=List[SkillOut], tags=["Skills"])
async def list_skills_others(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).filter_by(category="others"))
    return result.scalars().all()

@app.post("/api/skills", response_model=SkillOut, status_code=status.HTTP_201_CREATED, tags=["Skills"])
async def create_skill(skill_data: SkillCreate, db: AsyncSession = Depends(get_db)):
    # Standardize category spelling to lowercase
    skill_dict = skill_data.model_dump()
    skill_dict["category"] = skill_dict["category"].lower()
    
    # Restrict categories to valid clusters
    if skill_dict["category"] not in ["frontend", "tools", "others"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill category must be one of 'frontend', 'tools', or 'others'"
        )
        
    db_skill = Skill(**skill_dict)
    db.add(db_skill)
    await db.commit()
    await db.refresh(db_skill)
    return db_skill

@app.delete("/api/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Skills"])
async def delete_skill(skill_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).filter_by(id=skill_id))
    db_skill = result.scalars().first()
    if not db_skill:
        raise HTTPException(status_code=404, detail=f"Skill with ID {skill_id} not found")
    await db.delete(db_skill)
    await db.commit()
    return None

# --- UPDATE (PUT) ENDPOINTS ---

@app.put("/api/projects/{project_id}", response_model=ProjectOut, tags=["Projects"])
async def update_project(project_id: int, project_data: ProjectCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Project).filter_by(id=project_id))
    db_project = result.scalars().first()
    if not db_project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    
    for key, value in project_data.model_dump().items():
        setattr(db_project, key, value)
        
    await db.commit()
    await db.refresh(db_project)
    return db_project

@app.put("/api/certificates/{cert_id}", response_model=CertificateOut, tags=["Certificates"])
async def update_certificate(cert_id: int, cert_data: CertificateCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Certificate).filter_by(id=cert_id))
    db_cert = result.scalars().first()
    if not db_cert:
        raise HTTPException(status_code=404, detail=f"Certificate with ID {cert_id} not found")
    
    for key, value in cert_data.model_dump().items():
        setattr(db_cert, key, value)
        
    await db.commit()
    await db.refresh(db_cert)
    return db_cert

@app.put("/api/skills/{skill_id}", response_model=SkillOut, tags=["Skills"])
async def update_skill(skill_id: int, skill_data: SkillCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Skill).filter_by(id=skill_id))
    db_skill = result.scalars().first()
    if not db_skill:
        raise HTTPException(status_code=404, detail=f"Skill with ID {skill_id} not found")
    
    skill_dict = skill_data.model_dump()
    skill_dict["category"] = skill_dict["category"].lower()
    
    if skill_dict["category"] not in ["frontend", "tools", "others"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skill category must be one of 'frontend', 'tools', or 'others'"
        )
        
    for key, value in skill_dict.items():
        setattr(db_skill, key, value)
        
    await db.commit()
    await db.refresh(db_skill)
    return db_skill
