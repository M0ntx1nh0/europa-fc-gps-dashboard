"""
Página: Estatus del Equipo
Vista general y análisis del rendimiento colectivo

ESTRUCTURA PARA EXPORTACIÓN PDF (futuro con FPDF):
================================================
Gráficos exportables:
1. Tab "Vista General":
   - Gráfico de barras: fig (plotly) → df_equipo_sorted (datos)
   - Variables: metrica_col, metrica_nombre, tipo_estadistico, base_referencia
   
2. Tab "Comparativas":
   - Radar Chart: fig (matplotlib) → params, low, high, valores_jugadores, nombres_jugadores
   - Heatmap: fig (plotly) → matriz, nombres, nombres_metricas, df_tabla_valores
   - Scatter Plot: fig (plotly) → df_scatter
   
3. Tab "Evolución Temporal":
   - Líneas temporales: fig (plotly) → df_temporal
   
4. Tab "Distribuciones":
   - Histograma: fig (plotly) → valores, df_percentiles

Datos clave para reportes:
- df_filtrado: DataFrame principal con datos filtrados
- df_referencias: Referencias estadísticas calculadas
- modo_partido: Tipo de filtro temporal aplicado
- fecha_desde, fecha_hasta: Rango temporal

Para guardar gráficos:
- Matplotlib: fig.savefig('nombre.png', dpi=300, bbox_inches='tight')
- Plotly: fig.write_image('nombre.png', width=1200, height=800)
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Añadir directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

# Importar configuración y utilidades
from config import PAGE_TITLE, PAGE_ICON, LAYOUT, COLORES, METRICAS_DICT
from utils import (
    filtrar_por_fechas,
    obtener_partidos_disponibles,
    filtrar_por_partido,
    obtener_referencia_metrica,
    render_sidebar,
    cargar_plantilla_europa,
    mapear_posicion,
    calcular_referencias_normalizadas
)

# Configuración de página
st.set_page_config(
    page_title=f"{PAGE_TITLE} - Estatus del Equipo",
    page_icon=PAGE_ICON,
    layout=LAYOUT
)


def main():
    # Renderizar sidebar común
    render_sidebar()
    
    st.title("📊 Estatus del Equipo")
    st.markdown("Vista general del rendimiento colectivo")
    
    # Verificar que hay datos cargados
    if not st.session_state.get('datos_cargados', False):
        st.warning("⚠️ No hay datos cargados. Por favor, carga los datos desde la página **Home** primero.")
        st.info("💡 Ve a la página Home (🏠) en el menú lateral y carga tus archivos CSV.")
        st.stop()
    
    # Obtener datos del session_state
    df = st.session_state.get('df_procesado')
    
    if df is None or len(df) == 0:
        st.error("⚠️ No hay datos disponibles")
        st.stop()
    
    # Obtener fechas del session_state
    fecha_desde = st.session_state.get('fecha_desde')
    fecha_hasta = st.session_state.get('fecha_hasta')
    partido_seleccionado = st.session_state.get('partido_seleccionado')
    
    # Filtrar por rango de fechas
    df_rango = filtrar_por_fechas(df, fecha_desde, fecha_hasta)
    
    # Obtener lista de fechas únicas para los selectores
    fechas_disponibles = sorted(df_rango['date'].unique())
    
    if len(fechas_disponibles) == 0:
        st.error("⚠️ No hay partidos disponibles en el rango seleccionado")
        st.stop()
    
    # ========================================
    # SIDEBAR - SIN CONFIGURACIÓN ADICIONAL
    # ========================================
    
    # Ya no necesitamos selector de métrica aquí
    # Se selecciona en "Filtros de Referencia"
    
    # ========================================
    # FILTROS DE PARTIDO (Separados)
    # ========================================
    
    st.subheader("🎯 Filtros de Partido")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        modo_partido = st.radio(
            "Modo de selección:",
            options=['Partido Específico', 'Últimos N partidos', 'Rango de Fechas'],
            key='modo_partido'
        )
    
    with col2:
        if modo_partido == 'Partido Específico':
            partido_sel = st.selectbox(
                "Seleccionar partido:",
                options=fechas_disponibles,
                index=len(fechas_disponibles)-1,
                format_func=lambda x: x.strftime('%d/%m/%Y'),
                key='partido_especifico'
            )
            df_filtrado = df_rango[df_rango['date'] == partido_sel].copy()
            
        elif modo_partido == 'Últimos N partidos':
            n_partidos = st.selectbox(
                "Últimos N partidos:",
                options=[1, 2, 3, 4, 5, 6, 7, 8, 9],
                index=2,  # Default: 3
                key='n_partidos'
            )
            fechas_recientes = fechas_disponibles[-n_partidos:]
            df_filtrado = df_rango[df_rango['date'].isin(fechas_recientes)].copy()
            partido_sel = fechas_disponibles[-1]  # Último para referencia
            
        else:  # Rango de Fechas
            fecha_min = df_rango['date'].min()
            fecha_max = df_rango['date'].max()
            
            fecha_inicio = st.date_input(
                "Fecha inicio:",
                value=fecha_max - timedelta(days=30),
                min_value=fecha_min,
                max_value=fecha_max,
                key='fecha_inicio'
            )
            df_filtrado = df_rango[df_rango['date'] >= pd.to_datetime(fecha_inicio)].copy()
            partido_sel = fechas_disponibles[-1]
    
    with col3:
        if modo_partido == 'Rango de Fechas':
            fecha_fin = st.date_input(
                "Fecha fin:",
                value=fecha_max,
                min_value=fecha_min,
                max_value=fecha_max,
                key='fecha_fin'
            )
            df_filtrado = df_filtrado[df_filtrado['date'] <= pd.to_datetime(fecha_fin)].copy()
        
        st.metric(
            "Partidos seleccionados",
            len(df_filtrado['date'].unique())
        )
    
    st.markdown("---")
    
    # Crear diccionario de métricas disponibles para tabs (compatible con código existente)
    metricas_disponibles = {v: k for k, v in METRICAS_DICT.items()}
    
    # ========================================
    # CALCULAR REFERENCIAS (usar df_filtrado completo)
    # ========================================
    
    # Las referencias se calculan sobre los datos filtrados
    df_referencias = calcular_referencias_normalizadas(df_filtrado)
    
    # ========================================
    # TABS PRINCIPALES
    # ========================================
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Vista General",
        "🎯 Comparativas", 
        "📉 Evolución Temporal",
        "📈 Distribuciones"
    ])
    
    # ========================================
    # TAB 1: VISTA GENERAL
    # ========================================
    
    with tab1:
        st.subheader("📊 Vista General del Equipo")
        
        # ========================================
        # FILTROS DE REFERENCIA (SOLO PARA ESTE TAB)
        # ========================================
        
        st.markdown("### 📈 Configuración de Vista General")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Invertir METRICAS_DICT para tener nombre_bonito -> codigo_columna
            metrica_col = st.selectbox(
                "Métrica a analizar:",
                options=list(METRICAS_DICT.values()),  # Códigos de columna
                format_func=lambda x: [k for k, v in METRICAS_DICT.items() if v == x][0],  # Nombre bonito
                index=0,  # HSR por defecto
                key='metrica_analizar',
                help="Métrica principal para este análisis"
            )
            
            # Obtener nombre bonito
            metrica_nombre = [k for k, v in METRICAS_DICT.items() if v == metrica_col][0]
        
        with col2:
            tipo_estadistico = st.selectbox(
                "Estadística principal:",
                options=['Media', 'Mediana', 'Máximo', 'Mínimo', 'P70', 'P75', 'P80', 'P85', 'P90', 'P95'],
                index=0,
                key='tipo_estadistico',
                help="Estadística destacada en el gráfico"
            )
        
        with col3:
            base_referencia = st.selectbox(
                "Basado en:",
                options=['Todo el equipo', 'Por posición'],
                index=0,
                key='base_referencia',
                help="Todo el equipo: un solo valor\nPor posición: valores separados"
            )
        
        with col4:
            mostrar_referencias = st.multiselect(
                "Mostrar adicionales:",
                options=['Media', 'P75', 'P80', 'P85', 'P90', 'P95'],
                default=['P90'],
                key='mostrar_refs',
                help="Líneas de referencia adicionales"
            )
        
        st.markdown("---")
        
        # Agrupar por jugador (promedio si son varios partidos)
        if modo_partido == 'Partido Específico':
            df_equipo = df_filtrado.copy()
        else:
            # Promediar por jugador
            df_equipo = df_filtrado.groupby('player').agg({
                metrica_col: 'mean',
                'time': 'mean'
            }).reset_index()
        
        # Métricas del equipo
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                f"Media {metrica_nombre}",
                f"{df_equipo[metrica_col].mean():.1f}",
                delta=None
            )
        
        with col2:
            st.metric(
                f"Máximo {metrica_nombre}",
                f"{df_equipo[metrica_col].max():.1f}",
                delta=None
            )
        
        with col3:
            st.metric(
                f"Mínimo {metrica_nombre}",
                f"{df_equipo[metrica_col].min():.1f}",
                delta=None
            )
        
        with col4:
            st.metric(
                "Jugadores",
                len(df_equipo),
                delta=None
            )
        
        st.markdown("---")
        
        # Gráfico de barras con todos los jugadores
        st.subheader(f"🏃 Rendimiento Individual - {metrica_nombre}")
        
        # Ordenar por métrica
        df_equipo_sorted = df_equipo.sort_values(metrica_col, ascending=True)
        
        # Si "Basado en posición", añadir columna de posición y colorear
        if base_referencia == 'Por posición':
            try:
                df_plantilla = cargar_plantilla_europa()
                df_equipo_sorted['posicion'] = df_equipo_sorted['player'].apply(
                    lambda x: mapear_posicion(x, df_plantilla)
                )
                
                # Colores por posición
                colores_posicion = {
                    'Defensa': '#ef4444',
                    'Centrocampista': '#3b82f6',
                    'Delantero': '#22c55e',
                    'Sin posición': '#9ca3af'
                }
                
                # Asignar color a cada jugador según su posición
                df_equipo_sorted['color'] = df_equipo_sorted['posicion'].map(colores_posicion)
                
            except Exception as e:
                st.warning(f"⚠️ No se pudo cargar información de posiciones: {e}")
                df_equipo_sorted['posicion'] = 'Sin posición'
                df_equipo_sorted['color'] = '#1f77b4'
        else:
            # Color único para todo el equipo
            df_equipo_sorted['color'] = COLORES['primario']
        
        # Crear gráfico
        fig = go.Figure()
        
        # Si hay posiciones, crear una barra por posición
        if base_referencia == 'Por posición' and 'posicion' in df_equipo_sorted.columns:
            for posicion in ['Defensa', 'Centrocampista', 'Delantero', 'Sin posición']:
                df_pos = df_equipo_sorted[df_equipo_sorted['posicion'] == posicion]
                if len(df_pos) > 0:
                    fig.add_trace(go.Bar(
                        y=df_pos['player'],
                        x=df_pos[metrica_col],
                        orientation='h',
                        marker_color=colores_posicion.get(posicion, '#9ca3af'),
                        text=df_pos[metrica_col].round(1),
                        textposition='outside',
                        name=posicion,
                        hovertemplate='<b>%{y}</b><br>' +
                                     f'{metrica_nombre}: %{{x:.1f}}<br>' +
                                     f'Posición: {posicion}<br>' +
                                     '<extra></extra>'
                    ))
        else:
            # Barras con color único
            fig.add_trace(go.Bar(
                y=df_equipo_sorted['player'],
                x=df_equipo_sorted[metrica_col],
                orientation='h',
                marker_color=df_equipo_sorted['color'],
                text=df_equipo_sorted[metrica_col].round(1),
                textposition='outside',
                showlegend=False,
                hovertemplate='<b>%{y}</b><br>' +
                             f'{metrica_nombre}: %{{x:.1f}}<br>' +
                             '<extra></extra>'
            ))
        
        # Añadir líneas de referencia seleccionadas
        if df_referencias is not None:
            ref = obtener_referencia_metrica(df_referencias, metrica_col)
            if ref is not None and isinstance(ref, dict):
                # Colores distintivos para cada tipo de referencia
                colores_ref = {
                    'Media': '#FFA500',      # Naranja
                    'Mediana': '#9370DB',    # Púrpura
                    'P75': '#4169E1',        # Azul real
                    'P80': '#20B2AA',        # Verde azulado
                    'P85': '#32CD32',        # Verde lima
                    'P90': '#FF4500',        # Rojo-naranja
                    'P95': '#DC143C',        # Crimson
                    'Máximo': '#8B0000'      # Rojo oscuro
                }
                
                # Primero añadir el estadístico principal (más grueso)
                if tipo_estadistico in ref:
                    fig.add_vline(
                        x=ref[tipo_estadistico],
                        line_dash="solid",
                        line_color=colores_ref.get(tipo_estadistico, '#FF0000'),
                        line_width=3,
                        annotation_text=f"🎯 {tipo_estadistico}: {ref[tipo_estadistico]:.1f}",
                        annotation_position="top right",
                        annotation=dict(
                            font=dict(size=12, color="white"),
                            bgcolor=colores_ref.get(tipo_estadistico, '#FF0000'),
                            borderpad=4
                        )
                    )
                
                # Luego añadir referencias adicionales (más finas)
                for ref_tipo in mostrar_referencias:
                    if ref_tipo in ref and ref_tipo != tipo_estadistico:
                        fig.add_vline(
                            x=ref[ref_tipo],
                            line_dash="dash",
                            line_color=colores_ref.get(ref_tipo, '#999999'),
                            line_width=2,
                            annotation_text=f"{ref_tipo}: {ref[ref_tipo]:.1f}",
                            annotation_position="bottom right",
                            annotation=dict(
                                font=dict(size=10, color="white"),
                                bgcolor=colores_ref.get(ref_tipo, '#999999'),
                                borderpad=3
                            )
                        )
        
        fig.update_layout(
            title=f"Comparativa de Jugadores - {metrica_nombre}" + 
                  (" (por posición)" if base_referencia == 'Por posición' else ""),
            xaxis_title=metrica_nombre,
            yaxis_title="Jugador",
            height=max(400, len(df_equipo) * 30),
            showlegend=(base_referencia == 'Por posición'),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            hovermode='y'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabla resumen
        with st.expander("📋 Ver tabla de datos"):
            df_display = df_equipo[['player', metrica_col, 'time']].copy()
            df_display.columns = ['Jugador', metrica_nombre, 'Tiempo (min)']
            df_display = df_display.sort_values(metrica_nombre, ascending=False)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # ========================================
    # TAB 4: DISTRIBUCIONES
    # ========================================
    
    with tab4:
        st.subheader("📈 Distribución del Equipo")
        
        # Explicación del gráfico
        st.markdown("""
        **¿Qué muestra este gráfico?**
        
        El **histograma** muestra cómo se distribuyen los valores de una métrica en tu equipo:
        - **Eje horizontal (X)**: Rango de valores de la métrica (ej: HSR de 400 a 900)
        - **Eje vertical (Y)**: Cuántos jugadores/partidos hay en cada rango
        - **Barras altas**: Muchos jugadores/partidos con esos valores (zona común)
        - **Barras bajas**: Pocos jugadores/partidos con esos valores (zona rara)
        
        **Líneas de referencia:**
        - 🔴 **Media** (roja): Promedio del equipo
        - 🟠 **P75** (naranja): Top 25% del equipo
        - 🟢 **P90** (verde): Top 10% del equipo (élite)
        
        **Ejemplo:** Si hay una barra alta en 700-750 de HSR, significa que la mayoría del equipo hace entre 700-750 metros de alta intensidad.
        """)
        
        st.markdown("---")
        
        # Selector de métrica para histograma
        col1, col2 = st.columns([3, 1])
        
        with col1:
            metrica_dist = st.selectbox(
                "Métrica a analizar:",
                options=list(metricas_disponibles.keys()),
                format_func=lambda x: metricas_disponibles[x],
                key='metrica_distribucion'
            )
        
        with col2:
            n_bins = st.slider(
                "Nº de barras:",
                min_value=5,
                max_value=20,
                value=10,
                key='n_bins'
            )
        
        metrica_dist_nombre = metricas_disponibles[metrica_dist]
        
        # Preparar datos
        if modo_partido == 'Partido Específico':
            valores = df_filtrado[metrica_dist].dropna()
        else:
            # Todos los valores individuales (no promediados)
            valores = df_filtrado[metrica_dist].dropna()
        
        if len(valores) == 0:
            st.warning("⚠️ No hay datos para mostrar")
        else:
            # Calcular estadísticos
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Media", f"{valores.mean():.1f}")
            with col2:
                st.metric("Mediana", f"{valores.median():.1f}")
            with col3:
                st.metric("P75", f"{valores.quantile(0.75):.1f}")
            with col4:
                st.metric("P90", f"{valores.quantile(0.90):.1f}")
            with col5:
                st.metric("Máximo", f"{valores.max():.1f}")
            
            st.markdown("---")
            
            # Histograma
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=valores,
                nbinsx=n_bins,
                marker_color=COLORES['primario'],
                opacity=0.7,
                name='Frecuencia',
                hovertemplate='Rango: %{x}<br>Frecuencia: %{y}<extra></extra>'
            ))
            
            # Líneas verticales de referencias
            if df_referencias is not None:
                ref = obtener_referencia_metrica(df_referencias, metrica_dist)
                if ref is not None and isinstance(ref, dict):
                    # Media
                    fig.add_vline(
                        x=ref['Media'],
                        line_dash="solid",
                        line_color='red',
                        line_width=2,
                        annotation_text=f"Media: {ref['Media']:.1f}",
                        annotation_position="top right"
                    )
                    # P75
                    if 'P75' in ref:
                        fig.add_vline(
                            x=ref['P75'],
                            line_dash="dash",
                            line_color='orange',
                            line_width=2,
                            annotation_text=f"P75: {ref['P75']:.1f}",
                            annotation_position="top right"
                        )
                    # P90
                    if 'P90' in ref:
                        fig.add_vline(
                            x=ref['P90'],
                            line_dash="dot",
                            line_color='green',
                            line_width=2,
                            annotation_text=f"P90: {ref['P90']:.1f}",
                            annotation_position="top left"
                        )
            
            fig.update_layout(
                title=f"Histograma de {metrica_dist_nombre} - Distribución de Frecuencias",
                xaxis_title=f"{metrica_dist_nombre} (rangos de valores)",
                yaxis_title="Frecuencia (cuántos jugadores/partidos)",
                height=550,
                showlegend=False,
                bargap=0.1
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de percentiles
            st.subheader("📊 Tabla de Percentiles")
            
            percentiles = [10, 25, 50, 75, 90, 95]
            percentil_data = {
                'Percentil': [f'P{p}' for p in percentiles],
                'Valor': [valores.quantile(p/100) for p in percentiles],
                'Top %': [f'{100-p}%' for p in percentiles],
                'Interpretación': [
                    'Mínimo aceptable',
                    'Por debajo del promedio',
                    'Promedio (mediana)',
                    'Buen rendimiento',
                    'Muy buen rendimiento',
                    'Excelente (élite)'
                ]
            }
            
            df_percentiles = pd.DataFrame(percentil_data)
            df_percentiles['Valor'] = df_percentiles['Valor'].round(1)
            
            st.dataframe(df_percentiles, use_container_width=True, hide_index=True)
            
            # Interpretación
            st.info(f"""
            **💡 Interpretación:**
            - **P90 ({valores.quantile(0.90):.1f})**: Solo el top 10% alcanza o supera este valor
            - **P75 ({valores.quantile(0.75):.1f})**: El top 25% del equipo está por encima
            - **Mediana ({valores.median():.1f})**: 50% del equipo está por encima y 50% por debajo
            - **Media ({valores.mean():.1f})**: Promedio del equipo (puede verse afectado por valores extremos)
            """)

    
    # ========================================
    # TAB 2: COMPARATIVAS
    # ========================================
    
    with tab2:
        st.subheader("🎯 Análisis Comparativo")
        
        # Selector de modo
        modo_comparativa = st.radio(
            "Modo de análisis:",
            options=['Scatter Plot (2 métricas)', 'Comparar Jugadores/Posiciones'],
            horizontal=True,
            key='modo_comparativa'
        )
        
        st.markdown("---")
        
        if modo_comparativa == 'Scatter Plot (2 métricas)':
            st.markdown("""
            **Scatter Plot:** Analiza la relación entre dos métricas. Cada punto representa un jugador.
            """)
            
            # Selectores de métricas y filtros
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                metrica_x = st.selectbox(
                    "Métrica Eje X:",
                    options=list(metricas_disponibles.keys()),
                    index=1,  # Distancia por defecto
                    format_func=lambda x: metricas_disponibles[x],
                    key='metrica_x_scatter'
                )
            
            with col2:
                metrica_y = st.selectbox(
                    "Métrica Eje Y:",
                    options=list(metricas_disponibles.keys()),
                    index=0,  # HSR por defecto
                    format_func=lambda x: metricas_disponibles[x],
                    key='metrica_y_scatter'
                )
            
            with col3:
                filtro_posicion_scatter = st.selectbox(
                    "Filtrar por posición:",
                    options=['Todas', 'Defensa', 'Centrocampista', 'Delantero'],
                    index=0,
                    key='filtro_posicion_scatter',
                    help="Mostrar solo jugadores de una posición"
                )
            
            with col4:
                mostrar_nombres = st.checkbox(
                    "Mostrar nombres",
                    value=True,
                    key='mostrar_nombres_scatter'
                )
            
            metrica_x_nombre = metricas_disponibles[metrica_x]
            metrica_y_nombre = metricas_disponibles[metrica_y]
            
            # Preparar datos
            if modo_partido == 'Partido Específico':
                df_scatter = df_filtrado[['player', metrica_x, metrica_y, 'time']].copy()
            else:
                # Promediar por jugador
                df_scatter = df_filtrado.groupby('player').agg({
                    metrica_x: 'mean',
                    metrica_y: 'mean',
                    'time': 'mean'
                }).reset_index()
            
            # Eliminar NaN
            df_scatter = df_scatter.dropna(subset=[metrica_x, metrica_y])
            
            if len(df_scatter) == 0:
                st.warning("⚠️ No hay datos suficientes para el scatter plot")
            else:
                # Intentar cargar posiciones para colorear
                try:
                    df_plantilla = cargar_plantilla_europa()
                    df_scatter['posicion'] = df_scatter['player'].apply(
                        lambda x: mapear_posicion(x, df_plantilla)
                    )
                except:
                    df_scatter['posicion'] = 'Sin posición'
                
                # Aplicar filtro de posición si está seleccionado
                if filtro_posicion_scatter != 'Todas':
                    df_scatter = df_scatter[df_scatter['posicion'] == filtro_posicion_scatter].copy()
                    
                    if len(df_scatter) == 0:
                        st.warning(f"⚠️ No hay jugadores de la posición '{filtro_posicion_scatter}' en los datos seleccionados")
                        st.stop()
                
                # Crear scatter plot
                fig = px.scatter(
                    df_scatter,
                    x=metrica_x,
                    y=metrica_y,
                    color='posicion',
                    hover_name='player',
                    hover_data={
                        metrica_x: ':.1f',
                        metrica_y: ':.1f',
                        'time': ':.0f',
                        'posicion': True
                    },
                    labels={
                        metrica_x: metrica_x_nombre,
                        metrica_y: metrica_y_nombre,
                        'time': 'Tiempo (min)',
                        'posicion': 'Posición'
                    },
                    color_discrete_map={
                        'Defensa': '#ef4444',
                        'Centrocampista': '#3b82f6',
                        'Delantero': '#22c55e',
                        'Sin posición': '#9ca3af'
                    }
                )
                
                # Añadir nombres si está activado
                if mostrar_nombres:
                    for _, row in df_scatter.iterrows():
                        fig.add_annotation(
                            x=row[metrica_x],
                            y=row[metrica_y],
                            text=row['player'],
                            showarrow=False,
                            yshift=10,
                            font=dict(size=9)
                        )
                
                # Añadir líneas de referencia
                if df_referencias is not None:
                    # Línea vertical (eje X)
                    ref_x = obtener_referencia_metrica(df_referencias, metrica_x)
                    if ref_x is not None and isinstance(ref_x, dict) and tipo_estadistico in ref_x:
                        fig.add_vline(
                            x=ref_x[tipo_estadistico],
                            line_dash="dash",
                            line_color='gray',
                            annotation_text=f"{tipo_estadistico} X",
                            annotation_position="top"
                        )
                    
                    # Línea horizontal (eje Y)
                    ref_y = obtener_referencia_metrica(df_referencias, metrica_y)
                    if ref_y is not None and isinstance(ref_y, dict) and tipo_estadistico in ref_y:
                        fig.add_hline(
                            y=ref_y[tipo_estadistico],
                            line_dash="dash",
                            line_color='gray',
                            annotation_text=f"{tipo_estadistico} Y",
                            annotation_position="right"
                        )
                
                fig.update_traces(marker=dict(size=12))
                
                fig.update_layout(
                    title=f"Relación: {metrica_y_nombre} vs {metrica_x_nombre}",
                    height=600,
                    hovermode='closest'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Análisis de cuadrantes
                if df_referencias is not None:
                    ref_x = obtener_referencia_metrica(df_referencias, metrica_x)
                    ref_y = obtener_referencia_metrica(df_referencias, metrica_y)
                    
                    if (ref_x is not None and isinstance(ref_x, dict) and tipo_estadistico in ref_x and
                        ref_y is not None and isinstance(ref_y, dict) and tipo_estadistico in ref_y):
                        
                        valor_ref_x = ref_x[tipo_estadistico]
                        valor_ref_y = ref_y[tipo_estadistico]
                        
                        # Clasificar en cuadrantes
                        df_scatter['cuadrante'] = 'Bajo en ambas'
                        df_scatter.loc[
                            (df_scatter[metrica_x] >= valor_ref_x) & (df_scatter[metrica_y] >= valor_ref_y),
                            'cuadrante'
                        ] = '🟢 Alto en ambas'
                        df_scatter.loc[
                            (df_scatter[metrica_x] >= valor_ref_x) & (df_scatter[metrica_y] < valor_ref_y),
                            'cuadrante'
                        ] = f'🔵 Alto en {metrica_x_nombre}'
                        df_scatter.loc[
                            (df_scatter[metrica_x] < valor_ref_x) & (df_scatter[metrica_y] >= valor_ref_y),
                            'cuadrante'
                        ] = f'🔵 Alto en {metrica_y_nombre}'
                        df_scatter.loc[
                            (df_scatter[metrica_x] < valor_ref_x) & (df_scatter[metrica_y] < valor_ref_y),
                            'cuadrante'
                        ] = '🟠 Bajo en ambas'
                        
                        st.subheader("📊 Análisis por Cuadrantes")
                        
                        # Contar jugadores por cuadrante
                        cuadrantes = df_scatter['cuadrante'].value_counts()
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        for idx, (cuad, col) in enumerate(zip(cuadrantes.index, [col1, col2, col3, col4])):
                            with col:
                                st.metric(
                                    cuad,
                                    cuadrantes[cuad],
                                    delta=f"{cuadrantes[cuad]/len(df_scatter)*100:.0f}%"
                                )
                        
                        # Listar jugadores por cuadrante
                        with st.expander("👥 Ver jugadores por cuadrante"):
                            for cuad in cuadrantes.index:
                                st.markdown(f"**{cuad}:**")
                                jugadores = df_scatter[df_scatter['cuadrante'] == cuad]['player'].tolist()
                                st.write(", ".join(jugadores))
                                st.markdown("")
        
        else:  # Modo: Comparar Jugadores/Posiciones
            st.markdown("""
            **Comparar Jugadores/Posiciones:** Visualiza perfiles completos con Radar Chart o Heatmap.
            """)
            
            # Selectores principales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                modo_comparar = st.radio(
                    "Comparar por:",
                    options=['Jugadores individuales', 'Posiciones (promedio)'],
                    key='modo_comparar',
                    help="Jugadores: Selecciona hasta 3 jugadores específicos\nPosiciones: Compara promedios por posición (se aplicará el estadístico seleccionado)"
                )
            
            with col2:
                estadistico_comparar = st.selectbox(
                    "Estadística a usar:",
                    options=['Media', 'Mediana', 'Máximo', 'Mínimo', 'P70', 'P75', 'P80', 'P85', 'P90', 'P95'],
                    index=0,
                    key='estadistico_comparar',
                    help="Estadístico que se usará para calcular los valores de cada jugador/posición"
                )
            
            with col3:
                tipo_viz = st.radio(
                    "Tipo de visualización:",
                    options=['Radar/Spider Chart', 'Heatmap', 'Gráfico de Barras'],
                    key='tipo_viz',
                    help="Radar: Perfiles visuales completos (mín. 3 métricas)\nHeatmap: Tabla de colores compacta\nBarras: Comparación directa (cualquier número de métricas)"
                )
            
            st.markdown("---")
            
            # Preparar datos base según estadístico
            if modo_partido == 'Partido Específico':
                # Para partido específico, usar valores directos
                df_comp_base = df_filtrado.copy()
            else:
                # Para múltiples partidos, aplicar el estadístico seleccionado
                # Mapeo de estadísticos a funciones de agregación
                estadistico_map = {
                    'Media': 'mean',
                    'Mediana': 'median',
                    'Máximo': 'max',
                    'Mínimo': 'min',
                    'P70': lambda x: x.quantile(0.70),
                    'P75': lambda x: x.quantile(0.75),
                    'P80': lambda x: x.quantile(0.80),
                    'P85': lambda x: x.quantile(0.85),
                    'P90': lambda x: x.quantile(0.90),
                    'P95': lambda x: x.quantile(0.95)
                }
                
                agg_func = estadistico_map[estadistico_comparar]
                
                # Agrupar por jugador aplicando el estadístico
                df_comp_base = df_filtrado.groupby('player').agg({
                    metrica: agg_func for metrica in metricas_disponibles.keys()
                }).reset_index()
            
            # Selector según modo
            col_sel, col_metricas = st.columns([2, 1])
            
            with col_sel:
                if modo_comparar == 'Jugadores individuales':
                    jugadores_disponibles = sorted(df_comp_base['player'].unique())
                    
                    elementos_seleccionados = st.multiselect(
                        "Seleccionar jugadores (máximo 3):",
                        options=jugadores_disponibles,
                        default=jugadores_disponibles[:min(3, len(jugadores_disponibles))],
                        max_selections=3,
                        key='jugadores_comparar_visual',
                        help="Máximo 3 jugadores para mantener visualización clara"
                    )
                    
                    if len(elementos_seleccionados) < 2:
                        st.warning("⚠️ Selecciona al menos 2 jugadores")
                        st.stop()
                    
                    # Filtrar datos
                    df_comparacion = df_comp_base[df_comp_base['player'].isin(elementos_seleccionados)].copy()
                    df_comparacion['nombre'] = df_comparacion['player']
                    
                else:  # Por posiciones
                    elementos_seleccionados = st.multiselect(
                        "Seleccionar posiciones (máximo 3):",
                        options=['Defensa', 'Centrocampista', 'Delantero'],
                        default=['Defensa', 'Centrocampista', 'Delantero'],
                        max_selections=3,
                        key='posiciones_comparar_visual',
                        help=f"Compara el {estadistico_comparar.lower()} de cada posición"
                    )
                    
                    if len(elementos_seleccionados) < 2:
                        st.warning("⚠️ Selecciona al menos 2 posiciones")
                        st.stop()
                    
                    # Cargar posiciones y agrupar según estadístico
                    try:
                        df_plantilla = cargar_plantilla_europa()
                        
                        # Si es partido específico, usar df_filtrado con posiciones
                        if modo_partido == 'Partido Específico':
                            df_temp = df_filtrado.copy()
                        else:
                            # Para múltiples partidos, primero aplicar estadístico por jugador
                            # (ya calculado en df_comp_base)
                            df_temp = df_comp_base.copy()
                        
                        df_temp['posicion'] = df_temp['player'].apply(
                            lambda x: mapear_posicion(x, df_plantilla)
                        )
                        
                        # Agrupar por posición (usando media de los valores ya agregados por jugador)
                        # O valores directos si es partido específico
                        df_comparacion = df_temp.groupby('posicion').agg({
                            metrica: 'mean' for metrica in metricas_disponibles.keys()
                        }).reset_index()
                        
                        # Filtrar solo las seleccionadas
                        df_comparacion = df_comparacion[df_comparacion['posicion'].isin(elementos_seleccionados)].copy()
                        df_comparacion['nombre'] = df_comparacion['posicion']
                        
                        if len(df_comparacion) == 0:
                            st.warning("⚠️ No hay datos para las posiciones seleccionadas")
                            st.stop()
                            
                    except Exception as e:
                        st.error(f"⚠️ Error al cargar posiciones: {e}")
                        st.stop()
            
            with col_metricas:
                metricas_comparar = st.multiselect(
                    "Métricas a comparar:",
                    options=list(metricas_disponibles.keys()),
                    default=['hsr', 'total_distance', 'sprints', 'max_speed'],
                    format_func=lambda x: metricas_disponibles[x],
                    key='metricas_comparar_visual',
                    help="Selecciona las métricas que quieres visualizar"
                )
                
                if len(metricas_comparar) < 3:
                    if tipo_viz == 'Radar/Spider Chart':
                        st.warning("⚠️ El Radar Chart requiere al menos 3 métricas. Selecciona más métricas o usa 'Gráfico de Barras'.")
                        st.stop()
                            
            st.markdown("---")
            
            # ========================================
            # GENERAR VISUALIZACIÓN
            # ========================================
            
            if tipo_viz == 'Radar/Spider Chart':
                st.subheader("🕸️ Radar Chart - Perfiles Comparativos")
                
                # Info sobre el radar
                st.markdown("**Radar profesional con escalas independientes por métrica:**")
                
                # Calcular min-max para CADA métrica entre los seleccionados
                rangos_metricas = {}
                for metrica in metricas_comparar:
                    valores = df_comparacion[metrica]
                    rangos_metricas[metrica] = {
                        'min': valores.min(),
                        'max': valores.max()
                    }
                
                # Preparar datos para mplsoccer
                params = [metricas_disponibles[m] for m in metricas_comparar]
                low = [rangos_metricas[m]['min'] for m in metricas_comparar]
                high = [rangos_metricas[m]['max'] for m in metricas_comparar]
                
                # Valores de cada jugador
                valores_jugadores = []
                nombres_jugadores = []
                for idx, (df_idx, row) in enumerate(df_comparacion.iterrows()):
                    valores = [row[m] for m in metricas_comparar]
                    valores_jugadores.append(valores)
                    nombres_jugadores.append(row['nombre'])
                
                # Colores para cada jugador
                colores_radar = [
                    {'face': '#1E88E5', 'edge': '#0D47A1'},  # Azul
                    {'face': '#FF6F00', 'edge': '#E65100'},  # Naranja
                    {'face': '#43A047', 'edge': '#1B5E20'}   # Verde
                ]
                
                try:
                    # Importar mplsoccer
                    from mplsoccer import Radar
                    import matplotlib.pyplot as plt
                    
                    # Crear radar
                    radar = Radar(
                        params, 
                        low, 
                        high,
                        round_int=[False]*len(params),
                        num_rings=4,
                        ring_width=1,
                        center_circle_radius=1
                    )
                    
                    # Crear figura con tamaño reducido y alta resolución
                    fig, ax = radar.setup_axis(
                        figsize=(8, 8),      # Más compacto (antes era default ~12x12)
                        facecolor='white'
                    )
                    fig.set_dpi(150)         # Alta resolución (150 DPI)
                    
                    # Dibujar círculos de fondo
                    rings_inner = radar.draw_circles(
                        ax=ax, 
                        facecolor='#f0f0f0', 
                        edgecolor='#cccccc',
                        linewidth=1
                    )
                    
                    # Dibujar cada jugador
                    vertices_list = []
                    for idx, valores in enumerate(valores_jugadores):
                        if idx < len(colores_radar):
                            color = colores_radar[idx]
                            
                            # Dibujar área rellena
                            radar_poly, vertices = radar.draw_radar_solid(
                                valores, 
                                ax=ax,
                                kwargs={
                                    'facecolor': color['face'],
                                    'alpha': 0.4,
                                    'edgecolor': color['edge'],
                                    'lw': 2.5  # Ligeramente más fino
                                }
                            )
                            
                            vertices_list.append((vertices, color))
                    
                    # Dibujar puntos en los vértices (más pequeños)
                    for vertices, color in vertices_list:
                        ax.scatter(
                            vertices[:, 0], 
                            vertices[:, 1],
                            c=color['face'], 
                            edgecolors=color['edge'], 
                            marker='o', 
                            s=100,  # Reducido de 150 a 100
                            zorder=2,
                            linewidth=1.5
                        )
                    
                    # Etiquetas de rango (más pequeñas)
                    range_labels = radar.draw_range_labels(ax=ax, fontsize=8)
                    
                    # Etiquetas de parámetros (más pequeñas)
                    param_labels = radar.draw_param_labels(ax=ax, fontsize=10)
                    
                    # Título (más compacto) con estadístico
                    title_text = f"Comparativa ({estadistico_comparar}): {', '.join(nombres_jugadores[:3])}"
                    ax.text(
                        0.5, 1.12, title_text,
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=ax.transAxes,
                        fontsize=12,
                        fontweight='bold'
                    )
                    
                    # Leyenda (más compacta)
                    legend_elements = []
                    for idx, nombre in enumerate(nombres_jugadores[:3]):
                        color = colores_radar[idx]
                        from matplotlib.patches import Patch
                        legend_elements.append(
                            Patch(facecolor=color['face'], edgecolor=color['edge'], 
                                  label=nombre, linewidth=1.5)
                        )
                    
                    ax.legend(
                        handles=legend_elements,
                        loc='upper center',
                        bbox_to_anchor=(0.5, -0.08),
                        ncol=3,
                        frameon=False,
                        fontsize=9
                    )
                    
                    # Ajustar layout para que no se corten elementos
                    plt.tight_layout()
                    
                    # ========================================
                    # EXPORTACIÓN: Para PDF futuro
                    # Variables disponibles:
                    # - fig: Figura matplotlib completa
                    # - radar: Objeto Radar configurado
                    # - valores_jugadores: Lista con valores de cada jugador
                    # - nombres_jugadores: Lista con nombres
                    # - params: Lista con nombres de métricas
                    # - low, high: Rangos de cada métrica
                    # 
                    # Para guardar: fig.savefig('radar.png', dpi=300, bbox_inches='tight')
                    # ========================================
                    
                    # Mostrar en Streamlit
                    st.pyplot(fig, use_container_width=False)  # No usar ancho completo
                    plt.close()
                    
                    # Explicación
                    st.info("""
                    📊 **Cómo interpretar:** 
                    - **Escalas independientes:** Cada eje tiene su propio rango (min-max entre los seleccionados)
                    - **Áreas coloreadas:** Cada jugador tiene su color distintivo
                    - **Puntos en vértices:** Marcan el valor exacto de cada métrica
                    - **Anillos concéntricos:** Ayudan a leer los valores en cada eje
                    - **Área mayor = mejor rendimiento** en ese conjunto de métricas
                    """)
                    
                except ImportError:
                    st.error("""
                    ⚠️ **mplsoccer no está instalado**
                    
                    Para usar el Radar Chart profesional, necesitas instalar mplsoccer:
                    
                    ```bash
                    pip install mplsoccer --break-system-packages
                    ```
                    
                    Luego reinicia la aplicación.
                    """)
                except Exception as e:
                    st.error(f"Error al crear el radar: {str(e)}")
                    st.write("**Debug info:**", e)
                
            elif tipo_viz == "heatmap": 
                st.subheader("🌡️ Heatmap - Tabla de Calor")
                
                # Preparar matriz para heatmap
                matriz = []
                nombres = []
                
                for idx, (df_idx, row) in enumerate(df_comparacion.iterrows()):
                    valores = [row[m] for m in metricas_comparar]
                    matriz.append(valores)
                    nombres.append(row['nombre'])
                
                nombres_metricas = [metricas_disponibles[m] for m in metricas_comparar]
                
                # Normalizar por columna (métrica) para comparabilidad
                matriz_norm = np.array(matriz).T  # Transponer
                matriz_norm_scaled = []
                
                for i, metrica_vals in enumerate(matriz_norm):
                    val_min = metrica_vals.min()
                    val_max = metrica_vals.max()
                    
                    if val_max > val_min:
                        norm_vals = ((metrica_vals - val_min) / (val_max - val_min)) * 100
                    else:
                        norm_vals = np.full_like(metrica_vals, 50)
                    
                    matriz_norm_scaled.append(norm_vals)
                
                matriz_norm_scaled = np.array(matriz_norm_scaled).T  # Volver a transponer
                
                # Crear heatmap
                fig = go.Figure(data=go.Heatmap(
                    z=matriz_norm_scaled,
                    x=nombres_metricas,
                    y=nombres,
                    colorscale='RdYlGn',  # Rojo-Amarillo-Verde
                    text=np.array(matriz).round(1),
                    texttemplate='%{text}',
                    textfont={"size": 12},
                    colorbar=dict(
                        title="Escala<br>0-100",
                        tickvals=[0, 25, 50, 75, 100],
                        ticktext=['Bajo', '25', '50', '75', 'Alto']
                    ),
                    hovertemplate='<b>%{y}</b><br>' +
                                '<b>%{x}</b><br>' +
                                'Valor: %{text}<br>' +
                                'Normalizado: %{z:.1f}/100<br>' +
                                '<extra></extra>'
                ))
                
                fig.update_layout(
                    title=f"Comparativa de Métricas ({estadistico_comparar}) - Colores normalizados, valores reales mostrados",
                    height=max(300, len(nombres) * 80),
                    xaxis_title="Métrica",
                    yaxis_title=modo_comparar.split()[0]  # "Jugadores" o "Posiciones"
                )
                
                # ========================================
                # EXPORTACIÓN: Para PDF futuro
                # Variables disponibles:
                # - fig: Figura Plotly (heatmap)
                # - matriz: Valores reales [[val1, val2, ...], ...]
                # - matriz_norm_scaled: Valores normalizados 0-100
                # - nombres: Lista de nombres (jugadores/posiciones)
                # - nombres_metricas: Lista de nombres de métricas
                # - df_tabla_valores: DataFrame con valores para tabla
                # 
                # Para guardar: fig.write_image('heatmap.png', width=1200, height=800)
                # ========================================
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Explicación
                st.info("""
                🌡️ **Cómo interpretar:**
                - 🟢 Verde = Alto rendimiento en esa métrica (entre los seleccionados)
                - 🟡 Amarillo = Rendimiento medio
                - 🔴 Rojo = Bajo rendimiento en esa métrica
                - Los números muestran los **valores reales**, los colores están normalizados para comparar
                """)
            
            else:  # Gráfico de Barras
                st.subheader("📊 Gráfico de Barras - Comparación Directa")
                
                # Preparar datos
                nombres = []
                datos_por_metrica = {metricas_disponibles[m]: [] for m in metricas_comparar}
                
                for idx, (df_idx, row) in enumerate(df_comparacion.iterrows()):
                    nombres.append(row['nombre'])
                    for metrica in metricas_comparar:
                        datos_por_metrica[metricas_disponibles[metrica]].append(row[metrica])
                
                # Colores para cada jugador (consistentes)
                colores_jugadores = ['#1E88E5', '#FF6F00', '#43A047', '#E53935', '#8E24AA']
                
                # Crear subplots (una columna por métrica)
                from plotly.subplots import make_subplots
                
                n_metricas = len(metricas_comparar)
                
                fig = make_subplots(
                    rows=1, 
                    cols=n_metricas,
                    subplot_titles=[metricas_disponibles[m] for m in metricas_comparar],
                    horizontal_spacing=0.08,
                    specs=[[{"type": "bar"}] * n_metricas]
                )
                
                # Para cada métrica, crear un subplot
                for col_idx, (metrica, metrica_nombre) in enumerate(datos_por_metrica.items(), start=1):
                    valores = metrica_nombre
                    
                    # Añadir barras de cada jugador en este subplot
                    for jug_idx, (nombre, valor) in enumerate(zip(nombres, datos_por_metrica[metrica])):
                        fig.add_trace(
                            go.Bar(
                                name=nombre,
                                x=[metrica],
                                y=[valor],
                                text=[f"{valor:.1f}"],
                                textposition='outside',
                                marker_color=colores_jugadores[jug_idx % len(colores_jugadores)],
                                showlegend=(col_idx == 1),  # Solo mostrar leyenda en primer subplot
                                legendgroup=nombre,  # Agrupar para leyenda consistente
                                hovertemplate=f'<b>{nombre}</b><br>' +
                                              f'{metrica}: %{{y:.1f}}<br>' +
                                              '<extra></extra>'
                            ),
                            row=1,
                            col=col_idx
                        )
                
                # Aplicar tamaño de texto
                fig.update_traces(
                    textfont=dict(size=13, color='black'),
                    textposition='outside',
                    selector=dict(type='bar')
                )
                
                # Layout general
                fig.update_layout(
                    title=f"Comparativa de Métricas ({estadistico_comparar}) - Escalas Independientes",
                    height=500,
                    barmode='group',
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=-0.15,
                        xanchor="center",
                        x=0.5
                    ),
                    uniformtext_minsize=12,
                    uniformtext_mode='show'
                )
                
                # Ocultar etiquetas del eje X (ya están en títulos de subplot)
                fig.update_xaxes(showticklabels=False)
                
                # Configurar ejes Y independientes
                for i in range(1, n_metricas + 1):
                    fig.update_yaxes(title_text="Valor", row=1, col=i)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Explicación
                st.info("""
                📊 **Cómo interpretar:**
                - Cada panel muestra una métrica diferente con su **propia escala**
                - Cada color representa un jugador/posición (consistente entre paneles)
                - Las **escalas son independientes**: sprints ~30 y distancia ~8000 se ven proporcionadas
                - Los números sobre las barras muestran los valores exactos
                - **Ideal para comparar múltiples métricas sin distorsión visual**
                """)
                
            # Tabla de valores reales
            st.subheader("📊 Tabla de Valores Reales")
            
            df_tabla_valores = df_comparacion[['nombre'] + metricas_comparar].copy()
            df_tabla_valores.columns = ['Elemento'] + [metricas_disponibles[m] for m in metricas_comparar]
            
            # Formatear números
            for col in df_tabla_valores.columns[1:]:
                df_tabla_valores[col] = df_tabla_valores[col].round(1)
            
            st.dataframe(
                df_tabla_valores,
                use_container_width=True,
                hide_index=True
            )


    
   # ========================================
    # TAB 3: EVOLUCIÓN TEMPORAL
    # ========================================
    
    with tab3:
        st.subheader("📉 Evolución Temporal del Equipo")
        
        # Opciones de visualización
        col1, col2 = st.columns(2)
        
        with col1:
            metrica_evol = st.selectbox(
                "Métrica a visualizar:",
                options=list(metricas_disponibles.keys()),
                format_func=lambda x: metricas_disponibles[x],
                key='metrica_evolucion'
            )
        
        with col2:
            tipo_linea = st.selectbox(
                "Mostrar:",
                options=['Media del equipo', 'Por posición', 'Top 5 jugadores', 'Todos los jugadores', 'Selección manual'],
                index=0,
                key='tipo_linea_evol'
            )
        
        # Si es selección manual, mostrar selector de jugadores
        jugadores_seleccionados_evol = None
        if tipo_linea == 'Selección manual':
            jugadores_disponibles_evol = sorted(df_filtrado['player'].unique())
            
            jugadores_seleccionados_evol = st.multiselect(
                "Seleccionar jugadores (máximo 5):",
                options=jugadores_disponibles_evol,
                default=jugadores_disponibles_evol[:min(3, len(jugadores_disponibles_evol))],
                max_selections=5,
                key='jugadores_evol_manual',
                help="Máximo 5 jugadores para mantener el gráfico legible"
            )
            
            if len(jugadores_seleccionados_evol) == 0:
                st.warning("⚠️ Selecciona al menos 1 jugador")
                st.stop()
        
        metrica_evol_nombre = metricas_disponibles[metrica_evol]
        
        # Preparar datos temporales
        df_temporal = df_filtrado.copy()
        df_temporal = df_temporal.sort_values('date')
        
        # Crear figura
        fig = go.Figure()
        
        if tipo_linea == 'Media del equipo':
            # Calcular media por fecha
            df_media = df_temporal.groupby('date')[metrica_evol].mean().reset_index()
            df_media = df_media.sort_values('date')
            
            fig.add_trace(go.Bar(
                x=df_media['date'],
                y=df_media[metrica_evol],
                name='Media del equipo',
                marker_color=COLORES['primario'],
                text=[f"{v:.1f}" for v in df_media[metrica_evol]],
                textposition='outside',
                hovertemplate='<b>%{x|%d/%m/%Y}</b><br>' +
                             f'Media: %{{y:.1f}}<extra></extra>'
            ))
            
        elif tipo_linea == 'Por posición':
            # Cargar posiciones
            try:
                df_plantilla = cargar_plantilla_europa()
                df_temporal['posicion'] = df_temporal['player'].apply(
                    lambda x: mapear_posicion(x, df_plantilla)
                )
                
                posiciones = df_temporal['posicion'].unique()
                colores_pos = {
                    'Defensa': '#ef4444',
                    'Centrocampista': '#3b82f6',
                    'Delantero': '#22c55e'
                }
                
                for pos in posiciones:
                    if pos in colores_pos:
                        df_pos = df_temporal[df_temporal['posicion'] == pos]
                        df_pos_media = df_pos.groupby('date')[metrica_evol].mean().reset_index()
                        df_pos_media = df_pos_media.sort_values('date')
                        
                        fig.add_trace(go.Bar(
                            x=df_pos_media['date'],
                            y=df_pos_media[metrica_evol],
                            name=pos,
                            marker_color=colores_pos[pos],
                            text=[f"{v:.1f}" for v in df_pos_media[metrica_evol]],
                            textposition='outside',
                            hovertemplate=f'<b>%{{x|%d/%m/%Y}}</b><br>{pos}: %{{y:.1f}}<extra></extra>'
                        ))
            except:
                st.warning("⚠️ No se pudo cargar información de posiciones")
                
        elif tipo_linea == 'Top 5 jugadores':
            # Obtener top 5 jugadores por promedio
            df_promedios = df_temporal.groupby('player')[metrica_evol].mean().sort_values(ascending=False).head(5)
            
            for jugador in df_promedios.index:
                df_jug = df_temporal[df_temporal['player'] == jugador].sort_values('date')
                
                fig.add_trace(go.Bar(
                    x=df_jug['date'],
                    y=df_jug[metrica_evol],
                    name=jugador,
                    text=[f"{v:.1f}" for v in df_jug[metrica_evol]],
                    textposition='outside',
                    hovertemplate=f'<b>%{{x|%d/%m/%Y}}</b><br>{jugador}: %{{y:.1f}}<extra></extra>'
                ))
        
        elif tipo_linea == 'Todos los jugadores':
            jugadores = df_temporal['player'].unique()
            
            if len(jugadores) > 15:
                st.warning(f"⚠️ Hay {len(jugadores)} jugadores. El gráfico puede ser difícil de leer. Considera usar 'Top 5 jugadores'.")
            
            for jugador in jugadores:
                df_jug = df_temporal[df_temporal['player'] == jugador].sort_values('date')
                
                fig.add_trace(go.Bar(
                    x=df_jug['date'],
                    y=df_jug[metrica_evol],
                    name=jugador,
                    text=[f"{v:.0f}" for v in df_jug[metrica_evol]],
                    textposition='outside',
                    hovertemplate=f'<b>%{{x|%d/%m/%Y}}</b><br>{jugador}: %{{y:.1f}}<extra></extra>',
                    opacity=0.8
                ))
        
        else:  # Selección manual
            if jugadores_seleccionados_evol:
                for jugador in jugadores_seleccionados_evol:
                    df_jug = df_temporal[df_temporal['player'] == jugador].sort_values('date')
                    
                    if len(df_jug) > 0:
                        fig.add_trace(go.Bar(
                            x=df_jug['date'],
                            y=df_jug[metrica_evol],
                            name=jugador,
                            text=[f"{v:.1f}" for v in df_jug[metrica_evol]],
                            textposition='outside',
                            hovertemplate=f'<b>%{{x|%d/%m/%Y}}</b><br>{jugador}: %{{y:.1f}}<extra></extra>'
                        ))
        
        # Aplicar update_traces para texto
        fig.update_traces(
            textfont=dict(size=12, color='black'),
            textposition='outside',
            selector=dict(type='bar')
        )
        
        # Layout del gráfico
        fig.update_layout(
            title=f"Evolución de {metrica_evol_nombre} - {tipo_linea}",
            xaxis_title="Fecha",
            yaxis_title=metrica_evol_nombre,
            height=600,
            hovermode='x unified',
            barmode='group',
            xaxis=dict(
                tickformat='%d/%m',
                tickangle=-45
            ),
            uniformtext_minsize=11,
            uniformtext_mode='show'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Estadísticas de tendencia
        st.subheader("📊 Análisis de Tendencia")
        
        # Calcular tendencia según el tipo de visualización
        if tipo_linea == 'Media del equipo':
            # Media del equipo
            df_trend = df_temporal.groupby('date')[metrica_evol].mean().reset_index()
            df_trend = df_trend.sort_values('date')
            nombre_serie = "Media del equipo"
            
        elif tipo_linea == 'Por posición':
            # Calcular tendencia promediando todas las posiciones
            try:
                df_plantilla = cargar_plantilla_europa()
                df_temporal['posicion'] = df_temporal['player'].apply(
                    lambda x: mapear_posicion(x, df_plantilla)
                )
                df_trend = df_temporal.groupby('date')[metrica_evol].mean().reset_index()
                df_trend = df_trend.sort_values('date')
                nombre_serie = "Media de todas las posiciones"
            except:
                df_trend = df_temporal.groupby('date')[metrica_evol].mean().reset_index()
                df_trend = df_trend.sort_values('date')
                nombre_serie = "Media del equipo"
                
        elif tipo_linea == 'Top 5 jugadores':
            # Solo los Top 5 jugadores
            df_promedios = df_temporal.groupby('player')[metrica_evol].mean().sort_values(ascending=False).head(5)
            top5_jugadores = df_promedios.index.tolist()
            df_temp_top5 = df_temporal[df_temporal['player'].isin(top5_jugadores)]
            df_trend = df_temp_top5.groupby('date')[metrica_evol].mean().reset_index()
            df_trend = df_trend.sort_values('date')
            nombre_serie = f"Media Top 5: {', '.join(top5_jugadores)}"
            
        elif tipo_linea == 'Selección manual':
            # Solo los jugadores seleccionados
            if jugadores_seleccionados_evol and len(jugadores_seleccionados_evol) > 0:
                df_temp_sel = df_temporal[df_temporal['player'].isin(jugadores_seleccionados_evol)]
                df_trend = df_temp_sel.groupby('date')[metrica_evol].mean().reset_index()
                df_trend = df_trend.sort_values('date')
                nombre_serie = f"Media seleccionados: {', '.join(jugadores_seleccionados_evol)}"
            else:
                df_trend = df_temporal.groupby('date')[metrica_evol].mean().reset_index()
                df_trend = df_trend.sort_values('date')
                nombre_serie = "Media del equipo"
                
        else:  # Todos los jugadores
            df_trend = df_temporal.groupby('date')[metrica_evol].mean().reset_index()
            df_trend = df_trend.sort_values('date')
            nombre_serie = "Media de todos los jugadores"
        
        if len(df_trend) >= 2:
            valor_inicial = df_trend[metrica_evol].iloc[0]
            valor_final = df_trend[metrica_evol].iloc[-1]
            cambio = valor_final - valor_inicial
            cambio_pct = (cambio / valor_inicial * 100) if valor_inicial != 0 else 0
            
            # Mostrar de qué jugadores se calcula la tendencia
            st.caption(f"📍 Calculado sobre: **{nombre_serie}**")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Valor Inicial",
                    f"{valor_inicial:.1f}",
                    delta=None,
                    help=f"Fecha: {df_trend['date'].iloc[0].strftime('%d/%m/%Y')}"
                )
            
            with col2:
                st.metric(
                    "Valor Actual",
                    f"{valor_final:.1f}",
                    delta=None,
                    help=f"Fecha: {df_trend['date'].iloc[-1].strftime('%d/%m/%Y')}"
                )
            
            with col3:
                st.metric(
                    "Cambio Absoluto",
                    f"{cambio:+.1f}",
                    delta=f"{cambio_pct:+.1f}%"
                )
            
            with col4:
                tendencia = "📈 Mejorando" if cambio > 0 else "📉 Disminuyendo" if cambio < 0 else "➡️ Estable"
                st.metric(
                    "Tendencia",
                    tendencia,
                    delta=None
                )
            
            # Interpretación
            if abs(cambio_pct) >= 10:
                st.success(f"✅ Cambio significativo: {cambio_pct:+.1f}% en {metrica_evol_nombre}")
            elif abs(cambio_pct) >= 5:
                st.info(f"ℹ️ Cambio moderado: {cambio_pct:+.1f}% en {metrica_evol_nombre}")
            else:
                st.info(f"➡️ Cambio leve: {cambio_pct:+.1f}% en {metrica_evol_nombre}")



if __name__ == "__main__":
    main()