"""
Sidebar común para todas las páginas
"""

import streamlit as st
import pandas as pd
from utils.drive_loader import obtener_escudo_path


def render_sidebar():
    """
    Renderiza el sidebar común
    Se oculta automáticamente si NO está autenticado
    """
    
    # Si NO autenticado, ocultar sidebar y salir
    if not st.session_state.get('autenticado', False):
        st.markdown("""
            <style>
            [data-testid="stSidebar"] {
                display: none !important;
            }
            </style>
        """, unsafe_allow_html=True)
        return  # Salir sin renderizar nada más
    
    # SI autenticado, renderizar sidebar normal
    with st.sidebar:
        # Logo
        try:
            st.image(obtener_escudo_path(), width=150)
        except:
            st.markdown("⚽ **CE Europa**")
        
        st.markdown("---")
        st.markdown("### 📊 GPS Analytics")
        st.markdown("---")
        
        # Info de datos
        if st.session_state.get('datos_cargados', False):
            df = st.session_state.get('df_procesado')
            
            if df is not None and len(df) > 0:
                st.markdown("#### ✅ Datos Cargados")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Registros", len(df))
                with col2:
                    st.metric("Jugadores", df['player'].nunique())
                
                try:
                    fecha_min = df['date'].min()
                    fecha_max = df['date'].max()
                    
                    if isinstance(fecha_min, str):
                        fecha_min = pd.to_datetime(fecha_min)
                    if isinstance(fecha_max, str):
                        fecha_max = pd.to_datetime(fecha_max)
                    
                    st.caption(f"📅 {fecha_min.strftime('%d/%m/%Y')}")
                    st.caption(f"📅 {fecha_max.strftime('%d/%m/%Y')}")
                    ultima_carga = st.session_state.get('ultima_carga_drive')
                    if ultima_carga:
                        st.caption(f"🔄 Actualizado: {ultima_carga}")
                except:
                    st.caption("📅 Fechas no disponibles")
        else:
            st.warning("⚠️ Sin datos")
            st.caption("Ve a la página principal")
        
        st.markdown("---")
        st.caption("CE Europa v2.5")
