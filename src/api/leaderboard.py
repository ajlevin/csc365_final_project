from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import text
from pydantic import BaseModel, Field
from enum import Enum
from src import database as db

router = APIRouter()

class SortOptions(str, Enum):
    total_climbs = "total_climbs"
    hardest_grade = "hardest_grade"

class LeaderboardQueryParams(BaseModel):
    sort_by: SortOptions = Field(SortOptions.total_climbs, description="Sort by total climbs or hardest grade")

@router.get("/leaderboard")
def get_leaderboard(query_params: LeaderboardQueryParams = Depends()):
    """
    Get the climbing leaderboard
    """
    base_query = """
    SELECT 
        u.user_id,
        u.name,
        COUNT(c.climbing_id) AS total_climbs,
        MAX(r."YDS") AS hardest_grade
    FROM 
        public.users u
    JOIN 
        public.climbing c ON u.user_id = c.user_id
    JOIN 
        public.routes r ON c.route_id = r.route_id
    WHERE 
        r."YDS" IS NOT NULL
    GROUP BY 
        u.user_id, u.name
    """
    
    if query_params.sort_by == SortOptions.total_climbs:
        order_clause = "ORDER BY total_climbs DESC, hardest_grade DESC"
    else: 
        order_clause = "ORDER BY hardest_grade DESC, total_climbs DESC"
    
    query = f"{base_query} {order_clause};"
    
    try:
        with db.engine.begin() as connection:
            result = connection.execute(text(query)).fetchall()
            leaderboard = [
                {
                    "user_id": row.user_id,
                    "name": row.name,
                    "total_climbs": row.total_climbs,
                    "hardest_grade": row.hardest_grade
                }
                for row in result
            ]

        return {
            "success": True,
            "leaderboard": leaderboard
        }

    except Exception as e:
        print(e)
        return {"success": False, "error_message": str(e)}