"""
Módulo de Sidebar - Filtros Globales
Sidebar común para todas las páginas
"""

import streamlit as st
import pandas as pd
from pathlib import Path

from config import DATA_DIR
from utils import cargar_datos_csv, procesar_datos, filtrar_por_fechas, obtener_partidos_disponibles


def inicializar_session_state():
    """Inicializa las variables de session state si no existen"""
    if 'datos_cargados' not in st.session_state:
        st.session_state.datos_cargados = False
    if 'df_completo' not in st.session_state:
        st.session_state.df_completo = None
    if 'df_procesado' not in st.session_state:
        st.session_state.df_procesado = None
    if 'fecha_desde' not in st.session_state:
        st.session_state.fecha_desde = None
    if 'fecha_hasta' not in st.session_state:
        st.session_state.fecha_hasta = None
    if 'partido_seleccionado' not in st.session_state:
        st.session_state.partido_seleccionado = None
    if 'metrica_seleccionada' not in st.session_state:
        st.session_state.metrica_seleccionada = 'HSR'


def render_sidebar():
    """
    Renderiza el sidebar común con escudo y filtros globales
    Se usa en todas las páginas de la aplicación
    """
    # Inicializar session state
    inicializar_session_state()
    
    with st.sidebar:
        # ========================================
        # ESCUDO DEL CLUB
        # ========================================
        try:
            st.image("assets/Escudo/Escudo.png", width=150)
        except:
            pass
        
        # ========================================
        # HEADER
        # ========================================
        st.header("🎯 Configuración")
        
        # Información de la carpeta de datos
        st.info(f"📁 Carpeta de datos:\n`{DATA_DIR}`")
        
        # ========================================
        # BOTÓN DE CARGA
        # ========================================
        if st.button("🔄 Cargar/Recargar Datos", use_container_width=True):
            with st.spinner("Cargando datos..."):
                # Cargar datos
                df = cargar_datos_csv(DATA_DIR)
                
                if df is not None:
                    # Procesar datos
                    df_procesado = procesar_datos(df)
                    
                    # Guardar en session state
                    st.session_state.df_completo = df
                    st.session_state.df_procesado = df_procesado
                    st.session_state.datos_cargados = True
                    
                    # Inicializar fechas con RANGO COMPLETO
                    fecha_min = df_procesado['date'].min()
                    fecha_max = df_procesado['date'].max()
                    st.session_state.fecha_desde = fecha_min
                    st.session_state.fecha_hasta = fecha_max
                    
                    # Inicializar partido seleccionado (más reciente)
                    st.session_state.partido_seleccionado = fecha_max
                    
                    st.success(f"✅ Datos cargados: {len(df_procesado)} registros")
                    st.info(f"📅 Rango completo: {fecha_min.strftime('%d/%m/%Y')} → {fecha_max.strftime('%d/%m/%Y')}")
                    st.rerun()
                else:
                    st.error("❌ No se encontraron archivos CSV en la carpeta data/")
                    st.session_state.datos_cargados = False
        
        # ========================================
        # FILTROS GLOBALES (solo si hay datos)
        # ========================================
        if st.session_state.datos_cargados and st.session_state.df_procesado is not None:
            st.markdown("---")
            st.subheader("📅 Filtros Globales")
            
            df = st.session_state.df_procesado
            
            # Filtro de fechas
            fecha_min = df['date'].min()
            fecha_max = df['date'].max()
            
            col1, col2 = st.columns(2)
            with col1:
                fecha_desde = st.date_input(
                    "Desde:",
                    value=st.session_state.fecha_desde,
                    min_value=fecha_min,
                    max_value=fecha_max,
                    key='fecha_desde_global'
                )
            with col2:
                fecha_hasta = st.date_input(
                    "Hasta:",
                    value=st.session_state.fecha_hasta,
                    min_value=fecha_min,
                    max_value=fecha_max,
                    key='fecha_hasta_global'
                )
            
            # Actualizar session state si cambió
            fecha_desde_dt = pd.to_datetime(fecha_desde)
            fecha_hasta_dt = pd.to_datetime(fecha_hasta)
            
            if fecha_desde_dt != st.session_state.fecha_desde or fecha_hasta_dt != st.session_state.fecha_hasta:
                st.session_state.fecha_desde = fecha_desde_dt
                st.session_state.fecha_hasta = fecha_hasta_dt
                st.rerun()
            
            # Filtrar por fechas
            df_rango = filtrar_por_fechas(df, fecha_desde, fecha_hasta)
            
            st.info(f"📊 {len(df_rango)} registros en el rango")
            
            # Obtener partidos disponibles
            partidos = obtener_partidos_disponibles(df_rango)
            
            # Selector de partido
            if len(partidos) > 0:
                # Verificar si el partido actual está en los disponibles
                if st.session_state.partido_seleccionado is not None:
                    if st.session_state.partido_seleccionado not in partidos['date'].tolist():
                        # Si el partido seleccionado no está en el rango, seleccionar el más reciente
                        st.session_state.partido_seleccionado = partidos['date'].iloc[0]
                else:
                    # Si no hay partido seleccionado, seleccionar el más reciente
                    st.session_state.partido_seleccionado = partidos['date'].iloc[0]
                
                partido_seleccionado = st.selectbox(
                    "⚽ Partido:",
                    options=partidos['date'].tolist(),
                    format_func=lambda x: partidos[partidos['date']==x]['label'].values[0],
                    index=partidos['date'].tolist().index(st.session_state.partido_seleccionado),
                    key='partido_global'
                )
                
                # Actualizar session state si cambió
                if partido_seleccionado != st.session_state.partido_seleccionado:
                    st.session_state.partido_seleccionado = partido_seleccionado
                    st.rerun()
            else:
                st.warning("⚠️ No hay partidos en el rango seleccionado")
                st.session_state.partido_seleccionado = None
        
        # ========================================
        # FOOTER DEL SIDEBAR
        # ========================================
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; font-size: 0.8rem; color: #666;'>
            <p><strong>Europa FC</strong></p>
            <p>Sistema GPS v1.6</p>
        </div>
        """, unsafe_allow_html=True)