import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import PatchCollection
import matplotlib.patches as patches
from matplotlib.path import Path

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
    
class dibujar_seccion_viga(QWidget):
    def __init__(self, b, h, r, dest, n_sup, n_inf, d_sup, d_inf, *args, show_highlight=True, **kwargs):
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

        self.b = b
        self.h = h
        self.r = r
        self.dest = dest
        self.rec = r + 0.5 * dest
        self.n_sup = n_sup
        self.n_inf = n_inf
        self.d_sup = d_sup
        self.d_inf = d_inf

        self.show_highlight = bool(show_highlight)
        self.highlight_ms = 7.5
        self.pix_tol = 10.0
        self.view_margin = 0.05

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

        self.barras_longitudinales(x0, y0)

        self.ax.set_aspect('equal', adjustable='datalim')
        mx, my = self.view_margin * self.h, self.view_margin * self.h
        self.ax.set_xlim(-self.b/2 - mx, self.b/2 + mx)
        self.ax.set_ylim(-self.h/2 - my, self.h/2 + my)
        self.ax.axis('off')
        self.canvas.draw()

    def barras_longitudinales(self, x0, y0):
        if getattr(self, "_bars_pc", None) is not None:
            try: self._bars_pc.remove()
            except Exception: pass
            self._bars_pc = None

        # centros “pegados” al contorno interior
        circles, centers = [], []
        x_start, x_end = x0 + self.rec + self.dest/2 + self.d_sup/2, x0 + self.b - self.rec - self.dest/2 - self.d_sup/2
        y_top = y0 + self.h - self.rec - self.dest/2 - self.d_sup/2
        xsup = np.linspace(x_start, x_end, self.n_sup)

        # fila superior
        for x in xsup:
            circles.append(patches.Circle((x, y_top), self.d_sup/2))
            centers.append((x, y_top))

        # fila inferior
        x_start, x_end = x0 + self.rec + self.dest/2 + self.d_inf/2, x0 + self.b - self.rec - self.dest/2 - self.d_inf/2
        y_inf = y0 + self.rec + self.dest/2 + self.d_inf/2
        xinf = np.linspace(x_start, x_end, self.n_inf)
        for x in xinf:
            circles.append(patches.Circle((x, y_inf), self.d_inf/2))
            centers.append((x, y_inf))

        # una sola colección; el radio queda EXACTO en unidades de datos
        self._bars_pc = self.ax.add_collection(
            PatchCollection(circles, facecolor='k', edgecolor='none', zorder=10))

        # reemplaza _C para el hover con los centros de barras
        self.circulos_centros = centers
        self._C = np.asarray(centers, dtype=float)
        # self.canvas.draw_idle()

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
