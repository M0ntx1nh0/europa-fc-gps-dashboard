"""
Europa FC - Aplicación de Análisis GPS
Aplicación principal (Landing page)
v2.5.0 - Sistema de autenticación y carga desde Google Drive
"""

import streamlit as st
import pandas as pd
from pathlib import Path

# Importar configuración
from config import PAGE_TITLE, PAGE_ICON, LAYOUT, DATA_DIR, METRICAS_DICT

# Importar utilidades
from utils import render_sidebar, cargar_datos_desde_drive
from utils.auth import mostrar_login, mostrar_info_usuario

# Asegurar que pandas no convierte datetime a string
pd.options.mode.copy_on_write = True


# Configuración de la página
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout=LAYOUT,
    initial_sidebar_state="collapsed"  # ← CAMBIADO de "expanded" a "collapsed"
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
    # ==========================================
    # PASO 1: OCULTAR SIDEBAR SI NO AUTENTICADO
    # ==========================================
    if not st.session_state.get('autenticado', False):
        st.markdown("""
            <style>
            [data-testid="stSidebar"] {
                display: none !important;
            }
            </style>
        """, unsafe_allow_html=True)
    
    # ==========================================
    # PASO 2: AUTENTICACIÓN
    # ==========================================
    if not mostrar_login():
        st.stop()  # Detener ejecución si no está autenticado
    
    # ==========================================
    # PASO 3: RENDERIZAR SIDEBAR (ahora sí está autenticado)
    # ==========================================
    render_sidebar()
    
    # Mostrar info del usuario
    mostrar_info_usuario()
    
    # ==========================================
    # INICIALIZAR SESSION STATE
    # ==========================================
    if 'datos_cargados' not in st.session_state:
        st.session_state.datos_cargados = False
    
    # Header
    st.markdown('<h1 class="main-header">⚽ Europa FC - Análisis GPS</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Sistema de análisis de datos físicos y rendimiento</p>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ==========================================
    # CONTENIDO PRINCIPAL
    # ==========================================
    
    if not st.session_state.get('datos_cargados', False):
        # ========================================
        # PANTALLA DE BIENVENIDA + CARGA DE DATOS
        # ========================================
        
        st.subheader("📂 Carga de Datos")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            **Instrucciones:**
            1. Haz click en el botón "Cargar Datos desde Google Drive"
            2. Los datos se cargarán automáticamente desde la carpeta configurada
            3. Una vez cargados, podrás navegar a las otras páginas
            """)
        
        with col2:
            if st.button("📥 Cargar Datos desde Google Drive", type="primary", use_container_width=True):
                with st.spinner("Cargando datos desde Drive..."):
                    try:
                        # Cargar datos
                        df = cargar_datos_desde_drive(equipo='europa')
                        
                        if df is not None and len(df) > 0:
                            # CRÍTICO: Asegurar que date es datetime antes de guardar
                            df['date'] = pd.to_datetime(df['date'])

                            # Guardar en session_state CON CONVERSIÓN A DATETIME
                            st.session_state.df_procesado = df
                            st.session_state.datos_cargados = True
                            st.session_state.fecha_desde = pd.to_datetime(df['date'].min())
                            st.session_state.fecha_hasta = pd.to_datetime(df['date'].max())
                            st.session_state.partido_seleccionado = pd.to_datetime(df['date'].max())      
                            
                            st.success("✅ Datos cargados correctamente")
                            st.rerun()
                        else:
                            st.error("❌ No se encontraron datos")
                            
                    except Exception as e:
                        st.error(f"❌ Error al cargar datos: {str(e)}")
        
        st.markdown("---")
        
        # Información adicional
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
            
            1. **Haz click** en "Cargar Datos desde Google Drive" arriba
            2. **Espera** a que los datos se carguen automáticamente
            3. **Navega** por las diferentes páginas del menú lateral
            
            #### 📊 Páginas disponibles:
            
            - **🏠 Home:** Vista general y carga de datos
            - **📊 Equipo:** Player Cards y análisis del partido
            - **👤 Individual:** Evolución y análisis por jugador
            - **📊 Estatus del Equipo:** <span class="new-badge">NUEVO</span> Vista panorámica con gráficos avanzados
            
            ---
            
            **Nota:** Los datos se cargan automáticamente desde Google Drive
            """, unsafe_allow_html=True)
    
    else:
        # ========================================
        # PANTALLA DE DATOS CARGADOS
        # ========================================
        
        st.success("✅ **Datos cargados y listos**")
        
        df = st.session_state.df_procesado
        
        # Métricas principales
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
            # CORREGIDO: Asegurar conversión a datetime
            fecha_min = pd.to_datetime(df['date'].min())
            fecha_max = pd.to_datetime(df['date'].max())
            dias = (fecha_max - fecha_min).days
            st.metric("📅 Rango", f"{dias} días")
        
        st.markdown("---")
        
        # Info detallada
        st.subheader("📊 Resumen del Dataset")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Fechas disponibles:**")
            # CORREGIDO: Asegurar conversión a datetime
            fecha_min = pd.to_datetime(df['date'].min())
            fecha_max = pd.to_datetime(df['date'].max())
            st.caption(f"Desde: {fecha_min.strftime('%d/%m/%Y')}")
            st.caption(f"Hasta: {fecha_max.strftime('%d/%m/%Y')}")
            
            st.markdown("**Jugadores registrados:**")
            # CORREGIDO: dropna().astype(str) para evitar errores con NaN
            jugadores = sorted(df['player'].dropna().astype(str).unique())
            st.caption(f"{len(jugadores)} jugadores totales")
        
        with col2:
            st.markdown("**Partidos disponibles:**")
            fechas_partidos = sorted(df['date'].unique())
            for fecha in fechas_partidos[-5:]:  # Últimos 5
                # CORREGIDO: Asegurar que fecha es datetime
                fecha_dt = pd.to_datetime(fecha)
                st.caption(f"📅 {fecha_dt.strftime('%d/%m/%Y')}")
            if len(fechas_partidos) > 5:
                st.caption(f"... y {len(fechas_partidos) - 5} más")
        
        st.markdown("---")
        
        # Instrucciones de uso
        st.markdown("""
        ### 🎯 Cómo usar la aplicación
        
        #### 📊 **Páginas disponibles:**
        
        **Para análisis rápido:**
        - **🏠 Home:** Estadísticas de referencia normalizadas a 94 min
        - **📊 Equipo:** Player Cards con rendimiento individual del partido
        
        **Para análisis detallado:**
        - **👤 Individual:** Evolución temporal de cada jugador con filtros flexibles
        - **📊 Estatus del Equipo:** <span class="new-badge">NUEVO v2.5</span> Vista panorámica del equipo con múltiples filtros
        
        #### 💡 **Características principales:**
        - **Filtros flexibles** en cada página (Partido específico / Últimos N / Rango de fechas)
        - **Referencias normalizadas** a 94 minutos (>60 min jugados)
        - **Visualizaciones interactivas** con Plotly
        - **Exportación a PDF** en análisis individual
        
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
        
        # Navegación
        st.info("👈 **Ahora puedes navegar a las otras páginas usando el menú lateral**")
        
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
        <p style='font-size: 0.8rem;'>v2.5.0 - Febrero 2025</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()