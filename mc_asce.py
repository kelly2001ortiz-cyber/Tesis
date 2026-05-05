import numpy as np


def _num(d, k, default=None):
    v = d.get(k, default)
    if v is None or str(v).strip() == "":
        if default is None:
            raise ValueError(f"Falta el valor requerido: {k}")
        return float(default)
    return float(v)


def _ent(d, k, default=None):
    return int(float(_num(d, k, default)))


def calcular_fluencia(b, d, dl, fc, fy, ey, ec0, ecu, As, Asl, P0=0.0, columna=False):
    pt = As * fy / (b * d * fc)
    ptl = Asl * fy / (b * d * fc)
    alfay = ey / ec0
    Bc = dl / d

    k = np.sqrt(((pt + ptl) ** 2) / (4 * alfay ** 2) + (pt + Bc * ptl) / alfay) - (pt + ptl) / (2 * alfay)
    niu0 = P0 / ((b / 100) * (d / 100) * fc * 10)

    phi_y = ey / ((1 - k) * d / 100)
    if columna:
        c2 = 1 + 0.45 / (0.84 + pt)
        phi_y *= 1.05 + (c2 - 1.05) * niu0 / 0.3

    ec = min(phi_y * d / 100 - ey, ecu)
    niu = 0.75 / (1 + alfay) * (ec / ec0) ** 0.7
    alfac = min((1 - Bc) * ec / ey - Bc, 1.0)

    My = (0.5 * fc * 10 * b / 100 * (d / 100) ** 2) * (
        (1 + Bc - niu) * niu0 + (2 - niu) * pt + (niu - 2 * Bc) * alfac * ptl
    )
    return My, phi_y


def parametros_viga(cuantia, confinado, v_norma):
    x = max(0.0, min(0.5, cuantia))
    y = max(3.0, min(6.0, v_norma))

    def lin(t, t1, t2, q1, q2):
        return q1 if t <= t1 else q2 if t >= t2 else q1 + (q2 - q1) * (t - t1) / (t2 - t1)

    def bilin(q11, q21, q12, q22):
        return lin(y, 3.0, 6.0, lin(x, 0.0, 0.5, q11, q21), lin(x, 0.0, 0.5, q12, q22))

    if confinado:
        return bilin(0.025, 0.020, 0.020, 0.015), bilin(0.050, 0.030, 0.040, 0.020), 0.20
    return bilin(0.020, 0.010, 0.010, 0.005), bilin(0.030, 0.015, 0.015, 0.010), 0.20


def parametros_columna(rel_axial, rho_t, vy_vo, fc, fyt):
    vy_vo = max(0.2, vy_vo)
    a = max(0.0, 0.042 - 0.043 * rel_axial + 0.63 * rho_t - 0.023 * vy_vo)

    rel_b = min(rel_axial, 0.5)
    den = 5.0 - (rel_b / 0.8) * (1.0 / max(rho_t, 1e-6)) * (fc / max(fyt, 1e-6))
    b_base = a if den <= 0 else max(a, 0.5 / den - 0.01)

    if rel_axial <= 0.5:
        b = b_base
    elif rel_axial >= 0.7:
        b = a
    else:
        b = max(a, b_base * (0.7 - rel_axial) / 0.2)

    return a, b, max(0.0, 0.24 - 0.4 * rel_axial)


def construir_diagramas(My, phi_y, EI, Long, Lp, a, b_par, c, n=100):
    roty = Long * My / (6 * EI)
    if roty == 0:
        raise ValueError("La rotacion de fluencia resulto cero; revisa My, EI y Long.")

    rotu = roty + a
    rotR = roty + b_par
    Mu = My + 0.05 * (My / roty) * (rotu - roty)
    MR = c * My

    Mpts = np.array([0.0, My, Mu, MR, MR], dtype=float)
    Rpts = np.array([0.0, roty, rotu, rotu + 0.1 * (rotR - rotu), rotR], dtype=float)
    curu = phi_y + (rotu - roty) / Lp
    curR = phi_y + (rotR - roty) / Lp
    Cpts = np.array([0.0, phi_y, curu, curu + 0.1 * (curR - curu), curR], dtype=float)

    def interp(xp):
        idx = np.argsort(xp, kind="stable")
        xp, yp = xp[idx], Mpts[idx]
        xs, ys = [], []
        for x, y in zip(xp, yp):
            if xs and np.isclose(x, xs[-1], rtol=1e-12, atol=1e-15):
                ys[-1] = float(y)
            else:
                xs.append(float(x)); ys.append(float(y))
        xs, ys = np.asarray(xs), np.asarray(ys)
        x = np.linspace(xs.min(), xs.max(), n)
        return np.interp(x, xs, ys), x

    M, curv = interp(Cpts)
    Mr, rot = interp(Rpts)
    params = {
        "rigidez_asce": My / phi_y if phi_y != 0 else np.nan,
        "m_fluencia_asce": My,
        "curv_fluencia_asce": phi_y,
        "m_maximo_asce": Mu,
        "curv_m_max_asce": Cpts[2],
        "m_ultimo_asce": MR,
        "curv_ultima_asce": Cpts[4],
        "ductilidad_asce": Cpts[4] / phi_y if phi_y != 0 else np.nan,
    }
    return M, curv, Mr, rot, params


def calcular_viga(mat, sec, Long, V_usuario=None, n=100):
    fc, Ec, ec0, ecu, fy, ey = mat
    b = _num(sec, "disenar_viga_base")
    h = _num(sec, "disenar_viga_altura")
    rec = _num(sec, "disenar_viga_recubrimiento")
    d_est = _num(sec, "disenar_viga_diametro_transversal") / 10
    s_est = _num(sec, "disenar_viga_espaciamiento")
    d_sup = _num(sec, "disenar_viga_diametro_superior")
    d_inf = _num(sec, "disenar_viga_diametro_inferior")
    n_sup = _ent(sec, "disenar_viga_varillas_superior")
    n_inf = _ent(sec, "disenar_viga_varillas_inferior")

    area = lambda db_mm: np.pi / 4 * (db_mm / 10) ** 2
    d = h - rec - d_est - (d_sup / 10) / 2
    dl = h - d
    I = b * h ** 3 / 12
    EI = Ec * 10 * I / 100 ** 4
    As = n_inf * area(d_inf)
    Asl = n_sup * area(d_sup)
    Av = 2 * area(d_est * 10)

    My, phi_y = calcular_fluencia(b, d, dl, fc, fy, ey, ec0, ecu, As, Asl)

    beta1 = max(1.05 - fc / 1400 if fc > 280 else 0.85, 0.65)
    pb = 0.85 * fc / fy * beta1 * (6120 / (6120 + fy))
    cuantia = (As / (b * d) - Asl / (b * d)) / pb

    Lp = 0.08 * (Long / 2) + 0.022 * (fy * 0.0980665) * (d_inf / 1000)
    alpha = Long / (Long - 2 * Lp)
    V_calc = (abs(alpha * My) + abs(alpha * My)) / Long
    V = V_usuario if V_usuario is not None and V_usuario > 0 else V_calc

    Vs = Av * fy * d / s_est
    confinado = (s_est <= d / 3) and (Vs >= 0.75 * V)
    v_norma = 1.1926 * (V / ((b / 100) * (d / 100) * np.sqrt(fc)))
    a, b_par, c = parametros_viga(cuantia, confinado, v_norma)

    M, curv, Mr, rot, p = construir_diagramas(My, phi_y, EI, Long, Lp, a, b_par, c, n)
    p.update({
        "corte_viga_asce": V,
        "corte_viga_asce_calculado": V_calc * 1000,
        "corte_viga_asce_usado": V * 1000,
        "v_norma_viga_asce": v_norma,
        "confinado_viga_asce": confinado,
        "lp_asce": Lp,
    })
    return M, curv, Mr, rot, p


def calcular_columna(mat, sec, datos_asce, direccion, V_usuario=None, n=100):
    fc, Ec, ec0, ecu, fy, ey = mat
    es_x = str(direccion).strip().lower().endswith("x")

    # Se conserva tu convencion: para Direccion X se invierten base/altura y varillas/ramales.
    if es_x:
        b = _num(sec, "disenar_columna_altura")
        h = _num(sec, "disenar_columna_base")
        n_x = _ent(sec, "disenar_columna_varillasY_2")
        n_y = _ent(sec, "disenar_columna_varillasX_2")
        ram_x = _num(sec, "disenar_columna_ramalesY")
    else:
        b = _num(sec, "disenar_columna_base")
        h = _num(sec, "disenar_columna_altura")
        n_x = _ent(sec, "disenar_columna_varillasX_2")
        n_y = _ent(sec, "disenar_columna_varillasY_2")
        ram_x = _num(sec, "disenar_columna_ramalesX")

    rec = _num(sec, "disenar_columna_recubrimiento")
    d_est = _num(sec, "disenar_columna_diametro_transversal") / 10
    s_est = _num(sec, "disenar_columna_espaciamiento")
    db = _num(sec, "disenar_columna_diametro_longitudinal_2")
    db_esq = _num(sec, "disenar_columna_diametro_longitudinal_esq")
    P0 = _num(sec, "disenar_columna_axial") / 1000
    Long = _num(datos_asce, "long_viga_asce")

    area = lambda db_mm: np.pi / 4 * (db_mm / 10) ** 2
    A_corner = area(db_esq)
    A_gen = area(db)
    As = 2 * A_corner + max(0, n_y - 2) * A_gen 
    Asl = 2 * A_corner + max(0, n_y - 2) * A_gen
    As_total = 4 * A_corner + 2 * max(0, n_x - 2) * A_gen + 2 * max(0, n_y - 2) * A_gen

    d = h - rec - d_est - (db_esq / 10) / 2
    dl = rec + d_est + (db_esq / 10) / 2
    A = b * h
    I = b * h ** 3 / 12
    rel_axial_EI = P0 / ((b * h / 100**2) * fc * 10) # Relacion axial para determinar factor de rigidez.
    factor_EI = 0.70 if rel_axial_EI > 0.5 else 0.30  # Obtenido de ASCE
    EI = factor_EI * Ec * 10 * I / 100**4
    Av = ram_x * np.pi / 4 * d_est ** 2

    My, phi_y = calcular_fluencia(b, d, dl, fc, fy, ey, ec0, ecu, As, Asl, P0, columna=True)

    La_m = Long / 2
    La_cm = La_m * 100
    Lp = 0.08 * La_m + 0.022 * (fy * 0.0980665) * (db / 1000)
    alpha = Long / (Long - 2 * Lp)
    Vy_calc = (abs(alpha * My) + abs(alpha * My)) / Long
    Vy = V_usuario if V_usuario is not None and V_usuario > 0 else Vy_calc

    if La_cm <= 0 or d <= 0:
        raise ValueError("La y d deben ser mayores que cero.")
    Vs_kg = Av * fy * d / s_est
    Vc_kg = 0.5 * np.sqrt(fc) * (d / La_cm) * np.sqrt(max(0, 1 + (P0 * 1000) / (0.5 * A * np.sqrt(fc)))) * 0.8 * A
    Vo = (Vc_kg + Vs_kg) / 1000
    if Vo <= 0:
        raise ValueError("No se pudo calcular V0 de forma valida.")

    vy_vo = max(0.2, Vy / Vo)
    rel_axial = P0 / ((A / 100 ** 2) * fc * 10)
    rho_t = Av / (b * s_est)
    a, b_par, c = parametros_columna(rel_axial, rho_t, vy_vo, fc, fy)

    M, curv, Mr, rot, p = construir_diagramas(My, phi_y, EI, Long, Lp, a, b_par, c, n)
    p.update({
        "corte_columna_asce": Vy,
        "corte_columna_asce_calculado": Vy_calc,
        "corte_columna_asce_usado": Vy,
        "vo_columna_asce": Vo,
        "vy_vo_columna_asce": vy_vo,
        "relacion_axial_columna_asce": rel_axial,
        "rho_t_columna_asce": rho_t,
        "lp_asce": Lp,
        "la_asce": La_m,
        "as_total_columna_asce": As_total,
    })
    return M, curv, Mr, rot, p


def ejecutar_mc_asce(tipo_seccion, direccion, datos_hormigon, datos_acero, datos_seccion, datos_asce):
    tipo = str(tipo_seccion.currentText() if hasattr(tipo_seccion, "currentText") else tipo_seccion).strip().lower()
    direc = str(direccion.currentText() if hasattr(direccion, "currentText") else direccion).strip()

    mat = (
        _num(datos_hormigon, "esfuerzo_fc"),
        _num(datos_hormigon, "modulo_Ec"),
        _num(datos_hormigon, "def_max_sin_confinar"),
        _num(datos_hormigon, "def_ultima_sin_confinar"),
        _num(datos_acero, "esfuerzo_fy"),
        _num(datos_acero, "def_fluencia_acero"),
    )

    texto_v = datos_asce.get("corte_viga_asce", "")
    try:
        V_usuario = float(texto_v) / 1000 if str(texto_v).strip() != "" and float(texto_v) > 0 else None
    except Exception:
        V_usuario = None

    Long = _num(datos_asce, "long_viga_asce")
    if tipo == "viga":
        return calcular_viga(mat, datos_seccion, Long, V_usuario)
    return calcular_columna(mat, datos_seccion, datos_asce, direc, V_usuario)
