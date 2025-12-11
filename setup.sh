#!/bin/bash

# Script de configuración para Europa FC GPS App
# Uso: bash setup.sh

echo "🎯 Configurando Europa FC GPS App..."
echo ""

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 1. Verificar que estamos en la carpeta correcta
if [ ! -f "app.py" ]; then
    echo -e "${RED}❌ Error: Este script debe ejecutarse desde la carpeta Europa_APP${NC}"
    exit 1
fi

echo -e "${BLUE}✓ Carpeta correcta${NC}"

# 2. Crear carpeta data si no existe
if [ ! -d "data" ]; then
    echo -e "${BLUE}📁 Creando carpeta data...${NC}"
    mkdir data
    echo -e "${GREEN}✓ Carpeta data creada${NC}"
else
    echo -e "${GREEN}✓ Carpeta data ya existe${NC}"
fi

# 3. Crear entorno virtual
if [ ! -d "venv" ]; then
    echo -e "${BLUE}🔧 Creando entorno virtual...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Entorno virtual creado${NC}"
else
    echo -e "${GREEN}✓ Entorno virtual ya existe${NC}"
fi

# 4. Activar entorno virtual
echo -e "${BLUE}🔄 Activando entorno virtual...${NC}"
source venv/bin/activate

# 5. Actualizar pip
echo -e "${BLUE}📦 Actualizando pip...${NC}"
pip install --upgrade pip --quiet

# 6. Instalar dependencias
echo -e "${BLUE}📦 Instalando dependencias...${NC}"
pip install -r requirements.txt --quiet
echo -e "${GREEN}✓ Dependencias instaladas${NC}"

# 7. Verificar archivos CSV
CSV_COUNT=$(ls data/total_report_*.csv 2>/dev/null | wc -l)
if [ $CSV_COUNT -eq 0 ]; then
    echo ""
    echo -e "${RED}⚠️  ATENCIÓN: No hay archivos CSV en data/${NC}"
    echo ""
    echo "Por favor, copia tus archivos CSV a la carpeta data/"
    echo "Ejemplo:"
    echo "  cp /ruta/a/tus/archivos/total_report_*.csv data/"
    echo ""
    echo "O crea un enlace simbólico:"
    echo "  ln -s '/ruta/a/tus/archivos' data"
    echo ""
else
    echo -e "${GREEN}✓ ${CSV_COUNT} archivos CSV encontrados en data/${NC}"
fi

# 8. Instrucciones finales
echo ""
echo -e "${GREEN}✅ Configuración completada!${NC}"
echo ""
echo "Para ejecutar la aplicación:"
echo -e "${BLUE}  1. Activa el entorno virtual: ${NC}source venv/bin/activate"
echo -e "${BLUE}  2. Ejecuta la app: ${NC}streamlit run app.py"
echo ""
echo "La app se abrirá en: http://localhost:8501"
echo ""
