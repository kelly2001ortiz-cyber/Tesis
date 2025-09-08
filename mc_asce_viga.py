import numpy as np

def calcular_fluencia(b, d, dl, fc, fy, ey, ec0, ecu, As, Asl, P0):
    pt = As*fy/(b*d*fc)
    ptl = Asl*fy/(b*d*fc)
    alfay = ey/ec0
    Bc = dl/d
    term1 = (pt + ptl)**2 / (4 * alfay**2)
    term2 = (pt + Bc * ptl) / alfay
    term3 = (pt + ptl) / (2 * alfay)
    k = np.sqrt(term1 + term2) - term3
    niu0 = P0/((b/100)*(d/100)*fc*10)
    phy_y = ey/((1-k)*d/100)
    ec = phy_y * d/100 - ey
    ec = min(ec, ecu)
    niu = 0.75/(1 + alfay)*(ec/ec0)**(0.7)
    alfac = (1 - Bc) * ec/ey - Bc
    alfac = min(alfac, 1)
    My = (0.5 * fc*10 * b/100 * (d/100)**2) * (((1 + Bc - niu) * niu0 + (2 - niu) * pt +(niu - 2 * Bc) * alfac * ptl))
    return My, phy_y

def obtener_parametros_modelado(condicion, cuantia=None, confinado=None, V_ac=None, s_est=None):
    if condicion == "Flexión":
        if cuantia is None or confinado is None or V_ac is None:
            return "Faltan parámetros para condición de flexión."
        if confinado:
            if cuantia <= 0:
                return (0.025, 0.05, 0.2) if V_ac < 3 else (0.02, 0.04, 0.2)
            elif cuantia > 0 and cuantia <= 0.5:
                return (0.02, 0.04, 0.2) if V_ac < 3 else (0.015, 0.02, 0.2)
            else:
                return (0.015, 0.02, 0.2) if V_ac < 3 else (0.01, 0.015, 0.2)
        else:
            if cuantia <= 0:
                return (0.015, 0.02, 0.2) if V_ac < 3 else (0.01, 0.015, 0.2)
            else:
                return (0.01, 0.015, 0.2) if V_ac < 3 else (0.005, 0.01, 0.2)
    elif condicion == "Corte":
        if s_est is None:
            return "Falta información de separación de estribos."
        return (0.003, 0.02, 0.2) if s_est <= 0.5 else (0.003, 0.01, 0.2)
    elif condicion == "desarrollo":
        if s_est is None:
            return "Falta información de separación de estribos."
        return (0.003, 0.02, 0.0) if s_est <= 0.5 else (0.003, 0.01, 0.0)
    elif condicion == "empotramiento":
        return 0.015, 0.03, 0.2
    else:
        return "Condición no válida."

def calcular_respuesta_seccion(fc, fy, Ec, b, h, rec, d_est, s_est,
                              d_var_sup, n_var_sup, d_var_inf, n_var_inf,
                              ey, ec0, ecu, Long, Vv,
                              coefi, condicion, P0=0, n_puntos=100):
    # Datos iniciales
    d = h - rec
    dl = h - d
    A = b * h
    I = b * h**3 / 12
    As = n_var_inf * (np.pi /4 * (d_var_inf/10)**2)
    Asl = n_var_sup * (np.pi /4 * (d_var_sup/10)**2)
    Av = 2 * np.pi/4*(d_est)**2

    # Factor B1
    B1 = 1.05 - fc/1400 if fc > 280 else 0.85
    B1 = max(B1, 0.65)

    # Punto de fluencia
    My, phy_y = calcular_fluencia(b, d, dl, fc, fy, ey, ec0, ecu, As, Asl, P0)

    # Rigideces
    EA = Ec * A
    EI = Ec * 10 * I / 100**4

    # Cuantía
    p = As / (b * d)
    pl = Asl / (b * d)
    pb = 0.85*fc/fy*B1*(6120/(6120+fy))
    cuantia = (p - pl)/pb

    # Confinamiento
    Vs = Av*fy*d/s_est
    confinado = True if (s_est <= d/3 or Vs > 3/4*Vv) else False

    # Cortante actuante
    bw = b/100
    d_m = d/100
    V_ac = 1.1926 * (Vv / (bw * d_m * np.sqrt(fc)))

    params = obtener_parametros_modelado(condicion, cuantia, confinado, V_ac, s_est)
    if not isinstance(params, tuple) or len(params) != 3:
        raise ValueError(str(params))
    a, b_par, c = params

    # Rotación y curvatura
    roty = Long*My/(6*EI)
    Mi = coefi*My
    Mj = coefi*My
    Lp = (Mi - My)/(Mi + Mj)*Long

    rotu = roty + a
    Mu = My + 0.05 *EI * (rotu - roty)
    MR = c * My
    rotR = roty + b_par

    Rotacion = np.array([0, roty, rotu, rotu+((rotR-rotu)*0.1), rotR])
    Momento = np.array([0, My, Mu, MR, MR], dtype=float)

    cury = phy_y
    curu = cury + rotu/Lp
    curR = cury + rotR/Lp
    Curvatura = np.array([0, cury, curu, curu+((curR-curu)*0.1), curR], dtype=float)
    # Interpolación lineal a n_puntos (=100 por defecto) uniformes en Curvatura
    thetas = np.linspace(Curvatura.min(), Curvatura.max(), n_puntos)
    M = np.interp(thetas, Curvatura, Momento)

    # Interpolación lineal a n_puntos (=100 por defecto) uniformes en Rotacion
    rots = np.linspace(Rotacion.min(), Rotacion.max(), n_puntos)
    Mr = np.interp(rots, Rotacion, Momento)

    return M, thetas, Mr, rots

def ejecutar_mc_asce_viga (datos_hormigon, datos_acero, datos_seccion, datos_asce, condicion):
    fc = float(datos_hormigon.get("esfuerzo_fc"))              # Esfuerzo máximo (kg/cm² o MPa)
    Ec = float(datos_hormigon.get("modulo_Ec"))                 # Módulo de elasticidad (kg/cm² o MPa)
    ec0 = float(datos_hormigon.get("def_max_sin_confinar"))     # Deformación máxima (pico)
    ecu = float(datos_hormigon.get("def_ultima_sin_confinar")) 
    fy = float(datos_acero.get("esfuerzo_fy"))     # Esfuerzo de fluencia
    ey = float(datos_acero.get("def_fluencia_acero"))
    b = float(datos_seccion.get("disenar_viga_base"))     # Esfuerzo de fluencia
    h = float(datos_seccion.get("disenar_viga_altura"))     # Esfuerzo de fluencia
    rec = float(datos_seccion.get("disenar_viga_recubrimiento"))     # Esfuerzo de fluencia
    n_var_inf = int(float(datos_seccion.get("disenar_viga_varillas_inferior")))
    n_var_sup = int(float(datos_seccion.get("disenar_viga_varillas_superior")))
    d_est = float(datos_seccion.get("disenar_viga_diametro_transversal"))/10     # Esfuerzo de fluencia
    d_var_inf = float(datos_seccion.get("disenar_viga_diametro_inferior"))
    d_var_sup = float(datos_seccion.get("disenar_viga_diametro_superior"))
    s_est = float(datos_seccion.get("disenar_viga_espaciamiento"))
    Long = float(datos_asce.get("long_viga_asce"))
    Vv = float(datos_asce.get("cortante_viga_asce"))/1000
    coefi = float(datos_asce.get("coef_viga_asce"))

    M, thetas, Mr, rots = calcular_respuesta_seccion(
        fc, fy, Ec, b, h, rec, d_est, s_est,
        d_var_sup, n_var_sup, d_var_inf, n_var_inf,
        ey, ec0, ecu, Long, Vv,
        coefi, condicion=condicion, P0=0, n_puntos=100
    )
    return M, thetas, Mr, rots
