from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class Ingredient(BaseModel):
    name: str

class Meal(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    ingredients: List[str] = []

class MealCreate(BaseModel):
    name: str
    ingredients: List[str] = []

class MealSlot(BaseModel):
    model_config = ConfigDict(extra="ignore")
    day: int  # 0-6 (Lunes-Domingo)
    meal_type: str  # "desayuno", "comida", "cena"
    meal: Optional[Meal] = None

class WeeklyPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slots: List[MealSlot] = []
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class UpdateMealSlotRequest(BaseModel):
    day: int
    meal_type: str
    meal: Optional[MealCreate] = None

class ShoppingItem(BaseModel):
    name: str
    count: int = 1

# Initialize empty weekly plan structure
def create_empty_weekly_plan():
    slots = []
    days = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
    meal_types = ["desayuno", "comida", "cena"]
    for day_idx in range(7):
        for meal_type in meal_types:
            slots.append(MealSlot(day=day_idx, meal_type=meal_type, meal=None))
    return WeeklyPlan(slots=slots)

# Routes
@api_router.get("/")
async def root():
    return {"message": "KetoFlow API - Planificador de Dieta Cetogénica"}

@api_router.get("/weekly-plan")
async def get_weekly_plan():
    plan = await db.weekly_plans.find_one({}, {"_id": 0})
    if not plan:
        # Create initial empty plan
        new_plan = create_empty_weekly_plan()
        plan_dict = new_plan.model_dump()
        await db.weekly_plans.insert_one(plan_dict.copy())
        return plan_dict
    return plan

@api_router.put("/weekly-plan/slot")
async def update_meal_slot(request: UpdateMealSlotRequest):
    plan = await db.weekly_plans.find_one({}, {"_id": 0})
    if not plan:
        new_plan = create_empty_weekly_plan()
        plan = new_plan.model_dump()
        await db.weekly_plans.insert_one(plan.copy())
    
    # Find and update the specific slot
    slots = plan.get("slots", [])
    updated = False
    for slot in slots:
        if slot["day"] == request.day and slot["meal_type"] == request.meal_type:
            if request.meal:
                meal_data = Meal(
                    name=request.meal.name,
                    ingredients=request.meal.ingredients
                ).model_dump()
                slot["meal"] = meal_data
            else:
                slot["meal"] = None
            updated = True
            break
    
    if not updated:
        raise HTTPException(status_code=404, detail="Slot no encontrado")
    
    # Update the plan in database
    plan["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.weekly_plans.update_one(
        {"id": plan["id"]},
        {"$set": {"slots": slots, "updated_at": plan["updated_at"]}}
    )
    
    return {"message": "Comida actualizada", "slot": {"day": request.day, "meal_type": request.meal_type}}

@api_router.delete("/weekly-plan/slot")
async def delete_meal_slot(day: int, meal_type: str):
    plan = await db.weekly_plans.find_one({}, {"_id": 0})
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    slots = plan.get("slots", [])
    for slot in slots:
        if slot["day"] == day and slot["meal_type"] == meal_type:
            slot["meal"] = None
            break
    
    plan["updated_at"] = datetime.now(timezone.utc).isoformat()
    await db.weekly_plans.update_one(
        {"id": plan["id"]},
        {"$set": {"slots": slots, "updated_at": plan["updated_at"]}}
    )
    
    return {"message": "Comida eliminada"}

@api_router.delete("/weekly-plan/reset")
async def reset_weekly_plan():
    await db.weekly_plans.delete_many({})
    new_plan = create_empty_weekly_plan()
    plan_dict = new_plan.model_dump()
    await db.weekly_plans.insert_one(plan_dict.copy())
    return {"message": "Plan semanal reiniciado", "plan": plan_dict}

# Export endpoints
@api_router.get("/export/json")
async def export_as_json():
    """Export weekly plan as JSON database format"""
    plan = await db.weekly_plans.find_one({}, {"_id": 0})
    if not plan:
        plan = create_empty_weekly_plan().model_dump()
    
    # Format for export
    export_data = {
        "export_date": datetime.now(timezone.utc).isoformat(),
        "app": "KetoFlow",
        "version": "1.0",
        "weekly_plan": {
            "id": plan.get("id"),
            "created_at": plan.get("created_at"),
            "updated_at": plan.get("updated_at"),
            "days": {}
        }
    }
    
    days_names = ["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"]
    for slot in plan.get("slots", []):
        day_name = days_names[slot["day"]]
        if day_name not in export_data["weekly_plan"]["days"]:
            export_data["weekly_plan"]["days"][day_name] = {}
        
        meal_data = slot.get("meal")
        if meal_data:
            export_data["weekly_plan"]["days"][day_name][slot["meal_type"]] = {
                "name": meal_data.get("name"),
                "ingredients": meal_data.get("ingredients", [])
            }
        else:
            export_data["weekly_plan"]["days"][day_name][slot["meal_type"]] = None
    
    return export_data

from fastapi.responses import PlainTextResponse

@api_router.get("/export/csv", response_class=PlainTextResponse)
async def export_as_csv():
    """Export weekly plan as CSV format"""
    plan = await db.weekly_plans.find_one({}, {"_id": 0})
    if not plan:
        plan = create_empty_weekly_plan().model_dump()
    
    days_names = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    meal_types = ["desayuno", "comida", "cena"]
    
    # Build CSV
    lines = []
    lines.append("Día,Tipo de Comida,Nombre del Plato,Ingredientes")
    
    for slot in plan.get("slots", []):
        day_name = days_names[slot["day"]]
        meal_type = slot["meal_type"].capitalize()
        meal = slot.get("meal")
        
        if meal:
            name = meal.get("name", "").replace('"', '""')
            ingredients = "; ".join(meal.get("ingredients", [])).replace('"', '""')
            lines.append(f'"{day_name}","{meal_type}","{name}","{ingredients}"')
        else:
            lines.append(f'"{day_name}","{meal_type}","",""')
    
    return "\n".join(lines)

@api_router.get("/shopping-list", response_model=List[ShoppingItem])
async def get_shopping_list():
    plan = await db.weekly_plans.find_one({}, {"_id": 0})
    if not plan:
        return []
    
    # Aggregate all ingredients
    ingredient_count = {}
    for slot in plan.get("slots", []):
        if slot.get("meal") and slot["meal"].get("ingredients"):
            for ingredient in slot["meal"]["ingredients"]:
                ingredient_lower = ingredient.strip().lower()
                if ingredient_lower:
                    if ingredient_lower in ingredient_count:
                        ingredient_count[ingredient_lower] += 1
                    else:
                        ingredient_count[ingredient_lower] = 1
    
    # Convert to list and capitalize first letter
    shopping_list = [
        ShoppingItem(name=name.capitalize(), count=count)
        for name, count in sorted(ingredient_count.items())
    ]
    
    return shopping_list

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
