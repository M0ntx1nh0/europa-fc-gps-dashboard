"""
Módulo de autenticación para Europa FC GPS
Gestión de usuarios desde Google Drive
"""

import base64
import hashlib
import hmac
import json
import os
import time

import streamlit as st
from utils.drive_loader import cargar_usuarios_desde_drive
from utils.drive_loader import obtener_escudo_path

TOKEN_PARAM = "auth_token"
TOKEN_TTL_HORAS = 8


def _b64_encode(data):
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(texto):
    padding = "=" * (-len(texto) % 4)
    return base64.urlsafe_b64decode((texto + padding).encode("utf-8"))


def _obtener_auth_secret():
    # Prioridad: secrets -> env -> fallback local
    try:
        if hasattr(st, "secrets") and "auth_secret_key" in st.secrets:
            return str(st.secrets["auth_secret_key"])
    except Exception:
        pass
    return os.getenv("AUTH_SECRET_KEY", "europa_auth_dev_change_me")


def _firmar_payload(payload_json):
    secret = _obtener_auth_secret().encode("utf-8")
    return hmac.new(secret, payload_json.encode("utf-8"), hashlib.sha256).hexdigest()


def _generar_token(usuario):
    payload = {
        "usuario": str(usuario),
        "exp": int(time.time()) + (TOKEN_TTL_HORAS * 3600),
    }
    payload_json = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
    payload_b64 = _b64_encode(payload_json.encode("utf-8"))
    signature = _firmar_payload(payload_json)
    return f"{payload_b64}.{signature}"


def _validar_token(token):
    try:
        partes = str(token).split(".")
        if len(partes) != 2:
            return None

        payload_b64, signature = partes
        payload_json = _b64_decode(payload_b64).decode("utf-8")
        firma_esperada = _firmar_payload(payload_json)

        if not hmac.compare_digest(signature, firma_esperada):
            return None

        payload = json.loads(payload_json)
        if int(payload.get("exp", 0)) < int(time.time()):
            return None

        return payload
    except Exception:
        return None


def _get_query_param(nombre):
    try:
        valor = st.query_params.get(nombre)
        if isinstance(valor, list):
            return valor[0] if valor else None
        return valor
    except Exception:
        valores = st.experimental_get_query_params().get(nombre, [])
        return valores[0] if valores else None


def _set_query_param(nombre, valor):
    try:
        st.query_params[nombre] = valor
    except Exception:
        st.experimental_set_query_params(**{nombre: valor})


def _remove_query_param(nombre):
    try:
        params = dict(st.query_params)
        params.pop(nombre, None)
        st.query_params.clear()
        for k, v in params.items():
            st.query_params[k] = v
    except Exception:
        params = st.experimental_get_query_params()
        params.pop(nombre, None)
        st.experimental_set_query_params(**params)


def _iniciar_sesion(user_data):
    st.session_state.autenticado = True
    st.session_state.usuario = user_data['nombre']
    st.session_state.usuario_login = user_data['usuario']
    st.session_state.rol = user_data['rol']


def _obtener_usuario_por_login(usuario_login):
    try:
        df_usuarios = cargar_usuarios_desde_drive()
        if df_usuarios is None or df_usuarios.empty:
            return None

        usuario_data = df_usuarios[df_usuarios['usuario'] == usuario_login]
        if usuario_data.empty:
            return None

        return {
            'nombre': usuario_data.iloc[0]['nombre'],
            'usuario': usuario_data.iloc[0]['usuario'],
            'rol': usuario_data.iloc[0]['rol']
        }
    except Exception:
        return None


def _autenticar_desde_token():
    token = _get_query_param(TOKEN_PARAM)
    if not token:
        return False

    payload = _validar_token(token)
    if payload is None:
        _remove_query_param(TOKEN_PARAM)
        return False

    usuario_login = payload.get("usuario")
    user_data = _obtener_usuario_por_login(usuario_login)
    if not user_data:
        _remove_query_param(TOKEN_PARAM)
        return False

    _iniciar_sesion(user_data)
    return True


def verificar_credenciales(usuario, contraseña):
    """
    Verifica si las credenciales son válidas contra el CSV en Drive
    
    Args:
        usuario (str): Nombre de usuario
        contraseña (str): Contraseña
        
    Returns:
        dict: Información del usuario si es válido, None si no
    """
    try:
        # Cargar usuarios desde Drive
        df_usuarios = cargar_usuarios_desde_drive()
        
        if df_usuarios is None or df_usuarios.empty:
            st.error("⚠️ No se pudo cargar la lista de usuarios")
            return None
        
        # Buscar usuario
        usuario_data = df_usuarios[df_usuarios['usuario'] == usuario]
        
        if usuario_data.empty:
            return None
        
        # Verificar contraseña (convertir a string por si acaso)
        if str(usuario_data.iloc[0]['contraseña']) == str(contraseña):
            return {
                'nombre': usuario_data.iloc[0]['nombre'],
                'usuario': usuario_data.iloc[0]['usuario'],
                'rol': usuario_data.iloc[0]['rol']
            }
        
        return None
        
    except Exception as e:
        st.error(f"❌ Error verificando credenciales: {str(e)}")
        return None


def mostrar_login():
    """
    Muestra el formulario de login
    
    Returns:
        bool: True si el usuario está autenticado
    """
    # Si ya está autenticado, retornar True
    if st.session_state.get('autenticado', False):
        return True

    # Intentar login persistente (recordarme)
    if _autenticar_desde_token():
        return True
    
    # CSS para el login
    st.markdown("""
    <style>
        .login-header {
            text-align: center;
            color: #1f77b4;
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Contenedor centrado
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo
        try:
            st.image(obtener_escudo_path(), width=200)
        except:
            st.markdown("⚽")
        
        st.markdown('<div class="login-header">Europa FC GPS</div>', unsafe_allow_html=True)
        st.markdown("### 🔐 Acceso Restringido")
        
        # Formulario de login
        with st.form("login_form"):
            usuario = st.text_input("👤 Usuario:", key="login_usuario")
            contraseña = st.text_input("🔑 Contraseña:", type="password", key="login_contraseña")
            recordar_sesion = st.checkbox("Recordarme en este navegador (8h)", value=True)
            
            submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True)
            
            if submitted:
                if not usuario or not contraseña:
                    st.error("⚠️ Por favor, completa todos los campos")
                else:
                    user_data = verificar_credenciales(usuario, contraseña)
                    
                    if user_data:
                        _iniciar_sesion(user_data)
                        if recordar_sesion:
                            token = _generar_token(user_data['usuario'])
                            _set_query_param(TOKEN_PARAM, token)
                        else:
                            _remove_query_param(TOKEN_PARAM)
                        st.success(f"✅ Bienvenido, {user_data['nombre']}")
                        st.rerun()
                    else:
                        st.error("❌ Usuario o contraseña incorrectos")
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #666; font-size: 0.8rem;'>
            <p>Sistema de Análisis GPS</p>
            <p>Europa FC - Usuarios gestionados desde Drive</p>
        </div>
        """, unsafe_allow_html=True)
    
    return False


def cerrar_sesion():
    """
    Cierra la sesión actual
    """
    st.session_state.autenticado = False
    st.session_state.usuario = None
    st.session_state.usuario_login = None
    st.session_state.rol = None
    _remove_query_param(TOKEN_PARAM)
    st.rerun()


def mostrar_info_usuario():
    """
    Muestra información del usuario en el sidebar
    """
    if st.session_state.get('autenticado', False):
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"👤 **{st.session_state.get('usuario', 'Usuario')}**")
            st.caption(f"Rol: {st.session_state.get('rol', 'viewer')}")
            
            if st.button("🚪 Cerrar Sesión", use_container_width=True):
                cerrar_sesion()
