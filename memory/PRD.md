# KetoFlow - Planificador de Dieta Cetogénica

## Problem Statement Original
Necesito una tabla para generar dieta cetogénica semanal desayuno comida y cena y poder añadir los ingredientes para hacer una lista de la compra

## User Choices
- Entrada manual de comidas
- Sin información nutricional (solo recetas e ingredientes)
- Lista de compra simple sin categorías
- Tema claro

## Architecture
- **Backend**: FastAPI + MongoDB
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Database**: MongoDB (colección: weekly_plans)

## Core Requirements
1. Tabla semanal 7 días x 3 comidas (desayuno, comida, cena)
2. Añadir/editar/eliminar comidas con ingredientes
3. Lista de compra agregada de todos los ingredientes
4. Reiniciar semana completa
5. Persistencia de datos en MongoDB

## What's Been Implemented (Jan 2026)
- [x] Tabla editable semanal con 7 columnas (días) x 3 filas (comidas)
- [x] Edición inline directa (click en celda para editar)
- [x] Ingredientes separados por comas
- [x] **Añadir ingredientes a lista**: Botón 🛍️ al hacer hover sobre comida
- [x] **Lista de compra interactiva**: Checkboxes, eliminar individual, vaciar lista
- [x] Contador de ingredientes pendientes en header
- [x] Ingredientes repetidos muestran contador (x2, x3...)
- [x] **Exportación como JSON** (formato base de datos completo)
- [x] **Exportación como CSV** (formato tabla para Excel/Sheets)
- [x] Botón de reinicio de semana
- [x] UI en español con tema claro orgánico
- [x] 100% tests backend + 90% frontend

## API Endpoints
- GET /api/weekly-plan - Obtener plan semanal
- PUT /api/weekly-plan/slot - Actualizar slot de comida
- DELETE /api/weekly-plan/slot - Eliminar comida de slot
- DELETE /api/weekly-plan/reset - Reiniciar semana
- **GET /api/shopping-list** - Lista de compra
- **POST /api/shopping-list/add** - Añadir ingredientes a lista
- **PUT /api/shopping-list/toggle** - Marcar/desmarcar item
- **DELETE /api/shopping-list/item** - Eliminar item de lista
- **DELETE /api/shopping-list/clear** - Vaciar lista completa
- GET /api/export/json - Exportar plan como JSON
- GET /api/export/csv - Exportar plan como CSV

## Next Action Items (P1)
- [ ] Importar plan desde JSON/CSV
- [ ] Copiar semana anterior

## Backlog (P2)
- [ ] Información nutricional opcional
- [ ] Categorías en lista de compra
- [ ] Historial de semanas anteriores
