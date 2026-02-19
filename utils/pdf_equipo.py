"""
Generador de PDF para informe de análisis de equipo
"""

from datetime import datetime
from pathlib import Path
import os
import tempfile

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fpdf import FPDF
import plotly.graph_objects as go
from utils.drive_loader import obtener_escudo_path


class PDFEquipo(FPDF):
    """PDF personalizado para informe de equipo."""

    def __init__(self):
        super().__init__()
        self.COLOR_AZUL = (1, 97, 157)

    def header(self):
        if self.page_no() > 1:
            escudo_path = obtener_escudo_path()
            if os.path.exists(escudo_path):
                self.image(escudo_path, x=175, y=6, w=20)

            self.set_draw_color(*self.COLOR_AZUL)
            self.set_line_width(0.4)
            self.line(10, 26, 200, 26)
            self.ln(18)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("Arial", "I", 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f"Pagina {self.page_no()-1}", 0, 0, "C")


def _crear_grafico_png(df_grafico, metrica_nombre, estadistico, nivel_analisis, mostrar_tendencia=False):
    """Crea una imagen PNG con el gráfico de barras del análisis actual."""
    df_plot = df_grafico.copy()
    if df_plot.empty:
        return None

    df_plot["fecha"] = pd.to_datetime(df_plot["fecha"])
    fechas = (
        df_plot[["fecha", "fecha_label"]]
        .drop_duplicates()
        .sort_values("fecha")["fecha_label"]
        .tolist()
    )
    nombres = df_plot["nombre"].drop_duplicates().tolist()

    fig, ax = plt.subplots(figsize=(12, 5.8))
    x = np.arange(len(fechas))
    total_series = max(len(nombres), 1)
    width = min(0.7 / total_series, 0.32)
    total_barras = max(len(fechas) * total_series, 1)
    fontsize_valor = max(9, min(14, int(15 - (total_barras * 0.15))))
    fontsize_min = max(8, fontsize_valor - 1)

    max_y = float(df_plot["valor"].max())

    for idx, nombre in enumerate(nombres):
        df_serie = (
            df_plot[df_plot["nombre"] == nombre]
            .set_index("fecha_label")
            .reindex(fechas)
        )
        valores = df_serie["valor"].astype(float).to_numpy()
        minutos = df_serie["minutaje"].astype(float).to_numpy()
        color = df_serie["color"].dropna().iloc[0] if not df_serie["color"].dropna().empty else "#1f77b4"

        offsets = x + (idx - (total_series - 1) / 2) * width
        bars = ax.bar(offsets, valores, width=width * 0.92, color=color, label=nombre)

        for i_bar, bar in enumerate(bars):
            if np.isnan(valores[i_bar]):
                continue
            min_color = "#d32f2f" if minutos[i_bar] < 60 else "#111111"
            x_bar = bar.get_x() + bar.get_width() / 2
            y_bar = bar.get_height()

            # Offsets en puntos para mantener posición estable independientemente de escala del eje.
            ax.annotate(
                f"{valores[i_bar]:.1f}",
                (x_bar, y_bar),
                xytext=(0, 8),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=fontsize_valor,
                color="#111111",
            )
            ax.annotate(
                f"Min={int(round(minutos[i_bar]))}'",
                (x_bar, y_bar),
                xytext=(0, -2),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=fontsize_min,
                color=min_color,
            )

        # Línea de tendencia lineal opcional en el fallback de matplotlib.
        if mostrar_tendencia:
            valid_mask = ~np.isnan(valores)
            if valid_mask.sum() >= 2:
                x_valid = np.arange(len(valores))[valid_mask]
                y_valid = valores[valid_mask]
                coef = np.polyfit(x_valid, y_valid, 1)
                trend_vals = coef[0] * x_valid + coef[1]
                ax.plot(
                    offsets[valid_mask],
                    trend_vals,
                    linestyle="--",
                    linewidth=2,
                    color=color,
                    alpha=0.9,
                )

    ax.set_title(f"{estadistico} de {metrica_nombre} - {nivel_analisis}", fontsize=18, fontweight="bold")
    ax.set_xlabel("Fecha del partido", fontsize=14)
    ax.set_ylabel(f"{metrica_nombre} ({estadistico})", fontsize=14)
    ax.set_xticks(x)
    ax.set_xticklabels(fechas, rotation=35, ha="right", fontsize=12)
    ax.tick_params(axis="y", labelsize=12)
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    ax.set_ylim(0, max_y * 1.22)

    if nivel_analisis != "Equipo" and len(nombres) > 1:
        ax.legend(loc="upper right", frameon=False, ncol=min(len(nombres), 4), fontsize=11)

    fig.tight_layout()

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        output_png = tmp_file.name
    fig.savefig(output_png, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return output_png


def _crear_png_desde_plotly(fig):
    """Genera PNG desde una figura Plotly (requiere engine de imagen disponible)."""
    try:
        fig_pdf = go.Figure(fig)
        barras = [t for t in fig_pdf.data if getattr(t, "type", None) == "bar"]
        n_trazas = max(len(barras), 1)
        n_partidos = 1
        if barras:
            n_partidos = max([len(getattr(t, "x", []) or []) for t in barras] or [1])
        total_barras = max(n_trazas * n_partidos, 1)

        # Ajuste dinámico de tamaño para evitar textos ilegibles con muchas barras.
        size_label = max(12, min(20, int(21 - (0.25 * total_barras))))
        size_title = max(24, min(32, int(34 - (0.2 * n_trazas))))
        size_axis = max(16, min(22, int(24 - (0.18 * n_trazas))))
        size_ticks = max(12, min(18, int(19 - (0.15 * n_trazas))))
        size_legend = max(10, min(15, int(16 - (0.18 * n_trazas))))

        # Incrementar legibilidad para el PDF sin alterar la vista en pantalla.
        for trace in barras:
            if getattr(trace, "type", None) == "bar":
                trace.textfont = dict(size=size_label, color="black")
                trace.texttemplate = "V=%{y:.1f}<br>Min=%{customdata[1]:.0f}'"
                trace.textposition = "outside"
                trace.cliponaxis = False

        fig_pdf.update_layout(
            title_font=dict(size=size_title),
            xaxis_title_font=dict(size=size_axis),
            yaxis_title_font=dict(size=size_axis),
            xaxis=dict(tickfont=dict(size=size_ticks)),
            yaxis=dict(tickfont=dict(size=size_ticks)),
            legend=dict(font=dict(size=size_legend)),
            margin=dict(t=125, l=95, r=40, b=120),
            uniformtext=dict(minsize=size_label, mode="show"),
        )

        png_bytes = fig_pdf.to_image(format="png", width=1800, height=1050, scale=2)
    except Exception:
        return None

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
        tmp_file.write(png_bytes)
        return tmp_file.name


def _calcular_resumen_tendencia(df_grafico):
    resumen = []
    if df_grafico is None or df_grafico.empty:
        return resumen

    for nombre in df_grafico["nombre"].unique():
        serie_df = df_grafico[df_grafico["nombre"] == nombre].sort_values("fecha")
        y_vals = serie_df["valor"].astype(float).to_numpy()
        if len(y_vals) < 2:
            continue
        x_idx = np.arange(len(y_vals))
        coef = np.polyfit(x_idx, y_vals, 1)
        pendiente = float(coef[0])
        delta_pct = ((y_vals[-1] - y_vals[0]) / y_vals[0] * 100) if y_vals[0] != 0 else np.nan
        if pendiente > 0:
            lectura = "SUBE"
            semaforo = "VERDE"
        elif pendiente < 0:
            lectura = "BAJA"
            semaforo = "ROJO"
        else:
            lectura = "ESTABLE"
            semaforo = "AMARILLO"
        resumen.append({
            "Serie": str(nombre),
            "Semaforo": semaforo,
            "Lectura": lectura,
            "Pendiente": round(pendiente, 3),
            "CambioPct": round(float(delta_pct), 2) if not np.isnan(delta_pct) else np.nan,
        })
    return resumen


def _dibujar_tabla_tendencia(pdf, resumen_tendencia):
    if not resumen_tendencia:
        return

    # Evitar tablas excesivamente largas
    max_rows = 12
    resumen = resumen_tendencia[:max_rows]

    if pdf.get_y() > 235:
        pdf.add_page()

    pdf.ln(2)
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(*pdf.COLOR_AZUL)
    pdf.cell(0, 7, "Semaforo de tendencia", 0, 1)

    # Forzar estilo de tabla (evita heredar bordes gruesos de otros bloques).
    pdf.set_draw_color(200, 205, 210)
    pdf.set_line_width(0.2)

    headers = ["Serie", "Semaforo", "Lectura", "Pendiente", "Cambio %"]
    widths = [64, 30, 30, 30, 30]
    row_h = 6

    if pdf.get_y() + (row_h * (len(resumen) + 2)) > 270:
        pdf.add_page()
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(*pdf.COLOR_AZUL)
        pdf.cell(0, 7, "Semaforo de tendencia", 0, 1)

    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(50, 50, 50)
    for h, w in zip(headers, widths):
        pdf.cell(w, row_h, h, 1, 0, "C")
    pdf.ln(row_h)

    for row in resumen:
        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(widths[0], row_h, str(row["Serie"])[:26], 1, 0, "L")

        if row["Semaforo"] == "VERDE":
            pdf.set_text_color(22, 163, 74)
        elif row["Semaforo"] == "ROJO":
            pdf.set_text_color(220, 38, 38)
        else:
            pdf.set_text_color(202, 138, 4)
        pdf.cell(widths[1], row_h, row["Semaforo"], 1, 0, "C")

        pdf.set_text_color(40, 40, 40)
        pdf.cell(widths[2], row_h, row["Lectura"], 1, 0, "C")
        pdf.cell(widths[3], row_h, f"{row['Pendiente']:.3f}", 1, 0, "C")

        cambio = row["CambioPct"]
        cambio_txt = "-" if pd.isna(cambio) else f"{cambio:.2f}%"
        pdf.cell(widths[4], row_h, cambio_txt, 1, 1, "C")

    if len(resumen_tendencia) > max_rows:
        pdf.set_font("Arial", "I", 8)
        pdf.set_text_color(120, 120, 120)
        pdf.cell(0, 5, f"Mostrando {max_rows} series de {len(resumen_tendencia)}", 0, 1, "R")


def _escribir_texto_largo(pdf, texto, alto_linea=6):
    pdf.set_x(15)
    pdf.multi_cell(180, alto_linea, texto)


def _dividir_texto(pdf, texto, ancho_max):
    lineas = []
    for parrafo in str(texto).splitlines():
        if not parrafo.strip():
            lineas.append("")
            continue
        palabras = parrafo.split(" ")
        actual = ""
        for palabra in palabras:
            # Si una palabra supera el ancho, partirla en bloques que entren.
            if pdf.get_string_width(palabra) > ancho_max:
                if actual:
                    lineas.append(actual)
                    actual = ""
                bloque = ""
                for ch in palabra:
                    if pdf.get_string_width(bloque + ch) <= ancho_max:
                        bloque += ch
                    else:
                        if bloque:
                            lineas.append(bloque)
                        bloque = ch
                if bloque:
                    lineas.append(bloque)
                continue

            intento = palabra if not actual else f"{actual} {palabra}"
            if pdf.get_string_width(intento) <= ancho_max:
                actual = intento
            else:
                if actual:
                    lineas.append(actual)
                actual = palabra
        if actual:
            lineas.append(actual)
    return lineas


def _dibujar_caja_comentarios(pdf, comentario):
    y_inicio = pdf.get_y() + 2
    x_caja = 15
    ancho_caja = 180
    y_fin = 265  # deja aire para footer
    alto_caja = max(30, y_fin - y_inicio)

    # Caja gris
    pdf.set_fill_color(242, 243, 245)
    pdf.set_draw_color(210, 213, 218)
    pdf.set_line_width(0.4)
    pdf.rect(x_caja, y_inicio, ancho_caja, alto_caja, "DF")

    # Texto de comentarios dentro de la caja
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(55, 55, 55)

    pad = 4
    ancho_texto = ancho_caja - (pad * 2)
    alto_linea = 5
    max_lineas = max(1, int((alto_caja - (pad * 2)) / alto_linea))
    lineas = _dividir_texto(pdf, comentario, ancho_texto)

    if len(lineas) > max_lineas:
        lineas = lineas[:max_lineas]
        if lineas:
            if len(lineas[-1]) > 3:
                lineas[-1] = lineas[-1][:-3] + "..."
            else:
                lineas[-1] = "..."

    pdf.set_xy(x_caja + pad, y_inicio + pad)
    for linea in lineas:
        pdf.set_x(x_caja + pad)
        pdf.cell(ancho_texto, alto_linea, linea, 0, 1)

    pdf.set_y(y_inicio + alto_caja + 2)


def _draw_card_small(pdf, x, y, titulo, contenido_lista):
    """Tarjeta de métrica estilo informe individual."""
    pdf.set_draw_color(*pdf.COLOR_AZUL)
    pdf.set_line_width(0.5)
    ancho = 45
    altura = 35
    pdf.rect(x, y, ancho, altura)

    pdf.set_font("Arial", "B", 9)
    pdf.set_text_color(*pdf.COLOR_AZUL)
    pdf.set_xy(x + 2, y + 3)
    pdf.cell(ancho - 4, 6, titulo[:24], 0, 1, "C")

    pdf.set_font("Arial", "", 8)
    pdf.set_text_color(60, 60, 60)
    num_lineas = min(len(contenido_lista), 4)
    altura_linea = 4.5
    altura_total = num_lineas * altura_linea
    espacio_disponible = altura - 10
    pad_top = max(0, (espacio_disponible - altura_total) / 2)
    y_ini = y + 10 + pad_top

    for idx, linea in enumerate(contenido_lista[:4]):
        pdf.set_xy(x + 2, y_ini + (idx * altura_linea))
        pdf.cell(ancho - 4, altura_linea, str(linea)[:24], 0, 0, "L")


def _draw_info_card(pdf, y, titulo, contenido_lista):
    pdf.set_y(y)
    pdf.set_draw_color(*pdf.COLOR_AZUL)
    pdf.set_line_width(0.5)
    altura = 10 + (len(contenido_lista) * 7)
    pdf.rect(10, y, 190, altura)

    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*pdf.COLOR_AZUL)
    pdf.set_xy(15, y + 3)
    pdf.cell(0, 7, titulo, 0, 1)

    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(60, 60, 60)
    for linea in contenido_lista:
        pdf.set_x(15)
        pdf.cell(0, 6, str(linea)[:95], 0, 1)

    pdf.set_y(y + altura + 3)


def _draw_info_card_detalle(pdf, y, posicion, n_metricas, minutos_max, minutos_prom, minutos_min):
    """Tarjeta de información general con bloque de minutos a la derecha."""
    pdf.set_y(y)
    pdf.set_draw_color(*pdf.COLOR_AZUL)
    pdf.set_line_width(0.5)
    altura = 32
    x = 10
    w = 190
    pdf.rect(x, y, w, altura)

    # Separador vertical para bloque derecho de minutos.
    x_sep = x + 132
    pdf.line(x_sep, y, x_sep, y + altura)

    # Título bloque izquierdo.
    pdf.set_font("Arial", "B", 12)
    pdf.set_text_color(*pdf.COLOR_AZUL)
    pdf.set_xy(x + 5, y + 3)
    pdf.cell(120, 7, "Informacion General", 0, 1, "L")

    # Contenido izquierdo.
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.set_xy(x + 5, y + 11)
    pdf.cell(120, 6, f"Posicion: {posicion}", 0, 1, "L")
    pdf.set_x(x + 5)
    pdf.cell(120, 6, f"Metricas incluidas: {n_metricas}", 0, 1, "L")
    pdf.set_x(x + 5)
    pdf.cell(120, 6, "Informe de detalle individual dentro del reporte de equipo", 0, 1, "L")

    # Bloque derecho (minutos).
    pdf.set_font("Arial", "B", 10)
    pdf.set_text_color(*pdf.COLOR_AZUL)
    pdf.set_xy(x_sep + 4, y + 4)
    pdf.cell(50, 6, "Minutos", 0, 1, "L")

    def fmt(v):
        return "-" if pd.isna(v) else f"{v:.1f}'"

    pdf.set_font("Arial", "", 9)
    pdf.set_text_color(50, 50, 50)
    pdf.set_x(x_sep + 4)
    pdf.cell(50, 5, f"Max: {fmt(minutos_max)}", 0, 1, "L")
    pdf.set_x(x_sep + 4)
    pdf.cell(50, 5, f"Prom: {fmt(minutos_prom)}", 0, 1, "L")
    pdf.set_x(x_sep + 4)
    pdf.cell(50, 5, f"Min: {fmt(minutos_min)}", 0, 1, "L")

    pdf.set_y(y + altura + 3)


def _agregar_detalle_individual(pdf, detalles_jugadores):
    """Bloque final por jugador, con foto y tarjetas como el informe individual."""
    if not detalles_jugadores:
        return

    for jugador_data in detalles_jugadores:
        nombre = jugador_data.get("jugador", "Jugador")
        posicion = jugador_data.get("posicion", "Sin posición")
        foto_path = jugador_data.get("foto_path")
        minutos_max = jugador_data.get("minutos_max", np.nan)
        minutos_prom = jugador_data.get("minutos_prom", np.nan)
        minutos_min = jugador_data.get("minutos_min", np.nan)
        tarjetas = jugador_data.get("tarjetas", [])
        if not tarjetas:
            continue

        pdf.add_page()

        # Título jugador
        pdf.set_font("Arial", "B", 20)
        pdf.set_text_color(*pdf.COLOR_AZUL)
        pdf.cell(0, 15, nombre, 0, 1, "C")
        pdf.ln(3)

        # Foto centrada
        if foto_path and os.path.exists(foto_path):
            try:
                pdf.image(foto_path, x=80, y=pdf.get_y(), h=50)
                pdf.ln(55)
            except Exception:
                pdf.ln(6)

        # Tarjeta de información general
        _draw_info_card_detalle(
            pdf,
            pdf.get_y(),
            posicion=posicion,
            n_metricas=len(tarjetas),
            minutos_max=minutos_max,
            minutos_prom=minutos_prom,
            minutos_min=minutos_min,
        )

        # Tarjetas por métrica en grid de 4 columnas
        metricas_por_fila = 4
        y_base = pdf.get_y()
        for idx, tarjeta in enumerate(tarjetas):
            col = idx % metricas_por_fila
            row = idx // metricas_por_fila
            x = 10 + (col * 47.5)
            y = y_base + (row * 40)

            # Si no cabe otra fila, abrir nueva página y continuar.
            if y + 38 > 270:
                pdf.add_page()
                y_base = pdf.get_y()
                row = 0
                y = y_base

            _draw_card_small(
                pdf,
                x,
                y,
                tarjeta.get("metrica", "Metrica"),
                tarjeta.get("lineas", []),
            )

        filas = (len(tarjetas) + metricas_por_fila - 1) // metricas_por_fila
        pdf.set_y(min(270, y_base + (filas * 40) + 4))


def generar_pdf_equipo(
    metricas_pdf,
    estadistico,
    nivel_analisis,
    filtro_texto,
    alcance_texto,
    comentario,
    detalles_jugadores=None,
):
    """
    Genera informe PDF de análisis de equipo.

    metricas_pdf: lista de dicts con claves:
      - metrica_nombre
      - df_grafico
    """
    pdf = PDFEquipo()

    # Portada (estilo corporativo)
    pdf.add_page()

    # Fondo blanco
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(0, 0, 210, 297, "F")

    # Línea vertical azul a la izquierda
    pdf.set_draw_color(*pdf.COLOR_AZUL)
    pdf.set_line_width(3)
    pdf.line(40, 20, 40, 277)

    # Escudo arriba a la izquierda
    escudo_path = obtener_escudo_path()
    if os.path.exists(escudo_path):
        pdf.image(escudo_path, x=10, y=20, w=25)

    # Nombre en parte inferior izquierda
    pdf.set_xy(10, 260)
    pdf.set_font("Arial", "I", 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(30, 10, "Alex Bosch", 0, 0, "L")

    # Bloque de título a la derecha de la línea
    pdf.set_xy(50, 130)
    pdf.set_font("Arial", "B", 28)
    pdf.set_text_color(*pdf.COLOR_AZUL)
    pdf.multi_cell(150, 12, "Informe de Equipo", 0, "C")

    pdf.set_xy(50, pdf.get_y() + 10)
    pdf.set_font("Arial", "", 12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(150, 10, "Europa FC - Analisis GPS", 0, 1, "C")

    pdf.set_xy(50, pdf.get_y() + 2)
    pdf.set_font("Arial", "I", 11)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(150, 8, datetime.now().strftime("%d/%m/%Y %H:%M"), 0, 1, "C")

    # Resumen
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(*pdf.COLOR_AZUL)
    pdf.cell(0, 10, "Configuracion del informe", 0, 1)

    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(50, 50, 50)
    _escribir_texto_largo(pdf, f"Nivel de analisis: {nivel_analisis}")
    _escribir_texto_largo(pdf, f"Estadistico: {estadistico}")
    _escribir_texto_largo(pdf, f"Filtro de partidos: {filtro_texto}")
    _escribir_texto_largo(pdf, f"Alcance: {alcance_texto}")
    _escribir_texto_largo(
        pdf,
        "Metricas incluidas: " + ", ".join([m["metrica_nombre"] for m in metricas_pdf]),
    )
    if detalles_jugadores:
        _escribir_texto_largo(
            pdf,
            f"Detalle individual incluido: {len(detalles_jugadores)} jugador(es)",
        )

    if comentario and comentario.strip():
        pdf.ln(2)
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(*pdf.COLOR_AZUL)
        pdf.cell(0, 8, "Comentarios", 0, 1)
        _dibujar_caja_comentarios(pdf, comentario.strip())

    # Pagina por metrica
    for metrica_data in metricas_pdf:
        metrica_nombre = metrica_data["metrica_nombre"]
        df_grafico = metrica_data["df_grafico"]
        plotly_fig = metrica_data.get("plotly_fig")
        mostrar_tendencia = bool(metrica_data.get("mostrar_tendencia", False))
        if df_grafico is None or df_grafico.empty:
            continue

        png_path = _crear_png_desde_plotly(plotly_fig) if plotly_fig is not None else None
        if not png_path:
            png_path = _crear_grafico_png(
                df_grafico,
                metrica_nombre,
                estadistico,
                nivel_analisis,
                mostrar_tendencia=mostrar_tendencia,
            )
        if not png_path:
            continue

        pdf.add_page()
        pdf.set_font("Arial", "B", 15)
        pdf.set_text_color(*pdf.COLOR_AZUL)
        pdf.cell(0, 10, f"Metrica: {metrica_nombre}", 0, 1)

        pdf.set_font("Arial", "", 10)
        pdf.set_text_color(70, 70, 70)
        pdf.cell(0, 6, "La etiqueta de minutos se marca en rojo cuando Min < 60.", 0, 1)
        pdf.ln(2)

        pdf.image(png_path, x=10, y=pdf.get_y(), w=190)
        os.unlink(png_path)

        pdf.ln(106)
        pdf.set_font("Arial", "B", 10)
        pdf.set_text_color(*pdf.COLOR_AZUL)
        pdf.cell(0, 7, "Resumen rapido", 0, 1)

        pdf.set_font("Arial", "", 9)
        pdf.set_text_color(60, 60, 60)
        media = float(df_grafico["valor"].mean())
        maximo = float(df_grafico["valor"].max())
        minimo = float(df_grafico["valor"].min())
        min_media = float(df_grafico["minutaje"].mean())
        _escribir_texto_largo(
            pdf,
            (
                f"Valor medio: {media:.2f} | Maximo: {maximo:.2f} | Minimo: {minimo:.2f} | "
                f"Minutos medios: {min_media:.1f}"
            ),
            alto_linea=5,
        )
        if mostrar_tendencia:
            resumen_tendencia = _calcular_resumen_tendencia(df_grafico)
            _dibujar_tabla_tendencia(pdf, resumen_tendencia)

    # Bloque final opcional con tarjetas por jugador.
    _agregar_detalle_individual(pdf, detalles_jugadores or [])

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(__file__).parent.parent / "informes_pdf"
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"Informe_Equipo_{timestamp}.pdf"
    pdf.output(str(output_path))
    return str(output_path)
