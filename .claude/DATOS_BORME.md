# Datos disponibles del BORME

El Boletín Oficial del Registro Mercantil (BORME) publica diariamente información sobre empresas españolas. Estos son los datos que se pueden descargar y almacenar.

---

## 1. BORME (Edición del boletín)

Cada edición diaria del BORME contiene:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `cve` | String | Identificador único (ej: "BORME-A-2024-123-28") |
| `date` | Date | Fecha de publicación |
| `url` | URL | Enlace al PDF original |
| `province` | String | Provincia (Madrid, Barcelona, etc.) |
| `section` | String | Sección (A = Actos inscritos, B = Otros) |
| `from_reg` | Int | Número de registro inicial |
| `until_reg` | Int | Número de registro final |
| `anuncios` | JSON | Lista de IDs de anuncios publicados |

---

## 2. EMPRESAS (Company)

Información de cada sociedad mercantil:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | String | Nombre de la empresa |
| `slug` | String | Identificador URL-friendly |
| `nif` | String | NIF/CIF de la empresa |
| `type` | String | Tipo de sociedad (ver lista abajo) |
| `date_creation` | Date | Fecha de constitución |
| `date_extinction` | Date | Fecha de extinción (si aplica) |
| `is_active` | Bool | Si la empresa está activa |
| `date_updated` | Date | Última actualización |
| `in_bormes` | JSON | Lista de BORMEs donde aparece |
| `anuncios` | JSON | Lista de anuncios de la empresa |
| `cargos_actuales_p` | JSON | Cargos vigentes de personas |
| `cargos_actuales_c` | JSON | Cargos vigentes de otras empresas |
| `cargos_historial_p` | JSON | Historial de cargos de personas |
| `cargos_historial_c` | JSON | Historial de cargos de empresas |

### Tipos de sociedad disponibles
- SL (Sociedad Limitada)
- SA (Sociedad Anónima)
- SLU (Sociedad Limitada Unipersonal)
- SAU (Sociedad Anónima Unipersonal)
- COOP (Cooperativa)
- SCL (Sociedad Cooperativa Limitada)
- Y muchos más...

---

## 3. PERSONAS (Person)

Información de personas físicas vinculadas a empresas:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | String | Nombre completo |
| `slug` | String | Identificador URL-friendly |
| `date_updated` | Date | Última actualización |
| `in_companies` | JSON | Lista de empresas donde participa |
| `in_bormes` | JSON | Lista de BORMEs donde aparece |
| `cargos_actuales` | JSON | Cargos vigentes |
| `cargos_historial` | JSON | Historial de cargos |

---

## 4. ANUNCIOS

Cada anuncio mercantil publicado:

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id_anuncio` | Int | Número de anuncio |
| `year` | Int | Año de publicación |
| `borme` | FK | Referencia al BORME |
| `company` | FK | Referencia a la empresa |
| `datos_registrales` | String | Datos del registro mercantil |
| `actos` | JSON | Diccionario de actos (ver abajo) |

---

## 5. ACTOS MERCANTILES

Los actos que se registran en cada anuncio:

### Actos de cargos (nombramientos/ceses)
- **Nombramientos**: Administrador, Consejero, Presidente, Secretario, etc.
- **Ceses/Dimisiones**: De cualquiera de los cargos anteriores
- **Revocaciones**: Revocación de poderes

### Actos de capital
- Constitución
- Ampliación de capital
- Reducción de capital
- Cambio de domicilio social
- Cambio de denominación social

### Actos de estado
- Disolución
- Extinción
- Declaración de unipersonalidad
- Pérdida de unipersonalidad
- Fusión
- Escisión

### Otros actos
- Modificación de estatutos
- Depósito de cuentas anuales
- Situación concursal
- Reapertura hoja registral
- Cancelación
- Datos registrales

---

## 6. ESTRUCTURA DE CARGOS

Cada cargo tiene esta estructura JSON:

```json
{
  "name": "EMPRESA XYZ SL",      // Nombre de la empresa
  "title": "Administrador",      // Tipo de cargo
  "date_from": "2020-01-15",     // Fecha de nombramiento
  "date_to": "2023-06-30"        // Fecha de cese (solo en historial)
}
```

### Tipos de cargos disponibles
- Administrador Único
- Administrador Solidario
- Administrador Mancomunado
- Consejero
- Presidente
- Vicepresidente
- Secretario
- Consejero Delegado
- Director General
- Liquidador
- Apoderado
- Auditor
- Y otros...

---

## 7. COMANDOS CLI

```bash
# Inicializar base de datos
borme init

# Ver estadísticas
borme status

# Descargar rango de fechas
borme download --from 2024-01-01 --to 2024-12-31

# Descargar el BORME de hoy
borme today

# Importar PDF específico
borme pdf archivo.pdf

# Importar JSON específico
borme json archivo.json
```

---

## 8. FUENTE DE DATOS

- **URL oficial**: https://www.boe.es/diario_borme/
- **Formato**: PDF (convertido a JSON por bormeparser)
- **Frecuencia**: Diaria (excepto fines de semana y festivos)
- **Histórico disponible**: Desde 2009
- **Librería de parsing**: `bormeparser`
