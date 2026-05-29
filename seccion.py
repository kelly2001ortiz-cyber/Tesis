import numpy as np
from shapely.geometry import Point, box

class utilidades:
    """
    Utilidades geométricas de secciones de concreto reforzado.

    Métodos disponibles:
        - barras_columna: coordenadas y áreas de barras en columnas
        - barras_viga: coordenadas y áreas de barras en vigas
        - malla: discretización de la sección en fibras

    Coordenadas:
        x = 0 en el centro de la seccion
        y = 0 en el centro de la seccion
        x positivo hacia la derecha
        y positivo hacia arriba

    """

    @staticmethod
    def barras_columna(b, h, r, de, nb_x, nb_y, d_corner, d_edge, eje, agrupar):
        """
        Genera coordenadas y áreas de barras individuales 2D y agrupadas
        para una columna rectangular.

        Parámetros:
            b        : ancho de la sección
            h        : altura de la sección
            r        : recubrimiento libre
            de       : diámetro de estribos
            nb_x      : número de barras en dirección x
            nb_y      : número de barras en dirección y
            d_corner : diámetro de barras de esquina
            d_edge   : diámetro de barras laterales
            eje      : eje de análisis ("x" o "y")

        Retorna:
            Si agrupar=False:
                retorna barras_2d = array [x_i, y_i, A_i]

            Si agrupar=True:
                retorna As = array [coord_i, A_i]

        """
        eje = eje.lower()
        
        # Área de una barra
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
            xs = np.linspace(x_izq_edge, x_der_edge, nb_x)[1:-1]

            for x in xs:
                barras.append([x, y_bot_edge, Ab_edge])
                barras.append([x, y_top_edge, Ab_edge])

        # Barras intermedias en caras izquierda y derecha
        if nb_y > 2:
            ys = np.linspace(y_bot_edge, y_top_edge, nb_y)[1:-1]

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
        Genera coordenadas y áreas de barras individuales 2D y agrupadas
        para una viga rectangular.

        Parámetros:
            h      : altura de la sección
            r      : recubrimiento libre
            de     : diámetro de estribos
            nb_sup : número de barras superiores
            nb_inf : número de barras inferiores
            d_sup  : diámetro de barras superiores
            d_inf  : diámetro de barras inferiores
            eje      : eje de análisis ("x" o "y")

        Retorna:
            Si agrupar=False:
                retorna barras_2d = array [x_s, y_s, A_s]

            Si agrupar=True:
                retorna As = array [coord_i, A_i]

        """
        eje = eje.lower()

        # Área de una barra
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
    def malla(b, h, r, de, nf_x, nf_y, eje, barras_2d, agrupar):
        """
        Discretiza la sección rectangular en fibras 2D de recubrimiento y núcleo
        y agrupa áreas por coordenada del eje de análisis.

        Parámetros:
            b    : ancho de la sección
            h    : altura de la sección
            r    : recubrimiento libre
            de   : diámetro de estribos
            nf_x : número de divisiones base en x
            nf_y : número de divisiones base en y
            eje  : eje de análisis ("x" o "y")

        Coordenadas:
            x = 0 en el centro de la seccion, positivo hacia la derecha
            y = 0 en el centro de la seccion, positivo hacia arriba

        Retorna:
            Si agrupar=True:
                cover, core : arrays [coord_i, A_i]

            Si agrupar=False:
                cover_2d, core_2d : arrays [x_i, y_i, A_i]

        """
        buffer_resolution=32
        tol_area=1e-6

        eje = eje.lower()

        # Geometria centrada
        rec = r + de / 2

        x_min = -b / 2
        x_max =  b / 2
        y_min = -h / 2
        y_max =  h / 2

        x_core_min = x_min + rec
        x_core_max = x_max - rec
        y_core_min = y_min + rec
        y_core_max = y_max - rec

        # Bordes de malla
        x_edges = np.linspace(x_min, x_max, nf_x + 1)
        y_edges = np.linspace(y_min, y_max, nf_y + 1)

        x_edges = np.unique(np.concatenate((x_edges, [x_core_min, x_core_max])))
        y_edges = np.unique(np.concatenate((y_edges, [y_core_min, y_core_max])))

        # Crear fibras 2D : [x_c, y_c, A, x1, x2, y1, y2]
        cover_list = []
        core_list = []

        for i in range(len(x_edges) - 1):
            x1 = x_edges[i]
            x2 = x_edges[i + 1]
            xc = 0.5 * (x1 + x2)
            dx = x2 - x1

            for j in range(len(y_edges) - 1):
                y1 = y_edges[j]
                y2 = y_edges[j + 1]
                yc = 0.5 * (y1 + y2)
                dy = y2 - y1

                A = dx * dy

                es_core = (
                    x1 >= x_core_min and x2 <= x_core_max and
                    y1 >= y_core_min and y2 <= y_core_max
                )

                fibra = [xc, yc, A, x1, x2, y1, y2]

                if es_core:
                    core_list.append(fibra)
                else:
                    cover_list.append(fibra)

        cover_2d = np.array(cover_list, dtype=float)
        core_2d = np.array(core_list, dtype=float)

        # Geometrias de fibras del nucleo
        core_boxes = [
            box(row[3], row[5], row[4], row[6])
            for row in core_2d
        ]

        # Descontar barras del nucleo
        for xs, ys, As_barra in barras_2d:

            rb = np.sqrt(As_barra / np.pi)

            try:
                barra_geom = Point(xs, ys).buffer(rb, quad_segs=buffer_resolution)
            except TypeError:
                barra_geom = Point(xs, ys).buffer(rb, resolution=buffer_resolution)

            # Fibras candidatas por caja envolvente
            idxs = np.where(
                (core_2d[:, 4] >= xs - rb) &
                (core_2d[:, 3] <= xs + rb) &
                (core_2d[:, 6] >= ys - rb) &
                (core_2d[:, 5] <= ys + rb)
            )[0]

            candidatos = []

            for k in idxs:
                inter = core_boxes[k].intersection(barra_geom)

                if inter.is_empty:
                    continue

                A_rem = inter.area

                if A_rem <= tol_area:
                    continue

                c_rem = inter.centroid
                candidatos.append((k, c_rem.x, c_rem.y, A_rem))

            A_total_rem = sum(c[3] for c in candidatos)

            # Normalizar para que el area total descontada sea igual a As_barra
            factor = As_barra / A_total_rem

            for k, x_rem, y_rem, A_rem in candidatos:
                A_rem *= factor

                xc = core_2d[k, 0]
                yc = core_2d[k, 1]
                Ac = core_2d[k, 2]

                if A_rem >= Ac - tol_area:
                    core_2d[k, 2] = 0
                    continue
                
                Ac_new = Ac - A_rem
                xc_new = (Ac * xc - A_rem * x_rem) / Ac_new
                yc_new = (Ac * yc - A_rem * y_rem) / Ac_new

                core_2d[k, 0] = xc_new
                core_2d[k, 1] = yc_new
                core_2d[k, 2] = Ac_new

        # Eliminar fibras nulas
        cover_2d = cover_2d[cover_2d[:, 2] > tol_area]
        core_2d = core_2d[core_2d[:, 2] > tol_area]

        # Retornar fibras 2D
        if not agrupar:
            return cover_2d[:, :3], core_2d[:, :3]

        # Agrupar al formato [coord_i, A_i]
        def agrupar_fibras(fibras_2d):
            dic = {}

            for x_i, y_i, A_i in fibras_2d[:, :3]:

                if eje == "x":
                    coord = y_i
                else:
                    coord = x_i

                dic[coord] = dic.get(coord, 0) + A_i

            return np.array(sorted(dic.items(), reverse=True), dtype=float)

        cover = agrupar_fibras(cover_2d)
        core = agrupar_fibras(core_2d)

        return cover, core