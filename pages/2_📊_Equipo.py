"""
Página Equipo - Análisis de Equipo
v1.7 - Con filtros de posición, ordenamiento y sistema de colores
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
from pathlib import Path

# Añadir directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from config import PAGE_TITLE, PAGE_ICON, LAYOUT, METRICAS_DICT, COLORES
from utils import (calcular_referencias_normalizadas, filtrar_por_fechas, 
                   filtrar_por_partido, calcular_estadisticas_partido,
                   obtener_referencia_metrica, calcular_evolucion_temporal,
                   crear_dashboard_player_cards, render_sidebar,
                   cargar_plantilla_europa, mapear_posicion,
                   calcular_z_score, clasificar_rendimiento)

# Configuración
st.set_page_config(
    page_title=f"{PAGE_TITLE} - Equipo",
    page_icon=PAGE_ICON,
    layout=LAYOUT
)

def filtrar_por_posicion(df, posicion, df_plantilla):
    """
    Filtra jugadores por posición usando datos de plantilla
    
    Args:
        df: DataFrame con datos GPS
        posicion: 'Todas', 'Defensa', 'Centrocampista', 'Delantero'
        df_plantilla: DataFrame con plantilla Excel
        
    Returns:
        DataFrame filtrado
    """
    if posicion == 'Todas':
        return df
    
    # Obtener lista de jugadores de esa posición
    jugadores_posicion = df_plantilla[df_plantilla['Posición'] == posicion]['Jugador GPS'].tolist()
    
    # Filtrar dataframe
    df_filtrado = df[df['player'].isin(jugadores_posicion)]
    
    return df_filtrado


def ordenar_jugadores(df, criterio):
    """
    Ordena jugadores según criterio seleccionado
    
    Args:
        df: DataFrame con datos
        criterio: str con el criterio de ordenamiento
        
    Returns:
        Lista de jugadores ordenados
    """
    if criterio == 'Tiempo jugado':
        return df.sort_values('time', ascending=False)['player'].tolist()
    
    elif criterio == 'HSR':
        return df.sort_values('hsr', ascending=False)['player'].tolist()
    
    elif criterio == 'Distancia Total':
        return df.sort_values('total_distance', ascending=False)['player'].tolist()
    
    elif criterio == 'Sprints':
        return df.sort_values('sprints', ascending=False)['player'].tolist()
    
    elif criterio == 'Velocidad Máxima':
        return df.sort_values('max_speed', ascending=False)['player'].tolist()
    
    elif criterio == 'Alfabético':
        return sorted(df['player'].tolist())
    
    else:
        # Por defecto: tiempo jugado
        return df.sort_values('time', ascending=False)['player'].tolist()


def main():
    # Renderizar sidebar común
    render_sidebar()
    
    st.title("📊 Análisis de Equipo")
    
    # Verificar datos
    if not st.session_state.get('datos_cargados', False):
        st.warning("⚠️ No hay datos cargados. Por favor, carga los datos desde la página principal.")
        st.stop()
    
    # Cargar plantilla Excel
    try:
        df_plantilla = cargar_plantilla_europa()
    except Exception as e:
        st.error(f"❌ Error al cargar plantilla: {e}")
        st.info("📋 Verifica que el archivo Excel exista en: /Users/macmontxinho/Desktop/Teams/Europa/Plantillas CE Europa.XLSX")
        df_plantilla = None
    
    # Obtener datos
    df = st.session_state.df_procesado
    fecha_desde = st.session_state.get('fecha_desde')
    fecha_hasta = st.session_state.get('fecha_hasta')
    partido_seleccionado = st.session_state.get('partido_seleccionado')
    
    # Filtrar datos
    df_rango = filtrar_por_fechas(df, fecha_desde, fecha_hasta)
    df_partido = filtrar_por_partido(df_rango, partido_seleccionado)
    
    if len(df_partido) == 0:
        st.error("❌ No hay datos para el partido seleccionado")
        st.stop()
    
    # ========================================
    # SECCIÓN 1: DASHBOARD DEL EQUIPO
    # ========================================
    
    st.markdown("## 🏆 Dashboard del Equipo")
    
    # ========================================
    # SELECTORES DE FILTROS (4 columnas)
    # ========================================
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        n_partidos = st.selectbox(
            "Promediar últimos:",
            options=[3, 5, 10],
            format_func=lambda x: f"{x} partidos",
            key='n_partidos_dashboard',
            help="Número de partidos a promediar"
        )
    
    with col2:
        if df_plantilla is not None:
            posicion_filtro = st.selectbox(
                "Posición:",
                options=['Todas', 'Defensa', 'Centrocampista', 'Delantero'],
                key='filtro_posicion',
                help="Filtrar jugadores por posición"
            )
        else:
            posicion_filtro = 'Todas'
            st.info("⚠️ Plantilla no disponible")
    
    with col3:
        criterio_orden = st.selectbox(
            "Ordenar por:",
            options=['Tiempo jugado', 'HSR', 'Distancia Total', 
                    'Sprints', 'Velocidad Máxima', 'Alfabético'],
            key='orden_cards',
            help="Ordenar jugadores por métrica"
        )
    
    with col4:
        referencia_color = st.selectbox(
            "Colorear vs:",
            options=['Media', 'Mediana', 'P70', 'P75', 'P80', 'P85', 'P90', 'P95'],
            index=0,  # Media por defecto
            key='ref_color',
            help="Referencia para colorear métricas"
        )
    
    # ========================================
    # AYUDA: EXPANDER CON EXPLICACIÓN DETALLADA
    # ========================================
    
    with st.expander("ℹ️ **Ayuda: ¿Cómo funcionan los filtros y colores?**", expanded=False):
        
        # Sección: Filtros
        st.markdown("""
        ### 📊 **GUÍA DE FILTROS**
        
        #### 🏆 **Promediar últimos:**
        Calcula el promedio de las métricas usando los últimos N partidos.
        - **3 partidos**: Tendencia más reciente
        - **5 partidos**: Balance entre reciente y estabilidad
        - **10 partidos**: Visión más estable de rendimiento
        
        #### ⚽ **Posición:**
        Filtra las player cards por posición del jugador (según plantilla Excel).
        - **Todas**: Muestra todos los jugadores
        - **Defensa**: Solo defensas
        - **Centrocampista**: Solo centrocampistas
        - **Delantero**: Solo delanteros
        
        #### 📈 **Ordenar por:**
        Define el orden de las player cards (mayor → menor).
        - **Tiempo jugado**: Quien más minutos jugó primero
        - **HSR**: Quien más metros de alta intensidad
        - **Distancia Total**: Quien más metros recorrió
        - **Sprints**: Quien más sprints realizó
        - **Velocidad Máxima**: Quien alcanzó mayor velocidad
        - **Alfabético**: Orden A-Z
        
        #### 🎨 **Colorear vs:**
        Define el **nivel de exigencia** para los colores. Esta es la referencia que determina quién es 🟢 verde.
        """)
        
        st.markdown("---")
        
        # Sección: Referencias
        st.markdown("""
        ### 🎯 **¿QUÉ SIGNIFICA CADA REFERENCIA?**
        
        Las referencias son **percentiles** calculados sobre todos los datos del rango de fechas:
        
        | Referencia | Significado | Top % | Cuándo usar |
        |------------|-------------|-------|-------------|
        | **Media** | Promedio del equipo | ~50% | Análisis equilibrado ⭐ |
        | **Mediana** | Valor central | ~50% | Evitar outliers |
        | **P70** | Percentil 70 | Top 30% | Exigencia moderada |
        | **P75** | Percentil 75 | Top 25% | Buen rendimiento |
        | **P80** | Percentil 80 | Top 20% | Rendimiento alto |
        | **P85** | Percentil 85 | Top 15% | Muy buen rendimiento |
        | **P90** | Percentil 90 | Top 10% | Excelente rendimiento |
        | **P95** | Percentil 95 | Top 5% | Solo élite 🏆 |
        
        **💡 Tip:** Empieza con **Media** para ver el panorama general. Sube a P90/P95 para identificar a la élite.
        """)
        
        st.markdown("---")
        
        # Sección: Sistema de colores
        st.markdown("""
        ### 🎨 **SISTEMA DE COLORES (4 NIVELES)**
        
        Los colores se asignan comparando el valor del jugador con las referencias:
        """)
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("""
            **🟢 VERDE - Excelente**
            - Cumple o supera la referencia elegida
            - Es el objetivo a alcanzar
            
            **🔵 AZUL - Muy Bueno**
            - Sobre la Media del equipo
            - Pero bajo la referencia elegida
            """)
        
        with col_b:
            st.markdown("""
            **⚪ GRIS - Normal**
            - Entre P25 y Media
            - Rendimiento estándar
            
            **🟠 NARANJA - Mejorable**
            - Bajo P25 (percentil 25)
            - Área de oportunidad
            """)
        
        st.markdown("---")
        
        # Sección: Ejemplos prácticos
        st.markdown(f"""
        ### 📊 **EJEMPLOS PRÁCTICOS**
        
        **Actualmente coloreando vs: {referencia_color}**
        
        Imagina que un jugador tiene **280m de HSR** en un partido:
        """)
        
        # Tabla de ejemplos
        ejemplo_data = {
            'Referencia': ['Media', 'Media', 'P90', 'P90', 'P95'],
            'Valor Ref.': ['250m', '250m', '350m', '350m', '380m'],
            'HSR Jugador': ['280m', '220m', '280m', '360m', '280m'],
            'Color': ['🟢 Verde', '⚪ Gris', '🔵 Azul', '🟢 Verde', '🟠 Naranja'],
            'Por qué': [
                '280 > 250 (Media)',
                '220 < 250 (Media)',
                '280 > 250 (Media) pero < 350 (P90)',
                '360 > 350 (P90)',
                '280 < 350 (Media del dataset) < 380 (P95)'
            ]
        }
        
        df_ejemplo = pd.DataFrame(ejemplo_data)
        st.dataframe(df_ejemplo, use_container_width=True, hide_index=True)
        
        st.markdown("""
        ### 🎯 **ESTRATEGIAS DE USO**
        
        **Para MOTIVAR al equipo:**
        - Usa **Media** o **Mediana** → ~50% serán verdes ✅
        - Muestra que muchos están sobre el promedio
        
        **Para IDENTIFICAR ÉLITE:**
        - Usa **P90** o **P95** → Solo los mejores serán verdes 🏆
        - Identifica quién está realmente destacando
        
        **Para ANÁLISIS GENERAL:**
        - Usa **P75** o **P80** → Balance entre exigencia y motivación ⚖️
        
        **Para DETECTAR MEJORAS:**
        - Mira los 🟠 naranjas en cualquier referencia
        - Identifica áreas de trabajo específicas
        """)
        
        st.markdown("---")
        
        st.info("💡 **Recuerda:** Los colores son relativos al equipo y rango de fechas. No hay colores 'malos', solo información sobre dónde está cada jugador respecto a la referencia elegida.")
    
    # ========================================
    # APLICAR FILTROS
    # ========================================
    
    # Filtrar por posición
    if df_plantilla is not None and posicion_filtro != 'Todas':
        df_partido_filtrado = filtrar_por_posicion(df_partido, posicion_filtro, df_plantilla)
        df_rango_filtrado = filtrar_por_posicion(df_rango, posicion_filtro, df_plantilla)
    else:
        df_partido_filtrado = df_partido
        df_rango_filtrado = df_rango
    
    # Verificar si hay jugadores después del filtro
    if len(df_partido_filtrado) == 0:
        st.warning(f"⚠️ No hay jugadores de posición '{posicion_filtro}' en este partido")
        st.stop()
    
    # Mensaje informativo
    total_jugadores = len(df_partido_filtrado)
    if posicion_filtro == 'Todas':
        st.info(f"📊 Mostrando **{total_jugadores} jugadores** - Ordenados por: **{criterio_orden}** - Coloreado vs: **{referencia_color}**")
    else:
        st.info(f"📊 Mostrando **{total_jugadores} {posicion_filtro}{'s' if total_jugadores > 1 else ''}** - Ordenados por: **{criterio_orden}** - Coloreado vs: **{referencia_color}**")
    
    # ========================================
    # DASHBOARD CON PLAYER CARDS
    # ========================================
    
    # Calcular referencias normalizadas para colores
    df_referencias = calcular_referencias_normalizadas(df_rango_filtrado)
    
    # Dashboard con filtros aplicados
    crear_dashboard_player_cards(
        df_partido=df_partido_filtrado,
        df_rango=df_rango_filtrado,
        n_partidos=n_partidos,
        criterio_orden=criterio_orden,
        df_plantilla=df_plantilla,
        df_referencias=df_referencias,
        referencia_seleccionada=referencia_color
    )
    
    # Separador grande
    st.markdown("---")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ========================================
    # SECCIÓN 2: CONFIGURACIÓN DE ANÁLISIS
    # ========================================
    
    st.markdown("## 📊 Configuración de Análisis Detallado")
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        metrica_nombre = st.selectbox(
            "Selecciona la métrica a analizar:",
            options=list(METRICAS_DICT.keys()),
            key='metrica_equipo',
            help="Esta métrica se usará en los análisis detallados de abajo"
        )
        metrica_col = METRICAS_DICT[metrica_nombre]
    
    with col2:
        # Info del partido (usar df_partido original, no filtrado)
        st.info(f"**Partido:** {df_partido['session'].iloc[0]}  \n**Fecha:** {partido_seleccionado.strftime('%d/%m/%Y')}  \n**Jugadores:** {len(df_partido)}")
    
    st.markdown("---")
    
    # ========================================
    # SECCIÓN 3: TABS CON ANÁLISIS DETALLADOS
    # ========================================
    
    # NOTA: Las tabs usan datos SIN filtro de posición (análisis completo del equipo)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Análisis del Partido", 
        "🏆 Ranking del Partido",
        "📈 Evolución Temporal", 
        "📋 Datos Detallados"
    ])
    
    # TAB 1: ANÁLISIS DEL PARTIDO
    with tab1:
        col1, col2 = st.columns(2)
        
        # Estadísticas del partido
        with col1:
            st.subheader("📈 Datos del Partido")
            
            stats_partido = calcular_estadisticas_partido(df_partido, metrica_col)
            
            if stats_partido:
                col_a, col_b = st.columns(2)
                
                with col_a:
                    st.metric("Media", f"{stats_partido['media']:.2f}")
                    st.metric("Mediana", f"{stats_partido['mediana']:.2f}")
                    st.metric("Desv. Std", f"{stats_partido['desv_std']:.2f}")
                
                with col_b:
                    st.metric("Mínimo", f"{stats_partido['min']:.2f}")
                    st.metric("Máximo", f"{stats_partido['max']:.2f}")
                    st.metric("Jugadores", stats_partido['count'])
        
        # Referencia
        with col2:
            st.subheader("🎯 Referencia (94 min)")
            
            if df_referencias is not None:
                ref = obtener_referencia_metrica(df_referencias, metrica_col)
                
                if ref is not None:
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        st.metric("Media", f"{ref['Media']:.2f}")
                        st.metric("Mediana", f"{ref['Mediana']:.2f}")
                        st.metric("Desv. Std", f"{ref['Desv_Std']:.2f}")
                    
                    with col_b:
                        st.metric("P90", f"{ref['P90']:.2f}")
                        st.metric("P95", f"{ref['P95']:.2f}")
                        st.metric("Registros", ref['Count'])
                else:
                    st.warning("No hay referencia para esta métrica")
            else:
                st.warning("No hay referencias disponibles")
        
        st.markdown("---")
        
        # Gráfico comparativo
        st.subheader("📊 Comparación: Partido vs Referencia")
        
        if stats_partido and df_referencias is not None:
            ref = obtener_referencia_metrica(df_referencias, metrica_col)
            
            if ref is not None:
                fig = go.Figure()
                
                # Barras del partido
                fig.add_trace(go.Bar(
                    name='Partido',
                    x=['Media', 'Mediana', 'Máximo'],
                    y=[stats_partido['media'], stats_partido['mediana'], stats_partido['max']],
                    marker_color=COLORES['primario'],
                    text=[f"{stats_partido['media']:.1f}", 
                          f"{stats_partido['mediana']:.1f}", 
                          f"{stats_partido['max']:.1f}"],
                    textposition='auto'
                ))
                
                # Barras de referencia
                fig.add_trace(go.Bar(
                    name='Referencia 94min',
                    x=['Media', 'Mediana', 'Máximo'],
                    y=[ref['Media'], ref['Mediana'], ref['Max']],
                    marker_color=COLORES['secundario'],
                    text=[f"{ref['Media']:.1f}", 
                          f"{ref['Mediana']:.1f}", 
                          f"{ref['Max']:.1f}"],
                    textposition='auto'
                ))
                
                fig.update_layout(
                    title=f"{metrica_nombre} - Partido vs Referencia",
                    barmode='group',
                    height=400,
                    yaxis_title=metrica_nombre,
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Análisis comparativo
                dif_media = stats_partido['media'] - ref['Media']
                pct_dif = (dif_media / ref['Media']) * 100 if ref['Media'] != 0 else 0
                
                if abs(pct_dif) > 10:
                    if pct_dif > 0:
                        st.success(f"✅ El equipo está **{pct_dif:.1f}%** por encima de la referencia en {metrica_nombre}")
                    else:
                        st.warning(f"⚠️ El equipo está **{abs(pct_dif):.1f}%** por debajo de la referencia en {metrica_nombre}")
                else:
                    st.info(f"📊 El equipo está dentro del rango normal ({pct_dif:+.1f}%)")
    
    # TAB 2: RANKING DEL PARTIDO
    with tab2:
        st.subheader(f"🏆 Ranking de Jugadores - {metrica_nombre}")
        
        # Preparar datos para tabla
        df_tabla_ranking = df_partido[['player', 'position', 'time', metrica_col]].copy()
        df_tabla_ranking = df_tabla_ranking.sort_values(metrica_col, ascending=False)
        
        # Añadir ranking
        df_tabla_ranking.insert(0, 'Pos', range(1, len(df_tabla_ranking) + 1))
        
        # Añadir comparación con referencia
        if df_referencias is not None:
            ref = obtener_referencia_metrica(df_referencias, metrica_col)
            if ref is not None and isinstance(ref, dict):
                df_tabla_ranking['Dif_vs_Ref'] = df_tabla_ranking[metrica_col] - ref.get('Media', 0)
                df_tabla_ranking['Z-Score'] = df_tabla_ranking[metrica_col].apply(
                    lambda x: calcular_z_score(x, ref.get('Media', 0), ref.get('Desv_Std', 1))
                )
                df_tabla_ranking['Clasificación'] = df_tabla_ranking['Z-Score'].apply(clasificar_rendimiento)
        
        # Renombrar columnas para display
        df_display_ranking = df_tabla_ranking.copy()
        
        # Determinar columnas según si hay referencia o no
        if df_referencias is not None and 'Dif_vs_Ref' in df_tabla_ranking.columns:
            df_display_ranking.columns = ['Pos', 'Jugador', 'Posición', 'Tiempo (min)', 
                                          metrica_nombre, 'Dif. vs Ref', 'Z-Score', 'Rendimiento']
        else:
            df_display_ranking.columns = ['Pos', 'Jugador', 'Posición', 'Tiempo (min)', metrica_nombre]
        
        # Mostrar tabla
        if 'Dif. vs Ref' in df_display_ranking.columns:
            st.dataframe(
                df_display_ranking.style.format({
                    'Tiempo (min)': '{:.1f}',
                    metrica_nombre: '{:.2f}',
                    'Dif. vs Ref': '{:+.2f}',
                    'Z-Score': '{:+.2f}'
                }),
                use_container_width=True,
                height=500
            )
        else:
            st.dataframe(
                df_display_ranking.style.format({
                    'Tiempo (min)': '{:.1f}',
                    metrica_nombre: '{:.2f}'
                }),
                use_container_width=True,
                height=500
            )
        
        st.markdown("---")
        
        # Gráfico de barras
        st.subheader("📊 Gráfico de Ranking")
        
        fig = go.Figure()
        
        # Barras de jugadores
        fig.add_trace(go.Bar(
            x=df_partido['player'],
            y=df_partido[metrica_col],
            marker_color=COLORES['primario'],
            text=df_partido[metrica_col].round(1),
            textposition='auto',
            name=metrica_nombre
        ))
        
        # Línea de referencia
        if df_referencias is not None:
            ref = obtener_referencia_metrica(df_referencias, metrica_col)
            if ref is not None and isinstance(ref, dict):
                if 'Media' in ref:
                    fig.add_hline(
                        y=ref['Media'],
                        line_dash="dash",
                        line_color=COLORES['referencia'],
                        annotation_text=f"Ref. 94min: {ref['Media']:.1f}",
                        annotation_position="right"
                    )
                
                # Líneas de límites
                if 'Lim_Inf_2SD' in ref:
                    fig.add_hline(
                        y=ref['Lim_Inf_2SD'],
                        line_dash="dot",
                        line_color="orange",
                        annotation_text="Lím. Inferior"
                    )
                
                if 'Lim_Sup_2SD' in ref:
                    fig.add_hline(
                        y=ref['Lim_Sup_2SD'],
                        line_dash="dot",
                        line_color="orange",
                        annotation_text="Lím. Superior"
                    )
        
        fig.update_layout(
            title=f"{metrica_nombre} por Jugador",
            xaxis_title="Jugador",
            yaxis_title=metrica_nombre,
            height=500,
            xaxis_tickangle=-45,
            showlegend=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # TAB 3: EVOLUCIÓN TEMPORAL
    with tab3:
        st.subheader("📈 Evolución en el Tiempo")
        
        # Calcular evolución
        evolucion = calcular_evolucion_temporal(df_rango, metrica_col)
        
        if len(evolucion) > 0:
            fig = go.Figure()
            
            # Línea de media
            fig.add_trace(go.Scatter(
                x=evolucion['date'],
                y=evolucion['media'],
                mode='lines+markers',
                name='Media',
                line=dict(color=COLORES['primario'], width=3),
                marker=dict(size=10)
            ))
            
            # Línea de mediana
            fig.add_trace(go.Scatter(
                x=evolucion['date'],
                y=evolucion['mediana'],
                mode='lines+markers',
                name='Mediana',
                line=dict(color=COLORES['exito'], width=2),
                marker=dict(size=8)
            ))
            
            # Área entre min y max
            fig.add_trace(go.Scatter(
                x=evolucion['date'],
                y=evolucion['max'],
                mode='lines',
                name='Máximo',
                line=dict(width=0),
                showlegend=False
            ))
            
            fig.add_trace(go.Scatter(
                x=evolucion['date'],
                y=evolucion['min'],
                mode='lines',
                name='Rango Min-Max',
                line=dict(width=0),
                fillcolor='rgba(68, 68, 68, 0.1)',
                fill='tonexty'
            ))
            
            # Línea de referencia
            if df_referencias is not None:
                ref = obtener_referencia_metrica(df_referencias, metrica_col)
                if ref is not None:
                    fig.add_hline(
                        y=ref['Media'],
                        line_dash="dash",
                        line_color=COLORES['referencia'],
                        annotation_text="Ref. 94min",
                        annotation_position="right"
                    )
            
            # Marcar partido seleccionado
            partido_data = evolucion[evolucion['date'] == partido_seleccionado]
            if len(partido_data) > 0:
                fig.add_trace(go.Scatter(
                    x=[partido_seleccionado],
                    y=[partido_data['media'].iloc[0]],
                    mode='markers',
                    name='Partido Seleccionado',
                    marker=dict(size=20, color='red', symbol='star')
                ))
            
            fig.update_layout(
                title=f"Evolución de {metrica_nombre} en el Tiempo",
                xaxis_title="Fecha",
                yaxis_title=metrica_nombre,
                height=500,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Tabla de evolución
            with st.expander("📋 Ver tabla de evolución"):
                evolucion_display = evolucion.copy()
                evolucion_display['date'] = evolucion_display['date'].dt.strftime('%d/%m/%Y')
                evolucion_display.columns = ['Fecha', 'Media', 'Mediana', 'Máximo', 'Mínimo']
                
                st.dataframe(
                    evolucion_display.style.format({
                        'Media': '{:.2f}',
                        'Mediana': '{:.2f}',
                        'Máximo': '{:.2f}',
                        'Mínimo': '{:.2f}'
                    }),
                    use_container_width=True
                )
        else:
            st.warning("No hay suficientes datos para mostrar evolución")
    
    # TAB 4: DATOS DETALLADOS
    with tab4:
        st.subheader("📋 Datos Detallados del Partido")
        
        # Preparar tabla (usar df_partido completo, no filtrado)
        df_tabla = df_partido[['player', 'position', 'time', metrica_col]].copy()
        
        # Añadir posición desde plantilla si está disponible
        if df_plantilla is not None:
            df_tabla['Posición Real'] = df_tabla['player'].apply(
                lambda x: mapear_posicion(x, df_plantilla)
            )
        
        df_tabla = df_tabla.sort_values(metrica_col, ascending=False)
        
        # Renombrar columnas
        columnas_base = ['Jugador', 'Pos. GPS', 'Tiempo (min)', metrica_nombre]
        if df_plantilla is not None:
            columnas_base.insert(2, 'Posición')
            df_tabla.columns = columnas_base
        else:
            df_tabla.columns = columnas_base
        
        # Añadir comparación con referencia
        if df_referencias is not None:
            ref = obtener_referencia_metrica(df_referencias, metrica_col)
            if ref is not None and isinstance(ref, dict) and 'Media' in ref:
                # Asegurar que la columna es numérica
                df_tabla[metrica_nombre] = pd.to_numeric(df_tabla[metrica_nombre], errors='coerce')
                
                df_tabla['Dif. vs Ref'] = df_tabla[metrica_nombre] - ref['Media']
                df_tabla['% vs Ref'] = ((df_tabla[metrica_nombre] / ref['Media'] - 1) * 100).round(1)
        
        st.dataframe(
            df_tabla,
            use_container_width=True,
            height=500
        )
        
        # Botón de descarga
        csv = df_tabla.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar datos del partido (CSV)",
            data=csv,
            file_name=f"partido_{partido_seleccionado.strftime('%Y%m%d')}_{metrica_nombre}.csv",
            mime="text/csv"
        )


if __name__ == "__main__":
    main()