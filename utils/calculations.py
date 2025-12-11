"""
Módulo para cálculos y normalizaciones
"""

import pandas as pd
import numpy as np
import sys
from pathlib import Path

# Añadir directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from config import METRICAS_ACUMULATIVAS, MINUTOS_NORMALIZACION, MINUTOS_MINIMOS


def normalizar_a_94min(df, metricas_acumulativas):
    """
    Normaliza métricas acumulativas a 94 minutos
    
    Args:
        df (pd.DataFrame): DataFrame con datos
        metricas_acumulativas (list): Lista de métricas a normalizar
        
    Returns:
        pd.DataFrame: DataFrame con columnas normalizadas añadidas
    """
    df_norm = df.copy()
    
    for metrica in metricas_acumulativas:
        if metrica in df_norm.columns:
            df_norm[f'{metrica}_94min'] = df_norm[metrica] * (MINUTOS_NORMALIZACION / df_norm['time'])
    
    return df_norm


def calcular_referencias_normalizadas(df_rango):
    """
    Calcula estadísticas normalizadas a 94 minutos en formato transpuesto
    Solo incluye jugadores con >60 minutos
    
    Args:
        df_rango (pd.DataFrame): DataFrame con datos del rango seleccionado
        
    Returns:
        pd.DataFrame: DataFrame transpuesto con estadísticas
            Primera columna: 'Estadistica' (Media, P75, P90, etc.)
            Resto columnas: Métricas (hsr, sprints, etc.)
    """
    # Filtrar jugadores con >60 minutos
    df_filtrado = df_rango[df_rango['time'] > MINUTOS_MINIMOS].copy()
    
    if len(df_filtrado) == 0:
        return None
    
    # Normalizar métricas acumulativas
    df_filtrado = normalizar_a_94min(df_filtrado, METRICAS_ACUMULATIVAS)
    
    # Métricas para calcular estadísticas
    metricas_stats = []
    
    # Añadir métricas acumulativas normalizadas
    for metrica in METRICAS_ACUMULATIVAS:
        if f'{metrica}_94min' in df_filtrado.columns:
            metricas_stats.append((metrica, f'{metrica}_94min'))
    
    # Añadir métricas relativas (no se normalizan)
    metricas_relativas = ['minute_distance', 'max_speed', 'hsr_rel', 'hmld_relative']
    for metrica in metricas_relativas:
        if metrica in df_filtrado.columns:
            metricas_stats.append((metrica, metrica))
    
    # Diccionario para almacenar estadísticas por métrica (transpuesto)
    estadisticas_dict = {}
    
    for nombre_metrica, columna_datos in metricas_stats:
        datos = df_filtrado[columna_datos].dropna()
        
        if len(datos) > 0:
            estadisticas_dict[nombre_metrica] = {
                'Count': len(datos),
                'Media': round(datos.mean(), 2),
                'Mediana': round(datos.median(), 2),
                'Desv_Std': round(datos.std(), 2),
                'Min': round(datos.min(), 2),
                'Max': round(datos.max(), 2),
                'P25': round(datos.quantile(0.25), 2),
                'P50': round(datos.quantile(0.50), 2),
                'P70': round(datos.quantile(0.70), 2),
                'P75': round(datos.quantile(0.75), 2),
                'P80': round(datos.quantile(0.80), 2),
                'P85': round(datos.quantile(0.85), 2),
                'P90': round(datos.quantile(0.90), 2),
                'P95': round(datos.quantile(0.95), 2),
                'Lim_Inf_2SD': round(datos.mean() - 2*datos.std(), 2),
                'Lim_Sup_2SD': round(datos.mean() + 2*datos.std(), 2)
            }
    
    # Crear DataFrame transpuesto
    if estadisticas_dict:
        df_stats = pd.DataFrame(estadisticas_dict)
        # El índice actual son las estadísticas (Media, Mediana, etc.)
        # Las columnas son las métricas (hsr, sprints, etc.)
        # Resetear índice para que "Estadistica" sea una columna
        df_stats = df_stats.reset_index()
        df_stats.rename(columns={'index': 'Estadistica'}, inplace=True)
        return df_stats
    
    return None


def calcular_estadisticas_partido(df_partido, metrica):
    """
    Calcula estadísticas de una métrica para un partido
    
    Args:
        df_partido (pd.DataFrame): Datos del partido
        metrica (str): Nombre de la métrica
        
    Returns:
        dict: Diccionario con estadísticas
    """
    valores = df_partido[metrica].dropna()
    
    if len(valores) == 0:
        return None
    
    stats = {
        'media': round(valores.mean(), 2),
        'mediana': round(valores.median(), 2),
        'min': round(valores.min(), 2),
        'max': round(valores.max(), 2),
        'desv_std': round(valores.std(), 2),
        'count': len(valores)
    }
    
    return stats


def obtener_referencia_metrica(df_referencias, metrica):
    """
    Obtiene la referencia de una métrica específica (formato transpuesto)
    
    Args:
        df_referencias (pd.DataFrame): DataFrame transpuesto con referencias
            Primera columna: 'Estadistica'
            Resto: Métricas como columnas
        metrica (str): Nombre de la métrica
        
    Returns:
        dict or None: Diccionario con las estadísticas de la métrica o None
    """
    if df_referencias is None or len(df_referencias) == 0:
        return None
    
    # Verificar si la métrica existe como columna
    if metrica not in df_referencias.columns:
        return None
    
    # Convertir columna de métrica a diccionario
    # índice = 'Estadistica', valores = valores de la métrica
    resultado = {}
    for idx, row in df_referencias.iterrows():
        estadistica = row['Estadistica']
        valor = row[metrica]
        resultado[estadistica] = valor
    
    return resultado


def calcular_evolucion_temporal(df, metrica, agrupar_por='date'):
    """
    Calcula la evolución temporal de una métrica
    
    Args:
        df (pd.DataFrame): DataFrame con datos
        metrica (str): Nombre de la métrica
        agrupar_por (str): Campo por el que agrupar
        
    Returns:
        pd.DataFrame: DataFrame con evolución
    """
    evolucion = df.groupby(agrupar_por)[metrica].agg([
        ('media', 'mean'),
        ('mediana', 'median'),
        ('max', 'max'),
        ('min', 'min')
    ]).reset_index()
    
    evolucion = evolucion.sort_values(agrupar_por)
    
    return evolucion


def calcular_z_score(valor, media, desv_std):
    """
    Calcula el z-score de un valor
    
    Args:
        valor (float): Valor a evaluar
        media (float): Media de referencia
        desv_std (float): Desviación estándar de referencia
        
    Returns:
        float: Z-score
    """
    if desv_std == 0:
        return 0
    
    return (valor - media) / desv_std


def clasificar_rendimiento(z_score):
    """
    Clasifica el rendimiento según el z-score
    
    Args:
        z_score (float): Z-score del jugador
        
    Returns:
        str: Clasificación del rendimiento
    """
    if z_score >= 1.5:
        return "🟢 Excepcional"
    elif z_score >= 0.5:
        return "✅ Por encima"
    elif z_score >= -0.5:
        return "🟡 Normal"
    elif z_score >= -1.5:
        return "🟠 Por debajo"
    else:
        return "🔴 Muy bajo"