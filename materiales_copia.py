## esta hognestad con 0.20

import numpy as np
from scipy.optimize import root_scalar
from scipy.integrate import simpson

ecu_lim = 5e-2

class modelos:
    """
    Modelos constitutivos de materiales.

    Modelos disponibles:
        - bilineal: acero longitudinal y transversal
        - park: acero longitudinal y transversal
        - hognestad: hormigón no confinado
        - mander_u: hormigón no confinado
        - mander_c: hormigón confinado
        - buscar_ecu: deformación última del hormigón confinado por equilibrio energético
    """

    @staticmethod
    def bilineal(es, fy, fsu, Es, ey, esh, esu):
        """
        Modelo Bilineal para acero longitudinal o transversal.

        Parámetros:
            es  : deformación del acero
            fy  : esfuerzo de fluencia
            fsu : esfuerzo último
            Es  : módulo elástico del acero
            ey  : deformación de fluencia
            esh : deformación de inicio de endurecimiento
            esu : deformación última

        Retorna:
            fs : esfuerzo del acero
        """
        es = np.asarray(es, dtype=float)
        fs = np.zeros_like(es, dtype=float)
        abs_es = np.abs(es)
        sign = np.sign(es)

        # 1. Rama elástica lineal
        z1 = abs_es <= ey
        fs[z1] = Es * es[z1]

        # 2. Rama perfectamente plástica (hasta la rotura: esu)
        z2 = (abs_es > ey) & (abs_es <= esu)
        fs[z2] = fy * sign[z2]

        return fs

    @staticmethod
    def park(es, fy, fsu, Es, ey, esh, esu, N=None):
        """
        Modelo de Park para acero longitudinal o transversal.

        Parámetros:
            es  : deformacion del acero
            fy  : esfuerzo de fluencia
            fsu : esfuerzo ultimo
            Es  : módulo elástico del acero
            ey  : deformación de fluencia
            esh : deformación de inicio de endurecimiento
            esu : deformación ultima

        Retorna:
            fs : esfuerzo del acero
            Et : modulo tangente del acero
        """
        es = np.asarray(es, dtype=float)
        fs = np.zeros_like(es, dtype=float)
        Et = np.zeros_like(es, dtype=float)

        abs_es = np.abs(es)
        sign = np.sign(es)

        # 1. Rama elastica
        z1 = (abs_es <= ey)

        fs[z1] = Es * es[z1]
        Et[z1] = Es

        # 2. Meseta plastica
        z2 = (abs_es > ey) & (abs_es <= esh)

        fs[z2] = fy * sign[z2]
        Et[z2] = 0.0

        # 3. Endurecimiento por deformación Park
        z3 = (abs_es > esh) & (abs_es <= esu)

        delta_e = abs_es[z3] - esh
        r = esu - esh
        m = ((fsu / fy) * (30 * r + 1)**2 - 60 * r - 1) / (15 * r**2)

        parte1 = (m * delta_e + 2) / (60 * delta_e + 2)
        parte2 = delta_e * (60 - m) / (2 * (30 * r + 1)**2)

        fs[z3] = fy * sign[z3] * (parte1 + parte2)

        # Modulo tangente del tramo Park
        d_parte1 = (2 * m - 120) / (60 * delta_e + 2)**2
        d_parte2 = (60 - m) / (2 * (30 * r + 1)**2)

        Et[z3] = fy * (d_parte1 + d_parte2)

        return fs, Et

    @staticmethod
    def hognestad(ec, fc0, ec0, esp, Ec, datos_h=None, N=None):
        """
        Modelo de Hognestad para hormigón no confinado.

        Parámetros:
            ec      : deformacion del hormigon
            fc0     : resistencia máxima a compresion
            ec0     : deformacion en fc0
            esp     : deformacion ultima
            datos_h : datos adicionales mander confinado
            N       : salida preferente mander confinado
        Retorna:
            fc : esfuerzo del hormigon
            Et : modulo tangente del hormigon 
        """
        ec = np.asarray(ec, dtype=float)
        fc = np.zeros_like(ec, dtype=float)
        Et = np.zeros_like(ec, dtype=float)

        # 1. Rama ascendente parabólica
        z1 = (ec <= 0) & (ec >= -ec0)
        
        fc[z1] = -fc0 * (2 * (-ec[z1] / ec0) - (ec[z1] / ec0)**2)
        Et[z1] = 2 * fc0 / ec0 * (1 + ec[z1] / ec0)
        
        # 2. Rama descendente lineal
        z2 = (ec < -ec0) & (ec >= -esp)
        
        fc[z2] = -fc0 * (1 - 0.20 * (-ec[z2] - ec0) / (esp - ec0))
        Et[z2] = - 0.20 * fc0 / (esp - ec0)
        
        return fc, Et

    @staticmethod
    def mander_u(ec, fc0, ec0, esp, Ec, datos_h=None, N=None):
        """
        Modelo de Mander para hormigón no confinado.

        Parámetros:
            ec      : deformacion del hormigon
            fc0     : resistencia máxima a compresión
            ec0     : deformación en fc0
            esp     : deformación última
            Ec      : módulo de elasticidad del hormigon
            datos_h : datos adicionales mander confinado
            N       : salida preferente mander confinado

        Retorna:
            fc : esfuerzo del hormigon
            Et : modulo tangente del hormigon
        """
        ec = np.asarray(ec, dtype=float)
        fc = np.zeros_like(ec, dtype=float)
        Et = np.zeros_like(ec, dtype=float)

        Esec = fc0 / ec0
        r = Ec / (Ec - Esec)

        # 1. Rama ascendente curva
        z1 = (ec <= 0) & (ec >= -2*ec0)
        x = -ec[z1] / ec0

        fc[z1] = -fc0 * (x * r) / (r - 1 + x**r)
        Et[z1] = (fc0 / ec0) * (r * (r - 1) * (1 - x**r) / ((r - 1 + x**r)**2))

        # 2. Rama descendente lineal
        z2 = (ec < -2*ec0) & (ec >= -esp)
        fc2 = fc0 * (2 * r) / (r - 1 + 2**r)
        
        fc[z2] = -fc2 * (esp + ec[z2]) / (esp - 2*ec0)
        Et[z2] = -fc2 / (esp - 2*ec0)

        return fc, Et

    @staticmethod
    def mander_c(ec, fc0, ec0, esp, Ec, datos_h=None, N=None):
        """
        Modelo de Mander para hormigón confinado.

        Parámetros:
            ec      : deformación del hormigón
            fc0     : resistencia máxima a compresión del hormigón no confinado
            ec0     : deformación en fc0
            esp     : deformación última del hormigón no confinado
            Ec      : módulo de elasticidad del hormigón
            datos_h : tupla con:
                      (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nr_x, nr_y, ecu, fcc)
            N       : selector de salida

        Retorna:
            según N
                N = 1 o None
                    fc  : esfuerzo del hormigon
                    Et  : modulo tangente del hormigon
                N = 2
                    fc  : esfuerzo del hormigon (signo invertdo)
                    psh : cuantia de acero transversal
                    Acc : area confinada
                    pcc : cuantia del acero longitudinal
                N = 3
                    fcc : esfuerzo del hormigon confinado
        """
        fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nr_x, nr_y, ecu, fcc = datos_h

        def fcc_mander(flx, fly, fc0):
            """
            Calcula fcc según superficie de falla de Mander para confinamiento biaxial.

            flx, fly : presion lateral efectiva
            fc0      : resistencia no confinada
            
            """
            fl1 = min(flx, fly)
            fl2 = max(flx, fly)

            r = fl1 / fl2
            x_med = (fl1 + fl2) / (2 * fc0)
            
            A = 6.8886 - (0.6069 + 17.275 * r) * np.exp(-4.989 * r)
            B = 4.5 / ((5 / A) * (0.9849 - 0.6306 * np.exp(-3.8939 * r)) - 0.1) - 5
            fcc = fc0 * (1 + A * x_med * (0.1 + 0.9 / (1 + B * x_med)))
            
            return fcc

        # Dimensiones del núcleo al eje del estribo
        dc = h - 2 * r - de
        bc = b - 2 * r - de
        Ss = Sc - de

        # Área inefectiva
        Wx = (bc - de - 2 * d_corner - (nr_y - 2) * d_edge) / (nr_y - 1)
        Wy = (dc - de - 2 * d_corner - (nr_x - 2) * d_edge) / (nr_x - 1)

        Ainef = (2 * (nr_y - 1) * (Wx**2) / 6) + (2 * (nr_x - 1) * Wy**2 / 6)

        # Area efectiva confinada
        Ac = bc * dc
        Ae = (Ac - Ainef) * (1 - Ss / (2 * bc)) * (1 - Ss / (2 * dc))

        # Cuantia longitudinal
        Ab_corner = np.pi * d_corner**2 / 4
        Ab_edge = np.pi * d_edge**2 / 4

        AsL = 4 * Ab_corner + (nb - 4) * Ab_edge
        Acc = Ac - AsL
        pcc = AsL / Acc

        # Coeficiente de confinamiento efectivo
        Ke = Ae / Acc

        # Presion lateral de confinamiento
        Ash = np.pi * de**2 / 4
        Ashx = nr_x * Ash
        Ashy = nr_y * Ash

        pshx = (Ashx * bc) / (Sc * bc * dc)
        pshy = (Ashy * dc) / (Sc * bc * dc)

        fLx_eff = Ke * pshx * fyh
        fLy_eff = Ke * pshy * fyh

        # Resistencia confinada
        if fcc is None:
            fcc = fcc_mander(fLx_eff, fLy_eff, fc0)

        if N == 3:
            return fcc

        # Deformacion en resistencia maxima confinada
        ecc = ec0 * (1 + 5 * (fcc / fc0 - 1))
        Esec = fcc / ecc
        r = Ec / (Ec - Esec)

        # Cuantia volumetrica de estribos
        psh = pshx + pshy

        # Convencion: compresión negativa en entrada
        ec = np.asarray(ec, dtype=float)
        fc = np.zeros_like(ec, dtype=float)
        Et = np.zeros_like(ec, dtype=float)

        z1 = (ec <= 0) & (ec >= -ecu)
        x = -ec[z1] / ecc

        fc[z1] = -fcc * (x * r) / (r - 1 + x**r)
        Et[z1] = (fcc / ecc) * (r * (r - 1) * (1 - x**r) / ((r - 1 + x**r)**2)) 
                
        if N == 2:
            return -fc, psh, Acc, pcc

        return fc, Et

    @staticmethod
    def buscar_ecu(fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, datos_h):
        """
        Busca la deformacion ultima del hormigon confinado ecu mediante equilibrio energetico.

        Parametros:
            fc0, ec0, esp, Ec : parametros del hormigon
            fy, fsu, Es, ey, esh, esu : parametros del acero transversal/longitudinal
            datos_h : tupla de datos para mander_c:
                      (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nr_x, nr_y, ecu, fcc)

        Retorna:
            ecu : deformacion ultima del hormigon confinado
        """
        n = 101
        # Hormigon no confinado
        ec_uc = np.empty(n)
        ec_uc = np.linspace(-2 * ec0, 0.0, n-1)
        ec_uc = np.concatenate((ec_uc, [-esp]))
        ec_uc.sort()

        fc_uc = modelos.mander_u(ec_uc, fc0, ec0, esp, Ec, datos_h, 0)[0]
        A_uc = -simpson(fc_uc, x=ec_uc)

        # Acero transversal
        es_sh = np.linspace(0.0, esu, n-2)
        es_sh = np.concatenate((es_sh, [esh, ey]))
        es_sh.sort()
        fs_sh = modelos.park(es_sh, fy, fsu, Es, ey, esh, esu)[0]
        A_sh = simpson(fs_sh, x=es_sh)

        fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nr_x, nr_y, _, fcc = datos_h

        def f(ecu):
            datos_h_ecu = (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nr_x, nr_y, ecu, fcc)

            # Hormigon confinado hasta ecu
            ec_cc = np.linspace(-ecu, 0.0, n)
            fc_cc, psh, Acc, pcc = modelos.mander_c(ec_cc, fc0, ec0, esp, Ec, datos_h_ecu, 2)
            A_cc = simpson(fc_cc, x=ec_cc)

            # Balance de energia: Ucc - Uco - Ush
            Ush = Acc * psh * A_sh
            Uco = Acc * A_uc
            Ucc = Acc * A_cc
            
            E = Ush - (Ucc - Uco)
            return E
          
        try:
            sol = root_scalar(f, bracket=[1e-3, ecu_lim], method="brentq")
            return sol.root
        except ValueError:
            return ecu_lim
