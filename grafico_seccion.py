import sys
import numpy as np
import matplotlib
matplotlib.use('QtAgg')  # Backend interactivo para visualizar con PySide6/Qt
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
from matplotlib.collections import LineCollection
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSizePolicy
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT

from seccion import utilidades

class CustomToolbar(NavigationToolbar2QT):
    toolitems = [
        ('Home', 'Reset original view', 'home', 'home'),
        ('Back', 'Back to previous view', 'back', 'back'),
        ('Forward', 'Forward to next view', 'forward', 'forward'),
        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        ('Save', 'Save the figure', 'filesave', 'save_figure'),
    ]

class dibujar_seccion(QWidget):

    def __init__(self, data, tipo, config, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.figure, self.ax = plt.subplots()
        self.canvas = FigureCanvas(self.figure)

        self.toolbar = CustomToolbar(self.canvas, self)
        self.toolbar.setMaximumHeight(28)
        self.toolbar.coordinates = False

        self.figure.subplots_adjust(left=0, right=1, top=1, bottom=0)
        self.ax.set_position([0, 0, 1, 1])
        self.ax.margins(0, 0)

        self.label = QLabel(" ", self)
        self.label.setFixedHeight(24)
        self.label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        self.label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)


        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.label)

        self.data = data
        self.tipo = str(tipo).strip().lower()
        self.config = config

        self.highlight_ms = 7.5
        self.pix_tol = 10.0
        self.view_margin = 0.05

        self._cover_patch = None
        self._core_rect = None
        self.highlight_artist = None

        self.color_cover = "#00FFFF"
        self.color_core = "#FFFF00"

        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('draw_event', self._on_draw)

        self._leer_data()

        if self.config[0]:
            self.seccion()
        if self.config[1]:
            self.armado()
        if self.config[2]:
            self.rejilla()
        if self.config[3]:
            self.ejes()

        self.espacio()
        
        self.canvas.draw_idle()


    def _leer_data(self):
        # ---------------------------------------------------------
        # Datos de la seccion
        # ---------------------------------------------------------
        if self.tipo == "columna":
            (
                self.b,
                self.h,
                self.r,
                self.de,
                self.d_edge,
                self.d_corner,
                self.nb_x,
                self.nb_y,
                self.nf_x,
                self.nf_y,
                self.confinado,
            ) = self.data

            self.nb_x = int(self.nb_x)
            self.nb_y = int(self.nb_y)

        elif self.tipo == "viga":
            (
                self.b,
                self.h,
                self.r,
                self.de,
                self.d_sup,
                self.d_inf,
                self.nb_sup,
                self.nb_inf,
                self.nf_x,
                self.nf_y,
                self.confinado,
            ) = self.data

            self.nb_sup = int(self.nb_sup)
            self.nb_inf = int(self.nb_inf)

        # ---------------------------------------------------------
        # Armado de la seccion
        # ---------------------------------------------------------
        if self.tipo == "columna":
            barras_2d = utilidades.barras_columna(
                self.b,
                self.h,
                self.r,
                self.de,
                self.nb_x,
                self.nb_y,
                self.d_corner,
                self.d_edge,
                "x",
                False)

        elif self.tipo == "viga":
            barras_2d = utilidades.barras_viga(
                self.b,
                self.h,
                self.r,
                self.de,
                self.nb_sup,
                self.nb_inf,
                self.d_sup,
                self.d_inf,
                "x",
                False)

        self.barras_2d = barras_2d


    def seccion(self):
        self.ax.cla()
        self._cover_patch = None
        self._core_rect = None
        self.highlight_artist = None

        # ---------------------------------------------------------
        # Geometria base
        # ---------------------------------------------------------
        x_min = -self.b / 2
        x_max =  self.b / 2
        y_min = -self.h / 2
        y_max =  self.h / 2

        rec_cl = self.r + self.de / 2

        x_core_min = x_min + rec_cl
        x_core_max = x_max - rec_cl
        y_core_min = y_min + rec_cl
        y_core_max = y_max - rec_cl

        # ---------------------------------------------------------
        # Fondo de recubrimiento
        # ---------------------------------------------------------
        verts = [
            # Contorno exterior
            (x_min, y_min),
            (x_max, y_min),
            (x_max, y_max),
            (x_min, y_max),
            (x_min, y_min),

            # Contorno interior
            (x_core_min, y_core_min),
            (x_core_min, y_core_max),
            (x_core_max, y_core_max),
            (x_core_max, y_core_min),
            (x_core_min, y_core_min),
        ]

        codes = [
            Path.MOVETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.CLOSEPOLY,

            Path.MOVETO,
            Path.LINETO,
            Path.LINETO,
            Path.LINETO,
            Path.CLOSEPOLY,
        ]

        path = Path(verts, codes)

        self._cover_patch = patches.PathPatch(
            path,
            facecolor=self.color_cover,
            linewidth=0,
            alpha=0.45,
            zorder=0.5
        )
        self.ax.add_patch(self._cover_patch)

        # ---------------------------------------------------------
        # Fondo del nucleo
        # ---------------------------------------------------------
        if not self.confinado:
            self.color_core = self.color_cover

        self._core_rect = patches.Rectangle(
            (x_core_min, y_core_min),
            (x_core_max - x_core_min),
            (y_core_max - y_core_min),
            facecolor=self.color_core,
            linewidth=0,
            alpha=0.45,
            zorder=0
        )
        self.ax.add_patch(self._core_rect)

        # ---------------------------------------------------------
        # Contornos
        # ---------------------------------------------------------
        self._cover_ext = patches.Rectangle(
            (x_min, y_min),
            (x_max - x_min),
            (y_max - y_min),
            edgecolor="black",
            fill=False,
            linewidth=0.5,
            zorder=1
        )
        self.ax.add_patch(self._cover_ext)

        if self.confinado:
            self._core_ext = patches.Rectangle(
                (x_core_min, y_core_min),
                (x_core_max - x_core_min),
                (y_core_max - y_core_min),
                edgecolor="black",
                fill=False,
                linewidth=0.5,
                zorder=1
            )
            self.ax.add_patch(self._core_ext)

            seccion = np.vstack([verts])
            self._seccion = np.unique(seccion, axis=0)

        else:
            seccion = np.vstack([verts[0:5]])
            self._seccion = np.unique(seccion, axis=0)

        # # ---------------------------------------------------------
        # # Contorno estribo
        # # ---------------------------------------------------------
        # de_med = self.de/2

        # verts = [
        #     # Contorno exterior
        #     (x_core_min - de_med, y_core_min - de_med),
        #     (x_core_min - de_med, y_core_max + de_med),
        #     (x_core_max + de_med, y_core_max + de_med),
        #     (x_core_max + de_med, y_core_min - de_med),
        #     (x_core_min - de_med, y_core_min - de_med),

        #     # Contorno interior
        #     (x_core_min + de_med, y_core_min + de_med),
        #     (x_core_min + de_med, y_core_max - de_med),
        #     (x_core_max - de_med, y_core_max - de_med),
        #     (x_core_max - de_med, y_core_min + de_med),
        #     (x_core_min + de_med, y_core_min + de_med),
        # ]

        # codes = [
        #     Path.MOVETO,
        #     Path.LINETO,
        #     Path.LINETO,
        #     Path.LINETO,
        #     Path.CLOSEPOLY,

        #     Path.MOVETO,
        #     Path.LINETO,
        #     Path.LINETO,
        #     Path.LINETO,
        #     Path.CLOSEPOLY,
        # ]

        # path2 = Path(verts, codes)

        # self._estribo = patches.PathPatch(
        #     path2,
        #     fill=False,
        #     edgecolor='gray',
        #     linestyle='--',
        #     linewidth=0.5,
        #     zorder=1
        # )
        # self.ax.add_patch(self._estribo)


    def armado(self):
        # ---------------------------------------------------------
        # Barras longitudinales
        # ---------------------------------------------------------
        if self.barras_2d is not None and len(self.barras_2d) > 0:
            radios = np.sqrt(self.barras_2d[:, 2] / np.pi)

            for (xs, ys, _), rb in zip(self.barras_2d, radios):
                self.ax.add_patch(
                    patches.Circle(
                        (xs, ys),
                        rb,
                        fill=True,
                        color="black",
                        zorder=7
                    )
                )

        # ---------------------------------------------------------
        # Centro de barras longitudinales
        # ---------------------------------------------------------
        if self.barras_2d is not None and len(self.barras_2d) > 0:
            armado = np.vstack((self.barras_2d[:, :2]))

        self._armado = np.unique(armado, axis=0)


    def rejilla(self):
        # ---------------------------------------------------------
        # Calculo de fibras
        # ---------------------------------------------------------
        cover_2d, core_2d = utilidades.malla(
            self.b, 
            self.h, 
            self.r, 
            self.de, 
            self.nf_x, 
            self.nf_y, 
            "x",  
            self.barras_2d, 
            self.confinado, 
            False)

        # ---------------------------------------------------------
        # Geometria base
        # ---------------------------------------------------------
        x_min = -self.b / 2
        x_max =  self.b / 2
        y_min = -self.h / 2
        y_max =  self.h / 2

        nf_x = int(self.nf_x)
        nf_y = int(self.nf_y)

        rec_cl = self.r + self.de / 2

        x_core_min = x_min + rec_cl
        x_core_max = x_max - rec_cl
        y_core_min = y_min + rec_cl
        y_core_max = y_max - rec_cl

        # ---------------------------------------------------------
        # Malla base
        # ---------------------------------------------------------
        x_edges = np.linspace(x_min, x_max, nf_x + 1)
        y_edges = np.linspace(y_min, y_max, nf_y + 1)

        lineas_verticales = [((x, y_min), (x, y_max)) for x in x_edges]
        lineas_horizontales = [((x_min, y), (x_max, y)) for y in y_edges]

        self.ax.add_collection(
            LineCollection(
                lineas_verticales + lineas_horizontales,
                linewidths=0.50,
                colors="black",
                alpha=0.80,
                capstyle="butt",
                zorder=2
            )
        )

        # ---------------------------------------------------------
        # Contorno del nucleo
        # ---------------------------------------------------------
        contorno_nucleo = [
            ((x_core_min, y_core_max), (x_core_max, y_core_max)),
            ((x_core_min, y_core_max), (x_core_min, y_core_min)),
            ((x_core_min, y_core_min), (x_core_max, y_core_min)),
            ((x_core_max, y_core_min), (x_core_max, y_core_max))
        ]

        if self.confinado:
            self.ax.add_collection(
                LineCollection(
                    contorno_nucleo,
                    linewidths=0.50,
                    colors="black",
                    alpha=0.80,
                    capstyle="butt",
                    zorder=3
                )
            )

        # ---------------------------------------------------------
        # Centroides de fibras
        # ---------------------------------------------------------
        if cover_2d is not None and len(cover_2d) > 0:
            self.ax.scatter(
                cover_2d[:, 0],
                cover_2d[:, 1],
                s=20,
                color="red",
                marker="o",
                zorder=5,
                label="Cover"
            )

        if core_2d is not None and len(core_2d) > 0:
            self.ax.scatter(
                core_2d[:, 0],
                core_2d[:, 1],
                s=20,
                color="red",
                marker="o",
                zorder=5,
                label="Core"
            )

        # ---------------------------------------------------------
        # Guardar puntos para resaltado con mouse
        # ---------------------------------------------------------
        
        # Centros de fibras
        centros_arrays = []

        if cover_2d is not None and len(cover_2d) > 0:
            centros_arrays.append(cover_2d[:, :2])

        if core_2d is not None and len(core_2d) > 0:
            centros_arrays.append(core_2d[:, :2])
        
        fibra = np.vstack(centros_arrays)
        self._fibra = np.unique(fibra, axis=0)

        # Intersecciones de rejilla
        Xv, Yv = np.meshgrid(x_edges, y_edges, indexing="xy")
        rejilla = np.column_stack((Xv.ravel(), Yv.ravel()))

        if self.confinado:
            x_en_nucleo = x_edges[
                    (x_edges >= x_core_min) & 
                    (x_edges <= x_core_max)]
            
            y_en_nucleo = y_edges[
                (y_edges >= y_core_min) &
                (y_edges <= y_core_max)]

            inter_horizontales = np.column_stack((
                np.repeat(x_en_nucleo, 2),
                np.tile([y_core_min, y_core_max], len(x_en_nucleo))
            ))

            inter_verticales = np.column_stack((
                np.tile([x_core_min, x_core_max], len(y_en_nucleo)),
                np.repeat(y_en_nucleo, 2)
            ))

            interseccion_nucleo = np.vstack((
                inter_horizontales,
                inter_verticales
            ))

            esquinas_nucleo = np.array([
                [x_core_min, y_core_min],
                [x_core_max, y_core_min],
                [x_core_max, y_core_max],
                [x_core_min, y_core_max],
            ], dtype=float)

            rejilla = np.vstack((rejilla, interseccion_nucleo, esquinas_nucleo))
            self._rejilla = np.unique(rejilla, axis=0)

        else:
            rejilla = np.vstack((rejilla))
            self._rejilla = np.unique(rejilla, axis=0)


    def ejes(self):
        # ---------------------------------------------------------
        # Ejes locales X-Y
        # ---------------------------------------------------------
        lx = 0.10 * self.b
        ly = 0.10 * self.h

        color_ejes = "#00AA00"
        lw_ejes = 1.5

        flecha_x = patches.FancyArrowPatch(
            (0, 0),
            (lx, 0),
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=lw_ejes,
            color=color_ejes,
            shrinkA=0,
            shrinkB=0,
            zorder=20
        )
        self.ax.add_patch(flecha_x)

        flecha_y = patches.FancyArrowPatch(
            (0, 0),
            (0, ly),
            arrowstyle="-|>",
            mutation_scale=14,
            linewidth=lw_ejes,
            color=color_ejes,
            shrinkA=0,
            shrinkB=0,
            zorder=20
        )
        self.ax.add_patch(flecha_y)

        self.ax.text(
            lx + 0.015 * self.b, 0, "X",
            color=color_ejes, fontsize=9,
            fontweight="bold", va="center", zorder=21)

        self.ax.text(0, ly + 0.015 * self.h, "Y",
            color=color_ejes, fontsize=9, 
            fontweight="bold", ha="center", zorder=21)

        ejes = np.vstack([(0, 0)])
        self._ejes = np.unique(ejes , axis=0)


    def espacio(self):
        # ---------------------------------------------------------
        # Formato del espacio de dibujo
        # ---------------------------------------------------------
        margen_y = self.view_margin * self.h
        y_min = -self.h / 2
        y_max = self.h / 2

        self.ax.set_aspect("equal", adjustable="datalim", anchor="C")

        self.ax.set_ylim(y_min - margen_y, y_max + margen_y)
        self.ax.autoscale(enable=True, axis="x", tight=True)

        self.ax.margins(0, 0)
        self.ax.set_xticks([])
        self.ax.set_yticks([])

        for spine in self.ax.spines.values():
            spine.set_visible(False)

        self.ax.set_facecolor("white")
        self.ax.set_axis_off()

    def _on_draw(self, event=None):
        trans = self.ax.transData.transform

        self._groupos = []

        group_names = [
            ("_armado", "_armado_px"),
            ("_seccion", "_seccion_px"),
            ("_ejes", "_ejes_px"),
            ("_fibra", "_fibre_px"),
            ("_rejilla", "_rejilla_px"),
        ]

        for real_name, px_name in group_names:
            real_pts = getattr(self, real_name, None)

            if real_pts is None:
                px_pts = np.empty((0, 2))
                setattr(self, px_name, px_pts)
                continue

            if real_pts.size:
                px_pts = trans(real_pts)
                self._groupos.append((px_pts, real_pts))
            else:
                px_pts = np.empty((0, 2))

            setattr(self, px_name, px_pts)


    def on_mouse_move(self, event):
        if not (event.inaxes and event.x is not None and event.y is not None):
            self.label.setText(" ")
            self.remove_highlight()
            return

        def nearest(px_pts):
            if len(px_pts) == 0:
                return None
            
            d = np.hypot(px_pts[:,0]-event.x, px_pts[:,1]-event.y)
            i = d.argmin()
            
            return i, d[i]

        best_p = None
        best_d = None

        for px_pts, real_pts in self._groupos:
            result = nearest(px_pts)

            if result is None:
                continue

            i, d = result

            if i is not None and d <= self.pix_tol:
                if best_d is None or d < best_d:
                    best_d = d
                    best_p = tuple(real_pts[i])

        if best_p is not None:
            self.add_highlight(best_p)
            self.label.setText(f"X = {best_p[0]:.2f}    Y = {best_p[1]:.2f}")
        else:
            self.remove_highlight()
            
            if event.xdata is not None and event.ydata is not None:
                self.label.setText(f"X = {event.xdata:.2f}    Y = {event.ydata:.2f}")
            else:
                self.label.setText(" ")


    def add_highlight(self, p):
        if self.highlight_artist is None:
            (artist,) = self.ax.plot(p[0], p[1], marker='o', ms=self.highlight_ms, mfc='red', mec='red', mew=0.5, alpha=0.8, zorder=21)
            self.highlight_artist = artist
        else:
            self.highlight_artist.set_data([p[0]], [p[1]])
            self.highlight_artist.set_visible(True)
        
        self.canvas.draw_idle()


    def remove_highlight(self):
        if self.highlight_artist is not None and self.highlight_artist.get_visible():
            self.highlight_artist.set_visible(False)
            self.canvas.draw_idle()


    def closeEvent(self, event):
        plt.close(self.figure)
        super().closeEvent(event)


    def close(self):
        plt.close(self.figure)
        super().close()