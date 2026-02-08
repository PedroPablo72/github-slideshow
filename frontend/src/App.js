import { useState, useEffect, useCallback } from "react";
import "@/App.css";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { Sun, Utensils, Moon, ShoppingCart, Plus, Trash2, RotateCcw, X, Check, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
const MEAL_TYPES = [
  { key: "desayuno", label: "Desayuno", icon: Sun },
  { key: "comida", label: "Comida", icon: Utensils },
  { key: "cena", label: "Cena", icon: Moon },
];

function App() {
  const [weeklyPlan, setWeeklyPlan] = useState(null);
  const [shoppingList, setShoppingList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showShoppingList, setShowShoppingList] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [mealName, setMealName] = useState("");
  const [ingredientInput, setIngredientInput] = useState("");
  const [ingredients, setIngredients] = useState([]);
  const [saving, setSaving] = useState(false);

  const fetchWeeklyPlan = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/weekly-plan`);
      setWeeklyPlan(response.data);
    } catch (error) {
      console.error("Error fetching weekly plan:", error);
      toast.error("Error al cargar el plan semanal");
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchShoppingList = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/shopping-list`);
      setShoppingList(response.data);
    } catch (error) {
      console.error("Error fetching shopping list:", error);
      toast.error("Error al cargar la lista de compra");
    }
  }, []);

  useEffect(() => {
    fetchWeeklyPlan();
  }, [fetchWeeklyPlan]);

  useEffect(() => {
    if (showShoppingList) {
      fetchShoppingList();
    }
  }, [showShoppingList, fetchShoppingList]);

  const getMealForSlot = (day, mealType) => {
    if (!weeklyPlan?.slots) return null;
    const slot = weeklyPlan.slots.find(
      (s) => s.day === day && s.meal_type === mealType
    );
    return slot?.meal || null;
  };

  const openMealDialog = (day, mealType) => {
    const existingMeal = getMealForSlot(day, mealType);
    setSelectedSlot({ day, mealType });
    setMealName(existingMeal?.name || "");
    setIngredients(existingMeal?.ingredients || []);
    setIngredientInput("");
    setDialogOpen(true);
  };

  const addIngredient = () => {
    const trimmed = ingredientInput.trim();
    if (trimmed && !ingredients.includes(trimmed)) {
      setIngredients([...ingredients, trimmed]);
      setIngredientInput("");
    }
  };

  const removeIngredient = (index) => {
    setIngredients(ingredients.filter((_, i) => i !== index));
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addIngredient();
    }
  };

  const saveMeal = async () => {
    if (!mealName.trim()) {
      toast.error("Por favor, introduce un nombre para la comida");
      return;
    }

    setSaving(true);
    try {
      await axios.put(`${API}/weekly-plan/slot`, {
        day: selectedSlot.day,
        meal_type: selectedSlot.mealType,
        meal: {
          name: mealName.trim(),
          ingredients: ingredients,
        },
      });
      toast.success("Comida guardada correctamente");
      setDialogOpen(false);
      fetchWeeklyPlan();
    } catch (error) {
      console.error("Error saving meal:", error);
      toast.error("Error al guardar la comida");
    } finally {
      setSaving(false);
    }
  };

  const deleteMeal = async () => {
    setSaving(true);
    try {
      await axios.delete(`${API}/weekly-plan/slot`, {
        params: {
          day: selectedSlot.day,
          meal_type: selectedSlot.mealType,
        },
      });
      toast.success("Comida eliminada");
      setDialogOpen(false);
      fetchWeeklyPlan();
    } catch (error) {
      console.error("Error deleting meal:", error);
      toast.error("Error al eliminar la comida");
    } finally {
      setSaving(false);
    }
  };

  const resetWeek = async () => {
    if (!window.confirm("¿Estás seguro de que quieres reiniciar toda la semana?")) {
      return;
    }
    try {
      await axios.delete(`${API}/weekly-plan/reset`);
      toast.success("Plan semanal reiniciado");
      fetchWeeklyPlan();
    } catch (error) {
      console.error("Error resetting plan:", error);
      toast.error("Error al reiniciar el plan");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-10 h-10 animate-spin text-primary" />
          <p className="text-muted-foreground">Cargando tu plan...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background paper-texture">
      <Toaster richColors position="top-right" />
      
      {/* Header */}
      <header className="glass-header sticky top-0 z-40 border-b border-border/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-lg">K</span>
              </div>
              <h1 className="text-2xl font-bold text-foreground tracking-tight" style={{ fontFamily: 'Outfit, sans-serif' }}>
                KetoFlow
              </h1>
            </div>
            <div className="flex items-center gap-3">
              <Button
                data-testid="reset-week-btn"
                variant="ghost"
                size="sm"
                onClick={resetWeek}
                className="text-muted-foreground hover:text-foreground rounded-full"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Reiniciar
              </Button>
              <Button
                data-testid="shopping-list-btn"
                onClick={() => setShowShoppingList(true)}
                className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full px-5"
              >
                <ShoppingCart className="w-4 h-4 mr-2" />
                Lista de Compra
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Intro */}
        <div className="mb-8">
          <h2 className="text-3xl font-semibold text-foreground mb-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Tu Plan Semanal
          </h2>
          <p className="text-muted-foreground">
            Planifica tus comidas cetogénicas para toda la semana
          </p>
        </div>

        {/* Weekly Grid */}
        <div className="grid grid-cols-1 md:grid-cols-7 gap-4" data-testid="weekly-grid">
          {DAYS.map((day, dayIndex) => (
            <div
              key={day}
              className={`flex flex-col gap-3 animate-fade-in stagger-${dayIndex + 1}`}
              style={{ opacity: 0 }}
            >
              {/* Day Header */}
              <div className="text-center py-3 bg-primary/10 rounded-xl">
                <span className="text-sm font-bold uppercase tracking-widest text-primary" style={{ fontFamily: 'Outfit, sans-serif' }}>
                  {day}
                </span>
              </div>

              {/* Meal Slots */}
              {MEAL_TYPES.map(({ key, label, icon: Icon }) => {
                const meal = getMealForSlot(dayIndex, key);
                return (
                  <Card
                    key={`${dayIndex}-${key}`}
                    data-testid={`meal-slot-${dayIndex}-${key}`}
                    onClick={() => openMealDialog(dayIndex, key)}
                    className={`cursor-pointer transition-all duration-300 ${
                      meal
                        ? "meal-slot-filled card-hover"
                        : "meal-slot-empty bg-transparent"
                    } min-h-[120px] rounded-xl`}
                  >
                    <CardContent className="p-4 h-full flex flex-col">
                      {/* Meal Type Header */}
                      <div className="flex items-center gap-2 mb-2">
                        <Icon className={`w-4 h-4 ${meal ? "text-primary" : "text-muted-foreground"}`} />
                        <span className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                          {label}
                        </span>
                      </div>

                      {meal ? (
                        /* Filled State */
                        <div className="flex-1 flex flex-col">
                          <h4 className="font-semibold text-foreground text-sm mb-2 line-clamp-2">
                            {meal.name}
                          </h4>
                          {meal.ingredients.length > 0 && (
                            <div className="flex flex-wrap gap-1 mt-auto">
                              {meal.ingredients.slice(0, 3).map((ing, i) => (
                                <Badge
                                  key={i}
                                  variant="secondary"
                                  className="text-xs bg-accent/30 text-accent-foreground border-0"
                                >
                                  {ing}
                                </Badge>
                              ))}
                              {meal.ingredients.length > 3 && (
                                <Badge
                                  variant="secondary"
                                  className="text-xs bg-muted text-muted-foreground border-0"
                                >
                                  +{meal.ingredients.length - 3}
                                </Badge>
                              )}
                            </div>
                          )}
                        </div>
                      ) : (
                        /* Empty State */
                        <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground">
                          <Plus className="w-6 h-6 mb-1 opacity-50" />
                          <span className="text-xs">Añadir</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          ))}
        </div>
      </main>

      {/* Meal Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-md rounded-2xl">
          <DialogHeader>
            <DialogTitle className="text-xl" style={{ fontFamily: 'Outfit, sans-serif' }}>
              {selectedSlot && getMealForSlot(selectedSlot.day, selectedSlot.mealType)
                ? "Editar Comida"
                : "Añadir Comida"}
            </DialogTitle>
            <DialogDescription>
              {selectedSlot && `${DAYS[selectedSlot.day]} - ${MEAL_TYPES.find(m => m.key === selectedSlot.mealType)?.label}`}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            {/* Meal Name */}
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                Nombre de la comida
              </label>
              <Input
                data-testid="meal-name-input"
                placeholder="Ej: Huevos revueltos con aguacate"
                value={mealName}
                onChange={(e) => setMealName(e.target.value)}
                className="rounded-xl h-12"
              />
            </div>

            {/* Ingredients */}
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
                Ingredientes
              </label>
              <div className="flex gap-2">
                <Input
                  data-testid="ingredient-input"
                  placeholder="Añadir ingrediente..."
                  value={ingredientInput}
                  onChange={(e) => setIngredientInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="rounded-xl h-12 flex-1"
                />
                <Button
                  data-testid="add-ingredient-btn"
                  type="button"
                  onClick={addIngredient}
                  variant="secondary"
                  className="rounded-full h-12 px-4"
                >
                  <Plus className="w-4 h-4" />
                </Button>
              </div>

              {/* Ingredient Tags */}
              {ingredients.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {ingredients.map((ing, index) => (
                    <Badge
                      key={index}
                      variant="secondary"
                      className="pl-3 pr-1 py-1.5 bg-accent/30 text-accent-foreground border-0 rounded-full flex items-center gap-1"
                    >
                      {ing}
                      <button
                        data-testid={`remove-ingredient-${index}`}
                        onClick={() => removeIngredient(index)}
                        className="ml-1 hover:bg-destructive/20 rounded-full p-0.5 transition-colors"
                      >
                        <X className="w-3 h-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>

          <DialogFooter className="gap-2 sm:gap-0">
            {selectedSlot && getMealForSlot(selectedSlot.day, selectedSlot.mealType) && (
              <Button
                data-testid="delete-meal-btn"
                variant="destructive"
                onClick={deleteMeal}
                disabled={saving}
                className="rounded-full"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Eliminar
              </Button>
            )}
            <Button
              data-testid="save-meal-btn"
              onClick={saveMeal}
              disabled={saving}
              className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full px-6"
            >
              {saving ? (
                <Loader2 className="w-4 h-4 animate-spin mr-2" />
              ) : (
                <Check className="w-4 h-4 mr-2" />
              )}
              Guardar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Shopping List Dialog */}
      <Dialog open={showShoppingList} onOpenChange={setShowShoppingList}>
        <DialogContent className="sm:max-w-md rounded-2xl">
          <DialogHeader>
            <DialogTitle className="text-xl flex items-center gap-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              <ShoppingCart className="w-5 h-5 text-primary" />
              Lista de Compra
            </DialogTitle>
            <DialogDescription>
              Ingredientes de todas tus comidas planificadas
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="max-h-[400px] pr-4">
            {shoppingList.length > 0 ? (
              <div className="space-y-2">
                {shoppingList.map((item, index) => (
                  <div
                    key={index}
                    data-testid={`shopping-item-${index}`}
                    className="shopping-item animate-slide-in"
                    style={{ animationDelay: `${index * 0.03}s`, opacity: 0 }}
                  >
                    <span className="font-medium text-foreground">{item.name}</span>
                    {item.count > 1 && (
                      <Badge variant="outline" className="rounded-full">
                        x{item.count}
                      </Badge>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div className="empty-state">
                <ShoppingCart className="w-12 h-12 text-muted-foreground/30 mb-3" />
                <p className="text-muted-foreground">
                  No hay ingredientes todavía
                </p>
                <p className="text-sm text-muted-foreground/70">
                  Añade comidas para generar tu lista
                </p>
              </div>
            )}
          </ScrollArea>

          <DialogFooter>
            <Button
              data-testid="close-shopping-list-btn"
              variant="secondary"
              onClick={() => setShowShoppingList(false)}
              className="rounded-full w-full"
            >
              Cerrar
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;
