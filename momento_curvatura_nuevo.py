import numpy as np
from scipy.optimize import root_scalar
from materiales_copia import modelos
from seccion import utilidades
from diagrama_interaccion import calcular_series_di

park = modelos.park
hognestad = modelos.hognestad
mander_u = modelos.mander_u
mander_c = modelos.mander_c
buscar_ecu = modelos.buscar_ecu

barras_columna = utilidades.barras_columna
barras_viga = utilidades.barras_viga
malla = utilidades.malla

MODELOS_HORMIGON = {
    "hognestad": hognestad,
    "mander_u": mander_u,
    "mander_c": mander_c,
}


def sigma_hormigon(nombre_modelo):
    try:
        return MODELOS_HORMIGON[nombre_modelo.lower().strip()]
    except KeyError as exc:
        raise ValueError(f"Modelo de hormigon no valido: {nombre_modelo}") from exc


def _f(datos, clave, default=None):
    valor = datos.get(clave, default)
    if valor is None or valor == "":
        raise ValueError(f"Falta el dato '{clave}'")
    return float(valor)


def _ecu_limite(esp, datos_h):
    if datos_h is not None and len(datos_h) > 11 and datos_h[11] is not None:
        return float(datos_h[11])
    return float(esp)


# ============================================================
# MOTOR UNICO MOMENTO-CURVATURA, PARA VIGAS Y COLUMNAS
# ============================================================

def _deformaciones(fibras, e0, phi):
    return e0 - phi * fibras[:, 0]


def _resultante_hormigon(fibras, sigma_c, e0, phi, fc0, ec0, esp, Ec, datos_h):
    eps = _deformaciones(fibras, e0, phi)
    sig = sigma_c(eps, fc0, ec0, esp, Ec, datos_h, 1)
    A = fibras[:, 1]
    y = fibras[:, 0]
    return np.sum(sig * A), np.sum(sig * A * y)


def _resultante_acero(As, e0, phi, fy, fsu, Es, ey, esh, esu):
    eps = _deformaciones(As, e0, phi)
    sig = park(eps, fy, fsu, Es, ey, esh, esu)
    A = As[:, 1]
    y = As[:, 0]
    return np.sum(sig * A), np.sum(sig * A * y)


def _resultantes(e0, phi, cover, core, As, fc0, ec0, esp, Ec,
                 fy, fsu, Es, ey, esh, esu, P, datos_h,
                 sg_cover, sg_core):
    N1, M1 = _resultante_hormigon(cover, sg_cover, e0, phi, fc0, ec0, esp, Ec, datos_h)
    N2, M2 = _resultante_hormigon(core, sg_core, e0, phi, fc0, ec0, esp, Ec, datos_h)
    Ns, Ms = _resultante_acero(As, e0, phi, fy, fsu, Es, ey, esh, esu)
    return N1 + N2 + Ns - P, M1 + M2 + Ms


def _rango_e0(phi, cover, core, As, ecu, esu):
    y = np.concatenate((cover[:, 0], core[:, 0], As[:, 0]))
    q = -phi * y
    e0_min = -abs(ecu) - np.max(q)
    e0_max = abs(esu) - np.min(q)
    return (e0_min, e0_max) if e0_min <= e0_max else (e0_max, e0_min)


def _buscar_e0(phi, cover, core, As, tol, fc0, ec0, esp, Ec,
               fy, fsu, Es, ey, esh, esu, P, datos_h,
               sg_cover, sg_core, e0_prev, ecu):
    def R(e0):
        return _resultantes(
            e0, phi, cover, core, As, fc0, ec0, esp, Ec,
            fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core
        )[0]

    e0_min, e0_max = _rango_e0(phi, cover, core, As, ecu, esu)
    rango = e0_max - e0_min
    if rango <= 0:
        return None

    e0_obj = 0.0 if e0_prev is None else e0_prev
    e0 = float(np.clip(e0_obj, e0_min, e0_max))

    def dR_de0(e0_actual):
        de = min(max(1e-7, 1e-6 * rango), 1e-4)
        eps_s = _deformaciones(As, e0_actual, phi)
        dist = np.min(np.abs(esu - np.abs(eps_s)))
        if np.isfinite(dist) and dist > 0:
            de = min(de, 0.25 * dist)
        de = max(de, 1e-7)
        a = max(e0_min, e0_actual - de)
        b = min(e0_max, e0_actual + de)
        if abs(b - a) < 1e-14:
            return None
        return (R(b) - R(a)) / (b - a)

    for _ in range(100):
        r = R(e0)
        if abs(r) <= tol:
            return e0
        k = dR_de0(e0)
        if k is None or not np.isfinite(k) or abs(k) < 1e-14:
            break
        paso = float(np.clip(-r / k, -0.05 * rango, 0.05 * rango))
        mejoro = False
        for _ in range(20):
            e_trial = float(np.clip(e0 + paso, e0_min, e0_max))
            if abs(e_trial - e0) < 1e-14:
                break
            if abs(R(e_trial)) <= tol:
                return e_trial
            if abs(R(e_trial)) < abs(r):
                e0 = e_trial
                mejoro = True
                break
            paso *= 0.5
        if not mejoro:
            break

    if abs(R(e0)) <= tol:
        return e0

    e0_grid = np.linspace(e0_min, e0_max, 101)
    R_grid = np.fromiter((R(x) for x in e0_grid), dtype=float, count=len(e0_grid))
    roots = []
    idxs = np.unique(np.concatenate((
        np.flatnonzero(np.abs(R_grid[:-1]) < tol),
        np.flatnonzero(R_grid[:-1] * R_grid[1:] < 0.0),
    )))

    for i in idxs:
        a, b = e0_grid[i], e0_grid[i + 1]
        if abs(R_grid[i]) < tol:
            roots.append(a)
            continue
        try:
            sol = root_scalar(R, bracket=[a, b], method="brentq")
            if sol.converged and abs(R(sol.root)) <= tol:
                roots.append(sol.root)
        except ValueError:
            pass

    if not roots:
        return None
    return min(np.unique(np.array(roots, dtype=float)), key=lambda x: abs(x - e0_obj))


def diagrama_MC_unico(cover, core, As, tol, h, fc0, ec0, esp, Ec,
                      fy, fsu, Es, ey, esh, esu,
                      P, datos_h, sg_cover, sg_core, n=100):
    """
    Motor unico para vigas y columnas.

    Usa compatibilidad de deformaciones epsilon = e0 - phi*y y equilibrio axial
    N_int - P = 0. Devuelve M positivo, phi y c equivalente = e0/phi.
    """
    M_vals = [0.0]
    phi_vals = [0.0]
    c_vals = [0.0]

    y_ref = np.max(As[:, 0])
    if abs(y_ref) < 1e-14:
        y_ref = np.max(np.abs(As[:, 0]))
    phi_max = abs(esu / y_ref)

    a = phi_max / ((n - 1) * (1 + 0.5 * (n - 2) * 0.5))
    b = 0.5 * a
    phi_trial = [0.0] + [round(i * a + i * (i - 1) * b / 2, 100) for i in range(1, n)]

    e0_prev = None
    ecu = _ecu_limite(esp, datos_h)

    for phi in phi_trial[1:]:
        e0 = _buscar_e0(
            phi, cover, core, As, tol, fc0, ec0, esp, Ec,
            fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core,
            e0_prev, ecu
        )
        if e0 is None:
            continue

        M = -_resultantes(
            e0, phi, cover, core, As, fc0, ec0, esp, Ec,
            fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core
        )[1]
        if M <= 0:
            continue

        M_vals.append(M)
        phi_vals.append(phi)
        c_vals.append(e0 / phi if abs(phi) > 1e-14 else 0.0)
        e0_prev = e0

    return np.array(M_vals), np.array(phi_vals), np.array(c_vals)


# Alias conservados para no romper llamadas antiguas.
def diagrama_MC_columna(*args, **kwargs):
    return diagrama_MC_unico(*args, **kwargs)


def diagrama_MC(*args, **kwargs):
    kwargs.pop("recuperar_rama", None)
    return diagrama_MC_unico(*args, **kwargs)


# ============================================================
# PARAMETROS CARACTERISTICOS DE LA CURVA M-PHI
# ============================================================

def _limpiar_curva(phi, M):
    phi = np.asarray(phi, dtype=float).ravel()
    M = np.asarray(M, dtype=float).ravel()
    mask = np.isfinite(phi) & np.isfinite(M)
    phi, M = phi[mask], M[mask]
    if len(phi) == 0:
        raise ValueError("La curva momento-curvatura esta vacia.")
    idx = np.argsort(phi)
    phi, M = phi[idx], M[idx]
    keep = np.r_[True, np.diff(phi) > max(1e-12, 1e-10 * np.ptp(phi))]
    phi, M = phi[keep], M[keep]
    if phi[0] > 0:
        phi, M = np.r_[0.0, phi], np.r_[0.0, M]
    return phi, M


def _K_inicial(phi, M, min_pts=4, r2_min=0.999):
    mejor = None
    for i in range(max(2, min_pts), len(phi) + 1):
        x, y = phi[:i], M[:i]
        if np.any(np.diff(y) < 0):
            break
        den = np.dot(x, x)
        if den <= 0:
            break
        K = np.dot(x, y) / den
        yhat = K * x
        ss_res = np.sum((y - yhat) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1.0 if ss_tot <= 0 else 1.0 - ss_res / ss_tot
        if K > 0 and r2 >= r2_min:
            mejor = float(K)
        else:
            break
    if mejor is not None:
        return mejor
    i = min(max(2, min_pts), len(phi))
    return float(np.dot(phi[:i], M[:i]) / max(np.dot(phi[:i], phi[:i]), 1e-12))


def _interp(x, y, xq):
    return float(np.interp(float(xq), x, y))


def _phi_por_M(phi, M, idx_max, M_obj):
    for i in range(1, idx_max + 1):
        if M[i] >= M_obj:
            if abs(M[i] - M[i - 1]) < 1e-14:
                return float(phi[i])
            return float(phi[i - 1] + (M_obj - M[i - 1]) * (phi[i] - phi[i - 1]) / (M[i] - M[i - 1]))
    return float(phi[idx_max])


def _punto_degradacion(phi, M, idx_max, fraccion=0.80):
    M_lim = fraccion * M[idx_max]
    for i in range(idx_max + 1, len(M)):
        if M[i] <= M_lim:
            if i == idx_max + 1 or abs(M[i] - M[i - 1]) < 1e-14:
                return float(phi[i]), float(M_lim), True
            phi_f = phi[i - 1] + (M_lim - M[i - 1]) * (phi[i] - phi[i - 1]) / (M[i] - M[i - 1])
            return float(phi_f), float(M_lim), True
    return float(phi[-1]), float(M[-1]), False


def _area_hasta(phi, M, phi_ref):
    mask = phi < phi_ref
    x = np.append(phi[mask], phi_ref)
    y = np.append(M[mask], _interp(phi, M, phi_ref))
    return float(np.trapz(y, x))


def extraer_parametros_caracteristicos_mc(phi, M):
    phi, M = _limpiar_curva(phi, M)
    if len(phi) < 2:
        raise ValueError("No hay suficientes puntos en la tabla M-phi.")

    idx_max = int(np.argmax(M))
    M_max = float(M[idx_max])
    phi_peak = float(phi[idx_max])
    phi_max = _phi_por_M(phi, M, idx_max, 0.99 * M_max)
    K_ini = _K_inicial(phi[:idx_max + 1], M[:idx_max + 1]) if idx_max >= 1 else M_max / max(phi_peak, 1e-12)
    phi_u, M_u = float(phi[-1]), float(M[-1])
    phi_f, M_f, cruce_80 = _punto_degradacion(phi, M, idx_max, 0.80)

    if len(phi) < 4 or K_ini <= 1e-12:
        M_y = 0.60 * M_max
    else:
        phi_ref = phi_f if cruce_80 else phi_u
        M_ref = M_f if cruce_80 else M_u
        den = phi_ref - M_ref / K_ini
        M_y = 0.60 * M_max if den <= 1e-12 else (2 * _area_hasta(phi, M, phi_ref) - M_ref * phi_ref) / den

    M_y = float(np.clip(M_y, 1e-12, max(1e-12, 0.999 * M_max)))
    phi_y = float(M_y / K_ini) if K_ini > 1e-12 else float(0.60 * phi_max)
    phi_lim = max(min(phi_max * 0.999, phi_u * 0.999), 1e-12)
    phi_y = float(np.clip(phi_y, 1e-12, phi_lim))

    return {
        "rigidez_inicial": K_ini,
        "punto_fluencia": {"phi": phi_y, "M": M_y},
        "punto_maximo": {"phi": phi_max, "M": M_max},
        "punto_pico_real": {"phi": phi_peak, "M": M_max},
        "punto_falla": {"phi": phi_f, "M": M_f},
        "punto_ultimo": {"phi": phi_u, "M": M_u},
        "punto_final_analisis": {"phi": phi_u, "M": M_u},
        "punto_degradacion": {"phi": phi_f, "M": M_f},
        "ductilidad_curvatura": float(phi_u / phi_y) if phi_y > 0 else np.inf,
        "area_bajo_curva": _area_hasta(phi, M, phi_u),
        "criterio_fluencia": "Idealizacion bilineal; phi_y = M_y / K_i.",
        "criterio_maximo": "M_max es el pico real; phi_max alcanza 0.99*M_max en rama ascendente.",
        "criterio_falla": "Primer punto post-pico donde M desciende a 0.80*M_max.",
        "criterio_ultimo": "Ultimo punto disponible de la tabla M-phi.",
        "criterio_ductilidad": "mu_phi = phi_u / phi_y.",
    }


# ============================================================
# PREPARACION DE DATOS DE ENTRADA
# ============================================================

def _datos_h_mander_confinado(datos_hormigon, datos_acero, datos_seccion):
    fc0 = _f(datos_hormigon, "esfuerzo_fc")
    Ec = _f(datos_hormigon, "modulo_Ec")
    ec0 = _f(datos_hormigon, "def_max_sin_confinar")
    esp = _f(datos_hormigon, "def_ultima_sin_confinar")
    fy = _f(datos_acero, "esfuerzo_fy")
    fsu = _f(datos_acero, "esfuerzo_ultimo_acero")
    Es = _f(datos_acero, "modulo_Es")
    ey = _f(datos_acero, "def_fluencia_acero")
    esh = _f(datos_acero, "def_inicio_endurecimiento")
    esu = _f(datos_acero, "def_ultima_acero")

    b = _f(datos_seccion, "disenar_columna_base")
    h = _f(datos_seccion, "disenar_columna_altura")
    r = _f(datos_seccion, "disenar_columna_recubrimiento")
    Sc = _f(datos_seccion, "disenar_columna_espaciamiento")
    de = _f(datos_seccion, "disenar_columna_diametro_transversal") / 10.0
    d_edge = _f(datos_seccion, "disenar_columna_diametro_longitudinal_2") / 10.0
    d_corner = _f(datos_seccion, "disenar_columna_diametro_longitudinal_esq") / 10.0
    nr_x = int(_f(datos_seccion, "disenar_columna_ramalesX"))
    nr_y = int(_f(datos_seccion, "disenar_columna_ramalesY"))
    nb_x = int(_f(datos_seccion, "disenar_columna_varillasX_2"))
    nb_y = int(_f(datos_seccion, "disenar_columna_varillasY_2"))
    nb = 2 * (nb_x - 2) + 2 * nb_y

    base = (fy, b, h, r, Sc, de, d_corner, d_edge, nb, nr_x, nr_y)
    ecu = buscar_ecu(fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, base + (None, None))
    fcc = mander_c(0, fc0, ec0, esp, Ec, base + (ecu, None), 3)
    return base + (ecu, fcc)


def _preparar_seccion(datos_seccion, datos_fibras, tipo, eje):
    nf_x = int(_f(datos_fibras, "fibras_x"))
    nf_y = int(_f(datos_fibras, "fibras_y"))

    if tipo == "columna":
        b = _f(datos_seccion, "disenar_columna_base")
        h = _f(datos_seccion, "disenar_columna_altura")
        r = _f(datos_seccion, "disenar_columna_recubrimiento")
        de = _f(datos_seccion, "disenar_columna_diametro_transversal") / 10.0
        nb_x = int(_f(datos_seccion, "disenar_columna_varillasX_2"))
        nb_y = int(_f(datos_seccion, "disenar_columna_varillasY_2"))
        d_edge = _f(datos_seccion, "disenar_columna_diametro_longitudinal_2") / 10.0
        d_corner = _f(datos_seccion, "disenar_columna_diametro_longitudinal_esq") / 10.0
        cover, core = malla(b, h, r, de, nf_x, nf_y, eje)
        As = barras_columna(b, h, r, de, nb_x, nb_y, d_corner, d_edge, eje)
        P_real = _f(datos_seccion, "disenar_columna_axial", 0.0)
        return b, h, cover, core, As, P_real

    if tipo == "viga":
        b = _f(datos_seccion, "disenar_viga_base")
        h = _f(datos_seccion, "disenar_viga_altura")
        r = _f(datos_seccion, "disenar_viga_recubrimiento")
        de = _f(datos_seccion, "disenar_viga_diametro_transversal") / 10.0
        nb_sup = int(_f(datos_seccion, "disenar_viga_varillas_superior"))
        nb_inf = int(_f(datos_seccion, "disenar_viga_varillas_inferior"))
        d_sup = _f(datos_seccion, "disenar_viga_diametro_superior") / 10.0
        d_inf = _f(datos_seccion, "disenar_viga_diametro_inferior") / 10.0
        cover, core = malla(b, h, r, de, nf_x, nf_y, "x")
        As = barras_viga(h, r, de, nb_sup, nb_inf, d_sup, d_inf)
        return b, h, cover, core, As, 0.0

    raise ValueError(f"Tipo de seccion no valido: {tipo}")


# ============================================================
# API PRINCIPAL CONSERVADA
# ============================================================

def calcular_momento_curvatura(datos_hormigon, datos_acero, datos_seccion,
                               datos_fibras, tipo_seccion, eje,
                               modelo_cover, modelo_core, P=0.0, tol=1e-5):
    tipo = tipo_seccion.strip().lower()
    eje = eje.strip().lower()
    modelo_cover = modelo_cover.strip().lower()
    modelo_core = modelo_core.strip().lower()

    fc0 = _f(datos_hormigon, "esfuerzo_fc")
    Ec = _f(datos_hormigon, "modulo_Ec")
    ec0 = _f(datos_hormigon, "def_max_sin_confinar")
    esp = _f(datos_hormigon, "def_ultima_sin_confinar")
    fy = _f(datos_acero, "esfuerzo_fy")
    fsu = _f(datos_acero, "esfuerzo_ultimo_acero")
    Es = _f(datos_acero, "modulo_Es")
    ey = _f(datos_acero, "def_fluencia_acero")
    esh = _f(datos_acero, "def_inicio_endurecimiento")
    esu = _f(datos_acero, "def_ultima_acero")

    if tipo == "viga" and (modelo_cover == "mander_c" or modelo_core == "mander_c"):
        raise ValueError("Mander confinado no esta habilitado para vigas en esta integracion.")

    b, h, cover, core, As, P_real = _preparar_seccion(datos_seccion, datos_fibras, tipo, eje)
    if tipo != "columna":
        P_real = P

    datos_h = None
    ecu_confinada = None
    fcc_confinada = None
    if tipo == "columna" and (modelo_cover == "mander_c" or modelo_core == "mander_c"):
        datos_h = _datos_h_mander_confinado(datos_hormigon, datos_acero, datos_seccion)
        ecu_confinada = datos_h[11]
        fcc_confinada = datos_h[12]

    M, phi, c = diagrama_MC_unico(
        cover, core, As, tol, h, fc0, ec0, esp, Ec,
        fy, fsu, Es, ey, esh, esu, P_real,
        datos_h, sigma_hormigon(modelo_cover), sigma_hormigon(modelo_core)
    )

    phi_fin = phi * 100.0
    M_fin = M / 1e5

    try:
        parametros_mc = extraer_parametros_caracteristicos_mc(phi_fin, M_fin)
    except Exception as exc:
        parametros_mc = {
            "error": str(exc),
            "punto_final_analisis": {
                "phi": float(phi_fin[-1]) if len(phi_fin) else None,
                "M": float(M_fin[-1]) if len(M_fin) else None,
            },
        }

    if ecu_confinada is not None:
        parametros_mc["ecu_confinada"] = ecu_confinada
        parametros_mc["fcc_confinada"] = fcc_confinada

    return phi_fin, M_fin, c, parametros_mc


def calcular_series_mc(datos_hormigon, datos_acero, datos_seccion,
                       datos_fibras, tipo_seccion, eje):
    tipo = tipo_seccion.strip().lower()
    configs = [
        ("hognestad", "hognestad", "hognestad"),
        ("mander_no_conf", "mander_u", "mander_u"),
    ]
    if tipo == "columna":
        configs.append(("mander_conf", "mander_u", "mander_c"))

    series = {}
    parametros = {}
    for nombre, cover, core in configs:
        phi, M, _, p = calcular_momento_curvatura(
            datos_hormigon, datos_acero, datos_seccion, datos_fibras,
            tipo, eje, cover, core
        )
        series[nombre] = (phi, M)
        parametros[nombre] = p

    return series, parametros


def calcular_resultados_seccion(datos_hormigon, datos_acero, datos_seccion,
                                datos_fibras, tipo_seccion, eje):
    tipo = tipo_seccion.strip().lower()
    mc_series, mc_parametros = calcular_series_mc(
        datos_hormigon, datos_acero, datos_seccion, datos_fibras, tipo, eje
    )
    resultados = {
        "mc_matriz": None,
        "mc_series": mc_series,
        "mc_parametros": mc_parametros,
        "di_matriz": None,
        "di_series": {},
    }
    if tipo == "columna":
        di_matriz, di_series = calcular_series_di(datos_hormigon, datos_acero, datos_seccion, eje)
        resultados["di_matriz"] = di_matriz
        resultados["di_series"] = di_series
    return resultados
