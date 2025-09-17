
import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
from matplotlib.collections import LineCollection, PatchCollection

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QSizePolicy
)
from PySide6.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT

class CustomToolbar(NavigationToolbar2QT):
    toolitems = [
        ('Home', 'Reset original view', 'home', 'home'),
        ('Back', 'Back to previous view', 'back', 'back'),
        ('Forward', 'Forward to next view', 'forward', 'forward'),
        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        ('Save', 'Save the figure', 'filesave', 'save_figure'),
    ]

class dibujar_seccion_columna(QWidget):
    def __init__(self, b, h, r, dest, n_x, n_y, d_corner, d_edge, *args, show_highlight=True, **kwargs):
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
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        layout.addWidget(self.label)

        self.b, self.h, self.r, self.dest, self.d_edge, self.d_corner = b, h, r, dest, d_edge, d_corner
        self.rec = r + 0.5 * dest
        self.n_x, self.n_y = n_x, n_y

        self.show_highlight = bool(show_highlight)
        self.highlight_ms = 7.5
        self.pix_tol = 10.0
        self.view_margin = 0.4

        self._cover_patch = None
        self._core_rect = None
        self.highlight_artist = None

        self.vertices, self.centros = [], []
        self._V = np.empty((0, 2))
        self._C = np.empty((0, 2))
        self._Vpx = np.empty((0, 2))
        self._Cpx = np.empty((0, 2))

        self.seccion()
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        self.canvas.mpl_connect('draw_event', self._on_draw)

    def seccion(self):
        x0, y0, rec = -0.5 * self.b, -0.5 * self.h, self.rec

        verts = [
            (x0, y0), (x0 + self.b, y0), (x0 + self.b, y0 + self.h), (x0, y0 + self.h), (x0, y0),
            (x0 + rec, y0 + rec), (x0 + rec, y0 + self.h - rec),
            (x0 + self.b - rec, y0 + self.h - rec), (x0 + self.b - rec, y0 + rec), (x0 + rec, y0 + rec)
        ]
        self._V = np.asarray(verts, dtype=float)
        codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY,
                 Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
        path = Path(verts, codes)
        if self._cover_patch is None:
            self._cover_patch = patches.PathPatch(path, fc='#00FFFF', ec='k', lw=1, alpha=0.5)
            self.ax.add_patch(self._cover_patch)
        else:
            self._cover_patch.set_path(path)

        v0 = (x0 + rec, y0 + rec)
        w, h = self.b - 2 * rec, self.h - 2 * rec
        if self._core_rect is None:
            self._core_rect = patches.Rectangle(v0, w, h, fc='#FFFF00', ec='k', lw=1, alpha=0.5)
            self.ax.add_patch(self._core_rect)
        else:
            self._core_rect.set_xy(v0); self._core_rect.set_width(w); self._core_rect.set_height(h)

        verts = [
            (x0 + self.r, y0 + self.r),
            (x0 + self.b - self.r, y0 + self.r),
            (x0 + self.b - self.r, y0 + self.h - self.r),
            (x0 + self.r, y0 + self.h - self.r),
            (x0 + self.r, y0 + self.r),

            (x0 + self.rec + self.dest/2, y0 + self.rec + self.dest/2),
            (x0 + self.rec + self.dest/2, y0 + self.h - self.rec - self.dest/2),
            (x0 + self.b - self.rec - self.dest/2, y0 + self.h - self.rec - self.dest/2),
            (x0 + self.b - self.rec - self.dest/2, y0 + self.rec + self.dest/2),
            (x0 + self.rec + self.dest/2, y0 + self.rec + self.dest/2)
        ]
        codes = [
            Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY,
            Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY
        ]
        path = Path(verts, codes)
        patch = patches.PathPatch(path, ec='gray', lw=1, linestyle='--', fill=False)
        self.ax.add_patch(patch)

        self.ax.arrow(0, 0, self.b/10, 0, head_width=self.b/75, head_length=self.h/50, fc='#00FF00', ec='#00FF00', clip_on=True)
        self.ax.arrow(0, 0, 0, self.h/10, head_width=self.b/75, head_length=self.h/50, fc='#00FF00', ec='#00FF00', clip_on=True)
        self.ax.text(self.b/10 + 4, 0, 'X', color='#00FF00', fontsize=8, clip_on=True)
        self.ax.text(0, self.h/10 + 4, 'Y', color='#00FF00', fontsize=8, clip_on=True)

        self.barras_longitudinales(self.n_x, self.n_y, self.d_edge, x0, y0)

        self.ax.set_aspect('equal', adjustable='datalim')
        mx, my = self.view_margin * self.h, self.view_margin * self.h
        self.ax.set_xlim(-self.b/2 - mx, self.b/2 + mx)
        self.ax.set_ylim(-self.h/2 - my, self.h/2 + my)
        self.ax.axis('off')
        self.canvas.draw()

    def barras_longitudinales(self, n_x, n_y, d_edge, x0, y0):
        if getattr(self, "_bars_pc", None) is not None:
            try: self._bars_pc.remove()
            except Exception: pass
            self._bars_pc = None

        # centros barras laterales
        x_start_edge, x_end_edge = x0 + self.rec + self.dest/2 + d_edge/2, x0 + self.b - self.rec - self.dest/2 - d_edge/2
        y_start_edge, y_end_edge = y0 + self.rec + self.dest/2 + d_edge/2, y0 + self.h - self.rec - self.dest/2 - d_edge/2

        # centros barras esquineras
        x_start_corner, x_end_corner = x0 + self.rec + self.dest/2 + self.d_corner/2, x0 + self.b - self.rec - self.dest/2 - self.d_corner/2
        y_start_corner, y_end_corner = y0 + self.rec + self.dest/2 + self.d_corner/2, y0 + self.h - self.rec - self.dest/2 - self.d_corner/2

        xs_corner = np.linspace(x_start_corner, x_end_corner, 2)
        ys_corner = np.linspace(y_start_corner, y_end_corner, 2)

        xs_edge = np.linspace(x_start_corner, x_end_corner, n_x)[1:-1]
        ys_edge = np.linspace(y_start_corner, y_end_corner, n_y)[1:-1]

        circles, centers = [], []

        # filas inferior y superior (sin esquinas)
        for x in xs_edge:
            circles.append(patches.Circle((x, y_start_edge), d_edge/2))
            circles.append(patches.Circle((x, y_end_edge),   d_edge/2))
            centers.append((x, y_start_edge))
            centers.append((x, y_end_edge))

        # columnas izquierda y derecha (sin esquinas)
        for y in ys_edge:
            circles.append(patches.Circle((x_start_edge, y), d_edge/2))
            circles.append(patches.Circle((x_end_edge,   y), d_edge/2))
            centers.append((x_start_edge, y))
            centers.append((x_end_edge, y))

        # esquinas
        for x in xs_corner:
            circles.append(patches.Circle((x, y_start_corner), self.d_corner/2))
            circles.append(patches.Circle((x, y_end_corner),   self.d_corner/2))
            centers.append((x, y_start_corner))
            centers.append((x, y_end_corner))

        # una sola colección; el radio queda EXACTO en unidades de datos
        self._bars_pc = self.ax.add_collection(
            PatchCollection(circles, facecolor='k', edgecolor='none', zorder=10))

        # reemplaza _C para el hover con los centros de barras
        self.circulos_centros = centers
        self._C = np.asarray(centers, dtype=float)
        
    def _on_draw(self, event=None):
        trans = self.ax.transData.transform
        self._Vpx = trans(self._V) if self._V.size else np.empty((0, 2))
        self._Cpx = trans(self._C) if self._C.size else np.empty((0, 2))

    def on_mouse_move(self, event):
        if not (event.inaxes and event.x is not None and event.y is not None):
            self.label.setText(" "); self.remove_highlight(); return
        def nearest(px_pts, tol):
            if len(px_pts) == 0: return None
            d = np.hypot(px_pts[:,0]-event.x, px_pts[:,1]-event.y); i = d.argmin()
            return i if d[i] <= tol else None
        i = nearest(self._Vpx, self.pix_tol)
        p = tuple(self._V[i]) if i is not None else None
        if p is None:
            j = nearest(self._Cpx, self.pix_tol)
            p = tuple(self._C[j]) if j is not None else None
        if p and self.show_highlight:
            self.add_highlight(p)
            self.label.setText(f"X = {p[0]:.2f}    Y = {p[1]:.2f}")
        else:
            self.remove_highlight()
            self.label.setText(f"X = {event.xdata:.2f}    Y = {event.ydata:.2f}" if (event.xdata is not None and event.ydata is not None) else " ")

    def add_highlight(self, p):
        if not self.show_highlight:
            return
        if self.highlight_artist is None:
            (a,) = self.ax.plot(p[0], p[1], marker='o', ms=self.highlight_ms, mfc='red', mec='red', mew=0.5, alpha=0.8, zorder=21)
            self.highlight_artist = a
        else:
            self.highlight_artist.set_data([p[0]], [p[1]])
            self.highlight_artist.set_visible(True)
        self.canvas.draw_idle()

    def remove_highlight(self):
        if self.highlight_artist is not None and self.highlight_artist.get_visible():
            self.highlight_artist.set_visible(False)
            self.canvas.draw_idle()