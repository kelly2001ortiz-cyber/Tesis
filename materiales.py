import numpy as np
from scipy.optimize import brentq
from scipy.integrate import simpson

class modelos:
    """
    Modelos constitutivos de materiales.

    Modelos disponibles:
        - park: acero longitudinal y transversal
        - hognestad: hormigón no confinado
        - mander_u: hormigón no confinado
        - mander_c: hormigón confinado
        - buscar_ecu: deformación última del hormigón confinado por equilibrio energético
    """

    @staticmethod
    def park(es, fy, fsu, Es, ey, esh, esu):
        """
        Modelo de Park para acero longitudinal o transversal.

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

        # Rama elástica lineal
        z1 = abs_es <= ey
        fs[z1] = Es * es[z1]

        # Rama perfectamente plástica
        z2 = (abs_es > ey) & (abs_es <= esh)
        fs[z2] = fy * sign[z2]

        # Rama de endurecimiento por deformación
        z3 = (abs_es > esh) & (abs_es <= esu)
        delta_e = abs_es[z3] - esh
        r = esu - esh
        m = ((fsu / fy) * (30 * r + 1) ** 2 - 60 * r - 1) / (15 * r ** 2)
        parte1 = (m * delta_e + 2) / (60 * delta_e + 2)
        parte2 = delta_e * (60 - m) / (2 * (30 * r + 1) ** 2)
        fs[z3] = sign[z3] * fy * (parte1 + parte2)

        return fs

    @staticmethod
    def hognestad(ec, fc0, ec0, esp):
        """
        Modelo de Hognestad para hormigón no confinado.

        Parámetros:
            ec  : deformación del hormigón
            fc0 : resistencia máxima a compresión
            ec0 : deformación en fc0
            esp : deformación última

        Retorna:
            fc : esfuerzo del hormigón
        """
        ec = np.asarray(ec, dtype=float)
        fc = np.zeros_like(ec, dtype=float)

        # Rama ascendente parabólica
        z1 = (ec <= 0) & (ec >= -ec0)
        fc[z1] = fc0 * (2 * (-ec[z1] / ec0) - (ec[z1] / ec0) ** 2)

        # Rama descendente lineal
        z2 = (ec < -ec0) & (ec >= -esp)
        fc[z2] = fc0 * (1 - 0.15 * (-ec[z2] - ec0) / (esp - ec0))

        return -fc

    @staticmethod
    def mander_u(ec, fc0, ec0, esp, Ec, datos_h=None, N=None):
        """
        Modelo de Mander para hormigón no confinado.

        Parámetros:
            ec      : deformación del hormigón
            fc0     : resistencia máxima a compresión
            ec0     : deformación en fc0
            esp     : deformación última
            Ec      : módulo de elasticidad del hormigón
            datos_h : datos adicionales mander confinado
            N       : salida preferente mander confinado

        Retorna:
            fc : esfuerzo del hormigón
        """
        ec = np.asarray(ec, dtype=float)
        fc = np.zeros_like(ec, dtype=float)

        ec00 = 2 * ec0

        # Módulo secante y parámetro r
        Esec = fc0 / ec0
        r = Ec / (Ec - Esec)

        # Rama ascendente curva
        z1 = (ec <= 0) & (ec >= -ec00)
        x = ec[z1] / -ec0
        fc[z1] = fc0 * (x * r) / (r - 1 + x ** r)

        # Rama descendente lineal
        z2 = (ec >= -esp) & (ec < -ec00)
        fc[z2] = fc0 * (2 * r) / (r - 1 + 2 ** r) * (esp + ec[z2]) / (esp - ec00)

        return -fc

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
                      (fyh, b, h, r, Sc, de, d_corner, d_edge, Nb, NLx, NLy, ecu, fcc)
            N       : selector de salida
                      N = 1 o None -> esfuerzo del hormigón
                      N = 2        -> retorna fc, psh, Acc, pcc
                      N = 3        -> retorna solo fcc

        Retorna:
            según N
        """

        fyh, b, h, r, Sc, de, d_corner, d_edge, Nb, NLx, NLy, ecu, fcc = datos_h

        def fccfco(flx, fly, fc0):
            sigma1 = -min(flx, fly)
            sigma2 = -max(flx, fly)

            def f(sigma3):
                sigma_oct = (sigma1 + sigma2 + sigma3) / 3
                tau_oct_i = (((sigma1 - sigma2) ** 2 + (sigma2 - sigma3) ** 2 + (sigma3 - sigma1) ** 2) ** 0.5 ) / 3

                cos_theta = (sigma1 - sigma_oct) / (2 ** 0.5 * tau_oct_i)
                cos_theta = np.clip(cos_theta, -1, 1)

                sigmap_oct = sigma_oct / fc0

                T = 0.069232 - 0.661091 * sigmap_oct - 0.049350 * sigmap_oct ** 2
                C = 0.122965 - 1.150502 * sigmap_oct - 0.315545 * sigmap_oct ** 2
                D = 4 * (C ** 2 - T ** 2) * cos_theta ** 2
                tau_oct_j = fc0 * C * (D / (2 * cos_theta) + (2 * T - C) * (D + 5 * T**2 - 4 * T * C)**0.5) / (D + (2 * T - C)**2)

                return tau_oct_i - tau_oct_j

            return -brentq(f, -3*fc0, -fc0)

        # Dimensiones del núcleo
        dc = h - 2 * r - de
        bc = b - 2 * r - de
        Ss = Sc - de

        # Área inefectiva
        Wx = (bc - de - 2 * d_corner - (NLx - 2) * d_edge) / (NLx - 1)
        Wy = (dc - de - 2 * d_corner - (NLy - 2) * d_edge) / (NLy - 1)

        Ainef = (2 * (NLx - 1) * (Wx ** 2) / 6) + (2 * (NLy - 1) * Wy ** 2 / 6)

        # Área efectiva confinada
        Ae = (bc * dc - Ainef) * (1 - Ss / (2 * bc)) * (1 - Ss / (2 * dc))

        # Cuantía longitudinal
        AsL = np.pi * (d_corner ** 2 + (Nb - 4) * d_edge ** 2 / 4)
        Ac = bc * dc
        pcc = AsL / Ac
        Acc = Ac * (1 - pcc)

        # Coeficiente de confinamiento efectivo
        Ke = Ae / Acc

        # Presión lateral de confinamiento
        Ash = np.pi * de ** 2 / 4
        Ashx = NLx * Ash
        Ashy = NLy * Ash

        psx = (Ashx * bc) / (Sc * bc * dc)
        psy = (Ashy * dc) / (Sc * bc * dc)

        flx = Ke * psx * fyh
        fly = Ke * psy * fyh

        # Resistencia confinada
        if fcc is None:
            fcc = fccfco(flx, fly, fc0)

        if N == 3:
            return fcc

        # Deformación en resistencia máxima confinada
        ecc = ec0 * (1 + 5 * (fcc / fc0 - 1))
        Esec = fcc / ecc
        r = Ec / (Ec - Esec)

        # Cuantía volumétrica de estribos
        psh = psx + psy

        # Convención: compresión negativa en entrada
        ec = np.asarray(ec, dtype=float)
        fc = np.zeros_like(ec, dtype=float)

        z1 = (ec <= 0) & (ec >= -ecu)
        x = -ec[z1] / ecc
        fc[z1] = fcc * (x * r) / (r - 1 + x ** r)

        if N == 2:
            return fc, psh, Acc, pcc

        # salida por defecto: esfuerzo del hormigón
        return -fc

    @staticmethod
    def buscar_ecu(fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, datos_h):
        """
        Busca la deformación última del hormigón confinado ecu
        mediante equilibrio energético.

        Parámetros:
            fc0, ec0, esp, Ec : parámetros del hormigón
            fy, fsu, Es, ey, esh, esu : parámetros del acero transversal/longitudinal
            datos_h : tupla de datos para mander_c:
                      (fyh, b, h, r, Sc, de, d_corner, d_edge, Nb, NLx, NLy, ecu, fcc)

        Retorna:
            ecu : deformación última del hormigón confinado
        """

        # Hormigón no confinado
        ec_uc = np.empty(100)
        ec_uc[0] = -esp
        ec_uc[1:] = np.linspace(-2 * ec0, 0.0, 99)
        fc_uc = modelos.mander_u(ec_uc, fc0, ec0, esp, Ec, datos_h, 0)
        A_uc = -simpson(fc_uc, x=ec_uc)

        # Acero transversal
        es_sh = np.linspace(0, esu, 100)
        fs_sh = modelos.park(es_sh, fy, fsu, Es, ey, esh, esu)
        A_sh = simpson(fs_sh, x=es_sh)

        fyh, b, h, r, Sc, de, d_corner, d_edge, Nb, NLx, NLy, _, fcc = datos_h

        def f(ecu):
            # actualizar datos_h con el ecu de prueba
            datos_h_ecu = (fyh, b, h, r, Sc, de, d_corner, d_edge, Nb, NLx, NLy, ecu, fcc)

            # Hormigón confinado hasta ecu
            ec_cc = np.linspace(-ecu, 0, 100)
            fc_cc, psh, Acc, pcc = modelos.mander_c(ec_cc, fc0, ec0, esp, Ec, datos_h_ecu, 2)
            A_cc = simpson(fc_cc, x=ec_cc)

            # Acero longitudinal en compresión hasta ecu
            es = np.linspace(0, ecu, 100)
            fs_sc = modelos.park(es, fy, fsu, Es, ey, esh, ecu)
            A_sc = simpson(fs_sc, x=es)

            # Balance de energía: Ucc + Usc - Uco - Ush
            Ush = psh * Acc * A_sh
            Uco = Acc * A_uc
            Ucc = Acc * A_cc
            Usc = pcc * Acc * A_sc

            return Ucc + Usc - Uco - Ush

        return brentq(f, 2e-3, 5e-2)