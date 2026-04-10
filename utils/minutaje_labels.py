"""
Utilidades compartidas para las etiquetas de minutaje en app y PDF.
"""


def obtener_contexto_tramo(filtro_parte, nombre_serie=None):
    tramo = filtro_parte
    if filtro_parte == "1ª + 2ª (Separadas)" and nombre_serie is not None:
        nombre_serie = str(nombre_serie)
        if nombre_serie.endswith(" - 1ª Parte"):
            tramo = "1ª Parte"
        elif nombre_serie.endswith(" - 2ª Parte"):
            tramo = "2ª Parte"
    return tramo


def obtener_label_minutos(nivel_analisis, filtro_parte, nombre_serie=None, compacto=False):
    tramo = obtener_contexto_tramo(filtro_parte, nombre_serie)

    if nivel_analisis == "Individual":
        if tramo == "Total":
            return "MT" if compacto else "Min total"
        if tramo == "1ª Parte":
            return "M1ª" if compacto else "Min 1ª"
        if tramo == "2ª Parte":
            return "M2ª" if compacto else "Min 2ª"
        return "MA" if compacto else "Min acum"

    if tramo == "Total":
        return "MM" if compacto else "Min med"
    if tramo == "1ª Parte":
        return "MM1ª" if compacto else "Min med 1ª"
    if tramo == "2ª Parte":
        return "MM2ª" if compacto else "Min med 2ª"
    return "MMA" if compacto else "Min med acum"


def obtener_umbral_minutos(filtro_parte, nombre_serie=None):
    tramo = obtener_contexto_tramo(filtro_parte, nombre_serie)
    if tramo in ["1ª Parte", "2ª Parte"]:
        return 30
    return 60


def usar_etiqueta_compacta(total_series, total_fechas, soporte="app"):
    total_series = max(int(total_series or 0), 1)
    total_fechas = max(int(total_fechas or 0), 1)
    total_barras = total_series * total_fechas

    if soporte == "pdf":
        return total_barras >= 12 or total_series >= 5 or total_fechas >= 5

    return total_barras >= 9 or total_series >= 4 or total_fechas >= 5
