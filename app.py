"""
Europa FC - Aplicación de Análisis GPS
Aplicación principal (Landing page)
v2.0.2 - Actualizada con nueva página Estatus del Equipo
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# Importar configuración
from config import PAGE_TITLE, PAGE_ICON, LAYOUT, DATA_DIR, METRICAS_DICT

# Importar utilidades
from utils import render_sidebar

# Configuración de la página
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="expanded"
)

# CSS personalizado
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .subtitle {
        font-size: 1.5rem;
        color: #666;
        text-align: center;
        margin-bottom: 3rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .new-badge {
        background-color: #ff6b6b;
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 0.3rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Renderizar sidebar común
    render_sidebar()
    
    # Header
    st.markdown('<h1 class="main-header">⚽ Europa FC - Análisis GPS</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Sistema de análisis de datos físicos y rendimiento</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Contenido principal
    if not st.session_state.datos_cargados:
        # Pantalla de bienvenida
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            # Logo del Europa FC
            try:
                st.image("assets/Escudo/Escudo.png", width=400)
            except:
                st.info("⚽ Europa FC")
            
            st.markdown("""
            ### 👋 Bienvenido al Sistema de Análisis GPS
            
            Esta aplicación te permite analizar datos físicos de los partidos del Europa FC
            con herramientas avanzadas de visualización y análisis estadístico.
            
            #### 🚀 Para comenzar:
            
            1. **Asegúrate** de que los archivos CSV están en la carpeta `data/`
            2. **Haz clic** en "🔄 Cargar/Recargar Datos" en el sidebar
            3. **Selecciona** el rango de fechas, partido y métrica
            4. **Navega** por las diferentes páginas del menú lateral
            
            #### 📊 Páginas disponibles:
            
            - **🏠 Home:** Vista general y referencias normalizadas
            - **📊 Equipo:** Player Cards y análisis del partido
            - **👤 Individual:** Evolución y análisis por jugador
            - **📊 Estatus del Equipo:** <span class="new-badge">NUEVO</span> Vista panorámica con gráficos avanzados
            
            ---
            
            **Nota:** Los archivos CSV deben estar en formato Ubiko GPS
            y contener la columna `task='Total'`
            """, unsafe_allow_html=True)
    
    else:
        # Mostrar información del dataset
        df = st.session_state.df_procesado
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "📁 Total Registros",
                len(df),
                help="Registros totales en el dataset (task='Total')"
            )
        
        with col2:
            st.metric(
                "👥 Jugadores",
                df['player'].nunique(),
                help="Jugadores únicos en el dataset"
            )
        
        with col3:
            st.metric(
                "⚽ Partidos",
                df['date'].nunique(),
                help="Partidos únicos en el dataset"
            )
        
        with col4:
            st.metric(
                "📅 Rango",
                f"{df['date'].min().strftime('%d/%m/%y')} - {df['date'].max().strftime('%d/%m/%y')}",
                help="Rango de fechas del dataset"
            )
        
        st.markdown("---")
        
        # Instrucciones mejoradas
        st.markdown("""
        ### 🎯 Cómo usar la aplicación
        
        #### 1️⃣ **Configurar filtros** (Sidebar izquierdo)
        - Selecciona el rango de fechas que quieres analizar
        - Elige el partido específico que quieres estudiar
        - Selecciona la métrica que te interesa (HSR, Sprints, etc.)
        
        #### 2️⃣ **Navegar por las páginas**
        
        **Para análisis rápido:**
        - **🏠 Home:** Estadísticas de referencia normalizadas a 94 min
        - **📊 Equipo:** Player Cards con rendimiento individual del partido
        
        **Para análisis detallado:**
        - **👤 Individual:** Evolución temporal de cada jugador
        - **📊 Estatus del Equipo:** <span class="new-badge">NUEVO v2.0</span> Vista panorámica del equipo
        
        #### 3️⃣ **Interpretar los datos**
        - Las **referencias** están normalizadas a 94 minutos (solo jugadores >60 min)
        - Los **datos del partido** muestran valores originales (todos los jugadores)
        - Los **colores** en Player Cards indican rendimiento vs referencia
        
        ---
        
        ### 📖 Métricas disponibles
        """, unsafe_allow_html=True)
        
        # Mostrar métricas disponibles en columnas
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Métricas de Distancia:**")
            for metrica in ['HSR', 'Distancia Total', 'Distancia a Sprint']:
                st.markdown(f"- ✅ {metrica}")
        
        with col2:
            st.markdown("**Métricas de Intensidad:**")
            for metrica in ['Sprints', 'Velocidad Máxima', 'Aceleraciones', 'Desaceleraciones']:
                st.markdown(f"- ✅ {metrica}")
        
        with col3:
            st.markdown("**Métricas Relativas:**")
            for metrica in ['HSR Relativo', 'Distancia por Minuto', 'HMLD', 'HMLD Relativo']:
                st.markdown(f"- ✅ {metrica}")
        
        st.markdown("---")
        
        # Novedades v2.0
        with st.expander("✨ Novedades en v2.0 - Nueva Página", expanded=False):
            st.markdown("""
            ### 🎉 Nueva: Estatus del Equipo
            
            Vista panorámica del rendimiento colectivo:
            
            #### 🎯 Filtros Separados:
            - **Filtros de Partido:** Específico / Últimos N / Rango
            - **Filtros de Referencia:** 10 estadísticos (Media, P90, etc.)
            
            #### 📊 4 Tabs:
            1. **Vista General:** Barras comparativas
            2. **Distribuciones:** Histogramas + percentiles
            3. **Comparativas:** Scatter plots con cuadrantes
            4. **Evolución Temporal:** Tendencias del equipo
            """)
        
        # Vista previa de datos
        with st.expander("📋 Vista previa de datos"):
            st.dataframe(
                df.head(20),
                use_container_width=True
            )
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 2rem;'>
        <p><strong>Europa FC - Sistema de Análisis GPS</strong></p>
        <p>Desarrollado con ❤️ usando Streamlit</p>
        <p style='font-size: 0.8rem;'>v2.0.2 - Enero 2025</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()