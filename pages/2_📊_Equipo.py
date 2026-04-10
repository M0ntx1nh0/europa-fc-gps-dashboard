"""
Página: Análisis de Equipo
Vista general y comparativa del rendimiento
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import re
import unicodedata
import sys
from pathlib import Path

# Añadir directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from config import PAGE_TITLE, PAGE_ICON, LAYOUT, COLORES, METRICAS_DICT
from utils import (
    render_sidebar,
    cargar_plantilla_europa,
    mapear_posicion,
    obtener_foto_jugador
)
from utils.filtros import render_filtro_partidos
from utils.pdf_equipo import generar_pdf_equipo
from utils.minutaje_labels import (
    obtener_label_minutos,
    obtener_umbral_minutos,
    usar_etiqueta_compacta,
)

# Configuración
st.set_page_config(
    page_title=f"{PAGE_TITLE} - Equipo",
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="collapsed"
)

def main():
    # ==========================================
    # AUTENTICACIÓN
    # ==========================================
    if not st.session_state.get('autenticado', False):
        st.warning("⚠️ Por favor, inicia sesión desde la página principal")
        st.stop()
    
    # ==========================================
    # SIDEBAR
    # ==========================================
    render_sidebar()
    
    st.title("📊 Análisis de Equipo")
    
    # ==========================================
    # VERIFICAR DATOS
    # ==========================================
    if not st.session_state.get('datos_cargados', False):
        st.warning("⚠️ No hay datos cargados")
        st.stop()
    
    df = st.session_state.get('df_procesado')
    if df is None or len(df) == 0:
        st.error("⚠️ Error: datos no disponibles")
        st.stop()
    
    # ========================================
    # FILTRO DE PARTIDOS
    # ========================================
    df_filtrado, modo_partido, info_filtro = render_filtro_partidos(df, titulo="🎯 Filtros de Partido")
    
    st.markdown("---")
    
    # ========================================
    # CONFIGURACIÓN DEL ANÁLISIS
    # ========================================
    st.markdown("## ⚙️ Configuración del Análisis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        nivel_analisis = st.selectbox(
            "📊 Nivel de análisis:",
            options=['Equipo', 'Por posiciones', 'Individual'],
            key='nivel_analisis',
            help="Equipo: Promedio del equipo por partido\nPor posiciones: Comparar posiciones\nIndividual: Comparar jugadores"
        )
    
    with col2:
        # Métricas disponibles
        metricas_disponibles = {k: v for k, v in METRICAS_DICT.items() if v in df_filtrado.columns}
        
        if len(metricas_disponibles) == 0:
            st.error("❌ No hay métricas disponibles")
            st.stop()
        
        metrica_nombre = st.selectbox(
            "📈 Métrica:",
            options=list(metricas_disponibles.keys()),
            key='metrica_analisis'
        )
        metrica_col = METRICAS_DICT[metrica_nombre]
    
    with col3:
        opciones_estadistico = ['Media', 'Máximo', 'P70', 'P95']
        if nivel_analisis in ['Equipo', 'Por posiciones']:
            opciones_estadistico = ['Media', 'Máximo', 'P70', 'P95', 'Sumatorio']

        estadistico = st.selectbox(
            "📊 Estadístico:",
            options=opciones_estadistico,
            key='estadistico_analisis',
            help="Media: Promedio\nMáximo: Valor más alto\nP70/P95: Percentiles"
        )

    mostrar_tendencia_lineal = st.checkbox(
        "Mostrar línea de tendencia lineal",
        value=True,
        key="mostrar_tendencia_equipo",
        help="Añade una línea discontinua para facilitar la lectura (sube, baja o estable)."
    )

    filtro_parte = st.selectbox(
        "⏱️ Tramo de partido:",
        options=[
            "Total",
            "1ª Parte",
            "2ª Parte",
            "1ª + 2ª (Conjunto)",
            "1ª + 2ª (Separadas)",
        ],
        key="filtro_parte_analisis",
        help="Total, cada parte por separado o ambas mitades juntas."
    )

    st.markdown("---")
    
    # ========================================
    # SELECCIÓN ESPECÍFICA SEGÚN NIVEL
    # ========================================
    
    # Limpiar datos inválidos
    df_limpio = df_filtrado.copy()
    df_limpio = df_limpio[df_limpio['player'].notna()]
    df_limpio = df_limpio[df_limpio['player'].astype(str).str.strip() != '']
    df_limpio = df_limpio[df_limpio['player'].astype(str) != '0']
    df_limpio_base = df_limpio.copy()

    # Clasificar tramo por task/session para habilitar filtro de 1ª/2ª parte.
    def normalizar_texto(valor):
        txt = str(valor or "").strip().lower()
        txt = unicodedata.normalize("NFKD", txt)
        txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
        txt = re.sub(r"[^a-z0-9]+", " ", txt)
        return txt.strip()

    def clasificar_tramo(row):
        task_txt = normalizar_texto(row.get('task', ''))
        session_txt = normalizar_texto(row.get('session', ''))
        txt = f"{task_txt} {session_txt}"
        txt_compacto = txt.replace(" ", "")
        if 'total' in txt:
            return 'Total'
        if any(token in txt_compacto for token in ["total", "complet", "completo", "fullmatch"]):
            return 'Total'

        tiene_token_parte = re.search(
            r"\b(parte|part|periodo|period|half|mitad|temps|tiempo)\b", txt
        ) is not None
        es_primera = re.search(
            r"\b(1|1a|1r|p1|periodo 1|period 1|primera|primer|first)\b", txt
        ) is not None
        es_segunda = re.search(
            r"\b(2|2a|2n|p2|periodo 2|period 2|segunda|segundo|second)\b", txt
        ) is not None
        primera_compacta = any(
            token in txt_compacto
            for token in [
                "1apart", "part1", "parte1", "periodo1", "period1", "half1", "mitad1",
                "primertemps", "primerapart", "firsthalf", "p1"
            ]
        )
        segunda_compacta = any(
            token in txt_compacto
            for token in [
                "2apart", "part2", "parte2", "periodo2", "period2", "half2", "mitad2",
                "segontemps", "segundapart", "secondhalf", "p2"
            ]
        )

        # Ejemplos: "1A PART", "1ª PARTE", "Periodo 1", "P1", "First half"
        if (es_primera and tiene_token_parte) or primera_compacta:
            return '1ª Parte'
        # Ejemplos: "2A PART", "2ª PARTE", "Periodo 2", "P2", "Second half"
        if (es_segunda and tiene_token_parte) or segunda_compacta:
            return '2ª Parte'
        return 'Total'

    df_limpio['tramo_partido'] = df_limpio.apply(clasificar_tramo, axis=1)

    # Aplicar filtro de tramo.
    if filtro_parte == "Total":
        df_limpio = df_limpio[df_limpio['tramo_partido'] == 'Total']
        if len(df_limpio) == 0:
            # Fallback: si los datos no traen task='Total', usar todo el dataset filtrado.
            df_limpio = df_limpio_base.copy()
    elif filtro_parte == "1ª Parte":
        df_limpio = df_limpio[df_limpio['tramo_partido'] == '1ª Parte']
    elif filtro_parte == "2ª Parte":
        df_limpio = df_limpio[df_limpio['tramo_partido'] == '2ª Parte']
    elif filtro_parte == "1ª + 2ª (Conjunto)":
        df_limpio = df_limpio[df_limpio['tramo_partido'].isin(['1ª Parte', '2ª Parte'])].copy()
        df_limpio['tramo_partido'] = '1ª + 2ª'
    else:  # "1ª + 2ª (Separadas)"
        df_limpio = df_limpio[df_limpio['tramo_partido'].isin(['1ª Parte', '2ª Parte'])]

    if len(df_limpio) == 0:
        st.warning("⚠️ No hay datos para el tramo de partido seleccionado.")
        st.stop()
    df_tramo = df_limpio.copy()
    posiciones_seleccionadas = []
    jugadores_seleccionados = []
    df_plantilla_cache = None

    def obtener_df_con_posiciones(df_input):
        nonlocal df_plantilla_cache
        if 'posicion' in df_input.columns:
            return df_input.copy()
        try:
            if df_plantilla_cache is None:
                df_plantilla_cache = cargar_plantilla_europa()
            df_out = df_input.copy()
            df_out['posicion'] = df_out['player'].apply(
                lambda x: mapear_posicion(str(x), df_plantilla_cache)
                if pd.notna(x) and str(x).strip() != '' else 'Sin posición'
            )
            return df_out
        except Exception:
            st.error("⚠️ No se pudo cargar información de posiciones")
            st.stop()
    
    if nivel_analisis == 'Por posiciones':
        st.markdown("### 🎯 Seleccionar Posiciones")
        
        # Cargar plantilla para mapear posiciones
        df_limpio = obtener_df_con_posiciones(df_limpio)
        
        posiciones_seleccionadas = st.multiselect(
            "Selecciona posiciones:",
            options=['Defensa', 'Centrocampista', 'Delantero'],
            default=['Defensa', 'Centrocampista', 'Delantero'],
            key='posiciones_seleccionadas'
        )
        
        if len(posiciones_seleccionadas) == 0:
            st.warning("⚠️ Selecciona al menos una posición")
            st.stop()
        
        df_limpio = df_limpio[df_limpio['posicion'].isin(posiciones_seleccionadas)]
        
        if len(df_limpio) == 0:
            st.warning("⚠️ No hay datos para las posiciones seleccionadas")
            st.stop()
    
    elif nivel_analisis == 'Individual':
        st.markdown("### 👤 Seleccionar Jugadores")
        
        jugadores_disponibles = sorted(df_limpio['player'].unique())
        
        jugadores_seleccionados = st.multiselect(
            "Selecciona jugadores:",
            options=jugadores_disponibles,
            default=jugadores_disponibles[:min(3, len(jugadores_disponibles))],
            key='jugadores_seleccionados',
            help="Selecciona 1 o más jugadores para comparar"
        )
        
        if len(jugadores_seleccionados) == 0:
            st.warning("⚠️ Selecciona al menos un jugador")
            st.stop()
        
        df_limpio = df_limpio[df_limpio['player'].isin(jugadores_seleccionados)]
    
    st.markdown("---")
    
    # ========================================
    # PREPARAR DATOS PARA EL GRÁFICO
    # ========================================
    
    # Función auxiliar para calcular estadístico
    def calcular_estadistico(valores, tipo):
        if tipo == 'Media':
            return valores.mean()
        elif tipo == 'Máximo':
            return valores.max()
        elif tipo == 'P70':
            return valores.quantile(0.70)
        elif tipo == 'P95':
            return valores.quantile(0.95)
        elif tipo == 'Sumatorio':
            return valores.sum()
        return valores.mean()
    
    def aplicar_filtro_minutos(df_in, nivel_analisis_local):
        # Regla >60' solo para vista TOTAL en Equipo/Posiciones.
        # En mitades, aplicar >60' vacía el resultado (minutos por tramo suelen ser <60).
        if nivel_analisis_local in ['Equipo', 'Por posiciones'] and filtro_parte == "Total":
            return df_in[df_in['time'] > 60]
        return df_in

    def construir_datos_grafico(
        metrica_objetivo,
        nivel_analisis_local=None,
        df_base_local=None,
        posiciones_sel=None,
        jugadores_sel=None,
    ):
        nivel_local = nivel_analisis_local or nivel_analisis
        df_base = df_base_local.copy() if df_base_local is not None else df_limpio.copy()
        posiciones_sel = posiciones_sel if posiciones_sel is not None else posiciones_seleccionadas
        jugadores_sel = jugadores_sel if jugadores_sel is not None else jugadores_seleccionados
        fechas_disponibles_local = sorted(df_base['date'].unique())
        datos = []

        if nivel_local == 'Equipo':
            # Una barra por partido (estadístico del equipo completo)
            for fecha in fechas_disponibles_local:
                df_fecha_base = df_base[df_base['date'] == fecha]
                subgrupos = [("general", df_fecha_base)]
                if filtro_parte == "1ª + 2ª (Separadas)" and 'tramo_partido' in df_fecha_base.columns:
                    subgrupos = list(df_fecha_base.groupby('tramo_partido'))

                for tramo_key, df_fecha in subgrupos:
                    df_fecha = aplicar_filtro_minutos(df_fecha, nivel_local)
                    if len(df_fecha) == 0:
                        continue

                    valor = calcular_estadistico(df_fecha[metrica_objetivo], estadistico)
                    minutaje_promedio = df_fecha['time'].mean()
                    nombre_serie = 'Equipo'
                    if filtro_parte == "1ª + 2ª (Separadas)":
                        nombre_serie = f"Equipo - {tramo_key}"

                    datos.append({
                        'fecha': fecha,
                        'nombre': nombre_serie,
                        'valor': valor,
                        'minutaje': minutaje_promedio,
                        'color': COLORES['primario'],
                        'grupo': nombre_serie
                    })

        elif nivel_local == 'Por posiciones':
            colores_posicion = {
                'Defensa': '#ef4444',
                'Centrocampista': '#3b82f6',
                'Delantero': '#22c55e'
            }

            colores_individuales = ['#1E88E5', '#FF6F00', '#43A047', '#E53935', '#8E24AA', '#00ACC1']

            if len(posiciones_sel) == 1:
                # UNA SOLA POSICIÓN: barras por jugador
                jugadores_posicion = sorted(df_base['player'].unique())

                for idx, jugador in enumerate(jugadores_posicion):
                    for fecha in fechas_disponibles_local:
                        df_jug_fecha_base = df_base[
                            (df_base['player'] == jugador) &
                            (df_base['date'] == fecha)
                        ]
                        subgrupos = [("general", df_jug_fecha_base)]
                        if filtro_parte == "1ª + 2ª (Separadas)" and 'tramo_partido' in df_jug_fecha_base.columns:
                            subgrupos = list(df_jug_fecha_base.groupby('tramo_partido'))

                        for tramo_key, df_jug_fecha in subgrupos:
                            df_jug_fecha = aplicar_filtro_minutos(df_jug_fecha, nivel_local)
                            if len(df_jug_fecha) == 0:
                                continue
                            valor = calcular_estadistico(df_jug_fecha[metrica_objetivo], estadistico)
                            minutaje = df_jug_fecha['time'].mean()
                            nombre_serie = jugador
                            if filtro_parte == "1ª + 2ª (Separadas)":
                                nombre_serie = f"{jugador} - {tramo_key}"

                            datos.append({
                                'fecha': fecha,
                                'nombre': nombre_serie,
                                'valor': valor,
                                'minutaje': minutaje,
                                'color': colores_individuales[idx % len(colores_individuales)],
                                'grupo': nombre_serie
                            })
            else:
                # MÚLTIPLES POSICIONES: barras por posición
                for posicion in posiciones_sel:
                    for fecha in fechas_disponibles_local:
                        df_pos_fecha_base = df_base[
                            (df_base['posicion'] == posicion) &
                            (df_base['date'] == fecha)
                        ]
                        subgrupos = [("general", df_pos_fecha_base)]
                        if filtro_parte == "1ª + 2ª (Separadas)" and 'tramo_partido' in df_pos_fecha_base.columns:
                            subgrupos = list(df_pos_fecha_base.groupby('tramo_partido'))

                        for tramo_key, df_pos_fecha in subgrupos:
                            df_pos_fecha = aplicar_filtro_minutos(df_pos_fecha, nivel_local)
                            if len(df_pos_fecha) == 0:
                                continue
                            valor = calcular_estadistico(df_pos_fecha[metrica_objetivo], estadistico)
                            minutaje_promedio = df_pos_fecha['time'].mean()
                            nombre_serie = posicion
                            if filtro_parte == "1ª + 2ª (Separadas)":
                                nombre_serie = f"{posicion} - {tramo_key}"

                            datos.append({
                                'fecha': fecha,
                                'nombre': nombre_serie,
                                'valor': valor,
                                'minutaje': minutaje_promedio,
                                'color': colores_posicion[posicion],
                                'grupo': nombre_serie
                            })

        else:  # Individual
            colores_individuales = ['#1E88E5', '#FF6F00', '#43A047', '#E53935', '#8E24AA', '#00ACC1']

            for idx, jugador in enumerate(jugadores_sel):
                for fecha in fechas_disponibles_local:
                    df_jug_fecha_base = df_base[
                        (df_base['player'] == jugador) &
                        (df_base['date'] == fecha)
                    ]
                    subgrupos = [("general", df_jug_fecha_base)]
                    if filtro_parte == "1ª + 2ª (Separadas)" and 'tramo_partido' in df_jug_fecha_base.columns:
                        subgrupos = list(df_jug_fecha_base.groupby('tramo_partido'))

                    for tramo_key, df_jug_fecha in subgrupos:
                        if len(df_jug_fecha) == 0:
                            continue
                        valor = calcular_estadistico(df_jug_fecha[metrica_objetivo], estadistico)
                        minutaje = df_jug_fecha['time'].mean()
                        nombre_serie = jugador
                        if filtro_parte == "1ª + 2ª (Separadas)":
                            nombre_serie = f"{jugador} - {tramo_key}"

                        datos.append({
                            'fecha': fecha,
                            'nombre': nombre_serie,
                            'valor': valor,
                            'minutaje': minutaje,
                            'color': colores_individuales[idx % len(colores_individuales)],
                            'grupo': nombre_serie
                        })

        return datos

    def preparar_df_grafico(datos):
        df_out = pd.DataFrame(datos)
        df_out['fecha'] = pd.to_datetime(df_out['fecha'])
        sesiones_por_fecha = (
            df_limpio[['date', 'session']]
            .dropna(subset=['date'])
            .assign(date=lambda x: pd.to_datetime(x['date']))
            .sort_values('date')
            .groupby('date', as_index=False)['session']
            .first()
        )
        mapa_sesion = {
            pd.to_datetime(row['date']): str(row['session']).strip()
            for _, row in sesiones_por_fecha.iterrows()
            if pd.notna(row['session']) and str(row['session']).strip() != ''
        }

        df_out['session_label'] = df_out['fecha'].map(mapa_sesion).fillna('')
        df_out['fecha_base'] = df_out['fecha'].dt.strftime('%d/%m')
        df_out['fecha_label'] = np.where(
            df_out['session_label'].str.strip() != '',
            df_out['session_label'] + ' - ' + df_out['fecha_base'],
            df_out['fecha_base']
        )
        df_out['fecha_full'] = np.where(
            df_out['session_label'].str.strip() != '',
            df_out['session_label'] + ' - ' + df_out['fecha'].dt.strftime('%d/%m/%Y'),
            df_out['fecha'].dt.strftime('%d/%m/%Y')
        )
        return df_out

    # Crear datos del gráfico para la métrica principal
    datos_grafico = construir_datos_grafico(metrica_col)
    
    if len(datos_grafico) == 0:
        st.warning("⚠️ No hay datos para mostrar con la configuración actual")
        st.stop()
    
    df_grafico = preparar_df_grafico(datos_grafico)
    
    def crear_figura_plotly(df_grafico_plot, metrica_nombre_plot, mostrar_tendencia=False):
        orden_fechas_plot = (
            df_grafico_plot[['fecha', 'fecha_label']]
            .drop_duplicates()
            .sort_values('fecha')
        )
        orden_labels_plot = orden_fechas_plot['fecha_label'].tolist()

        fig_plot = go.Figure()
        df_local = df_grafico_plot.copy()
        df_local["trend"] = np.nan

        def extraer_base_y_tramo(nombre_serie):
            partes = str(nombre_serie).rsplit(" - ", 1)
            if len(partes) == 2 and partes[1] in ["1ª Parte", "2ª Parte"]:
                return partes[0], partes[1]
            return str(nombre_serie), None

        # Orden descendente por valor y, en modo separadas, emparejar 1ª/2ª por entidad.
        if filtro_parte == "1ª + 2ª (Separadas)":
            df_orden = df_local.copy()
            df_orden[["base", "tramo"]] = df_orden["nombre"].apply(
                lambda n: pd.Series(extraer_base_y_tramo(n))
            )
            orden_base = (
                df_orden.groupby("base")["valor"]
                .mean()
                .sort_values(ascending=False)
                .index
                .tolist()
            )
            idx_base = {b: i for i, b in enumerate(orden_base)}
            idx_tramo = {"1ª Parte": 0, "2ª Parte": 1, None: 2}

            series_unicas = sorted(
                df_local["nombre"].unique().tolist(),
                key=lambda n: (
                    idx_base.get(extraer_base_y_tramo(n)[0], 999),
                    idx_tramo.get(extraer_base_y_tramo(n)[1], 2),
                ),
            )
            orden_series = series_unicas
        else:
            orden_series = (
                df_local.groupby('nombre')['valor']
                .mean()
                .sort_values(ascending=False)
                .index
                .tolist()
            )

        usar_compacto = usar_etiqueta_compacta(
            total_series=len(orden_series),
            total_fechas=len(orden_labels_plot),
            soporte="app",
        )
        total_barras = max(len(orden_series) * len(orden_labels_plot), 1)
        font_size_texto = max(9, min(12, int(13 - (total_barras * 0.22))))

        for nombre in orden_series:
            df_grupo = df_local[df_local['nombre'] == nombre].sort_values('fecha').copy()

            if mostrar_tendencia and len(df_grupo) >= 2:
                y_vals = df_grupo["valor"].astype(float).values
                x_idx = np.arange(len(df_grupo))
                coef = np.polyfit(x_idx, y_vals, 1)
                df_grupo["trend"] = coef[0] * x_idx + coef[1]

            label_minutos = obtener_label_minutos(
                nivel_analisis,
                filtro_parte,
                nombre_serie=nombre,
                compacto=usar_compacto,
            )
            label_minutos_hover = obtener_label_minutos(
                nivel_analisis,
                filtro_parte,
                nombre_serie=nombre,
                compacto=False,
            )
            umbral_minutos = obtener_umbral_minutos(filtro_parte, nombre_serie=nombre)
            texto_barras = [
                (
                    f"{metrica_nombre_plot}={row['valor']:.1f}<br>"
                    f"<span style='color:{'#d32f2f' if row['minutaje'] < umbral_minutos else '#111111'}'>"
                    f"{label_minutos}={int(row['minutaje'])}'</span>"
                )
                for _, row in df_grupo.iterrows()
            ]

            fig_plot.add_trace(go.Bar(
                x=df_grupo['fecha_label'],
                y=df_grupo['valor'],
                name=nombre,
                marker_color=df_grupo['color'].iloc[0],
                text=texto_barras,
                textposition='outside',
                textfont=dict(size=font_size_texto, color='black'),
                cliponaxis=False,
                hovertemplate=(
                    '<b>%{customdata[0]}</b><br>' +
                    f'{nombre}<br>' +
                    f'{metrica_nombre_plot}: %{{y:.1f}}<br>' +
                    f'{label_minutos_hover}: %{{customdata[1]:.0f}}\'<br>' +
                    '<extra></extra>'
                ),
                customdata=np.column_stack((
                    df_grupo['fecha_full'],
                    df_grupo['minutaje'].round(0)
                ))
            ))

            if mostrar_tendencia and df_grupo["trend"].notna().any():
                fig_plot.add_trace(go.Scatter(
                    x=df_grupo['fecha_label'],
                    y=df_grupo['trend'],
                    mode='lines',
                    name=f'{nombre} (tendencia)',
                    line=dict(color=df_grupo['color'].iloc[0], width=2, dash='dash'),
                    hovertemplate=(
                        '<b>%{x}</b><br>' +
                        f'{nombre} tendencia: %{{y:.1f}}<extra></extra>'
                    ),
                    showlegend=(nivel_analisis != 'Equipo')
                ))

        titulo_grafico_plot = f"{estadistico} de {metrica_nombre_plot} - {nivel_analisis}"
        valor_max_plot = float(df_grafico_plot['valor'].max())
        valor_min_plot = float(df_grafico_plot['valor'].min())
        margen_superior_plot = max(valor_max_plot * 0.12, 20.0)

        fig_plot.update_layout(
            title=titulo_grafico_plot,
            xaxis_title="Fecha del Partido",
            yaxis_title=f"{metrica_nombre_plot} ({estadistico})",
            height=600,
            barmode='group',
            bargap=0.45,
            bargroupgap=0.12,
            hovermode='x unified',
            margin=dict(t=95),
            xaxis=dict(
                type='category',
                categoryorder='array',
                categoryarray=orden_labels_plot,
                tickangle=-45
            ),
            yaxis=dict(
                range=[min(0, valor_min_plot), valor_max_plot + margen_superior_plot]
            ),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            showlegend=(nivel_analisis != 'Equipo')
        )
        return fig_plot
    
    # ========================================
    # GRÁFICO DE BARRAS
    # ========================================
    
    st.markdown(f"## 📊 {estadistico} de {metrica_nombre}")
    fig = crear_figura_plotly(df_grafico, metrica_nombre, mostrar_tendencia=mostrar_tendencia_lineal)
    
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("ℹ️ Cómo se interpretan las etiquetas de minutos"):
        st.markdown(
            """
            | Nivel de análisis | Tramo | Etiqueta mostrada | Qué representa |
            |---|---|---|---|
            | `Individual` | `Total` | `Min total` | Minutos reales del jugador en el partido completo. |
            | `Individual` | `1ª Parte` | `Min 1ª` | Minutos reales del jugador en la primera parte. |
            | `Individual` | `2ª Parte` | `Min 2ª` | Minutos reales del jugador en la segunda parte. |
            | `Individual` | `1ª + 2ª (Conjunto)` | `Min acum` | Minutos acumulados del jugador al unir ambas partes. |
            | `Individual` | `1ª + 2ª (Separadas)` | `Min 1ª` / `Min 2ª` | Minutos reales del jugador en cada tramo mostrado por separado. |
            | `Equipo` / `Por posiciones` | `Total` | `Min med` | Minutaje medio del grupo que entra en el cálculo. En `Total` solo cuentan jugadores con `time > 60`. |
            | `Equipo` / `Por posiciones` | `1ª Parte` | `Min med 1ª` | Minutaje medio del grupo en la primera parte, sin filtro de `>60`. |
            | `Equipo` / `Por posiciones` | `2ª Parte` | `Min med 2ª` | Minutaje medio del grupo en la segunda parte, sin filtro de `>60`. |
            | `Equipo` / `Por posiciones` | `1ª + 2ª (Conjunto)` | `Min med acum` | Minutaje medio del grupo al unir ambas partes, sin filtro de `>60`. |
            | `Equipo` / `Por posiciones` | `1ª + 2ª (Separadas)` | `Min med 1ª` / `Min med 2ª` | Minutaje medio del grupo en cada tramo mostrado por separado. |
            """
        )
        st.caption(
            "El color rojo marca un minutaje bajo para el tramo mostrado: umbral de 60' en `Total` y `1ª + 2ª (Conjunto)`, y 30' en `1ª Parte`, `2ª Parte` y `1ª + 2ª (Separadas)`."
        )
        st.caption(
            "Si el gráfico tiene muchas barras, la etiqueta visible se compacta para que siga siendo legible: `MT` = Min total, `M1ª` = Min 1ª, `M2ª` = Min 2ª, `MA` = Min acum, `MM` = Min med, `MM1ª` = Min med 1ª, `MM2ª` = Min med 2ª, `MMA` = Min med acum."
        )

    # Resumen de tendencia con semáforo
    resumen_tendencia = []
    for nombre in df_grafico['nombre'].unique():
        serie_df = df_grafico[df_grafico['nombre'] == nombre].sort_values('fecha')
        y_vals = serie_df['valor'].astype(float).values
        if len(y_vals) < 2:
            continue
        x_idx = np.arange(len(y_vals))
        coef = np.polyfit(x_idx, y_vals, 1)
        pendiente = float(coef[0])
        delta_pct = ((y_vals[-1] - y_vals[0]) / y_vals[0] * 100) if y_vals[0] != 0 else np.nan
        if pendiente > 0:
            lectura = "↑ Sube"
        elif pendiente < 0:
            lectura = "↓ Baja"
        else:
            lectura = "→ Estable"
        resumen_tendencia.append({
            "Serie": nombre,
            "Lectura": lectura,
            "Pendiente": round(pendiente, 3),
            "Cambio % periodo": round(float(delta_pct), 2) if not np.isnan(delta_pct) else np.nan,
        })

    if len(resumen_tendencia) > 0:
        if len(resumen_tendencia) == 1:
            st.info(f"📌 Lectura rápida: **{resumen_tendencia[0]['Serie']}** {resumen_tendencia[0]['Lectura']} en el periodo.")
        else:
            estados = ", ".join([f"{r['Serie']}: {r['Lectura']}" for r in resumen_tendencia])
            st.info(f"📌 Lectura rápida: {estados}.")

        st.markdown("### 📌 Resumen de tendencia")
        df_resumen = pd.DataFrame(resumen_tendencia)
        color_map = {"↑ Sube": "🟢", "↓ Baja": "🔴", "→ Estable": "🟡"}
        df_resumen["Semáforo"] = df_resumen["Lectura"].map(color_map).fillna("⚪")
        df_resumen = df_resumen[["Serie", "Semáforo", "Lectura", "Pendiente", "Cambio % periodo"]]

        def estilo_lectura(v):
            if v == "↑ Sube":
                return "color: #16a34a; font-weight: 700;"
            if v == "↓ Baja":
                return "color: #dc2626; font-weight: 700;"
            if v == "→ Estable":
                return "color: #ca8a04; font-weight: 700;"
            return ""

        st.dataframe(
            df_resumen.style.map(estilo_lectura, subset=["Lectura"]),
            use_container_width=True,
            hide_index=True
        )
    
    # ========================================
    # TABLA DE DATOS
    # ========================================
    
    with st.expander("📋 Ver tabla de datos"):
        df_tabla = df_grafico.copy()
        df_tabla['fecha'] = df_tabla['fecha'].dt.strftime('%d/%m/%Y')
        df_tabla['minutaje'] = df_tabla['minutaje'].round(0).astype(int)
        df_tabla['valor'] = df_tabla['valor'].round(1)
        
        df_tabla = df_tabla[['fecha', 'nombre', 'valor', 'minutaje']]
        df_tabla.columns = ['Fecha', 'Nombre', f'{metrica_nombre} ({estadistico})', 'Minutos']
        
        st.dataframe(
            df_tabla,
            use_container_width=True,
            hide_index=True
        )

    # ========================================
    # EXPORTACIÓN PDF
    # ========================================
    st.markdown("---")
    st.subheader("📄 Informe PDF")
    st.caption("El informe usa los filtros actuales de partidos y tramo. Aquí puedes decidir qué bloques incluir.")

    incluir_bloque_equipo_pdf = st.checkbox(
        "Incluir bloque Equipo",
        key="incluir_bloque_equipo_pdf",
        value=(nivel_analisis == "Equipo")
    )

    metricas_equipo_pdf = []
    if incluir_bloque_equipo_pdf:
        todas_metricas_equipo_pdf = st.checkbox(
            "Seleccionar todas las métricas del bloque Equipo",
            key="todas_metricas_equipo_pdf",
            value=False
        )
        if todas_metricas_equipo_pdf:
            metricas_equipo_pdf = list(metricas_disponibles.keys())
            st.caption(f"Bloque Equipo: se incluirán todas las métricas ({len(metricas_equipo_pdf)}).")
        else:
            metricas_equipo_pdf = st.multiselect(
                "Métricas del bloque Equipo:",
                options=list(metricas_disponibles.keys()),
                default=[metrica_nombre],
                key="metricas_equipo_pdf",
                help="Métricas que se incluirán en la sección de equipo."
            )

    incluir_bloque_posiciones_pdf = st.checkbox(
        "Incluir bloque Posiciones",
        key="incluir_bloque_posiciones_pdf",
        value=(nivel_analisis == "Por posiciones")
    )

    posiciones_pdf_seleccionadas = []
    metricas_posiciones_pdf = []
    if incluir_bloque_posiciones_pdf:
        df_posiciones_pdf = obtener_df_con_posiciones(df_tramo)
        opciones_posiciones_pdf = ['Defensa', 'Centrocampista', 'Delantero']
        posiciones_pdf_seleccionadas = st.multiselect(
            "Posiciones a incluir en el bloque Posiciones:",
            options=opciones_posiciones_pdf,
            default=posiciones_seleccionadas if posiciones_seleccionadas else opciones_posiciones_pdf,
            key="posiciones_pdf_seleccionadas"
        )
        todas_metricas_posiciones_pdf = st.checkbox(
            "Seleccionar todas las métricas del bloque Posiciones",
            key="todas_metricas_posiciones_pdf",
            value=False
        )
        if todas_metricas_posiciones_pdf:
            metricas_posiciones_pdf = list(metricas_disponibles.keys())
            st.caption(f"Bloque Posiciones: se incluirán todas las métricas ({len(metricas_posiciones_pdf)}).")
        else:
            metricas_posiciones_pdf = st.multiselect(
                "Métricas del bloque Posiciones:",
                options=list(metricas_disponibles.keys()),
                default=[metrica_nombre],
                key="metricas_posiciones_pdf"
            )

    incluir_bloque_individual_pdf = st.checkbox(
        "Incluir bloque Individual",
        key="incluir_bloque_individual_pdf",
        value=(nivel_analisis == "Individual")
    )

    jugadores_pdf_seleccionados = []
    metricas_individual_pdf = []
    if incluir_bloque_individual_pdf:
        jugadores_pdf_disponibles = sorted(df_tramo['player'].dropna().astype(str).unique().tolist())
        jugadores_pdf_seleccionados = st.multiselect(
            "Jugadores a incluir en el bloque Individual:",
            options=jugadores_pdf_disponibles,
            default=jugadores_seleccionados if jugadores_seleccionados else jugadores_pdf_disponibles[:min(3, len(jugadores_pdf_disponibles))],
            key="jugadores_pdf_seleccionados"
        )
        todas_metricas_individual_pdf = st.checkbox(
            "Seleccionar todas las métricas del bloque Individual",
            key="todas_metricas_individual_pdf",
            value=False
        )
        if todas_metricas_individual_pdf:
            metricas_individual_pdf = list(metricas_disponibles.keys())
            st.caption(f"Bloque Individual: se incluirán todas las métricas ({len(metricas_individual_pdf)}).")
        else:
            metricas_individual_pdf = st.multiselect(
                "Métricas del bloque Individual:",
                options=list(metricas_disponibles.keys()),
                default=[metrica_nombre],
                key="metricas_individual_pdf"
            )

    mostrar_tendencia_pdf = st.checkbox(
        "Incluir líneas de tendencia en el PDF",
        key="mostrar_tendencia_pdf_equipo",
        value=False
    )

    incluir_tabla_tendencia_pdf = st.checkbox(
        "Incluir tabla de semáforo de tendencia en el PDF",
        key="incluir_tabla_tendencia_pdf_equipo",
        value=False
    )

    incluir_detalle_individual = st.checkbox(
        "Añadir detalle individual de jugadores al final del informe",
        key="incluir_detalle_individual_pdf",
        value=(nivel_analisis == "Individual")
    )

    incluir_glosario_pdf = st.checkbox(
        "Incluir glosario en el informe",
        key="incluir_glosario_pdf_equipo",
        value=True
    )

    jugadores_detalle_pdf = []
    if incluir_detalle_individual:
        if incluir_bloque_individual_pdf and len(jugadores_pdf_seleccionados) > 0:
            jugadores_detalle_pdf = jugadores_pdf_seleccionados.copy()
            st.caption(f"Detalle individual: {len(jugadores_detalle_pdf)} jugador(es) del bloque Individual.")
        elif nivel_analisis == "Individual":
            jugadores_detalle_pdf = jugadores_seleccionados.copy()
            st.caption(f"Detalle individual: {len(jugadores_detalle_pdf)} jugador(es) seleccionados en el análisis.")
        else:
            jugadores_detalle_pdf = sorted(df_tramo['player'].dropna().astype(str).unique().tolist())
            st.caption(f"Detalle individual: {len(jugadores_detalle_pdf)} jugador(es) según el filtro actual.")

    comentario_pdf = st.text_area(
        "Comentarios para el informe (opcional):",
        key="comentario_pdf_equipo",
        height=110,
        placeholder="Escribe aquí observaciones técnicas, contexto del partido o conclusiones..."
    )

    def construir_texto_filtro():
        if modo_partido == 'Partido Específico':
            fecha = info_filtro.get('partido_seleccionado')
            base = f"Partido específico: {fecha.strftime('%d/%m/%Y')}" if fecha is not None else "Partido específico"
            return f"{base} | Tramo: {filtro_parte}"
        if modo_partido == 'Últimos N partidos':
            n = info_filtro.get('n_partidos', 0)
            ini = info_filtro.get('fecha_inicio')
            fin = info_filtro.get('fecha_fin')
            if ini is not None and fin is not None:
                return f"Últimos {n} partidos ({ini.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')}) | Tramo: {filtro_parte}"
            return f"Últimos {n} partidos | Tramo: {filtro_parte}"

        ini = info_filtro.get('fecha_inicio')
        fin = info_filtro.get('fecha_fin')
        if ini is not None and fin is not None:
            return f"Rango de fechas: {ini.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')} | Tramo: {filtro_parte}"
        return f"Rango de fechas personalizado | Tramo: {filtro_parte}"

    def construir_texto_alcance():
        bloques = []
        if incluir_bloque_equipo_pdf:
            bloques.append("Equipo completo")
        if incluir_bloque_posiciones_pdf and len(posiciones_pdf_seleccionadas) > 0:
            bloques.append("Posiciones: " + ", ".join(posiciones_pdf_seleccionadas))
        if incluir_bloque_individual_pdf and len(jugadores_pdf_seleccionados) > 0:
            bloques.append("Jugadores: " + ", ".join(jugadores_pdf_seleccionados))

        if bloques:
            return " | ".join(bloques)

        if nivel_analisis == 'Equipo':
            return "Equipo completo"
        if nivel_analisis == 'Por posiciones':
            if len(posiciones_seleccionadas) == 1:
                jugadores = sorted(df_limpio['player'].unique().tolist())
                return f"Posición: {posiciones_seleccionadas[0]} | Jugadores: {', '.join(jugadores)}"
            return f"Posiciones: {', '.join(posiciones_seleccionadas)}"
        return f"Jugadores: {', '.join(jugadores_seleccionados)}"

    def construir_resumen_bloques_pdf():
        resumen = []
        if incluir_bloque_equipo_pdf:
            resumen.append({
                "bloque": "EQUIPO",
                "alcance": "Equipo completo",
                "metricas": "Todas las métricas" if len(metricas_equipo_pdf) == len(metricas_disponibles) else ", ".join(metricas_equipo_pdf),
            })
        if incluir_bloque_posiciones_pdf and len(posiciones_pdf_seleccionadas) > 0:
            resumen.append({
                "bloque": "POSICIONES",
                "alcance": ", ".join(posiciones_pdf_seleccionadas),
                "metricas": "Todas las métricas" if len(metricas_posiciones_pdf) == len(metricas_disponibles) else ", ".join(metricas_posiciones_pdf),
            })
        if incluir_bloque_individual_pdf and len(jugadores_pdf_seleccionados) > 0:
            resumen.append({
                "bloque": "JUGADORES",
                "alcance": ", ".join(jugadores_pdf_seleccionados),
                "metricas": "Todas las métricas" if len(metricas_individual_pdf) == len(metricas_disponibles) else ", ".join(metricas_individual_pdf),
            })
        return resumen

    def construir_periodo_corto():
        def extraer_jornada(texto):
            txt = str(texto).strip().lower()
            match = re.search(r'\bj\s*(\d+)\b', txt)
            if not match:
                match = re.search(r'jornada\s*(\d+)', txt)
            if not match:
                match = re.search(r'(\d+)', txt)
            return f"J{int(match.group(1))}" if match else None

        jornadas = []
        if 'session' in df_tramo.columns:
            for sesion in df_tramo['session'].dropna().tolist():
                jornada = extraer_jornada(sesion)
                if jornada and jornada not in jornadas:
                    jornadas.append(jornada)

        def extraer_num_jornada(texto):
            match = re.search(r'(\d+)', str(texto))
            return int(match.group(1)) if match else None

        if jornadas:
            jornadas_ordenadas = sorted(
                jornadas,
                key=lambda s: (extraer_num_jornada(s) is None, extraer_num_jornada(s) or 9999, str(s))
            )
            if len(jornadas_ordenadas) == 1:
                return jornadas_ordenadas[0]
            return f"{jornadas_ordenadas[0]}-{jornadas_ordenadas[-1]}"

        fechas = sorted(pd.to_datetime(df_tramo['date']).dropna().unique().tolist())
        if len(fechas) == 1:
            return pd.to_datetime(fechas[0]).strftime('%d-%m-%y')
        if len(fechas) > 1:
            return f"{pd.to_datetime(fechas[0]).strftime('%d-%m-%y')} - {pd.to_datetime(fechas[-1]).strftime('%d-%m-%y')}"
        return "Periodo"

    def construir_periodo_portada():
        periodo_corto = construir_periodo_corto()
        if re.fullmatch(r'J\d+', periodo_corto):
            return f"De jornada {periodo_corto} a jornada {periodo_corto}"
        if re.fullmatch(r'J\d+-J\d+', periodo_corto):
            j_ini, j_fin = periodo_corto.split('-')
            return f"De jornada {j_ini} a jornada {j_fin}"
        return periodo_corto

    def construir_nombre_archivo_pdf():
        def sanitizar(texto):
            txt = str(texto).strip()
            txt = unicodedata.normalize("NFKD", txt)
            txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
            txt = re.sub(r"[^A-Za-z0-9]+", "_", txt)
            return txt.strip("_") or "NA"

        bloques_activos = []
        if incluir_bloque_equipo_pdf:
            bloques_activos.append("Equipo")
        if incluir_bloque_posiciones_pdf:
            bloques_activos.append("Posiciones")
        if incluir_bloque_individual_pdf:
            bloques_activos.append("Individual")

        if len(bloques_activos) > 1:
            nivel_nombre = "Mixto"
            alcance_nombre = "Grupo"
        elif incluir_bloque_equipo_pdf:
            nivel_nombre = "Equipo"
            alcance_nombre = "Equipo"
        elif incluir_bloque_posiciones_pdf:
            nivel_nombre = "Por posiciones"
            alcance_nombre = posiciones_pdf_seleccionadas[0] if len(posiciones_pdf_seleccionadas) == 1 else "Grupo"
        elif incluir_bloque_individual_pdf:
            nivel_nombre = "Individual"
            alcance_nombre = jugadores_pdf_seleccionados[0] if len(jugadores_pdf_seleccionados) == 1 else "Grupo"
        else:
            nivel_nombre = nivel_analisis
            alcance_nombre = "Grupo"

        periodo_nombre = construir_periodo_corto()
        return f"InformeEquipo_{sanitizar(nivel_nombre)}_{sanitizar(alcance_nombre)}_{sanitizar(periodo_nombre)}.pdf"

    if st.button("📥 Generar informe PDF", type="primary", use_container_width=True):
        if not any([incluir_bloque_equipo_pdf, incluir_bloque_posiciones_pdf, incluir_bloque_individual_pdf]):
            st.warning("⚠️ Selecciona al menos un bloque para el informe.")
        elif incluir_bloque_equipo_pdf and len(metricas_equipo_pdf) == 0:
            st.warning("⚠️ Selecciona al menos una métrica para el bloque Equipo.")
        elif incluir_bloque_posiciones_pdf and (len(posiciones_pdf_seleccionadas) == 0 or len(metricas_posiciones_pdf) == 0):
            st.warning("⚠️ Selecciona posiciones y métricas para el bloque Posiciones.")
        elif incluir_bloque_individual_pdf and (len(jugadores_pdf_seleccionados) == 0 or len(metricas_individual_pdf) == 0):
            st.warning("⚠️ Selecciona jugadores y métricas para el bloque Individual.")
        elif incluir_detalle_individual and len(jugadores_detalle_pdf) == 0:
            st.warning("⚠️ Selecciona al menos un jugador para el detalle individual.")
        else:
            with st.spinner("Generando informe PDF..."):
                metricas_para_pdf = []

                def agregar_metricas_bloque(nombre_bloque, nivel_bloque, metricas_bloque, df_base_bloque, posiciones_bloque=None, jugadores_bloque=None):
                    for metrica_pdf_nombre in metricas_bloque:
                        metrica_pdf_col = METRICAS_DICT[metrica_pdf_nombre]
                        datos_pdf = construir_datos_grafico(
                            metrica_pdf_col,
                            nivel_analisis_local=nivel_bloque,
                            df_base_local=df_base_bloque,
                            posiciones_sel=posiciones_bloque,
                            jugadores_sel=jugadores_bloque,
                        )
                        if len(datos_pdf) == 0:
                            continue
                        df_grafico_pdf = preparar_df_grafico(datos_pdf)
                        metricas_para_pdf.append({
                            "bloque_nombre": nombre_bloque,
                            "nivel_analisis": nivel_bloque,
                            "metrica_nombre": metrica_pdf_nombre,
                            "df_grafico": df_grafico_pdf,
                            "plotly_fig": crear_figura_plotly(
                                df_grafico_pdf,
                                metrica_pdf_nombre,
                                mostrar_tendencia=mostrar_tendencia_pdf
                            ),
                            "mostrar_tendencia": mostrar_tendencia_pdf,
                            "incluir_tabla_tendencia": incluir_tabla_tendencia_pdf,
                            "filtro_parte": filtro_parte,
                        })

                if incluir_bloque_equipo_pdf:
                    agregar_metricas_bloque(
                        nombre_bloque="Equipo",
                        nivel_bloque="Equipo",
                        metricas_bloque=metricas_equipo_pdf,
                        df_base_bloque=df_tramo,
                    )

                if incluir_bloque_posiciones_pdf:
                    df_posiciones_bloque = obtener_df_con_posiciones(df_tramo)
                    df_posiciones_bloque = df_posiciones_bloque[df_posiciones_bloque['posicion'].isin(posiciones_pdf_seleccionadas)]
                    agregar_metricas_bloque(
                        nombre_bloque="Posiciones",
                        nivel_bloque="Por posiciones",
                        metricas_bloque=metricas_posiciones_pdf,
                        df_base_bloque=df_posiciones_bloque,
                        posiciones_bloque=posiciones_pdf_seleccionadas,
                    )

                if incluir_bloque_individual_pdf:
                    df_individual_bloque = df_tramo[df_tramo['player'].isin(jugadores_pdf_seleccionados)].copy()
                    agregar_metricas_bloque(
                        nombre_bloque="Individual",
                        nivel_bloque="Individual",
                        metricas_bloque=metricas_individual_pdf,
                        df_base_bloque=df_individual_bloque,
                        jugadores_bloque=jugadores_pdf_seleccionados,
                    )

                detalles_jugadores_pdf = []
                if incluir_detalle_individual:
                    metricas_detalle_individual = metricas_individual_pdf if len(metricas_individual_pdf) > 0 else metricas_equipo_pdf
                    for jugador in jugadores_detalle_pdf:
                        df_jugador = df_tramo[df_tramo['player'] == jugador].copy()
                        if len(df_jugador) == 0:
                            continue

                        minutos_jugador = (
                            pd.to_numeric(df_jugador['time'], errors='coerce').dropna()
                            if 'time' in df_jugador.columns else pd.Series(dtype=float)
                        )
                        min_max = float(minutos_jugador.max()) if len(minutos_jugador) > 0 else np.nan
                        min_prom = float(minutos_jugador.mean()) if len(minutos_jugador) > 0 else np.nan
                        min_min = float(minutos_jugador.min()) if len(minutos_jugador) > 0 else np.nan

                        tarjetas = []
                        for metrica_pdf_nombre in metricas_detalle_individual:
                            metrica_col_det = METRICAS_DICT[metrica_pdf_nombre]
                            if metrica_col_det not in df_jugador.columns:
                                continue
                            valores = pd.to_numeric(df_jugador[metrica_col_det], errors='coerce').dropna()
                            if len(valores) == 0:
                                continue

                            tarjetas.append({
                                "metrica": metrica_pdf_nombre,
                                "lineas": [
                                    f"Media: {valores.mean():.1f}",
                                    f"Mejor: {valores.max():.1f}",
                                    f"Peor: {valores.min():.1f}",
                                ]
                            })

                        if len(tarjetas) > 0:
                            if 'posicion' in df_jugador.columns and df_jugador['posicion'].notna().any():
                                posicion_j = str(df_jugador['posicion'].dropna().iloc[0])
                            elif 'position' in df_jugador.columns and df_jugador['position'].notna().any():
                                posicion_j = str(df_jugador['position'].dropna().iloc[0])
                            else:
                                posicion_j = "Sin posición"

                            detalles_jugadores_pdf.append({
                                "jugador": jugador,
                                "posicion": posicion_j,
                                "foto_path": obtener_foto_jugador(jugador),
                                "minutos_max": min_max,
                                "minutos_prom": min_prom,
                                "minutos_min": min_min,
                                "tarjetas": tarjetas
                            })

                if len(metricas_para_pdf) == 0:
                    st.error("❌ No se pudo generar el informe con la selección actual.")
                else:
                    bloques_activos = [b for b in ["Equipo" if incluir_bloque_equipo_pdf else None, "Posiciones" if incluir_bloque_posiciones_pdf else None, "Individual" if incluir_bloque_individual_pdf else None] if b]
                    nivel_informe_pdf = "Mixto" if len(bloques_activos) > 1 else bloques_activos[0]
                    output_path = generar_pdf_equipo(
                        metricas_pdf=metricas_para_pdf,
                        estadistico=estadistico,
                        nivel_analisis=nivel_informe_pdf,
                        filtro_texto=construir_texto_filtro(),
                        alcance_texto=construir_texto_alcance(),
                        comentario=comentario_pdf,
                        detalles_jugadores=detalles_jugadores_pdf,
                        periodo_portada=construir_periodo_portada(),
                        output_filename=construir_nombre_archivo_pdf(),
                        resumen_bloques=construir_resumen_bloques_pdf(),
                        incluir_glosario=incluir_glosario_pdf,
                    )
                    with open(output_path, "rb") as f:
                        pdf_bytes = f.read()

                    st.success("✅ Informe generado correctamente.")
                    st.download_button(
                        label="📄 Descargar informe PDF",
                        data=pdf_bytes,
                        file_name=Path(output_path).name,
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"download_pdf_equipo_{datetime.now().strftime('%H%M%S')}"
                    )


if __name__ == "__main__":
    main()
