"""
Módulo de utilidades para la aplicación Europa FC GPS
"""

from .data_loader import validar_columnas
from .drive_loader import cargar_datos_desde_drive, cargar_plantilla_desde_drive, obtener_info_dataset
from .data_processor import (
    procesar_datos, 
    convertir_tiempo_a_minutos,
    filtrar_por_fechas,
    obtener_partidos_disponibles,
    filtrar_por_partido,
    limpiar_datos
)
from .calculations import (
    calcular_referencias_normalizadas,
    normalizar_a_94min,
    calcular_estadisticas_partido,
    obtener_referencia_metrica,
    calcular_evolucion_temporal,
    calcular_z_score,
    clasificar_rendimiento
)
from .visualizations import (
    crear_player_card,
    crear_dashboard_player_cards,
    calcular_promedio_ultimos_partidos,
    obtener_foto_jugador
)
from .sidebar import (
    render_sidebar,
    inicializar_session_state
)
from .plantilla import (
    cargar_plantilla_europa,
    mapear_posicion,
    obtener_info_jugador,
    obtener_jugadores_por_posicion,
    verificar_plantilla
)

from .pdf_evolucion_individual import generar_pdf_evolucion_individual


__all__ = [
    # data_loader
    'cargar_datos_csv',
    'validar_columnas',
    'obtener_info_dataset',
    # data_processor
    'procesar_datos',
    'convertir_tiempo_a_minutos',
    'filtrar_por_fechas',
    'obtener_partidos_disponibles',
    'filtrar_por_partido',
    'limpiar_datos',
    # calculations
    'calcular_referencias_normalizadas',
    'normalizar_a_94min',
    'calcular_estadisticas_partido',
    'obtener_referencia_metrica',
    'calcular_evolucion_temporal',
    'calcular_z_score',
    'clasificar_rendimiento',
    # visualizations
    'crear_player_card',
    'crear_dashboard_player_cards',
    'calcular_promedio_ultimos_partidos',
    'obtener_foto_jugador',
    # sidebar
    'render_sidebar',
    'inicializar_session_state',
    # plantilla
    'cargar_plantilla_europa',
    'mapear_posicion',
    'obtener_info_jugador',
    'obtener_jugadores_por_posicion',
    'verificar_plantilla'
]