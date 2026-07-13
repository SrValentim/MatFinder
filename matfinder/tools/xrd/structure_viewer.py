"""
structure_viewer.py
Widget de visualização 3D de estruturas cristalinas para PhaseDRX
Parte do projeto MatFinder - Copyright (C) 2025 Raynner Valentim (UFAM)
"""

import numpy as np
import logging
import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QSlider, QCheckBox, QMessageBox, QDialog,
    QGroupBox, QDialogButtonBox, QFrame, QComboBox, QSpinBox
)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon, QVector4D
import pyqtgraph.opengl as gl
import pyqtgraph as pg
from matfinder.core.translator import ptr

try:
    from pymatgen.core import Structure
    PYMATGEN_AVAILABLE = True
except ImportError:
    PYMATGEN_AVAILABLE = False
    logging.warning(ptr("pymatgen não disponível. Instale com: pip install pymatgen"))

# Importar biblioteca universal de distâncias de ligações
try:
    from .bond_library import get_bond_distance, validate_bond, get_library_stats
    BOND_LIBRARY_AVAILABLE = True
    logging.info("✅ Biblioteca de ligações químicas carregada")
except ImportError:
    BOND_LIBRARY_AVAILABLE = False
    logging.warning(ptr("⚠️  Biblioteca de ligações não disponível - usando fallback genérico"))


def _site_symbol(site):
    """Símbolo do elemento de um sítio, robusto a sítios DESORDENADOS.

    Em estruturas com ocupação parcial (comuns em CIFs do COD), `site.specie`
    lança AttributeError; nesse caso usamos a espécie de MAIOR ocupação, o que
    é adequado para a visualização (cor/raio/ligações). As posições — e portanto
    as distâncias medidas — não dependem disto.
    """
    try:
        return site.specie.symbol
    except Exception:
        try:
            sp = max(site.species, key=site.species.get)
            return getattr(sp, 'symbol', str(sp))
        except Exception:
            return 'X'


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
        self._completion_atoms = []   # átomos fora da célula que fecham a coordenação (borda)

        # AJUSTE: Tamanho padrão dos átomos em 70% para melhor visualização
        # (antes era 100% = 1.0, agora 70% = 0.7)
        self.atom_scale = 0.7

        self.bond_radius = 0.15  # Raio padrão dos cilindros de ligação (em Angstroms)
        self.supercell_expansion = [1, 1, 1]  # Expansão da célula [a, b, c]

        # Variáveis de controle de visibilidade
        self._show_bonds = True
        self._show_cell = True
        self._merge_cells = False  # Mesclar células (mostrar apenas caixa externa da supercélula)

        # Variáveis para animação
        self._animation_timer = None
        self._animation_angle = 0
        self._animation_type = None  # 'rotation_x', 'rotation_y', 'rotation_z', 'vibration'
        self._original_atom_positions = []

        # Medição de distância interatômica (baseada em VESTA, Mercury e outros)
        self._atom_info = []            # [{'pos','element','mesh'}] para picking
        self._measure_first_idx = None  # índice do primeiro átomo selecionado
        self._measurements = []         # medições persistentes: {'line','label','mid'}
        self._rubber_line = None        # linha pontilhada que acompanha o mouse
        self._highlight_item = None     # destaque do átomo selecionado
        self._orig_mouse_double = None
        self._orig_mouse_press = None
        self._orig_mouse_move = None

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
        self.info_label = QLabel(ptr("Nenhuma estrutura carregada"))
        self.info_label.setStyleSheet("color: gray; font-style: italic; font-size: 10pt;")
        self.info_label.setCursor(Qt.CursorShape.PointingHandCursor)  # Cursor de mão ao passar
        self.info_label.mouseDoubleClickEvent = self._open_supercell_dialog
        control_layout.addWidget(self.info_label)

        control_layout.addStretch()

        # Botão de reset da câmera
        reset_btn = QPushButton("↻")
        reset_btn.setFixedSize(28, 28)
        reset_btn.setToolTip(ptr("Resetar visualização da câmera"))
        reset_btn.clicked.connect(self._reset_camera)
        control_layout.addWidget(reset_btn)

        layout.addLayout(control_layout)

        # Armazenar referência ao container para redimensionamento
        self.viewer_container = viewer_container

        # Iniciar sincronização periódica do gizmo
        self._start_gizmo_sync_timer()

        # Instalar handlers de medição de distância (picking por duplo-clique)
        self._install_measure_handlers()

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
            elements.add(_site_symbol(site))

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

        # Reprojetar rótulos de distância (acompanham a estrutura ao girar/zoom)
        try:
            self._update_measurement_labels()
        except Exception:
            pass

    def _start_gizmo_sync_timer(self):
        """Inicia timer para sincronizar o gizmo periodicamente."""
        from PySide6.QtCore import QTimer
        self._gizmo_sync_timer = QTimer()
        self._gizmo_sync_timer.timeout.connect(self._sync_orientation_gizmo)
        self._gizmo_sync_timer.start(50)  # Sincronizar a cada 50ms (~20 FPS)

    def resource_path(self, relative_path):
        """Retorna caminho absoluto do recurso (funciona em dev e produção)."""
        try:
            base_path = sys._MEIPASS  # PyInstaller
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

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
                ptr("Dependência Ausente"),
                ptr("A biblioteca 'pymatgen' não está instalada.\n\nPara instalar, execute:\npip install pymatgen")
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
            error_msg = ptr("Erro ao carregar CIF: {}").format(str(e))
            logging.error(error_msg)
            QMessageBox.critical(self, ptr("Erro"), error_msg)
            self.info_label.setText(ptr("Erro ao carregar estrutura"))
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

            # Limpar medições de distância
            self._clear_measurements()
            self._atom_info = []

            # Limpar também a estrutura
            self.structure = None

            # Atualizar label de informações
            if hasattr(self, 'info_label'):
                self.info_label.setText(ptr("Nenhuma estrutura carregada"))
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
            logging.warning(ptr("⚠️ Renderização ignorada: view_widget destruído"))
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
            # Medições ficam inválidas ao re-renderizar (átomos recriados)
            self._clear_measurements()
            self._atom_info = []

        # IMPORTANTE: Renderizar na ordem correta para melhor visualização
        # 1. Primeiro ligações (ficam "atrás")
        # 2. Depois célula unitária
        # 3. Por último átomos (ficam "na frente")

        formula = self.structure.composition.reduced_formula
        logging.info(f"Renderizando estrutura: {formula}")

        # DEBUG: Verificar limites das coordenadas
        if logging.getLogger().level <= logging.DEBUG:
            all_coords = np.array([site.coords for site in self.structure])
            all_frac = np.array([site.frac_coords for site in self.structure])
            logging.debug(f"Coordenadas cartesianas - X: [{all_coords[:, 0].min():.3f}, {all_coords[:, 0].max():.3f}]")
            logging.debug(f"Coordenadas cartesianas - Y: [{all_coords[:, 1].min():.3f}, {all_coords[:, 1].max():.3f}]")
            logging.debug(f"Coordenadas cartesianas - Z: [{all_coords[:, 2].min():.3f}, {all_coords[:, 2].max():.3f}]")
            logging.debug(f"Coordenadas fracionárias - a: [{all_frac[:, 0].min():.3f}, {all_frac[:, 0].max():.3f}]")
            logging.debug(f"Coordenadas fracionárias - b: [{all_frac[:, 1].min():.3f}, {all_frac[:, 1].max():.3f}]")
            logging.debug(f"Coordenadas fracionárias - c: [{all_frac[:, 2].min():.3f}, {all_frac[:, 2].max():.3f}]")

        # Renderizar ligações (sempre ativo por padrão)
        self._render_bonds()

        # Renderizar célula unitária (sempre ativo por padrão)
        self._render_unit_cell()


        # Renderizar átomos por último (ficam na frente).
        # Inclui a réplica de borda/face/canto (convenção do VESTA): um átomo em
        # coordenada fracionária 0/1 é compartilhado entre células vizinhas e aparece
        # em todas as suas imagens dentro de [0, N] em cada eixo, deixando a célula
        # visualmente completa. Ver _iter_display_atoms().
        for pos, element, base_idx in self._iter_display_atoms():
            color = self.ATOMIC_COLORS.get(element, self.ATOMIC_COLORS['default'])
            radius = self.ATOMIC_RADII.get(element, self.ATOMIC_RADII['default']) * self.atom_scale

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
            self._atom_info.append({'pos': pos.copy(), 'element': element,
                                    'mesh': mesh, 'base_idx': base_idx})

        # Átomos de COMPLETUDE de borda (definidos por _render_bonds): fecham anéis e
        # poliedros como no VESTA. Desenhados APÓS os primários para manter a mesma ordem
        # de índice usada pelas ligações.
        for a in getattr(self, '_completion_atoms', []):
            element = a['element']
            color = self.ATOMIC_COLORS.get(element, self.ATOMIC_COLORS['default'])
            radius = self.ATOMIC_RADII.get(element, self.ATOMIC_RADII['default']) * self.atom_scale
            mesh_data = gl.MeshData.sphere(rows=15, cols=15, radius=radius)
            mesh = gl.GLMeshItem(
                meshdata=mesh_data,
                smooth=True,
                color=(*color, 0.95),
                shader='shaded',
                glOptions='opaque'
            )
            p = np.asarray(a['pos'], dtype=float)
            mesh.translate(p[0], p[1], p[2])
            self.view_widget.addItem(mesh)
            self.atom_meshes.append(mesh)
            self._atom_info.append({'pos': p.copy(), 'element': element,
                                    'mesh': mesh, 'base_idx': a.get('base_idx', -1)})

        logging.info(f"✅ Estrutura renderizada: {len(self.atom_meshes)} átomos, "
                    f"{len(self.bond_meshes)} ligações, {len(self.unit_cell_lines)} arestas da célula")

    def _iter_display_atoms(self):
        """Gera (pos_cartesiana, elemento, base_idx) de todos os átomos a exibir.

        Aplica a REPLICAÇÃO DE BORDA (convenção do VESTA): um átomo em coordenada
        fracionária 0 (ou 1) está na face/aresta/canto da célula e é compartilhado com
        as células vizinhas; por isso é desenhado em todas as suas imagens dentro de
        [0, N] em cada eixo (N = expansão da supercélula naquele eixo). Não inventa
        átomos — são imagens periódicas dos mesmos sítios; deixa a célula completa como
        no VESTA. Para átomos internos (fração != 0/1), o comportamento é o de sempre.
        """
        if not self.structure:
            return
        lattice = self.structure.lattice
        N = self.supercell_expansion
        tol = 5e-3
        for idx, site in enumerate(self.structure):
            element = _site_symbol(site)
            f = np.array(site.frac_coords, dtype=float) % 1.0
            per_axis = []
            for ax in range(3):
                fx = f[ax]
                if fx < tol or fx > 1.0 - tol:      # átomo na borda deste eixo
                    per_axis.append([float(o) for o in range(0, N[ax] + 1)])  # 0..N
                else:
                    per_axis.append([fx + o for o in range(0, N[ax])])        # 0..N-1
            for fa in per_axis[0]:
                for fb in per_axis[1]:
                    for fc in per_axis[2]:
                        pos = lattice.get_cartesian_coords(np.array([fa, fb, fc]))
                        yield pos, element, idx

    def _iter_boundary_candidates(self):
        """Imagens periódicas FORA da célula [0,N] (padding de 1 célula), candidatas a
        COMPLETAR a coordenação dos átomos de borda — fecham anéis/poliedros como no
        VESTA. Só são efetivamente desenhadas se estiverem ligadas a um átomo primário."""
        if not self.structure:
            return
        lattice = self.structure.lattice
        N = self.supercell_expansion
        tol = 5e-3
        for idx, site in enumerate(self.structure):
            element = _site_symbol(site)
            f0 = np.array(site.frac_coords, dtype=float) % 1.0
            for tx in range(-1, N[0] + 2):
                for ty in range(-1, N[1] + 2):
                    for tz in range(-1, N[2] + 2):
                        frac = f0 + np.array([tx, ty, tz], dtype=float)
                        # dentro do padded [-1, N+1]?
                        if not all(-1.0 - tol <= frac[a] <= N[a] + 1.0 + tol for a in range(3)):
                            continue
                        # excluir os que já são PRIMÁRIOS (frac em [0, N])
                        if all(-tol <= frac[a] <= N[a] + tol for a in range(3)):
                            continue
                        yield {'pos': lattice.get_cartesian_coords(frac),
                               'element': element, 'base_idx': idx}

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
            self._completion_atoms = []

            # Átomos PRIMÁRIOS (célula [0,N] com réplica de borda) — mesma ordem dos meshes.
            primary = [{'pos': np.asarray(p, dtype=float), 'element': e}
                       for p, e, _i in self._iter_display_atoms()]
            n_primary = len(primary)
            primary_pos = (np.array([p['pos'] for p in primary])
                           if primary else np.zeros((0, 3)))

            # Candidatos FORA da célula (padding de 1 célula) para completar a coordenação
            # de borda — fecham anéis/poliedros como no VESTA.
            outside = list(self._iter_boundary_candidates())
            outside_pos = (np.array([o['pos'] for o in outside])
                           if outside else np.zeros((0, 3)))

            # Lista combinada: primários (0..n_primary-1) + externos usados (sob demanda).
            # Os índices em 'combined' são os mesmos dos meshes de átomo (ver _render_structure).
            combined = list(primary)
            outside_index = {}   # k em 'outside' -> índice em 'combined'
            added_pairs = set()

            def _keep_outside(k):
                if k not in outside_index:
                    outside_index[k] = len(combined)
                    o = outside[k]
                    combined.append({'pos': o['pos'], 'element': o['element']})
                    self._completion_atoms.append(o)
                return outside_index[k]

            # Para cada átomo PRIMÁRIO, achar a vizinhança (primários + externos) e ligar
            # pelo critério VESTA (até 1.35x do mais próximo, respeitando a distância máxima
            # por par de elementos). Só se desenha ligação que envolva um primário; átomos
            # externos só entram se ficarem ligados a um primário.
            for i in range(n_primary):
                pos1 = primary_pos[i]
                el1 = primary[i]['element']
                r2 = self._get_max_bond_distance(el1) * 2.0

                cand = []  # (dist, kind, ref)   kind: 'p'=primário, 'o'=externo
                if n_primary:
                    dp = np.linalg.norm(primary_pos - pos1, axis=1)
                    for j in np.where(dp < r2)[0]:
                        if j == i:
                            continue
                        d = float(dp[j])
                        if d <= self._get_max_bond_distance(el1, primary[int(j)]['element']):
                            cand.append((d, 'p', int(j)))
                if len(outside):
                    do = np.linalg.norm(outside_pos - pos1, axis=1)
                    for k in np.where(do < r2)[0]:
                        d = float(do[k])
                        if d <= self._get_max_bond_distance(el1, outside[int(k)]['element']):
                            cand.append((d, 'o', int(k)))

                if not cand:
                    continue
                cand.sort(key=lambda x: x[0])
                dmax = cand[0][0] * 1.35   # critério VESTA sobre o vizinho mais próximo

                for d, kind, ref in cand:
                    if d > dmax:
                        break
                    if kind == 'p':
                        a, b = (i, ref) if i < ref else (ref, i)
                        pos_b = primary[ref]['pos']
                    else:
                        a, b = i, _keep_outside(ref)
                        pos_b = outside[ref]['pos']
                    if (a, b) in added_pairs:
                        continue
                    added_pairs.add((a, b))

                    cyl = self._create_bond_cylinder(pos1, pos_b)
                    if cyl:
                        self.view_widget.addItem(cyl)
                        self.bond_meshes.append(cyl)
                        cyl._bond_atoms = (a, b)
                        cyl._original_pos1 = np.asarray(combined[a]['pos'], float).copy()
                        cyl._original_pos2 = np.asarray(combined[b]['pos'], float).copy()

            logging.info(f"✅ Ligações: {len(self.bond_meshes)} "
                         f"({n_primary} átomos + {len(self._completion_atoms)} de borda)")

            if len(self.bond_meshes) == 0:
                logging.warning("⚠️  Nenhuma ligação encontrada")

            if BOND_LIBRARY_AVAILABLE:
                self._validate_rendered_bonds(combined)

        except Exception as e:
            logging.error(f"❌ Erro ao renderizar ligações: {e}")
            import traceback
            traceback.print_exc()

    def _validate_rendered_bonds(self, all_atoms):
        """
        Valida todas as ligações renderizadas contra a biblioteca científica.
        Alerta se encontrar ligações suspeitas ou fantasmas.
        """
        if not BOND_LIBRARY_AVAILABLE:
            return

        suspicious_bonds = []
        invalid_bonds = []
        untabulated_pairs = set()

        # Analisar todas as ligações criadas
        for bond in self.bond_meshes:
            if not hasattr(bond, '_bond_atoms'):
                continue

            idx1, idx2 = bond._bond_atoms
            if idx1 >= len(all_atoms) or idx2 >= len(all_atoms):
                continue

            atom1 = all_atoms[idx1]
            atom2 = all_atoms[idx2]

            elem1 = atom1['element']
            elem2 = atom2['element']
            dist = np.linalg.norm(atom2['pos'] - atom1['pos'])

            # Validar com biblioteca
            validation = validate_bond(elem1, elem2, dist)

            if not validation['is_valid']:
                invalid_bonds.append((elem1, elem2, dist, validation))
            elif validation['confidence'] == 'low':
                suspicious_bonds.append((elem1, elem2, dist, validation))

            if not validation['is_tabulated']:
                untabulated_pairs.add(tuple(sorted([elem1, elem2])))

        # Reportar resultados
        total_bonds = len(self.bond_meshes)

        if invalid_bonds:
            logging.error(f"❌ LIGAÇÕES FANTASMAS DETECTADAS: {len(invalid_bonds)}/{total_bonds}")
            for elem1, elem2, dist, val in invalid_bonds[:5]:  # Mostrar até 5
                logging.error(f"  {elem1}-{elem2}: {dist:.3f} Å > {val['max_expected']:.3f} Å (máximo)")

        if suspicious_bonds:
            logging.warning(f"⚠️  Ligações suspeitas: {len(suspicious_bonds)}/{total_bonds}")
            for elem1, elem2, dist, val in suspicious_bonds[:3]:
                logging.warning(f"  {elem1}-{elem2}: {dist:.3f} Å (confiança baixa)")

        if untabulated_pairs:
            logging.info(f"ℹ️  Pares não tabelados (usando fallback): {len(untabulated_pairs)}")
            for pair in list(untabulated_pairs)[:5]:
                logging.info(f"  {pair[0]}-{pair[1]}")

        if not invalid_bonds and not suspicious_bonds:
            logging.info(f"✅ Todas as {total_bonds} ligações validadas cientificamente")

    def _get_max_bond_distance(self, element1, element2=None):
        """
        WRAPPER: Usa biblioteca universal se disponível, senão fallback local.
        """
        if BOND_LIBRARY_AVAILABLE and element2 is not None:
            # Usar biblioteca universal (>200 pares + validação científica)
            return get_bond_distance(element1, element2)

        # Fallback para método local (compatibilidade)
        return self._get_max_bond_distance_fallback(element1, element2)

    def _get_max_bond_distance_fallback(self, element1, element2=None):
        """
        Retorna a distância máxima REAL para ligação entre dois elementos.

        CORREÇÃO CRÍTICA: Usa distâncias específicas por PAR de elementos
        para evitar ligações fantasmas (ex: entre camadas no grafite).

        Args:
            element1 (str): Símbolo do primeiro elemento
            element2 (str, optional): Símbolo do segundo elemento. Se None, retorna raio individual.

        Returns:
            float: Distância máxima em Angstroms para considerar ligação

        Referências:
            - Pyykko & Atsumi, Chem. Eur. J. 15, 186 (2009) - Raios covalentes
            - VESTA: Algoritmo de ligações químicas
            - CSD (Cambridge Structural Database): Distâncias experimentais
        """

        # Se element2 não fornecido, retornar busca conservadora
        if element2 is None:
            # Raios covalentes conservadores para BUSCA inicial
            search_radii = {
                'H': 1.5, 'He': 1.5,
                'Li': 2.0, 'Be': 2.0, 'B': 2.0, 'C': 2.0, 'N': 2.0, 'O': 2.0, 'F': 2.0,
                'Na': 2.5, 'Mg': 2.5, 'Al': 2.5, 'Si': 2.5, 'P': 2.5, 'S': 2.5, 'Cl': 2.5,
                'K': 3.0, 'Ca': 3.0, 'Sc': 3.0, 'Ti': 3.0, 'V': 3.0, 'Cr': 3.0,
                'Mn': 3.0, 'Fe': 3.0, 'Co': 3.0, 'Ni': 3.0, 'Cu': 3.0, 'Zn': 3.0,
                'Ga': 3.0, 'Ge': 3.0, 'As': 3.0, 'Se': 3.0, 'Br': 3.0,
                'Rb': 3.5, 'Sr': 3.5, 'Y': 3.5, 'Zr': 3.5, 'Nb': 3.5, 'Mo': 3.5,
                'Sm': 3.5, 'Gd': 3.5, 'Tb': 3.5, 'Dy': 3.5, 'Ho': 3.5, 'Er': 3.5,
                'Ce': 3.5, 'Nd': 3.5, 'W': 3.5,
            }
            return search_radii.get(element1, 3.0)

        # ====================================================================
        # TABELA DE DISTÂNCIAS MÁXIMAS POR PAR DE ELEMENTOS
        # Baseado em raios covalentes + margem de segurança (20-30%)
        # ====================================================================

        # Normalizar ordem (sempre alfabética para consistência)
        pair = tuple(sorted([element1, element2]))

        # Distâncias máximas específicas (em Angstroms)
        # Format: (elem1, elem2): max_distance
        pair_distances = {
            # === CARBONO (casos críticos!) ===
            ('C', 'C'): 1.70,    # 🔴 CRÍTICO: Grafite/grafeno (1.42 Å típico, max 1.70)
                                  # Evita ligações inter-camadas (3.35 Å)
            ('C', 'H'): 1.20,    # C-H em orgânicos
            ('C', 'N'): 1.60,    # C-N em aminas, amidas
            ('C', 'O'): 1.60,    # C-O em álcoois, éteres
            ('C', 'S'): 2.00,    # C-S em tióis
            ('C', 'Si'): 2.00,   # C-Si em organosilanos
            ('C', 'W'): 2.30,    # Carbeto de tungstênio

            # === OXIGÊNIO (óxidos metálicos) ===
            ('O', 'O'): 1.60,    # Peróxidos (1.48 Å típico)
            ('H', 'O'): 1.10,    # OH em hidróxidos
            ('N', 'O'): 1.55,    # Óxidos de nitrogênio
            ('O', 'S'): 1.80,    # Sulfatos, sulfitos
            ('O', 'P'): 1.80,    # Fosfatos
            ('O', 'Si'): 1.90,   # Silicatos

            # === METAIS ALCALINOS E ALCALINO-TERROSOS ===
            ('Li', 'O'): 2.20,   # Óxido de lítio
            ('Na', 'O'): 2.60,   # Óxido de sódio
            ('K', 'O'): 3.00,    # Óxido de potássio
            ('Mg', 'O'): 2.30,   # Óxido de magnésio
            ('Ca', 'O'): 2.60,   # Óxido de cálcio
            ('Sr', 'O'): 2.80,   # Óxido de estrôncio

            # === METAIS DE TRANSIÇÃO - ÓXIDOS ===
            ('Ti', 'O'): 2.20,   # TiO2 (1.95 Å típico)
            ('V', 'O'): 2.10,    # Óxidos de vanádio
            ('Cr', 'O'): 2.10,   # Óxidos de cromo
            ('Mn', 'O'): 2.20,   # Óxidos de manganês
            ('Fe', 'O'): 2.20,   # Óxidos de ferro (1.95-2.05 Å)
            ('Co', 'O'): 2.20,   # Óxidos de cobalto
            ('Ni', 'O'): 2.20,   # Óxidos de níquel
            ('Cu', 'O'): 2.10,   # Óxidos de cobre
            ('Zn', 'O'): 2.20,   # Óxido de zinco
            ('Zr', 'O'): 2.30,   # Zircônia
            ('Nb', 'O'): 2.30,   # Óxidos de nióbio
            ('Mo', 'O'): 2.20,   # Óxidos de molibdênio
            ('W', 'O'): 2.20,    # Óxidos de tungstênio

            # === LANTANÍDEOS - ÓXIDOS ===
            ('Ce', 'O'): 2.60,   # CeO2 (2.34 Å típico)
            ('Nd', 'O'): 2.60,   # Óxidos de neodímio
            ('Sm', 'O'): 2.60,   # Óxidos de samário
            ('Gd', 'O'): 2.60,   # Óxidos de gadolínio

            # === SEMICONDUTORES ===
            ('Si', 'Si'): 2.50,  # Silício cristalino (2.35 Å)
            ('Ge', 'Ge'): 2.60,  # Germânio
            ('Si', 'O'): 1.90,   # Silicatos, quartzo
            ('Ge', 'O'): 2.00,   # Óxidos de germânio

            # === NITRETOS E SULFETOS ===
            ('Si', 'N'): 2.00,   # Nitreto de silício
            ('B', 'N'): 1.70,    # Nitreto de boro (grafítico)
            ('Fe', 'S'): 2.50,   # Sulfetos de ferro
            ('Cu', 'S'): 2.40,   # Sulfetos de cobre
            ('Zn', 'S'): 2.50,   # Sulfeto de zinco

            # === LIGAÇÕES METÁLICAS ===
            ('Fe', 'Fe'): 2.80,  # Ferro metálico
            ('Cu', 'Cu'): 2.80,  # Cobre metálico
            ('Al', 'Al'): 3.00,  # Alumínio metálico
            ('Au', 'Au'): 3.00,  # Ouro metálico
            ('Ag', 'Ag'): 3.00,  # Prata metálica
        }

        # Buscar distância específica
        if pair in pair_distances:
            return pair_distances[pair]

        # ====================================================================
        # FALLBACK: Calcular baseado em raios covalentes + margem
        # ====================================================================

        # Raios covalentes padrão (Pyykko & Atsumi, 2009)
        covalent_radii = {
            'H': 0.31, 'He': 0.28, 'Li': 1.28, 'Be': 0.96, 'B': 0.84,
            'C': 0.76, 'N': 0.71, 'O': 0.66, 'F': 0.57, 'Ne': 0.58,
            'Na': 1.66, 'Mg': 1.41, 'Al': 1.21, 'Si': 1.11, 'P': 1.07,
            'S': 1.05, 'Cl': 1.02, 'Ar': 1.06, 'K': 2.03, 'Ca': 1.76,
            'Sc': 1.70, 'Ti': 1.60, 'V': 1.53, 'Cr': 1.39, 'Mn': 1.39,
            'Fe': 1.32, 'Co': 1.26, 'Ni': 1.24, 'Cu': 1.32, 'Zn': 1.22,
            'Ga': 1.22, 'Ge': 1.20, 'As': 1.19, 'Se': 1.20, 'Br': 1.20,
            'Kr': 1.16, 'Rb': 2.20, 'Sr': 1.95, 'Y': 1.90, 'Zr': 1.75,
            'Nb': 1.64, 'Mo': 1.54, 'Tc': 1.47, 'Ru': 1.46, 'Rh': 1.42,
            'Pd': 1.39, 'Ag': 1.45, 'Cd': 1.44, 'In': 1.42, 'Sn': 1.39,
            'Sb': 1.39, 'Te': 1.38, 'I': 1.39, 'Xe': 1.40, 'Cs': 2.44,
            'Ba': 2.15, 'La': 2.07, 'Ce': 2.04, 'Pr': 2.03, 'Nd': 2.01,
            'Pm': 1.99, 'Sm': 1.98, 'Eu': 1.98, 'Gd': 1.96, 'Tb': 1.94,
            'Dy': 1.92, 'Ho': 1.92, 'Er': 1.89, 'Tm': 1.90, 'Yb': 1.87,
            'Lu': 1.87, 'Hf': 1.75, 'Ta': 1.70, 'W': 1.62, 'Re': 1.51,
            'Os': 1.44, 'Ir': 1.41, 'Pt': 1.36, 'Au': 1.36, 'Hg': 1.32,
            'Tl': 1.45, 'Pb': 1.46, 'Bi': 1.48, 'Po': 1.40, 'At': 1.50,
        }

        r1 = covalent_radii.get(element1, 1.5)
        r2 = covalent_radii.get(element2, 1.5)

        # Margem de segurança: 30% para ligações covalentes/iônicas
        max_distance = (r1 + r2) * 1.30

        logging.debug(f"Distância calculada {element1}-{element2}: {max_distance:.3f} Å (r1={r1:.3f}, r2={r2:.3f})")

        return max_distance

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
        Renderiza as arestas da célula unitária CORRETAMENTE.

        IMPORTANTE: Em cristalografia, a célula unitária é definida pelos vetores
        de rede a, b, c partindo da ORIGEM (0,0,0). Os 8 vértices são:
        - Origem: (0,0,0)
        - 7 combinações: a, b, c, a+b, a+c, b+c, a+b+c

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

        # Vetores de rede (base da célula unitária em coordenadas cartesianas)
        a_vec = lattice.matrix[0]
        b_vec = lattice.matrix[1]
        c_vec = lattice.matrix[2]

        # IMPORTANTE: A célula unitária SEMPRE começa em (0,0,0) na cristalografia
        # Os 8 vértices do paralelepípedo (NÃO necessariamente um cubo!)
        origin = np.array([0.0, 0.0, 0.0])
        vertices_base = np.array([
            origin,                    # Vértice 0: (0, 0, 0)
            a_vec,                     # Vértice 1: (1, 0, 0) em frac
            a_vec + b_vec,             # Vértice 2: (1, 1, 0)
            b_vec,                     # Vértice 3: (0, 1, 0)
            c_vec,                     # Vértice 4: (0, 0, 1)
            a_vec + c_vec,             # Vértice 5: (1, 0, 1)
            a_vec + b_vec + c_vec,     # Vértice 6: (1, 1, 1)
            b_vec + c_vec,             # Vértice 7: (0, 1, 1)
        ])

        # Definir as 12 arestas do paralelepípedo
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # Face inferior (z=0)
            (4, 5), (5, 6), (6, 7), (7, 4),  # Face superior (z=1)
            (0, 4), (1, 5), (2, 6), (3, 7),  # Arestas verticais conectando as faces
        ]

        # DECISÃO: Mesclar células ou mostrar todas individualmente?
        if self._merge_cells and (na > 1 or nb > 1 or nc > 1):
            # MODO MESCLADO: Mostrar apenas UMA caixa gigante englobando toda a supercélula
            # Útil didaticamente para visualização mais limpa

            # Vértices da supercélula mesclada (8 vértices do paralelepípedo grande)
            merged_vertices = np.array([
                origin,                              # (0, 0, 0)
                a_vec * na,                          # (na, 0, 0)
                a_vec * na + b_vec * nb,             # (na, nb, 0)
                b_vec * nb,                          # (0, nb, 0)
                c_vec * nc,                          # (0, 0, nc)
                a_vec * na + c_vec * nc,             # (na, 0, nc)
                a_vec * na + b_vec * nb + c_vec * nc,  # (na, nb, nc)
                b_vec * nb + c_vec * nc,             # (0, nb, nc)
            ])

            # Criar linhas para as 12 arestas da caixa mesclada
            for edge_i, edge_j in edges:
                pts = np.array([merged_vertices[edge_i], merged_vertices[edge_j]])
                line = gl.GLLinePlotItem(
                    pos=pts,
                    color=(0.2, 0.2, 0.8, 1.0),  # Azul escuro para diferenciar
                    width=2.5,  # Mais grossa para destacar
                    antialias=True
                )
                self.view_widget.addItem(line)
                self.unit_cell_lines.append(line)

            logging.info(
                f"✅ Renderizada 1 caixa mesclada (12 arestas) para supercélula {na}×{nb}×{nc}"
            )

        else:
            # MODO NORMAL: Desenhar TODAS as células individuais da supercélula
            for i in range(na):
                for j in range(nb):
                    for k in range(nc):
                        # Vetor de translação para esta célula
                        # Usa os MESMOS vetores que os átomos (garantindo alinhamento)
                        translation = a_vec * i + b_vec * j + c_vec * k

                        # Vértices da célula transladada
                        cart_vertices = vertices_base + translation

                        # Criar linhas para cada aresta
                        for edge_i, edge_j in edges:
                            pts = np.array([cart_vertices[edge_i], cart_vertices[edge_j]])
                            line = gl.GLLinePlotItem(
                                pos=pts,
                                color=(0.0, 0.0, 0.0, 1.0),
                                width=1.5,
                                antialias=True
                            )
                            self.view_widget.addItem(line)
                            self.unit_cell_lines.append(line)

            logging.info(
                f"✅ Renderizadas {len(self.unit_cell_lines)} arestas "
                f"({na}×{nb}×{nc} células individuais)"
            )

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

        # Se ativando e não houver ligações, re-renderizar tudo (mantém átomos de
        # completude e índices em sincronia com as ligações).
        if visible and self.structure and not self.bond_meshes:
            self._render_structure()

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

    # ==================================================================
    # MEDIÇÃO DE DISTÂNCIA INTERATÔMICA (baseada em VESTA, Mercury e outros)
    # ------------------------------------------------------------------
    # Duplo-clique num átomo o seleciona; uma linha pontilhada acompanha o
    # mouse; o duplo-clique num segundo átomo fixa a linha e mostra a
    # distância (em Å) no meio dela. Clique direito limpa as medições.
    # ==================================================================
    def _install_measure_handlers(self):
        """Sobrepõe os handlers de mouse do view_widget (mesmo padrão de
        override por atributo já usado em info_label.mouseDoubleClickEvent)."""
        try:
            vw = self.view_widget
            self._orig_mouse_double = vw.mouseDoubleClickEvent
            self._orig_mouse_press = vw.mousePressEvent
            self._orig_mouse_move = vw.mouseMoveEvent
            vw.mouseDoubleClickEvent = self._measure_double_click
            vw.mousePressEvent = self._measure_mouse_press
            vw.mouseMoveEvent = self._measure_mouse_move
        except Exception as e:
            logging.warning(f"Handlers de medição 3D não instalados: {e}")

    def _measure_double_click(self, ev):
        try:
            p = ev.position()
            idx = self._pick_atom(p.x(), p.y())
            if idx is not None:
                self._on_atom_picked(idx)
        except Exception as e:
            logging.warning(f"Erro no duplo-clique de medição: {e}")

    def _measure_mouse_press(self, ev):
        try:
            if ev.button() == Qt.MouseButton.RightButton and (
                self._measure_first_idx is not None or self._measurements
            ):
                self._clear_measurements()
        except Exception as e:
            logging.warning(f"Erro no clique direito de medição: {e}")
        if self._orig_mouse_press is not None:
            self._orig_mouse_press(ev)

    def _measure_mouse_move(self, ev):
        if self._orig_mouse_move is not None:
            self._orig_mouse_move(ev)
        if self._measure_first_idx is not None:
            try:
                p = ev.position()
                self._update_rubber_line(p.x(), p.y())
            except Exception:
                pass

    def _on_atom_picked(self, idx):
        if idx < 0 or idx >= len(self._atom_info):
            return
        if self._measure_first_idx is None:
            self._measure_first_idx = idx
            self._add_highlight(idx)
            self._start_rubber_line(idx)
            try:
                self.view_widget.setMouseTracking(True)
            except Exception:
                pass
        else:
            if idx != self._measure_first_idx:
                self._complete_measurement(self._measure_first_idx, idx)
            self._measure_first_idx = None
            self._remove_highlight()
            self._remove_rubber_line()
            try:
                self.view_widget.setMouseTracking(False)
            except Exception:
                pass

    def _complete_measurement(self, idx1, idx2):
        try:
            p1 = np.asarray(self._atom_info[idx1]['pos'], dtype=float)
            p2 = np.asarray(self._atom_info[idx2]['pos'], dtype=float)
            dist = float(np.linalg.norm(p2 - p1))
            line = self._make_dashed_line(p1, p2, color=(0.12, 0.12, 0.12, 1.0), width=2.5)
            if line is not None:
                self.view_widget.addItem(line)
            label = self._make_distance_label(dist)
            mid = (p1 + p2) / 2.0
            self._measurements.append({'line': line, 'label': label, 'mid': mid})
            self._update_measurement_labels()
            e1 = self._atom_info[idx1]['element']
            e2 = self._atom_info[idx2]['element']
            logging.info(f"Distância {e1}-{e2}: {dist:.3f} Å")
        except Exception as e:
            logging.warning(f"Erro ao medir distância: {e}")

    def _add_highlight(self, idx):
        self._remove_highlight()
        try:
            info = self._atom_info[idx]
            r = self.ATOMIC_RADII.get(info['element'], self.ATOMIC_RADII['default']) * self.atom_scale
            md = gl.MeshData.sphere(rows=8, cols=8, radius=r * 1.35)
            hl = gl.GLMeshItem(meshdata=md, smooth=False, drawFaces=False,
                               drawEdges=True, edgeColor=(1.0, 0.85, 0.0, 1.0),
                               glOptions='opaque')
            p = info['pos']
            hl.translate(p[0], p[1], p[2])
            self.view_widget.addItem(hl)
            self._highlight_item = hl
        except Exception as e:
            logging.warning(f"Erro ao destacar átomo: {e}")

    def _remove_highlight(self):
        if self._highlight_item is not None:
            try:
                self.view_widget.removeItem(self._highlight_item)
            except Exception:
                pass
            self._highlight_item = None

    def _start_rubber_line(self, idx):
        self._remove_rubber_line()
        try:
            p = np.asarray(self._atom_info[idx]['pos'], dtype=float)
            line = gl.GLLinePlotItem(pos=np.array([p, p]), color=(0.4, 0.4, 0.4, 0.9),
                                     width=1.5, antialias=True, mode='lines')
            self.view_widget.addItem(line)
            self._rubber_line = line
        except Exception as e:
            logging.warning(f"Erro ao iniciar linha de medição: {e}")

    def _update_rubber_line(self, mx, my):
        if self._rubber_line is None or self._measure_first_idx is None:
            return
        try:
            p1 = np.asarray(self._atom_info[self._measure_first_idx]['pos'], dtype=float)
            end = self._screen_to_plane_point(mx, my, p1)
            if end is None:
                return
            seg = self._dashed_segments(p1, end)
            if seg is not None and len(seg) >= 2:
                self._rubber_line.setData(pos=seg, mode='lines')
        except Exception:
            pass

    def _remove_rubber_line(self):
        if self._rubber_line is not None:
            try:
                self.view_widget.removeItem(self._rubber_line)
            except Exception:
                pass
            self._rubber_line = None

    def _clear_measurements(self):
        """Remove todas as medições, o destaque e a linha que acompanha o mouse."""
        self._remove_rubber_line()
        self._remove_highlight()
        self._measure_first_idx = None
        try:
            self.view_widget.setMouseTracking(False)
        except Exception:
            pass
        for m in getattr(self, '_measurements', []):
            try:
                if m.get('line') is not None:
                    self.view_widget.removeItem(m['line'])
            except Exception:
                pass
            try:
                if m.get('label') is not None:
                    m['label'].deleteLater()
            except Exception:
                pass
        self._measurements = []

    def _make_distance_label(self, dist):
        try:
            lbl = QLabel(self._format_distance(dist), self.viewer_container)
            lbl.setStyleSheet(
                "QLabel { background: rgba(255,255,255,225); color: #111;"
                " border: 1px solid #777; border-radius: 3px; padding: 0px 4px;"
                " font-size: 10pt; font-weight: bold; }"
            )
            lbl.setAttribute(Qt.WA_TransparentForMouseEvents, True)
            lbl.adjustSize()
            lbl.show()
            lbl.raise_()
            return lbl
        except Exception as e:
            logging.warning(f"Erro ao criar rótulo de distância: {e}")
            return None

    def _format_distance(self, dist):
        """Formata a distância em Å com vírgula decimal (ex.: '1,42 Å')."""
        return ("%.2f" % dist).replace('.', ',') + " Å"

    def _update_measurement_labels(self):
        if not getattr(self, '_measurements', None):
            return
        try:
            mvp = self._get_mvp()
        except Exception:
            return
        for m in self._measurements:
            lbl = m.get('label')
            if lbl is None:
                continue
            scr = self._project_to_screen(m['mid'], mvp=mvp)
            if scr is None:
                lbl.hide()
                continue
            px, py = scr
            lbl.move(int(px - lbl.width() / 2), int(py - lbl.height() / 2))
            if not lbl.isVisible():
                lbl.show()
            lbl.raise_()

    # ---------- projeção / picking ----------
    def _get_mvp(self):
        # A assinatura de projectionMatrix() varia entre versões do pyqtgraph:
        # umas aceitam projectionMatrix() (region=None), outras exigem (region, viewport).
        vw = self.view_widget
        try:
            proj = vw.projectionMatrix()
        except TypeError:
            try:
                vp = vw.getViewport()
            except Exception:
                vp = (0, 0, max(1, vw.width()), max(1, vw.height()))
            try:
                proj = vw.projectionMatrix(vp, vp)
            except TypeError:
                proj = vw.projectionMatrix(vp)
        view = vw.viewMatrix()
        m = proj * view  # QMatrix4x4 × QMatrix4x4 (ok no PySide6)
        # QMatrix4x4 × QVector4D NÃO é confiável no PySide6 -> converter p/ numpy.
        # .data() é column-major; reshape+transpose dá a matriz linha-major.
        return np.array(m.data(), dtype=float).reshape(4, 4).T

    def _project_ndc(self, point3d, mvp=None):
        """Projeta um ponto 3D -> (ndc_x, ndc_y, w). None se atrás da câmera.
        mvp é a matriz numpy 4x4 de _get_mvp()."""
        if mvp is None:
            mvp = self._get_mvp()
        clip = mvp @ np.array([float(point3d[0]), float(point3d[1]),
                               float(point3d[2]), 1.0])
        w = clip[3]
        if w <= 1e-6:
            return None
        return (clip[0] / w, clip[1] / w, w)

    def _project_to_screen(self, point3d, mvp=None):
        ndc = self._project_ndc(point3d, mvp=mvp)
        if ndc is None:
            return None
        W = self.view_widget.width()
        H = self.view_widget.height()
        return ((ndc[0] * 0.5 + 0.5) * W, (1.0 - (ndc[1] * 0.5 + 0.5)) * H)

    def _camera_right(self):
        """Vetor 'direita' aproximado da câmera (para estimar o raio projetado)."""
        try:
            eye = self.view_widget.cameraPosition()
            center = self.view_widget.opts['center']
            fwd = np.array([center.x() - eye.x(), center.y() - eye.y(),
                            center.z() - eye.z()], dtype=float)
            if np.linalg.norm(fwd) < 1e-9:
                return np.array([1.0, 0.0, 0.0])
            fwd /= np.linalg.norm(fwd)
            right = np.cross(fwd, np.array([0.0, 0.0, 1.0]))
            if np.linalg.norm(right) < 1e-6:
                return np.array([1.0, 0.0, 0.0])
            return right / np.linalg.norm(right)
        except Exception:
            return np.array([1.0, 0.0, 0.0])

    def _pick_atom(self, mx, my):
        """Retorna o índice do átomo sob (mx, my) ou None (projeção direta em NDC)."""
        try:
            if not self._atom_info:
                return None
            W = self.view_widget.width()
            H = self.view_widget.height()
            if W <= 0 or H <= 0:
                return None
            ndc_mx = 2.0 * (mx / W) - 1.0
            ndc_my = 1.0 - 2.0 * (my / H)
            mvp = self._get_mvp()
            right = self._camera_right()
            best_idx = None
            best_depth = None
            for i, info in enumerate(self._atom_info):
                p = np.asarray(info['pos'], dtype=float)
                ndc = self._project_ndc(p, mvp=mvp)
                if ndc is None:
                    continue
                ax, ay, w = ndc
                r = self.ATOMIC_RADII.get(info['element'], self.ATOMIC_RADII['default']) * self.atom_scale
                edge = self._project_ndc(p + right * r, mvp=mvp)
                if edge is None:
                    continue
                r_ndc = max(((edge[0] - ax) ** 2 + (edge[1] - ay) ** 2) ** 0.5, 0.02)
                d = ((ndc_mx - ax) ** 2 + (ndc_my - ay) ** 2) ** 0.5
                if d <= r_ndc and (best_depth is None or w < best_depth):
                    best_depth = w
                    best_idx = i
            return best_idx
        except Exception as e:
            logging.warning(f"Erro no picking de átomo: {e}")
            return None

    def _ndc_to_ray(self, ndc_x, ndc_y):
        """Converte um ponto NDC num raio (origem, direção) no espaço do mundo."""
        mvp = self._get_mvp()
        try:
            inv = np.linalg.inv(mvp)
        except np.linalg.LinAlgError:
            return None
        near = inv @ np.array([ndc_x, ndc_y, -1.0, 1.0])
        far = inv @ np.array([ndc_x, ndc_y, 1.0, 1.0])
        if abs(near[3]) < 1e-9 or abs(far[3]) < 1e-9:
            return None
        o = near[:3] / near[3]
        f = far[:3] / far[3]
        d = f - o
        if np.linalg.norm(d) < 1e-9:
            return None
        return o, d / np.linalg.norm(d)

    def _screen_to_plane_point(self, mx, my, plane_pt):
        """Interseção do raio do mouse com o plano por plane_pt, normal = direção de visão."""
        try:
            W = self.view_widget.width()
            H = self.view_widget.height()
            if W <= 0 or H <= 0:
                return None
            ray = self._ndc_to_ray(2.0 * (mx / W) - 1.0, 1.0 - 2.0 * (my / H))
            if ray is None:
                return None
            o, d = ray
            eye = self.view_widget.cameraPosition()
            center = self.view_widget.opts['center']
            n = np.array([center.x() - eye.x(), center.y() - eye.y(),
                          center.z() - eye.z()], dtype=float)
            if np.linalg.norm(n) < 1e-9:
                return None
            n /= np.linalg.norm(n)
            denom = float(np.dot(n, d))
            if abs(denom) < 1e-9:
                return None
            t = float(np.dot(n, np.asarray(plane_pt, dtype=float) - o)) / denom
            if t <= 0:
                return None
            return o + t * d
        except Exception:
            return None

    def _dashed_segments(self, p1, p2, dash=0.18, gap=0.14):
        """Gera pares de pontos (para mode='lines') formando uma linha pontilhada."""
        p1 = np.asarray(p1, dtype=float)
        p2 = np.asarray(p2, dtype=float)
        vec = p2 - p1
        length = float(np.linalg.norm(vec))
        if length < 1e-6:
            return None
        direction = vec / length
        seg = []
        t = 0.0
        step = dash + gap
        while t < length:
            seg.append(p1 + direction * t)
            seg.append(p1 + direction * min(t + dash, length))
            t += step
        if len(seg) < 2:
            seg = [p1, p2]
        return np.array(seg)

    def _make_dashed_line(self, p1, p2, color=(0.12, 0.12, 0.12, 1.0), width=2.5):
        try:
            seg = self._dashed_segments(p1, p2)
            if seg is None:
                return None
            return gl.GLLinePlotItem(pos=seg, color=color, width=width,
                                     antialias=True, mode='lines')
        except Exception as e:
            logging.warning(f"Erro ao criar linha pontilhada: {e}")
            return None

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
        # Medições ficam inválidas quando os átomos vibram
        self._clear_measurements()
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
        self.setWindowTitle(ptr("Configurações de Visualização 3D"))
        self.setMinimumWidth(300)

        layout = QVBoxLayout(self)

        # Tamanho dos átomos
        size_group = QGroupBox(ptr("Tamanho dos Átomos"))
        size_layout = QVBoxLayout(size_group)

        size_controls = QHBoxLayout()
        size_controls.addWidget(QLabel(ptr("Escala:")))

        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(25, 200)
        # Normalizar: 0.7 (real) = 100% (mostrado)
        self.size_slider.setValue(int((viewer.atom_scale / 0.7) * 100))
        self.size_slider.valueChanged.connect(self._update_size_label)
        size_controls.addWidget(self.size_slider)

        self.size_label = QLabel(f"{int((viewer.atom_scale / 0.7) * 100)}%")
        self.size_label.setMinimumWidth(50)
        size_controls.addWidget(self.size_label)

        size_layout.addLayout(size_controls)
        layout.addWidget(size_group)

        # Visibilidade
        visibility_group = QGroupBox(ptr("Visibilidade"))
        visibility_layout = QVBoxLayout(visibility_group)

        self.show_cell_check = QCheckBox(ptr("Mostrar Célula Unitária"))
        self.show_cell_check.setChecked(viewer._show_cell)
        self.show_cell_check.setToolTip(ptr("Mostra/oculta as arestas da célula unitária"))
        visibility_layout.addWidget(self.show_cell_check)

        self.show_bonds_check = QCheckBox(ptr("Mostrar Ligações"))
        self.show_bonds_check.setChecked(viewer._show_bonds)
        self.show_bonds_check.setToolTip(ptr("Mostra/oculta as ligações químicas entre átomos"))
        visibility_layout.addWidget(self.show_bonds_check)

        # NOVO: Mesclar células (mostrar apenas caixa externa da supercélula)
        self.merge_cells_check = QCheckBox(ptr("Mesclar Células (Caixa Única)"))
        self.merge_cells_check.setChecked(getattr(viewer, '_merge_cells', False))
        self.merge_cells_check.setToolTip(
            ptr("Mostra apenas uma caixa englobando toda a supercélula\nao invés de mostrar cada célula unitária individualmente.\nÚtil para visualização mais limpa e didática.")
        )
        visibility_layout.addWidget(self.merge_cells_check)

        layout.addWidget(visibility_group)

        # Espessura das Ligações
        bonds_group = QGroupBox(ptr("Ligações"))
        bonds_layout = QVBoxLayout(bonds_group)

        bonds_controls = QHBoxLayout()
        bonds_controls.addWidget(QLabel(ptr("Espessura:")))

        # Obter raio atual das ligações (padrão 0.15)
        current_radius = getattr(viewer, 'bond_radius', 0.15)

        self.bonds_slider = QSlider(Qt.Orientation.Horizontal)
        self.bonds_slider.setRange(5, 30)  # 0.05 a 0.30 Angstrom
        self.bonds_slider.setValue(int(current_radius * 100))
        self.bonds_slider.valueChanged.connect(self._update_bonds_label)
        bonds_controls.addWidget(self.bonds_slider)

        self.bonds_label = QLabel(ptr("{:.2f} Å").format(current_radius))
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
        self.bonds_label.setText(ptr("{:.2f} Å").format(radius))

    def _apply_settings(self):
        """Aplica as configurações sem fechar o diálogo."""
        # Salvar estrutura antes de aplicar configurações (proteção extra)
        saved_structure = self.viewer.structure

        if not saved_structure:
            QMessageBox.warning(
                self,
                ptr("Nenhuma Estrutura"),
                ptr("Não há estrutura carregada para aplicar configurações.")
            )
            return

        try:
            # Converter de porcentagem mostrada para escala real
            # 100% mostrado = 0.7 real (tamanho padrão otimizado)
            slider_percent = self.size_slider.value()
            self.viewer.atom_scale = (slider_percent / 100.0) * 0.7

            # Atualizar flags de visibilidade
            self.viewer._show_cell = self.show_cell_check.isChecked()
            self.viewer._show_bonds = self.show_bonds_check.isChecked()
            self.viewer._merge_cells = self.merge_cells_check.isChecked()

            # Atualizar espessura das ligações
            self.viewer.bond_radius = self.bonds_slider.value() / 100.0

            # CRÍTICO: Garantir que estrutura não seja perdida
            self.viewer.structure = saved_structure

            # Re-renderizar estrutura com novas configurações
            # _render_structure() limpa elementos visuais mas preserva self.viewer.structure
            self.viewer._render_structure()

            # Aplicar visibilidade APÓS renderização
            self._apply_visibility()

            logging.info(
                f"✅ Configurações 3D aplicadas: "
                f"tamanho={slider_percent}%, "
                f"células={'mescladas' if self.viewer._merge_cells else 'individuais'}, "
                f"ligações={'visíveis' if self.viewer._show_bonds else 'ocultas'}, "
                f"célula={'visível' if self.viewer._show_cell else 'oculta'}"
            )

        except Exception as e:
            logging.error(f"Erro ao aplicar configurações 3D: {e}")
            import traceback
            traceback.print_exc()
            # Restaurar estrutura em caso de erro
            self.viewer.structure = saved_structure
            QMessageBox.critical(
                self,
                ptr("Erro"),
                ptr("Erro ao aplicar configurações: {}").format(e)
            )

    def _apply_visibility(self):
        """Aplica configurações de visibilidade aos elementos já renderizados."""
        # Mostrar/ocultar ligações
        for bond in self.viewer.bond_meshes:
            bond.setVisible(self.viewer._show_bonds)

        # Mostrar/ocultar células unitárias
        for line in self.viewer.unit_cell_lines:
            line.setVisible(self.viewer._show_cell)

        logging.debug(
            f"Visibilidade aplicada: "
            f"{len(self.viewer.bond_meshes)} ligações ({'vis' if self.viewer._show_bonds else 'oculto'}), "
            f"{len(self.viewer.unit_cell_lines)} linhas ({'vis' if self.viewer._show_cell else 'oculto'})"
        )

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
        self.setWindowTitle(ptr("Animações 3D"))
        self.setMinimumWidth(280)

        layout = QVBoxLayout(self)

        # Rotação Contínua
        rotation_group = QGroupBox(ptr("Rotação Contínua"))
        rotation_layout = QVBoxLayout(rotation_group)

        # Velocidade de rotação
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel(ptr("Velocidade:")))

        self.speed_combo = QComboBox()
        self.speed_combo.addItem(ptr(" Lenta"), 0.5)      # 0.5 graus/frame
        self.speed_combo.addItem(ptr(" Normal"), 1.0)     # 1.0 grau/frame
        self.speed_combo.addItem(ptr(" Rápida"), 2.0)     # 2.0 graus/frame
        self.speed_combo.setCurrentIndex(1)  # Normal como padrão
        speed_layout.addWidget(self.speed_combo)

        rotation_layout.addLayout(speed_layout)

        rot_label = QLabel(ptr("Girar em torno do eixo:"))
        rotation_layout.addWidget(rot_label)

        rot_buttons = QHBoxLayout()

        btn_rot_x = QPushButton(ptr("Eixo X"))
        btn_rot_x.clicked.connect(lambda: self._start_rotation('x'))
        rot_buttons.addWidget(btn_rot_x)

        btn_rot_y = QPushButton(ptr("Eixo Y"))
        btn_rot_y.clicked.connect(lambda: self._start_rotation('y'))
        rot_buttons.addWidget(btn_rot_y)

        btn_rot_z = QPushButton(ptr("Eixo Z"))
        btn_rot_z.clicked.connect(lambda: self._start_rotation('z'))
        rot_buttons.addWidget(btn_rot_z)

        rotation_layout.addLayout(rot_buttons)
        layout.addWidget(rotation_group)

        # Vibração
        vibration_group = QGroupBox(ptr("Vibração Térmica"))
        vibration_layout = QVBoxLayout(vibration_group)

        vib_controls = QHBoxLayout()
        vib_controls.addWidget(QLabel(ptr("Amplitude:")))

        self.vib_slider = QSlider(Qt.Orientation.Horizontal)
        self.vib_slider.setRange(1, 50)
        self.vib_slider.setValue(10)
        vib_controls.addWidget(self.vib_slider)

        self.vib_label = QLabel(ptr("0.10 Å"))
        self.vib_label.setMinimumWidth(60)
        vib_controls.addWidget(self.vib_label)

        self.vib_slider.valueChanged.connect(lambda v: self.vib_label.setText(ptr("{:.2f} Å").format(v / 100)))

        vibration_layout.addLayout(vib_controls)

        btn_vibrate = QPushButton(ptr("Iniciar Vibração"))
        btn_vibrate.clicked.connect(self._start_vibration)
        vibration_layout.addWidget(btn_vibrate)

        layout.addWidget(vibration_group)

        # Controle
        control_layout = QHBoxLayout()

        self.stop_btn = QPushButton(ptr("⏹ Parar Animação"))
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
    """
    Diálogo avançado para expansão estrutural (supercélula).

    Permite:
    - Controle individual de expansão em a, b, c
    - Expansão incremental a partir da configuração atual
    - Validação científica em tempo real
    - Estimativa de átomos e ligações
    - Aplicação com preview antes de confirmar
    """

    def __init__(self, viewer, current_expansion, parent=None):
        super().__init__(parent)
        self.viewer = viewer
        self.current_expansion = list(current_expansion)  # [na, nb, nc]
        self.preview_expansion = list(current_expansion)  # Para preview

        self.setWindowTitle(ptr("Expansão Estrutural (Supercélula)"))
        self.setFixedSize(420, 420)  # Tamanho fixo, não redimensionável

        # Configurar ícone
        try:
            icon_path = self.resource_path(os.path.join("matfinder", "assets", "icons", "polvo.ico"))
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except:
            pass

        self._setup_ui()
        self._update_preview()

    def resource_path(self, relative_path):
        """Retorna caminho absoluto do recurso."""
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def _setup_ui(self):
        """Configura a interface do diálogo."""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)

        # Configuração atual (compacta)
        current_group = QGroupBox(ptr("Configuração Atual"))
        current_layout = QVBoxLayout(current_group)
        current_layout.setContentsMargins(8, 8, 8, 8)

        self.current_info_label = QLabel()
        self.current_info_label.setStyleSheet("font-size: 9pt; padding: 3px;")
        current_layout.addWidget(self.current_info_label)

        layout.addWidget(current_group)

        # Controles de expansão (minimalistas com cores)
        controls_group = QGroupBox(ptr("Expansão Estrutural"))
        controls_layout = QVBoxLayout(controls_group)
        controls_layout.setSpacing(5)
        controls_layout.setContentsMargins(8, 8, 8, 8)

        # Direção A
        self.a_spinbox = self._create_expansion_control(
            controls_layout,
            "a:",
            self.current_expansion[0],
            "#FFCCCC"  # Vermelho claro
        )

        # Direção B
        self.b_spinbox = self._create_expansion_control(
            controls_layout,
            "b:",
            self.current_expansion[1],
            "#CCFFCC"  # Verde claro
        )

        # Direção C
        self.c_spinbox = self._create_expansion_control(
            controls_layout,
            "c:",
            self.current_expansion[2],
            "#CCCCFF"  # Azul claro
        )

        layout.addWidget(controls_group)

        # Expansões predefinidas
        presets_group = QGroupBox(ptr("Expansão Predefinida"))
        presets_layout = QHBoxLayout(presets_group)
        presets_layout.setContentsMargins(8, 8, 8, 8)

        preset_btn1 = QPushButton("1×1×1")
        preset_btn1.clicked.connect(lambda: self._apply_preset(1, 1, 1))
        presets_layout.addWidget(preset_btn1)

        preset_btn2 = QPushButton("2×2×2")
        preset_btn2.clicked.connect(lambda: self._apply_preset(2, 2, 2))
        presets_layout.addWidget(preset_btn2)

        preset_btn3 = QPushButton("3×3×3")
        preset_btn3.clicked.connect(lambda: self._apply_preset(3, 3, 3))
        presets_layout.addWidget(preset_btn3)

        reset_btn = QPushButton(ptr("Resetar"))
        reset_btn.clicked.connect(self._reset_to_original)
        presets_layout.addWidget(reset_btn)

        layout.addWidget(presets_group)

        # Info dinâmica (sem preview fixo)
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet(
            "background: #F5F5F5; padding: 8px; border: 1px solid #DDD; "
            "border-radius: 3px; font-size: 9pt;"
        )
        layout.addWidget(self.info_label)

        # Botões de ação
        from PySide6.QtWidgets import QDialogButtonBox
        button_box = QDialogButtonBox()

        # Botão Preview
        preview_btn = button_box.addButton("Preview", QDialogButtonBox.ButtonRole.ApplyRole)
        preview_btn.clicked.connect(self._apply_preview)

        # Botão Aceitar
        ok_btn = button_box.addButton("Aceitar", QDialogButtonBox.ButtonRole.AcceptRole)
        ok_btn.clicked.connect(self.accept)

        # Botão Cancelar
        cancel_btn = button_box.addButton("Cancelar", QDialogButtonBox.ButtonRole.RejectRole)
        cancel_btn.clicked.connect(self.reject)

        layout.addWidget(button_box)

        # Conectar sinais de atualização
        self.a_spinbox.valueChanged.connect(self._update_preview)
        self.b_spinbox.valueChanged.connect(self._update_preview)
        self.c_spinbox.valueChanged.connect(self._update_preview)

    def _create_expansion_control(self, parent_layout, label_text, initial_value, bg_color):
        """Cria um controle de expansão minimalista."""
        container = QWidget()
        container.setStyleSheet(f"background: {bg_color}; padding: 5px; border-radius: 3px;")
        hlayout = QHBoxLayout(container)
        hlayout.setContentsMargins(5, 3, 5, 3)
        hlayout.setSpacing(8)

        # Label
        label = QLabel(label_text)
        label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        label.setMinimumWidth(20)
        hlayout.addWidget(label)

        # Botão -
        minus_btn = QPushButton("−")
        minus_btn.setFixedSize(25, 22)
        hlayout.addWidget(minus_btn)

        # SpinBox
        spinbox = QSpinBox()
        spinbox.setRange(1, 10)
        spinbox.setValue(initial_value)
        spinbox.setFixedWidth(50)
        spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        spinbox.setStyleSheet("background: white; font-weight: bold;")
        hlayout.addWidget(spinbox)

        # Botão +
        plus_btn = QPushButton("+")
        plus_btn.setFixedSize(25, 22)
        hlayout.addWidget(plus_btn)

        hlayout.addStretch()

        # Label de multiplicador
        mult_label = QLabel(ptr("x{}").format(initial_value))
        mult_label.setStyleSheet("font-weight: bold; color: #555;")
        mult_label.setMinimumWidth(35)
        hlayout.addWidget(mult_label)

        # Conectar botões
        minus_btn.clicked.connect(lambda: spinbox.setValue(max(1, spinbox.value() - 1)))
        plus_btn.clicked.connect(lambda: spinbox.setValue(min(10, spinbox.value() + 1)))
        spinbox.valueChanged.connect(lambda v: mult_label.setText(ptr("x{}").format(v)))

        parent_layout.addWidget(container)
        return spinbox

    def _apply_preset(self, na, nb, nc):
        """Aplica um preset rápido."""
        self.a_spinbox.setValue(na)
        self.b_spinbox.setValue(nb)
        self.c_spinbox.setValue(nc)

    def _reset_to_original(self):
        """Reseta para a configuração original."""
        self.a_spinbox.setValue(self.current_expansion[0])
        self.b_spinbox.setValue(self.current_expansion[1])
        self.c_spinbox.setValue(self.current_expansion[2])

    def _update_preview(self):
        """Atualiza informações dinâmicas da expansão."""
        na = self.a_spinbox.value()
        nb = self.b_spinbox.value()
        nc = self.c_spinbox.value()

        self.preview_expansion = [na, nb, nc]

        if not self.viewer.structure:
            return

        # Atualizar info atual
        n_unit = len(self.viewer.structure)
        n_current = n_unit * self.current_expansion[0] * self.current_expansion[1] * self.current_expansion[2]

        current_text = (
            ptr("Expansão: <b>{}x{}x{}</b> | Átomos: <b>{}</b>").format(self.current_expansion[0], self.current_expansion[1], self.current_expansion[2], n_current)
        )
        self.current_info_label.setText(current_text)

        # Calcular nova configuração
        n_new = n_unit * na * nb * nc
        n_cells = na * nb * nc

        # Estimativa de ligações
        avg_bonds_per_atom = 6
        est_bonds = (n_new * avg_bonds_per_atom) // 2

        # Estimativa de uso de memória (aproximada)
        # Cada átomo: ~200 bytes (coords, mesh, etc)
        # Cada ligação: ~100 bytes (cilindro mesh)
        mem_mb = (n_new * 200 + est_bonds * 100) / (1024 * 1024)

        # Status de performance
        if n_new <= 50:
            perf_status = ptr("<span style='color:green;'><b>Rápida</b></span>")
            perf_detail = "Renderização instantânea"
        elif n_new <= 200:
            perf_status = ptr("<span style='color:green;'><b>Boa</b></span>")
            perf_detail = "Performance adequada"
        elif n_new <= 500:
            perf_status = ptr("<span style='color:orange;'><b>Moderada</b></span>")
            perf_detail = "Pode apresentar lentidão"
        else:
            perf_status = ptr("<span style='color:red;'><b>Lenta</b></span>")
            perf_detail = "Renderização pode travar"

        # Texto informativo
        info_text = (
            ptr("<b>Nova Configuração: {}x{}x{}</b><br><b>Átomos Totais:</b> {} ({} células)<br><b>Ligações:</b> ~{}<br><b>Memória:</b> ~{:.1f} MB<br><b>Performance:</b> {} - {}").format(na, nb, nc, n_new, n_cells, est_bonds, mem_mb, perf_status, perf_detail)
        )

        self.info_label.setText(info_text)

    def _apply_preview(self):
        """Aplica a expansão como preview (temporário)."""
        if not self.viewer.structure:
            return

        # Obter nova expansão
        new_expansion = self.get_expansion()

        # Aplicar temporariamente
        self.viewer.supercell_expansion = new_expansion
        self.viewer._render_structure()

        # Atualizar label do viewer
        formula = self.viewer.structure.composition.reduced_formula
        n_atoms_unit = len(self.viewer.structure)
        n_atoms_total = n_atoms_unit * new_expansion[0] * new_expansion[1] * new_expansion[2]
        lattice = self.viewer.structure.lattice
        a, b, c = lattice.a, lattice.b, lattice.c

        info_html = f"""
        <div style='color: green; font-weight: bold;'>
            {formula} • {n_atoms_total} átomos ({new_expansion[0]}x{new_expansion[1]}x{new_expansion[2]})<br>
            <span style='color: #FF0000;'>a={a:.3f}</span> 
            <span style='color: #00AA00;'>b={b:.3f}</span> 
            <span style='color: #0000FF;'>c={c:.3f}</span> Å
        </div>
        """
        self.viewer.info_label.setText(info_html)
        self.viewer.info_label.setTextFormat(Qt.TextFormat.RichText)

    def get_expansion(self):
        """Retorna a expansão selecionada [na, nb, nc]."""
        return [
            self.a_spinbox.value(),
            self.b_spinbox.value(),
            self.c_spinbox.value()
        ]


