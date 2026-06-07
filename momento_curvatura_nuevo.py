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


def sigma_hormigon(nombre_modelo):
    nombre = nombre_modelo.lower().strip()

    modelos_h = {
        "hognestad": hognestad,
        "mander_u": mander_u,
        "mander_c": mander_c,
    }

    return modelos_h[nombre]

def resultantes_hormigon(fibras, sigma_c, e0, phi, fc0, ec0, esp, Ec, datos_h):
    yi = fibras[:, 0]
    Ai = fibras[:, 1]

    ec = e0 - phi * yi
    sigma, Et = sigma_c(ec, fc0, ec0, esp, Ec, datos_h, 1)

    N = np.sum(sigma * Ai)
    M = np.sum(sigma * Ai * yi)

    return N, M, Et

def resultantes_acero(As, sigma_s, e0, phi, fy, fsu, Es, ey, esh, esu):
    yi = As[:, 0]
    Ai = As[:, 1]

    es = e0 - phi * yi
    sigma, Et = sigma_s(es, fy, fsu, Es, ey, esh, esu, 1)

    N = np.sum(sigma * Ai)
    M = np.sum(sigma * Ai * yi)

    return N, M, Et

def resultantes(e0, phi, cover, core, As, fc0, ec0, esp, Ec,
                fy, fsu, Es, ey, esh, esu, P, datos_h,
                sg_cover, sg_core):

    N_cover, M_cover, Kt_cover = resultantes_hormigon(cover, sg_cover, e0, phi, fc0, ec0, esp, Ec, datos_h)
    N_core, M_core, Kt_core = resultantes_hormigon(core, sg_core, e0, phi, fc0, ec0, esp, Ec, datos_h)
    N_steel, M_steel, Kt_steel = resultantes_acero(As, park, e0, phi, fy, fsu, Es, ey, esh, esu)

    N_int = N_cover + N_core + N_steel
    M_total = M_cover + M_core + M_steel

    R = N_int - P

    return R, M_total

def predecir_e0(phi_i, phi_prev, e0_prev,
                         cover, core, As,
                         fc0, ec0, esp, Ec,
                         fy, fsu, Es, ey, esh, esu,
                         datos_h, sg_cover, sg_core,
                         e0_min=None, e0_max=None):

    dphi = phi_i - phi_prev

    if abs(dphi) < 1e-12:
        return e0_prev

    # Deformaciones en el estado anterior
    ec_cover = e0_prev - phi_prev * cover[:, 0]
    ec_core = e0_prev - phi_prev * core[:, 0]
    es = e0_prev - phi_prev * As[:, 0]

    # Tangentes de materiales
    _, Et_cover = sg_cover(ec_cover, fc0, ec0, esp, Ec, datos_h, 1)
    _, Et_core = sg_core(ec_core, fc0, ec0, esp, Ec, datos_h, 1)
    _, Et_steel = park(es, fy, fsu, Es, ey, esh, esu, 1)

    # Rigideces tangentes de seccion
    EA = (
        np.sum(Et_cover * cover[:, 1]) +
        np.sum(Et_core * core[:, 1]) +
        np.sum(Et_steel * As[:, 1])
    )

    EAy = (
        np.sum(Et_cover * cover[:, 1] * cover[:, 0]) +
        np.sum(Et_core * core[:, 1] * core[:, 0]) +
        np.sum(Et_steel * As[:, 1] * As[:, 0])
    )

    if not np.isfinite(EA) or abs(EA) < 1e-12:
        return e0_prev

    de0 = (EAy / EA) * dphi

    if not np.isfinite(de0):
        return e0_prev

    e0_pred = e0_prev + de0

    if e0_min is not None and e0_max is not None:
        e0_pred = float(np.clip(e0_pred, e0_min, e0_max))

    return e0_pred

def momrot(phi, cover, core, As, tol, fc0, ec0, esp, Ec,
           fy, fsu, Es, ey, esh, esu,
           P, datos_h, sg_cover, sg_core,
           e0_ref=None,
           usar_brent_global=False):

    def N_equilibrio(e0):
        N = resultantes(e0, phi, cover, core, As, fc0, ec0, esp, Ec,
                        fy, fsu, Es, ey, esh, esu, P, datos_h,
                        sg_cover, sg_core)[0]
        return N

    def M_equilibrio(e0):
        M = resultantes(e0, phi, cover, core, As, fc0, ec0, esp, Ec,
                        fy, fsu, Es, ey, esh, esu, P, datos_h,
                        sg_cover, sg_core)[1]
        return M

    def limites_e0():
        y_all = np.concatenate([
            cover[:, 0],
            core[:, 0],
            As[:, 0]
        ])

        q = -phi * y_all

        if datos_h is not None and len(datos_h) > 11 and datos_h[11] is not None:
            ecu = datos_h[11]
            eps_min = -max(abs(esp), abs(ecu))
        else:
            eps_min = -abs(esp)

        eps_max = abs(esu)

        e0_min = eps_min - np.max(q)
        e0_max = eps_max - np.min(q)

        if e0_min > e0_max:
            e0_min, e0_max = e0_max, e0_min

        return e0_min, e0_max

    def dR_de0(e0):
        ec_cover = e0 - phi * cover[:, 0]
        ec_core = e0 - phi * core[:, 0]
        es = e0 - phi * As[:, 0]

        _, Et_cover = sg_cover(ec_cover, fc0, ec0, esp, Ec, datos_h, 1)
        _, Et_core = sg_core(ec_core, fc0, ec0, esp, Ec, datos_h, 1)
        _, Et_steel = park(es, fy, fsu, Es, ey, esh, esu, 1)

        Kt = (
            np.sum(Et_cover * cover[:, 1]) +
            np.sum(Et_core * core[:, 1]) +
            np.sum(Et_steel * As[:, 1])
        )

        return Kt

    def buscar_e0_brentq(a, b, npts, e0_obj):
        if a > b:
            a, b = b, a

        e0_vals = np.linspace(a, b, npts)
        R_vals = np.array([N_equilibrio(e0) for e0 in e0_vals], dtype=float)

        roots = []

        for i in range(npts - 1):
            e1 = e0_vals[i]
            e2 = e0_vals[i + 1]

            R1 = R_vals[i]
            R2 = R_vals[i + 1]

            if not np.isfinite(R1) or not np.isfinite(R2):
                continue

            if abs(R1) <= tol:
                roots.append(e1)
                continue

            if abs(R2) <= tol:
                roots.append(e2)
                continue

            if R1 * R2 < 0.0:
                try:
                    sol = root_scalar(
                        N_equilibrio,
                        bracket=[e1, e2],
                        method="brentq"
                    )

                    if sol.converged:
                        r = sol.root
                        if abs(N_equilibrio(r)) <= tol:
                            roots.append(r)

                except ValueError:
                    pass

        if not roots:
            return None

        # Eliminar raices repetidas
        roots = np.array(sorted(roots), dtype=float)
        roots_unicas = [roots[0]]

        for r in roots[1:]:
            if abs(r - roots_unicas[-1]) > 1e-12:
                roots_unicas.append(r)

        roots_unicas = np.array(roots_unicas, dtype=float)

        root = float(roots_unicas[np.argmin(np.abs(roots_unicas - e0_obj))])

        return root

    def buscar_e0_brentq_local(e0_min, e0_max, e0_obj):
        rango = e0_max - e0_min
        
        if rango <= 0.0:
            return None

        e0_obj = float(np.clip(e0_obj, e0_min, e0_max))

        ventanas = [
            0.01 * rango,
            0.02 * rango,
            0.05 * rango,
            0.10 * rango,
            0.20 * rango,
            0.40 * rango,
            0.70 * rango,
        ]

        for ancho in ventanas:
            a = max(e0_min, e0_obj - ancho)
            b = min(e0_max, e0_obj + ancho)

            root = buscar_e0_brentq(a, b, 101, e0_obj)

            if root is not None:
                return root

        return None

    def buscar_e0_brentq_global(e0_min, e0_max, e0_obj):
        return buscar_e0_brentq(e0_min, e0_max, 501, e0_obj)

    def buscar_e0_newton(e0_min, e0_max, e0_obj):
        rango = e0_max - e0_min

        if rango <= 0:
            return None

        e0 = float(np.clip(e0_obj, e0_min, e0_max))

        max_iter = 100
        max_step = 0.01 * rango

        for _itr in range(max_iter):
            R = N_equilibrio(e0)

            if not np.isfinite(R):
                break

            if abs(R) <= tol:
                return e0

            Kt = dR_de0(e0)

            if Kt is None or not np.isfinite(Kt) or abs(Kt) < 1e-12:
                break

            de0 = -R / Kt

            if not np.isfinite(de0):
                break

            de0 = float(np.clip(de0, -max_step, max_step))

            if abs(de0) < 1e-12:
                break

            R_abs = abs(R)
            aceptado = False

            for _ in range(20):
                e0_trial = e0 + de0
                e0_trial = float(np.clip(e0_trial, e0_min, e0_max))

                if abs(e0_trial - e0) < 1e-12:
                    break

                R_trial = N_equilibrio(e0_trial)

                if not np.isfinite(R_trial):
                    de0 *= 0.5
                    continue

                if abs(R_trial) <= tol:
                    return e0_trial

                if abs(R_trial) < R_abs:
                    e0 = e0_trial
                    aceptado = True
                    break

                de0 *= 0.50

            if not aceptado:
                break

        R_final = N_equilibrio(e0)

        if np.isfinite(R_final) and abs(R_final) <= tol:
            return e0

        return None

    e0_min, e0_max = limites_e0()

    if e0_ref is None:
        e0_obj = 0.0
    else:
        e0_obj = e0_ref

    e0_obj = float(np.clip(e0_obj, e0_min, e0_max))

    e0 = buscar_e0_newton(e0_min, e0_max, e0_obj)

    if e0 is None:
        e0 = buscar_e0_brentq_local(e0_min, e0_max, e0_obj)

    if e0 is None and usar_brent_global:
        e0 = buscar_e0_brentq_global(e0_min, e0_max, e0_obj)

    if e0 is None:
        return None, None

    M = M_equilibrio(e0)

    return M, e0

def diagrama_MC(cover, core, As, tol, fc0, ec0, esp, Ec,
                fy, fsu, Es, ey, esh, esu,
                P, datos_h, sg_cover, sg_core, n,
                phi_max=None,
                usar_brent_global=False):

    # Curvatura maxima predeterminada
    if phi_max is None:
        y_max = np.max(np.abs(As[:, 0]))
        phi_max = esu / y_max

    # Curvaturas calculadas
    a = phi_max / ((n - 1) * (1 + (n - 2) / 2 * (0.5)))
    b = 0.5 * a

    phi_vec = [0.0]

    for i in range(1, n):
        phi_i = i * a + i * (i - 1) / 2 * b
        phi_vec.append(phi_i)

    # Primer punto en phi = 0
    M_0, e0_0 = momrot(
        0.0,
        cover, core, As, tol, fc0, ec0, esp, Ec,
        fy, fsu, Es, ey, esh, esu,
        P, datos_h, sg_cover, sg_core,
        e0_ref=0.0,
        usar_brent_global=True
    )

    # Inicializar resultados
    phi_vals = [0.0]
    M_vals = [-M_0]
    e0_vals = [e0_0]
    c_vals = [0.0]
    es_vals = [0.0]
    ec_vals = [0.0]

    # Si la malla no es confinada, core viene vacio.
    # Para los valores auxiliares de deformacion de hormigon se usa cover.
    if core is not None and len(core) > 0:
        y_hormigon_ref = float(np.max(core[:, 0]))
    else:
        y_hormigon_ref = float(np.max(cover[:, 0]))

    # Recorrido incremental
    for phi_i in phi_vec[1:]:

        phi_prev = phi_vals[-1]
        e0_prev = e0_vals[-1]

        e0_ref = predecir_e0(
            phi_i, phi_prev, e0_prev,
            cover, core, As,
            fc0, ec0, esp, Ec,
            fy, fsu, Es, ey, esh, esu,
            datos_h, sg_cover, sg_core
        )

        M_i, e0_i = momrot(
            phi_i,
            cover, core, As, tol, fc0, ec0, esp, Ec,
            fy, fsu, Es, ey, esh, esu,
            P, datos_h, sg_cover, sg_core,
            e0_ref=e0_ref,
            usar_brent_global=usar_brent_global
        )

        if M_i is None:
            break

        M_i = -M_i

        if M_i < 0.0:
            break

        phi_vals.append(phi_i)
        M_vals.append(M_i)
        c_vals.append(e0_i/phi_i)
        e0_vals.append(e0_i)
        es_vals.append(e0_i + phi_i * max(As[:, 0]))
        ec_vals.append(e0_i - phi_i * y_hormigon_ref)


    return (
        np.array(M_vals, dtype=float),
        np.array(phi_vals, dtype=float),
        np.array(c_vals, dtype=float),
    )
    
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

MODELOS_HORMIGON = {
    "hognestad": hognestad,
    "mander_u": mander_u,
    "mander_c": mander_c,
}

_ACEROS_LEGACY = [
    (4587.156, 6095.8206, 2099898.063, 0.023, 0.13),
    (4794.0877, 6725.1784, 1997536.0, 0.0138, 0.1141),
    (4605.0, 7457.0, 2000000.0, 0.0139, 0.0809),
    (4577.0, 7491.0, 2000000.0, 0.0088, 0.1171),
]


def _f(datos, clave, default=None):
    valor = datos.get(clave, default)
    if valor is None or valor == "":
        raise ValueError(f"Falta el dato '{clave}'")
    return float(valor)


def _normalizar_texto(valor):
    return str(valor).strip().lower()


def _normalizar_tipo(tipo):
    t = _normalizar_texto(tipo)
    if "col" in t:
        return "columna"
    if "vig" in t:
        return "viga"
    raise ValueError(f"Tipo de seccion no valido: {tipo}")


def _normalizar_eje(eje):
    e = _normalizar_texto(eje)
    if e in ("x", "eje x", "direccion x", "dirección x") or e.endswith(" x"):
        return "x"
    if e in ("y", "eje y", "direccion y", "dirección y") or e.endswith(" y"):
        return "y"
    raise ValueError(f"Eje de analisis no valido: {eje}")


def _sigma_hormigon_seguro(nombre_modelo):
    nombre = _normalizar_texto(nombre_modelo)
    try:
        return MODELOS_HORMIGON[nombre]
    except KeyError as exc:
        raise ValueError(f"Modelo de hormigon no valido: {nombre_modelo}") from exc


def _malla_confinada(modelo_cover, modelo_core):

    modelo_cover = _normalizar_texto(modelo_cover)
    modelo_core = _normalizar_texto(modelo_core)

    return modelo_cover == "mander_c" or modelo_core == "mander_c"


def _datos_hormigon_legacy(datos_hormigon):
    fc0 = _f(datos_hormigon, "esfuerzo_fc")
    esp = _f(datos_hormigon, "def_ultima_sin_confinar")
    Ec = 15100.0 * fc0 ** 0.5
    ec0 = 2.0 * fc0 / Ec
    return fc0, ec0, esp, Ec


def _datos_acero_legacy(datos_acero):
    fy = _f(datos_acero, "esfuerzo_fy")
    fsu = _f(datos_acero, "esfuerzo_ultimo_acero")
    Es = _f(datos_acero, "modulo_Es")
    esh = _f(datos_acero, "def_inicio_endurecimiento")
    esu = _f(datos_acero, "def_ultima_acero")

    for fy0, fsu0, Es0, esh0, esu0 in _ACEROS_LEGACY:
        if (abs(fy - fy0) <= 1e-2 and
            abs(fsu - fsu0) <= 1e-2 and
            abs(Es - Es0) <= 1e-1 and
            abs(esh - esh0) <= 1e-8 and
            abs(esu - esu0) <= 1e-8):
            fy, fsu, Es, esh, esu = fy0, fsu0, Es0, esh0, esu0
            break

    ey = fy / Es
    return fy, fsu, Es, ey, esh, esu


def _datos_columna(datos_seccion):
    b = _f(datos_seccion, "disenar_columna_base")
    h = _f(datos_seccion, "disenar_columna_altura")
    r = _f(datos_seccion, "disenar_columna_recubrimiento")
    nb_x = int(_f(datos_seccion, "disenar_columna_varillasX_2"))
    nb_y = int(_f(datos_seccion, "disenar_columna_varillasY_2"))
    de = _f(datos_seccion, "disenar_columna_diametro_transversal") / 10.0
    Sc = _f(datos_seccion, "disenar_columna_espaciamiento")
    d_edge = _f(datos_seccion, "disenar_columna_diametro_longitudinal_2") / 10.0
    d_corner = _f(datos_seccion, "disenar_columna_diametro_longitudinal_esq") / 10.0
    nr_x = int(_f(datos_seccion, "disenar_columna_ramalesX"))
    nr_y = int(_f(datos_seccion, "disenar_columna_ramalesY"))
    P = _f(datos_seccion, "disenar_columna_axial", 0.0)
    nb = (nb_x - 2) * 2 + nb_y * 2
    return b, h, r, nb_x, nb_y, de, Sc, d_edge, d_corner, nr_x, nr_y, P, nb


def _preparar_columna(datos_seccion, datos_fibras, eje, conf_malla):
    nf_x = int(_f(datos_fibras, "fibras_x"))
    nf_y = int(_f(datos_fibras, "fibras_y"))
    b, h, r, nb_x, nb_y, de, Sc, d_edge, d_corner, nr_x, nr_y, P, nb = _datos_columna(datos_seccion)
    As_malla = barras_columna(b, h, r, de, nb_x, nb_y, d_corner, d_edge, eje, False)
    cover, core = malla(b, h, r, de, nf_x, nf_y, eje, As_malla, conf_malla, True)
    As = barras_columna(b, h, r, de, nb_x, nb_y, d_corner, d_edge, eje, True)
    return cover, core, As, P, (b, h, r, de, Sc, d_corner, d_edge, nb, nr_x, nr_y)


def _preparar_viga(datos_seccion, datos_fibras, eje, conf_malla=False):
    nf_x = int(_f(datos_fibras, "fibras_x"))
    nf_y = int(_f(datos_fibras, "fibras_y"))
    b = _f(datos_seccion, "disenar_viga_base")
    h = _f(datos_seccion, "disenar_viga_altura")
    r = _f(datos_seccion, "disenar_viga_recubrimiento")
    de = _f(datos_seccion, "disenar_viga_diametro_transversal") / 10.0
    nb_sup = int(_f(datos_seccion, "disenar_viga_varillas_superior"))
    nb_inf = int(_f(datos_seccion, "disenar_viga_varillas_inferior"))
    d_sup = _f(datos_seccion, "disenar_viga_diametro_superior") / 10.0
    d_inf = _f(datos_seccion, "disenar_viga_diametro_inferior") / 10.0

    As_malla = barras_viga(b, h, r, de, nb_sup, nb_inf, d_sup, d_inf, eje, False)
    cover, core = malla(b, h, r, de, nf_x, nf_y, eje, As_malla, conf_malla, True)
    As = barras_viga(b, h, r, de, nb_sup, nb_inf, d_sup, d_inf, eje, True)
    return cover, core, As, 0.0, None


def _datos_h_inicial_columna(fy, datos_base_columna, esp):
    b, h, r, de, Sc, d_corner, d_edge, nb, nr_x, nr_y = datos_base_columna
    ecu = None
    fcc = None
    return (fy, b, h, r, Sc, de, d_corner, d_edge, nb, nr_x, nr_y, ecu, fcc)


def _datos_h_mander_columna(fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, datos_base_columna):
    datos_h = _datos_h_inicial_columna(fy, datos_base_columna, esp)
    ecu = buscar_ecu(fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, datos_h)

    b, h, r, de, Sc, d_corner, d_edge, nb, nr_x, nr_y = datos_base_columna
    fcc = None
    datos_h = (fy, b, h, r, Sc, de, d_corner, d_edge, nb, nr_x, nr_y, ecu, fcc)
    fcc = mander_c(0, fc0, ec0, esp, Ec, datos_h, 3)
    datos_h = (fy, b, h, r, Sc, de, d_corner, d_edge, nb, nr_x, nr_y, ecu, fcc)
    return datos_h, ecu, fcc


def calcular_momento_curvatura(datos_hormigon, datos_acero, datos_seccion,
                               datos_fibras, tipo_seccion, eje,
                               modelo_cover, modelo_core, P=0.0, tol=1e-3, n=100):
    tipo = _normalizar_tipo(tipo_seccion)
    eje = _normalizar_eje(eje)
    modelo_cover = _normalizar_texto(modelo_cover)
    modelo_core = _normalizar_texto(modelo_core)

    fc0, ec0, esp, Ec = _datos_hormigon_legacy(datos_hormigon)
    fy, fsu, Es, ey, esh, esu = _datos_acero_legacy(datos_acero)

    if tipo == "viga" and (modelo_cover == "mander_c" or modelo_core == "mander_c"):
        raise ValueError("Mander confinado no esta habilitado para vigas en esta integracion.")

    conf_malla = _malla_confinada(modelo_cover, modelo_core)

    if tipo == "columna":
        cover, core, As, P_real, datos_base_columna = _preparar_columna(
            datos_seccion, datos_fibras, eje, conf_malla
        )
    else:
        cover, core, As, P_real, datos_base_columna = _preparar_viga(
            datos_seccion, datos_fibras, eje, conf_malla
        )
        P_real = P

    datos_h = None
    ecu_diagrama = esp
    fcc_confinada = None

    if tipo == "columna":
        datos_h = _datos_h_inicial_columna(fy, datos_base_columna, esp)
        if modelo_cover == "mander_c" or modelo_core == "mander_c":
            datos_h, ecu_diagrama, fcc_confinada = _datos_h_mander_columna(
                fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, datos_base_columna
            )
    else:
        datos_h = None
        ecu_diagrama = esp

    M, phi, c = diagrama_MC(
        cover, core, As, tol, fc0, ec0, esp, Ec,
        fy, fsu, Es, ey, esh, esu,
        P_real, datos_h,
        _sigma_hormigon_seguro(modelo_cover),
        _sigma_hormigon_seguro(modelo_core),
        n
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

    if fcc_confinada is not None:
        parametros_mc["ecu_confinada"] = float(ecu_diagrama)
        parametros_mc["fcc_confinada"] = float(fcc_confinada)

    return phi_fin, M_fin, c, parametros_mc


def calcular_series_mc(datos_hormigon, datos_acero, datos_seccion,
                       datos_fibras, tipo_seccion, eje):
    tipo = _normalizar_tipo(tipo_seccion)
    eje = _normalizar_eje(eje)
    configs = [
        ("hognestad", "hognestad", "hognestad"),
        ("mander_no_conf", "mander_u", "mander_u"),
    ]
    if tipo == "columna":
        configs.append(("mander_conf", "mander_u", "mander_c"))

    series = {}
    parametros = {}
    for nombre, cover_model, core_model in configs:
        phi, M, _, p = calcular_momento_curvatura(
            datos_hormigon, datos_acero, datos_seccion, datos_fibras,
            tipo, eje, cover_model, core_model
        )
        series[nombre] = (phi, M)
        parametros[nombre] = p

    return series, parametros


def calcular_resultados_seccion(datos_hormigon, datos_acero, datos_seccion,
                                datos_fibras, tipo_seccion, eje):
    tipo = _normalizar_tipo(tipo_seccion)
    eje = _normalizar_eje(eje)
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

def diagrama_MC_unico(cover, core, As, tol, fc0, ec0, esp, Ec,
                      fy, fsu, Es, ey, esh, esu,
                      P, datos_h, sg_cover, sg_core, n=100, ecu=None):
    return diagrama_MC(
        cover, core, As, tol, fc0, ec0, esp, Ec,
        fy, fsu, Es, ey, esh, esu,
        P, datos_h, sg_cover, sg_core, n
    )
