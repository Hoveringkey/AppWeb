# Axis Design System

## 1. Dirección visual

Axis debe sentirse como un sistema interno de RH/nómina moderno, premium y operativo. La UI debe tener una estética limpia, clara y empresarial, con glassmorphism aplicado de forma consistente en todas las interfaces, sin comprometer legibilidad ni velocidad de captura.

La referencia visual no debe copiarse literalmente. Debe traducirse a Axis como un sistema productivo: claro, preciso, con superficies tipo glass, bordes amplios, sombras suaves, tablas limpias y navegación flotante.

### Principios visuales

- Claridad antes que decoración.
- Glassmorphism visible, pero siempre legible.
- Interfaz clara premium con superficies translúcidas.
- Navegación flotante, sin sidebar.
- Jerarquía visual fuerte: título, contexto, acción principal, contenido.
- Tablas limpias, compactas y no saturadas.
- Componentes reutilizables antes que estilos por pantalla.
- Operación crítica por encima de estética, especialmente en nómina, incidencias y empleados.

## 2. Identidad de marca interna

### Nombre visible

Mantener el nombre visual **Axis**.

### Personalidad

Axis debe sentirse entre:

- minimalista ejecutiva;
- ERP moderno, sobrio y rápido.

No debe sentirse como una app experimental, gamer, excesivamente futurista ni decorativa. Es una herramienta interna para operación real de RH/nómina.

### Sensación general

- Premium, pero sobria.
- Ligera, pero robusta.
- Moderna, pero operativa.
- Limpia, pero no vacía.
- Clara, pero con profundidad visual.

## 3. Paleta de color

La paleta base será **Slate / blanco / azul**, con acentos controlados.

### Background

Usar fondos claros con profundidad sutil.

```css
--color-bg: #f8fafc;
--color-bg-soft: #f1f5f9;
--color-bg-elevated: #ffffff;
--color-bg-gradient-a: #f8fafc;
--color-bg-gradient-b: #eef4ff;
--color-bg-gradient-c: #f7f3ff;
```

Uso recomendado:

- `--color-bg` para el fondo principal.
- Gradientes muy sutiles en PageShell.
- No usar fondos saturados.
- Evitar negro puro salvo texto o botones principales.

### Surfaces

```css
--color-surface: rgba(255, 255, 255, 0.78);
--color-surface-strong: rgba(255, 255, 255, 0.92);
--color-surface-muted: rgba(248, 250, 252, 0.72);
```

Uso:

- Cards, panels y tablas deben usar surface glass.
- Formularios y modales deben usar surface strong para legibilidad.
- Evitar superficies completamente transparentes en tablas densas.

### Glass

```css
--glass-bg: rgba(255, 255, 255, 0.68);
--glass-bg-strong: rgba(255, 255, 255, 0.82);
--glass-bg-soft: rgba(255, 255, 255, 0.52);
--glass-blur: 20px;
--glass-blur-strong: 28px;
--glass-saturate: 160%;
```

Glass debe aplicarse a:

- navbar flotante;
- cards principales;
- modales;
- dropdowns;
- paneles de filtros;
- estados vacíos/loading/error;
- contenedores de dashboard.

No aplicar glass excesivo a:

- texto;
- tablas con muchas filas;
- botones pequeños dentro de tablas;
- celdas de datos críticos.

### Borders

```css
--color-border: rgba(15, 23, 42, 0.10);
--color-border-strong: rgba(15, 23, 42, 0.16);
--color-border-soft: rgba(255, 255, 255, 0.72);
```

Regla:

- Borders sutiles, casi siempre de 1px.
- Bordes internos de tablas más ligeros.
- Cards con border visible pero no pesado.

### Text

```css
--color-text: #0f172a;
--color-text-muted: #475569;
--color-text-subtle: #64748b;
--color-text-disabled: #94a3b8;
--color-text-inverse: #ffffff;
```

Regla:

- Texto principal en slate oscuro.
- No usar gris demasiado claro para información operativa.
- Labels y metadatos pueden usar muted/subtle.

### Accent

```css
--color-accent: #2563eb;
--color-accent-hover: #1d4ed8;
--color-accent-soft: rgba(37, 99, 235, 0.10);
--color-accent-border: rgba(37, 99, 235, 0.24);
```

Uso:

- Acción principal.
- Estado activo en navbar.
- Links importantes.
- Indicadores de selección.

No usar azul en exceso. Si todo es azul, nada destaca.

### Status colors

```css
--color-success: #16a34a;
--color-success-soft: rgba(22, 163, 74, 0.12);
--color-success-border: rgba(22, 163, 74, 0.24);

--color-warning: #d97706;
--color-warning-soft: rgba(217, 119, 6, 0.12);
--color-warning-border: rgba(217, 119, 6, 0.24);

--color-error: #dc2626;
--color-error-soft: rgba(220, 38, 38, 0.12);
--color-error-border: rgba(220, 38, 38, 0.24);

--color-info: #0284c7;
--color-info-soft: rgba(2, 132, 199, 0.12);
--color-info-border: rgba(2, 132, 199, 0.24);
```

Regla:

- Status con chips suaves, no bloques saturados.
- Error debe ser claro y visible.
- Warning no debe parecer error.
- Success no debe usarse para decorar.

## 4. Tipografía

### Familia

Usar la fuente existente del proyecto si ya está definida y es moderna. Si no hay una decisión clara, usar stack del sistema:

```css
--font-sans: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
```

No instalar dependencias nuevas solo para tipografía.

### Pesos

```css
--font-regular: 400;
--font-medium: 500;
--font-semibold: 600;
--font-bold: 700;
```

### Jerarquía

```css
--text-xs: 0.75rem;
--text-sm: 0.875rem;
--text-base: 1rem;
--text-lg: 1.125rem;
--text-xl: 1.25rem;
--text-2xl: 1.5rem;
--text-3xl: 1.875rem;
```

Uso:

- H1: 28–32px, 700.
- H2: 22–24px, 650/700.
- H3: 18–20px, 600.
- Body: 14–16px, 400/500.
- Labels: 12–13px, 500/600.
- Table text: 13–14px.

Regla:

- Evitar títulos enormes en pantallas operativas.
- Dashboard puede tener más aire visual.
- Nómina y empleados deben priorizar lectura rápida.

## 5. Layout

## PageShell

Todas las páginas deben vivir dentro de un `PageShell` común.

Características:

- Fondo claro premium con gradiente sutil.
- Padding superior suficiente para navbar flotante.
- Max width controlado.
- Espacing consistente.
- Sin sidebar.

Tokens sugeridos:

```css
--page-max-width: 1280px;
--page-padding-x: 24px;
--page-padding-y: 32px;
--navbar-height: 64px;
--navbar-top: 18px;
```

En mobile, reducir padding.

## Navbar flotante

Formato elegido:

- Barra flotante amplia.
- Fit width, no full width rígido.
- Centrada horizontalmente.
- Glass visible.
- Bordes redondeados altos.
- Active state claro.
- Agrupar navegación en dropdowns.

Estructura sugerida:

- Izquierda: marca Axis.
- Centro: navegación principal y dropdowns.
- Derecha: usuario, rol, logout o menú de cuenta.

Navegación sugerida:

- Dashboard
- Capital Humano
  - Empleados
  - Importación
  - Vacaciones
- Operaciones
  - Incidencias
  - Préstamos
  - Horas extra
- Nómina
  - Preview
  - Reportes
  - Historial
  - Snapshots
- Administración, si aplica por rol

Regla:

- No meter todas las rutas como links sueltos si la navbar se vuelve larga.
- Usar dropdowns por módulo.
- Mostrar opciones según rol si el sistema ya lo hace; no cambiar lógica de permisos.

## Spacing

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
```

Regla:

- Usar spacing consistente.
- No inventar márgenes por pantalla.
- Dashboard puede usar más spacing.
- Tablas y formularios operativos deben mantener densidad media.

## Grids

- Dashboard: grid responsive de KPI cards y charts.
- Empleados: tabla/lista principal + filtros superiores.
- Detalle de empleado: grid de secciones.
- Formularios: 2 columnas en desktop, 1 columna en mobile.
- Nómina: layout más denso y funcional.

## 6. Glassmorphism

Nivel elegido: **medio**, aplicado a todo el proyecto.

Esto significa:

- El lenguaje glass debe ser consistente en todas las pantallas.
- No todas las superficies deben ser igual de transparentes.
- La legibilidad manda.

### Receta base

```css
.glass-surface {
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.72);
  box-shadow: 0 18px 60px rgba(15, 23, 42, 0.08);
  backdrop-filter: blur(20px) saturate(160%);
  -webkit-backdrop-filter: blur(20px) saturate(160%);
}
```

### Glass en navbar

```css
.glass-navbar {
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.10);
  backdrop-filter: blur(24px) saturate(170%);
  -webkit-backdrop-filter: blur(24px) saturate(170%);
}
```

### Glass en tablas

Las tablas no deben ser demasiado translúcidas.

Usar:

```css
.data-panel {
  background: rgba(255, 255, 255, 0.86);
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 18px 50px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(16px) saturate(145%);
}
```

### Cuándo usar glass fuerte

- Login card.
- Modales.
- Navbar.
- Dropdowns.
- Empty states.

### Cuándo usar glass moderado

- Dashboard cards.
- KPI cards.
- Paneles de filtros.
- Formularios.

### Cuándo usar glass sólido

- Tablas.
- Nómina.
- Captura operativa.
- Información financiera crítica.

## 7. Radios, sombras y bordes

### Radios

Nivel elegido: alto.

```css
--radius-sm: 10px;
--radius-md: 14px;
--radius-lg: 18px;
--radius-xl: 24px;
--radius-2xl: 28px;
--radius-pill: 999px;
```

Uso:

- Navbar: pill / 999px o 28px.
- Cards: 24–28px.
- Modales: 24–28px.
- Inputs: 12–16px.
- Tablas: contenedor 20–24px, celdas sin redondeo excesivo.
- Badges: pill.

### Sombras

```css
--shadow-xs: 0 1px 2px rgba(15, 23, 42, 0.05);
--shadow-sm: 0 8px 24px rgba(15, 23, 42, 0.06);
--shadow-md: 0 18px 50px rgba(15, 23, 42, 0.08);
--shadow-lg: 0 24px 80px rgba(15, 23, 42, 0.12);
```

Regla:

- Sombras suaves, no dramáticas.
- Evitar sombra negra pesada.
- La profundidad debe sentirse premium, no flotante artificial.

## 8. Componentes base

## PageShell

Responsabilidad:

- Fondo global.
- Espacing general.
- Max width.
- Contenedor principal.

Props sugeridas:

- `title`
- `description`
- `actions`
- `children`
- `maxWidth`

## FloatingNavbar

Responsabilidad:

- Navegación principal.
- Dropdowns por módulo.
- Estado activo.
- Usuario/rol.
- Logout.

Reglas:

- No cambiar rutas.
- No cambiar guards.
- No cambiar auth flow.
- No introducir sidebar.

## GlassCard

Variantes:

- `default`
- `strong`
- `subtle`
- `interactive`

Reglas:

- Usar como contenedor base.
- No crear cards custom por pantalla si GlassCard resuelve el caso.

## Button

Variantes:

- `primary`
- `secondary`
- `ghost`
- `danger`
- `success`

Tamaños:

- `sm`
- `md`
- `lg`

Reglas:

- Acción primaria visible y única por sección.
- Botones destructivos deben pedir confirmación visual cuando aplique.
- No usar `alert()` para flujos críticos.

## Input

Estados:

- default;
- focus;
- error;
- disabled;
- loading si aplica.

Reglas:

- Label siempre visible en formularios críticos.
- Placeholder no reemplaza label.
- Error debajo del campo.

## Select

Debe seguir el mismo lenguaje que Input.

Reglas:

- Usar altura consistente.
- Dropdown legible.
- No hacer selects demasiado decorativos en pantallas densas.

## Modal

Uso:

- Alta/baja de empleados.
- Confirmaciones críticas.
- Detalles contextuales.
- Acciones de nómina.

Reglas:

- Glass fuerte, pero contenido sólido.
- Header claro.
- Footer con acciones.
- Acción destructiva separada visualmente.

## StatusBadge

Variantes:

- success;
- warning;
- error;
- info;
- neutral;
- accent.

Uso:

- Estatus de empleados.
- Incidencias.
- Préstamos.
- Estados de nómina.
- Permisos.

## DataTable

Responsabilidad:

- Tabla consistente.
- Header sobrio.
- Hover claro.
- Empty state integrado.
- Loading state integrado.

Reglas:

- Densidad limpia pero compacta.
- No saturar con bordes pesados.
- Acciones por fila alineadas a la derecha.
- Badges para estados.
- Filtros arriba de la tabla.

## LoadingState

Debe reemplazar textos pobres como `Cargando sesion...`.

Contenido:

- Spinner o skeleton sutil.
- Mensaje en español.
- Card/panel centrado si es pantalla completa.

Ejemplos:

- `Validando sesión...`
- `Cargando empleados...`
- `Preparando información de nómina...`

## ErrorState

Debe incluir:

- título claro;
- explicación breve;
- acción si aplica;
- estilo visual consistente.

Ejemplos:

- `No se pudo cargar la información.`
- `Reintentar`
- `Volver al dashboard`

## EmptyState

Debe incluir:

- mensaje útil;
- acción primaria si aplica;
- no debe sentirse como error.

Ejemplos:

- `No hay incidencias registradas para este periodo.`
- `Crear incidencia`

## 9. Estados del sistema

### Loading

- Usar skeletons cuando hay tablas/cards.
- Usar spinner solo para cargas cortas.
- Mensajes siempre en español.

### Empty

- Texto claro.
- Acción sugerida si aplica.
- No usar pantalla vacía sin explicación.

### Error

- Mostrar qué falló.
- No filtrar errores técnicos al usuario final salvo útil.
- Permitir reintentar si aplica.

### Disabled

- Debe ser visible.
- No reducir opacidad al punto de ilegibilidad.
- Agregar tooltip o texto si la acción está bloqueada por rol.

### Success

- Confirmaciones visuales no intrusivas.
- Evitar `alert()`.
- Preferir toast interno si ya existe; si no existe, estado inline.

### Permission denied

Reemplazar estado pobre de ProtectedRoute.

Debe mostrar:

- título: `Acceso no autorizado`;
- explicación: `Tu rol actual no tiene permiso para ver esta sección.`;
- acción: `Volver al dashboard`;
- diseño glass consistente.

## 10. Tablas y AG Grid

Densidad elegida: limpia pero compacta.

### Headers

- Texto pequeño, uppercase opcional.
- Peso 600.
- Color muted.
- Fondo muy sutil.

### Filas

- Altura media.
- Hover suave.
- Separadores ligeros.
- Sin zebra stripes fuertes.

### Celdas

- Texto principal slate oscuro.
- Metadatos muted.
- Números alineados correctamente.
- Fechas consistentes.
- Montos con formato claro.

### Filtros

- Panel superior glass.
- Search visible.
- Filtros agrupados.
- Acciones secundarias no deben competir con acción principal.

### Acciones por fila

- Usar botones ghost/icon.
- Confirmar acciones destructivas.
- Evitar `alert()`.

### Badges

- Estados con chips suaves.
- No usar colores saturados como fondo completo.

## 11. Dashboard

El dashboard puede ser más visual que las pantallas operativas.

### KPI cards

- Glass medio.
- Título pequeño.
- Valor fuerte.
- Delta o contexto en muted/status.
- Iconos sutiles si ya existen.

### Charts

- No hardcodear colores directamente en componentes.
- Usar tokens CSS o constantes de tema.
- Paleta limitada.
- Tooltips con surface glass/strong.
- Gridlines sutiles.

Colores permitidos para charts:

```css
--chart-1: #2563eb;
--chart-2: #64748b;
--chart-3: #16a34a;
--chart-4: #d97706;
--chart-5: #7c3aed;
--chart-danger: #dc2626;
```

Regla:

- No usar arcoíris.
- No usar colores decorativos sin significado.
- Finanzas/nómina debe usar colores sobrios.

## 12. Formularios

### Labels

- Siempre visibles.
- Peso 500/600.
- Color slate.

### Inputs

- Altura consistente.
- Bordes sutiles.
- Focus con accent ring.
- Background surface strong.

### Validación

- Error debajo del campo.
- Color error.
- Mensaje accionable.

### Botones

- Primario a la derecha en modales.
- Cancelar secundario.
- Destructivo separado.

### Captura operativa

- Priorizar velocidad.
- No esconder campos esenciales.
- No usar animaciones que ralenticen.

## 13. Login

El login debe estar completamente en español.

Reemplazar:

- `Welcome Back` por `Bienvenido de nuevo` o `Acceso a Axis`.
- `Username` por `Usuario`.
- `Password` por `Contraseña`.
- `Sign In` por `Iniciar sesión`.

Estilo:

- Card glass centrada.
- Fondo claro premium con gradiente sutil.
- Marca Axis visible.
- Mensajes de error claros.
- No modificar auth flow.

## 14. ProtectedRoute

Reemplazar estilos inline.

Estados requeridos:

- Loading: `Validando sesión...`
- Permission denied: `Acceso no autorizado`
- Error si aplica.

Reglas:

- No cambiar lógica de permisos.
- No cambiar token refresh.
- Solo mejorar UI.

## 15. Reglas de implementación

### Permitido

- Crear tokens CSS.
- Crear componentes UI reutilizables.
- Mejorar estados visuales.
- Reemplazar estilos inline por clases/componentes.
- Rediseñar por fases.
- Usar CSS existente si se puede ordenar.

### Prohibido

- Tocar backend.
- Tocar models.
- Tocar migrations.
- Tocar serializers.
- Tocar services de nómina.
- Tocar permisos/RBAC.
- Cambiar endpoints.
- Cambiar payloads.
- Cambiar auth flow/token refresh salvo bug visual inevitable.
- Instalar dependencias.
- Usar Supabase desde frontend.
- Crear sidebar.
- Usar `git add .`.
- Subir `.env`, `supabase/`, dumps, CSVs o backups.

### CSS

- No estilos inline salvo valores dinámicos inevitables.
- No duplicar CSS por pantalla.
- Usar tokens.
- Crear componentes base antes de rediseñar pantallas complejas.
- No meter colores hardcodeados si existe token.

### React

- Separar lógica de UI cuando sea posible.
- No reescribir flujos funcionales por estética.
- No cambiar rutas.
- No cambiar guards.
- No tocar endpoints.

## 16. Fases de implementación

## Fase 0 — Design.md e identidad visual

Objetivo:

- Crear esta fuente de verdad visual.
- Auditar si existen documentos visuales anteriores.
- Eliminar/reemplazar documentación visual obsoleta solo con aprobación.

Archivo:

- `docs/design.md`

No tocar código de aplicación.

## Fase 1 — Design system base

Objetivo:

- Crear base visual reutilizable sin rediseñar pantallas completas.

Archivos permitidos:

- `frontend/src/index.css`
- `frontend/src/styles/*`
- `frontend/src/components/ui/*`
- `frontend/src/auth/ProtectedRoute.tsx` solo estados visuales
- `frontend/src/components/Login.tsx`
- `frontend/src/components/Login.css`
- `frontend/src/App.tsx` solo si hace falta PageShell sin cambiar rutas

Componentes base:

- PageShell
- GlassCard
- Button
- Input
- Select
- Modal
- StatusBadge
- DataTable
- LoadingState
- ErrorState
- EmptyState

Validación:

```powershell
cd C:\Users\jetro\Downloads\Axis\frontend
npm.cmd run build
```

Manual:

- login;
- logout;
- ruta protegida;
- acceso denegado;
- sesión expirada si aplica.

## Fase 2 — Layout + navbar flotante

Objetivo:

- Convertir navbar actual en floating glass navbar.
- Mantener rutas.
- Mantener role guards.
- Sin sidebar.
- Dropdowns glass.
- Responsive básico.
- Page content con spacing correcto.

Validación:

- rutas actuales funcionan;
- dropdowns funcionan;
- logout funciona;
- mobile básico no se rompe.

## Fase 3 — Dashboard

Objetivo:

- Dashboard premium glass.
- KPI cards.
- Charts con tokens.
- Loading/error/empty states.
- Sin cambiar endpoint `/api/payroll/dashboard/`.

Validación:

- dashboard carga;
- datos reales se muestran;
- build OK.

## Fase 4 — Capital Humano / Empleados

Objetivo:

- Rediseñar EmployeeDirectory y EmployeeDetail.
- Mejorar tablas, cards, modales alta/baja.
- Reemplazar `alert()` por estados visuales.
- Mantener endpoints y payloads.
- No cambiar lógica de alta/baja.

Orden:

1. EmployeeDirectory visual.
2. EmployeeDetail visual.
3. VacationStatus.
4. ImportView.

## Fase 5 — Operaciones

Objetivo:

- Incidencias.
- Préstamos.
- Estados visuales consistentes.
- Formularios premium pero rápidos para captura.

## Fase 6 — Nómina

Dejar al final porque es zona crítica.

Objetivo:

- PayrollView.
- PayrollReport.
- ExtraHoursView.
- HistoryView.
- GridRenderers.
- Preview/commit visualmente claros.

Respetar restricciones:

- Finance puede commit.
- HR no puede commit.
- Segundo commit mismo periodo debe dar 409.
- Snapshots visibles.

## Fase 7 — QA visual y funcional

Validaciones:

- `npm.cmd run build` pasa.
- Login funciona.
- Dashboard carga.
- Empleados 40 visibles.
- Incidencias funcionan.
- Préstamos funcionan.
- Horas extra funcionan.
- Preview nómina funciona.
- Finance commit funciona.
- HR commit bloqueado.
- Segundo commit mismo periodo devuelve 409.
- Snapshots visibles.
- Git diff solo frontend visual/docs.
- No backend changes.

## 17. Checklist de aceptación visual

Antes de aprobar cualquier fase visual:

- La UI se siente parte del mismo sistema.
- No hay mezcla visible entre slate viejo y glass nuevo.
- No hay sidebar.
- Navbar es flotante glass.
- Login está en español.
- No hay textos pobres como `Cargando sesion...`.
- Estados loading/error/empty están diseñados.
- No hay `alert()` en flujos rediseñados.
- No hay colores hardcodeados si existe token.
- Tablas son limpias, legibles y no saturadas.
- Cards tienen glass consistente.
- Bordes y sombras son suaves.
- Responsive básico no se rompe.
- Build pasa.
- No se tocó backend.
- No se tocó lógica crítica.

## 18. Observaciones desde referencias visuales

Patrones extraídos de las imágenes de inspiración:

- Fondos claros con aire visual amplio.
- Superficies blancas translúcidas y elevadas.
- Bordes redondeados altos.
- Sombras suaves y difusas.
- Tablas limpias con headers discretos.
- Acciones principales en botones negros o azules sólidos.
- Uso moderado de chips de estado.
- Mucho whitespace, pero sin perder estructura.
- Jerarquía fuerte en títulos y contenido principal.
- Filtros agrupados sobre tablas.
- Cards con profundidad sutil.
- Menús limpios, no saturados.

Ajuste necesario para Axis:

Las referencias son visualmente limpias, pero varias son demasiado ligeras para una app de RH/nómina. Axis debe conservar más estructura operativa: filtros claros, tablas legibles, estados robustos y acciones críticas explícitas. El glass debe elevar la experiencia, no ocultar información ni reducir velocidad de captura.

