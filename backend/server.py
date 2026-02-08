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
    checked: bool = False

class AddToShoppingListRequest(BaseModel):
    ingredients: List[str]

# Initialize empty weekly plan structure
def create_empty_weekly_plan():
    slots = []
    meal_types = ["desayuno", "aperitivo", "comida", "cena"]
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
    """Get the custom shopping list"""
    items = await db.shopping_list.find({}, {"_id": 0}).to_list(1000)
    return items

@api_router.post("/shopping-list/add")
async def add_to_shopping_list(request: AddToShoppingListRequest):
    """Add ingredients to shopping list"""
    added = []
    for ingredient in request.ingredients:
        ingredient_lower = ingredient.strip().lower()
        if not ingredient_lower:
            continue
        
        # Check if already exists
        existing = await db.shopping_list.find_one({"name_lower": ingredient_lower}, {"_id": 0})
        if existing:
            # Increment count
            await db.shopping_list.update_one(
                {"name_lower": ingredient_lower},
                {"$inc": {"count": 1}}
            )
        else:
            # Add new
            await db.shopping_list.insert_one({
                "name": ingredient.strip().capitalize(),
                "name_lower": ingredient_lower,
                "count": 1,
                "checked": False
            })
        added.append(ingredient.strip().capitalize())
    
    return {"message": f"Añadidos {len(added)} ingredientes", "added": added}

@api_router.delete("/shopping-list/item")
async def remove_from_shopping_list(name: str):
    """Remove an item from shopping list"""
    result = await db.shopping_list.delete_one({"name_lower": name.lower()})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
    return {"message": "Ingrediente eliminado"}

@api_router.put("/shopping-list/toggle")
async def toggle_shopping_item(name: str):
    """Toggle checked status of an item"""
    item = await db.shopping_list.find_one({"name_lower": name.lower()}, {"_id": 0})
    if not item:
        raise HTTPException(status_code=404, detail="Ingrediente no encontrado")
    
    new_checked = not item.get("checked", False)
    await db.shopping_list.update_one(
        {"name_lower": name.lower()},
        {"$set": {"checked": new_checked}}
    )
    return {"message": "Estado actualizado", "checked": new_checked}

@api_router.delete("/shopping-list/clear")
async def clear_shopping_list():
    """Clear entire shopping list"""
    await db.shopping_list.delete_many({})
    return {"message": "Lista vaciada"}

@api_router.get("/shopping-list/export/text", response_class=PlainTextResponse)
async def export_shopping_list_text():
    """Export shopping list as plain text for sharing"""
    items = await db.shopping_list.find({}, {"_id": 0}).to_list(1000)
    if not items:
        return "Lista de compra vacía"
    
    lines = ["🥑 LISTA DE COMPRA - KetoFlow", "=" * 30, ""]
    
    pending = [item for item in items if not item.get("checked", False)]
    checked = [item for item in items if item.get("checked", False)]
    
    if pending:
        lines.append("📋 PENDIENTES:")
        for item in pending:
            count = f" (x{item['count']})" if item.get('count', 1) > 1 else ""
            lines.append(f"  ○ {item['name']}{count}")
        lines.append("")
    
    if checked:
        lines.append("✅ COMPRADOS:")
        for item in checked:
            count = f" (x{item['count']})" if item.get('count', 1) > 1 else ""
            lines.append(f"  ✓ {item['name']}{count}")
        lines.append("")
    
    lines.append("=" * 30)
    lines.append(f"Total: {len(pending)} pendientes, {len(checked)} comprados")
    
    return "\n".join(lines)

@api_router.get("/shopping-list/export/whatsapp")
async def export_shopping_list_whatsapp():
    """Export shopping list formatted for WhatsApp sharing"""
    items = await db.shopping_list.find({}, {"_id": 0}).to_list(1000)
    if not items:
        return {"text": "Lista de compra vacía", "url": ""}
    
    lines = ["*🥑 LISTA DE COMPRA*", ""]
    
    pending = [item for item in items if not item.get("checked", False)]
    
    if pending:
        for item in pending:
            count = f" (x{item['count']})" if item.get('count', 1) > 1 else ""
            lines.append(f"☐ {item['name']}{count}")
    else:
        lines.append("✅ ¡Todo comprado!")
    
    text = "\n".join(lines)
    # URL encode for WhatsApp
    import urllib.parse
    whatsapp_url = f"https://wa.me/?text={urllib.parse.quote(text)}"
    
    return {"text": text, "url": whatsapp_url}

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
