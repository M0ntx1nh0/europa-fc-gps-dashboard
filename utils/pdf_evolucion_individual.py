"""
Generador de PDF para Informes de Evolución Individual
"""

from fpdf import FPDF
from datetime import datetime
import tempfile
import os
from pathlib import Path

class PDFEvolucionIndividual(FPDF):
    """PDF personalizado con header y footer"""
    
    def __init__(self, fecha_desde, fecha_hasta):
        super().__init__()
        self.COLOR_AZUL = (1, 97, 157)  # #01619d
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        
    def header(self):
        """Header con escudo y fecha en todas las páginas excepto portada"""
        if self.page_no() > 1:
            # Escudo arriba a la derecha (AÚN MÁS ARRIBA)
            escudo_path = escudo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "Escudo", "Escudo.png")
            if os.path.exists(escudo_path):
                self.image(escudo_path, x=175, y=6, w=20)  # ← y=6 (antes 8)
            
            # Fecha arriba a la izquierda (ALINEADA CON CENTRO DEL ESCUDO)
            self.set_font('Arial', 'I', 9)
            self.set_text_color(100, 100, 100)
            periodo = f"{self.fecha_desde.strftime('%d/%m/%Y')} - {self.fecha_hasta.strftime('%d/%m/%Y')}"
            self.text(10, 16, periodo)  # ← y=16 (6 + 20/2 = 16, centro del escudo)
            
            # Línea separadora azul (AÚN MÁS ARRIBA)
            self.set_draw_color(*self.COLOR_AZUL)
            self.set_line_width(0.5)
            self.line(10, 26, 200, 26)  # ← y=26 (antes 28)
            self.ln(20)  # ← ln(20) (antes 23) - AÚN MENOS ESPACIO
    
    def footer(self):
        """Footer con número de página"""
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'Página {self.page_no()-1}', 0, 0, 'C')


def generar_pdf_evolucion_individual(
    jugadores_datos,
    metricas_seleccionadas,
    estadistica_jugador,
    estadistica_posicion,
    fecha_desde,
    fecha_hasta,
    df_rango,
    METRICAS_DICT,
    COLORES
):
    """
    Genera PDF con evolución individual
    """
    
    pdf = PDFEvolucionIndividual(fecha_desde, fecha_hasta)
    
    # ========================================
    # PORTADA (TODO EN 1 PÁGINA)
    # ========================================
    
    pdf.add_page()
    
    # Fondo blanco (por defecto)
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(0, 0, 210, 297, 'F')
    
    # Línea vertical azul a la izquierda
    pdf.set_draw_color(*pdf.COLOR_AZUL)
    pdf.set_line_width(3)
    pdf.line(40, 20, 40, 277)  # Vertical desde arriba hasta abajo
    
    # Escudo arriba a la izquierda (a la izquierda de la línea)
    escudo_path = escudo_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "Escudo", "Escudo.png")
    if os.path.exists(escudo_path):
        pdf.image(escudo_path, x=10, y=20, w=25)
    
    # Alex Bosch abajo a la izquierda
    pdf.set_xy(10, 260)
    pdf.set_font('Arial', 'I', 12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(30, 10, 'Alex Bosch', 0, 0, 'L')
    
    # DERECHA: Título + Fecha (centrado verticalmente)
    pdf.set_xy(50, 130)
    pdf.set_font('Arial', 'B', 28)
    pdf.set_text_color(*pdf.COLOR_AZUL)
    pdf.multi_cell(150, 12, 'Informe de Evaluación\nIndividual', 0, 'C')
    
    # Fecha debajo del título
    pdf.set_xy(50, pdf.get_y() + 10)
    pdf.set_font('Arial', '', 12)
    pdf.set_text_color(80, 80, 80)
    periodo_texto = f"{fecha_desde.strftime('%B %Y')} - {fecha_hasta.strftime('%B %Y')}"
    pdf.cell(150, 10, periodo_texto, 0, 1, 'C')
    
    # ========================================
    # PÁGINAS DE JUGADORES
    # ========================================
    
    for jugador_data in jugadores_datos:
        nombre = jugador_data['nombre']
        posicion = jugador_data['posicion']
        foto_path = jugador_data['foto_path']
        stats = jugador_data['stats']
        df_completos_por_metrica = jugador_data['df_completos_por_metrica']
        
        # ========================================
        # PÁGINA DE DATOS DEL JUGADOR
        # ========================================
        
        pdf.add_page()
        
        # Título
        pdf.set_font('Arial', 'B', 20)
        pdf.set_text_color(*pdf.COLOR_AZUL)
        pdf.cell(0, 15, nombre, 0, 1, 'C')
        
        pdf.ln(5)
        
        # Foto del jugador (centrada, SIN ESTIRAR)
        if os.path.exists(foto_path):
            # Mantener aspect ratio
            pdf.image(foto_path, x=80, y=pdf.get_y(), h=50)  # Solo height, mantiene proporción
            pdf.ln(55)
        
        # Tarjeta de información básica
        y_inicial = pdf.get_y()
        
        # TARJETA: Posición y Período
        draw_card(pdf, y_inicial, "Información General", [
            f"Posición: {posicion}",
            f"Período: {fecha_desde.strftime('%d/%m/%Y')} - {fecha_hasta.strftime('%d/%m/%Y')}"
        ])
        
        pdf.ln(5)
        
        # TARJETAS DE MÉTRICAS (2 por fila, CENTRADAS VERTICALMENTE)
        metricas_por_fila = 4
        y_card = pdf.get_y()
        
        for idx, metrica_col in enumerate(metricas_seleccionadas):
            metrica_nombre = [k for k, v in METRICAS_DICT.items() if v == metrica_col][0]
            stat = stats.get(metrica_col, {})
            
            # Posición X de la tarjeta
            col_num = idx % metricas_por_fila
            x_card = 10 + (col_num * 47.5)
            
            # Si es el inicio de una nueva fila
            if col_num == 0 and idx > 0:
                y_card = pdf.get_y() + 5
            
            # Contenido de la tarjeta
            contenido = [
                f"Media: {stat.get('media', 0):.1f}",
                f"Mejor: {stat.get('mejor', 0):.1f}",
                f"Peor: {stat.get('peor', 0):.1f}",
                f"vs Ref: {stat.get('vs_ref', 0):+.1f}"
            ]
            
            draw_card_small(pdf, x_card, y_card, metrica_nombre, contenido)
            
            # Mover Y después de cada fila completa
            if col_num == metricas_por_fila - 1:
                pdf.set_y(y_card + 40)
        
        # Ajustar posición final si quedaron tarjetas incompletas
        if len(metricas_seleccionadas) % metricas_por_fila != 0:
            pdf.set_y(y_card + 40)
        
        # ========================================
        # PÁGINAS DE GRÁFICOS (2 POR PÁGINA)
        # ========================================
        
        graficos_por_pagina = 2
        total_metricas = len(metricas_seleccionadas)
        
        for idx_metrica, metrica_col in enumerate(metricas_seleccionadas):
            metrica_nombre = [k for k, v in METRICAS_DICT.items() if v == metrica_col][0]
            
            # Obtener df_completo específico para esta métrica
            df_completo_metrica = df_completos_por_metrica.get(metrica_col)
            
            if df_completo_metrica is None:
                continue
            
            # Nueva página cada 2 gráficos
            if idx_metrica % graficos_por_pagina == 0:
                pdf.add_page()
                y_inicial_pagina = pdf.get_y()
            
            # Posición Y del gráfico
            if idx_metrica % graficos_por_pagina == 0:
                y_grafico = y_inicial_pagina
            else:
                y_grafico = y_inicial_pagina + 130  # Segunda mitad de la página
            
            pdf.set_y(y_grafico)
            
            # Título del gráfico
            pdf.set_font('Arial', 'B', 14)
            pdf.set_text_color(*pdf.COLOR_AZUL)
            pdf.cell(0, 8, f"Evolución de {metrica_nombre} - {nombre}", 0, 1, 'C')
            
            # Subtítulo con estadísticas (LEYENDA AQUÍ)
            pdf.set_font('Arial', 'I', 9)
            pdf.set_text_color(80, 80, 80)
            subtitulo = f"Línea jugador: {estadistica_jugador} {nombre} | Línea posición: {estadistica_posicion} {posicion}s"
            pdf.cell(0, 6, subtitulo, 0, 1, 'C')
            
            pdf.ln(2)
            
            # Generar gráfico
            fig = crear_grafico_evolucion(
                df_completo_metrica, 
                metrica_col, 
                metrica_nombre,
                nombre,
                posicion,
                estadistica_jugador,
                estadistica_posicion,
                COLORES
            )
            
            # Guardar gráfico como imagen temporal
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                tmp_path = tmp_file.name
                fig.savefig(tmp_path, dpi=120, bbox_inches='tight')
                
                import matplotlib.pyplot as plt
                plt.close(fig)
            
            # Insertar imagen en PDF (altura reducida para 2 por página)
            pdf.image(tmp_path, x=10, y=pdf.get_y(), w=190, h=110)
            
            # Eliminar archivo temporal
            os.unlink(tmp_path)
    
    # ========================================
    # GUARDAR PDF
    # ========================================
    
    # Crear nombre de archivo
    jugadores_str = "_".join([j['nombre'] for j in jugadores_datos[:3]])
    if len(jugadores_datos) > 3:
        jugadores_str += f"_y_{len(jugadores_datos)-3}_mas"
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"Informe_Evolucion_{jugadores_str}_{timestamp}.pdf"
    
    # Guardar en carpeta del proyecto
    project_dir = Path(__file__).parent.parent
    output_dir = project_dir / "informes_pdf"
    output_dir.mkdir(exist_ok=True)
    
    output_path = str(output_dir / filename)
    pdf.output(output_path)
    
    return output_path


def draw_card(pdf, y, titulo, contenido_lista):
    """
    Dibuja una tarjeta con borde azul
    """
    pdf.set_y(y)
    
    # Borde azul
    pdf.set_draw_color(*pdf.COLOR_AZUL)
    pdf.set_line_width(0.5)
    
    altura = 10 + (len(contenido_lista) * 8)
    pdf.rect(10, y, 190, altura)
    
    # Título
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(*pdf.COLOR_AZUL)
    pdf.set_xy(15, y + 3)
    pdf.cell(0, 8, titulo, 0, 1)
    
    # Contenido
    pdf.set_font('Arial', '', 10)
    pdf.set_text_color(60, 60, 60)
    for linea in contenido_lista:
        pdf.set_x(15)
        pdf.cell(0, 6, linea, 0, 1)
    
    pdf.set_y(y + altura + 3)


def draw_card_small(pdf, x, y, titulo, contenido_lista):
    """
    Dibuja una tarjeta pequeña (para métricas) CENTRADA VERTICALMENTE
    """
    # Borde azul
    pdf.set_draw_color(*pdf.COLOR_AZUL)
    pdf.set_line_width(0.5)
    
    ancho = 45
    altura = 35
    pdf.rect(x, y, ancho, altura)
    
    # Título
    pdf.set_font('Arial', 'B', 9)
    pdf.set_text_color(*pdf.COLOR_AZUL)
    pdf.set_xy(x + 2, y + 3)
    pdf.cell(ancho - 4, 6, titulo, 0, 1, 'C')
    
    # Contenido (CENTRADO VERTICALMENTE)
    pdf.set_font('Arial', '', 8)
    pdf.set_text_color(60, 60, 60)
    
    # Calcular altura total del contenido
    num_lineas = len(contenido_lista)
    altura_linea = 4.5
    altura_total_contenido = num_lineas * altura_linea
    
    # Calcular espacio disponible y centrar
    espacio_disponible = altura - 10  # 10 = título + padding
    padding_top = (espacio_disponible - altura_total_contenido) / 2
    
    y_inicial_contenido = y + 10 + padding_top
    
    for idx, linea in enumerate(contenido_lista):
        pdf.set_xy(x + 2, y_inicial_contenido + (idx * altura_linea))
        pdf.cell(ancho - 4, altura_linea, linea, 0, 0, 'L')


def crear_grafico_evolucion(df_completo, metrica_col, metrica_nombre, nombre_jugador, posicion, estadistica_jugador, estadistica_posicion, COLORES):
    """
    Crea gráfico de evolución usando MATPLOTLIB (con leyenda debajo)
    """
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    
    # Crear figura
    fig, ax = plt.subplots(figsize=(12, 5), dpi=120)
    
    # 1. BARRAS - Solo partidos donde jugó
    df_jugo = df_completo[df_completo[metrica_col].notna()].copy()
    
    if len(df_jugo) > 0:
        fechas_jugo = mdates.date2num(df_jugo['date'])
        valores_jugo = df_jugo[metrica_col].values
        
        ax.bar(fechas_jugo, valores_jugo, 
               width=0.8, 
               color=COLORES['primario'], 
               alpha=0.7, 
               label=f'{metrica_nombre} (real)',
               edgecolor='black',
               linewidth=0.5)
        
        # Etiquetas de valores de métrica
        for fecha, valor in zip(fechas_jugo, valores_jugo):
            ax.text(fecha, valor + max(valores_jugo)*0.02, 
                   f"{int(valor)}",  # ← MUESTRA VALOR DE LA MÉTRICA
                   ha='center', 
                   va='bottom', 
                   fontsize=7,
                   fontweight='bold')
    
    # 2. LÍNEA ACUMULADA DEL JUGADOR
    df_con_acum_jug = df_completo[df_completo['valor_acum_jugador'].notna()].copy()
    
    if len(df_con_acum_jug) > 0:
        fechas_jug = mdates.date2num(df_con_acum_jug['date'])
        valores_jug = df_con_acum_jug['valor_acum_jugador'].values
        
        ax.plot(fechas_jug, valores_jug,
               color='#ef4444',
               linewidth=2.5,
               linestyle='-',
               marker='o',
               markersize=6,
               label=f'{estadistica_jugador} {nombre_jugador}')
    
    # 3. LÍNEA ACUMULADA DE LA POSICIÓN
    df_con_acum_pos = df_completo[df_completo['valor_acum_posicion'].notna()].copy()
    
    if len(df_con_acum_pos) > 0:
        fechas_pos = mdates.date2num(df_con_acum_pos['date'])
        valores_pos = df_con_acum_pos['valor_acum_posicion'].values
        
        ax.plot(fechas_pos, valores_pos,
               color='#ef4444',
               linewidth=2,
               linestyle='--',
               label=f'{estadistica_posicion} {posicion}s')
    
    # Configuración de ejes
    ax.set_xlabel('Fecha del partido', fontsize=9, fontweight='bold')
    ax.set_ylabel(metrica_nombre, fontsize=9, fontweight='bold')
    
    # Formato de fechas
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right', fontsize=8)
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    
    # Leyenda ABAJO (fuera del gráfico)
    ax.legend(loc='upper center', 
             bbox_to_anchor=(0.5, -0.18), 
             ncol=3, 
             frameon=True,
             fontsize=8)
    
    # Ajustar layout
    plt.tight_layout()
    
    return fig