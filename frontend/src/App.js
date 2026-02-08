import { useState, useEffect, useCallback, useRef } from "react";
import "@/App.css";
import axios from "axios";
import { Toaster, toast } from "sonner";
import { Sun, Utensils, Moon, ShoppingCart, Download, RotateCcw, X, Plus, Loader2, FileJson, FileSpreadsheet, ShoppingBag, Trash2, Copy, Share2, FileText, MessageCircle, Coffee } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from "@/components/ui/dropdown-menu";
import { Checkbox } from "@/components/ui/checkbox";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const DAYS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];
const MEAL_TYPES = [
  { key: "desayuno", label: "Desayuno", icon: Sun },
  { key: "aperitivo", label: "Aperitivo", icon: Coffee },
  { key: "comida", label: "Comida", icon: Utensils },
  { key: "cena", label: "Cena", icon: Moon },
];

// Editable Cell Component
const EditableCell = ({ day, mealType, meal, onSave, onDelete, onAddToList }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [mealName, setMealName] = useState(meal?.name || "");
  const [ingredientsText, setIngredientsText] = useState(meal?.ingredients?.join(", ") || "");
  const [saving, setSaving] = useState(false);
  const nameInputRef = useRef(null);

  useEffect(() => {
    setMealName(meal?.name || "");
    setIngredientsText(meal?.ingredients?.join(", ") || "");
  }, [meal]);

  useEffect(() => {
    if (isEditing && nameInputRef.current) {
      nameInputRef.current.focus();
    }
  }, [isEditing]);

  const handleSave = async () => {
    if (!mealName.trim()) {
      if (meal) {
        await handleDelete();
      } else {
        setIsEditing(false);
      }
      return;
    }

    setSaving(true);
    const ingredients = ingredientsText
      .split(",")
      .map(i => i.trim())
      .filter(i => i.length > 0);

    try {
      await onSave(day, mealType, { name: mealName.trim(), ingredients });
      setIsEditing(false);
    } catch (error) {
      console.error("Error saving:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    setSaving(true);
    try {
      await onDelete(day, mealType);
      setMealName("");
      setIngredientsText("");
      setIsEditing(false);
    } catch (error) {
      console.error("Error deleting:", error);
    } finally {
      setSaving(false);
    }
  };

  const handleAddToList = (e) => {
    e.stopPropagation();
    if (meal?.ingredients?.length > 0) {
      onAddToList(meal.ingredients);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSave();
    }
    if (e.key === "Escape") {
      setMealName(meal?.name || "");
      setIngredientsText(meal?.ingredients?.join(", ") || "");
      setIsEditing(false);
    }
  };

  const MealIcon = MEAL_TYPES.find(m => m.key === mealType)?.icon || Utensils;

  if (isEditing) {
    return (
      <div className="p-2 space-y-2 bg-primary/5 rounded-lg border-2 border-primary/30">
        <Input
          ref={nameInputRef}
          data-testid={`edit-name-${day}-${mealType}`}
          value={mealName}
          onChange={(e) => setMealName(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Nombre del plato..."
          className="h-8 text-sm rounded-lg"
          disabled={saving}
        />
        <Textarea
          data-testid={`edit-ingredients-${day}-${mealType}`}
          value={ingredientsText}
          onChange={(e) => setIngredientsText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ingredientes (separados por coma)"
          className="text-xs min-h-[50px] rounded-lg resize-none"
          disabled={saving}
        />
        <div className="flex gap-1 justify-end">
          {meal && (
            <Button
              data-testid={`delete-${day}-${mealType}`}
              size="sm"
              variant="ghost"
              onClick={handleDelete}
              disabled={saving}
              className="h-7 px-2 text-destructive hover:text-destructive hover:bg-destructive/10"
            >
              <X className="w-3 h-3" />
            </Button>
          )}
          <Button
            data-testid={`cancel-${day}-${mealType}`}
            size="sm"
            variant="ghost"
            onClick={() => {
              setMealName(meal?.name || "");
              setIngredientsText(meal?.ingredients?.join(", ") || "");
              setIsEditing(false);
            }}
            disabled={saving}
            className="h-7 px-2"
          >
            Cancelar
          </Button>
          <Button
            data-testid={`save-${day}-${mealType}`}
            size="sm"
            onClick={handleSave}
            disabled={saving}
            className="h-7 px-3 bg-primary text-primary-foreground hover:bg-primary/90 rounded-full"
          >
            {saving ? <Loader2 className="w-3 h-3 animate-spin" /> : "Guardar"}
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div
      data-testid={`cell-${day}-${mealType}`}
      className={`p-2 rounded-lg transition-all min-h-[80px] relative group ${
        meal
          ? "bg-white border border-border/50 hover:border-primary/30 hover:shadow-sm"
          : "border-2 border-dashed border-border/50 hover:border-primary/30 hover:bg-primary/5 cursor-pointer"
      }`}
      onClick={() => !meal && setIsEditing(true)}
    >
      {meal ? (
        <div>
          <div 
            className="cursor-pointer"
            onClick={() => setIsEditing(true)}
          >
            <div className="flex items-start gap-1.5 mb-1">
              <MealIcon className="w-3 h-3 text-primary mt-0.5 flex-shrink-0" />
              <span className="font-medium text-sm text-foreground line-clamp-2 pr-6">{meal.name}</span>
            </div>
            {meal.ingredients?.length > 0 && (
              <div className="flex flex-wrap gap-1 mt-1.5">
                {meal.ingredients.slice(0, 3).map((ing, i) => (
                  <Badge key={i} variant="secondary" className="text-[10px] px-1.5 py-0 bg-accent/30 border-0">
                    {ing}
                  </Badge>
                ))}
                {meal.ingredients.length > 3 && (
                  <Badge variant="secondary" className="text-[10px] px-1.5 py-0 bg-muted border-0">
                    +{meal.ingredients.length - 3}
                  </Badge>
                )}
              </div>
            )}
          </div>
          
          {/* Add to shopping list button */}
          {meal.ingredients?.length > 0 && (
            <Button
              data-testid={`add-to-list-${day}-${mealType}`}
              size="sm"
              variant="ghost"
              onClick={handleAddToList}
              className="absolute top-1 right-1 h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity bg-primary/10 hover:bg-primary/20 rounded-full"
              title="Añadir a lista de compra"
            >
              <ShoppingBag className="w-3 h-3 text-primary" />
            </Button>
          )}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center h-full text-muted-foreground/50">
          <Plus className="w-4 h-4 mb-1" />
          <span className="text-[10px]">Click para añadir</span>
        </div>
      )}
    </div>
  );
};

function App() {
  const [weeklyPlan, setWeeklyPlan] = useState(null);
  const [shoppingList, setShoppingList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showShoppingList, setShowShoppingList] = useState(false);

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
    fetchShoppingList();
  }, [fetchWeeklyPlan, fetchShoppingList]);

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

  const saveMeal = async (day, mealType, mealData) => {
    try {
      await axios.put(`${API}/weekly-plan/slot`, {
        day,
        meal_type: mealType,
        meal: mealData,
      });
      toast.success("Comida guardada");
      await fetchWeeklyPlan();
    } catch (error) {
      console.error("Error saving meal:", error);
      toast.error("Error al guardar");
      throw error;
    }
  };

  const deleteMeal = async (day, mealType) => {
    try {
      await axios.delete(`${API}/weekly-plan/slot`, {
        params: { day, meal_type: mealType },
      });
      toast.success("Comida eliminada");
      await fetchWeeklyPlan();
    } catch (error) {
      console.error("Error deleting meal:", error);
      toast.error("Error al eliminar");
      throw error;
    }
  };

  const addToShoppingList = async (ingredients) => {
    try {
      await axios.post(`${API}/shopping-list/add`, { ingredients });
      toast.success(`${ingredients.length} ingrediente(s) añadido(s) a la lista`);
      fetchShoppingList();
    } catch (error) {
      console.error("Error adding to list:", error);
      toast.error("Error al añadir a la lista");
    }
  };

  const toggleShoppingItem = async (name) => {
    try {
      await axios.put(`${API}/shopping-list/toggle`, null, { params: { name } });
      fetchShoppingList();
    } catch (error) {
      console.error("Error toggling item:", error);
    }
  };

  const removeShoppingItem = async (name) => {
    try {
      await axios.delete(`${API}/shopping-list/item`, { params: { name } });
      toast.success("Ingrediente eliminado");
      fetchShoppingList();
    } catch (error) {
      console.error("Error removing item:", error);
      toast.error("Error al eliminar");
    }
  };

  const clearShoppingList = async () => {
    if (!window.confirm("¿Vaciar toda la lista de compra?")) return;
    try {
      await axios.delete(`${API}/shopping-list/clear`);
      toast.success("Lista vaciada");
      fetchShoppingList();
    } catch (error) {
      console.error("Error clearing list:", error);
      toast.error("Error al vaciar la lista");
    }
  };

  const copyShoppingList = async () => {
    try {
      const response = await axios.get(`${API}/shopping-list/export/text`);
      await navigator.clipboard.writeText(response.data);
      toast.success("Lista copiada al portapapeles");
    } catch (error) {
      console.error("Error copying list:", error);
      toast.error("Error al copiar");
    }
  };

  const downloadShoppingList = async () => {
    try {
      const response = await axios.get(`${API}/shopping-list/export/text`);
      const blob = new Blob([response.data], { type: "text/plain;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `lista_compra_${new Date().toISOString().split("T")[0]}.txt`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Lista descargada");
    } catch (error) {
      console.error("Error downloading list:", error);
      toast.error("Error al descargar");
    }
  };

  const shareWhatsApp = async () => {
    try {
      const response = await axios.get(`${API}/shopping-list/export/whatsapp`);
      if (response.data.url) {
        window.open(response.data.url, "_blank");
      }
    } catch (error) {
      console.error("Error sharing:", error);
      toast.error("Error al compartir");
    }
  };

  const shareNative = async () => {
    try {
      const response = await axios.get(`${API}/shopping-list/export/text`);
      if (navigator.share) {
        await navigator.share({
          title: "Lista de Compra - KetoFlow",
          text: response.data,
        });
      } else {
        // Fallback to copy
        await navigator.clipboard.writeText(response.data);
        toast.success("Lista copiada al portapapeles");
      }
    } catch (error) {
      if (error.name !== "AbortError") {
        console.error("Error sharing:", error);
        toast.error("Error al compartir");
      }
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

  // Export functions
  const exportAsJSON = async () => {
    try {
      const response = await axios.get(`${API}/export/json`);
      const blob = new Blob([JSON.stringify(response.data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ketoflow_plan_${new Date().toISOString().split("T")[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Plan exportado como JSON");
    } catch (error) {
      console.error("Error exporting JSON:", error);
      toast.error("Error al exportar");
    }
  };

  const exportAsCSV = async () => {
    try {
      const response = await axios.get(`${API}/export/csv`);
      const blob = new Blob([response.data], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ketoflow_plan_${new Date().toISOString().split("T")[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast.success("Plan exportado como CSV");
    } catch (error) {
      console.error("Error exporting CSV:", error);
      toast.error("Error al exportar");
    }
  };

  const shoppingListCount = shoppingList.filter(item => !item.checked).length;

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
        <div className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
                <span className="text-primary-foreground font-bold text-lg">K</span>
              </div>
              <h1 className="text-2xl font-bold text-foreground tracking-tight" style={{ fontFamily: 'Outfit, sans-serif' }}>
                KetoFlow
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <Button
                data-testid="reset-week-btn"
                variant="ghost"
                size="sm"
                onClick={resetWeek}
                className="text-muted-foreground hover:text-foreground rounded-full"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Reiniciar</span>
              </Button>
              
              {/* Export Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    data-testid="export-btn"
                    variant="outline"
                    size="sm"
                    className="rounded-full"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    <span className="hidden sm:inline">Exportar</span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="rounded-xl">
                  <DropdownMenuItem 
                    data-testid="export-json-btn"
                    onClick={exportAsJSON}
                    className="cursor-pointer"
                  >
                    <FileJson className="w-4 h-4 mr-2 text-primary" />
                    Exportar como JSON
                  </DropdownMenuItem>
                  <DropdownMenuItem 
                    data-testid="export-csv-btn"
                    onClick={exportAsCSV}
                    className="cursor-pointer"
                  >
                    <FileSpreadsheet className="w-4 h-4 mr-2 text-green-600" />
                    Exportar como CSV
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>

              <Button
                data-testid="shopping-list-btn"
                onClick={() => setShowShoppingList(true)}
                className="bg-primary text-primary-foreground hover:bg-primary/90 rounded-full px-4 relative"
              >
                <ShoppingCart className="w-4 h-4 mr-2" />
                <span className="hidden sm:inline">Lista de Compra</span>
                {shoppingListCount > 0 && (
                  <span className="absolute -top-1 -right-1 bg-accent text-accent-foreground text-xs font-bold rounded-full w-5 h-5 flex items-center justify-center">
                    {shoppingListCount}
                  </span>
                )}
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Intro */}
        <div className="mb-6">
          <h2 className="text-2xl sm:text-3xl font-semibold text-foreground mb-1" style={{ fontFamily: 'Outfit, sans-serif' }}>
            Tu Plan Semanal
          </h2>
          <p className="text-muted-foreground text-sm">
            Haz click en cualquier celda para editar · Usa el icono <ShoppingBag className="w-3 h-3 inline" /> para añadir ingredientes a la lista
          </p>
        </div>

        {/* Weekly Table */}
        <Card className="rounded-2xl border-border/50 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full border-collapse" data-testid="weekly-table">
              <thead>
                <tr className="bg-primary/10">
                  <th className="p-3 text-left text-xs font-bold uppercase tracking-widest text-primary border-b border-border/30 min-w-[80px]">
                    Comida
                  </th>
                  {DAYS.map((day) => (
                    <th
                      key={day}
                      className="p-3 text-center text-xs font-bold uppercase tracking-widest text-primary border-b border-border/30 min-w-[140px]"
                      style={{ fontFamily: 'Outfit, sans-serif' }}
                    >
                      {day}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {MEAL_TYPES.map(({ key, label, icon: Icon }) => (
                  <tr key={key} className="border-b border-border/20 last:border-b-0">
                    <td className="p-3 bg-muted/30 border-r border-border/20">
                      <div className="flex items-center gap-2">
                        <Icon className="w-4 h-4 text-primary" />
                        <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                          {label}
                        </span>
                      </div>
                    </td>
                    {DAYS.map((_, dayIndex) => (
                      <td key={`${dayIndex}-${key}`} className="p-2 border-r border-border/10 last:border-r-0">
                        <EditableCell
                          day={dayIndex}
                          mealType={key}
                          meal={getMealForSlot(dayIndex, key)}
                          onSave={saveMeal}
                          onDelete={deleteMeal}
                          onAddToList={addToShoppingList}
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Instructions */}
        <div className="mt-4 text-center text-xs text-muted-foreground">
          <p>💡 <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px]">Enter</kbd> para guardar · <kbd className="px-1.5 py-0.5 bg-muted rounded text-[10px]">Esc</kbd> para cancelar · Hover sobre comida para añadir a lista</p>
        </div>
      </main>

      {/* Shopping List Dialog */}
      <Dialog open={showShoppingList} onOpenChange={setShowShoppingList}>
        <DialogContent className="sm:max-w-md rounded-2xl">
          <DialogHeader>
            <DialogTitle className="text-xl flex items-center gap-2" style={{ fontFamily: 'Outfit, sans-serif' }}>
              <ShoppingCart className="w-5 h-5 text-primary" />
              Lista de Compra
              {shoppingList.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {shoppingList.filter(i => !i.checked).length} pendientes
                </Badge>
              )}
            </DialogTitle>
            <DialogDescription>
              Marca los ingredientes que ya tienes o has comprado
            </DialogDescription>
          </DialogHeader>

          <ScrollArea className="max-h-[400px] pr-4">
            {shoppingList.length > 0 ? (
              <div className="space-y-2">
                {shoppingList.map((item, index) => (
                  <div
                    key={index}
                    data-testid={`shopping-item-${index}`}
                    className={`flex items-center gap-3 py-3 px-4 rounded-xl bg-card border border-border/50 transition-all ${
                      item.checked ? "opacity-50 bg-muted/30" : "hover:bg-muted/30"
                    }`}
                  >
                    <Checkbox
                      data-testid={`check-item-${index}`}
                      checked={item.checked}
                      onCheckedChange={() => toggleShoppingItem(item.name)}
                      className="data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                    />
                    <span className={`flex-1 font-medium ${item.checked ? "line-through text-muted-foreground" : "text-foreground"}`}>
                      {item.name}
                    </span>
                    {item.count > 1 && (
                      <Badge variant="outline" className="rounded-full">
                        x{item.count}
                      </Badge>
                    )}
                    <Button
                      data-testid={`remove-item-${index}`}
                      variant="ghost"
                      size="sm"
                      onClick={() => removeShoppingItem(item.name)}
                      className="h-7 w-7 p-0 text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </Button>
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
                  Usa el icono <ShoppingBag className="w-3 h-3 inline" /> en cada comida para añadir
                </p>
              </div>
            )}
          </ScrollArea>

          <DialogFooter className="flex-col sm:flex-row gap-2">
            {shoppingList.length > 0 && (
              <div className="flex gap-2 w-full sm:w-auto">
                {/* Share/Export dropdown */}
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      data-testid="share-list-btn"
                      variant="outline"
                      className="rounded-full flex-1 sm:flex-none"
                      size="sm"
                    >
                      <Share2 className="w-4 h-4 mr-2" />
                      Compartir
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="rounded-xl">
                    <DropdownMenuItem
                      data-testid="copy-list-btn"
                      onClick={copyShoppingList}
                      className="cursor-pointer"
                    >
                      <Copy className="w-4 h-4 mr-2 text-primary" />
                      Copiar al portapapeles
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      data-testid="download-list-btn"
                      onClick={downloadShoppingList}
                      className="cursor-pointer"
                    >
                      <FileText className="w-4 h-4 mr-2 text-blue-600" />
                      Descargar como texto
                    </DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem
                      data-testid="share-whatsapp-btn"
                      onClick={shareWhatsApp}
                      className="cursor-pointer"
                    >
                      <MessageCircle className="w-4 h-4 mr-2 text-green-600" />
                      Enviar por WhatsApp
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      data-testid="share-native-btn"
                      onClick={shareNative}
                      className="cursor-pointer"
                    >
                      <Share2 className="w-4 h-4 mr-2 text-violet-600" />
                      Compartir...
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>

                <Button
                  data-testid="clear-shopping-list-btn"
                  variant="ghost"
                  onClick={clearShoppingList}
                  className="rounded-full text-destructive hover:text-destructive hover:bg-destructive/10"
                  size="sm"
                >
                  <Trash2 className="w-4 h-4" />
                </Button>
              </div>
            )}
            <Button
              data-testid="close-shopping-list-btn"
              variant="secondary"
              onClick={() => setShowShoppingList(false)}
              className="rounded-full w-full sm:w-auto"
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
