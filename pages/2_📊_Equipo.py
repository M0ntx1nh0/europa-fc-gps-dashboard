"""
Página: Análisis de Equipo
Vista general y comparativa del rendimiento
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
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
        estadistico = st.selectbox(
            "📊 Estadístico:",
            options=['Media', 'Máximo', 'P70', 'P95'],
            key='estadistico_analisis',
            help="Media: Promedio\nMáximo: Valor más alto\nP70/P95: Percentiles"
        )

    mostrar_tendencia_lineal = st.checkbox(
        "Mostrar línea de tendencia lineal",
        value=True,
        key="mostrar_tendencia_equipo",
        help="Añade una línea discontinua para facilitar la lectura (sube, baja o estable)."
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
    posiciones_seleccionadas = []
    jugadores_seleccionados = []
    
    if nivel_analisis == 'Por posiciones':
        st.markdown("### 🎯 Seleccionar Posiciones")
        
        # Cargar plantilla para mapear posiciones
        try:
            df_plantilla = cargar_plantilla_europa()
            df_limpio['posicion'] = df_limpio['player'].apply(
                lambda x: mapear_posicion(str(x), df_plantilla) 
                if pd.notna(x) and str(x).strip() != '' else 'Sin posición'
            )
        except:
            st.error("⚠️ No se pudo cargar información de posiciones")
            st.stop()
        
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
        return valores.mean()
    
    # Obtener fechas únicas ordenadas
    fechas_disponibles = sorted(df_limpio['date'].unique())

    def construir_datos_grafico(metrica_objetivo):
        datos = []

        if nivel_analisis == 'Equipo':
            # Una barra por partido (estadístico del equipo completo)
            for fecha in fechas_disponibles:
                df_fecha = df_limpio[df_limpio['date'] == fecha]

                if len(df_fecha) > 0:
                    valor = calcular_estadistico(df_fecha[metrica_objetivo], estadistico)
                    minutaje_promedio = df_fecha['time'].mean()

                    datos.append({
                        'fecha': fecha,
                        'nombre': 'Equipo',
                        'valor': valor,
                        'minutaje': minutaje_promedio,
                        'color': COLORES['primario'],
                        'grupo': 'Equipo'
                    })

        elif nivel_analisis == 'Por posiciones':
            colores_posicion = {
                'Defensa': '#ef4444',
                'Centrocampista': '#3b82f6',
                'Delantero': '#22c55e'
            }

            colores_individuales = ['#1E88E5', '#FF6F00', '#43A047', '#E53935', '#8E24AA', '#00ACC1']

            if len(posiciones_seleccionadas) == 1:
                # UNA SOLA POSICIÓN: barras por jugador
                jugadores_posicion = sorted(df_limpio['player'].unique())

                for idx, jugador in enumerate(jugadores_posicion):
                    for fecha in fechas_disponibles:
                        df_jug_fecha = df_limpio[
                            (df_limpio['player'] == jugador) &
                            (df_limpio['date'] == fecha)
                        ]

                        if len(df_jug_fecha) > 0:
                            valor = calcular_estadistico(df_jug_fecha[metrica_objetivo], estadistico)
                            minutaje = df_jug_fecha['time'].mean()

                            datos.append({
                                'fecha': fecha,
                                'nombre': jugador,
                                'valor': valor,
                                'minutaje': minutaje,
                                'color': colores_individuales[idx % len(colores_individuales)],
                                'grupo': jugador
                            })
            else:
                # MÚLTIPLES POSICIONES: barras por posición
                for posicion in posiciones_seleccionadas:
                    for fecha in fechas_disponibles:
                        df_pos_fecha = df_limpio[
                            (df_limpio['posicion'] == posicion) &
                            (df_limpio['date'] == fecha)
                        ]

                        if len(df_pos_fecha) > 0:
                            valor = calcular_estadistico(df_pos_fecha[metrica_objetivo], estadistico)
                            minutaje_promedio = df_pos_fecha['time'].mean()

                            datos.append({
                                'fecha': fecha,
                                'nombre': posicion,
                                'valor': valor,
                                'minutaje': minutaje_promedio,
                                'color': colores_posicion[posicion],
                                'grupo': posicion
                            })

        else:  # Individual
            colores_individuales = ['#1E88E5', '#FF6F00', '#43A047', '#E53935', '#8E24AA', '#00ACC1']

            for idx, jugador in enumerate(jugadores_seleccionados):
                for fecha in fechas_disponibles:
                    df_jug_fecha = df_limpio[
                        (df_limpio['player'] == jugador) &
                        (df_limpio['date'] == fecha)
                    ]

                    if len(df_jug_fecha) > 0:
                        valor = calcular_estadistico(df_jug_fecha[metrica_objetivo], estadistico)
                        minutaje = df_jug_fecha['time'].mean()

                        datos.append({
                            'fecha': fecha,
                            'nombre': jugador,
                            'valor': valor,
                            'minutaje': minutaje,
                            'color': colores_individuales[idx % len(colores_individuales)],
                            'grupo': jugador
                        })

        return datos

    def preparar_df_grafico(datos):
        df_out = pd.DataFrame(datos)
        df_out['fecha'] = pd.to_datetime(df_out['fecha'])
        df_out['fecha_label'] = df_out['fecha'].dt.strftime('%d/%m')
        df_out['fecha_full'] = df_out['fecha'].dt.strftime('%d/%m/%Y')
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

        for nombre in df_local['nombre'].unique():
            df_grupo = df_local[df_local['nombre'] == nombre].sort_values('fecha').copy()

            if mostrar_tendencia and len(df_grupo) >= 2:
                y_vals = df_grupo["valor"].astype(float).values
                x_idx = np.arange(len(df_grupo))
                coef = np.polyfit(x_idx, y_vals, 1)
                df_grupo["trend"] = coef[0] * x_idx + coef[1]

            texto_barras = [
                (
                    f"{metrica_nombre_plot}={row['valor']:.1f}<br>"
                    f"<span style='color:{'#d32f2f' if row['minutaje'] < 60 else '#111111'}'>"
                    f"Min={int(row['minutaje'])}'</span>"
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
                textfont=dict(size=10, color='black'),
                cliponaxis=False,
                hovertemplate=(
                    '<b>%{customdata[0]}</b><br>' +
                    f'{nombre}<br>' +
                    f'{metrica_nombre_plot}: %{{y:.1f}}<br>' +
                    'Minutos: %{customdata[1]:.0f}<br>' +
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

    todas_metricas_pdf = st.checkbox(
        "Seleccionar todas las métricas",
        key="todas_metricas_pdf_equipo",
        value=False
    )

    if todas_metricas_pdf:
        metricas_pdf = list(metricas_disponibles.keys())
        st.caption(f"Se incluirán todas las métricas disponibles ({len(metricas_pdf)}).")
    else:
        metricas_pdf = st.multiselect(
            "Métricas a incluir en el informe:",
            options=list(metricas_disponibles.keys()),
            default=[metrica_nombre],
            key="metricas_pdf_equipo",
            help="Incluye la métrica visible y añade las que quieras para el informe."
        )

    incluir_detalle_individual = st.checkbox(
        "Añadir detalle individual de jugadores al final del informe",
        key="incluir_detalle_individual_pdf",
        value=False
    )

    jugadores_detalle_pdf = []
    if incluir_detalle_individual:
        if nivel_analisis == "Individual":
            jugadores_detalle_pdf = jugadores_seleccionados.copy()
            st.caption(f"Detalle individual: {len(jugadores_detalle_pdf)} jugador(es) seleccionados en el análisis.")
        else:
            jugadores_detalle_pdf = sorted(df_limpio['player'].dropna().astype(str).unique().tolist())
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
            return f"Partido específico: {fecha.strftime('%d/%m/%Y')}" if fecha is not None else "Partido específico"
        if modo_partido == 'Últimos N partidos':
            n = info_filtro.get('n_partidos', 0)
            ini = info_filtro.get('fecha_inicio')
            fin = info_filtro.get('fecha_fin')
            if ini is not None and fin is not None:
                return f"Últimos {n} partidos ({ini.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')})"
            return f"Últimos {n} partidos"

        ini = info_filtro.get('fecha_inicio')
        fin = info_filtro.get('fecha_fin')
        if ini is not None and fin is not None:
            return f"Rango de fechas: {ini.strftime('%d/%m/%Y')} - {fin.strftime('%d/%m/%Y')}"
        return "Rango de fechas personalizado"

    def construir_texto_alcance():
        if nivel_analisis == 'Equipo':
            return "Equipo completo"
        if nivel_analisis == 'Por posiciones':
            if len(posiciones_seleccionadas) == 1:
                jugadores = sorted(df_limpio['player'].unique().tolist())
                return f"Posición: {posiciones_seleccionadas[0]} | Jugadores: {', '.join(jugadores)}"
            return f"Posiciones: {', '.join(posiciones_seleccionadas)}"
        return f"Jugadores: {', '.join(jugadores_seleccionados)}"

    if st.button("📥 Generar informe PDF", type="primary", use_container_width=True):
        if len(metricas_pdf) == 0:
            st.warning("⚠️ Selecciona al menos una métrica para el informe.")
        elif incluir_detalle_individual and len(jugadores_detalle_pdf) == 0:
            st.warning("⚠️ Selecciona al menos un jugador para el detalle individual.")
        else:
            with st.spinner("Generando informe PDF..."):
                metricas_para_pdf = []

                for metrica_pdf_nombre in metricas_pdf:
                    metrica_pdf_col = METRICAS_DICT[metrica_pdf_nombre]
                    datos_pdf = construir_datos_grafico(metrica_pdf_col)
                    if len(datos_pdf) == 0:
                        continue
                    df_grafico_pdf = preparar_df_grafico(datos_pdf)
                    metricas_para_pdf.append({
                        "metrica_nombre": metrica_pdf_nombre,
                        "df_grafico": df_grafico_pdf,
                        "plotly_fig": crear_figura_plotly(
                            df_grafico_pdf,
                            metrica_pdf_nombre,
                            mostrar_tendencia=mostrar_tendencia_lineal
                        ),
                        "mostrar_tendencia": mostrar_tendencia_lineal
                    })

                detalles_jugadores_pdf = []
                if incluir_detalle_individual:
                    for jugador in jugadores_detalle_pdf:
                        df_jugador = df_limpio[df_limpio['player'] == jugador].copy()
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
                        for metrica_pdf_nombre in metricas_pdf:
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
                    output_path = generar_pdf_equipo(
                        metricas_pdf=metricas_para_pdf,
                        estadistico=estadistico,
                        nivel_analisis=nivel_analisis,
                        filtro_texto=construir_texto_filtro(),
                        alcance_texto=construir_texto_alcance(),
                        comentario=comentario_pdf,
                        detalles_jugadores=detalles_jugadores_pdf
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
