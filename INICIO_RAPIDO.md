# 🚀 GUÍA DE INICIO RÁPIDO

## ⚡ Instalación Automática (Recomendado)

```bash
# 1. Descargar todos los archivos a:
#    /Users/macmontxinho/Desktop/Teams/Europa/Europa_APP

# 2. Abrir terminal y navegar a la carpeta
cd /Users/macmontxinho/Desktop/Teams/Europa/Europa_APP

# 3. Ejecutar script de configuración
bash setup.sh

# 4. Copiar archivos CSV a data/
cp /Users/macmontxinho/Desktop/Teams/Europa/Partidos/1er\ equipo/total_report_*.csv data/

# 5. Ejecutar la app
source venv/bin/activate
streamlit run app.py
```

---

## 🔧 Instalación Manual

### **Paso 1: Crear estructura**

```bash
cd /Users/macmontxinho/Desktop/Teams/Europa
mkdir -p Europa_APP/data
cd Europa_APP
```

### **Paso 2: Copiar archivos**

Copia todos los archivos de esta carpeta a `Europa_APP/`

### **Paso 3: Configurar entorno**

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### **Paso 4: Copiar datos**

```bash
# Opción A: Copiar archivos
cp /Users/macmontxinho/Desktop/Teams/Europa/Partidos/1er\ equipo/total_report_*.csv data/

# Opción B: Enlace simbólico
ln -s "/Users/macmontxinho/Desktop/Teams/Europa/Partidos/1er equipo" data/partidos
```

### **Paso 5: Ejecutar**

```bash
streamlit run app.py
```

---

## 📊 Primer Uso

1. **La app se abre en:** `http://localhost:8501`

2. **En el sidebar:**
   - Haz clic en "🔄 Cargar/Recargar Datos"
   - Espera a que carguen los CSV
   - Verás "✅ Datos cargados correctamente"

3. **Configura filtros:**
   - Selecciona rango de fechas
   - Elige un partido
   - Selecciona una métrica

4. **Explora las páginas:**
   - 🏠 Home → Referencias
   - 📊 Equipo → Análisis de equipo
   - 👤 Individual → Análisis por jugador

---

## ❓ Solución de Problemas

### No encuentra los CSV:
```bash
# Verifica que están en data/
ls data/*.csv

# Verifica permisos
chmod 644 data/*.csv
```

### Error al activar venv:
```bash
# Recrea el entorno
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Streamlit no se abre:
```bash
# Prueba otro puerto
streamlit run app.py --server.port 8502
```

---

## 🔄 Actualizar Datos

Para añadir nuevos partidos:

```bash
# Copiar nuevo CSV
cp nuevo_partido.csv data/

# En la app, haz clic en "🔄 Cargar/Recargar Datos"
```

---

## 📝 Estructura Final

```
Europa_APP/
├── venv/                    ✓ Creado por setup.sh
├── data/                    ✓ Creado por setup.sh
│   └── total_report_*.csv  ← Copiar tus CSV aquí
├── utils/
│   ├── __init__.py
│   ├── data_loader.py
│   ├── data_processor.py
│   └── calculations.py
├── pages/
│   ├── 1_🏠_Home.py
│   ├── 2_📊_Equipo.py
│   └── 3_👤_Individual.py
├── app.py
├── config.py
├── requirements.txt
├── setup.sh                ← Ejecutar primero
└── README.md
```

---

**¡Listo para empezar! ⚽📊**
