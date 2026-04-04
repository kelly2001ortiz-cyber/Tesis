import numpy as np
from scipy.integrate import simpson
from scipy.optimize import brentq

# Modelo de Mander para hormigon confinado
def mander_c(ec, fc0, Ec, ec0, fyh, b, h, r, Sc, de, d_corner, d_edge, Nb, NLx, NLy, ecu):
    # calculo de f'cc - Mander, J. B., Priestley, M. J. N., and Park, R. (1984) "Seismic design of bridge piers"
    def fccfco(flx, fly, fc0):
        sigma1, sigma2 = -min(flx, fly), -max(flx, fly)
        def f(sigma3):
            sigma_oct = (sigma1 + sigma2 + sigma3) / 3
            tau_oct_i = (((sigma1 - sigma2) ** 2 + (sigma2 - sigma3) ** 2 + (sigma3 - sigma1) ** 2) ** 0.5 ) / 3
            cos_theta = (sigma1 - sigma_oct) / (2 ** 0.5 * tau_oct_i)
            cos_theta = np.clip(cos_theta, -1, 1)
            # coeficiente de esfuerzo normal octaedrico
            sigmap_oct = sigma_oct / fc0
            # ecuaciones de los meridianos
            T = 0.069232 - 0.661091 * sigmap_oct - 0.049350 * sigmap_oct ** 2
            C = 0.122965 - 1.150502 * sigmap_oct - 0.315545 * sigmap_oct ** 2
            # coeficiente de esfuerzo cortante octaedrico
            D = 4 * (C ** 2 - T ** 2) * cos_theta ** 2
            tau_oct_j = fc0 * C * (D / (2 * cos_theta) + (2 * T - C) * (D + 5 * T**2 - 4 * T * C)**0.5) / (D + (2 * T - C)**2)
            return tau_oct_i - tau_oct_j
        sigma3 = brentq(f, -3*fc0, -fc0)
        return -sigma3
    # dimensiones del nucleo
    dc = h - 2 * r - de    # altura confinada
    bc = b - 2 * r - de    # base confinada
    Ss = Sc - de           # longitud libre entre estribos
    # area inefectiva
    Wx = (bc - de - 2 * d_corner - (NLx - 2) * d_edge) / (NLx - 1)
    Wy = (dc - de - 2 * d_corner - (NLy - 2) * d_edge) / (NLy - 1)
    Ainef = (2 * (NLx - 1) * (Wx ** 2) / 6) + (2 * (NLy - 1) * Wy ** 2 / 6)
    # area efectiva confinada
    Ae = (bc * dc - Ainef) * (1 - Ss / (2 * bc)) * (1 - Ss / (2 * dc))
    # cuantia del acero longitudinal
    AsL = np.pi * (d_corner ** 2 + (Nb - 4) * d_edge ** 2 / 4)
    Ac = bc * dc
    pcc = AsL / Ac
    Acc = Ac * (1 - pcc)
    # coeficiente de confinamiento efectivo
    Ke = Ae / Acc
    # presion lateral de confinamiento
    Ash = np.pi * de ** 2 / 4
    Ashx = NLx * Ash
    Ashy = NLy * Ash
    psx = (Ashx * bc) / (Sc * bc * dc)
    psy = (Ashy * dc) / (Sc * bc * dc)
    flx = Ke * psx * fyh
    fly = Ke * psy * fyh
    # incremento de resistencia por confinamiento
    fcc = fccfco(flx, fly, fc0)
    ecc = ec0 * (1 + 5 * (fcc / fc0 - 1))
    # modulo secante y parámetro r
    Esec = fcc / ecc
    r = Ec / (Ec - Esec)
    # cuantia volumetrica de estribos
    psh = psx + psy
    # diagrama esfuerzo-deformacion
    ec = np.asarray(ec, dtype=float)
    fc = np.zeros_like(ec, dtype=float)
    x = ec / ecc
    fc = fcc * (x * r) / (r - 1 + x ** r)
    return fc, psh, Acc, pcc

# Modelo de Mander para hormigon no confinado
def mander_u(ec, fc0, ec0, esp, Ec):
    ec = np.asarray(ec, dtype=float)
    fc = np.zeros_like(ec, dtype=float)
    ec00 = 2 * ec0
    # modulo secante y parámetro r
    Esec = fc0 / ec0
    r = Ec / (Ec - Esec)
    # rama ascendente curva
    z1 = (ec <= 0) & (ec >= -ec00)
    x = ec[z1] / -ec0
    fc[z1] = -fc0 * (x * r) / (r - 1 + x ** r)
    # rama descendente lineal
    z2 = (ec >= -esp) & (ec < -ec00)
    fc[z2] = -fc0 * (2 * r) / (r - 1 + 2 ** r) * (esp + ec[z2]) / (esp - ec00)
    return fc

# Modelo de Park para acero longitudinal
def park(es, fy, fsu, Es, ey, esh, esu):
    es = np.asarray(es, dtype=float)
    fs = np.zeros_like(es, dtype=float)
    abs_es = np.abs(es)
    sign = np.sign(es)
    # rama elestica lineal
    z1 = (abs_es <= ey)
    fs[z1] = Es * es[z1]
    # rama perfectamente plastica
    z2 = (abs_es > ey) & (abs_es <= esh)
    fs[z2] = fy * sign[z2]
    # rama de endurecimiento por deformacion
    z3 = (abs_es > esh) & (abs_es <= esu)
    delta_e = abs_es[z3] - esh
    r = esu - esh
    m = ((fsu / fy) * (30 * r + 1) ** 2 - 60 * r - 1) / (15 * r ** 2)
    parte1 = (m * delta_e + 2) / (60 * delta_e + 2)
    parte2 = delta_e * (60 - m) / (2 * (30 * r + 1) ** 2)
    fs[z3] = sign[z3] * fy * (parte1 + parte2)
    return fs

### -------------------------------------------------------------------------------------- ###
def mander_confinado(datos_hormigon, datos_acero, datos_seccion):
    fc0 = float(datos_hormigon.get("esfuerzo_fc"))
    Ec = float(datos_hormigon.get("modulo_Ec"))
    ec0 = float(datos_hormigon.get("def_max_sin_confinar"))
    esp = float(datos_hormigon.get("def_ultima_sin_confinar")) 

    Es = float(datos_acero.get("modulo_Es"))
    fy = float(datos_acero.get("esfuerzo_fy"))
    ey = float(datos_acero.get("def_fluencia_acero"))
    fsu = float(datos_acero.get("esfuerzo_ultimo_acero"))
    esh = float(datos_acero.get("def_inicio_endurecimiento"))
    esu = float(datos_acero.get("def_ultima_acero"))

    b = float(datos_seccion.get("disenar_columna_base"))
    h = float(datos_seccion.get("disenar_columna_altura"))
    r = float(datos_seccion.get("disenar_columna_recubrimiento"))
    Nb1 = int(float(datos_seccion.get("disenar_columna_varillasX_2")))
    Nb2 = int(float(datos_seccion.get("disenar_columna_varillasY_2")))
    de = float(datos_seccion.get("disenar_columna_diametro_transversal"))/10
    Sc = float(datos_seccion.get("disenar_columna_espaciamiento"))
    d_edge = int(float(datos_seccion.get("disenar_columna_diametro_longitudinal_2")))/10
    d_corner = int(float(datos_seccion.get("disenar_columna_diametro_longitudinal_esq")))/10
    NLx = float(datos_seccion.get("disenar_columna_ramalesX"))
    NLy = float(datos_seccion.get("disenar_columna_ramalesY"))
    Nb = (Nb1 - 2) * 2 + Nb2 * 2
    
    def buscar_ecu():
        # hormigon no confinado
        ec_uc = np.empty(100)
        ec_uc[0] = -esp
        ec_uc[1:] = np.linspace(-2 * ec0, 0.0, 99)
        fc_uc = mander_u(ec_uc, fc0, ec0, esp, Ec)
        A_uc = -simpson(fc_uc, x=ec_uc)
        # acero transversal
        es_sh = np.linspace(0, esu, 100)
        fs_sh = park(es_sh, fy, fsu, Es, ey, esh, esu)
        A_sh = simpson(fs_sh, x=es_sh)
        def f(ecu):
            # hormigon confinado hasta ecu
            ec_cc = np.linspace(0, ecu, 100)
            fc_cc, psh, Acc, pcc = mander_c(ec_cc, fc0, Ec, ec0, fy, b, h, r, Sc,
                                        de, d_corner, d_edge, Nb, NLx, NLy, ecu)            
            A_cc = simpson(fc_cc, x=ec_cc)
            # acero longitudinal en compresion hasta ecu
            fs_sc = park(ec_cc, fy, fsu, Es, ey, esh, ecu)
            A_sc = simpson(fs_sc, x=ec_cc)
            # balance de energia: Ucc + Usc - Uco - Ush
            Ush = psh * Acc * A_sh
            Uco = Acc * A_uc
            Ucc = Acc * A_cc
            Usc = pcc * Acc * A_sc
            return Ucc + Usc - Uco - Ush
        return brentq(f, 2e-3, 5e-2)

    ecu = buscar_ecu()
    ec = np.linspace(0, ecu, 100)
    fc, _, _, _ = mander_c(ec, fc0, Ec, ec0, fy, b, h, r, Sc, de, 
                                   d_corner, d_edge, Nb, NLx, NLy, ecu)
    return ec, fc
