"""
Módulo de autenticación para Europa FC GPS
Gestión de usuarios desde Google Drive
"""

import streamlit as st
from utils.drive_loader import cargar_usuarios_desde_drive


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
            st.image("assets/Escudo/Escudo.png", width=200)
        except:
            st.markdown("⚽")
        
        st.markdown('<div class="login-header">Europa FC GPS</div>', unsafe_allow_html=True)
        st.markdown("### 🔐 Acceso Restringido")
        
        # Formulario de login
        with st.form("login_form"):
            usuario = st.text_input("👤 Usuario:", key="login_usuario")
            contraseña = st.text_input("🔑 Contraseña:", type="password", key="login_contraseña")
            
            submitted = st.form_submit_button("Iniciar Sesión", use_container_width=True)
            
            if submitted:
                if not usuario or not contraseña:
                    st.error("⚠️ Por favor, completa todos los campos")
                else:
                    user_data = verificar_credenciales(usuario, contraseña)
                    
                    if user_data:
                        st.session_state.autenticado = True
                        st.session_state.usuario = user_data['nombre']
                        st.session_state.usuario_login = user_data['usuario']
                        st.session_state.rol = user_data['rol']
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