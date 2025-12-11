# 📸 Fotos de Jugadores

## Cómo añadir fotos

### Formato de archivo:
- **Nombre:** `nombre_apellido.jpg` (todo en minúsculas, espacios reemplazados por guiones bajos)
- **Formatos soportados:** `.jpg`, `.jpeg`, `.png`, `.webp`
- **Tamaño recomendado:** 200x200 píxeles (cuadrado)
- **Peso recomendado:** < 500 KB

### Ejemplos:
```
pedro_garcia.jpg
juan_lopez.png
carlos_martinez.jpeg
```

### Pasos:

1. **Descargar foto del jugador** (preferiblemente cuadrada)

2. **Renombrar según el nombre en los datos GPS:**
   - Nombre en CSV: "Pedro García" → Foto: `pedro_garcia.jpg`
   - Nombre en CSV: "Juan López" → Foto: `juan_lopez.jpg`

3. **Copiar a esta carpeta:**
   ```bash
   cp foto_jugador.jpg /ruta/Europa_APP/assets/jugadores/
   ```

4. **Reiniciar la app** (o hacer clic en "Cargar/Recargar Datos")

---

## Si no hay foto

Si no existe foto para un jugador, la app mostrará automáticamente un **placeholder** con las iniciales del jugador en un círculo de color.

Ejemplo: "Pedro García" → Círculo azul con "PG"

---

## Optimizar fotos (opcional)

Para reducir el tamaño de las fotos:

### Usando ImageMagick:
```bash
convert foto.jpg -resize 200x200^ -gravity center -extent 200x200 -quality 85 foto_optimizada.jpg
```

### Usando Python (si tienes Pillow):
```python
from PIL import Image

img = Image.open('foto.jpg')
img = img.resize((200, 200), Image.LANCZOS)
img.save('foto_optimizada.jpg', optimize=True, quality=85)
```

---

## Estructura esperada:

```
assets/jugadores/
├── README.md (este archivo)
├── pedro_garcia.jpg
├── juan_lopez.png
├── carlos_martinez.jpg
└── ...
```

---

**Nota:** Las fotos NO se suben al repositorio de Git por defecto (para proteger privacidad y reducir tamaño del repo).

Si quieres incluirlas en Git, elimina `assets/jugadores/*.jpg` de `.gitignore`.
