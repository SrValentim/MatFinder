"""
structure_viewer.py
Widget de visualização 3D de estruturas cristalinas para PhaseDRX
Parte do projeto MatFinder - Copyright (C) 2025 Raynner Valentim (UFAM)
"""

import numpy as np
import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QCheckBox, QMessageBox, QDialog,
    QGroupBox, QDialogButtonBox, QFrame, QComboBox
)
from PySide6.QtCore import Qt, Slot
import pyqtgraph.opengl as gl
import pyqtgraph as pg

try:
    from pymatgen.core import Structure
    PYMATGEN_AVAILABLE = True
except ImportError:
    PYMATGEN_AVAILABLE = False
    logging.warning("pymatgen não disponível. Instale com: pip install pymatgen")


class StructureViewer3D(QWidget):
    """Widget para visualização interativa de estruturas cristalinas em 3D."""

    # Tabela de cores atômicas (formato RGB normalizado 0-1)
    # Baseada em cores padrão CPK e Jmol para visualização cristalográfica
    ATOMIC_COLORS = {
        'H': (1.0, 1.0, 1.0),      # Branco
        'He': (0.85, 1.0, 1.0),    # Ciano claro
        'Li': (0.8, 0.5, 1.0),     # Rosa
        'Be': (0.76, 1.0, 0.0),    # Verde-amarelo
        'B': (1.0, 0.71, 0.71),    # Salmão
        'C': (0.5, 0.5, 0.5),      # Cinza
        'N': (0.19, 0.31, 0.97),   # Azul
        'O': (1.0, 0.05, 0.05),    # Vermelho
        'F': (0.56, 0.88, 0.31),   # Verde claro
        'Ne': (0.7, 0.89, 0.96),   # Azul claro
        'Na': (0.67, 0.36, 0.95),  # Violeta
        'Mg': (0.54, 1.0, 0.0),    # Verde
        'Al': (0.75, 0.65, 0.65),  # Cinza rosado
        'Si': (0.94, 0.78, 0.63),  # Bege
        'P': (1.0, 0.5, 0.0),      # Laranja
        'S': (1.0, 1.0, 0.19),     # Amarelo
        'Cl': (0.12, 0.94, 0.12),  # Verde brilhante
        'Ar': (0.5, 0.82, 0.89),   # Azul celeste
        'K': (0.56, 0.25, 0.83),   # Roxo
        'Ca': (0.24, 1.0, 0.0),    # Verde lima
        'Sc': (0.90, 0.90, 0.90),  # Cinza claro
        'Ti': (0.75, 0.76, 0.78),  # Cinza prateado
        'V': (0.65, 0.65, 0.67),   # Cinza
        'Cr': (0.54, 0.6, 0.78),   # Azul aço
        'Mn': (0.61, 0.48, 0.78),  # Lilás
        'Fe': (0.88, 0.4, 0.2),    # Laranja ferrugem
        'Co': (0.94, 0.56, 0.63),  # Rosa
        'Ni': (0.31, 0.82, 0.31),  # Verde
        'Cu': (0.78, 0.5, 0.2),    # Cobre
        'Zn': (0.49, 0.5, 0.69),   # Azul acinzentado
        'Ga': (0.76, 0.56, 0.56),  # Marrom claro
        'Ge': (0.4, 0.56, 0.56),   # Cinza esverdeado
        'As': (0.74, 0.5, 0.89),   # Roxo claro
        'Se': (1.0, 0.63, 0.0),    # Laranja
        'Br': (0.65, 0.16, 0.16),  # Marrom avermelhado
        'Kr': (0.36, 0.72, 0.82),  # Azul claro
        'Rb': (0.44, 0.18, 0.69),  # Roxo escuro
        'Sr': (0.0, 1.0, 0.0),     # Verde
        'Y': (0.58, 1.0, 1.0),     # Ciano
        'Zr': (0.58, 0.88, 0.88),  # Ciano pálido
        'Nb': (0.45, 0.76, 0.79),  # Azul esverdeado
        'Mo': (0.33, 0.71, 0.71),  # Verde água
        'Tc': (0.23, 0.62, 0.62),  # Verde-azul escuro
        'Ru': (0.14, 0.56, 0.56),  # Azul escuro
        'Rh': (0.04, 0.49, 0.55),  # Azul
        'Pd': (0.0, 0.41, 0.52),   # Azul petróleo
        'Ag': (0.75, 0.75, 0.75),  # Prata
        'Cd': (1.0, 0.85, 0.56),   # Dourado claro
        'In': (0.65, 0.46, 0.45),  # Marrom
        'Sn': (0.4, 0.5, 0.5),     # Cinza
        'Sb': (0.62, 0.39, 0.71),  # Roxo
        'Te': (0.83, 0.48, 0.0),   # Laranja
        'I': (0.58, 0.0, 0.58),    # Violeta
        'Xe': (0.26, 0.62, 0.69),  # Azul celeste
        'Cs': (0.34, 0.09, 0.56),  # Roxo escuro
        'Ba': (0.0, 0.79, 0.0),    # Verde
        'La': (0.44, 0.83, 1.0),   # Azul claro (Lantanídeos)
        'Ce': (1.0, 1.0, 0.78),    # Amarelo claro
        'Pr': (0.85, 1.0, 0.78),   # Verde-amarelo claro
        'Nd': (0.78, 1.0, 0.78),   # Verde claro
        'Pm': (0.64, 1.0, 0.78),   # Verde
        'Sm': (0.56, 1.0, 0.78),   # Verde
        'Eu': (0.38, 1.0, 0.78),   # Verde
        'Gd': (0.27, 1.0, 0.78),   # Verde
        'Tb': (0.19, 1.0, 0.78),   # Verde
        'Dy': (0.12, 1.0, 0.78),   # Verde-ciano
        'Ho': (0.0, 1.0, 0.61),    # Ciano
        'Er': (0.0, 0.90, 0.46),   # Ciano
        'Tm': (0.0, 0.83, 0.32),   # Ciano escuro
        'Yb': (0.0, 0.75, 0.22),   # Verde-azul
        'Lu': (0.0, 0.67, 0.14),   # Verde-azul escuro
        'Hf': (0.30, 0.76, 1.0),   # Azul claro
        'Ta': (0.30, 0.65, 1.0),   # Azul
        'W': (0.13, 0.58, 0.84),   # Azul
        'Re': (0.15, 0.49, 0.67),  # Azul escuro
        'Os': (0.15, 0.40, 0.59),  # Azul escuro
        'Ir': (0.09, 0.33, 0.53),  # Azul muito escuro
        'Pt': (0.82, 0.82, 0.88),  # Platina
        'Au': (1.0, 0.82, 0.14),   # Ouro
        'Hg': (0.72, 0.72, 0.82),  # Cinza azulado
        'Tl': (0.65, 0.33, 0.30),  # Marrom
        'Pb': (0.34, 0.35, 0.38),  # Cinza chumbo
        'Bi': (0.62, 0.31, 0.71),  # Roxo
        'default': (0.8, 0.8, 0.8) # Cinza claro (fallback)
    }

    # Raios atômicos para visualização (em Angstroms)
    # Valores otimizados para visualização cristalográfica clara (este é o padrão 100%)
    # Baseados em raios iônicos típicos ajustados para boa percepção visual
    # Ajustados para tamanho ideal (reduzidos em 10% do valor anterior)
    ATOMIC_RADII = {
        'H': 0.41, 'He': 0.54, 'Li': 0.81, 'Be': 0.53, 'B': 0.79,
        'C': 0.69, 'N': 0.63, 'O': 0.66, 'F': 0.65, 'Ne': 0.64,
        'Na': 1.04, 'Mg': 0.77, 'Al': 0.61, 'Si': 0.49, 'P': 0.95,
        'S': 0.92, 'Cl': 0.89, 'Ar': 0.88, 'K': 1.37, 'Ca': 1.03,
        'Sc': 0.79, 'Ti': 0.68, 'V': 0.66, 'Cr': 0.68, 'Mn': 0.73,
        'Fe': 0.68, 'Co': 0.71, 'Ni': 0.69, 'Cu': 0.78, 'Zn': 0.79,
        'Ga': 0.68, 'Ge': 0.60, 'As': 0.65, 'Se': 0.93, 'Br': 1.03,
        'Kr': 0.93, 'Rb': 1.49, 'Sr': 1.19, 'Y': 0.94, 'Zr': 0.77,
        'Nb': 0.74, 'Mo': 0.71, 'Tc': 0.71, 'Ru': 0.74, 'Rh': 0.75,
        'Pd': 0.85, 'Ag': 1.04, 'Cd': 0.98, 'In': 0.85, 'Sn': 0.75,
        'Sb': 0.81, 'Te': 1.00, 'I': 1.20, 'Xe': 1.18, 'Cs': 1.63,
        'Ba': 1.34, 'La': 1.05, 'Ce': 1.04, 'Pr': 1.02, 'Nd': 1.01,
        'Pm': 1.00, 'Sm': 0.99, 'Eu': 0.98, 'Gd': 0.97, 'Tb': 0.95,
        'Dy': 0.95, 'Ho': 0.94, 'Er': 0.93, 'Tm': 0.92, 'Yb': 0.90,
        'Lu': 0.89, 'Hf': 0.77, 'Ta': 0.74, 'W': 0.72, 'Re': 0.69,
        'Os': 0.69, 'Ir': 0.69, 'Pt': 0.72, 'Au': 0.77, 'Hg': 0.92,
        'Tl': 0.93, 'Pb': 1.20, 'Bi': 1.05, 'Po': 0.97, 'At': 1.29,
        'Rn': 1.21, 'Fr': 1.75, 'Ra': 1.46, 'Ac': 1.13, 'Th': 0.97,
        'Pa': 0.94, 'U': 0.90, 'Np': 0.91, 'Pu': 0.90, 'Am': 0.89,
        'default': 0.77
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.structure = None
        self.atom_meshes = []
        self.bond_meshes = []
        self.unit_cell_lines = []
        self.atom_scale = 1.0
        self.bond_radius = 0.15  # Raio padrão dos cilindros de ligação (em Angstroms)
        self.supercell_expansion = [1, 1, 1]  # Expansão da célula [a, b, c]

        # Variáveis de controle de visibilidade
        self._show_bonds = True
        self._show_cell = True

        # Variáveis para animação
        self._animation_timer = None
        self._animation_angle = 0
        self._animation_type = None  # 'rotation_x', 'rotation_y', 'rotation_z', 'vibration'
        self._original_atom_positions = []

        self._init_ui()

    def _init_ui(self):
        """Inicializa a interface do visualizador."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Container para viewer principal com gizmo sobreposto
        from PySide6.QtWidgets import QFrame, QStackedLayout
        viewer_container = QWidget()
        viewer_container.setMinimumSize(400, 400)

        # Widget GLView para renderização 3D
        self.view_widget = gl.GLViewWidget(viewer_container)
        self.view_widget.setCameraPosition(distance=30, azimuth=45, elevation=30)
        self.view_widget.setBackgroundColor('w')  # Fundo branco

        # NOTA: Eixos XYZ (a, b, c) REMOVIDOS da estrutura principal
        # Agora aparecem APENAS no gizmo de orientação (canto inferior esquerdo)
        # com os ângulos CORRETOS da célula unitária (α, β, γ)

        # Criar widget de orientação (gizmo) no canto inferior esquerdo
        self._create_orientation_gizmo(viewer_container)

        # Criar legenda de elementos no canto superior direito
        self._create_element_legend(viewer_container)

        layout.addWidget(viewer_container, stretch=1)

        # Painel de controles - Layout compacto e discreto
        control_layout = QHBoxLayout()
        control_layout.setSpacing(5)
        control_layout.setContentsMargins(0, 0, 0, 0)

        # Label de informações (à esquerda) - clicável para expandir célula
        self.info_label = QLabel("Nenhuma estrutura carregada")
        self.info_label.setStyleSheet("color: gray; font-style: italic; font-size: 10pt;")
        self.info_label.setCursor(Qt.CursorShape.PointingHandCursor)  # Cursor de mão ao passar
        self.info_label.mouseDoubleClickEvent = self._open_supercell_dialog
        control_layout.addWidget(self.info_label)

        control_layout.addStretch()

        # Botão de reset da câmera
        reset_btn = QPushButton("↻")
        reset_btn.setFixedSize(28, 28)
        reset_btn.setToolTip("Resetar visualização da câmera")
        reset_btn.clicked.connect(self._reset_camera)
        control_layout.addWidget(reset_btn)

        layout.addLayout(control_layout)

        # Armazenar referência ao container para redimensionamento
        self.viewer_container = viewer_container

        # Iniciar sincronização periódica do gizmo
        self._start_gizmo_sync_timer()

    def _add_axes(self):
        """Adiciona eixos coordenados XYZ."""
        axis_length = 5
        axis_width = 2

        # Eixo X (vermelho)
        x_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [axis_length, 0, 0]]),
            color=(1, 0, 0, 1),
            width=axis_width,
            antialias=True
        )
        self.view_widget.addItem(x_axis)

        # Eixo Y (verde)
        y_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, axis_length, 0]]),
            color=(0, 1, 0, 1),
            width=axis_width,
            antialias=True
        )
        self.view_widget.addItem(y_axis)

        # Eixo Z (azul)
        z_axis = gl.GLLinePlotItem(
            pos=np.array([[0, 0, 0], [0, 0, axis_length]]),
            color=(0, 0, 1, 1),
            width=axis_width,
            antialias=True
        )
        self.view_widget.addItem(z_axis)

    def _create_orientation_gizmo(self, parent_container):
        """
        Cria o widget de orientação (gizmo) no canto inferior esquerdo.
        Usa os vetores REAIS da célula unitária (a, b, c) com ângulos corretos (α, β, γ).
        """
        # Container para o gizmo e labels
        self.gizmo_container = QWidget(parent_container)
        self.gizmo_container.setFixedSize(100, 100)
        self.gizmo_container.move(10, parent_container.height() - 110)

        # Criar um GLViewWidget pequeno para o gizmo
        self.orientation_gizmo = gl.GLViewWidget(self.gizmo_container)
        self.orientation_gizmo.setGeometry(0, 0, 100, 100)
        self.orientation_gizmo.setCameraPosition(distance=8, azimuth=45, elevation=30)
        self.orientation_gizmo.setBackgroundColor((240, 240, 240, 220))  # Fundo semi-transparente

        # Adicionar borda sutil
        self.orientation_gizmo.setStyleSheet("""
            QWidget {
                border: 1px solid rgba(0, 0, 0, 0.2);
                border-radius: 3px;
                background-color: rgba(240, 240, 240, 220);
            }
        """)

        # Desabilitar interação direta com o gizmo
        self.orientation_gizmo.setMouseTracking(False)
        self.orientation_gizmo.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        # Armazenar referência para poder atualizar depois
        self.gizmo_items = []

        self.gizmo_container.raise_()

    def _update_gizmo_with_lattice(self):
        """
        Atualiza o gizmo de orientação com os vetores REAIS da célula unitária.
        Chamado após carregar uma estrutura CIF.
        """
        if not self.structure or not hasattr(self, 'orientation_gizmo'):
            return

        # Limpar itens antigos do gizmo
        for item in self.gizmo_items:
            try:
                self.orientation_gizmo.removeItem(item)
            except:
                pass
        self.gizmo_items.clear()

        # Obter matriz da célula unitária (vetores a, b, c)
        lattice = self.structure.lattice
        lattice_matrix = lattice.matrix  # Shape: (3, 3) - cada linha é um vetor

        # Normalizar vetores para que fiquem do mesmo tamanho no gizmo
        gizmo_scale = 3.0  # Tamanho das setas no gizmo

        # Calcular vetores normalizados (proporcionalmente)
        max_length = max(lattice.a, lattice.b, lattice.c)

        vector_a = (lattice_matrix[0] / max_length) * gizmo_scale
        vector_b = (lattice_matrix[1] / max_length) * gizmo_scale
        vector_c = (lattice_matrix[2] / max_length) * gizmo_scale

        origin = np.array([0, 0, 0])

        # Adicionar seta para vetor a (vermelho)
        self._add_gizmo_arrow(self.orientation_gizmo,
                             origin,
                             vector_a,
                             color=(1.0, 0.0, 0.0, 1.0),
                             label='a')

        # Adicionar seta para vetor b (verde)
        self._add_gizmo_arrow(self.orientation_gizmo,
                             origin,
                             vector_b,
                             color=(0.0, 1.0, 0.0, 1.0),
                             label='b')

        # Adicionar seta para vetor c (azul)
        self._add_gizmo_arrow(self.orientation_gizmo,
                             origin,
                             vector_c,
                             color=(0.0, 0.0, 1.0, 1.0),
                             label='c')

        logging.debug(f"Gizmo atualizado com ângulos reais: α={lattice.alpha:.1f}°, β={lattice.beta:.1f}°, γ={lattice.gamma:.1f}°")


    def _add_gizmo_arrow(self, view_widget, start, end, color, label):
        """Adiciona uma seta ao gizmo de orientação."""
        # Linha do eixo
        line = gl.GLLinePlotItem(
            pos=np.array([start, end]),
            color=color,
            width=4,
            antialias=True
        )
        view_widget.addItem(line)
        self.gizmo_items.append(line)

        # Cone da ponta da seta (pequeno)
        direction = end - start
        length = np.linalg.norm(direction)
        direction = direction / length

        # Criar pequeno cone para a ponta
        cone_height = 0.3
        cone_radius = 0.15
        base_pos = end - direction * cone_height

        try:
            # Geometria simplificada do cone
            verts = []
            faces = []
            cols = 8

            # Vértice da ponta
            verts.append([0, 0, cone_height])

            # Base do cone
            for j in range(cols):
                theta = (j / cols) * 2 * np.pi
                x = cone_radius * np.cos(theta)
                y = cone_radius * np.sin(theta)
                verts.append([x, y, 0])

            # Centro da base
            verts.append([0, 0, 0])

            # Faces laterais
            for j in range(cols):
                v1 = j + 1
                v2 = (j + 1) % cols + 1
                faces.append([0, v1, v2])

            # Faces da base
            for j in range(cols):
                v1 = j + 1
                v2 = (j + 1) % cols + 1
                faces.append([len(verts) - 1, v2, v1])

            verts = np.array(verts)
            faces = np.array(faces)

            mesh_data = gl.MeshData(vertexes=verts, faces=faces)
            cone = gl.GLMeshItem(
                meshdata=mesh_data,
                smooth=True,
                color=color,
                shader='shaded',
                glOptions='opaque'
            )

            # Rotacionar cone para alinhar com a direção
            z_axis = np.array([0, 0, 1])
            rotation_axis = np.cross(z_axis, direction)
            rotation_axis_norm = np.linalg.norm(rotation_axis)

            if rotation_axis_norm > 1e-6:
                rotation_axis = rotation_axis / rotation_axis_norm
                cos_angle = np.dot(z_axis, direction)
                angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
                angle_deg = np.degrees(angle)
                cone.rotate(angle_deg, rotation_axis[0], rotation_axis[1], rotation_axis[2])
            elif np.dot(z_axis, direction) < 0:
                cone.rotate(180, 1, 0, 0)

            cone.translate(base_pos[0], base_pos[1], base_pos[2])
            view_widget.addItem(cone)
            self.gizmo_items.append(cone)
        except:
            pass

        # Nota: Labels são adicionados como QLabel 2D no método _create_gizmo_labels
        # pois GLTextItem não funciona bem em todos os ambientes

    def _create_gizmo_labels(self, container):
        """Cria labels 2D (a, b, c) sobrepostos no gizmo de orientação."""
        # Posições aproximadas dos labels (ajustadas para visão padrão azimuth=45, elevation=30)
        # Estas são posições 2D em pixels dentro do gizmo de 100x100

        label_configs = [
            {'text': 'a', 'color': '#FF0000', 'x': 75, 'y': 70},  # Vermelho, direita-baixo
            {'text': 'b', 'color': '#00FF00', 'x': 20, 'y': 75},  # Verde, esquerda-baixo
            {'text': 'c', 'color': '#0000FF', 'x': 50, 'y': 15},  # Azul, centro-topo
        ]

        self.gizmo_labels = []

        for config in label_configs:
            label = QLabel(config['text'], container)
            label.setStyleSheet(f"""
                color: {config['color']};
                font-size: 14pt;
                font-weight: bold;
                background: transparent;
                border: none;
            """)
            label.setAlignment(Qt.AlignCenter)
            label.setFixedSize(20, 20)
            label.move(config['x'], config['y'])
            label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            label.raise_()
            label.show()
            self.gizmo_labels.append(label)

    def _create_element_legend(self, parent_container):
        """Cria a legenda minimalista de elementos no canto superior direito."""
        from PySide6.QtWidgets import QVBoxLayout

        # Criar widget de legenda (sem fundo, totalmente transparente)
        self.element_legend = QWidget(parent_container)
        self.element_legend.setAttribute(Qt.WA_TranslucentBackground)
        self.element_legend.setStyleSheet("background: transparent;")

        # Layout vertical para os itens
        self.legend_layout = QVBoxLayout(self.element_legend)
        self.legend_layout.setContentsMargins(0, 0, 0, 0)
        self.legend_layout.setSpacing(5)
        self.legend_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)

        # Posicionar no canto superior direito
        self.element_legend.move(parent_container.width() - 80, 10)
        self.element_legend.raise_()

        # Inicialmente oculto
        self.element_legend.hide()

    def _update_element_legend(self):
        """Atualiza a legenda minimalista com esferas 3D dos elementos."""
        if not hasattr(self, 'element_legend') or not self.structure:
            return

        # Limpar itens anteriores
        while self.legend_layout.count():
            child = self.legend_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Obter elementos únicos da estrutura
        elements = set()
        for site in self.structure:
            elements.add(site.specie.symbol)

        # Ordenar elementos alfabeticamente
        elements = sorted(elements)

        # Se não houver elementos, ocultar legenda
        if not elements:
            self.element_legend.hide()
            return

        # Adicionar cada elemento à legenda com mini-esfera 3D
        for element in elements:
            # Obter cor do elemento
            color_rgb = self.ATOMIC_COLORS.get(element, self.ATOMIC_COLORS['default'])

            # Criar container para o item (esfera + texto)
            item_widget = QWidget()
            item_widget.setAttribute(Qt.WA_TranslucentBackground)
            item_widget.setStyleSheet("background: transparent;")

            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(0, 0, 0, 0)
            item_layout.setSpacing(8)

            # Criar mini-esfera 3D usando GLViewWidget
            sphere_view = gl.GLViewWidget()
            sphere_view.setFixedSize(30, 30)
            sphere_view.setCameraPosition(distance=4, azimuth=45, elevation=30)
            sphere_view.setBackgroundColor((255, 255, 255, 0))  # Fundo transparente

            # Desabilitar interação
            sphere_view.setEnabled(False)
            sphere_view.setAttribute(Qt.WA_TransparentForMouseEvents, True)

            # Criar mini-esfera
            radius = 0.8  # Raio fixo para a legenda
            mesh_data = gl.MeshData.sphere(rows=12, cols=12, radius=radius)
            sphere_mesh = gl.GLMeshItem(
                meshdata=mesh_data,
                smooth=True,
                color=(*color_rgb, 1.0),
                shader='shaded',
                glOptions='opaque'
            )
            sphere_view.addItem(sphere_mesh)

            item_layout.addWidget(sphere_view)

            # Nome do elemento (sem fundo, discreto)
            element_label = QLabel(element)
            element_label.setStyleSheet("""
                font-size: 12pt;
                font-weight: bold;
                color: #333;
                background: transparent;
            """)
            item_layout.addWidget(element_label)
            item_layout.addStretch()

            self.legend_layout.addWidget(item_widget)

        # Ajustar tamanho da legenda
        legend_height = len(elements) * 35
        legend_width = 80
        self.element_legend.setFixedSize(legend_width, legend_height)

        # Mostrar legenda
        self.element_legend.show()
        self.element_legend.raise_()

    def _sync_orientation_gizmo(self):
        """Sincroniza a orientação do gizmo com a câmera principal."""
        if hasattr(self, 'orientation_gizmo') and hasattr(self, 'view_widget'):
            try:
                # Obter parâmetros da câmera principal
                params = self.view_widget.cameraParams()

                # Aplicar mesma rotação ao gizmo (mas manter distância fixa)
                self.orientation_gizmo.setCameraPosition(
                    distance=8,
                    azimuth=params['azimuth'],
                    elevation=params['elevation']
                )
            except Exception as e:
                # Ignorar erros de sincronização silenciosamente
                pass

    def _start_gizmo_sync_timer(self):
        """Inicia timer para sincronizar o gizmo periodicamente."""
        from PySide6.QtCore import QTimer
        self._gizmo_sync_timer = QTimer()
        self._gizmo_sync_timer.timeout.connect(self._sync_orientation_gizmo)
        self._gizmo_sync_timer.start(50)  # Sincronizar a cada 50ms (~20 FPS)

    def resizeEvent(self, event):
        """Reposiciona o gizmo e a legenda quando a janela é redimensionada."""
        super().resizeEvent(event)

        if hasattr(self, 'viewer_container') and hasattr(self, 'view_widget'):
            # Ajustar tamanho do viewer principal ao container
            self.view_widget.resize(self.viewer_container.size())

        if hasattr(self, 'gizmo_container') and hasattr(self, 'viewer_container'):
            # Posicionar container do gizmo (que inclui os labels) no canto inferior esquerdo
            self.gizmo_container.move(10, self.viewer_container.height() - 110)
            self.gizmo_container.raise_()

        if hasattr(self, 'element_legend') and hasattr(self, 'viewer_container'):
            # Posicionar legenda no canto superior direito (minimalista)
            self.element_legend.move(self.viewer_container.width() - 90, 10)
            self.element_legend.raise_()

    def load_cif(self, cif_path):
        """
        Carrega um arquivo CIF e renderiza a estrutura.

        Args:
            cif_path (str): Caminho para o arquivo CIF

        Returns:
            bool: True se carregado com sucesso, False caso contrário
        """
        if not PYMATGEN_AVAILABLE:
            QMessageBox.warning(
                self,
                "Dependência Ausente",
                "A biblioteca 'pymatgen' não está instalada.\n\n"
                "Para instalar, execute:\npip install pymatgen"
            )
            logging.error("pymatgen não está instalado")
            return False

        try:
            # Ler estrutura do CIF
            self.structure = Structure.from_file(cif_path)
            formula = self.structure.composition.reduced_formula
            n_atoms = len(self.structure)

            logging.info(f"Estrutura carregada: {formula} ({n_atoms} átomos)")

            # Obter parâmetros de rede ANTES de qualquer operação
            lattice = self.structure.lattice
            a, b, c = lattice.a, lattice.b, lattice.c

            # Renderizar nova estrutura (isso limpa automaticamente os itens antigos)
            self._render_structure()

            # Atualizar gizmo de orientação com vetores reais da célula
            self._update_gizmo_with_lattice()

            # NÃO resetar câmera - manter posição/zoom atual
            # A câmera só será resetada manualmente pelo botão "Resetar Câmera"

            # Atualizar label de informações com parâmetros de rede
            info_html = f"""
            <div style='color: green; font-weight: bold;'>
                {formula} • {n_atoms} átomos<br>
                <span style='color: #FF0000;'>a={a:.3f}</span> 
                <span style='color: #00AA00;'>b={b:.3f}</span> 
                <span style='color: #0000FF;'>c={c:.3f}</span> Å
            </div>
            """
            self.info_label.setText(info_html)
            self.info_label.setTextFormat(Qt.TextFormat.RichText)

            # Atualizar legenda de elementos
            self._update_element_legend()

            return True

        except Exception as e:
            error_msg = f"Erro ao carregar CIF: {str(e)}"
            logging.error(error_msg)
            QMessageBox.critical(self, "Erro", error_msg)
            self.info_label.setText("Erro ao carregar estrutura")
            self.info_label.setStyleSheet("color: red;")

            # Limpar estrutura em caso de erro
            self.structure = None

            return False

    def _clear_structure(self):
        """Remove todos os elementos da visualização com proteção contra erros OpenGL."""
        n_atoms = len(self.atom_meshes)
        n_bonds = len(self.bond_meshes)
        n_lines = len(self.unit_cell_lines)

        logging.info(f"🧹 Limpando estrutura: {n_atoms} átomos, {n_bonds} ligações, {n_lines} linhas")

        try:
            for mesh in self.atom_meshes:
                try:
                    self.view_widget.removeItem(mesh)
                except (RuntimeError, AttributeError):
                    pass  # Widget já foi destruído

            for bond in self.bond_meshes:
                try:
                    self.view_widget.removeItem(bond)
                except (RuntimeError, AttributeError):
                    pass

            for line in self.unit_cell_lines:
                try:
                    self.view_widget.removeItem(line)
                except (RuntimeError, AttributeError):
                    pass
        except Exception as e:
            logging.warning(f"Erro ao limpar estrutura: {e}")
        finally:
            self.atom_meshes.clear()
            self.bond_meshes.clear()
            self.unit_cell_lines.clear()

            # Limpar também a estrutura
            self.structure = None

            # Atualizar label de informações
            if hasattr(self, 'info_label'):
                self.info_label.setText("Nenhuma estrutura carregada")
                self.info_label.setStyleSheet("color: gray; font-style: italic;")

            logging.info("✅ Estrutura completamente limpa")

    def _render_structure(self):
        """Renderiza a estrutura 3D com átomos, ligações e célula unitária."""
        if not self.structure:
            return

        # PROTEÇÃO: Não renderizar se widget está desabilitado ou sendo destruído
        try:
            if not self.view_widget.isEnabled():
                logging.debug("⚠️ Renderização ignorada: view_widget desabilitado")
                return
            if not self.view_widget.isVisible():
                logging.debug("⚠️ Renderização ignorada: view_widget invisível")
                return
        except (RuntimeError, AttributeError):
            logging.warning("⚠️ Renderização ignorada: view_widget destruído")
            return

        # Limpar elementos antigos ANTES de renderizar novos
        # (sem definir self.structure = None, apenas remover meshes)
        try:
            for mesh in self.atom_meshes:
                try:
                    self.view_widget.removeItem(mesh)
                except (RuntimeError, AttributeError):
                    pass

            for bond in self.bond_meshes:
                try:
                    self.view_widget.removeItem(bond)
                except (RuntimeError, AttributeError):
                    pass

            for line in self.unit_cell_lines:
                try:
                    self.view_widget.removeItem(line)
                except (RuntimeError, AttributeError):
                    pass
        except Exception as e:
            logging.warning(f"Erro ao limpar elementos antigos: {e}")
        finally:
            self.atom_meshes.clear()
            self.bond_meshes.clear()
            self.unit_cell_lines.clear()

        # IMPORTANTE: Renderizar na ordem correta para melhor visualização
        # 1. Primeiro ligações (ficam "atrás")
        # 2. Depois célula unitária
        # 3. Por último átomos (ficam "na frente")

        logging.info(f"Renderizando estrutura: {self.structure.composition.reduced_formula}")

        # Renderizar ligações (sempre ativo por padrão)
        self._render_bonds()

        # Renderizar célula unitária (sempre ativo por padrão)
        self._render_unit_cell()


        # Renderizar átomos por último (ficam na frente)
        # Criar supercélula baseada na expansão [na, nb, nc]
        na, nb, nc = self.supercell_expansion
        lattice = self.structure.lattice

        for i in range(na):
            for j in range(nb):
                for k in range(nc):
                    # Vetor de translação para esta célula
                    translation = lattice.matrix[0] * i + lattice.matrix[1] * j + lattice.matrix[2] * k

                    # Renderizar todos os átomos da célula unitária transladados
                    for site in self.structure:
                        pos = site.coords + translation
                        element = site.specie.symbol

                        # Obter cor e raio
                        color = self.ATOMIC_COLORS.get(element, self.ATOMIC_COLORS['default'])
                        radius = self.ATOMIC_RADII.get(element, self.ATOMIC_RADII['default']) * self.atom_scale

                        # Criar esfera para o átomo
                        mesh_data = gl.MeshData.sphere(rows=15, cols=15, radius=radius)
                        mesh = gl.GLMeshItem(
                            meshdata=mesh_data,
                            smooth=True,
                            color=(*color, 0.95),
                            shader='shaded',
                            glOptions='opaque'
                        )
                        mesh.translate(pos[0], pos[1], pos[2])
                        self.view_widget.addItem(mesh)
                        self.atom_meshes.append(mesh)

        logging.info(f"✅ Estrutura renderizada: {len(self.atom_meshes)} átomos, "
                    f"{len(self.bond_meshes)} ligações, {len(self.unit_cell_lines)} arestas da célula")


    def _render_bonds(self):
        """
        Renderiza as ligações entre átomos próximos.
        Usa algoritmo similar ao VESTA: mostra apenas vizinhos mais próximos.
        AGORA com suporte para SUPERCÉLULA - renderiza ligações em toda a estrutura expandida.
        """
        if not self.structure:
            return

        # Limpar bonds antigos
        for bond in self.bond_meshes:
            self.view_widget.removeItem(bond)
        self.bond_meshes.clear()

        try:
            na, nb, nc = self.supercell_expansion
            lattice = self.structure.lattice
            n_sites = len(self.structure)
            n_total_atoms = n_sites * na * nb * nc

            logging.info(f"Calculando ligações para supercélula {na}×{nb}×{nc} = {n_total_atoms} átomos")

            # Dicionário para rastrear pares já adicionados (evitar duplicatas)
            added_pairs = set()

            # Criar lista de TODOS os átomos da supercélula com suas posições
            all_atoms = []
            for i in range(na):
                for j in range(nb):
                    for k in range(nc):
                        translation = lattice.matrix[0] * i + lattice.matrix[1] * j + lattice.matrix[2] * k
                        for idx, site in enumerate(self.structure):
                            pos = site.coords + translation
                            all_atoms.append({
                                'pos': pos,
                                'element': site.specie.symbol,
                                'cell': (i, j, k),
                                'site_idx': idx,
                                'global_idx': len(all_atoms)  # Índice único global
                            })

            # Calcular ligações entre TODOS os átomos da supercélula
            for idx1, atom1 in enumerate(all_atoms):
                pos1 = atom1['pos']
                element1 = atom1['element']

                # Definir distância máxima de ligação
                max_bond_dist = self._get_max_bond_distance(element1)

                # Buscar vizinhos próximos
                neighbor_data = []
                for idx2, atom2 in enumerate(all_atoms):
                    if idx2 <= idx1:  # Evitar duplicatas e auto-ligação
                        continue

                    pos2 = atom2['pos']
                    dist = np.linalg.norm(pos2 - pos1)

                    if dist < max_bond_dist:
                        neighbor_data.append((idx2, dist, pos2, atom2['element']))

                # Ordenar por distância
                neighbor_data.sort(key=lambda x: x[1])

                # Usar critério: vizinhos até 1.35x da distância do mais próximo
                if neighbor_data:
                    min_dist = neighbor_data[0][1]
                    max_neighbor_dist = min_dist * 1.35

                    for idx2, dist, pos2, element2 in neighbor_data:
                        if dist > max_neighbor_dist:
                            break

                        # Criar cilindro 3D para a ligação
                        bond_cylinder = self._create_bond_cylinder(pos1, pos2)
                        if bond_cylinder:
                            self.view_widget.addItem(bond_cylinder)
                            self.bond_meshes.append(bond_cylinder)

                            # Armazenar informações para animação
                            bond_cylinder._bond_atoms = (idx1, idx2)
                            bond_cylinder._original_pos1 = pos1.copy()
                            bond_cylinder._original_pos2 = pos2.copy()

            logging.info(f"✅ Renderizadas {len(self.bond_meshes)} ligações na supercélula {na}×{nb}×{nc}")

            if len(self.bond_meshes) == 0:
                logging.warning(f"⚠️  Nenhuma ligação encontrada")

        except Exception as e:
            logging.error(f"❌ Erro ao renderizar ligações: {e}")
            import traceback
            traceback.print_exc()

    def _get_max_bond_distance(self, element):
        """
        Retorna a distância máxima de busca para ligações baseada no elemento.
        Usa raios covalentes típicos.
        """
        # Raios covalentes aproximados (em Å) + margem de segurança
        max_distances = {
            'H': 1.5, 'He': 1.5,
            'Li': 2.5, 'Be': 2.5, 'B': 2.5, 'C': 2.5, 'N': 2.5, 'O': 2.5, 'F': 2.5,
            'Na': 3.0, 'Mg': 3.0, 'Al': 3.0, 'Si': 3.0, 'P': 3.0, 'S': 3.0, 'Cl': 3.0,
            'K': 3.5, 'Ca': 3.5, 'Sc': 3.5, 'Ti': 3.5, 'V': 3.5, 'Cr': 3.5,
            'Mn': 3.5, 'Fe': 3.5, 'Co': 3.5, 'Ni': 3.5, 'Cu': 3.5, 'Zn': 3.5,
            'Ga': 3.5, 'Ge': 3.5, 'As': 3.5, 'Se': 3.5, 'Br': 3.5,
            'Rb': 4.0, 'Sr': 4.0, 'Y': 4.0, 'Zr': 4.0, 'Nb': 4.0, 'Mo': 4.0,
            'Sm': 4.0, 'Gd': 4.0, 'Tb': 4.0, 'Dy': 4.0, 'Ho': 4.0, 'Er': 4.0,
        }
        return max_distances.get(element, 3.5)  # Padrão: 3.5 Å

    def _create_bond_cylinder(self, pos1, pos2, radius=None):
        """
        Cria um cilindro 3D com sombreamento para representar uma ligação atômica.

        Args:
            pos1 (np.array): Posição do primeiro átomo [x, y, z]
            pos2 (np.array): Posição do segundo átomo [x, y, z]
            radius (float): Raio do cilindro em Angstroms (None = usar self.bond_radius)

        Returns:
            gl.GLMeshItem: Cilindro 3D com sombreamento
        """
        try:
            # Usar raio configurável
            if radius is None:
                radius = self.bond_radius

            # Calcular vetor direção e comprimento
            direction = pos2 - pos1
            length = np.linalg.norm(direction)

            if length < 0.01:  # Evitar ligações muito curtas
                return None

            # Normalizar direção
            direction = direction / length

            # Criar cilindro orientado ao longo do eixo Z inicialmente
            rows, cols = 12, 12  # Resolução do cilindro
            verts = []
            faces = []

            # Gerar vértices do cilindro
            for i in range(rows + 1):
                z = (i / rows) * length
                for j in range(cols):
                    theta = (j / cols) * 2 * np.pi
                    x = radius * np.cos(theta)
                    y = radius * np.sin(theta)
                    verts.append([x, y, z])

            # Gerar faces (triângulos)
            for i in range(rows):
                for j in range(cols):
                    # Índices dos vértices
                    v0 = i * cols + j
                    v1 = i * cols + (j + 1) % cols
                    v2 = (i + 1) * cols + j
                    v3 = (i + 1) * cols + (j + 1) % cols

                    # Dois triângulos por quadrado
                    faces.append([v0, v1, v2])
                    faces.append([v1, v3, v2])

            verts = np.array(verts)
            faces = np.array(faces)

            # Criar mesh data
            mesh_data = gl.MeshData(vertexes=verts, faces=faces)

            # Criar mesh item com sombreamento
            cylinder = gl.GLMeshItem(
                meshdata=mesh_data,
                smooth=True,
                color=(0.5, 0.5, 0.5, 1.0),  # Cinza médio completamente opaco
                shader='shaded',  # Shader com iluminação
                glOptions='opaque'  # Totalmente sólido
            )

            # Calcular rotação necessária para alinhar com a direção da ligação
            # Eixo Z padrão
            z_axis = np.array([0, 0, 1])

            # Vetor perpendicular (eixo de rotação)
            rotation_axis = np.cross(z_axis, direction)
            rotation_axis_norm = np.linalg.norm(rotation_axis)

            if rotation_axis_norm > 1e-6:  # Se não são paralelos
                rotation_axis = rotation_axis / rotation_axis_norm

                # Ângulo de rotação
                cos_angle = np.dot(z_axis, direction)
                angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
                angle_deg = np.degrees(angle)

                # Aplicar rotação
                cylinder.rotate(angle_deg, rotation_axis[0], rotation_axis[1], rotation_axis[2])
            elif np.dot(z_axis, direction) < 0:  # Direção oposta
                # Rotação de 180° em torno de X
                cylinder.rotate(180, 1, 0, 0)

            # Transladar para a posição inicial
            cylinder.translate(pos1[0], pos1[1], pos1[2])

            return cylinder

        except Exception as e:
            logging.warning(f"Erro ao criar cilindro de ligação: {e}")
            return None

    def _render_unit_cell(self):
        """
        Renderiza as arestas da célula unitária.
        Se houver expansão de supercélula, desenha TODAS as células.
        """
        if not self.structure:
            return

        # Limpar linhas antigas
        for line in self.unit_cell_lines:
            self.view_widget.removeItem(line)
        self.unit_cell_lines.clear()

        lattice = self.structure.lattice
        na, nb, nc = self.supercell_expansion

        # Vértices da célula unitária (coordenadas fracionárias)
        vertices = np.array([
            [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],  # Base inferior
            [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],  # Base superior
        ])

        # Definir arestas (pares de índices de vértices)
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Base inferior
            (4, 5), (5, 6), (6, 7), (7, 4),  # Base superior
            (0, 4), (1, 5), (2, 6), (3, 7),  # Arestas verticais
        ]

        # Desenhar TODAS as células da supercélula
        for i in range(na):
            for j in range(nb):
                for k in range(nc):
                    # Vetor de translação para esta célula
                    translation = lattice.matrix[0] * i + lattice.matrix[1] * j + lattice.matrix[2] * k

                    # Converter vértices para coordenadas cartesianas e transladar
                    cart_vertices = np.array([lattice.get_cartesian_coords(v) + translation for v in vertices])

                    # Criar linhas para cada aresta
                    for edge_i, edge_j in edges:
                        pts = np.array([cart_vertices[edge_i], cart_vertices[edge_j]])
                        line = gl.GLLinePlotItem(
                            pos=pts,
                            color=(0.0, 0.0, 0.0, 1.0),
                            width=1.5,  # Linhas finas e discretas
                            antialias=True
                        )
                        self.view_widget.addItem(line)
                        self.unit_cell_lines.append(line)

        logging.info(f"✅ Renderizadas {len(self.unit_cell_lines)} arestas para supercélula {na}×{nb}×{nc}")

    # NOTA: Função _render_lattice_arrows removida
    # As setas a,b,c agora aparecem APENAS no gizmo de orientação (canto inferior esquerdo)
    # com os ângulos CORRETOS da célula unitária (α, β, γ)

    def _create_arrow_cylinder(self, start, end, radius=0.08, color=(1.0, 0.0, 0.0, 1.0)):
        """Cria um cilindro para o corpo da seta."""
        try:
            direction = end - start
            length = np.linalg.norm(direction)

            if length < 0.01:
                return None

            # Reduzir comprimento em 10% para deixar espaço para o cone
            end_adjusted = start + direction * 0.9

            # Usar o mesmo método de criação de cilindros das ligações
            direction_adj = end_adjusted - start
            length_adj = np.linalg.norm(direction_adj)
            direction_adj = direction_adj / length_adj

            # Criar geometria do cilindro
            rows, cols = 10, 10
            verts = []
            faces = []

            for i in range(rows + 1):
                z = (i / rows) * length_adj
                for j in range(cols):
                    theta = (j / cols) * 2 * np.pi
                    x = radius * np.cos(theta)
                    y = radius * np.sin(theta)
                    verts.append([x, y, z])

            for i in range(rows):
                for j in range(cols):
                    v0 = i * cols + j
                    v1 = i * cols + (j + 1) % cols
                    v2 = (i + 1) * cols + j
                    v3 = (i + 1) * cols + (j + 1) % cols
                    faces.append([v0, v1, v2])
                    faces.append([v1, v3, v2])

            verts = np.array(verts)
            faces = np.array(faces)

            mesh_data = gl.MeshData(vertexes=verts, faces=faces)
            cylinder = gl.GLMeshItem(
                meshdata=mesh_data,
                smooth=True,
                color=color,
                shader='shaded',
                glOptions='opaque'
            )

            # Rotacionar e transladar
            z_axis = np.array([0, 0, 1])
            rotation_axis = np.cross(z_axis, direction_adj)
            rotation_axis_norm = np.linalg.norm(rotation_axis)

            if rotation_axis_norm > 1e-6:
                rotation_axis = rotation_axis / rotation_axis_norm
                cos_angle = np.dot(z_axis, direction_adj)
                angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
                angle_deg = np.degrees(angle)
                cylinder.rotate(angle_deg, rotation_axis[0], rotation_axis[1], rotation_axis[2])
            elif np.dot(z_axis, direction_adj) < 0:
                cylinder.rotate(180, 1, 0, 0)

            cylinder.translate(start[0], start[1], start[2])
            return cylinder

        except Exception as e:
            logging.warning(f"Erro ao criar cilindro de seta: {e}")
            return None

    def _create_arrow_cone(self, tip_position, direction, height=0.4, radius=0.2, color=(1.0, 0.0, 0.0, 1.0)):
        """Cria um cone para a ponta da seta."""
        try:
            direction = direction / np.linalg.norm(direction)

            # Base do cone (10% antes da ponta)
            base_position = tip_position - direction * height

            # Criar geometria do cone
            rows, cols = 10, 16
            verts = []
            faces = []

            # Vértice da ponta (topo do cone)
            verts.append([0, 0, height])

            # Vértices da base
            for j in range(cols):
                theta = (j / cols) * 2 * np.pi
                x = radius * np.cos(theta)
                y = radius * np.sin(theta)
                verts.append([x, y, 0])

            # Centro da base
            verts.append([0, 0, 0])

            # Faces laterais (triângulos da ponta até a base)
            for j in range(cols):
                v1 = j + 1
                v2 = (j + 1) % cols + 1
                faces.append([0, v1, v2])

            # Faces da base
            for j in range(cols):
                v1 = j + 1
                v2 = (j + 1) % cols + 1
                faces.append([len(verts) - 1, v2, v1])

            verts = np.array(verts)
            faces = np.array(faces)

            mesh_data = gl.MeshData(vertexes=verts, faces=faces)
            cone = gl.GLMeshItem(
                meshdata=mesh_data,
                smooth=True,
                color=color,
                shader='shaded',
                glOptions='opaque'
            )

            # Rotacionar para alinhar com a direção
            z_axis = np.array([0, 0, 1])
            rotation_axis = np.cross(z_axis, direction)
            rotation_axis_norm = np.linalg.norm(rotation_axis)

            if rotation_axis_norm > 1e-6:
                rotation_axis = rotation_axis / rotation_axis_norm
                cos_angle = np.dot(z_axis, direction)
                angle = np.arccos(np.clip(cos_angle, -1.0, 1.0))
                angle_deg = np.degrees(angle)
                cone.rotate(angle_deg, rotation_axis[0], rotation_axis[1], rotation_axis[2])
            elif np.dot(z_axis, direction) < 0:
                cone.rotate(180, 1, 0, 0)

            cone.translate(base_position[0], base_position[1], base_position[2])
            return cone

        except Exception as e:
            logging.warning(f"Erro ao criar cone de seta: {e}")
            return None

    def _toggle_unit_cell(self, state):
        """Mostra/oculta a célula unitária."""
        visible = (state == Qt.CheckState.Checked)
        for line in self.unit_cell_lines:
            line.setVisible(visible)

        # Se ativando, renderizar novamente
        if visible and self.structure and not self.unit_cell_lines:
            self._render_unit_cell()

    def _toggle_bonds(self, state):
        """Mostra/oculta as ligações."""
        visible = (state == Qt.CheckState.Checked)
        for bond in self.bond_meshes:
            bond.setVisible(visible)

        # Se ativando, renderizar novamente
        if visible and self.structure and not self.bond_meshes:
            self._render_bonds()

    def _update_atom_sizes(self, value):
        """Atualiza o tamanho dos átomos."""
        self.atom_scale = value / 100.0
        self.size_label.setText(f"{value}%")

        # Re-renderizar estrutura com novo tamanho
        # IMPORTANTE: NÃO chamar _clear_structure() - apenas re-renderizar
        if self.structure:
            self._render_structure()

    def _open_supercell_dialog(self, event):
        """Abre diálogo para selecionar expansão da célula (supercélula)."""
        if not self.structure:
            return

        dialog = SupercellDialog(self, self.supercell_expansion, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_expansion = dialog.get_expansion()
            if new_expansion != self.supercell_expansion:
                self.supercell_expansion = new_expansion
                # Re-renderizar estrutura com nova expansão
                # IMPORTANTE: NÃO chamar _clear_structure() - apenas re-renderizar
                self._render_structure()

                # Atualizar label de informações
                formula = self.structure.composition.reduced_formula
                n_atoms_unit = len(self.structure)
                n_atoms_total = n_atoms_unit * new_expansion[0] * new_expansion[1] * new_expansion[2]
                lattice = self.structure.lattice
                a, b, c = lattice.a, lattice.b, lattice.c

                info_html = f"""
                <div style='color: green; font-weight: bold;'>
                    {formula} • {n_atoms_total} átomos ({new_expansion[0]}×{new_expansion[1]}×{new_expansion[2]})<br>
                    <span style='color: #FF0000;'>a={a:.3f}</span> 
                    <span style='color: #00AA00;'>b={b:.3f}</span> 
                    <span style='color: #0000FF;'>c={c:.3f}</span> Å
                </div>
                """
                self.info_label.setText(info_html)
                self.info_label.setTextFormat(Qt.TextFormat.RichText)

    def _reset_camera(self):
        """
        Reseta a posição da câmera para visualização padrão.
        Centraliza em TODA a supercélula expandida.
        """
        if self.structure:
            na, nb, nc = self.supercell_expansion
            lattice = self.structure.lattice

            # Criar lista de TODAS as posições dos átomos na supercélula
            all_positions = []
            for i in range(na):
                for j in range(nb):
                    for k in range(nc):
                        translation = lattice.matrix[0] * i + lattice.matrix[1] * j + lattice.matrix[2] * k
                        for site in self.structure:
                            pos = site.coords + translation
                            all_positions.append(pos)

            all_positions = np.array(all_positions)

            # Calcular centro de TODA a supercélula
            center = all_positions.mean(axis=0)

            # Calcular distância apropriada baseada no tamanho TOTAL
            max_dist = np.max(np.linalg.norm(all_positions - center, axis=1))
            distance = max(30, max_dist * 2.5)

            self.view_widget.setCameraPosition(
                pos=pg.Vector(center[0], center[1], center[2]),
                distance=distance,
                azimuth=45,
                elevation=30
            )

            logging.info(f"📹 Câmera resetada: centro={center}, distância={distance:.1f} Å (supercélula {na}×{nb}×{nc})")
        else:
            self.view_widget.setCameraPosition(distance=30, azimuth=45, elevation=30)

        # Sincronizar o gizmo de orientação
        self._sync_orientation_gizmo()

    def closeEvent(self, event):
        """Limpeza segura ao fechar o visualizador."""
        try:
            # Parar animações
            self.stop_animation()

            # Parar timer do gizmo
            if hasattr(self, '_gizmo_sync_timer') and self._gizmo_sync_timer:
                self._gizmo_sync_timer.stop()

            # Desabilitar renderização
            if hasattr(self, 'view_widget'):
                self.view_widget.setEnabled(False)

            # Limpar estrutura
            self._clear_structure()

            logging.debug("✅ StructureViewer3D fechado com segurança")
        except Exception as e:
            logging.warning(f"Erro ao fechar StructureViewer3D: {e}")
        finally:
            super().closeEvent(event)

    def start_rotation_animation(self, axis='z', speed=1.0):
        """
        Inicia animação de rotação CONTÍNUA em torno de um eixo.

        Args:
            axis: Eixo de rotação ('x', 'y' ou 'z')
            speed: Velocidade em graus por frame (0.5=Lenta, 1.0=Normal, 2.0=Rápida)
        """
        self.stop_animation()
        self._animation_type = f'rotation_{axis}'
        self._animation_angle = 0
        self._rotation_speed = speed  # Armazenar velocidade

        from PySide6.QtCore import QTimer
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(lambda: self._animate_rotation(axis))
        self._animation_timer.start(16)  # ~60 FPS
        logging.info(f"Iniciando rotação CONTÍNUA em {axis.upper()} (velocidade: {speed}°/frame)")

    def start_vibration_animation(self, amplitude=0.1):
        """Inicia animação de vibração da estrutura.

        A vibração atômica real ocorre em ~10^13 Hz, mas aqui simulamos
        visualmente com frequência ajustada para percepção humana.
        Amplitude típica: ~0.1 Angstrom à temperatura ambiente.
        """
        if not self.structure:
            return

        self.stop_animation()
        self._animation_type = 'vibration'
        self._animation_angle = 0
        self._vibration_amplitude = amplitude

        # Salvar posições originais dos átomos
        self._original_atom_positions = []
        for mesh in self.atom_meshes:
            pos_vec = mesh.transform().column(3)  # QVector4D (x, y, z, w)
            # Extrair x, y, z usando métodos do QVector4D
            self._original_atom_positions.append((pos_vec.x(), pos_vec.y(), pos_vec.z()))

        from PySide6.QtCore import QTimer
        self._animation_timer = QTimer()
        self._animation_timer.timeout.connect(self._animate_vibration)
        # Frequência visual ajustada: ~60 FPS (16ms) para simular vibração rápida
        # A frequência real (~10^13 Hz) seria impossível de visualizar
        self._animation_timer.start(16)  # ~60 FPS
        logging.info("Iniciando animação de vibração")

    def stop_animation(self):
        """Para qualquer animação em andamento."""
        if self._animation_timer:
            self._animation_timer.stop()
            self._animation_timer = None

        # Restaurar posições originais se estava vibrando
        if self._animation_type == 'vibration' and self._original_atom_positions:
            # Restaurar átomos
            for i, mesh in enumerate(self.atom_meshes):
                if i < len(self._original_atom_positions):
                    orig_x, orig_y, orig_z = self._original_atom_positions[i]
                    mesh.resetTransform()
                    mesh.translate(orig_x, orig_y, orig_z)

            # Restaurar ligações às posições originais
            for bond in self.bond_meshes:
                if hasattr(bond, '_original_pos1') and hasattr(bond, '_original_pos2'):
                    # Remover cilindro atual
                    self.view_widget.removeItem(bond)

                    # Recriar na posição original
                    new_bond = self._create_bond_cylinder(bond._original_pos1, bond._original_pos2)
                    if new_bond:
                        self.view_widget.addItem(new_bond)
                        # Copiar atributos
                        new_bond._bond_atoms = bond._bond_atoms
                        new_bond._original_pos1 = bond._original_pos1
                        new_bond._original_pos2 = bond._original_pos2
                        # Substituir na lista
                        idx = self.bond_meshes.index(bond)
                        self.bond_meshes[idx] = new_bond

        self._animation_type = None
        self._animation_angle = 0
        logging.info("Animação parada")

    def _animate_rotation(self, axis):
        """Executa um frame da animação de rotação CONTÍNUA."""
        # Usar velocidade configurada (padrão 2.0 se não definida)
        speed = getattr(self, '_rotation_speed', 2.0)
        self._animation_angle = (self._animation_angle + speed) % 360  # Rotação infinita

        # Rotacionar a câmera
        opts = self.view_widget.cameraParams()

        if axis == 'z':
            # Rotação horizontal (azimuth) - CONTÍNUA
            new_azimuth = (opts['azimuth'] + speed) % 360
            self.view_widget.setCameraPosition(
                azimuth=new_azimuth,
                elevation=opts['elevation'],
                distance=opts['distance']
            )
        elif axis == 'y':
            # Rotação vertical (elevation) - CONTÍNUA
            # Usar azimuth para rotação contínua ao invés de elevation limitada
            new_azimuth = (opts['azimuth'] + speed) % 360
            # Variar elevation suavemente para dar efeito de rotação em Y
            new_elevation = 30 * np.sin(np.radians(self._animation_angle * 2))

            self.view_widget.setCameraPosition(
                azimuth=new_azimuth,
                elevation=new_elevation,
                distance=opts['distance']
            )
        elif axis == 'x':
            # Rotação em X - CONTÍNUA
            new_azimuth = (opts['azimuth'] + speed * 0.5) % 360
            new_elevation = 30 * np.sin(np.radians(self._animation_angle))

            self.view_widget.setCameraPosition(
                azimuth=new_azimuth,
                elevation=new_elevation,
                distance=opts['distance']
            )

        # Sincronizar gizmo de orientação
        self._sync_orientation_gizmo()

    def _animate_vibration(self):
        """Executa um frame da animação de vibração.

        Simula vibração atômica térmica com frequência visual ajustada.
        A frequência real é ~10^13 Hz, aqui aproximamos visualmente.
        """
        if not self._original_atom_positions:
            return

        # Incremento de ângulo maior (30°) para simular vibração mais rápida
        # Aproximação visual da alta frequência real (~10^13 Hz)
        self._animation_angle += 30

        # Armazenar novas posições dos átomos
        current_atom_positions = {}

        # Vibrar átomos usando onda senoidal
        for i, mesh in enumerate(self.atom_meshes):
            if i < len(self._original_atom_positions):
                orig_x, orig_y, orig_z = self._original_atom_positions[i]

                # Vibração térmica em 3D com fases diferentes para cada átomo
                offset_x = self._vibration_amplitude * np.sin(np.radians(self._animation_angle + i * 30))
                offset_y = self._vibration_amplitude * np.cos(np.radians(self._animation_angle + i * 45))
                offset_z = self._vibration_amplitude * np.sin(np.radians(self._animation_angle + i * 60))

                new_x = orig_x + offset_x
                new_y = orig_y + offset_y
                new_z = orig_z + offset_z

                mesh.resetTransform()
                mesh.translate(new_x, new_y, new_z)

                # Armazenar posição atual
                current_atom_positions[i] = np.array([new_x, new_y, new_z])

        # Atualizar ligações para acompanhar os átomos
        for bond in self.bond_meshes:
            if hasattr(bond, '_bond_atoms'):
                atom1_idx, atom2_idx = bond._bond_atoms

                # Obter posições atuais dos átomos
                if atom1_idx in current_atom_positions and atom2_idx in current_atom_positions:
                    pos1 = current_atom_positions[atom1_idx]
                    pos2 = current_atom_positions[atom2_idx]

                    # Remover o cilindro antigo
                    self.view_widget.removeItem(bond)

                    # Criar novo cilindro na posição atualizada
                    new_bond = self._create_bond_cylinder(pos1, pos2)
                    if new_bond:
                        self.view_widget.addItem(new_bond)
                        # Copiar atributos para o novo cilindro
                        new_bond._bond_atoms = bond._bond_atoms
                        new_bond._original_pos1 = bond._original_pos1
                        new_bond._original_pos2 = bond._original_pos2
                        # Substituir na lista
                        idx = self.bond_meshes.index(bond)
                        self.bond_meshes[idx] = new_bond


# Diálogo de Ferramentas do Visualizador 3D
class Viewer3DToolsDialog(QDialog):
    """Diálogo para configurações de visualização 3D."""

    def __init__(self, viewer, parent=None):
        super().__init__(parent)
        self.viewer = viewer
        self.setWindowTitle("Configurações de Visualização 3D")
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        # Tamanho dos átomos
        size_group = QGroupBox("Tamanho dos Átomos")
        size_layout = QVBoxLayout(size_group)

        size_controls = QHBoxLayout()
        size_controls.addWidget(QLabel("Escala:"))

        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(25, 200)
        self.size_slider.setValue(int(viewer.atom_scale * 100))
        self.size_slider.valueChanged.connect(self._update_size_label)
        size_controls.addWidget(self.size_slider)

        self.size_label = QLabel(f"{viewer.atom_scale * 100:.0f}%")
        self.size_label.setMinimumWidth(50)
        size_controls.addWidget(self.size_label)

        size_layout.addLayout(size_controls)
        layout.addWidget(size_group)

        # Visibilidade
        visibility_group = QGroupBox("Visibilidade")
        visibility_layout = QVBoxLayout(visibility_group)

        self.show_cell_check = QCheckBox("Mostrar Célula Unitária")
        self.show_cell_check.setChecked(viewer._show_cell)
        visibility_layout.addWidget(self.show_cell_check)

        self.show_bonds_check = QCheckBox("Mostrar Ligações")
        self.show_bonds_check.setChecked(viewer._show_bonds)
        visibility_layout.addWidget(self.show_bonds_check)


        layout.addWidget(visibility_group)

        # Espessura das Ligações
        bonds_group = QGroupBox("Ligações")
        bonds_layout = QVBoxLayout(bonds_group)

        bonds_controls = QHBoxLayout()
        bonds_controls.addWidget(QLabel("Espessura:"))

        # Obter raio atual das ligações (padrão 0.15)
        current_radius = getattr(viewer, 'bond_radius', 0.15)

        self.bonds_slider = QSlider(Qt.Orientation.Horizontal)
        self.bonds_slider.setRange(5, 30)  # 0.05 a 0.30 Angstrom
        self.bonds_slider.setValue(int(current_radius * 100))
        self.bonds_slider.valueChanged.connect(self._update_bonds_label)
        bonds_controls.addWidget(self.bonds_slider)

        self.bonds_label = QLabel(f"{current_radius:.2f} Å")
        self.bonds_label.setMinimumWidth(60)
        bonds_controls.addWidget(self.bonds_label)

        bonds_layout.addLayout(bonds_controls)
        layout.addWidget(bonds_group)

        # Botões
        from PySide6.QtWidgets import QDialogButtonBox
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel |
            QDialogButtonBox.StandardButton.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Apply).clicked.connect(self._apply_settings)
        layout.addWidget(button_box)

    def _update_size_label(self, value):
        self.size_label.setText(f"{value}%")

    def _update_bonds_label(self, value):
        radius = value / 100.0
        self.bonds_label.setText(f"{radius:.2f} Å")

    def _apply_settings(self):
        """Aplica as configurações sem fechar o diálogo."""
        self.viewer.atom_scale = self.size_slider.value() / 100.0

        # Atualizar visibilidade
        self.viewer._show_cell = self.show_cell_check.isChecked()
        self.viewer._show_bonds = self.show_bonds_check.isChecked()

        # Atualizar espessura das ligações
        self.viewer.bond_radius = self.bonds_slider.value() / 100.0

        # Re-renderizar se houver estrutura
        # IMPORTANTE: NÃO chamar _clear_structure() pois apaga self.structure
        # _render_structure() já faz a limpeza automática dos elementos visuais
        if self.viewer.structure:
            self.viewer._render_structure()
            logging.info("✅ Configurações 3D aplicadas e estrutura re-renderizada")

    def accept(self):
        """Aplicar e fechar."""
        self._apply_settings()
        super().accept()


# Diálogo de Animação do Visualizador 3D
class Viewer3DAnimationDialog(QDialog):
    """Diálogo para controlar animações 3D."""

    def __init__(self, viewer, parent=None):
        super().__init__(parent)
        self.viewer = viewer
        self.setWindowTitle("Animações 3D")
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)

        # Rotação Contínua
        rotation_group = QGroupBox("Rotação Contínua")
        rotation_layout = QVBoxLayout(rotation_group)

        # Velocidade de rotação
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Velocidade:"))

        self.speed_combo = QComboBox()
        self.speed_combo.addItem(" Lenta", 0.5)      # 0.5 graus/frame
        self.speed_combo.addItem(" Normal", 1.0)     # 1.0 grau/frame
        self.speed_combo.addItem(" Rápida", 2.0)     # 2.0 graus/frame
        self.speed_combo.setCurrentIndex(1)  # Normal como padrão
        speed_layout.addWidget(self.speed_combo)

        rotation_layout.addLayout(speed_layout)

        rot_label = QLabel("Girar em torno do eixo:")
        rotation_layout.addWidget(rot_label)

        rot_buttons = QHBoxLayout()

        btn_rot_x = QPushButton("Eixo X")
        btn_rot_x.clicked.connect(lambda: self._start_rotation('x'))
        rot_buttons.addWidget(btn_rot_x)

        btn_rot_y = QPushButton("Eixo Y")
        btn_rot_y.clicked.connect(lambda: self._start_rotation('y'))
        rot_buttons.addWidget(btn_rot_y)

        btn_rot_z = QPushButton("Eixo Z")
        btn_rot_z.clicked.connect(lambda: self._start_rotation('z'))
        rot_buttons.addWidget(btn_rot_z)

        rotation_layout.addLayout(rot_buttons)
        layout.addWidget(rotation_group)

        # Vibração
        vibration_group = QGroupBox("Vibração Térmica")
        vibration_layout = QVBoxLayout(vibration_group)

        vib_controls = QHBoxLayout()
        vib_controls.addWidget(QLabel("Amplitude:"))

        self.vib_slider = QSlider(Qt.Orientation.Horizontal)
        self.vib_slider.setRange(1, 50)
        self.vib_slider.setValue(10)
        vib_controls.addWidget(self.vib_slider)

        self.vib_label = QLabel("0.10 Å")
        self.vib_label.setMinimumWidth(60)
        vib_controls.addWidget(self.vib_label)

        self.vib_slider.valueChanged.connect(lambda v: self.vib_label.setText(f"{v/100:.2f} Å"))

        vibration_layout.addLayout(vib_controls)

        btn_vibrate = QPushButton("Iniciar Vibração")
        btn_vibrate.clicked.connect(self._start_vibration)
        vibration_layout.addWidget(btn_vibrate)

        layout.addWidget(vibration_group)

        # Controle
        control_layout = QHBoxLayout()

        self.stop_btn = QPushButton("⏹ Parar Animação")
        self.stop_btn.clicked.connect(self._stop_animation)
        control_layout.addWidget(self.stop_btn)

        layout.addLayout(control_layout)

        # Botão fechar
        from PySide6.QtWidgets import QDialogButtonBox
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _start_rotation(self, axis):
        speed = self.speed_combo.currentData()  # Pegar velocidade selecionada
        self.viewer.start_rotation_animation(axis, speed=speed)

    def _start_vibration(self):
        amplitude = self.vib_slider.value() / 100.0
        self.viewer.start_vibration_animation(amplitude)

    def _stop_animation(self):
        self.viewer.stop_animation()

    def closeEvent(self, event):
        """Para animação ao fechar o diálogo."""
        self.viewer.stop_animation()
        super().closeEvent(event)


# Diálogo de Expansão de Célula (Supercélula)
class SupercellDialog(QDialog):
    """Diálogo para selecionar expansão da célula unitária (supercélula)."""

    def __init__(self, viewer, current_expansion, parent=None):
        super().__init__(parent)
        self.viewer = viewer
        self.current_expansion = current_expansion
        self.setWindowTitle("Expansão da Célula Unitária")
        self.setMinimumWidth(320)

        layout = QVBoxLayout(self)

        # Título informativo
        info_label = QLabel(
            "Selecione a expansão da célula unitária (supercélula).\n"
            "Valores maiores mostram mais células repetidas."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #555; font-size: 9pt; padding: 5px;")
        layout.addWidget(info_label)

        # Opções predefinidas (comuns em cristalografia)
        options_group = QGroupBox("Expansões Predefinidas")
        options_layout = QVBoxLayout(options_group)

        self.preset_buttons = []

        # Opções baseadas no VESTA e Mercury
        presets = [
            ("1×1×1", [1, 1, 1], "Célula unitária original"),
            ("2×2×2", [2, 2, 2], "2× em todas as direções"),
            ("2×2×1", [2, 2, 1], "2× em a e b"),
            ("2×1×1", [2, 1, 1], "2× apenas em a"),
            ("1×2×1", [1, 2, 1], "2× apenas em b"),
            ("1×1×2", [1, 1, 2], "2× apenas em c"),
            ("3×3×3", [3, 3, 3], "3× em todas as direções"),
        ]

        from PySide6.QtWidgets import QRadioButton, QButtonGroup
        self.button_group = QButtonGroup(self)

        for i, (label, expansion, tooltip) in enumerate(presets):
            # Calcular número de átomos
            n_atoms_unit = len(viewer.structure) if viewer.structure else 0
            n_atoms_total = n_atoms_unit * expansion[0] * expansion[1] * expansion[2]

            radio = QRadioButton(f"{label} ({n_atoms_total} átomos)")
            radio.setToolTip(tooltip)
            radio.expansion = expansion

            # Marcar se for a expansão atual
            if expansion == current_expansion:
                radio.setChecked(True)

            self.button_group.addButton(radio, i)
            options_layout.addWidget(radio)
            self.preset_buttons.append(radio)

        layout.addWidget(options_group)

        # Aviso para muitos átomos
        warning_label = QLabel(
            "⚠️ Expansões grandes (>500 átomos) podem ficar lentas"
        )
        warning_label.setStyleSheet("color: #CC6600; font-size: 8pt; font-style: italic;")
        layout.addWidget(warning_label)

        # Botões
        from PySide6.QtWidgets import QDialogButtonBox
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok |
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_expansion(self):
        """Retorna a expansão selecionada [na, nb, nc]."""
        for button in self.preset_buttons:
            if button.isChecked():
                return button.expansion
        return self.current_expansion


