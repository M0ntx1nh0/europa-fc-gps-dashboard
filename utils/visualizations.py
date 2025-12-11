"""
Módulo de visualizaciones - Player Cards v1.7
Con sistema de colores dinámico y filtros avanzados
"""

import streamlit as st
import pandas as pd
from pathlib import Path


def obtener_foto_jugador(nombre_jugador, carpeta_fotos="assets/jugadores"):
    """
    Obtiene la ruta de la foto del jugador
    
    Args:
        nombre_jugador (str): Nombre del jugador
        carpeta_fotos (str): Carpeta con las fotos
        
    Returns:
        str: Ruta de la foto o foto por defecto (fotopendt.jpg)
    """
    from pathlib import Path
    
    # Extensiones posibles
    extensiones = ['.jpg', '.jpeg', '.png', '.webp']
    
    # Variaciones de búsqueda
    variaciones = [
        nombre_jugador,  # Nombre completo original: "Pedro García"
        nombre_jugador.split()[0],  # Solo primer nombre: "Pedro"
        nombre_jugador.split()[-1] if len(nombre_jugador.split()) > 1 else nombre_jugador,  # Solo apellido: "García"
        nombre_jugador.replace(' ', '_'),  # Con guiones bajos: "Pedro_García"
        nombre_jugador.lower().replace(' ', '_'),  # Minúsculas con guiones: "pedro_garcía"
        nombre_jugador.lower().replace(' ', ''),  # Minúsculas sin espacios: "pedrogarcia"
    ]
    
    # Buscar foto con cada variación
    for variacion in variaciones:
        for ext in extensiones:
            # Probar con la variación exacta
            ruta = Path(carpeta_fotos) / f"{variacion}{ext}"
            if ruta.exists():
                return str(ruta)
            
            # Probar con primera letra mayúscula
            ruta_cap = Path(carpeta_fotos) / f"{variacion.capitalize()}{ext}"
            if ruta_cap.exists():
                return str(ruta_cap)
            
            # Probar todo en mayúsculas
            ruta_upper = Path(carpeta_fotos) / f"{variacion.upper()}{ext}"
            if ruta_upper.exists():
                return str(ruta_upper)
    
    # Si no existe foto específica, usar foto por defecto
    foto_default = Path(carpeta_fotos) / "fotopendt.jpg"
    if foto_default.exists():
        return str(foto_default)
    
    # Si ni siquiera existe la foto por defecto, retornar None
    return None


def obtener_color_metrica(valor, referencia_seleccionada, referencias_dict):
    """
    Calcula el color de una métrica según su valor vs referencia
    
    Args:
        valor (float): Valor de la métrica del jugador
        referencia_seleccionada (str): 'Media', 'P90', etc.
        referencias_dict (dict): Diccionario con todas las referencias
            {
                'Media': 250.0,
                'Mediana': 245.0,
                'P70': 280.0,
                'P75': 300.0,
                'P80': 320.0,
                'P85': 335.0,
                'P90': 350.0,
                'P95': 380.0,
                'P25': 200.0
            }
    
    Returns:
        str: Color en formato CSS ('green', 'blue', 'gray', 'orange')
    """
    if referencias_dict is None or len(referencias_dict) == 0:
        return 'gray'
    
    # Obtener valor de referencia seleccionada
    ref_valor = referencias_dict.get(referencia_seleccionada, referencias_dict.get('Media', 0))
    
    if ref_valor == 0:
        return 'gray'
    
    # Sistema de colores de 4 niveles
    # 🟢 Verde: Cumple o supera referencia seleccionada
    if valor >= ref_valor:
        return 'green'
    
    # 🔵 Azul: Sobre media pero bajo referencia
    elif valor >= referencias_dict.get('Media', 0):
        return 'blue'
    
    # ⚪ Gris: Entre P25 y Media
    elif valor >= referencias_dict.get('P25', 0):
        return 'gray'
    
    # 🟠 Naranja: Bajo P25
    else:
        return 'orange'


def calcular_promedio_ultimos_partidos(df, jugador, n_partidos, metricas):
    """
    Calcula el promedio de las últimas N apariciones de un jugador
    
    Args:
        df (pd.DataFrame): DataFrame con todos los datos
        jugador (str): Nombre del jugador
        n_partidos (int): Número de partidos a promediar
        metricas (list): Lista de métricas a calcular
        
    Returns:
        dict: Diccionario con promedios y tiempo del último partido
    """
    # Filtrar datos del jugador
    df_jugador = df[df['player'] == jugador].copy()
    df_jugador = df_jugador.sort_values('date', ascending=False)
    
    # Tomar últimos N partidos
    df_ultimos = df_jugador.head(n_partidos)
    
    if len(df_ultimos) == 0:
        return None
    
    # Calcular promedios
    promedios = {
        'partidos_jugados': len(df_ultimos),
        'tiempo_promedio': df_ultimos['time'].mean(),
        'tiempo_ultimo_partido': df_ultimos['time'].iloc[0]  # Tiempo del más reciente
    }
    
    for metrica in metricas:
        if metrica in df_ultimos.columns:
            promedios[metrica] = df_ultimos[metrica].mean()
        else:
            promedios[metrica] = 0
    
    return promedios


def crear_player_card(jugador, stats, posicion='', minutos=0, colores=None, menos_60_min=False):
    """
    Crea una player card visual con estadísticas y colores dinámicos
    
    Args:
        jugador (str): Nombre del jugador
        stats (dict): Diccionario con estadísticas
        posicion (str): Posición del jugador
        minutos (int): Minutos jugados del último partido
        colores (dict): Diccionario con colores por métrica
        menos_60_min (bool): True si jugador tiene <60min (añade asterisco)
    """
    # Obtener foto (siempre retorna una foto válida o fotopendt.jpg)
    foto_path = obtener_foto_jugador(jugador)
    
    # Nombre con asterisco si <60min
    nombre_display = f"{jugador}*" if menos_60_min else jugador
    
    # Mapeo de colores CSS
    color_map = {
        'green': '#22c55e',   # Verde
        'blue': '#3b82f6',    # Azul
        'gray': '#6b7280',    # Gris
        'orange': '#f97316'   # Naranja
    }
    
    # Función auxiliar para obtener color de métrica
    def get_color(metrica_key, valor_default='#1f77b4'):
        if colores and metrica_key in colores:
            return color_map.get(colores[metrica_key], valor_default)
        return valor_default
    
    # Contenedor con borde y estilo
    st.markdown("""
    <style>
    .player-container {
        border: 2px solid #e0e0e0;
        border-radius: 12px;
        padding: 0;
        background: white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        overflow: hidden;
    }
    .player-header {
        background: #f8f9fa;
        padding: 12px 10px;
        text-align: center;
        border-bottom: 2px solid #e0e0e0;
        min-height: 45px;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .player-name-blue {
        font-size: 1.1rem;
        font-weight: bold;
        color: #1f77b4;
        margin: 0;
    }
    .player-body {
        padding: 15px;
    }
    .player-position-text {
        font-size: 0.85rem;
        color: #666;
        text-align: center;
        margin: 5px 0 10px 0;
    }
    .metric-container {
        text-align: center;
        padding: 5px;
    }
    .metric-value-small {
        font-size: 1rem;
        font-weight: bold;
        margin: 0;
    }
    .metric-label-small {
        font-size: 0.7rem;
        color: #666;
        margin: 0;
    }
    .minutos-text {
        text-align: center;
        font-size: 0.85rem;
        color: #666;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Iniciar contenedor con borde
    st.markdown('<div class="player-container">', unsafe_allow_html=True)
    
    # Header con nombre en azul (centrado verticalmente)
    st.markdown(f'<div class="player-header"><div class="player-name-blue">{nombre_display}</div></div>', unsafe_allow_html=True)
    
    # Body del card
    st.markdown('<div class="player-body">', unsafe_allow_html=True)
    
    # Foto (siempre existe - específica del jugador o fotopendt.jpg)
    if foto_path:
        from PIL import Image
        try:
            img = Image.open(foto_path)
            # Centrar con columnas
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(img, width=150)
        except Exception as e:
            # Error al cargar imagen - mostrar placeholder
            st.markdown(f"""
            <div style='width:150px;height:150px;border-radius:50%;background:#cccccc;
                        display:flex;align-items:center;justify-content:center;
                        margin:0 auto;font-size:0.8rem;color:#666;text-align:center;'>
                Error<br>cargando<br>imagen
            </div>
            """, unsafe_allow_html=True)
    
    # Posición debajo de la foto
    st.markdown(f'<div class="player-position-text">{posicion}</div>', unsafe_allow_html=True)
    
    # Separador
    st.markdown('<hr style="margin: 10px 0; border: none; border-top: 1px solid #e0e0e0;">', unsafe_allow_html=True)
    
    # ========================================
    # MÉTRICAS EN GRID 3 COLUMNAS CON COLORES
    # ========================================
    
    # FILA 1: Distancia Total | HSR | HMLD
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label-small">Distancia Total (m)</div>
            <div class="metric-value-small" style="color:{get_color('total_distance')}">{stats.get('total_distance', 0):.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label-small">HSR (m)</div>
            <div class="metric-value-small" style="color:{get_color('hsr')}">{stats.get('hsr', 0):.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label-small">HMLD (m)</div>
            <div class="metric-value-small" style="color:{get_color('hmld')}">{stats.get('hmld', 0):.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # FILA 2: Distancia por minutos | HSR Rel | HMLD Rel
    col4, col5, col6 = st.columns(3)
    
    with col4:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label-small">Distancia por minutos (m/min)</div>
            <div class="metric-value-small" style="color:{get_color('minute_distance')}">{stats.get('minute_distance', 0):.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col5:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label-small">HSR Rel (m/min)</div>
            <div class="metric-value-small" style="color:{get_color('hsr_rel')}">{stats.get('hsr_rel', 0):.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col6:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label-small">HMLD Rel (m/min)</div>
            <div class="metric-value-small" style="color:{get_color('hmld_relative')}">{stats.get('hmld_relative', 0):.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # FILA 3: Distancia a Sprint | Nº de Sprints | Velocidad Máxima
    col7, col8, col9 = st.columns(3)
    
    with col7:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label-small">Distancia a Sprint (m)</div>
            <div class="metric-value-small" style="color:{get_color('distance_vrange6')}">{stats.get('distance_vrange6', 0):.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col8:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label-small">Nº de Sprints</div>
            <div class="metric-value-small" style="color:{get_color('sprints')}">{stats.get('sprints', 0):.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col9:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label-small">Velocidad Máxima (km/h)</div>
            <div class="metric-value-small" style="color:{get_color('max_speed')}">{stats.get('max_speed', 0):.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # FILA 4: Tiempo Promedio | Nº Aceleraciones expl | Nº Deceleraciones expl
    col10, col11, col12 = st.columns(3)
    
    with col10:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label-small">Tiempo Promedio (prome...</div>
            <div class="metric-value-small" style="color:#6b7280">{stats.get('tiempo_promedio', 0):.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col11:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label-small">Nº Aceleraciones expl</div>
            <div class="metric-value-small" style="color:{get_color('num_acc_expl')}">{stats.get('num_acc_expl', 0):.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col12:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-label-small">Nº Deceleraciones expl</div>
            <div class="metric-value-small" style="color:{get_color('num_dec_expl')}">{stats.get('num_dec_expl', 0):.1f}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Minutos jugados del ÚLTIMO PARTIDO (no promedio)
    minutos_text = f"⏱️ Min. Partido Seleccionado: {minutos:.0f} min"
    if menos_60_min:
        minutos_text += "*"
    st.markdown(f'<div class="minutos-text">{minutos_text}</div>', unsafe_allow_html=True)
    
    # Cerrar body y contenedor
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


def crear_dashboard_player_cards(df_partido, df_rango, n_partidos=3, 
                                 criterio_orden='Tiempo jugado',
                                 df_plantilla=None,
                                 df_referencias=None,
                                 referencia_seleccionada='Media'):
    """
    Crea un dashboard completo con player cards filtradas y ordenadas
    
    Args:
        df_partido (pd.DataFrame): Datos del partido seleccionado
        df_rango (pd.DataFrame): Datos de todos los partidos en el rango
        n_partidos (int): Número de partidos a promediar
        criterio_orden (str): Criterio de ordenamiento
        df_plantilla (pd.DataFrame): Plantilla con posiciones
        df_referencias (pd.DataFrame): Referencias normalizadas para colores
        referencia_seleccionada (str): 'Media', 'P90', etc.
    """
    # Obtener lista de jugadores según ordenamiento
    if criterio_orden == 'Tiempo jugado':
        jugadores = df_partido.sort_values('time', ascending=False)['player'].tolist()
    elif criterio_orden == 'HSR':
        jugadores = df_partido.sort_values('hsr', ascending=False)['player'].tolist()
    elif criterio_orden == 'Distancia Total':
        jugadores = df_partido.sort_values('total_distance', ascending=False)['player'].tolist()
    elif criterio_orden == 'Sprints':
        jugadores = df_partido.sort_values('sprints', ascending=False)['player'].tolist()
    elif criterio_orden == 'Velocidad Máxima':
        jugadores = df_partido.sort_values('max_speed', ascending=False)['player'].tolist()
    elif criterio_orden == 'Alfabético':
        jugadores = sorted(df_partido['player'].tolist())
    else:
        # Por defecto: tiempo jugado
        jugadores = df_partido.sort_values('time', ascending=False)['player'].tolist()
    
    if len(jugadores) == 0:
        st.warning("⚠️ No hay jugadores en este partido")
        return
    
    # Métricas a calcular (TODAS las métricas disponibles)
    metricas = [
        'total_distance', 'minute_distance', 'max_speed', 
        'hsr', 'hsr_rel', 'hmld', 'hmld_relative',
        'distance_vrange6', 'sprints', 
        'num_acc_expl', 'num_dec_expl'
    ]
    
    # Verificar cuántos partidos hay disponibles
    if len(jugadores) > 0:
        primer_jugador = jugadores[0]
        df_primer_jugador = df_rango[df_rango['player'] == primer_jugador]
        partidos_disponibles = len(df_primer_jugador.sort_values('date', ascending=False).head(n_partidos))
        
        # No mostrar aviso aquí (ya se muestra en la página principal)
    
    # Preparar referencias por métrica (convertir a dict)
    referencias_por_metrica = {}
    if df_referencias is not None and len(df_referencias) > 0:
        for metrica in metricas:
            if metrica in df_referencias.columns:
                # Crear dict con todas las estadísticas de esta métrica
                referencias_por_metrica[metrica] = {
                    'Media': df_referencias.loc[df_referencias['Estadistica'] == 'Media', metrica].values[0] if 'Media' in df_referencias['Estadistica'].values else 0,
                    'Mediana': df_referencias.loc[df_referencias['Estadistica'] == 'Mediana', metrica].values[0] if 'Mediana' in df_referencias['Estadistica'].values else 0,
                    'P25': df_referencias.loc[df_referencias['Estadistica'] == 'P25', metrica].values[0] if 'P25' in df_referencias['Estadistica'].values else 0,
                    'P70': df_referencias.loc[df_referencias['Estadistica'] == 'P70', metrica].values[0] if 'P70' in df_referencias['Estadistica'].values else 0,
                    'P75': df_referencias.loc[df_referencias['Estadistica'] == 'P75', metrica].values[0] if 'P75' in df_referencias['Estadistica'].values else 0,
                    'P80': df_referencias.loc[df_referencias['Estadistica'] == 'P80', metrica].values[0] if 'P80' in df_referencias['Estadistica'].values else 0,
                    'P85': df_referencias.loc[df_referencias['Estadistica'] == 'P85', metrica].values[0] if 'P85' in df_referencias['Estadistica'].values else 0,
                    'P90': df_referencias.loc[df_referencias['Estadistica'] == 'P90', metrica].values[0] if 'P90' in df_referencias['Estadistica'].values else 0,
                    'P95': df_referencias.loc[df_referencias['Estadistica'] == 'P95', metrica].values[0] if 'P95' in df_referencias['Estadistica'].values else 0,
                }
    
    # Crear grid de 4 columnas
    cols_per_row = 4
    
    # Iterar por jugadores en grupos de 4
    for i in range(0, len(jugadores), cols_per_row):
        cols = st.columns(cols_per_row)
        
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(jugadores):
                jugador = jugadores[idx]
                
                # Obtener datos del jugador en este partido
                jugador_data = df_partido[df_partido['player'] == jugador].iloc[0]
                
                # Obtener posición desde plantilla o desde CSV
                if df_plantilla is not None:
                    from utils.plantilla import mapear_posicion
                    posicion = mapear_posicion(jugador, df_plantilla)
                else:
                    posicion = jugador_data.get('position', '')
                
                # Calcular promedios de últimos N partidos
                stats = calcular_promedio_ultimos_partidos(
                    df_rango, jugador, n_partidos, metricas
                )
                
                if stats:
                    # Verificar si jugador tiene <60 min (en el último partido)
                    tiempo_ultimo = stats.get('tiempo_ultimo_partido', 0)
                    menos_60_min = tiempo_ultimo < 60
                    
                    # Calcular colores por métrica
                    colores = {}
                    if referencias_por_metrica:
                        for metrica in metricas:
                            if metrica in referencias_por_metrica and metrica in stats:
                                colores[metrica] = obtener_color_metrica(
                                    stats[metrica],
                                    referencia_seleccionada,
                                    referencias_por_metrica[metrica]
                                )
                    
                    with col:
                        crear_player_card(
                            jugador=jugador,
                            stats=stats,
                            posicion=posicion,
                            minutos=tiempo_ultimo,
                            colores=colores,
                            menos_60_min=menos_60_min
                        )
        
        # Pequeño espacio entre filas
        if i + cols_per_row < len(jugadores):
            st.markdown("<div style='margin-bottom:10px;'></div>", unsafe_allow_html=True)
    
    # Nota al final si hay jugadores con <60min
    if df_partido[df_partido['time'] < 60].shape[0] > 0:
        st.caption("ℹ️ (*) Jugadores con <60min en el último partido - Comparación con referencias P94 limitada")