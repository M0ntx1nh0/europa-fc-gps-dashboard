# ✅ CHECKLIST DE VERIFICACIÓN

## 📁 Archivos Necesarios

Verifica que tienes todos estos archivos:

### Raíz del proyecto:
- [ ] app.py
- [ ] config.py
- [ ] requirements.txt
- [ ] setup.sh
- [ ] README.md
- [ ] INICIO_RAPIDO.md
- [ ] .gitignore

### Carpeta utils/:
- [ ] utils/__init__.py
- [ ] utils/data_loader.py
- [ ] utils/data_processor.py
- [ ] utils/calculations.py

### Carpeta pages/:
- [ ] pages/1_🏠_Home.py
- [ ] pages/2_📊_Equipo.py
- [ ] pages/3_👤_Individual.py

### Carpeta data/:
- [ ] data/ (carpeta vacía o con .gitkeep)

---

## 🔧 Pasos de Instalación

1. [ ] Copiar todos los archivos a `/Users/macmontxinho/Desktop/Teams/Europa/Europa_APP`

2. [ ] Ejecutar `bash setup.sh`

3. [ ] Copiar archivos CSV a `data/`

4. [ ] Activar venv: `source venv/bin/activate`

5. [ ] Ejecutar: `streamlit run app.py`

---

## ✓ Verificación

Para verificar que todo funciona:

```bash
# 1. Verificar archivos
ls -la

# 2. Verificar entorno virtual
source venv/bin/activate
python --version

# 3. Verificar dependencias
pip list | grep streamlit

# 4. Verificar CSV
ls data/*.csv

# 5. Ejecutar app
streamlit run app.py
```

---

## 🎯 Primera Ejecución

Cuando ejecutes la app por primera vez:

1. [ ] Se abre en http://localhost:8501
2. [ ] Aparece la página principal con "Bienvenido"
3. [ ] Haces clic en "🔄 Cargar/Recargar Datos"
4. [ ] Aparece "✅ Datos cargados correctamente"
5. [ ] Puedes seleccionar fechas en el sidebar
6. [ ] Puedes navegar a las páginas 🏠 📊 👤

---

## ❌ Problemas Comunes

### No se encuentra Python:
```bash
python3 --version
```

### No se encuentra pip:
```bash
python3 -m pip --version
```

### Permisos denegados en setup.sh:
```bash
chmod +x setup.sh
```

### No se cargan los CSV:
```bash
# Verificar que existen
ls -la data/

# Verificar formato
head -2 data/total_report_*.csv | head -1
```

---

## 📞 Soporte

Si algo no funciona:

1. Verifica este checklist
2. Lee el README.md
3. Revisa INICIO_RAPIDO.md
4. Comprueba los mensajes de error en la terminal

---

✅ **Todo listo cuando todos los checkboxes están marcados**
