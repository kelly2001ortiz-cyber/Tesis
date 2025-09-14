import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path
from matplotlib.collections import LineCollection
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QSizePolicy
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

class dibujar_fibras(QWidget):

    def __init__(self, b, h, r, dest, n_x, n_y, direccion, *args, **kwargs):
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

        self.b, self.h, self.r, self.dest = b, h, r, dest
        self.rec = r + 0.5 * dest
        self.n_x, self.n_y = n_x, n_y
        self.direccion = direccion

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
        codes = [Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY,
                 Path.MOVETO, Path.LINETO, Path.LINETO, Path.LINETO, Path.CLOSEPOLY]
        path = Path(verts, codes)
        if self._cover_patch is None:
            self._cover_patch = patches.PathPatch(path, fc='#00FFFF', ec='#00FFFF', lw=0, alpha=0.5)
            self.ax.add_patch(self._cover_patch)
        else:
            self._cover_patch.set_path(path)

        v0 = (x0 + rec, y0 + rec)
        w, h = self.b - 2 * rec, self.h - 2 * rec
        if self._core_rect is None:
            self._core_rect = patches.Rectangle(v0, w, h, fc='#FFFF00', ec='#FFFF00', lw=0, alpha=0.5)
            self.ax.add_patch(self._core_rect)
        else:
            self._core_rect.set_xy(v0); self._core_rect.set_width(w); self._core_rect.set_height(h)

        self.ax.arrow(0, 0, self.b/10, 0, head_width=self.b/75, head_length=self.h/50, fc='#00FF00', ec='#00FF00', clip_on=True)
        self.ax.arrow(0, 0, 0, self.h/10, head_width=self.b/75, head_length=self.h/50, fc='#00FF00', ec='#00FF00', clip_on=True)
        self.ax.text(self.b/10 + 4, 0, 'X', color='#00FF00', fontsize=8, clip_on=True)
        self.ax.text(0, self.h/10 + 4, 'Y', color='#00FF00', fontsize=8, clip_on=True)

        self.rejilla()

        self.ax.set_aspect('equal', adjustable='datalim')
        mx, my = self.view_margin * self.h, self.view_margin * self.h
        self.ax.set_xlim(-self.b/2 - mx, self.b/2 + mx)
        self.ax.set_ylim(-self.h/2 - my, self.h/2 + my)
        self.ax.axis('off')
        self.canvas.draw()

    def rejilla(self):
        # geometria base
        xL, xR = -self.b/2,  self.b/2
        xiL, xiR = xL + self.rec, xR - self.rec
        yB, yT = -self.h/2,  self.h/2
        yiB, yiT = yB + self.rec, yT - self.rec

        # contornos
        self.ax.add_patch(patches.Rectangle((xL,  yB),  2*xR,  2*yT,  fill=False, ec='k', lw=0.5, clip_on=True))
        self.ax.add_patch(patches.Rectangle((xiL, yiB), 2*xiR, 2*yiT, fill=False, ec='k', lw=0.5, clip_on=True))

        # direccion de analisis
        try:
            texto_dir = self.direccion.currentText().strip()
        except Exception:
            # Si por alguna razón no es QComboBox, conviértelo a str
            texto_dir = str(self.direccion).strip() if self.direccion is not None else "Dirección Y"

        es_x = (texto_dir == "Dirección X")
        es_y = (texto_dir == "Dirección Y")

        if es_x:
            # ====== Fibras en direccion X ======
            x_lines = np.unique(np.concatenate([np.linspace(xL, xR, self.n_x + 1), [xiL, xiR]]))
            v_lines = [((x, yB), (x, yT)) for x in x_lines]
            lc_v = LineCollection(v_lines, lw=0.5, colors="k", capstyle="butt")
            lc_v.set_snap(True)
            self.ax.add_collection(lc_v)

            horizontales = [
                (yB, xL, xR),    # borde inferior exterior
                (yT, xL, xR),    # borde superior exterior
                (yiB, xiL, xiR), # límite inferior del núcleo
                (yiT, xiL, xiR)  # límite superior del núcleo
            ]
            verts = []
            for x in x_lines:
                for y, x0, x1 in horizontales:
                    if x0 <= x <= x1:
                        verts.append((x, y))

            x_edges = x_lines; x_edges.sort()
            y_edges = np.array([yB, yiB, yiT, yT]); y_edges.sort()

        elif es_y:
            # ====== Fibras en direccion Y ======
            y_lines = np.unique(np.concatenate([np.linspace(yB, yT, self.n_y + 1), [yiB, yiT]]))
            h_lines = [((xL, y), (xR, y)) for y in y_lines]
            lc_h = LineCollection(h_lines, linewidths=0.5, colors="k", capstyle="butt")
            lc_h.set_snap(True)
            self.ax.add_collection(lc_h)

            verticales = [
                (xL, yB, yT),    # borde exterior izq.
                (xR, yB, yT),    # borde exterior der.
                (xiL, yiB, yiT), # borde interior izq.
                (xiR, yiB, yiT), # borde interior der.
            ]
            verts = []
            for y in y_lines:
                for x, y0, y1 in verticales:
                    if y0 <= y <= y1:
                        verts.append((x, y))

            x_edges = np.array([xL, xiL, xiR, xR]); x_edges.sort()
            y_edges = y_lines; y_edges.sort()

        # guardar vertices
        V = np.unique(np.round(np.asarray(verts, float), 10), axis=0) if verts else np.empty((0, 2))

        # centros
        xc = (x_edges[:-1] + x_edges[1:]) / 2
        yc = (y_edges[:-1] + y_edges[1:]) / 2
        Xc, Yc = np.meshgrid(xc, yc, indexing="xy")

        # centro de esquinas
        corner_centers = np.array([
            [(xL + xiL)/2, (yiT + yT)/2],  # sup-izq
            [(xiR + xR)/2, (yiT + yT)/2],  # sup-der
            [(xL + xiL)/2, (yB + yiB)/2],  # inf-izq
            [(xiR + xR)/2, (yB + yiB)/2],  # inf-der
        ])
        Xf, Yf = Xc.ravel(), Yc.ravel()
        mask = np.ones(Xf.shape, dtype=bool)
        for cx, cy in corner_centers:
            mask &= ~(np.isclose(Xf, cx, atol=1e-10) & np.isclose(Yf, cy, atol=1e-10))

        # dibujar y guardar
        self.ax.scatter(Xf[mask], Yf[mask], color="red", s=10, zorder=3, alpha=0.5)
        self.centros = list(zip(Xf[mask], Yf[mask]))

        # buffers para resaltado
        self._V = V if V.size else np.empty((0, 2))
        self._C = np.array(self.centros, float) if self.centros else np.empty((0, 2))

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
        if p:
            self.add_highlight(p); self.label.setText(f"X = {p[0]:.2f}    Y = {p[1]:.2f}")
        else:
            self.remove_highlight()
            self.label.setText(f"X = {event.xdata:.2f}    Y = {event.ydata:.2f}" if (event.xdata is not None and event.ydata is not None) else " ")

    def add_highlight(self, p):
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