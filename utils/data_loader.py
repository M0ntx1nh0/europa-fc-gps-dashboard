"""
Módulo para carga de datos CSV
"""

import pandas as pd
import streamlit as st
import glob
from pathlib import Path


@st.cache_data
def cargar_datos_csv(carpeta_csv):
    """
    Carga todos los archivos CSV de la carpeta
    
    Args:
        carpeta_csv (str): Ruta a la carpeta con archivos CSV
        
    Returns:
        pd.DataFrame: DataFrame concatenado con todos los datos
    """
    archivos = glob.glob(str(Path(carpeta_csv) / 'total_report_*.csv'))
    
    if not archivos:
        return None
    
    dfs = []
    archivos_procesados = 0
    archivos_con_error = 0
    
    for archivo in archivos:
        try:
            # Leer CSV con formato europeo (decimal=',', thousands='.')
            df = pd.read_csv(
                archivo, 
                sep=';', 
                decimal=',', 
                thousands='.', 
                encoding='utf-8'
            )
            dfs.append(df)
            archivos_procesados += 1
            
        except Exception as e:
            archivos_con_error += 1
            st.warning(f"⚠️ Error leyendo {Path(archivo).name}: {str(e)}")
    
    if dfs:
        df_completo = pd.concat(dfs, ignore_index=True)
        
        # Mensaje informativo
        if archivos_procesados > 0:
            st.success(f"✅ {archivos_procesados} archivos cargados correctamente")
        if archivos_con_error > 0:
            st.warning(f"⚠️ {archivos_con_error} archivos con errores")
            
        return df_completo
    
    return None


def validar_columnas(df, columnas_requeridas):
    """
    Valida que el DataFrame tenga las columnas requeridas
    
    Args:
        df (pd.DataFrame): DataFrame a validar
        columnas_requeridas (list): Lista de columnas requeridas
        
    Returns:
        tuple: (bool, list) - (es_valido, columnas_faltantes)
    """
    columnas_presentes = set(df.columns)
    columnas_requeridas_set = set(columnas_requeridas)
    columnas_faltantes = columnas_requeridas_set - columnas_presentes
    
    es_valido = len(columnas_faltantes) == 0
    
    return es_valido, list(columnas_faltantes)


def obtener_info_dataset(df):
    """
    Obtiene información básica del dataset
    
    Args:
        df (pd.DataFrame): DataFrame a analizar
        
    Returns:
        dict: Diccionario con información del dataset
    """
    info = {
        'total_registros': len(df),
        'jugadores_unicos': df['player'].nunique() if 'player' in df.columns else 0,
        'partidos_unicos': df['date'].nunique() if 'date' in df.columns else 0,
        'fecha_min': df['date'].min() if 'date' in df.columns else None,
        'fecha_max': df['date'].max() if 'date' in df.columns else None,
        'columnas': list(df.columns),
        'memoria_mb': df.memory_usage(deep=True).sum() / 1024**2
    }
    
    return info
