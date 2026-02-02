"""
Módulo para carga de datos desde Google Drive
"""

import pandas as pd
import streamlit as st
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
import os
import json
from pathlib import Path
import tempfile

# IDs de carpetas en Google Drive
FOLDER_IDS = {
    'europa': '1VEUshVeUc2ql5qoiy1uBoM4SKSAUgMSP',
    'datos': '18Nve5WnlrNTGs2LGuzhpEldbVMuLUwH_',
    'fotos_jugadores': '1IZxw0TkG8d82UjteI5L5cRe78i-QFiey',
    'plantilla': '1YEmQ57mtxXSg-6TEDiS1BrSQNyjMm9Kj',
    'referencias_94min': '1oG5gTFjFgSc-CNvS0rpzY2UaG8KNeQJ3'
}


def autenticar_google_drive():
    """
    Autentica con Google Drive usando Service Account
    
    Returns:
        GoogleDrive: Objeto de conexión a Drive
    """
    try:
        # Determinar ruta del service account
        service_account_path = None
        
        # Intentar obtener de Streamlit Secrets (producción)
        try:
            if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
                # PRODUCCIÓN: Crear archivo temporal con las credenciales
                service_account_info = dict(st.secrets["gcp_service_account"])
                
                with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                    json.dump(service_account_info, f)
                    service_account_path = f.name
            else:
                raise FileNotFoundError("No secrets")
        except (FileNotFoundError, AttributeError, KeyError):
            # LOCAL: Usar archivo service_account.json
            local_path = Path(__file__).parent.parent / 'service_account.json'
            
            if not local_path.exists():
                st.error(f"❌ No se encuentra service_account.json en {local_path}")
                return None
            
            service_account_path = str(local_path)
        
        # Configurar PyDrive2 con Service Account
        settings = {
            "client_config_backend": "service",
            "service_config": {
                "client_json_file_path": service_account_path,
            }
        }
        
        # Autenticar
        gauth = GoogleAuth(settings=settings)
        gauth.ServiceAuth()
        
        # Crear drive
        drive = GoogleDrive(gauth)
        
        st.success("✅ Conectado a Google Drive")
        
        # Limpiar archivo temporal si se creó
        if service_account_path and service_account_path.endswith('.json') and 'tmp' in service_account_path:
            try:
                os.unlink(service_account_path)
            except:
                pass
        
        return drive
        
    except Exception as e:
        st.error(f"❌ Error autenticando con Google Drive: {str(e)}")
        st.exception(e)
        return None


def listar_archivos_carpeta(drive, folder_id, patron='*.csv'):
    """
    Lista archivos de una carpeta de Drive
    
    Args:
        drive: Objeto GoogleDrive
        folder_id: ID de la carpeta
        patron: Patrón de archivos a buscar
        
    Returns:
        list: Lista de archivos
    """
    try:
        query = f"'{folder_id}' in parents and trashed=false"
        file_list = drive.ListFile({'q': query}).GetList()
        
        # Filtrar por patrón si es necesario
        if patron and patron != '*':
            import fnmatch
            patron = patron.replace('*.', '.')  # Convertir *.csv a .csv
            file_list = [f for f in file_list if fnmatch.fnmatch(f['title'], f"*{patron}")]
        
        return file_list
        
    except Exception as e:
        st.error(f"❌ Error listando archivos: {str(e)}")
        return []


@st.cache_data(ttl=3600)  # Cache por 1 hora
def cargar_datos_desde_drive(equipo='europa'):
    """
    Carga todos los archivos CSV de la carpeta de datos en Drive
    
    Args:
        equipo (str): Nombre del equipo (por ahora solo 'europa')
        
    Returns:
        pd.DataFrame: DataFrame concatenado con todos los datos
    """
    drive = autenticar_google_drive()
    
    if drive is None:
        return None
    
    # Obtener ID de carpeta de datos
    folder_id = FOLDER_IDS['datos']
    
    # Listar archivos CSV
    archivos = listar_archivos_carpeta(drive, folder_id, patron='*.csv')
    
    if not archivos:
        st.warning(f"⚠️ No se encontraron archivos CSV en la carpeta de datos")
        return None
    
    st.info(f"📂 Encontrados {len(archivos)} archivos CSV en Drive")
    
    dfs = []
    archivos_procesados = 0
    archivos_con_error = 0
    
    # Crear directorio temporal
    with tempfile.TemporaryDirectory() as temp_dir:
        for archivo in archivos:
            try:
                # Descargar archivo temporal
                temp_path = os.path.join(temp_dir, archivo['title'])
                archivo.GetContentFile(temp_path)
                
                # Leer CSV
                df = pd.read_csv(
                    temp_path,
                    sep=';',
                    decimal=',',
                    thousands='.',
                    encoding='utf-8'
                )
                
                dfs.append(df)
                archivos_procesados += 1
                
            except Exception as e:
                archivos_con_error += 1
                st.warning(f"⚠️ Error leyendo {archivo['title']}: {str(e)}")
    
    if dfs:
        df_completo = pd.concat(dfs, ignore_index=True)
        
        # Mensajes informativos
        if archivos_procesados > 0:
            st.success(f"✅ {archivos_procesados} archivos cargados desde Google Drive")
        if archivos_con_error > 0:
            st.warning(f"⚠️ {archivos_con_error} archivos con errores")
        
        return df_completo
    
    return None


@st.cache_data(ttl=3600)
def cargar_plantilla_desde_drive(equipo='europa'):
    """
    Carga el archivo de plantilla desde Drive
    
    Args:
        equipo (str): Nombre del equipo
        
    Returns:
        pd.DataFrame: DataFrame con información de la plantilla
    """
    drive = autenticar_google_drive()
    
    if drive is None:
        return None
    
    folder_id = FOLDER_IDS['plantilla']
    
    # Buscar archivo Excel de plantilla
    archivos = listar_archivos_carpeta(drive, folder_id, patron='*.xlsx')
    
    if not archivos:
        st.warning("⚠️ No se encontró archivo de plantilla en Drive")
        return None
    
    # Usar el primer archivo encontrado
    archivo = archivos[0]
    
    try:
        # Descargar temporalmente
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            archivo.GetContentFile(tmp_file.name)
            df_plantilla = pd.read_excel(tmp_file.name)
            os.unlink(tmp_file.name)
        
        st.success(f"✅ Plantilla cargada desde Drive: {archivo['title']}")
        return df_plantilla
        
    except Exception as e:
        st.error(f"❌ Error cargando plantilla: {str(e)}")
        return None


def obtener_ruta_foto_jugador_drive(jugador):
    """
    Obtiene la ruta de foto de un jugador desde Drive
    (Por ahora, placeholder para implementar después)
    
    Args:
        jugador (str): Nombre del jugador
        
    Returns:
        str: Ruta a la foto del jugador
    """
    # Por ahora, devolver ruta local por defecto
    from utils.visualizations import obtener_foto_jugador
    return obtener_foto_jugador(jugador)


def obtener_info_dataset(df):
    """
    Obtiene información básica del dataset
    (Mantener compatibilidad con código existente)
    
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