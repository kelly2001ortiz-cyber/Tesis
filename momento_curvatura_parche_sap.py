import numpy as np
from scipy.optimize import root_scalar
from materiales import modelos
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

# Resultantes del hormigon
def resultantes_hormigon(fibras, sigma_c, c, phi, fc0, ec0, esp, Ec, datos_h):
    yi = fibras[:, 0]
    Ai = fibras[:, 1]
    ec = -phi * (yi - c)
    sigma = sigma_c(ec, fc0, ec0, esp, Ec, datos_h, 1)
    N = np.sum(sigma * Ai)
    M = np.sum(sigma * Ai * yi)
    return N, M

# Resultantes del acero
def resultantes_acero(As, sigma_s, c, phi, fy, fsu, Es, ey, esh, esu):
    yi = As[:, 0]
    Ai = As[:, 1]
    es = -phi * (yi - c)
    sigma = sigma_s(es, fy, fsu, Es, ey, esh, esu)
    N = np.sum(sigma * Ai)
    M = np.sum(sigma * Ai * yi)
    return N, M

# Suma de resultantes de los materiales
def resultantes(c, phi, cover, core, As, fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core):
    N_uc, M_uc = resultantes_hormigon(cover, sg_cover, c, phi, fc0, ec0, esp, Ec, datos_h)
    N_cc, M_cc = resultantes_hormigon(core, sg_core, c, phi, fc0, ec0, esp, Ec, datos_h)
    N_s, M_s = resultantes_acero(As, park, c, phi, fy, fsu, Es, ey, esh, esu)

    N_total = N_uc + N_cc + N_s - P
    M_total = M_uc + M_cc + M_s
    return N_total, M_total

# Funcion para encontrar la distancia al eje neutro
def momrot(c_min, c_max, phi, cover, core, As, tol, h, fc0, ec0, esp, Ec,
           fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core, c_prev=None, phi_prev=None):

    def N_equilibrio(c):
        N = resultantes(c, phi, cover, core, As, fc0, ec0, esp, Ec,
                        fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core)[0]
        return N

    def es_max(c_eval, phi_eval):
        yi = As[:, 0]
        e_s = -phi_eval * (yi - c_eval)
        es_validas = e_s[np.abs(e_s) < esu]
        es = np.max(abs(es_validas)) if len(es_validas) else -np.inf
        return es

    def ordenar_por_continuidad(roots):
        roots = np.unique(np.asarray(roots, dtype=float)).tolist()
        if c_prev is None or not roots:
            return roots
        return sorted(roots, key=lambda x: abs(x - c_prev))

    def filtrar_por_continuidad(roots, es_prev):
        roots = ordenar_por_continuidad(roots)
        if not roots:
            return []

        # Mantener continuidad de rama, pero sin bloquear la convergencia
        # cuando la deformación de referencia deja de ser informativa.
        if (not np.isfinite(es_prev)) or es_prev <= 0.0:
            return roots

        raices_filtradas = []
        for c_root in roots:
            es = es_max(c_root, phi)
            if es >= 0.85 * es_prev:
                raices_filtradas.append(c_root)

        # Si ninguna raíz pasa el filtro heurístico, volver a priorizar
        # únicamente la continuidad geométrica para no perder la solución.
        return raices_filtradas if raices_filtradas else roots

    def encontrar_raices(a, b, npts):
        c_vals = np.linspace(a, b, npts)
        N_vals = np.fromiter((N_equilibrio(c) for c in c_vals), dtype=float, count=npts)
        roots = []

        idx_signo = np.flatnonzero(N_vals[:-1] * N_vals[1:] < 0.0)
        idx_cero = np.flatnonzero(np.abs(N_vals[:-1]) < tol)
        idxs = np.unique(np.concatenate((idx_cero, idx_signo)))

        for i in idxs:
            c1 = c_vals[i]
            c2 = c_vals[i + 1]
            N1 = N_vals[i]
            N2 = N_vals[i + 1]

            if abs(N1) < tol:
                roots.append(c1)
            elif N1 * N2 < 0.0:
                try:
                    sol = root_scalar(N_equilibrio, bracket=[c1, c2], method="brentq")
                    if sol.converged and abs(N_equilibrio(sol.root)) <= tol:
                        roots.append(sol.root)
                except ValueError:
                    pass
        if not roots:
            return []
        return np.unique(np.array(roots, dtype=float)).tolist()

    def barrido_global():
        # No restringir el eje neutro al espesor de la sección: con carga axial,
        # el eje neutro puede quedar fuera y la solución sigue siendo físicamente válida.
        rangos = [
            (c_min, c_max, 80),
            (-1.5 * h, 1.5 * h, 120),
            (-3.0 * h, 3.0 * h, 180),
            (-6.0 * h, 6.0 * h, 260),
            (-12.0 * h, 12.0 * h, 360),
        ]
        for a, b, npts in rangos:
            roots = encontrar_raices(a, b, npts=npts)
            if roots:
                return ordenar_por_continuidad(roots)
        return []

    def buscar_c():
        # Primer punto: explorar en un rango amplio para capturar soluciones con axial.
        if c_prev is None:
            return barrido_global()

        es_prev = es_max(c_prev, phi_prev)

        # Primero intentar alrededor de la raíz previa, priorizando continuidad.
        ventanas = [0.02*h, 0.04*h, 0.08*h, 0.15*h, 0.35*h, 0.75*h, 1.50*h, 3.0*h]

        for dc in ventanas:
            a = c_prev - dc
            b = c_prev + dc
            roots = encontrar_raices(a, b, npts=60)
            roots = filtrar_por_continuidad(roots, es_prev)
            if roots:
                return roots

        # Si falla la búsqueda local, hacer un barrido global amplio.
        roots = barrido_global()
        roots = filtrar_por_continuidad(roots, es_prev)
        if roots:
            return roots

        return []

    c_posibles = buscar_c()
    if not c_posibles:
        return None, None

    c = c_posibles[0] if c_prev is None else min(c_posibles, key=lambda x: abs(x - c_prev))
    M = resultantes(c, phi, cover, core, As, fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core)[1]
    return M, c

# Funcion para obtener el diagrama momento-curvatura
def diagrama_MC(cover, core, As, tol, h, fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core):
    
    dphi_min, dphi_max = 2e-8, 5e-5
    phi_ini, dphi_ini = 2e-5, 1e-6

    phi_vals = [0.0]
    M_vals = [0.0]
    c_vals = [0.0]

    phi = phi_ini
    dphi = dphi_ini
    c_min = -h / 2
    c_max = h / 2
    c_prev = None
    phi_prev = None
    Mmax = 0.0
    post_pico = False
    pts_extra = None
    n_pts_extra = 10  # Aumentado de 4 a 10 para garantizar más puntos post-pico
    fallos_consecutivos = 0
    max_fallos = 50  # Límite de fallos consecutivos antes de reducir paso más agresivamente

    for _ in range(2000):  # Aumentado de 1000 a 2000 para más iteraciones
        Mi, ci = momrot(c_min, c_max, phi, cover, core, As, tol, h, fc0, ec0, esp, Ec,
                        fy, fsu, Es, ey, esh, esu, P, datos_h, sg_cover, sg_core, c_prev, phi_prev)

        # No hay solucion de equilibrio: falla numerica/fisica.
        # Si falla, probar reduciendo paso antes de salir.
        if Mi is None:
            fallos_consecutivos += 1
            if fallos_consecutivos > max_fallos:
                # Si hay demasiados fallos, salir
                break
            if dphi > dphi_min:
                dphi = max(0.50 * dphi, dphi_min)  # Reducción más agresiva
                # Reintentar desde el último estado convergido, no en el mismo punto fallido.
                if phi_prev is None:
                    phi = max(0.50 * phi, dphi_min)
                else:
                    phi = phi_prev + dphi
                continue
            break

        Mi = -Mi
        fallos_consecutivos = 0  # Reiniciar contador de fallos

        # Guardar resultados
        phi_vals.append(phi)
        M_vals.append(Mi)
        c_vals.append(ci)

        # Actualizar momento maximo
        if Mi > Mmax:
            Mmax = Mi
        elif Mi < 0.90 * Mmax:
            post_pico = True

        # Control post-pico
        if post_pico and Mi < 0.70 * Mmax:
            dphi = max(0.80 * dphi, dphi_min)
            if pts_extra is None:
                pts_extra = n_pts_extra
            pts_extra -= 1
            if pts_extra < 0:
                break

        # Adaptacion del paso
        if len(M_vals) >= 2:
            dM = abs(M_vals[-1] - M_vals[-2]) / max(abs(Mmax), 1e-6)
            if dM > 0.05:
                dphi = max(0.5 * dphi, dphi_min)
            elif dM < 0.01:
                dphi = min(1.2 * dphi, dphi_max)

        c_prev = ci
        phi_prev = phi
        phi += dphi

    return np.array(M_vals, dtype=float), np.array(phi_vals, dtype=float), np.array(c_vals, dtype=float)

# =========================
# Postproceso M-φ
# =========================

def _limpiar_curva_mc(phi, M):
    phi = np.asarray(phi, dtype=float).ravel()
    M = np.asarray(M, dtype=float).ravel()

    mask = np.isfinite(phi) & np.isfinite(M)
    phi = phi[mask]
    M = M[mask]

    if len(phi) == 0:
        raise ValueError("La curva momento-curvatura está vacía.")

    # Ordenar por curvatura
    idx = np.argsort(phi)
    phi = phi[idx]
    M = M[idx]

    # Eliminar duplicados de phi conservando el último
    # Usar tolerancia relativa para evitar eliminar puntos muy cercanos
    phi_range = np.ptp(phi) if len(phi) > 1 else max(abs(phi[0]), 1.0)
    tol_duplicados = max(1e-12, 1e-10 * phi_range)  # Tolerancia adaptativa
    
    indices_validos = [0]
    for i in range(1, len(phi)):
        if abs(phi[i] - phi[indices_validos[-1]]) > tol_duplicados:
            indices_validos.append(i)
    
    phi = phi[indices_validos]
    M = M[indices_validos]

    # Asegurar punto inicial
    if phi[0] > 0.0:
        phi = np.insert(phi, 0, 0.0)
        M = np.insert(M, 0, 0.0)

    return phi, M


def _ajuste_lineal_por_origen(x, y):
    """
    Ajuste lineal M = K * phi forzado a pasar por el origen.
    """
    den = np.dot(x, x)
    if den <= 0:
        return 0.0, 0.0

    K = np.dot(x, y) / den
    y_hat = K * x

    ss_res = np.sum((y - y_hat) ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)

    if ss_tot <= 0:
        r2 = 1.0
    else:
        r2 = 1.0 - ss_res / ss_tot

    return float(K), float(r2)


def _rigidez_inicial_desde_tabla(phi, M, min_pts=4, r2_min=0.999):
    """
    Busca la mayor porción inicial de la curva que siga siendo casi lineal,
    y devuelve su pendiente como rigidez inicial.
    """
    n = len(phi)
    if n < 2:
        raise ValueError("No hay suficientes puntos para calcular la rigidez inicial.")

    mejor_K = None

    # Se recorre progresivamente la rama inicial
    for i in range(max(min_pts, 2), n + 1):
        x = phi[:i]
        y = M[:i]

        # Debe ser monótona creciente en el tramo inicial
        if np.any(np.diff(y) < 0):
            break

        K, r2 = _ajuste_lineal_por_origen(x, y)

        if K <= 0:
            break

        if r2 >= r2_min:
            mejor_K = K
        else:
            break

    if mejor_K is not None:
        return float(mejor_K)

    # Fallback: usar los primeros puntos disponibles
    i = min(max(min_pts, 2), n)
    K, _ = _ajuste_lineal_por_origen(phi[:i], M[:i])
    return float(K)


def _interp_lineal_xy(x, y, xq):
    return float(np.interp(float(xq), x, y))

def _buscar_punto_falla_por_resistencia(phi, M, idx_max, fraccion=0.80):
    """
    Busca el punto de falla como el primer punto de la rama descendente
    donde M <= fraccion * M_max.

    Si encuentra cruce, interpola linealmente para obtener phi_f.
    Si no encuentra cruce, usa el último punto disponible como fallback.
    """
    phi = np.asarray(phi, dtype=float)
    M = np.asarray(M, dtype=float)

    M_max = float(M[idx_max])
    M_lim = fraccion * M_max

    # Si no hay rama descendente, fallback
    if idx_max >= len(M) - 1:
        return float(phi[-1]), float(M[-1]), False

    # Recorrer solo post-pico
    for i in range(idx_max + 1, len(M)):
        if M[i] <= M_lim:
            # Si justo cayó en el punto i
            if i == idx_max + 1:
                phi_f = float(phi[i])
                return phi_f, float(M_lim), True

            # Interpolar entre (i-1) e i
            phi1, M1 = float(phi[i - 1]), float(M[i - 1])
            phi2, M2 = float(phi[i]), float(M[i])

            if abs(M2 - M1) < 1e-14:
                phi_f = phi2
            else:
                phi_f = phi1 + (M_lim - M1) * (phi2 - phi1) / (M2 - M1)

            return float(phi_f), float(M_lim), True

    # Si nunca bajó al 80% del pico
    return float(phi[-1]), float(M[-1]), False


def extraer_parametros_caracteristicos_mc(phi, M):
    """
    Extrae parámetros característicos directamente de la tabla M-φ.

    Criterios adoptados:
    - rigidez inicial: pendiente de la rama inicial lineal
    - punto de fluencia: fluencia equivalente por bilinealización
    - punto máximo: máximo momento de la tabla
    - punto de falla: primer punto post-pico donde M <= 0.80*Mmax
    - ductilidad: phi_f / phi_y
    """
    phi, M = _limpiar_curva_mc(phi, M)

    if len(phi) < 2:
        raise ValueError("No hay suficientes puntos en la tabla M-φ (mínimo 2).")
    
    # Si hay menos de 4 puntos, usar procedimiento simplificado
    usar_simplificado = len(phi) < 4
    if usar_simplificado:
        import warnings
        warnings.warn(f"Curva M-φ con solo {len(phi)} puntos. Usando procedimiento simplificado para extraer parámetros.")

    # Punto máximo
    idx_max = int(np.argmax(M))
    phi_max = float(phi[idx_max])
    M_max = float(M[idx_max])

    # Rigidez inicial a partir de la rama inicial
    try:
        K_ini = _rigidez_inicial_desde_tabla(phi[:idx_max + 1], M[:idx_max + 1])
    except:
        # Si falla, calcular simplemente como M_max / phi_max
        K_ini = M_max / phi_max if phi_max > 0 else 1.0

    # Punto final del análisis (solo informativo)
    phi_fin = float(phi[-1])
    M_fin = float(M[-1])

    # Punto de falla por caída al 80% de la resistencia máxima
    try:
        phi_f, M_f, hubo_cruce_80 = _buscar_punto_falla_por_resistencia(
            phi, M, idx_max, fraccion=0.80
        )
    except:
        # Fallback: usar el último punto como falla
        phi_f = float(phi[-1])
        M_f = float(M[-1])
        hubo_cruce_80 = False

    # Área bajo la curva hasta el punto de falla
    phi_area = phi[phi <= phi_f]
    M_area = M[:len(phi_area)]

    # Si phi_f quedó entre dos puntos, agregarlo por interpolación
    if len(phi_area) == 0 or abs(phi_area[-1] - phi_f) > 1e-12:
        M_phi_f = _interp_lineal_xy(phi, M, phi_f)
        phi_area = np.append(phi_area, phi_f)
        M_area = np.append(M_area, M_phi_f)

    A = float(np.trapz(M_area, phi_area))

    # Fluencia equivalente por idealización bilineal
    if usar_simplificado:
        # Para curvas con pocos puntos, usar valor conservador
        phi_y = phi_max * 0.50  # 50% del punto máximo
    else:
        denom = K_ini * phi_f - M_f
        if denom <= 1e-12:
            phi_y = phi_max * 0.60
        else:
            phi_y = (2.0 * A - M_f * phi_f) / denom

    phi_y = float(np.clip(phi_y, 1e-12, min(phi_f * 0.999, phi_max)))
    M_y = _interp_lineal_xy(phi, M, phi_y)

    # Ductilidad por curvatura
    mu_phi = float(phi_f / phi_y) if phi_y > 0 else np.inf

    if hubo_cruce_80:
        criterio_falla = (
            "Punto de falla definido como el primer punto post-pico "
            "en que la resistencia desciende al 80% del momento máximo."
        )
    else:
        if usar_simplificado:
            criterio_falla = (
                "Curva con pocos puntos: se adoptó el último punto disponible "
                "como punto de falla (fallback simplificado)."
            )
        else:
            criterio_falla = (
                "La curva no descendió hasta el 80% del momento máximo; "
                "se adoptó el último punto disponible del análisis como fallback."
            )

    return {
        "rigidez_inicial": K_ini,
        "punto_fluencia": {"phi": phi_y, "M": M_y},
        "punto_maximo": {"phi": phi_max, "M": M_max},
        "punto_falla": {"phi": phi_f, "M": M_f},
        "punto_final_analisis": {"phi": phi_fin, "M": M_fin},
        "ductilidad_curvatura": mu_phi,
        "area_bajo_curva": A,
        "criterio_fluencia": (
            "Curvatura de fluencia equivalente obtenida por idealización "
            "bilineal de la curva M-φ."
        ),
        "criterio_falla": criterio_falla,
    }
    
def _f(datos, clave, default=None):
    valor = datos.get(clave, default)
    if valor is None or valor == "":
        raise ValueError(f"Falta el dato '{clave}'")
    return float(valor)


def _datos_h_mander_confinado(datos_hormigon, datos_acero, datos_seccion):
    fc0 = _f(datos_hormigon, "esfuerzo_fc")
    Ec  = _f(datos_hormigon, "modulo_Ec")
    ec0 = _f(datos_hormigon, "def_max_sin_confinar")
    esp = _f(datos_hormigon, "def_ultima_sin_confinar")

    fy  = _f(datos_acero, "esfuerzo_fy")
    fsu = _f(datos_acero, "esfuerzo_ultimo_acero")
    Es  = _f(datos_acero, "modulo_Es")
    ey  = _f(datos_acero, "def_fluencia_acero")
    esh = _f(datos_acero, "def_inicio_endurecimiento")
    esu = _f(datos_acero, "def_ultima_acero")

    b        = _f(datos_seccion, "disenar_columna_base")
    h        = _f(datos_seccion, "disenar_columna_altura")
    r        = _f(datos_seccion, "disenar_columna_recubrimiento")
    Sc       = _f(datos_seccion, "disenar_columna_espaciamiento")
    de       = _f(datos_seccion, "disenar_columna_diametro_transversal") / 10.0
    d_edge   = _f(datos_seccion, "disenar_columna_diametro_longitudinal_2") / 10.0
    d_corner = _f(datos_seccion, "disenar_columna_diametro_longitudinal_esq") / 10.0
    nl_x     = int(_f(datos_seccion, "disenar_columna_ramalesX"))
    nl_y     = int(_f(datos_seccion, "disenar_columna_ramalesY"))
    nb_x     = int(_f(datos_seccion, "disenar_columna_varillasX_2"))
    nb_y     = int(_f(datos_seccion, "disenar_columna_varillasY_2"))
    nb       = 2 * (nb_x - 2) + 2 * nb_y

    fyh = fy

    datos_h_base = (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nl_x, nl_y, None, None)

    fcc = mander_c(
        ec=np.array([0.0]),
        fc0=fc0,
        ec0=ec0,
        esp=esp,
        Ec=Ec,
        datos_h=datos_h_base,
        N=3,
    )

    datos_h_ecu = (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nl_x, nl_y, None, fcc)

    ecu = buscar_ecu(
        fc0=fc0,
        ec0=ec0,
        esp=esp,
        Ec=Ec,
        fy=fy,
        fsu=fsu,
        Es=Es,
        ey=ey,
        esh=esh,
        esu=esu,
        datos_h=datos_h_ecu,
    )

    return (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nl_x, nl_y, ecu, fcc)


def calcular_momento_curvatura(
    datos_hormigon,
    datos_acero,
    datos_seccion,
    datos_fibras,
    tipo_seccion,
    eje,
    modelo_cover,
    modelo_core,
    P=0.0,
    tol=1e-5,
):
    tipo = tipo_seccion.strip().lower()
    eje = eje.strip().lower()
    modelo_cover = modelo_cover.strip().lower()
    modelo_core = modelo_core.strip().lower()
    usa_mander_c = (modelo_cover == "mander_c" or modelo_core == "mander_c")

    # Materiales
    fc0 = _f(datos_hormigon, "esfuerzo_fc")
    Ec  = _f(datos_hormigon, "modulo_Ec")
    ec0 = _f(datos_hormigon, "def_max_sin_confinar")
    esp = _f(datos_hormigon, "def_ultima_sin_confinar")

    fy  = _f(datos_acero, "esfuerzo_fy")
    fsu = _f(datos_acero, "esfuerzo_ultimo_acero")
    Es  = _f(datos_acero, "modulo_Es")
    ey  = _f(datos_acero, "def_fluencia_acero")
    esh = _f(datos_acero, "def_inicio_endurecimiento")
    esu = _f(datos_acero, "def_ultima_acero")

    # Fibras
    nf_x = int(_f(datos_fibras, "fibras_x"))
    nf_y = int(_f(datos_fibras, "fibras_y"))

    # Modelos constitutivos
    sg_cover = sigma_hormigon(modelo_cover)
    sg_core = sigma_hormigon(modelo_core)

    datos_h = None

    if tipo == "columna":
        b        = _f(datos_seccion, "disenar_columna_base")
        h        = _f(datos_seccion, "disenar_columna_altura")
        r        = _f(datos_seccion, "disenar_columna_recubrimiento")
        de       = _f(datos_seccion, "disenar_columna_diametro_transversal") / 10.0
        nb_x     = int(_f(datos_seccion, "disenar_columna_varillasX_2"))
        nb_y     = int(_f(datos_seccion, "disenar_columna_varillasY_2"))
        d_edge   = _f(datos_seccion, "disenar_columna_diametro_longitudinal_2") / 10.0
        d_corner = _f(datos_seccion, "disenar_columna_diametro_longitudinal_esq") / 10.0

        cover, core = malla(b, h, r, de, nf_x, nf_y, eje)
        As = barras_columna(b, h, r, de, nb_x, nb_y, d_corner, d_edge, eje)

        P_real = _f(datos_seccion, "disenar_columna_axial", P)

        if usa_mander_c:
            datos_h = _datos_h_mander_confinado(datos_hormigon, datos_acero, datos_seccion)

    elif tipo == "viga":
        b      = _f(datos_seccion, "disenar_viga_base")
        h      = _f(datos_seccion, "disenar_viga_altura")
        r      = _f(datos_seccion, "disenar_viga_recubrimiento")
        de     = _f(datos_seccion, "disenar_viga_diametro_transversal") / 10.0
        nb_sup = int(_f(datos_seccion, "disenar_viga_varillas_superior"))
        nb_inf = int(_f(datos_seccion, "disenar_viga_varillas_inferior"))
        d_sup  = _f(datos_seccion, "disenar_viga_diametro_superior") / 10.0
        d_inf  = _f(datos_seccion, "disenar_viga_diametro_inferior") / 10.0

        cover, core = malla(b, h, r, de, nf_x, nf_y, "x")
        As = barras_viga(h, r, de, nb_sup, nb_inf, d_sup, d_inf)

        P_real = P

        if usa_mander_c:
            raise ValueError("Mander confinado no está habilitado para vigas en esta integración.")

    else:
        raise ValueError(f"Tipo de sección no válido: {tipo_seccion}")

    M, phi, c = diagrama_MC(
        cover, core, As, tol, h,
        fc0, ec0, esp, Ec,
        fy, fsu, Es, ey, esh, esu,
        P_real, datos_h, sg_cover, sg_core,
    )

    phi_fin = phi * 100.0
    M_fin = M / 1e5

    try:
        parametros_mc = extraer_parametros_caracteristicos_mc(phi_fin, M_fin)
    except Exception as e:
        parametros_mc = {
            "error": str(e),
            "punto_final_analisis": {
                "phi": float(phi_fin[-1]) if len(phi_fin) else None,
                "M": float(M_fin[-1]) if len(M_fin) else None,
            },
        }

    return phi_fin, M_fin, c, parametros_mc

def calcular_series_mc(
    datos_hormigon,
    datos_acero,
    datos_seccion,
    datos_fibras,
    tipo_seccion,
    eje,
):
    tipo = tipo_seccion.strip().lower()

    series = {}
    parametros = {}

    phi, M, _, p = calcular_momento_curvatura(
        datos_hormigon, datos_acero, datos_seccion, datos_fibras,
        tipo, eje, "hognestad", "hognestad"
    )
    series["hognestad"] = (phi, M)
    parametros["hognestad"] = p

    phi, M, _, p = calcular_momento_curvatura(
        datos_hormigon, datos_acero, datos_seccion, datos_fibras,
        tipo, eje, "mander_u", "mander_u"
    )
    series["mander_no_conf"] = (phi, M)
    parametros["mander_no_conf"] = p

    if tipo == "columna":
        phi, M, _, p = calcular_momento_curvatura(
            datos_hormigon, datos_acero, datos_seccion, datos_fibras,
            tipo, eje, "mander_u", "mander_c"
        )
        series["mander_conf"] = (phi, M)
        parametros["mander_conf"] = p

    return series, parametros

def calcular_resultados_seccion(
    datos_hormigon,
    datos_acero,
    datos_seccion,
    datos_fibras,
    tipo_seccion,
    eje,
):
    tipo = tipo_seccion.strip().lower()

    mc_series, mc_parametros = calcular_series_mc(
        datos_hormigon=datos_hormigon,
        datos_acero=datos_acero,
        datos_seccion=datos_seccion,
        datos_fibras=datos_fibras,
        tipo_seccion=tipo,
        eje=eje,
    )

    resultados = {
        "mc_matriz": None,
        "mc_series": mc_series,
        "mc_parametros": mc_parametros,
        "di_matriz": None,
        "di_series": {},
    }

    if tipo == "columna":
        di_matriz, di_series = calcular_series_di(
            datos_hormigon=datos_hormigon,
            datos_acero=datos_acero,
            datos_seccion=datos_seccion,
            eje=eje,
        )
        resultados["di_matriz"] = di_matriz
        resultados["di_series"] = di_series

    return resultados