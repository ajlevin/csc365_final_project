from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from src.api import auth
import sqlalchemy
from sqlalchemy.exc import SQLAlchemyError
from passlib.context import CryptContext
from src import database as db

router = APIRouter(
    prefix="/user",
    tags=["user"],
    dependencies=[Depends(auth.get_api_key)],
)

class User(BaseModel):
    name: str
    email: str
    age: int
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    name: str
    email: str
    age: int

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def authenticateUser(user_id: int, user_login: UserLogin):
    user_query = """
    SELECT user_id, name, email, password 
    FROM users 
    WHERE email = :email AND user_id = :user_id
    """
    with db.engine.begin() as connection:
        user = connection.execute(sqlalchemy.text(user_query), {"email": user_login.email, "user_id": user_id}).fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        verify_password = lambda plain_password, hashed_password: pwd_context.verify(plain_password, hashed_password)

        if not verify_password(user_login.password, user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return user
    
@router.post("/")
def create_user(new_profile: User):
    """
    Create New Climbing User 
    """
    hashed_password = pwd_context.hash(new_profile.password)
    insert_user_row = """
    INSERT INTO users (name, email, age, password) 
    VALUES(:profile_name, :profile_email, :profile_age, :password) 
    returning user_id
    """

    insert_user_dictionary ={
                                "profile_name": new_profile.name, 
                                "profile_email": new_profile.email,
                                "profile_age": new_profile.age,
                                "password": hashed_password
                            }

    try:
        with db.engine.begin() as connection:
            user_id = connection.execute(sqlalchemy.text(insert_user_row), insert_user_dictionary).scalar_one()
        
        return {
            "success": True,
            "user_id": user_id
            }
    
    except:
        return {"success": False}

@router.put("/{user_id}")
def update_user(user_id: int, user_login: UserLogin, altered_user: UserUpdate):
    authenticateUser(user_id, user_login)

    update_user_row = """
    UPDATE users 
    SET name = :updated_name, email = :updated_email, age = :updated_age 
    WHERE user_id = :user_id
    """

    update_user_dicitonary = {
        "updated_name": altered_user.name,
        "updated_email": altered_user.email,
        "updated_age": altered_user.age,
        "user_id": user_id
    }

    try:
        with db.engine.begin() as connection:
            connection.execute(sqlalchemy.text(update_user_row), update_user_dicitonary)
        return {"success": True}
    except SQLAlchemyError as e:
        return {"success": False}


