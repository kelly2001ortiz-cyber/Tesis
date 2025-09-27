import numpy as np
from scipy.integrate import simpson
from scipy.optimize import brentq

# --- Modelo constitutivo del hormigon confinado de Mander ---
def mander_confinado(datos_hormigon, datos_acero, datos_seccion):

    def mander_cc(ecu):
        # Obtener parametros de sección, materiales y armado
        fc0 = float(datos_hormigon.get("esfuerzo_fc"))
        Ec = float(datos_hormigon.get("modulo_Ec"))
        ec0 = float(datos_hormigon.get("def_max_sin_confinar"))
        esu = float(datos_hormigon.get("def_ultima_confinada"))
        fy = float(datos_acero.get("esfuerzo_fy"))
        b = float(datos_seccion.get("disenar_columna_base"))
        h = float(datos_seccion.get("disenar_columna_altura"))
        rec = float(datos_seccion.get("disenar_columna_recubrimiento"))
        Sc = float(datos_seccion.get("disenar_columna_espaciamiento"))
        de = float(datos_seccion.get("disenar_columna_diametro_transversal"))/10
        dbe = float(datos_seccion.get("disenar_columna_diametro_longitudinal_2"))/10
        dbi = float(datos_seccion.get("disenar_columna_diametro_longitudinal_2"))/10
        Nb1 = float(datos_seccion.get("disenar_columna_varillasX_2"))
        Nb2 = float(datos_seccion.get("disenar_columna_varillasY_2"))
        Nb = (Nb1-2)*2 + Nb2*2
        NLx = float(datos_seccion.get("disenar_columna_ramalesX"))
        NLy = float(datos_seccion.get("disenar_columna_ramalesY"))

        # calculo de f'cc - Mander, J. B., Priestley, M. J. N., and Park, R. (1984) "Seismic design of bridge piers"
        def fccfco(flx, fly, fc0):
            sigma1, sigma2, sigma3 = -min(flx, fly), -max(flx, fly), -fc0
            tau_oct_i, tau_oct_j = 1, 2
            tol = 1e-6
            for i in range(1000):
                # esfuerzos octaedricos
                sigma_oct = (sigma1 + sigma2 + sigma3) / 3
                tau_oct_i = (((sigma1 - sigma2) ** 2 + (sigma2 - sigma3) ** 2 + (sigma3 - sigma1) ** 2) ** 0.5 ) / 3
                cos_theta = (sigma1 - sigma_oct) / (2 ** 0.5 * tau_oct_i)
                # coeficiente de esfuerzo normal octaedrico
                sigmap_oct = sigma_oct / fc0
                # ecuaciones de los meridianos
                T = 0.069232 - 0.661091 * sigmap_oct - 0.049350 * sigmap_oct ** 2
                C = 0.122965 - 1.150502 * sigmap_oct - 0.315545 * sigmap_oct ** 2
                # coeficiente de esfuerzo cortante octaedrico
                D = 4 * (C ** 2 - T ** 2) * cos_theta ** 2
                tau_oct_j = fc0 * C * (D / (2 * cos_theta) + (2 * T - C) * (D + 5 * T ** 2 - 4 * T * C) ** 0.5) / (D + (2 * T - C) ** 2)            
                sigma3_nuevo = (sigma1 + sigma2) / 2 - (4.5 * tau_oct_j ** 2 - 0.75 * (sigma1 - sigma2) ** 2) ** 0.5
                if abs(tau_oct_i - tau_oct_j) < tol and abs(sigma3 - sigma3_nuevo) < tol:
                    sigma3 = sigma3_nuevo
                    break
                sigma3 = sigma3_nuevo
            return -sigma3
        # dimensiones del nucleo
        dc = h - 2 * rec - de              # Altura confinada
        bc = b - 2 * rec - de              # Base confinada
        Ss = Sc - de                       # Longitud libre entre estribos
        # area inefectiva (zona no confinada)
        Wx = (bc - de - 2 * dbe - (NLx - 2) * dbi) / (NLx - 1)
        Wy = (dc - de - 2 * dbe - (NLy - 2) * dbi) / (NLy - 1)
        Ainef = (2 * (NLx - 1) * Wx ** 2 / 6) + (2 * (NLy - 1) * Wy ** 2 / 6)
        # Area efectiva confinada
        Ae = (bc * dc - Ainef) * (1 - Ss / (2 * bc)) * (1 - Ss / (2 * dc))
        # cuantia del acero longitudinal
        Ast = np.pi * (dbe ** 2 + (Nb - 4) * dbi ** 2 / 4)
        Ac = bc * dc
        Acc = Ac - Ast
        pcc = Ast / Acc
        # coeficiente de confinamiento efectivo
        ke = Ae / Acc
        # presion lateral de confinamiento
        Ash = np.pi * de ** 2 / 4
        px = (NLx * Ash * bc) / (Sc * bc * dc)
        py = (NLy * Ash * dc) / (Sc * bc * dc)
        flx = ke * px * fy
        fly = ke * py * fy
        # incremento de resistencia por confinamiento
        fcc = fccfco(flx, fly, fc0)
        ecc = ec0 * (1 + 5 * (fcc / fc0 - 1))
        # modulo secante y parámetro r
        Esec = fcc / ecc
        r = Ec / (Ec - Esec)
        # cuantia volumetrica de estribos
        psh = (NLx * Ash * bc + NLy * Ash * dc) / (Acc * Sc)
        # diagrama esfuerzo-deformacion
        ec = np.linspace(0, ecu, 100)
        fc = np.zeros_like(ec)
        x = ec / ecc
        fc = fcc * (x * r) / (r - 1 + x ** r)
        return ec, fc, psh, Acc

    def mander_uc():
        # Obtener parametros de materiales
        fc0 = float(datos_hormigon.get("esfuerzo_fc"))
        Ec = float(datos_hormigon.get("modulo_Ec"))
        ec0 = float(datos_hormigon.get("def_max_sin_confinar"))
        esp = float(datos_hormigon.get("def_ultima_sin_confinar")) # Agregar

        ec00 = 2 * ec0

        ec = np.zeros(100)
        ec[-1] = esp
        ec[:99] = np.linspace(0, ec00, 99)
        fc = np.zeros_like(ec)
        # Módulo secante y parámetro r
        Esec = fc0 / ec0
        r = Ec / (Ec - Esec)
        # Diagrama esfuerzo-deformacion
        z1 = (ec > 0) & (ec <= ec00)
        x = ec[z1] / ec0
        fc[z1] = fc0 * (x * r) / (r - 1 + x ** r)
        fc[-1] = 0
        return ec, fc

    def park_sh():
        # Obtener parametros de materiales
        fy = float(datos_acero.get("esfuerzo_fy"))
        fsu = float(datos_acero.get("esfuerzo_ultimo_acero"))
        Es = float(datos_acero.get("modulo_Es"))
        ey = float(datos_acero.get("def_fluencia_acero"))
        esh = float(datos_acero.get("def_inicio_endurecimiento"))
        esu = float(datos_acero.get("def_ultima_acero"))  # Cambiar por el del acero

        es = np.linspace(0, esu, 100)
        fs = np.zeros_like(es)
        # zona elestica
        z1 = (es <= ey)
        fs[z1] = Es * es[z1]
        # zona perfectamente plastica
        z2 = (es > ey) & (es <= esh)
        fs[z2] = fy
        # zona de endurecimiento por deformacion
        z3 = (es > esh) & (es <= esu)
        r = esu - esh
        m = ((fsu / fy) * (30 * r + 1) ** 2 - 60 * r - 1) / (15 * r ** 2)  
        delta_e = es[z3] - esh
        parte1 = (m * delta_e + 2) / (60 * delta_e + 2)
        parte2 = delta_e * (60 - m) / (2 * (30 * r + 1) ** 2)
        fs[z3] = np.sign(es[z3]) * fy * (parte1 + parte2)
        return es, fs

    ### -------------------------------------------------------------------------------------- ###
    def g(ecu):
        # hormigon no confinado
        ec_uc, fc_uc = mander_uc()
        A_uc = simpson(fc_uc, ec_uc)
        # acero transversal
        es_sh, fs_sh = park_sh()
        A_sh = simpson(fs_sh, es_sh)
        # hormigon confinado hasta ecu
        ec_cc, fc_cc, psh, Acc = mander_cc(ecu)
        A_cc = simpson(fc_cc, ec_cc)
        # balance de energia: Ucc - Uco - Ush
        Ush = psh * Acc * A_sh
        Uco = Acc * A_uc
        Ucc = Acc * A_cc
        return Ucc - Uco - Ush

    ecu = brentq(g, 0.002, 0.100)
    ec_cc, fc_cc, _, _ = mander_cc(ecu)

    return ec_cc, fc_cc
