import numpy as np

def calcular_fluencia(b, d, dl, fc, fy, ecy, ec0, ecu, As, Asl, P0):
    pt = As*fy/(b*d*fc)
    ptl = Asl*fy/(b*d*fc)
    alfay = ecy/ec0
    Bc = dl/d
    term1 = (pt + ptl)**2 / (4 * alfay**2)
    term2 = (pt + Bc * ptl) / alfay
    term3 = (pt + ptl) / (2 * alfay)
    k = np.sqrt(term1 + term2) - term3
    c2 = 1 + 0.45 / (0.84 + pt)
    niu0 = P0/((b/100)*(d/100)*fc*10)
    phi_y = (1.05 + (c2 - 1.05)*niu0/0.3) * (ecy/((1-k)*d/100))
    ec = phi_y * d/100 - ecy
    ec = min(ec, ecu)
    niu = 0.75/(1 + alfay)*(ec/ec0)**(0.7)
    alfac = (1 - Bc) * ec/ecy - Bc
    alfac = min(alfac, 1)
    My = (0.5 * fc*10 * b/100 * (d/100)**2) * (((1 + Bc - niu) * niu0 + (2 - niu) * pt +(niu - 2 * Bc) * alfac * ptl))
    roty = phi_y
    return My, roty

def obtener_parametros_modelado(condicion, p_rel=None, confinado=None, V_norm=None, s_est=None, d=None):
    # Condición I: Vigas controladas por Flexión
    if condicion == "Flexión":
        if p_rel is None or confinado is None or V_norm is None:
            return "Faltan parámetros para condición de flexión."

        if confinado:
            if p_rel <= 0.1:
                if V_norm <= 3:
                    return 0.02, 0.03, 0.2
                else:
                    return 0.016, 0.024, 0.2
            elif p_rel >= 0.4:
                if V_norm <= 3:
                    return 0.015, 0.025, 0.2
                else:
                    return 0.012, 0.02, 0.2

    # Casos con refuerzo NO confinado
        else:
            if p_rel <= 0.1:
                if V_norm <= 3:
                    return 0.006, 0.015, 0.2
                else:
                    return 0.005, 0.012, 0.2
            elif p_rel >= 0.4:
                if V_norm <= 3:
                    return 0.003, 0.01, 0.2
                else:
                    return 0.002, 0.008, 0.2

    # Condición II: Controladas por corte
    elif condicion == "Corte":
        if s_est is None or d is None:
            return "Falta información"
        if s_est <= d / 2 or p_rel <= 0.1:
            return "No se permitirá."

    else:
        return "Condición no válida."

def calcular_respuesta_seccion(fc, fy, Ec, b, h, rec, d_est, s_est,
        d_long, n_var_x, n_var_y, ram_x, ram_y,
        ey, ec0, ecu, Long, Vv, P0, condicion, n_puntos=100):
    # Datos iniciales
    d = h - rec
    dl = h - d
    A = b * h
    I = b * h**3 / 12
    n_var_total = (n_var_x - 2) * 2 + (n_var_y) * 2
    As = n_var_total/2 * (np.pi /4 * (d_long/10)**2)
    Asl = As
    Av = ram_y * np.pi/4*(d_est)**2

    # Factor B1
    B1 = 1.05 - fc/1400 if fc > 280 else 0.85
    B1 = max(B1, 0.65)

    ct = h/2     # cm
    fct = 0.10*fc  # kg/cm2     
    # Determinacion del punto A
    MA = (I/ct*(fct + P0/A))/10**5
    phyA = MA/(Ec*I)
    # Punto de fluencia
    My, phy_y = calcular_fluencia(b, d, dl, fc, fy, ey, ec0, ecu, As, Asl, P0)

    # Rigideces
    EA = Ec * A
    EI = Ec * 10 * I / 100**4

    # Cuantía a flexión
    p_rel = P0/(A/100**2*fc*10)  # Cuantía de acero a tracción
    # Comprobación de refuerzo transversal confinado
    Vs = (Av*fy*d/s_est)/1000   # T
    if s_est <= d/3 or Vs > 3/4*Vv:
        confinado = True
    else: 
        confinado = False
    # Cortante actuante
    bw = b/100   # m
    d = d/100    # m
    #fc = fc*10   # T/m2
    V_norm = 1.1926 * (Vv / (bw * d * np.sqrt(fc))) # Pound/in

    params = obtener_parametros_modelado(condicion, p_rel, confinado, V_norm, s_est, d)
    if not isinstance(params, tuple) or len(params) != 3:
        raise ValueError(str(params))
    a, b_par, c = params
    
    # Determinacion de rotacion de fluencia según ASCE 
    roty = Long*My/(6*EI)

    #----------------------------------------------------------
    # Hallar el diagrama momento rotacion
    rotu = roty + a   # rad
    Mu = My + 0.05 *EI * (rotu - roty)
    MR = c * My
    rotR = roty + b_par
    Momento = np.array([0, My, Mu, MR, MR])
    Rotacion = np.array([0, roty, rotu, rotu+((rotR-rotu)*0.1), rotR])

    # Hallar el diagrama momento curvatura
    Mi = 1.05*My
    Mj = 1.05*My
    Lp = (Mi - My)/(Mi + Mj)*Long
    cury = phy_y    # rad/m
    curu = cury + rotu/Lp    # rad/m
    curR = cury + rotR/Lp    # rad/m
    Curvatura = np.array([0, cury, curu, curu+((curR-curu)*0.1), curR], dtype=float)

    # Interpolación lineal a n_puntos (=100 por defecto) uniformes en Curvatura
    thetas = np.linspace(Curvatura.min(), Curvatura.max(), n_puntos)
    M = np.interp(thetas, Curvatura, Momento)

    # Interpolación lineal a n_puntos (=100 por defecto) uniformes en Rotacion
    rots = np.linspace(Rotacion.min(), Rotacion.max(), n_puntos)
    Mr = np.interp(rots, Rotacion, Momento)

    return M, thetas, Mr, rots

def ejecutar_mc_asce_columnaX (datos_hormigon, datos_acero, datos_seccion, datos_asce, condicion):

    fc = float(datos_hormigon.get("esfuerzo_fc"))              # Esfuerzo máximo (kg/cm² o MPa)
    Ec = float(datos_hormigon.get("modulo_Ec"))                 # Módulo de elasticidad (kg/cm² o MPa)
    ec0 = float(datos_hormigon.get("def_max_sin_confinar"))     # Deformación máxima (pico)
    ecu = float(datos_hormigon.get("def_ultima_sin_confinar")) 
    fy = float(datos_acero.get("esfuerzo_fy"))     # Esfuerzo de fluencia
    ey = float(datos_acero.get("def_fluencia_acero"))
    h = float(datos_seccion.get("disenar_columna_base"))     # Esfuerzo de fluencia
    b = float(datos_seccion.get("disenar_columna_altura"))     # Esfuerzo de fluencia
    rec = float(datos_seccion.get("disenar_columna_recubrimiento"))     # Esfuerzo de fluencia
    
    n_var_y = int(float(datos_seccion.get("disenar_columna_varillasX_2")))
    n_var_x = int(float(datos_seccion.get("disenar_columna_varillasY_2")))
    d_est = float(datos_seccion.get("disenar_columna_diametro_transversal"))/10     # Esfuerzo de fluencia
    d_long = float(datos_seccion.get("disenar_columna_diametro_longitudinal_2"))
    ram_y = float(datos_seccion.get("disenar_columna_ramalesX"))
    ram_x = float(datos_seccion.get("disenar_columna_ramalesY"))

    s_est = float(datos_seccion.get("disenar_columna_espaciamiento"))
    Long = float(datos_asce.get("long_viga_asce"))
    Vv = float(datos_asce.get("cortante_viga_asce"))/1000
    P0 = float(datos_asce.get("axial_columna_asce"))/1000

    M, thetas, Mr, rots = calcular_respuesta_seccion(
        fc, fy, Ec, b, h, rec, d_est, s_est,
        d_long, n_var_x, n_var_y, ram_x, ram_y,
        ey, ec0, ecu, Long, Vv, P0, condicion=condicion, n_puntos=100
    )
    return M, thetas, Mr, rots
