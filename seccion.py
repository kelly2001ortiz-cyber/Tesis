import numpy as np
from shapely.geometry import Point, box

class utilidades:
    """
    Utilidades geometricas de secciones de concreto reforzado.

    Metodos disponibles:
        - barras_columna : coordenadas y areas de barras en columnas
        - barras_viga    : coordenadas y areas de barras en vigas
        - malla          : discretizacion de la seccion en fibras

    Coordenadas:
        x = 0 en el centro de la seccion
        y = 0 en el centro de la seccion
        x positivo hacia la derecha
        y positivo hacia arriba
    """

    @staticmethod
    def barras_columna(b, h, r, de, nb_x, nb_y, d_corner, d_edge, eje, agrupar):
        """
        Genera coordenadas y areas de barras individuales 2D y agrupadas
        para una columna rectangular.

        Parametros:
            b        : ancho de la seccion
            h        : altura de la seccion
            r        : recubrimiento libre
            de       : diametro de estribos
            nb_x     : numero de barras en direccion x
            nb_y     : numero de barras en direccion y
            d_corner : diametro de barras de esquina
            d_edge   : diametro de barras laterales
            eje      : eje de analisis ("x" o "y")
            agrupar  : permte agrupar fibras dependiendo del eje

        Retorna:
            Si agrupar=False:
                retorna barras_2d = array [x_i, y_i, A_i]

            Si agrupar=True:
                retorna As = array [coord_i, A_i]
        """

        eje = eje.lower()
        
        # Area de una barra
        Ab_corner = np.pi * d_corner**2 / 4
        Ab_edge = np.pi * d_edge**2 / 4

        x_min = -b / 2
        x_max =  b / 2
        y_min = -h / 2
        y_max =  h / 2

        c_corner = r + de + d_corner / 2
        c_edge = r + de + d_edge / 2

        x_izq_corner  = x_min + c_corner
        x_der_corner = x_max - c_corner
        y_bot_corner   = y_min + c_corner
        y_top_corner   = y_max - c_corner

        x_izq_edge  = x_min + c_edge
        x_der_edge = x_max - c_edge
        y_bot_edge   = y_min + c_edge
        y_top_edge   = y_max - c_edge

        barras = []

        # Barras de esquina
        barras.append([x_izq_corner,  y_bot_corner, Ab_corner])
        barras.append([x_der_corner, y_bot_corner, Ab_corner])
        barras.append([x_izq_corner,  y_top_corner, Ab_corner])
        barras.append([x_der_corner, y_top_corner, Ab_corner])

        # Barras intermedias en caras inferior y superior
        if nb_x > 2:
            xs = np.linspace(x_izq_corner, x_der_corner, nb_x)[1:-1]

            for x in xs:
                barras.append([x, y_bot_edge, Ab_edge])
                barras.append([x, y_top_edge, Ab_edge])

        # Barras intermedias en caras izquierda y derecha
        if nb_y > 2:
            ys = np.linspace(y_bot_corner, y_top_corner, nb_y)[1:-1]

            for y in ys:
                barras.append([x_izq_edge,  y, Ab_edge])
                barras.append([x_der_edge, y, Ab_edge])

        barras_2d = np.array(barras, dtype=float)
    
        # Retornar en formato [x_i, y_i, A_i]
        if not agrupar:
            return barras_2d

        # Agrupar al formato [coord_i, A_i]
        dic = {}
        
        for x_i, y_i, A_i in barras_2d:
            if eje == "x":
                coord = y_i
            else:
                coord = x_i

            dic[coord] = dic.get(coord, 0) + A_i

        As = np.array(sorted(dic.items(), reverse=True), dtype=float)

        return As

    @staticmethod
    def barras_viga(b, h, r, de, nb_sup, nb_inf, d_sup, d_inf, eje, agrupar):
        """
        Genera coordenadas y areas de barras individuales 2D y agrupadas
        para una viga rectangular.

        Parametros:
            h       : altura de la seccion
            r       : recubrimiento libre
            de      : diametro de estribos
            nb_sup  : numero de barras superiores
            nb_inf  : numero de barras inferiores
            d_sup   : diametro de barras superiores
            d_inf   : diametro de barras inferiores
            eje     : eje de analisis ("x" o "y")
            agrupar : permte agrupar fibras dependiendo del eje

        Retorna:
            Si agrupar=False:
                retorna barras_2d = array [x_s, y_s, A_s]

            Si agrupar=True:
                retorna As = array [coord_i, A_i]
        """

        eje = eje.lower()

        # Area de una barra
        Ab_sup = np.pi * d_sup**2 / 4
        Ab_inf = np.pi * d_inf**2 / 4     

        # Coordenadas verticales
        y_sup = h / 2 - (r + de + d_sup / 2)
        y_inf = -h / 2 + (r + de + d_inf / 2)

        # Coordenadas horizontales de barras superiores
        x_sup_min = -b / 2 + (r + de + d_sup / 2)
        x_sup_max =  b / 2 - (r + de + d_sup / 2)
        x_sup = np.linspace(x_sup_min, x_sup_max, nb_sup)

        # Coordenadas horizontales de barras inferiores
        x_inf_min = -b / 2 + (r + de + d_inf / 2)
        x_inf_max =  b / 2 - (r + de + d_inf / 2)
        x_inf = np.linspace(x_inf_min, x_inf_max, nb_inf)

        barras = []

        # Barras superiores
        for x in x_sup:
            barras.append([x, y_sup, Ab_sup])

        # Barras inferiores
        for x in x_inf:
            barras.append([x, y_inf, Ab_inf])

        barras_2d = np.array(barras, dtype=float)

        # Retornar en formato [x_i, y_i, A_i]
        if not agrupar:
            return barras_2d

        # Agrupar al formato [coord_i, A_i]
        dic = {}

        for x_i, y_i, A_i in barras_2d:

            if eje == "x":
                coord = y_i
            else:
                coord = x_i

            dic[coord] = dic.get(coord, 0) + A_i

        As = np.array(sorted(dic.items(), reverse=True), dtype=float)

        return As

    @staticmethod
    def malla(b, h, r, de, nf_x, nf_y, eje, barras_2d, conf, agrupar):
        """
        Discretiza la sección rectangular en fibras 2D de recubrimiento y núcleo
        y agrupa areas por coordenada del eje de análisis.

        Parámetros:
            b       : ancho de la seccion
            h       : altura de la seccion
            r       : recubrimiento libre
            de      : diámetro de estribos
            nf_x    : numero de divisiones base en x
            nf_y    : numero de divisiones base en y
            eje     : eje de análisis ("x" o "y")
            conf    : eleguir entre nucleo confinado o no
            agrupar : permte agrupar fibras dependiendo del eje

        Retorna:
            Si agrupar=False:
                retorna cover/core = array [x_i, y_i, A_i]

            Si agrupar=True:
                retorna cover/core = array [coord_i, A_i]

            Si conf=False:
                retorna cover

            Si conf=True:
                retorna cover y core
        """
        
        eje = eje.lower()

        tol_area = 1e-6
        buffer_resolution = 8

        # Geometria centrada
        x_min = -b / 2
        x_max =  b / 2
        y_min = -h / 2
        y_max =  h / 2

        rec_cl = r + de / 2.0

        x_core_min = x_min + rec_cl
        x_core_max = x_max - rec_cl
        y_core_min = y_min + rec_cl
        y_core_max = y_max - rec_cl

        # Malla base vectorizada
        x_edges = np.linspace(x_min, x_max, nf_x + 1)
        y_edges = np.linspace(y_min, y_max, nf_y + 1)

        x1 = x_edges[:-1]
        x2 = x_edges[1:]
        y1 = y_edges[:-1]
        y2 = y_edges[1:]

        X1, Y1 = np.meshgrid(x1, y1, indexing="ij")
        X2, Y2 = np.meshgrid(x2, y2, indexing="ij")

        X1 = X1.ravel()
        X2 = X2.ravel()
        Y1 = Y1.ravel()
        Y2 = Y2.ravel()

        A_cell = (X2 - X1) * (Y2 - Y1)
        Xc_cell = 0.5 * (X1 + X2)
        Yc_cell = 0.5 * (Y1 + Y2)

        # Interseccion analitica con el nucleo
        Xi1 = np.maximum(X1, x_core_min)
        Xi2 = np.minimum(X2, x_core_max)
        Yi1 = np.maximum(Y1, y_core_min)
        Yi2 = np.minimum(Y2, y_core_max)

        dx_core = np.maximum(0.0, Xi2 - Xi1)
        dy_core = np.maximum(0.0, Yi2 - Yi1)

        A_core = dx_core * dy_core

        if conf:
            mask_core = A_core > tol_area
        else:
            A_core = np.zeros_like(A_cell)
            mask_core = np.zeros_like(A_cell, dtype=bool)

        Xc_core = 0.5 * (Xi1 + Xi2)
        Yc_core = 0.5 * (Yi1 + Yi2)

        core_2d = np.column_stack((
            Xc_core[mask_core],
            Yc_core[mask_core],
            A_core[mask_core],
            Xi1[mask_core],
            Xi2[mask_core],
            Yi1[mask_core],
            Yi2[mask_core],
        ))

        # Cover equivalente por celda
        A_cover = A_cell - A_core
        mask_cover = A_cover > tol_area

        Qx_cover = A_cell * Xc_cell - A_core * Xc_core
        Qy_cover = A_cell * Yc_cell - A_core * Yc_core

        Xc_cover = np.zeros_like(A_cover)
        Yc_cover = np.zeros_like(A_cover)

        Xc_cover[mask_cover] = Qx_cover[mask_cover] / A_cover[mask_cover]
        Yc_cover[mask_cover] = Qy_cover[mask_cover] / A_cover[mask_cover]

        cover_2d = np.column_stack((
            Xc_cover[mask_cover],
            Yc_cover[mask_cover],
            A_cover[mask_cover],
            X1[mask_cover],
            X2[mask_cover],
            Y1[mask_cover],
            Y2[mask_cover],
        ))

        if cover_2d.size == 0:
            cover_2d = np.empty((0, 7), dtype=float)

        if core_2d.size == 0:
            core_2d = np.empty((0, 7), dtype=float)

        # Descontar barras longitudinales
        fibra_descuento = core_2d if conf else cover_2d

        if fibra_descuento.size > 0 and barras_2d is not None and len(barras_2d) > 0:

            # Precalcular cajas Shapely una sola vez
            fibra_boxes = [
                box(row[3], row[5], row[4], row[6])
                for row in fibra_descuento
            ]

            for xs, ys, As_barra in barras_2d:

                if As_barra <= 0.0:
                    continue

                rb = np.sqrt(As_barra / np.pi)

                try:
                    barra_geom = Point(xs, ys).buffer(
                        rb,
                        quad_segs=buffer_resolution
                    )
                except TypeError:
                    barra_geom = Point(xs, ys).buffer(
                        rb,
                        resolution=buffer_resolution
                    )

                idxs = np.where(
                    (fibra_descuento[:, 2] > tol_area) &
                    (fibra_descuento[:, 4] >= xs - rb) &
                    (fibra_descuento[:, 3] <= xs + rb) &
                    (fibra_descuento[:, 6] >= ys - rb) &
                    (fibra_descuento[:, 5] <= ys + rb)
                )[0]

                if len(idxs) == 0:
                    continue

                cortes = []

                for k in idxs:
                    inter = fibra_boxes[k].intersection(barra_geom)

                    if inter.is_empty:
                        continue

                    A_int = inter.area

                    if A_int <= tol_area:
                        continue

                    c_int = inter.centroid
                    cortes.append((k, c_int.x, c_int.y, A_int))

                if not cortes:
                    continue

                A_int_total = sum(c[3] for c in cortes)

                if A_int_total <= tol_area:
                    continue

                # Normalizar para descontar exactamente el area de la barra
                factor = As_barra / A_int_total

                for k, x_int, y_int, A_int in cortes:

                    Ac = fibra_descuento[k, 2]

                    if Ac <= tol_area:
                        continue

                    A_rem = A_int * factor
                    A_rem = min(A_rem, Ac)

                    if A_rem >= Ac - tol_area:
                        fibra_descuento[k, 2] = 0.0
                        continue

                    xc = fibra_descuento[k, 0]
                    yc = fibra_descuento[k, 1]

                    Ac_new = Ac - A_rem

                    fibra_descuento[k, 0] = (Ac * xc - A_rem * x_int) / Ac_new
                    fibra_descuento[k, 1] = (Ac * yc - A_rem * y_int) / Ac_new
                    fibra_descuento[k, 2] = Ac_new

        # Eliminar fibras nulas
        if cover_2d.size > 0:
            cover_2d = cover_2d[cover_2d[:, 2] > tol_area]

        if core_2d.size > 0:
            core_2d = core_2d[core_2d[:, 2] > tol_area]

        # Retorno 2D
        if not agrupar:
            return cover_2d[:, :3], core_2d[:, :3]

        # Agrupar por eje
        def agrupar_fibras(fibras_2d):
            if fibras_2d.size == 0:
                return np.empty((0, 2), dtype=float)

            if eje == "x":
                coords = fibras_2d[:, 1]
            elif eje == "y":
                coords = fibras_2d[:, 0]

            areas = fibras_2d[:, 2]

            coords_round = np.round(coords, 12)
            coord_unicos, inv = np.unique(coords_round, return_inverse=True)
            area_agrupada = np.bincount(inv, weights=areas)

            fibras = np.column_stack((coord_unicos, area_agrupada))
            fibras = fibras[np.argsort(fibras[:, 0])[::-1]]

            return fibras

        cover = agrupar_fibras(cover_2d)
        core = agrupar_fibras(core_2d)

        return cover, core