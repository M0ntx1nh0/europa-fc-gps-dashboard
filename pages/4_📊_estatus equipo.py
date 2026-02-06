"""
Página: Estatus del Equipo
Vista general y análisis del rendimiento colectivo
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import sys
from pathlib import Path
from utils.filtros import render_filtro_partidos

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

# Configuración de página (DEBE SER LO PRIMERO)
st.set_page_config(
    page_title=f"{PAGE_TITLE} - Estatus del Equipo",
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="collapsed"  # ← AÑADIDO
)


def main():
    # ==========================================
    # VERIFICAR AUTENTICACIÓN
    # ==========================================
    if not st.session_state.get('autenticado', False):
        st.warning("⚠️ Por favor, inicia sesión desde la página principal")
        st.info("👉 Ve a la app principal para iniciar sesión")
        st.stop()
    
    # ==========================================
    # RENDERIZAR SIDEBAR
    # ==========================================
    render_sidebar()  # ← CORREGIDO: Sin parámetros
    
    st.title("📊 Estatus del Equipo")
    st.markdown("Vista general del rendimiento colectivo")
    
    # ==========================================
    # VERIFICAR DATOS CARGADOS
    # ==========================================
    if not st.session_state.get('datos_cargados', False):
        st.warning("⚠️ No hay datos cargados")
        st.info("💡 Ve a la página principal y carga los datos desde Google Drive")
        st.stop()
    
    # ==========================================
    # OBTENER DATOS DE FORMA SEGURA
    # ==========================================
    df = st.session_state.get('df_procesado')  # ← CORREGIDO: Uso de .get()
    
    if df is None or len(df) == 0:
        st.error("⚠️ Error: datos no disponibles")
        st.stop()
    
    # ========================================
    # FILTROS INDEPENDIENTES
    # ========================================
    df_filtrado, modo_partido, info_filtro = render_filtro_partidos(df)
    
    st.markdown("---")
    
    # ========================================
    # CALCULAR MÉTRICAS DERIVADAS (si no existen)
    # ========================================
    
    # Calcular HSR Relativo si no existe
    if 'hsr_rel' not in df_filtrado.columns and 'hsr' in df_filtrado.columns and 'time' in df_filtrado.columns:
        df_filtrado['hsr_rel'] = (df_filtrado['hsr'] / df_filtrado['time']) * 90
        if 'hsr_rel' not in df.columns:
            df['hsr_rel'] = (df['hsr'] / df['time']) * 90
            st.session_state['df_procesado'] = df
    
    # Calcular Distancia Relativa si no existe
    if 'total_distance_rel' not in df_filtrado.columns and 'total_distance' in df_filtrado.columns and 'time' in df_filtrado.columns:
        df_filtrado['total_distance_rel'] = (df_filtrado['total_distance'] / df_filtrado['time']) * 90
        if 'total_distance_rel' not in df.columns:
            df['total_distance_rel'] = (df['total_distance'] / df['time']) * 90
            st.session_state['df_procesado'] = df
    
    # Calcular Sprints Relativos si no existe
    if 'sprints_rel' not in df_filtrado.columns and 'sprints' in df_filtrado.columns and 'time' in df_filtrado.columns:
        df_filtrado['sprints_rel'] = (df_filtrado['sprints'] / df_filtrado['time']) * 90
        if 'sprints_rel' not in df.columns:
            df['sprints_rel'] = (df['sprints'] / df['time']) * 90
            st.session_state['df_procesado'] = df
    
    # CORREGIDO: Crear diccionario de métricas disponibles
    metricas_disponibles = {v: k for k, v in METRICAS_DICT.items() if v in df_filtrado.columns}
    
    # Añadir métricas relativas si existen pero no están en METRICAS_DICT
    if 'hsr_rel' in df_filtrado.columns and 'hsr_rel' not in metricas_disponibles:
        metricas_disponibles['hsr_rel'] = 'HSR Relativo (90min)'
    
    if 'total_distance_rel' in df_filtrado.columns and 'total_distance_rel' not in metricas_disponibles:
        metricas_disponibles['total_distance_rel'] = 'Distancia Relativa (90min)'
    
    if 'sprints_rel' in df_filtrado.columns and 'sprints_rel' not in metricas_disponibles:
        metricas_disponibles['sprints_rel'] = 'Sprints Relativos (90min)'
    
    if len(metricas_disponibles) == 0:
        st.error("❌ No hay métricas disponibles en los datos")
        st.stop()
    
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
        
        st.markdown("### 📈 Configuración de Vista General")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            opciones_metricas = [col for col in metricas_disponibles.keys()]
            
            if len(opciones_metricas) == 0:
                st.error("❌ No hay métricas disponibles")
                st.stop()
            
            metrica_col = st.selectbox(
                "Métrica a analizar:",
                options=opciones_metricas,
                format_func=lambda x: metricas_disponibles[x],
                index=0,
                key='metrica_analizar',
                help="Métrica principal para este análisis"
            )
            
            metrica_nombre = metricas_disponibles[metrica_col]
        
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
        
        if metrica_col not in df_filtrado.columns:
            st.error(f"❌ La columna '{metrica_col}' no existe en los datos filtrados")
            st.stop()
        
        # Agrupar por jugador (promedio si son varios partidos)
        if modo_partido == 'Partido Específico':
            df_equipo = df_filtrado.copy()
        else:
            df_equipo = df_filtrado.groupby('player').agg({
                metrica_col: 'mean',
                'time': 'mean'
            }).reset_index()
        
        # ========================================
        # CORREGIDO: Calcular referencias MANUALMENTE sobre la métrica específica
        # ========================================
        referencias_manual = {
            'Media': df_equipo[metrica_col].mean(),
            'Mediana': df_equipo[metrica_col].median(),
            'P70': df_equipo[metrica_col].quantile(0.70),
            'P75': df_equipo[metrica_col].quantile(0.75),
            'P80': df_equipo[metrica_col].quantile(0.80),
            'P85': df_equipo[metrica_col].quantile(0.85),
            'P90': df_equipo[metrica_col].quantile(0.90),
            'P95': df_equipo[metrica_col].quantile(0.95),
            'Máximo': df_equipo[metrica_col].max(),
            'Mínimo': df_equipo[metrica_col].min()
        }
        
        # Métricas del equipo
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                f"Media {metrica_nombre}",
                f"{referencias_manual['Media']:.1f}",
                delta=None
            )
        
        with col2:
            st.metric(
                f"Máximo {metrica_nombre}",
                f"{referencias_manual['Máximo']:.1f}",
                delta=None
            )
        
        with col3:
            st.metric(
                f"Mínimo {metrica_nombre}",
                f"{referencias_manual['Mínimo']:.1f}",
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
        
        df_equipo_sorted = df_equipo.sort_values(metrica_col, ascending=True)
        
        if base_referencia == 'Por posición':
            try:
                df_plantilla = cargar_plantilla_europa()
                # CORREGIDO: Proteger mapeo de posiciones
                df_equipo_sorted['posicion'] = df_equipo_sorted['player'].apply(
                    lambda x: mapear_posicion(str(x), df_plantilla) if pd.notna(x) and str(x).strip() != '' and str(x) != '0' else 'Sin posición'
                )
                
                colores_posicion = {
                    'Defensa': '#ef4444',
                    'Centrocampista': '#3b82f6',
                    'Delantero': '#22c55e',
                    'Sin posición': '#9ca3af'
                }
                
                df_equipo_sorted['color'] = df_equipo_sorted['posicion'].map(colores_posicion)
                
            except Exception as e:
                st.warning(f"⚠️ No se pudo cargar información de posiciones: {e}")
                df_equipo_sorted['posicion'] = 'Sin posición'
                df_equipo_sorted['color'] = '#1f77b4'
        else:
            df_equipo_sorted['color'] = COLORES['primario']
        
        # Crear gráfico
        fig = go.Figure()
        
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
        
        # CORREGIDO: Usar referencias_manual
        colores_ref = {
            'Media': '#FFA500',
            'Mediana': '#9370DB',
            'P70': '#4169E1',
            'P75': '#4169E1',
            'P80': '#20B2AA',
            'P85': '#32CD32',
            'P90': '#FF4500',
            'P95': '#DC143C',
            'Máximo': '#8B0000'
        }
        
        # Estadístico principal
        if tipo_estadistico in referencias_manual:
            fig.add_vline(
                x=referencias_manual[tipo_estadistico],
                line_dash="solid",
                line_color=colores_ref.get(tipo_estadistico, '#FF0000'),
                line_width=3,
                annotation_text=f"🎯 {tipo_estadistico}: {referencias_manual[tipo_estadistico]:.1f}",
                annotation_position="top right",
                annotation=dict(
                    font=dict(size=12, color="white"),
                    bgcolor=colores_ref.get(tipo_estadistico, '#FF0000'),
                    borderpad=4
                )
            )
        
        # Referencias adicionales
        for ref_tipo in mostrar_referencias:
            if ref_tipo in referencias_manual and ref_tipo != tipo_estadistico:
                fig.add_vline(
                    x=referencias_manual[ref_tipo],
                    line_dash="dash",
                    line_color=colores_ref.get(ref_tipo, '#999999'),
                    line_width=2,
                    annotation_text=f"{ref_tipo}: {referencias_manual[ref_tipo]:.1f}",
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
        
        st.markdown("""
        **¿Qué muestra este gráfico?**
        
        El **histograma** muestra cómo se distribuyen los valores de una métrica en tu equipo.
        """)
        
        st.markdown("---")
        
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
        
        if modo_partido == 'Partido Específico':
            valores = df_filtrado[metrica_dist].dropna()
        else:
            valores = df_filtrado[metrica_dist].dropna()
        
        if len(valores) == 0:
            st.warning("⚠️ No hay datos para mostrar")
        else:
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
            
            fig = go.Figure()
            
            fig.add_trace(go.Histogram(
                x=valores,
                nbinsx=n_bins,
                marker_color=COLORES['primario'],
                opacity=0.7,
                name='Frecuencia',
                hovertemplate='Rango: %{x}<br>Frecuencia: %{y}<extra></extra>'
            ))
            
            fig.add_vline(
                x=valores.mean(),
                line_dash="solid",
                line_color='red',
                line_width=2,
                annotation_text=f"Media: {valores.mean():.1f}",
                annotation_position="top right"
            )
            
            fig.add_vline(
                x=valores.quantile(0.75),
                line_dash="dash",
                line_color='orange',
                line_width=2,
                annotation_text=f"P75: {valores.quantile(0.75):.1f}",
                annotation_position="top right"
            )
            
            fig.add_vline(
                x=valores.quantile(0.90),
                line_dash="dot",
                line_color='green',
                line_width=2,
                annotation_text=f"P90: {valores.quantile(0.90):.1f}",
                annotation_position="top left"
            )
            
            fig.update_layout(
                title=f"Histograma de {metrica_dist_nombre}",
                xaxis_title=f"{metrica_dist_nombre}",
                yaxis_title="Frecuencia",
                height=550,
                showlegend=False,
                bargap=0.1
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
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
            
            st.info(f"""
            **💡 Interpretación:**
            - **P90 ({valores.quantile(0.90):.1f})**: Solo el top 10% alcanza o supera este valor
            - **P75 ({valores.quantile(0.75):.1f})**: El top 25% del equipo está por encima
            - **Mediana ({valores.median():.1f})**: 50% del equipo está por encima y 50% por debajo
            """)

    
    # ========================================
    # TAB 2: COMPARATIVAS
    # ========================================
    
    with tab2:
        st.subheader("🎯 Análisis Comparativo")
        
        modo_comparativa = st.radio(
            "Modo de análisis:",
            options=['Scatter Plot (2 métricas)', 'Comparar Jugadores/Posiciones'],
            horizontal=True,
            key='modo_comparativa'
        )
        
        st.markdown("---")
        
        if modo_comparativa == 'Scatter Plot (2 métricas)':
            st.markdown("**Scatter Plot:** Analiza la relación entre dos métricas.")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                metrica_x = st.selectbox(
                    "Métrica Eje X:",
                    options=list(metricas_disponibles.keys()),
                    index=min(1, len(metricas_disponibles)-1),
                    format_func=lambda x: metricas_disponibles[x],
                    key='metrica_x_scatter'
                )
            
            with col2:
                metrica_y = st.selectbox(
                    "Métrica Eje Y:",
                    options=list(metricas_disponibles.keys()),
                    index=0,
                    format_func=lambda x: metricas_disponibles[x],
                    key='metrica_y_scatter'
                )
            
            with col3:
                filtro_posicion_scatter = st.selectbox(
                    "Filtrar por posición:",
                    options=['Todas', 'Defensa', 'Centrocampista', 'Delantero'],
                    index=0,
                    key='filtro_posicion_scatter'
                )
            
            with col4:
                mostrar_nombres = st.checkbox(
                    "Mostrar nombres",
                    value=True,
                    key='mostrar_nombres_scatter'
                )
            
            metrica_x_nombre = metricas_disponibles[metrica_x]
            metrica_y_nombre = metricas_disponibles[metrica_y]
            
            if metrica_x not in df_filtrado.columns or metrica_y not in df_filtrado.columns:
                st.error(f"❌ Una o ambas métricas no están disponibles")
                st.stop()
            
            # CORREGIDO: Siempre agrupar por jugador
            df_scatter = df_filtrado.groupby('player').agg({
                metrica_x: 'mean',
                metrica_y: 'mean',
                'time': 'mean'
            }).reset_index()
            
            df_scatter = df_scatter.dropna(subset=[metrica_x, metrica_y])
            
            if len(df_scatter) == 0:
                st.warning("⚠️ No hay datos suficientes")
            else:
                try:
                    df_plantilla = cargar_plantilla_europa()
                    # CORREGIDO: Proteger mapeo de posiciones
                    df_scatter['posicion'] = df_scatter['player'].apply(
                        lambda x: mapear_posicion(str(x), df_plantilla) if pd.notna(x) and str(x).strip() != '' and str(x) != '0' else 'Sin posición'
                    )
                except Exception as e:
                    st.warning(f"⚠️ No se pudo cargar posiciones: {e}")
                    df_scatter['posicion'] = 'Sin posición'
                
                if filtro_posicion_scatter != 'Todas':
                    df_scatter = df_scatter[df_scatter['posicion'] == filtro_posicion_scatter].copy()
                    
                    if len(df_scatter) == 0:
                        st.warning(f"⚠️ No hay jugadores de '{filtro_posicion_scatter}'")
                        st.stop()
                
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
                
                media_x = df_scatter[metrica_x].mean()
                media_y = df_scatter[metrica_y].mean()
                
                fig.add_vline(
                    x=media_x,
                    line_dash="dash",
                    line_color='gray',
                    annotation_text=f"Media X: {media_x:.1f}",
                    annotation_position="top"
                )
                
                fig.add_hline(
                    y=media_y,
                    line_dash="dash",
                    line_color='gray',
                    annotation_text=f"Media Y: {media_y:.1f}",
                    annotation_position="right"
                )
                
                fig.update_traces(marker=dict(size=12))
                
                fig.update_layout(
                    title=f"Relación: {metrica_y_nombre} vs {metrica_x_nombre}",
                    height=600,
                    hovermode='closest'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("📊 Análisis por Cuadrantes")
                
                df_scatter['cuadrante'] = '🟠 Bajo en ambas'
                df_scatter.loc[
                    (df_scatter[metrica_x] >= media_x) & (df_scatter[metrica_y] >= media_y),
                    'cuadrante'
                ] = '🟢 Alto en ambas'
                df_scatter.loc[
                    (df_scatter[metrica_x] >= media_x) & (df_scatter[metrica_y] < media_y),
                    'cuadrante'
                ] = f'🔵 Alto en {metrica_x_nombre}'
                df_scatter.loc[
                    (df_scatter[metrica_x] < media_x) & (df_scatter[metrica_y] >= media_y),
                    'cuadrante'
                ] = f'🔵 Alto en {metrica_y_nombre}'
                
                cuadrantes = df_scatter['cuadrante'].value_counts()
                
                col1, col2, col3, col4 = st.columns(4)
                
                for idx, (cuad, col) in enumerate(zip(cuadrantes.index, [col1, col2, col3, col4])):
                    with col:
                        st.metric(
                            cuad,
                            cuadrantes[cuad],
                            delta=f"{cuadrantes[cuad]/len(df_scatter)*100:.0f}%"
                        )
                
                with st.expander("👥 Ver jugadores por cuadrante"):
                    for cuad in cuadrantes.index:
                        st.markdown(f"**{cuad}:**")
                        jugadores = df_scatter[df_scatter['cuadrante'] == cuad]['player'].tolist()
                        st.write(", ".join([str(j) for j in jugadores]))
                        st.markdown("")
        
        else:  # Comparar Jugadores/Posiciones
            st.markdown("**Comparar:** Visualiza perfiles con Radar/Heatmap/Barras")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                modo_comparar = st.radio(
                    "Comparar por:",
                    options=['Jugadores individuales', 'Jugadores por posición', 'Posiciones (promedio)'],
                    key='modo_comparar',
                    help="Individuales: Selecciona jugadores específicos\nPor posición: Todos los jugadores agrupados por posición\nPromedio: Promedio de cada posición"
                )
            
            with col2:
                estadistico_comparar = st.selectbox(
                    "Estadística:",
                    options=['Media', 'Mediana', 'Máximo', 'Mínimo', 'P90'],
                    index=0,
                    key='estadistico_comparar'
                )
            
            with col3:
                # CORREGIDO: Filtrar opciones de visualización según modo
                if modo_comparar == 'Jugadores por posición':
                    opciones_viz = ['Heatmap', 'Gráfico de Barras']
                    tipo_viz = st.radio(
                        "Visualización:",
                        options=opciones_viz,
                        key='tipo_viz',
                        help="⚠️ Radar Chart no disponible para 'Jugadores por posición' (demasiados elementos)"
                    )
                else:
                    tipo_viz = st.radio(
                        "Visualización:",
                        options=['Radar/Spider Chart', 'Heatmap', 'Gráfico de Barras'],
                        key='tipo_viz'
                    )
            
            st.markdown("---")

            # INDICADOR VISUAL DEL ESTADÍSTICO ACTIVO
            st.info(f"📊 **Estadístico activo:** {estadistico_comparar} | **Modo:** {modo_comparar}")
            
            # ========================================
            # PREPARAR DATOS BASE - LIMPIEZA Y AGREGACIÓN
            # ========================================
                        
            # PASO 1: Limpiar datos inválidos
            df_limpio = df_filtrado.copy()

            # Filtrar filas con player inválido (NaN, '0', vacíos)
            df_limpio = df_limpio[df_limpio['player'].notna()]  # No NaN
            df_limpio = df_limpio[df_limpio['player'].astype(str).str.strip() != '']  # No vacíos
            df_limpio = df_limpio[df_limpio['player'].astype(str) != '0']  # No '0'
            df_limpio = df_limpio[df_limpio['player'].astype(str) != 'nan']  # No 'nan' como string

            if len(df_limpio) == 0:
                st.error("❌ No hay datos válidos después de filtrar jugadores inválidos")
                st.stop()

            # PASO 2: Agrupar por jugador (SIEMPRE, incluso en Partido Específico)
            # Esto evita duplicados de jugadores en el mismo partido
            estadistico_map = {
                'Media': 'mean',
                'Mediana': 'median',
                'Máximo': 'max',
                'Mínimo': 'min',
                'P90': lambda x: x.quantile(0.90)
            }

            agg_func = estadistico_map[estadistico_comparar]

            df_comp_base = df_limpio.groupby('player').agg({
                metrica: agg_func for metrica in metricas_disponibles.keys()
            }).reset_index()

            # Asegurar que player sea string
            df_comp_base['player'] = df_comp_base['player'].astype(str)
            
            col_sel, col_metricas = st.columns([2, 1])
            
            with col_sel:
                if modo_comparar == 'Jugadores individuales':
                    jugadores_disponibles = sorted(df_comp_base['player'].dropna().astype(str).unique())
                    
                    elementos_seleccionados = st.multiselect(
                        "Jugadores (máx 3):",
                        options=jugadores_disponibles,
                        default=jugadores_disponibles[:min(3, len(jugadores_disponibles))],
                        max_selections=3,
                        key='jugadores_comparar_visual'
                    )
                    
                    if len(elementos_seleccionados) < 2:
                        st.warning("⚠️ Selecciona al menos 2")
                        st.stop()
                    
                    df_comparacion = df_comp_base[df_comp_base['player'].isin(elementos_seleccionados)].copy()
                    df_comparacion['nombre'] = df_comparacion['player']
                    df_comparacion['grupo'] = df_comparacion['player']
                
                elif modo_comparar == 'Jugadores por posición':
                    try:
                        df_plantilla = cargar_plantilla_europa()
                        
                        # CORREGIDO: Proteger mapeo de posiciones
                        df_comp_base['posicion'] = df_comp_base['player'].apply(
                            lambda x: mapear_posicion(str(x), df_plantilla) if pd.notna(x) and str(x).strip() != '' and str(x) != '0' else 'Sin posición'
                        )
                        
                        elementos_seleccionados = st.multiselect(
                            "Seleccionar posiciones:",
                            options=['Defensa', 'Centrocampista', 'Delantero'],
                            default=['Defensa', 'Centrocampista', 'Delantero'],
                            key='posiciones_jugadores_visual',
                            help="Muestra todos los jugadores de las posiciones seleccionadas"
                        )
                        
                        if len(elementos_seleccionados) == 0:
                            st.warning("⚠️ Selecciona al menos 1 posición")
                            st.stop()
                        
                        df_comparacion = df_comp_base[df_comp_base['posicion'].isin(elementos_seleccionados)].copy()
                        
                        if len(df_comparacion) == 0:
                            st.warning("⚠️ No hay jugadores en las posiciones seleccionadas")
                            st.stop()
                        
                        df_comparacion['nombre'] = df_comparacion['player']
                        df_comparacion['grupo'] = df_comparacion['posicion']
                        
                    except Exception as e:
                        st.error(f"⚠️ Error al cargar posiciones: {e}")
                        st.stop()
                    
                else:  # Posiciones (promedio)
                    elementos_seleccionados = st.multiselect(
                        "Posiciones (máx 3):",
                        options=['Defensa', 'Centrocampista', 'Delantero'],
                        default=['Defensa', 'Centrocampista', 'Delantero'],
                        max_selections=3,
                        key='posiciones_comparar_visual'
                    )
                    
                    if len(elementos_seleccionados) < 2:
                        st.warning("⚠️ Selecciona al menos 2")
                        st.stop()
                    
                    try:
                        df_plantilla = cargar_plantilla_europa()
                        
                        # CORREGIDO: Usar df_comp_base que YA tiene la agregación por jugador según estadistico_comparar
                        df_temp = df_comp_base.copy()
                        
                        # Mapear posiciones (los jugadores ya están en df_comp_base, un registro por jugador)
                        df_temp['posicion'] = df_temp['player'].apply(
                            lambda x: mapear_posicion(str(x), df_plantilla) if pd.notna(x) and str(x).strip() != '' and str(x) != '0' else 'Sin posición'
                        )
                        
                        # CORREGIDO: Agrupar por posición - ahora promedia el estadístico de cada jugador
                        # df_comp_base ya contiene el estadístico seleccionado (Media, Máximo, etc.) por jugador
                        # Aquí promediamos esos estadísticos por posición
                        df_comparacion = df_temp.groupby('posicion').agg({
                            metrica: 'mean' for metrica in metricas_disponibles.keys()
                        }).reset_index()
                        
                        df_comparacion = df_comparacion[df_comparacion['posicion'].isin(elementos_seleccionados)].copy()
                        df_comparacion['nombre'] = df_comparacion['posicion']
                        df_comparacion['grupo'] = df_comparacion['posicion']
                        
                        if len(df_comparacion) == 0:
                            st.warning("⚠️ Sin datos")
                            st.stop()
                            
                    except Exception as e:
                        st.error(f"⚠️ Error: {e}")
                        st.stop()
            
            with col_metricas:
                metricas_comparar = st.multiselect(
                    "Métricas:",
                    options=list(metricas_disponibles.keys()),
                    default=[m for m in ['hsr', 'total_distance', 'sprints', 'max_speed'] if m in metricas_disponibles.keys()][:4],
                    format_func=lambda x: metricas_disponibles[x],
                    key='metricas_comparar_visual'
                )
                
                if len(metricas_comparar) < 3 and tipo_viz == 'Radar/Spider Chart':
                    st.warning("⚠️ Radar requiere 3+ métricas")
                    st.stop()
                            
            st.markdown("---")
            
            # ===== RADAR CHART =====
            if tipo_viz == 'Radar/Spider Chart':
                st.subheader("🕸️ Radar Chart")
                
                # Limitar número de elementos
                if len(df_comparacion) > 6:
                    st.warning(f"⚠️ Demasiados elementos ({len(df_comparacion)}) para Radar Chart. Mostrando solo los primeros 6.")
                    df_comparacion = df_comparacion.head(6)
                
                rangos_metricas = {}
                for metrica in metricas_comparar:
                    valores = df_comparacion[metrica]
                    rangos_metricas[metrica] = {
                        'min': valores.min(),
                        'max': valores.max()
                    }
                
                params = [metricas_disponibles[m] for m in metricas_comparar]
                low = [rangos_metricas[m]['min'] for m in metricas_comparar]
                high = [rangos_metricas[m]['max'] for m in metricas_comparar]
                
                valores_jugadores = []
                nombres_jugadores = []
                
                for idx, (df_idx, row) in enumerate(df_comparacion.iterrows()):
                    valores = [row[m] for m in metricas_comparar]
                    valores_jugadores.append(valores)
                    nombres_jugadores.append(row['nombre'])
                
                colores_individuales = [
                    {'face': '#1E88E5', 'edge': '#0D47A1'},
                    {'face': '#FF6F00', 'edge': '#E65100'},
                    {'face': '#43A047', 'edge': '#1B5E20'},
                    {'face': '#E53935', 'edge': '#C62828'},
                    {'face': '#8E24AA', 'edge': '#6A1B9A'},
                    {'face': '#00ACC1', 'edge': '#00838F'}
                ]
                
                try:
                    from mplsoccer import Radar
                    import matplotlib.pyplot as plt
                    
                    radar = Radar(
                        params, 
                        low, 
                        high,
                        round_int=[False]*len(params),
                        num_rings=4,
                        ring_width=1,
                        center_circle_radius=1
                    )
                    
                    fig, ax = radar.setup_axis(figsize=(9, 9), facecolor='white')
                    fig.set_dpi(150)
                    
                    rings_inner = radar.draw_circles(
                        ax=ax, 
                        facecolor='#f0f0f0', 
                        edgecolor='#cccccc',
                        linewidth=1
                    )
                    
                    vertices_list = []
                    for idx, valores in enumerate(valores_jugadores):
                        color = colores_individuales[idx % len(colores_individuales)]
                        
                        radar_poly, vertices = radar.draw_radar_solid(
                            valores, 
                            ax=ax,
                            kwargs={
                                'facecolor': color['face'],
                                'alpha': 0.35,
                                'edgecolor': color['edge'],
                                'lw': 2.5
                            }
                        )
                        
                        vertices_list.append((vertices, color))
                    
                    for vertices, color in vertices_list:
                        ax.scatter(
                            vertices[:, 0], 
                            vertices[:, 1],
                            c=color['face'], 
                            edgecolors=color['edge'], 
                            marker='o', 
                            s=100,
                            zorder=2,
                            linewidth=1.5
                        )
                    
                    range_labels = radar.draw_range_labels(ax=ax, fontsize=8)
                    param_labels = radar.draw_param_labels(ax=ax, fontsize=10)
                    
                    title_text = f"Comparativa ({estadistico_comparar}): {', '.join(nombres_jugadores[:3])}"
                    if len(nombres_jugadores) > 3:
                        title_text += f" (+{len(nombres_jugadores)-3} más)"
                    
                    ax.text(
                        0.5, 1.12, title_text,
                        horizontalalignment='center',
                        verticalalignment='center',
                        transform=ax.transAxes,
                        fontsize=11,
                        fontweight='bold'
                    )
                    
                    # Leyenda
                    legend_elements = []
                    from matplotlib.patches import Patch
                    for idx, nombre in enumerate(nombres_jugadores):
                        color = colores_individuales[idx % len(colores_individuales)]
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
                        fontsize=8
                    )
                    
                    plt.tight_layout()
                    st.pyplot(fig, use_container_width=False)
                    plt.close()
                    
                except ImportError:
                    st.error("⚠️ mplsoccer no está instalado. Usa: pip install mplsoccer")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            
            # ===== HEATMAP =====
            elif tipo_viz == 'Heatmap':
                st.subheader("🌡️ Heatmap - Tabla de Calor")
                
                # Crear el gráfico primero
                matriz = []
                nombres = []
                
                for idx, (df_idx, row) in enumerate(df_comparacion.iterrows()):
                    valores = [row[m] for m in metricas_comparar]
                    matriz.append(valores)
                    nombres.append(row['nombre'])
                
                nombres_metricas = [metricas_disponibles[m] for m in metricas_comparar]
                
                matriz_norm = np.array(matriz).T
                matriz_norm_scaled = []
                
                for i, metrica_vals in enumerate(matriz_norm):
                    val_min = metrica_vals.min()
                    val_max = metrica_vals.max()
                    
                    if val_max > val_min:
                        norm_vals = ((metrica_vals - val_min) / (val_max - val_min)) * 100
                    else:
                        norm_vals = np.full_like(metrica_vals, 50)
                    
                    matriz_norm_scaled.append(norm_vals)
                
                matriz_norm_scaled = np.array(matriz_norm_scaled).T
                
                fig = go.Figure(data=go.Heatmap(
                    z=matriz_norm_scaled,
                    x=nombres_metricas,
                    y=nombres,
                    colorscale='RdYlGn',
                    text=np.array(matriz).round(1),
                    texttemplate='%{text}',
                    textfont={"size": 10 if len(nombres) > 5 else 12},
                    colorbar=dict(
                        title="Escala<br>Normalizada",
                        tickvals=[0, 25, 50, 75, 100],
                        ticktext=['Bajo<br>(0)', '25', 'Medio<br>(50)', '75', 'Alto<br>(100)']
                    ),
                    hovertemplate='<b>%{y}</b><br><b>%{x}</b><br>Valor real: %{text}<br>Normalizado: %{z:.1f}/100<br><extra></extra>'
                ))
                
                fig.update_layout(
                    title=f"Heatmap ({estadistico_comparar}) - {modo_comparar}",
                    height=max(400, len(nombres) * 35),
                    xaxis_title="Métrica",
                    yaxis_title="Jugador" if modo_comparar != 'Posiciones (promedio)' else "Posición"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # CORREGIDO: Explicación DESPUÉS del gráfico
                with st.expander("📖 ¿Cómo interpretar el Heatmap?"):
                    st.markdown("""
                    **📊 Interpretación de colores:**
                    
                    - **🟢 Verde (75-100)**: Rendimiento **excelente** en esa métrica (entre los mejores del grupo)
                    - **🟡 Amarillo (50-75)**: Rendimiento **bueno** (por encima del promedio)
                    - **🟠 Naranja (25-50)**: Rendimiento **medio-bajo** (por debajo del promedio)
                    - **🔴 Rojo (0-25)**: Rendimiento **bajo** (entre los más bajos del grupo)
                    
                    **⚙️ Cálculo de colores (normalización por columna):**
                    
                    1. Para cada métrica, se identifica el **valor mínimo** y **máximo** entre los seleccionados
                    2. Cada valor se convierte a escala 0-100 según su posición entre mín-máx
                    3. **Números** = valores reales (ej: 650m de HSR)
                    4. **Colores** = cómo se compara con el resto en esa métrica
                    
                    **💡 Ejemplo:**
                    - Jugador A: 650 HSR → Máximo del grupo → Verde (100/100)
                    - Jugador B: 525 HSR → Punto medio → Amarillo (~50/100)
                    - Jugador C: 400 HSR → Mínimo del grupo → Rojo (0/100)
                    
                    **👁️ Ventaja del Heatmap:**
                    Permite comparar métricas con escalas muy diferentes (ej: sprints ~30 vs distancia ~8000) en la misma visualización.
                    """)
            
            # ===== GRÁFICO DE BARRAS =====
            else:
                st.subheader("📊 Gráfico de Barras - Comparación Directa")
                
                nombres = []
                grupos = []
                datos_por_metrica = {metricas_disponibles[m]: [] for m in metricas_comparar}
                
                for idx, (df_idx, row) in enumerate(df_comparacion.iterrows()):
                    nombres.append(row['nombre'])
                    grupos.append(row.get('grupo', row['nombre']))
                    for metrica in metricas_comparar:
                        datos_por_metrica[metricas_disponibles[metrica]].append(row[metrica])
                
                # Colores según grupo
                colores_grupo = {
                    'Defensa': '#ef4444',
                    'Centrocampista': '#3b82f6',
                    'Delantero': '#22c55e'
                }
                
                colores_individuales = ['#1E88E5', '#FF6F00', '#43A047', '#E53935', '#8E24AA', '#00ACC1']
                
                # CORREGIDO: Si solo hay una posición seleccionada, usar colores individuales
                posiciones_unicas = len(set(grupos))
                
                if modo_comparar == 'Jugadores por posición' and posiciones_unicas == 1:
                    # Una sola posición → colores individuales por jugador
                    colores_jugadores = [colores_individuales[i % len(colores_individuales)] for i in range(len(nombres))]
                    usar_nombres_en_eje = True
                elif modo_comparar == 'Jugadores por posición':
                    # Múltiples posiciones → color por posición
                    colores_jugadores = [colores_grupo.get(g, '#9ca3af') for g in grupos]
                    usar_nombres_en_eje = False
                else:
                    colores_jugadores = [colores_individuales[i % len(colores_individuales)] for i in range(len(nombres))]
                    usar_nombres_en_eje = False
                
                from plotly.subplots import make_subplots
                
                n_metricas = len(metricas_comparar)
                
                fig = make_subplots(
                    rows=1, 
                    cols=n_metricas,
                    subplot_titles=[metricas_disponibles[m] for m in metricas_comparar],
                    horizontal_spacing=0.10,
                    specs=[[{"type": "bar"}] * n_metricas]
                )
                
                # CORREGIDO: Si hay una sola posición, mostrar nombres en el eje X
                for col_idx, (metrica, metrica_nombre) in enumerate(datos_por_metrica.items(), start=1):
                    
                    for jug_idx, (nombre, valor) in enumerate(zip(nombres, datos_por_metrica[metrica])):
                        fig.add_trace(
                            go.Bar(
                                name=nombre,
                                x=[nombre if usar_nombres_en_eje else metrica],
                                y=[valor],
                                text=[f"{valor:.1f}"],
                                textposition='outside',
                                marker_color=colores_jugadores[jug_idx],
                                showlegend=False,
                                legendgroup=nombre,
                                hovertemplate=f'<b>{nombre}</b><br>{metrica}: %{{y:.1f}}<br><extra></extra>'
                            ),
                            row=1,
                            col=col_idx
                        )
                
                fig.update_traces(
                    textfont=dict(size=11, color='black'),
                    textposition='outside',
                    selector=dict(type='bar')
                )
                
                fig.update_layout(
                    title=f"Comparativa ({estadistico_comparar}) - {modo_comparar}",
                    height=500,
                    barmode='group',
                    showlegend=False,
                    uniformtext_minsize=10,
                    uniformtext_mode='show'
                )
                
                # CORREGIDO: Rotar etiquetas del eje X si son nombres
                if usar_nombres_en_eje:
                    for i in range(1, n_metricas + 1):
                        fig.update_xaxes(
                            tickangle=-45,
                            tickfont=dict(size=9),
                            row=1,
                            col=i
                        )
                else:
                    fig.update_xaxes(showticklabels=False)
                
                for i in range(1, n_metricas + 1):
                    fig.update_yaxes(title_text="Valor", row=1, col=i)
                
                st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de valores
            st.subheader("📊 Tabla de Valores Reales")
            
            df_tabla_valores = df_comparacion[['nombre'] + metricas_comparar].copy()
            
            # Añadir columna de grupo si es "Por posición"
            if modo_comparar == 'Jugadores por posición':
                df_tabla_valores.insert(1, 'Posición', df_comparacion['grupo'])
            
            df_tabla_valores.columns = ['Jugador'] + (['Posición'] if modo_comparar == 'Jugadores por posición' else []) + [metricas_disponibles[m] for m in metricas_comparar]
            
            for col in df_tabla_valores.columns[1:] if modo_comparar != 'Jugadores por posición' else df_tabla_valores.columns[2:]:
                df_tabla_valores[col] = df_tabla_valores[col].round(1)
            
            st.dataframe(df_tabla_valores, use_container_width=True, hide_index=True, height=min(400, len(df_tabla_valores) * 35 + 50))
    
    # ========================================
    # TAB 3: EVOLUCIÓN TEMPORAL
    # ========================================
    
    with tab3:
        st.subheader("📉 Evolución Temporal")
        
        col1, col2 = st.columns(2)
        
        with col1:
            metrica_evol = st.selectbox(
                "Métrica:",
                options=list(metricas_disponibles.keys()),
                format_func=lambda x: metricas_disponibles[x],
                key='metrica_evolucion'
            )
        
        with col2:
            tipo_linea = st.selectbox(
                "Mostrar:",
                options=['Media del equipo', 'Top 5 jugadores'],
                index=0,
                key='tipo_linea_evol'
            )
        
        metrica_evol_nombre = metricas_disponibles[metrica_evol]
        
        df_temporal = df_filtrado.copy()
        df_temporal = df_temporal.sort_values('date')
        
        fig = go.Figure()
        
        if tipo_linea == 'Media del equipo':
            df_media = df_temporal.groupby('date')[metrica_evol].mean().reset_index()
            df_media = df_media.sort_values('date')
            
            fig.add_trace(go.Bar(
                x=df_media['date'],
                y=df_media[metrica_evol],
                name='Media',
                marker_color=COLORES['primario'],
                text=[f"{v:.1f}" for v in df_media[metrica_evol]],
                textposition='outside',
                hovertemplate='<b>%{x|%d/%m/%Y}</b><br>Media: %{y:.1f}<extra></extra>'
            ))
        else:
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
        
        fig.update_traces(
            textfont=dict(size=12, color='black'),
            textposition='outside',
            selector=dict(type='bar')
        )
        
        fig.update_layout(
            title=f"Evolución de {metrica_evol_nombre}",
            xaxis_title="Fecha",
            yaxis_title=metrica_evol_nombre,
            height=600,
            hovermode='x unified',
            barmode='group',
            xaxis=dict(tickformat='%d/%m', tickangle=-45),
            uniformtext_minsize=11,
            uniformtext_mode='show'
        )
        
        st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()