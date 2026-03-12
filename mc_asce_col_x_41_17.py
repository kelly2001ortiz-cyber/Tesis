import numpy as np

def calcular_areas_longitudinales_columna_y(n_var_x, n_var_y, d_long_general, d_long_esquina):
    if n_var_x < 2 or n_var_y < 2:
        raise ValueError("n_var_x y n_var_y deben ser al menos 2.")
    A_corner = np.pi / 4.0 * (d_long_esquina / 10.0) ** 2  #cm2
    A_gen = np.pi / 4.0 * (d_long_general / 10.0) ** 2  #cm2
    As_eje_y = 2.0 * A_corner + max(0, n_var_y- 2) * A_gen # max(0, n_var_x- 2)/2.0 * A_gen
    As_total = (4.0 * A_corner + 2.0 * max(0, n_var_x - 2) * A_gen + 2.0 * max(0, n_var_y - 2) * A_gen)

    return As_eje_y, As_total

def calcular_fluencia(b, d, dl, fc, fy, ecy, ec0, ecu, As, Asl, P0):
    pt = As * fy / (b * d * fc)
    ptl = Asl * fy / (b * d * fc)
    alfay = ecy / ec0
    Bc = dl / d
    term1 = (pt + ptl) ** 2 / (4 * alfay ** 2)
    term2 = (pt + Bc * ptl) / alfay
    term3 = (pt + ptl) / (2 * alfay)
    k = np.sqrt(term1 + term2) - term3
    c2 = 1 + 0.45 / (0.84 + pt)
    niu0 = P0 / ((b / 100.0) * (d / 100.0) * fc * 10.0)
    phi_y = (1.05 + (c2 - 1.05) * niu0 / 0.3) * (ecy / ((1 - k) * d / 100.0))
    ec = phi_y * d / 100.0 - ecy
    ec = min(ec, ecu)
    niu = 0.75 / (1 + alfay) * (ec / ec0) ** 0.7
    alfac = (1 - Bc) * ec / ecy - Bc
    alfac = min(alfac, 1.0)
    My = (0.5 * fc * 10.0 * b / 100.0 * (d / 100.0) ** 2) * (((1 + Bc - niu) * niu0) + ((2 - niu) * pt) + ((niu - 2 * Bc) * alfac * ptl))
    return My, phi_y

def calcular_momentos_extremo_desde_lp(My, Long, Lp):
    if Lp <= 0:
        raise ValueError("Lp debe ser mayor que cero.")
    if 2.0 * Lp >= Long:
        raise ValueError("Lp no puede ser mayor o igual que Long/2 con Mi = Mj.")
    alpha = Long / (Long - 2.0 * Lp)
    Mi = alpha * My
    Mj = alpha * My
    return Mi, Mj, alpha

def calcular_vy_desde_momentos(Mi, Mj, Long):
    return (abs(Mi) + abs(Mj)) / Long

def calcular_vo_rectangular(fc, Ag, Av, fy, d, s, La, P0):
    P0_kg = P0 * 1000.0
    Vs_kg = Av * fy * d / s
    #  Sezen-Moehle.
    if La <= 0 or d <= 0:
        raise ValueError("La y d deben ser mayores que cero.")
    factor_aspecto = d / La    # La shear span (distancia desde la sección crítica hasta el putno de inflexión)
    term_axial = np.sqrt(max(0.0, 1.0 + P0_kg / (0.5 * Ag * np.sqrt(fc))))
    Vc_kg = 0.5 * np.sqrt(fc) * factor_aspecto * term_axial * 0.8 * Ag
    V0_kg = Vc_kg + Vs_kg
    return V0_kg / 1000.0  # T

def obtener_parametros_modelado_columna_asce41_17(relacion_axial, rho_t, vy_vo, fc, fyt):
    vy_vo = max(0.2, vy_vo)  # no menor a 0.2 para evitar valores extremos

    a = max(0.0, 0.042 - 0.043 * relacion_axial + 0.63 * rho_t - 0.023 * vy_vo)

    # b donde NUD/(Ag f'cE) no excede 0.5
    relacion_axial_b = min(relacion_axial, 0.5)
    rho_t_eff = max(rho_t, 1e-6)  # Evitar divisiones inválidas
    fyt_eff = max(fyt, 1e-6)      # Evitar divisiones inválidas
    denominador = (5.0 - (relacion_axial_b / 0.8) * (1.0 / rho_t_eff) * (fc / fyt_eff))
    if denominador <= 0:
        b_base = a
    else:
        b_base = 0.5 / denominador - 0.01
        b_base = max(a, b_base)

    # Reducción lineal de b cuando relacion_axial > 0.5 hasta cero en 0.7,
    if relacion_axial <= 0.5:
        b = b_base
    elif relacion_axial >= 0.7:
        b = a
    else:
        factor = (0.7 - relacion_axial) / (0.7 - 0.5)
        b = max(a, b_base * factor)

    c = max(0.0, 0.24 - 0.4 * relacion_axial)

    return a, b, c

def calcular_respuesta_seccion(
    fc, fy, Ec, b, h, rec, d_est, s_est,
    d_long_general, d_long_esquina,
    n_var_x, n_var_y, ram_x, ram_y,
    ey, ec0, ecu, Long, P0, n_puntos=100):

    d = h - rec - d_est - (d_long_general / 10.0) / 2.0           # cm
    dl = h - d                      # cm
    A = b * h                       # cm2
    I = b * h**3 / 12.0             # cm4

    As_face_y, As_total = calcular_areas_longitudinales_columna_y(
        n_var_x=n_var_x,
        n_var_y=n_var_y,
        d_long_general=d_long_general,
        d_long_esquina=d_long_esquina)
    
    As = As_face_y
    Asl = As_face_y
    Av = ram_x * np.pi / 4.0 * (d_est) ** 2   # confirmar  cm

    My, phy_y = calcular_fluencia(b, d, dl, fc, fy, ey, ec0, ecu, As, Asl, P0)

    EA = Ec * A
    EI = Ec * 10.0 * I / 100.0**4

    # Longitud plástica
    La_m = Long / 2.0
    La_cm = La_m * 100.0
    fy_mpa = fy * 0.0980665
    db_m = d_long_general / 1000.0
    Lp =  0.08 * La_m + 0.022 * fy_mpa * db_m

    # Mi, Mj y Vy calculados
    Mi, Mj, alpha = calcular_momentos_extremo_desde_lp(My, Long, Lp)
    Vy = calcular_vy_desde_momentos(Mi, Mj, Long)

    # V0 y razón Vy/Vo calculados
    Vo = calcular_vo_rectangular(fc=fc, Ag=A, Av=Av, fy=fy, d=d, s=s_est, La=La_cm, P0=P0)
    if Vo <= 0:
        raise ValueError("No se pudo calcular V0 de forma válida.")
    vy_vo = max(0.2, Vy / Vo)

    # parametros  de ASCE 41-17
    relacion_axial = P0 / ((A / 100.0**2) * fc * 10.0)
    rho_t = Av / (b * s_est)
    a, b_par, c = obtener_parametros_modelado_columna_asce41_17(relacion_axial=relacion_axial, rho_t=rho_t, vy_vo=vy_vo, fc=fc, fyt=fy)

    # Momento-rotación
    roty = Long * My / (6.0 * EI)
    rotu = roty + a
    Mu = My + 0.05 * EI * (rotu - roty)
    MR = c * My
    rotR = roty + b_par
    Momento = np.array([0.0, My, Mu, MR, MR], dtype=float)
    Rotacion = np.array([0.0, roty, rotu, rotu + 0.1 * (rotR - rotu), rotR], dtype=float)
    rots = np.linspace(Rotacion.min(), Rotacion.max(), n_puntos)
    Mr = np.interp(rots, Rotacion, Momento)
    
    # Momento-curvatura
    cury = phy_y
    curu = cury + rotu / Lp
    curR = cury + rotR / Lp
    Curvatura = np.array([0.0, cury, curu, curu + 0.1 * (curR - curu), curR], dtype=float)
    thetas = np.linspace(Curvatura.min(), Curvatura.max(), n_puntos)
    M = np.interp(thetas, Curvatura, Momento)

    return M, thetas, Mr, rots

def ejecutar_mc_asce_columnaY(datos_hormigon, datos_acero, datos_seccion, datos_asce):
    fc = float(datos_hormigon.get("esfuerzo_fc"))
    Ec = float(datos_hormigon.get("modulo_Ec"))
    ec0 = float(datos_hormigon.get("def_max_sin_confinar"))
    ecu = float(datos_hormigon.get("def_ultima_sin_confinar"))
    fy = float(datos_acero.get("esfuerzo_fy"))
    ey = float(datos_acero.get("def_fluencia_acero"))
    h = float(datos_seccion.get("disenar_columna_base"))
    b = float(datos_seccion.get("disenar_columna_altura"))
    rec = float(datos_seccion.get("disenar_columna_recubrimiento"))
    n_var_y = int(float(datos_seccion.get("disenar_columna_varillasX_2")))
    n_var_x = int(float(datos_seccion.get("disenar_columna_varillasY_2")))
    d_est = float(datos_seccion.get("disenar_columna_diametro_transversal")) / 10.0
    d_long_general = float(datos_seccion.get("disenar_columna_diametro_longitudinal_2"))
    d_long_esquina = float(datos_seccion.get("disenar_columna_diametro_longitudinal_esq"))
    ram_y = float(datos_seccion.get("disenar_columna_ramalesX"))
    ram_x = float(datos_seccion.get("disenar_columna_ramalesY"))
    s_est = float(datos_seccion.get("disenar_columna_espaciamiento"))
    Long = float(datos_asce.get("long_columna_asce"))
    P0 = float(datos_asce.get("axial_columna_asce")) / 1000.0  # T

    M, thetas, Mr, rots = calcular_respuesta_seccion(
        fc, fy, Ec, b, h, rec, d_est, s_est,
        d_long_general, d_long_esquina,
        n_var_x, n_var_y, ram_x, ram_y,
        ey, ec0, ecu, Long, P0,
        n_puntos=100)

    return M, thetas, Mr, rots