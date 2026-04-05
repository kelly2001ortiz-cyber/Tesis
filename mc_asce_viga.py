import numpy as np

def calcular_fluencia(b, d, dl, fc, fy, ey, ec0, ecu, As, Asl, P0):
    pt = As * fy / (b * d * fc)
    ptl = Asl * fy / (b * d * fc)
    alfay = ey / ec0
    Bc = dl / d
    term1 = (pt + ptl) ** 2 / (4 * alfay ** 2)
    term2 = (pt + Bc * ptl) / alfay
    term3 = (pt + ptl) / (2 * alfay)
    k = np.sqrt(term1 + term2) - term3
    niu0 = P0 / ((b / 100) * (d / 100) * fc * 10)
    phy_y = ey / ((1 - k) * d / 100)
    ec = phy_y * d / 100 - ey
    ec = min(ec, ecu)
    niu = 0.75 / (1 + alfay) * (ec / ec0) ** 0.7
    alfac = (1 - Bc) * ec / ey - Bc
    alfac = min(alfac, 1)
    My = (0.5 * fc * 10 * b / 100 * (d / 100) ** 2) * (((1 + Bc - niu) * niu0 + (2 - niu) * pt + (niu - 2 * Bc) * alfac * ptl))
    return My, phy_y

def _interp_lineal(x, x1, x2, y1, y2):
    if x <= x1:
        return y1
    if x >= x2:
        return y2
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)

def _interp_bilineal(x, y, x1, x2, y1, y2, q11, q21, q12, q22):
    r1 = _interp_lineal(x, x1, x2, q11, q21)
    r2 = _interp_lineal(x, x1, x2, q12, q22)
    return _interp_lineal(y, y1, y2, r1, r2)

def obtener_parametros_modelado_viga_asce41_17(cuantia_relativa, confinado, v_norma):
    """
      x = (rho - rho') / rho_bal
      y = V / (bw * d * sqrt(fc'))
    """
    x = max(0.0, min(0.5, cuantia_relativa))
    y = max(3.0, min(6.0, v_norma))

    if confinado:
        a = _interp_bilineal(
            x, y,
            0.0, 0.5,
            3.0, 6.0,
            0.025, 0.020,
            0.020, 0.015)
        b = _interp_bilineal(
            x, y,
            0.0, 0.5,
            3.0, 6.0,
            0.050, 0.030,
            0.040, 0.020)
    else:
        a = _interp_bilineal(
            x, y,
            0.0, 0.5,
            3.0, 6.0,
            0.020, 0.010,
            0.010, 0.005)
        b = _interp_bilineal(
            x, y,
            0.0, 0.5,
            3.0, 6.0,
            0.030, 0.015,
            0.015, 0.010)
    c = 0.20
    return a, b, c

def calcular_lp_viga_paulay_priestley_1992(z, fy_mpa, db_m):
    return 0.08 * z + 0.022 * fy_mpa * db_m

def calcular_momentos_extremo_desde_lp(My, Long, Lp):
    """
        Lp = ((Mi - My) / (Mi + Mj)) * Long
    """
    if Lp <= 0:
        raise ValueError("Lp debe ser mayor que cero.")

    if 2.0 * Lp >= Long:
        raise ValueError("Lp no puede ser mayor o igual que Long/2.")

    alpha = Long / (Long - 2.0 * Lp)
    Mi = alpha * My
    Mj = alpha * My
    return Mi, Mj, alpha

def calcular_cortante_diseno_desde_momentos(Mi, Mj, Long):
    return (abs(Mi) + abs(Mj)) / Long

def calcular_respuesta_seccion(
    fc, fy, Ec, b, h, rec, d_est, s_est,
    d_var_sup, n_var_sup, d_var_inf, n_var_inf,
    ey, ec0, ecu, Long, P0=0, n_puntos=100, V_usuario=None):

    #Cálculos iniciales
    d = h - rec - d_est - (d_var_sup / 10)/2           # cm
    dl = h - d                     # cm
    I = b * h**3 / 12              # cm4
    As = n_var_inf * (np.pi / 4 * (d_var_inf / 10) ** 2)   # cm2
    Asl = n_var_sup * (np.pi / 4 * (d_var_sup / 10) ** 2)  # cm2
    Av = 2 * np.pi / 4 * (d_est) ** 2                      # cm2
    EI = Ec * 10 * I / 100**4
    B1 = 1.05 - fc / 1400 if fc > 280 else 0.85
    B1 = max(B1, 0.65)

    # Punto de fluencia
    My, phy_y = calcular_fluencia(b, d, dl, fc, fy, ey, ec0, ecu, As, Asl, P0)

    # Relación de Cuantía
    p = As / (b * d)
    pl = Asl / (b * d)
    pb = 0.85 * fc / fy * B1 * (6120 / (6120 + fy))
    cuantia = (p - pl) / pb

    # Longitud plástica Lp
    z = Long / 2              # m
    db_m = d_var_inf / 1000      # mm -> m
    fy_mpa = fy * 0.0980665        # kg/cm2 -> MPa
    Lp = calcular_lp_viga_paulay_priestley_1992(z=z, fy_mpa=fy_mpa, db_m=db_m)

    # Obtener Mi y Mj a partir de Lp
    Mi, Mj, alpha = calcular_momentos_extremo_desde_lp(My, Long, Lp)

    # Cortante de diseño calculado
    V_calc = calcular_cortante_diseno_desde_momentos(Mi, Mj, Long)
    if V_usuario is not None and V_usuario > 0:
        V_diseno = V_usuario
    else:
        V_diseno = V_calc

    # Clasificación del refuerzo transversal (Confinado / NoConfinado)
    Vs = Av * fy * d / s_est
    confinado = (s_est <= d / 3) and (Vs >= 0.75 * V_diseno)

    # Cortante normalizado para ingresar a la tabla de parámetros de modelado
    bw = b / 100.0                 # cm -> m
    d_m = d / 100.0                # cm -> m
    v_norma = 1.1926 * (V_diseno / (bw * d_m * np.sqrt(fc)))

    # Parámetros ASCE 41-17 para vigas controladas por flexión
    a, b_par, c = obtener_parametros_modelado_viga_asce41_17(
        cuantia_relativa=cuantia,
        confinado=confinado,
        v_norma=v_norma)

    # Diagrama momento-rotación
    roty = Long * My / (6 * EI)              # Rotación en el punto de fluencia
    rotu = roty + a                          # Rotación última
    Mu = My + 0.05 * EI * (rotu - roty)      # Momento último
    MR = c * My                              # Momento residual
    rotR = roty + b_par                      # Rotación residual
    Rotacion = np.array([0, roty, rotu, rotu + ((rotR - rotu) * 0.1), rotR], dtype=float)
    Momento = np.array([0, My, Mu, MR, MR], dtype=float)

    # Diagrama momento-curvatura
    cury = phy_y                   # Curvatura en el punto de fluencia
    curu = cury + rotu / Lp        # Curvatura última
    curR = cury + rotR / Lp        # Curvatura residual
    #curu = cury + (rotu - roty) / Lp
    #curR = cury + (rotR - roty) / Lp
    Curvatura = np.array([0, cury, curu, curu + ((curR - curu) * 0.1), curR], dtype=float)

    # Interpolación lineal a n_puntos Curvatura
    thetas = np.linspace(Curvatura.min(), Curvatura.max(), n_puntos)
    M = np.interp(thetas, Curvatura, Momento)

    # Interpolación lineal a n_puntos Rotacion
    rots = np.linspace(Rotacion.min(), Rotacion.max(), n_puntos)
    Mr = np.interp(rots, Rotacion, Momento)
    
    rigidez = My / cury if cury != 0 else np.nan
    ductilidad = curR / cury if cury != 0 else np.nan

    parametros = {
        "rigidez_asce": rigidez,
        "m_fluencia_asce": My,
        "curv_fluencia_asce": cury,
        "m_maximo_asce": Mu,
        "curv_m_max_asce": curu,
        "m_ultimo_asce": MR,
        "curv_ultima_asce": curR,
        "ductilidad_asce": ductilidad,
        "corte_viga_asce": V_diseno,
        "corte_viga_asce_calculado": V_calc,
    }

    return M, thetas, Mr, rots, parametros

def ejecutar_mc_asce_viga(datos_hormigon, datos_acero, datos_seccion, datos_asce):
    fc = float(datos_hormigon.get("esfuerzo_fc"))
    Ec = float(datos_hormigon.get("modulo_Ec"))
    ec0 = float(datos_hormigon.get("def_max_sin_confinar"))
    ecu = float(datos_hormigon.get("def_ultima_sin_confinar"))
    fy = float(datos_acero.get("esfuerzo_fy"))
    ey = float(datos_acero.get("def_fluencia_acero"))
    b = float(datos_seccion.get("disenar_viga_base"))
    h = float(datos_seccion.get("disenar_viga_altura"))
    rec = float(datos_seccion.get("disenar_viga_recubrimiento"))
    n_var_inf = int(float(datos_seccion.get("disenar_viga_varillas_inferior")))
    n_var_sup = int(float(datos_seccion.get("disenar_viga_varillas_superior")))
    d_est = float(datos_seccion.get("disenar_viga_diametro_transversal")) / 10.0
    d_var_inf = float(datos_seccion.get("disenar_viga_diametro_inferior"))
    d_var_sup = float(datos_seccion.get("disenar_viga_diametro_superior"))
    s_est = float(datos_seccion.get("disenar_viga_espaciamiento"))
    Long = float(datos_asce.get("long_viga_asce"))
    
    corte_viga_asce = datos_asce.get("corte_viga_asce", "")
    try:
        V_usuario = float(corte_viga_asce) if str(corte_viga_asce).strip() != "" else None
    except Exception:
        V_usuario = None
        
    M, thetas, Mr, rots, parametros = calcular_respuesta_seccion(
        fc, fy, Ec, b, h, rec, d_est, s_est,
        d_var_sup, n_var_sup, d_var_inf, n_var_inf,
        ey, ec0, ecu, Long, P0=0, n_puntos=100, V_usuario=V_usuario)
    
    return M, thetas, Mr, rots, parametros