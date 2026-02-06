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
    layout=LAYOUT,
    initial_sidebar_state="collapsed"
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
    render_sidebar()
    
    st.title("🏠 Estadísticas de Referencia")
    st.markdown("### Normalizadas a 94 minutos")
    
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
    df = st.session_state.get('df_procesado')
    
    if df is None or len(df) == 0:
        st.error("⚠️ Error: datos no disponibles")
        st.stop()

    # Inicializar fechas si no existen
    if 'fecha_desde' not in st.session_state:
        st.session_state.fecha_desde = pd.to_datetime(df['date'].min())
    if 'fecha_hasta' not in st.session_state:
        st.session_state.fecha_hasta = pd.to_datetime(df['date'].max())

    fecha_desde = st.session_state.fecha_desde
    fecha_hasta = st.session_state.fecha_hasta

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
    
    # CORREGIDO: Obtener número de registros correctamente
    # Buscar la fila donde Estadistica == 'Count'
    try:
        row_count = df_referencias[df_referencias['Estadistica'] == 'Count']
        if len(row_count) > 0:
            # Tomar cualquier columna de métricas (todas tienen el mismo Count)
            # Usar la segunda columna (la primera es 'Estadistica')
            n_registros = int(row_count.iloc[0, 1])
        else:
            n_registros = 0
    except:
        n_registros = 0
    
    st.success(f"✅ Referencias calculadas con **{n_registros}** registros")
    
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
        
        # Verificar si ya tiene columna 'Estadística' o necesita reset_index
        if 'Estadística' not in df_referencias.columns:
            df_display = df_referencias.reset_index()
            df_display.rename(columns={'index': 'Estadística'}, inplace=True)
        else:
            df_display = df_referencias.copy()
        
        # Convertir columnas numéricas explícitamente
        for col in df_display.columns:
            if col not in ['Estadística']:
                try:
                    df_display[col] = pd.to_numeric(df_display[col], errors='coerce')
                except:
                    pass
        
        # Formatear solo columnas numéricas
        format_dict = {}
        for col in df_display.columns:
            if col == 'Estadística':
                continue
            elif col in ['Count', 'count']:
                format_dict[col] = '{:.0f}'
            elif pd.api.types.is_numeric_dtype(df_display[col]):
                format_dict[col] = '{:.2f}'
        
        # Mostrar tabla
        st.dataframe(
            df_display.style.format(format_dict, na_rep="-"),
            use_container_width=True,
            height=600
        )
    
    with tab2:
        st.subheader("Detalle por Métrica")
        
        # CORREGIDO: Filtrar 'Estadistica' SIN ACENTO
        metricas_disponibles = [col for col in df_referencias.columns 
                               if col not in ['Estadistica', 'Count', 'count', 'index']]
        
        # Si NO hay métricas, mostrar error
        if len(metricas_disponibles) == 0:
            st.error("❌ No se encontraron métricas en el DataFrame")
            st.write("Columnas disponibles:", df_referencias.columns.tolist())
            st.stop()
        
        # Selector de métrica
        metrica_seleccionada = st.selectbox(
            "Seleccionar métrica:",
            options=metricas_disponibles,
            key='selector_metrica_home'
        )
        
        # CORREGIDO: Crear diccionario con estadísticas de la métrica seleccionada
        # Las filas tienen la estadística en la columna 'Estadistica'
        # y el valor de esa estadística para la métrica en la columna metrica_seleccionada
        metrica_data = {}
        for idx, row in df_referencias.iterrows():
            estadistica = row['Estadistica']  # 'Count', 'Media', 'Mediana', etc.
            valor = row[metrica_seleccionada]  # Valor para esa estadística
            
            # Convertir a numérico
            try:
                valor = float(valor)
            except:
                valor = 0
            
            metrica_data[estadistica] = valor
        
        # Mostrar en columnas
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("📊 Media", f"{metrica_data.get('Media', 0):.2f}")
            st.metric("📊 Mediana", f"{metrica_data.get('Mediana', 0):.2f}")
            st.metric("📊 Desv. Std", f"{metrica_data.get('Desv_Std', 0):.2f}")
        
        with col2:
            st.metric("🔽 Mínimo", f"{metrica_data.get('Min', 0):.2f}")
            st.metric("🔼 Máximo", f"{metrica_data.get('Max', 0):.2f}")
            rango = metrica_data.get('Max', 0) - metrica_data.get('Min', 0)
            st.metric("📈 Rango", f"{rango:.2f}")
        
        with col3:
            st.metric("📊 P25", f"{metrica_data.get('P25', 0):.2f}")
            st.metric("📊 P50", f"{metrica_data.get('P50', 0):.2f}")
            st.metric("📊 P75", f"{metrica_data.get('P75', 0):.2f}")
        
        with col4:
            st.metric("🔝 P90", f"{metrica_data.get('P90', 0):.2f}")
            st.metric("🔝 P95", f"{metrica_data.get('P95', 0):.2f}")
            count_value = metrica_data.get('Count', 0)
            st.metric("📊 Count", f"{int(count_value)}")
        
        st.markdown("---")
        
        # Límites ±2SD
        st.subheader("🎯 Límites de Rendimiento (±2 Desv. Estándar)")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            lim_inf = metrica_data.get('Lim_Inf_2SD', 0)
            st.markdown(f"""
            <div style='background-color: #ffebee; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #f44336;'>
                <h4 style='color: #d32f2f; margin: 0;'>🔴 Por Debajo</h4>
                <p style='font-size: 2rem; font-weight: bold; margin: 0.5rem 0;'>{lim_inf:.2f}</p>
                <p style='color: #666; margin: 0; font-size: 0.9rem;'>Límite inferior (2.5%)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            media = metrica_data.get('Media', 0)
            st.markdown(f"""
            <div style='background-color: #e8f5e9; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #4caf50;'>
                <h4 style='color: #388e3c; margin: 0;'>✅ Rango Normal</h4>
                <p style='font-size: 2rem; font-weight: bold; margin: 0.5rem 0;'>{media:.2f}</p>
                <p style='color: #666; margin: 0; font-size: 0.9rem;'>Media (95% de datos)</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            lim_sup = metrica_data.get('Lim_Sup_2SD', 0)
            st.markdown(f"""
            <div style='background-color: #fff3e0; padding: 1rem; border-radius: 0.5rem; border-left: 4px solid #ff9800;'>
                <h4 style='color: #f57c00; margin: 0;'>🟠 Por Encima</h4>
                <p style='font-size: 2rem; font-weight: bold; margin: 0.5rem 0;'>{lim_sup:.2f}</p>
                <p style='color: #666; margin: 0; font-size: 0.9rem;'>Límite superior (2.5%)</p>
            </div>
            """, unsafe_allow_html=True)
    
    with tab3:
        st.subheader("📥 Exportar Datos")
        
        # CORREGIDO: Resetear índice antes de exportar
        df_export = df_referencias.reset_index()
        df_export.rename(columns={'index': 'Métrica'}, inplace=True)
        
        # Preparar CSV
        csv = df_export.to_csv(index=False).encode('utf-8')
        
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