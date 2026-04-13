import numpy as np

class utilidades:
    """
    Utilidades geométricas de secciones de concreto reforzado.

    Métodos disponibles:
        - barras_columna: coordenadas y áreas de barras en columnas
        - barras_viga: coordenadas y áreas de barras en vigas
        - malla: discretización de la sección en fibras
    """

    @staticmethod
    def barras_columna(b, h, r, de, nb_x, nb_y, d_corner, d_edge, eje):
        """
        Coordenadas y áreas de barras de acero en una columna.

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
            As : arreglo de dos columnas [coord_i, A_i]
                 coord_i = coordenada de cada capa de acero
                 A_i     = área total de acero en esa capa
        """

        eje = eje.lower()
        
        # Área de una barra
        Ab_corner = np.pi * d_corner**2 / 4
        Ab_edge = np.pi * d_edge**2 / 4

        # Si se analiza respecto al eje x, las capas se ubican en y
        # Si se analiza respecto al eje y, las capas se ubican en x
        dim = h if eje == "x" else b
        n_dir = nb_y if eje == "x" else nb_x
        n_perp = nb_x if eje == "x" else nb_y

        c_corner = r + de + d_corner / 2
        c_edge = r + de + d_edge / 2

        # Coordenadas extremas e intermedias
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

        # Coordenadas centradas en la sección
        coord_i = dim / 2 - coord

        As = np.column_stack((coord_i, A_i))
        
        return As

    @staticmethod
    def barras_viga(h, r, de, nb_sup, nb_inf, d_sup, d_inf):
        """
        Coordenadas y áreas de barras de acero en una viga.

        Parámetros:
            h      : altura de la sección
            r      : recubrimiento libre
            de     : diámetro de estribos
            nb_sup : número de barras superiores
            nb_inf : número de barras inferiores
            d_sup  : diámetro de barras superiores
            d_inf  : diámetro de barras inferiores

        Retorna:
            As : arreglo de dos columnas [y_i, A_i]
                 y_i = coordenada vertical de cada capa
                 A_i = área total de acero en esa capa
        """
        # Coordenadas de las capas medidas desde el centro de la sección
        y_sup = h / 2 - (r + de + d_sup / 2)
        y_inf = -h / 2 + (r + de + d_inf / 2)

        # Área de una barra
        Ab_sup = np.pi * d_sup**2 / 4
        Ab_inf = np.pi * d_inf**2 / 4

        # Área total por capa
        A_sup = nb_sup * Ab_sup
        A_inf = nb_inf * Ab_inf

        y_i = np.array([y_sup, y_inf], dtype=float)
        A_i = np.array([A_sup, A_inf], dtype=float)

        As = np.column_stack((y_i, A_i))

        return As


    @staticmethod
    def malla(b, h, r, de, nf_x, nf_y, eje):
        """
        Discretiza la sección rectangular en fibras 2D de recubrimiento y núcleo
        y agrupa áreas por coordenada del eje de análisis.

        Parámetros:
            b   : ancho de la sección
            h   : altura de la sección
            r   : recubrimiento libre
            de  : diámetro de estribos
            nf_x  : número de divisiones base en x
            nf_y  : número de divisiones base en y
            eje : eje de análisis ("x" o "y")

        Retorna:
            cover : arreglo [coord_i, A_i] de fibras del recubrimiento
            core  : arreglo [coord_i, A_i] de fibras del núcleo
        """
        
        eje = eje.lower()

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

                es_core = (x1 >= rec) and (x2 <= b - rec) and (y1 >= rec) and (y2 <= h - rec)

                dic = core_dict if es_core else cover_dict
                dic[coord_i] = dic.get(coord_i, 0.0) + area

        cover = np.array(sorted(cover_dict.items(), reverse=True), dtype=float)
        core = np.array(sorted(core_dict.items(), reverse=True), dtype=float)

        return cover, core