from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import models
from db import SessionLocal, engine
from llm import compare_players
from config import SECRET_KEY

# Create all tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency: database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Security settings
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user

# Register endpoint
@app.post("/register")
def register(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(password)
    new_user = models.User(name=name, email=email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"msg": "User registered successfully"}

# Login endpoint
@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Player comparison model
class PlayerComparisonRequest(BaseModel):
    player1: str
    player2: str

# Compare players endpoint
@app.post("/compare_players")
def compare_players_endpoint(
    request: PlayerComparisonRequest,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    try:
        # Get comparison from LLM
        comparison_result = compare_players(request.player1, request.player2)
        
        # Store the query in database
        new_query = models.PlayerQuery(
            user_id=user.id,
            player1=request.player1,
            player2=request.player2,
            result=comparison_result
        )
        db.add(new_query)
        db.commit()
        
        return {
            "player1": request.player1,
            "player2": request.player2,
            "comparison": comparison_result
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing players: {str(e)}"
        )

# Get user's comparison history
@app.get("/comparison_history")
def get_comparison_history(
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    queries = db.query(models.PlayerQuery).filter(
        models.PlayerQuery.user_id == user.id
    ).order_by(models.PlayerQuery.timestamp.desc()).all()
    
    return [
        {
            "player1": query.player1,
            "player2": query.player2,
            "result": query.result,
            "timestamp": query.timestamp
        }
        for query in queries
    ]

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy", "message": "MLB Player Comparison API is running"}