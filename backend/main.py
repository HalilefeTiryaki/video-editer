import json
import os

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from . import auth, models, schemas, worksheet
from .database import Base, engine
from .deps import get_current_user, get_db

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Video Editor Backend")


@app.post("/auth/register", response_model=schemas.UserPublic, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    user = models.User(
        email=payload.email,
        password_hash=auth.hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=schemas.TokenPair)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not auth.verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = auth.create_access_token({"sub": str(user.id)})
    refresh_token = auth.create_refresh_token({"sub": str(user.id)})
    return schemas.TokenPair(access_token=access_token, refresh_token=refresh_token)


@app.get("/me", response_model=schemas.UserPublic)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@app.post("/worksheet/generate", response_model=schemas.WorksheetGenerateResponse)
def generate_worksheet(
    payload: schemas.WorksheetGenerateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    with db.begin():
        db_user = db.query(models.User).filter(models.User.id == current_user.id).first()
        if not db_user or db_user.credits < 1:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not enough credits")
        db_user.credits -= 1

        theme_words = payload.theme_words or []
        if os.getenv("OPENAI_API_KEY"):
            try:
                content, solutions = worksheet.openai_generator(
                    payload.level,
                    payload.topic,
                    payload.age_group,
                    payload.duration,
                    payload.activity_types,
                    theme_words,
                )
            except Exception:
                content, solutions = worksheet.template_generator(
                    payload.level,
                    payload.topic,
                    payload.age_group,
                    payload.duration,
                    payload.activity_types,
                    theme_words,
                )
        else:
            content, solutions = worksheet.template_generator(
                payload.level,
                payload.topic,
                payload.age_group,
                payload.duration,
                payload.activity_types,
                theme_words,
            )

        worksheet_row = models.Worksheet(
            user_id=db_user.id,
            level=payload.level,
            topic=payload.topic,
            content=json.dumps(content, ensure_ascii=False),
            solutions=json.dumps(solutions, ensure_ascii=False),
        )
        db.add(worksheet_row)

    title = f"Arbeitsblatt – {payload.level} – {payload.topic}"
    return schemas.WorksheetGenerateResponse(
        title=title,
        estimated_duration=f"{payload.duration} min",
        content=content,
        solutions=solutions,
        remaining_credits=db_user.credits,
    )
