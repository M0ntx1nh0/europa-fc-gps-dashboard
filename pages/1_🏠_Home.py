"""
Página Home - Referencias Normalizadas 94 min
"""

import streamlit as st
import pandas as pd
import sys
from pathlib import Path

# Añadir directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from config import PAGE_TITLE, PAGE_ICON, LAYOUT
from utils import calcular_referencias_normalizadas, filtrar_por_fechas, render_sidebar

# Configuración de la página
st.set_page_config(
    page_title=f"{PAGE_TITLE} - Home",
    page_icon=PAGE_ICON,
    layout=LAYOUT
)

def main():
    # Renderizar sidebar común
    render_sidebar()
    
    st.title("🏠 Estadísticas de Referencia")
    st.markdown("### Normalizadas a 94 minutos")
    
    # Verificar que hay datos cargados
    if not st.session_state.get('datos_cargados', False):
        st.warning("⚠️ No hay datos cargados. Por favor, carga los datos desde la página principal.")
        st.info("👈 Ve a la página principal y haz clic en '🔄 Cargar/Recargar Datos'")
        st.stop()
    
    df = st.session_state.df_procesado
    fecha_desde = st.session_state.get('fecha_desde')
    fecha_hasta = st.session_state.get('fecha_hasta')
    
    # Filtrar por fechas
    df_rango = filtrar_por_fechas(df, fecha_desde, fecha_hasta)
    
    # Información del rango
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "📅 Rango de fechas",
            f"{fecha_desde.strftime('%d/%m/%y')} - {fecha_hasta.strftime('%d/%m/%y')}"
        )
    
    with col2:
        jugadores_mas_60 = len(df_rango[df_rango['time'] > 60])
        st.metric(
            "👥 Registros >60 min",
            jugadores_mas_60,
            help="Jugadores con más de 60 minutos jugados (base para normalización)"
        )
    
    with col3:
        st.metric(
            "⚽ Partidos",
            df_rango['date'].nunique()
        )
    
    st.markdown("---")
    
    # Calcular referencias
    with st.spinner("Calculando estadísticas normalizadas..."):
        df_referencias = calcular_referencias_normalizadas(df_rango)
    
    if df_referencias is None or len(df_referencias) == 0:
        st.error("❌ No hay suficientes datos (>60 min) en el rango seleccionado para calcular referencias")
        st.info("💡 Prueba ampliando el rango de fechas o verifica que hay partidos con jugadores que jugaron más de 60 minutos")
        st.stop()
    
    # Información
    st.success(f"✅ Referencias calculadas con {df_referencias['Count'].iloc[0] if len(df_referencias) > 0 else 0} registros")
    
    st.markdown("""
    ### ℹ️ ¿Qué son estas referencias?
    
    Estas estadísticas están **normalizadas a 94 minutos** y calculadas **solo con jugadores que jugaron más de 60 minutos**.
    
    - 📊 **Normalización:** Los valores se ajustan como si todos hubieran jugado 94 minutos
    - 👥 **Filtro:** Solo jugadores con >60 min (para evitar sesgos)
    - 🎯 **Uso:** Estas son las referencias para comparar el rendimiento del equipo e individual
    
    **Límites ±2SD:** Valores fuera de estos límites son considerados excepcionales (muy altos o muy bajos)
    """)
    
    st.markdown("---")
    
    # Tabs para diferentes vistas
    tab1, tab2, tab3 = st.tabs(["📊 Tabla Completa", "🎯 Por Métrica", "📥 Exportar"])
    
    with tab1:
        st.subheader("Tabla de Referencias Completa")
        
        # Mostrar tabla completa
        st.dataframe(
            df_referencias.style.format({
                'Media': '{:.2f}',
                'Mediana': '{:.2f}',
                'Desv_Std': '{:.2f}',
                'Min': '{:.2f}',
                'Max': '{:.2f}',
                'P25': '{:.2f}',
                'P50': '{:.2f}',
                'P75': '{:.2f}',
                'P90': '{:.2f}',
                'P95': '{:.2f}',
                'Lim_Inf_2SD': '{:.2f}',
                'Lim_Sup_2SD': '{:.2f}'
            }),
            use_container_width=True,
            height=600
        )
    
    with tab2:
        st.subheader("Detalle por Métrica")
        
        # Selector de métrica
        metrica_seleccionada = st.selectbox(
            "Seleccionar métrica:",
            options=df_referencias['Métrica'].tolist()
        )
        
        # Filtrar métrica
        metrica_data = df_referencias[df_referencias['Métrica'] == metrica_seleccionada].iloc[0]
        
        # Mostrar en columnas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Media", f"{metrica_data['Media']:.2f}")
            st.metric("📊 Mediana", f"{metrica_data['Mediana']:.2f}")
            st.metric("📊 Desv. Std", f"{metrica_data['Desv_Std']:.2f}")
        
        with col2:
            st.metric("🔽 Mínimo", f"{metrica_data['Min']:.2f}")
            st.metric("🔼 Máximo", f"{metrica_data['Max']:.2f}")
            st.metric("📈 Rango", f"{metrica_data['Max'] - metrica_data['Min']:.2f}")
        
        with col3:
            st.metric("📊 P25", f"{metrica_data['P25']:.2f}")
            st.metric("📊 P50", f"{metrica_data['P50']:.2f}")
            st.metric("📊 P75", f"{metrica_data['P75']:.2f}")
        
        with col4:
            st.metric("🔝 P90", f"{metrica_data['P90']:.2f}")
            st.metric("🔝 P95", f"{metrica_data['P95']:.2f}")
            st.metric("📊 Count", f"{metrica_data['Count']}")
        
        st.markdown("---")
        
        # Límites ±2SD
        st.subheader("🎯 Límites de Rendimiento (±2 Desv. Estándar)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div style='background-color: #ffebee; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #f44336;'>
                <h4 style='color: #d32f2f; margin: 0;'>🔴 Por Debajo</h4>
                <p style='font-size: 2rem; font-weight: bold; margin: 0.5rem 0;'>{metrica_data['Lim_Inf_2SD']:.2f}</p>
                <p style='color: #666; margin: 0; font-size: 0.9rem;'>Límite inferior (2.5%)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style='background-color: #e8f5e9; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #4caf50;'>
                <h4 style='color: #388e3c; margin: 0;'>✅ Rango Normal</h4>
                <p style='font-size: 2rem; font-weight: bold; margin: 0.5rem 0;'>{metrica_data['Media']:.2f}</p>
                <p style='color: #666; margin: 0; font-size: 0.9rem;'>Media (95% de datos)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div style='background-color: #fff3e0; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ff9800;'>
                <h4 style='color: #f57c00; margin: 0;'>🟠 Por Encima</h4>
                <p style='font-size: 2rem; font-weight: bold; margin: 0.5rem 0;'>{metrica_data['Lim_Sup_2SD']:.2f}</p>
                <p style='color: #666; margin: 0; font-size: 0.9rem;'>Límite superior (2.5%)</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab3:
        st.subheader("📥 Exportar Datos")
        
        # Preparar CSV
        csv = df_referencias.to_csv(index=False).encode('utf-8')
        
        st.download_button(
            label="📥 Descargar Referencias (CSV)",
            data=csv,
            file_name=f"referencias_94min_{fecha_desde.strftime('%Y%m%d')}_{fecha_hasta.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.info("""
        **Archivo incluye:**
        - Todas las métricas normalizadas
        - Estadísticas completas (Media, Mediana, Percentiles, etc.)
        - Límites ±2 Desviaciones Estándar
        - Basado en jugadores con >60 minutos
        """)


if __name__ == "__main__":
    main()
