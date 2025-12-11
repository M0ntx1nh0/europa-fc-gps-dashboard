# ⚽ Europa FC - Sistema de Análisis GPS

Aplicación profesional de Streamlit para análisis de datos físicos de partidos.

## 📁 Estructura del Proyecto

```
Europa_APP/
├── venv/                          # Entorno virtual (crear localmente)
├── data/                          # CSV de GPS (crear localmente)
│   ├── total_report_*.csv
│   └── ...
├── utils/                         # Módulo de utilidades
│   ├── __init__.py
│   ├── data_loader.py            # Carga de CSV
│   ├── data_processor.py         # Procesamiento
│   └── calculations.py           # Cálculos y normalizaciones
├── pages/                         # Páginas de la app
│   ├── 1_🏠_Home.py              # Referencias normalizadas
│   ├── 2_📊_Equipo.py            # Análisis de equipo
│   └── 3_👤_Individual.py        # Análisis individual
├── app.py                         # Aplicación principal
├── config.py                      # Configuración centralizada
├── requirements.txt               # Dependencias
├── .gitignore
└── README.md                      # Este archivo
```

---

## 🚀 Instalación y Configuración

### **1. Crear la estructura en tu máquina:**

```bash
# Navegar a la carpeta
cd /Users/macmontxinho/Desktop/Teams/Europa

# Crear carpeta del proyecto
mkdir -p Europa_APP/data
cd Europa_APP
```

### **2. Copiar los archivos:**

Copia todos los archivos de esta carpeta a `/Users/macmontxinho/Desktop/Teams/Europa/Europa_APP/`

### **3. Crear entorno virtual:**

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate  # En macOS/Linux
```

### **4. Instalar dependencias:**

```bash
pip install -r requirements.txt
```

### **5. Copiar archivos CSV a la carpeta data/:**

```bash
# Copiar tus CSV a la carpeta data/
cp /Users/macmontxinho/Desktop/Teams/Europa/Partidos/1er\ equipo/total_report_*.csv data/
```

O puedes crear un enlace simbólico:

```bash
# Crear enlace simbólico a la carpeta original
ln -s "/Users/macmontxinho/Desktop/Teams/Europa/Partidos/1er equipo" data
```

---

## ▶️ Ejecutar la Aplicación

```bash
# Asegurarte de estar en la carpeta Europa_APP
cd /Users/macmontxinho/Desktop/Teams/Europa/Europa_APP

# Activar entorno virtual (si no está activado)
source venv/bin/activate

# Ejecutar la app
streamlit run app.py
```

La aplicación se abrirá automáticamente en: `http://localhost:8501`

---

## 📊 Cómo Usar la App

### **1. Cargar Datos:**
- En el sidebar, haz clic en "🔄 Cargar/Recargar Datos"
- La app cargará todos los CSV de la carpeta `data/`
- Verás un mensaje de confirmación

### **2. Configurar Filtros:**
- **Fechas:** Selecciona el rango que quieres analizar
- **Partido:** Elige el partido específico
- **Métrica:** Selecciona la métrica a visualizar

### **3. Navegar por las Páginas:**

#### **🏠 Home - Referencias**
- Tabla de estadísticas normalizadas a 94 minutos
- Solo jugadores con >60 minutos
- Base de comparación para análisis

#### **📊 Equipo**
- Análisis del partido seleccionado
- Comparación vs referencias
- Evolución temporal del equipo

#### **👤 Individual**
- Ranking de jugadores
- Evolución individual
- Comparativas entre jugadores

---

## 🔧 Configuración

### **Cambiar carpeta de datos:**

Edita `config.py`:

```python
# Rutas
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"  # ← Cambiar aquí
```

### **Añadir nuevas métricas:**

Edita `config.py`:

```python
METRICAS_DICT = {
    'Mi Nueva Métrica': 'columna_csv',
    # ...
}
```

---

## 📦 Módulos

### **utils/data_loader.py**
- `cargar_datos_csv()`: Carga CSV de la carpeta
- `validar_columnas()`: Valida estructura
- `obtener_info_dataset()`: Información del dataset

### **utils/data_processor.py**
- `procesar_datos()`: Procesa y limpia datos
- `convertir_tiempo_a_minutos()`: Convierte MM:SS a decimal
- `filtrar_por_fechas()`: Filtra por rango
- `obtener_partidos_disponibles()`: Lista partidos

### **utils/calculations.py**
- `calcular_referencias_normalizadas()`: Normalización a 94 min
- `calcular_estadisticas_partido()`: Stats de partido
- `calcular_z_score()`: Cálculo de z-scores
- `clasificar_rendimiento()`: Clasificación de rendimiento

---

## 🌐 Desplegar en Streamlit Cloud

### **1. Subir a GitHub:**

```bash
# Inicializar repositorio
git init

# Añadir archivos (sin CSV grandes)
git add .

# Commit
git commit -m "Initial commit - Europa FC GPS App"

# Conectar con GitHub
git remote add origin https://github.com/tu-usuario/europa-gps.git
git push -u origin main
```

### **2. Configurar Streamlit Cloud:**

1. Ve a https://share.streamlit.io/
2. Conecta tu repositorio de GitHub
3. Selecciona:
   - Branch: `main`
   - Main file: `app.py`
4. Click en "Deploy"

**Nota:** Para deployment en la nube, los CSV deben estar en el repo o usar una base de datos externa.

---

## 🛠️ Troubleshooting

### **Error: "No se encontraron archivos CSV"**
- Verifica que los CSV están en `data/`
- Verifica que empiezan con `total_report_`
- Verifica permisos de lectura

### **Error al importar módulos**
```bash
# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### **Streamlit no se abre**
```bash
# Verificar puerto
streamlit run app.py --server.port 8502
```

---

## 📝 Notas Técnicas

### **Normalización a 94 minutos:**
- Solo para calcular referencias
- Solo jugadores >60 minutos
- Fórmula: `valor_94min = valor_original × (94 / tiempo_jugado)`

### **Métricas acumulativas normalizadas:**
- total_distance, hsr, distance_vrange6
- sprints, num_acc_expl, num_dec_expl, hmld

### **Métricas NO normalizadas:**
- minute_distance (ya es por minuto)
- max_speed (es un pico)
- hsr_rel, hmld_relative (ya son relativos)

---

## 🔄 Actualizar Datos

Para añadir nuevos partidos:

```bash
# Copiar nuevos CSV a data/
cp nuevo_partido.csv data/

# Recargar la app (automático)
# O hacer clic en "🔄 Cargar/Recargar Datos"
```

---

## 📧 Soporte

Para dudas técnicas:
- Revisar este README
- Verificar que los CSV tienen el formato correcto
- Comprobar que `task='Total'` existe en los datos

---

**Desarrollado para Europa FC** ⚽📊  
**Versión 1.0** - Noviembre 2025
