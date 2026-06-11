import numpy as np


class utilidades:
    """
    Utilidades geometricas de secciones de concreto reforzado.

    Metodos disponibles:
        - barras_columna: coordenadas y areas de barras en columnas
        - barras_viga: coordenadas y areas de barras en vigas
        - malla: discretizacion de la seccion en fibras
    """

    @staticmethod
    def barras_columna(b, h, r, de, nb_x, nb_y, d_corner, d_edge, eje, agrupado=True):
        eje = str(eje).lower()
        nb_x = int(nb_x)
        nb_y = int(nb_y)

        Ab_corner = np.pi * d_corner**2 / 4
        Ab_edge = np.pi * d_edge**2 / 4

        if not agrupado:
            x0 = -0.5 * b
            y0 = -0.5 * h

            x_start_corner = x0 + r + de + d_corner / 2
            x_end_corner = x0 + b - r - de - d_corner / 2
            y_start_corner = y0 + r + de + d_corner / 2
            y_end_corner = y0 + h - r - de - d_corner / 2

            x_start_edge = x0 + r + de + d_edge / 2
            x_end_edge = x0 + b - r - de - d_edge / 2
            y_start_edge = y0 + r + de + d_edge / 2
            y_end_edge = y0 + h - r - de - d_edge / 2

            barras = []

            # Esquinas
            barras.append([x_start_corner, y_start_corner, Ab_corner])
            barras.append([x_end_corner, y_start_corner, Ab_corner])
            barras.append([x_end_corner, y_end_corner, Ab_corner])
            barras.append([x_start_corner, y_end_corner, Ab_corner])

            # Barras intermedias en caras inferior y superior
            if nb_x > 2:
                xs_edge = np.linspace(x_start_corner, x_end_corner, nb_x)[1:-1]
                for x in xs_edge:
                    barras.append([x, y_start_edge, Ab_edge])
                    barras.append([x, y_end_edge, Ab_edge])

            # Barras intermedias en caras izquierda y derecha
            if nb_y > 2:
                ys_edge = np.linspace(y_start_corner, y_end_corner, nb_y)[1:-1]
                for y in ys_edge:
                    barras.append([x_start_edge, y, Ab_edge])
                    barras.append([x_end_edge, y, Ab_edge])

            return np.array(barras, dtype=float)

        dim = h if eje == "x" else b
        n_dir = nb_y if eje == "x" else nb_x
        n_perp = nb_x if eje == "x" else nb_y

        c_corner = r + de + d_corner / 2
        c_edge = r + de + d_edge / 2

        c1_corner = c_corner
        c2_corner = dim - c_corner
        c1_edge = c_edge
        c2_edge = dim - c_edge

        if n_dir == 2:
            coord = np.array([c1_corner, c2_corner], dtype=float)
            A_i = np.array([2 * Ab_corner, 2 * Ab_corner], dtype=float)
        else:
            c_mid = np.linspace(c1_corner, c2_corner, n_dir)[1:-1]

            coord = np.concatenate((
                [c1_corner],
                [c1_edge],
                c_mid,
                [c2_edge],
                [c2_corner]
            ))

            nbarras = np.full(n_dir + 2, 2, dtype=float)
            nbarras[1] = n_perp - 2
            nbarras[-2] = n_perp - 2

            A_i = nbarras * Ab_edge
            A_i[0] = 2 * Ab_corner
            A_i[-1] = 2 * Ab_corner

        coord_i = dim / 2 - coord
        return np.column_stack((coord_i, A_i))

    @staticmethod
    def barras_viga(*args):
        if len(args) == 7:
            h, r, de, nb_sup, nb_inf, d_sup, d_inf = args
            b = None
            agrupado = True
        elif len(args) == 10:
            b, h, r, de, nb_sup, nb_inf, d_sup, d_inf, eje, agrupado = args
        else:
            raise TypeError("barras_viga espera 7 argumentos para calculo o 10 para grafico")

        nb_sup = int(nb_sup)
        nb_inf = int(nb_inf)

        if not agrupado:
            Ab_sup = np.pi * d_sup**2 / 4
            Ab_inf = np.pi * d_inf**2 / 4

            x_min = -b / 2
            x_max = b / 2

            y_sup = h / 2 - (r + de + d_sup / 2)
            y_inf = -h / 2 + (r + de + d_inf / 2)

            xs_sup = np.linspace(
                x_min + r + de + d_sup / 2,
                x_max - r - de - d_sup / 2,
                nb_sup
            )

            xs_inf = np.linspace(
                x_min + r + de + d_inf / 2,
                x_max - r - de - d_inf / 2,
                nb_inf
            )

            barras = []

            for x in xs_sup:
                barras.append([x, y_sup, Ab_sup])

            for x in xs_inf:
                barras.append([x, y_inf, Ab_inf])

            return np.array(barras, dtype=float)

        y_sup = h / 2 - (r + de + d_sup / 2)
        y_inf = -h / 2 + (r + de + d_inf / 2)

        Ab_sup = np.pi * d_sup**2 / 4
        Ab_inf = np.pi * d_inf**2 / 4

        A_sup = nb_sup * Ab_sup
        A_inf = nb_inf * Ab_inf

        y_i = np.array([y_sup, y_inf], dtype=float)
        A_i = np.array([A_sup, A_inf], dtype=float)

        return np.column_stack((y_i, A_i))

    @staticmethod
    def malla(b, h, r, de, nf_x, nf_y, eje, barras_2d=None, confinado=True, agrupado=True):
        eje = str(eje).lower()
        nf_x = int(nf_x)
        nf_y = int(nf_y)

        if not agrupado:
            rec = r + de / 2

            x_min = -b / 2
            x_max = b / 2
            y_min = -h / 2
            y_max = h / 2

            x_edges = np.linspace(x_min, x_max, nf_x + 1)
            y_edges = np.linspace(y_min, y_max, nf_y + 1)

            if confinado:
                x_edges = np.unique(np.concatenate((x_edges, [x_min + rec, x_max - rec])))
                y_edges = np.unique(np.concatenate((y_edges, [y_min + rec, y_max - rec])))

            cover = []
            core = []

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

                    area = dx * dy

                    es_core = (
                        confinado
                        and x1 >= x_min + rec
                        and x2 <= x_max - rec
                        and y1 >= y_min + rec
                        and y2 <= y_max - rec
                    )

                    if es_core:
                        core.append([xc, yc, area])
                    else:
                        cover.append([xc, yc, area])

            return np.array(cover, dtype=float), np.array(core, dtype=float)

        rec = r + de / 2

        x_edges = np.linspace(0.0, b, nf_x + 1)
        y_edges = np.linspace(0.0, h, nf_y + 1)

        add_x = []
        add_y = []

        if 0.0 < rec < b:
            add_x.extend([rec, b - rec])
        if 0.0 < rec < h:
            add_y.extend([rec, h - rec])

        if add_x:
            x_edges = np.unique(np.concatenate((x_edges, np.array(add_x))))
        if add_y:
            y_edges = np.unique(np.concatenate((y_edges, np.array(add_y))))

        cover_dict = {}
        core_dict = {}

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

                area = dx * dy

                if eje == "x":
                    coord_i = h / 2 - yc
                else:
                    coord_i = xc - b / 2

                es_core = (
                    x1 >= rec
                    and x2 <= b - rec
                    and y1 >= rec
                    and y2 <= h - rec
                )

                dic = core_dict if es_core else cover_dict
                dic[coord_i] = dic.get(coord_i, 0.0) + area

        cover = np.array(sorted(cover_dict.items(), reverse=True), dtype=float)
        core = np.array(sorted(core_dict.items(), reverse=True), dtype=float)

        return cover, core