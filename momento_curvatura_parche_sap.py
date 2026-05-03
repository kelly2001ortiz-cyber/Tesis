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
def resultantes(c, phi, cover, core, As, fc0, ec0, esp, Ec,
                fy, fsu, Es, ey, esh, esu,
                P, datos_h, sg_cover, sg_core):
    N_uc, M_uc = resultantes_hormigon(cover, sg_cover, c, phi, fc0, ec0, esp, Ec, datos_h)
    N_cc, M_cc = resultantes_hormigon(core, sg_core, c, phi, fc0, ec0, esp, Ec, datos_h)
    N_s, M_s = resultantes_acero(As, park, c, phi, fy, fsu, Es, ey, esh, esu)

    N_total = N_uc + N_cc + N_s - P
    M_total = M_uc + M_cc + M_s
    return N_total, M_total

# Funcion para encontrar la distancia al eje neutro
def momrot(c_min, c_max, phi, cover, core, As, tol, h, fc0, ec0, esp, Ec,
           fy, fsu, Es, ey, esh, esu,
           P, datos_h, sg_cover, sg_core, c_prev, phi_prev):

    def N_equilibrio(c):
        N = resultantes(c, phi, cover, core, As, fc0, ec0, esp, Ec,
                        fy, fsu, Es, ey, esh, esu, P, datos_h,
                        sg_cover, sg_core)[0]

        return N

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

    def buscar_c():
        # Primer punto
        if c_prev is None:
            c = encontrar_raices(c_min, c_max, npts=101)
            return c

        # Intento de busqueda directo cerca de la raíz previa
        dc0 = 0.02*h
        a0 = max(c_min, c_prev - dc0)
        b0 = min(c_max, c_prev + dc0)
        N_a0 = N_equilibrio(a0)
        N_b0 = N_equilibrio(b0)

        if abs(N_a0) < tol:
            return [a0]
        if abs(N_b0) < tol:
            return [b0]

        if N_a0 * N_b0 < 0.0:
            try:
                sol = root_scalar(N_equilibrio, bracket=[a0, b0], method="brentq")
                if sol.converged and abs(N_equilibrio(sol.root)) <= tol:
                    return [sol.root]
            except ValueError:
                pass

        # Si falla el intento directo, usar ventanas crecientes
        ventanas = [0.04*h, 0.08*h, 0.15*h, 0.30*h, 0.40*h, 0.50*h]
        for dc in ventanas:
            a = max(c_min, c_prev - dc)
            b = min(c_max, c_prev + dc)
            roots = encontrar_raices(a, b, npts=51)
            if roots:
                return roots

        return encontrar_raices(c_min, c_max, npts=201)

    c_posibles = buscar_c()
    
    if not c_posibles:
        return None, None

    if c_prev is None:
        c = min(c_posibles, key=lambda x: abs(x))
    else:
        c = min(c_posibles, key=lambda x: abs(x - c_prev))

    M = resultantes(c, phi, cover, core, As, fc0, ec0, esp, Ec,
                    fy, fsu, Es, ey, esh, esu,
                    P, datos_h, sg_cover, sg_core)[1]
    return M, c

# Funcion para obtener el diagrama momento-curvatura
def diagrama_MC(cover, core, As, tol, h, fc0, ec0, esp, Ec,
                fy, fsu, Es, ey, esh, esu,
                P, datos_h, sg_cover, sg_core):
    
    dphi_min, dphi_max = 5.0e-7, 3.5e-5
    phi_ini, dphi_ini = 3.5e-7, 5.0e-7

    phi_vals = [0.0]
    M_vals = [0.0]
    c_vals = [0.0]

    phi = phi_ini
    dphi = dphi_ini
    c_min = -500*h
    c_max = 500*h
    c_prev = None
    phi_prev = None
    Mmax = 0.0
    post_pico = False
    pts_extra = 50
    fallos_consecutivos = 0
    max_fallos = 10
    
    residual = False
    caida_final_detectada = False
    tol_horizontal = 0.01

    # Parámetros de control
    limite_post_pico = 0.80       # entra a zona post-pico
    limite_residual = 0.65        # si mantiene al menos 65% de Mmax, es residual aceptable

    caida_suave = 0.05            # variación pequeña entre puntos
    caida_brusca_1paso = 0.25     # caída fuerte entre dos puntos
    caida_brusca_ventana = 0.30   # caída fuerte en varios puntos

    w = 3                         # ventana corta para detectar caída brusca

    for _ in range(10000):
        Mi, ci = momrot(c_min, c_max, phi, cover, core, As, tol, h, fc0, ec0, esp, Ec,
                        fy, fsu, Es, ey, esh, esu,
                        P, datos_h, sg_cover, sg_core, c_prev, phi_prev)

        # No hay solucion de equilibrio: falla numerica/fisica
        # Si falla, probar reduciendo paso antes de salir
        if Mi is None:
            fallos_consecutivos += 1
            if fallos_consecutivos > max_fallos:
                break

            if dphi > dphi_min and phi_prev is not None:
                dphi = max(0.50 * dphi, dphi_min)
                phi = phi_prev + dphi
                continue
            break

        Mi = -Mi
        fallos_consecutivos = 0

        # Guardar resultados
        if Mi <= 0:
            break
        else:
            phi_vals.append(phi)
            M_vals.append(Mi)
            c_vals.append(ci)

        # ===============================
        # Control de picos y post-pico
        # ===============================

        # Momento anterior
        if len(M_vals) >= 2:
            M_anterior = M_vals[-2]
        else:
            M_anterior = Mi

        if caida_final_detectada:
            # seguir solo puntos extra
            pts_extra -= 1
            # aumentar paso
            dphi = min(1.25 * dphi, dphi_max)
            cambio_relativo = abs(Mi - M_anterior) / Mmax if Mmax > 0 else 0.0
            
            if (
                pts_extra <= 0 or 
                cambio_relativo <= tol_horizontal):
                break

        # Actualizar momento máximo
        if Mi > Mmax:
            Mmax = Mi
            post_pico = False
            residual = False

        else:
            # Entrar a post-pico
            if Mi < limite_post_pico * Mmax:
                post_pico = True

        # Evaluar post-pico
        if post_pico and Mmax > 0:

            # Caída respecto al punto anterior
            caida_1paso = (M_anterior - Mi) / Mmax

            # Caída en una ventana corta
            if len(M_vals) > w:
                M_antes_ventana = M_vals[-w]
                caida_ventana = (M_antes_ventana - Mi) / Mmax
            else:
                caida_ventana = 0.0

            # Detectar rama residual estable
            if Mi >= limite_residual * Mmax and abs(caida_1paso) <= caida_suave:
                residual = True

            # Detectar caída brusca final
            caida_final = (
                Mi < limite_residual * Mmax and
                (
                caida_1paso >= caida_brusca_1paso or
                caida_ventana >= caida_brusca_ventana
            ))

            if caida_final:
                caida_final_detectada = True

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


def _buscar_phi_en_rama_ascendente_por_umbral(phi, M, idx_max, fraccion=0.99):
    """
    Busca la primera curvatura en la rama ascendente que alcanza
    una fracción del momento máximo.

    Retorna:
        phi_obj, M_obj, encontrado
    """
    phi = np.asarray(phi, dtype=float)
    M = np.asarray(M, dtype=float)

    M_max = float(M[idx_max])
    M_obj = fraccion * M_max

    if idx_max <= 0:
        return float(phi[idx_max]), float(M[idx_max]), False

    for i in range(1, idx_max + 1):
        if M[i] >= M_obj:
            phi1, M1 = float(phi[i - 1]), float(M[i - 1])
            phi2, M2 = float(phi[i]), float(M[i])

            if abs(M2 - M1) < 1e-14:
                phi_obj = phi2
            else:
                phi_obj = phi1 + (M_obj - M1) * (phi2 - phi1) / (M2 - M1)

            return float(phi_obj), float(M_obj), True

    return float(phi[idx_max]), float(M[idx_max]), False


def _buscar_punto_falla_por_resistencia(phi, M, idx_max, fraccion=0.80):
    """
    Busca el punto de degradación como el primer punto post-pico
    donde M <= fraccion * M_max.

    Si encuentra cruce, interpola linealmente.
    Si no encuentra cruce, usa el último punto disponible como fallback.
    """
    phi = np.asarray(phi, dtype=float)
    M = np.asarray(M, dtype=float)

    M_max = float(M[idx_max])
    M_lim = fraccion * M_max

    if idx_max >= len(M) - 1:
        return float(phi[-1]), float(M[-1]), False

    for i in range(idx_max + 1, len(M)):
        if M[i] <= M_lim:
            if i == idx_max + 1:
                return float(phi[i]), float(M_lim), True

            phi1, M1 = float(phi[i - 1]), float(M[i - 1])
            phi2, M2 = float(phi[i]), float(M[i])

            if abs(M2 - M1) < 1e-14:
                phi_f = phi2
            else:
                phi_f = phi1 + (M_lim - M1) * (phi2 - phi1) / (M2 - M1)

            return float(phi_f), float(M_lim), True

    return float(phi[-1]), float(M[-1]), False


def _area_hasta_phi(phi, M, phi_ref):
    """
    Calcula el área bajo la curva M-φ hasta una curvatura phi_ref.
    Si phi_ref cae entre dos puntos, interpola linealmente.
    """
    phi = np.asarray(phi, dtype=float)
    M = np.asarray(M, dtype=float)

    mask = phi < phi_ref
    phi_area = phi[mask]
    M_area = M[mask]

    M_ref = _interp_lineal_xy(phi, M, phi_ref)

    if len(phi_area) == 0 or abs(phi_area[-1] - phi_ref) > 1e-12:
        phi_area = np.append(phi_area, phi_ref)
        M_area = np.append(M_area, M_ref)

    return float(np.trapz(M_area, phi_area))


def extraer_parametros_caracteristicos_mc(phi, M):
    """
    Extrae parámetros característicos directamente de la tabla M-φ.

    Criterios adoptados:
    - rigidez inicial: pendiente de la rama inicial lineal
    - punto de fluencia:
        * My por idealización bilineal
        * phi_y = My / Ki
    - punto máximo:
        * Mmax = pico real
        * phi_max = primera curvatura que alcanza 0.99*Mmax
    - punto de falla:
        * primer punto post-pico donde M <= 0.80*Mmax
    - punto último:
        * último punto de la tabla M-φ
    - ductilidad:
        * mu_phi = phi_u / phi_y
    """
    phi, M = _limpiar_curva_mc(phi, M)

    if len(phi) < 2:
        raise ValueError("No hay suficientes puntos en la tabla M-φ (mínimo 2).")

    usar_simplificado = len(phi) < 4

    # -----------------------------
    # Punto máximo (momento pico real)
    # -----------------------------
    idx_max = int(np.argmax(M))
    M_max = float(M[idx_max])
    phi_peak = float(phi[idx_max])

    # Curvatura representativa del máximo:
    # primera curvatura que alcanza 99% del pico
    phi_max, _, _ = _buscar_phi_en_rama_ascendente_por_umbral(
        phi, M, idx_max, fraccion=0.99
    )

    # -----------------------------
    # Rigidez inicial
    # -----------------------------
    try:
        K_ini = _rigidez_inicial_desde_tabla(phi[:idx_max + 1], M[:idx_max + 1])
    except Exception:
        K_ini = M_max / max(phi_peak, 1e-12)

    # -----------------------------
    # Punto último = último punto de la tabla
    # -----------------------------
    phi_u = float(phi[-1])
    M_u = float(M[-1])

    # -----------------------------
    # Punto de falla = 80% post-pico
    # -----------------------------
    try:
        phi_f, M_f, hubo_cruce_80 = _buscar_punto_falla_por_resistencia(
            phi, M, idx_max, fraccion=0.80
        )
    except Exception:
        phi_f, M_f, hubo_cruce_80 = phi_u, M_u, False

    # -----------------------------
    # Punto de fluencia
    #   1) My por idealización bilineal
    #   2) phi_y = My / Ki
    # -----------------------------
    if usar_simplificado or K_ini <= 1e-12:
        M_y = 0.60 * M_max
    else:
        # Para estimar My usamos como referencia el punto de falla (80% post-pico).
        # Si no existe cruce, usamos el punto último como fallback.
        phi_ref = phi_f if hubo_cruce_80 else phi_u
        M_ref = M_f if hubo_cruce_80 else M_u

        A_ref = _area_hasta_phi(phi, M, phi_ref)

        # Idealización bilineal con phi_y = My / Ki:
        # 2A = My*(phi_ref - M_ref/Ki) + M_ref*phi_ref
        denom = phi_ref - (M_ref / K_ini)

        if denom <= 1e-12:
            M_y = 0.60 * M_max
        else:
            M_y = (2.0 * A_ref - M_ref * phi_ref) / denom

    # Acotar My sin alterar el criterio principal
    M_y = float(np.clip(M_y, 1e-12, max(1e-12, 0.999 * M_max)))

    # Curvatura de fluencia a partir de Ki y My
    phi_y = float(M_y / K_ini) if K_ini > 1e-12 else float(0.60 * phi_max)

    # Limitar phi_y para que quede antes del máximo y del último punto,
    # pero SIN modificar M_y
    phi_lim = min(phi_max * 0.999, phi_u * 0.999) if phi_u > 0 else phi_max * 0.999
    phi_lim = max(phi_lim, 1e-12)

    if phi_y <= 0:
        phi_y = 1e-12
    elif phi_y > phi_lim:
        phi_y = phi_lim

    # -----------------------------
    # Ductilidad por curvatura
    #   usa el punto último, no el punto de falla
    # -----------------------------
    mu_phi = float(phi_u / phi_y) if phi_y > 0 else np.inf

    return {
        "rigidez_inicial": K_ini,

        # Fluencia
        "punto_fluencia": {"phi": phi_y, "M": M_y},

        # Máximo
        "punto_maximo": {"phi": phi_max, "M": M_max},
        "punto_pico_real": {"phi": phi_peak, "M": M_max},

        # Falla visible en resultados = 80% post-pico
        "punto_falla": {"phi": phi_f, "M": M_f},

        # Último punto de la curva
        "punto_ultimo": {"phi": phi_u, "M": M_u},
        "punto_final_analisis": {"phi": phi_u, "M": M_u},

        # Degradación explícita (mismo valor que punto_falla)
        "punto_degradacion": {"phi": phi_f, "M": M_f},

        "ductilidad_curvatura": mu_phi,
        "area_bajo_curva": _area_hasta_phi(phi, M, phi_u),

        "criterio_fluencia": (
            "Momento de fluencia efectivo obtenido por idealización bilineal; "
            "la curvatura de fluencia se calculó como phi_y = M_y / K_i."
        ),
        "criterio_maximo": (
            "M_max se definió como el pico real de la curva y phi_max como la "
            "primera curvatura en la rama ascendente que alcanza el 99% de M_max."
        ),
        "criterio_falla": (
            "El punto de falla se definió como el primer punto post-pico "
            "en el que la resistencia desciende al 80% del momento máximo."
        ),
        "criterio_ultimo": (
            "El punto último se definió como el último punto disponible "
            "de la tabla M-φ."
        ),
        "criterio_ductilidad": (
            "La ductilidad por curvatura se calculó como mu_phi = phi_u / phi_y, "
            "usando la curvatura última de la tabla y no el punto de falla al 80%."
        ),
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
    nr_x     = int(_f(datos_seccion, "disenar_columna_ramalesX"))
    nr_y     = int(_f(datos_seccion, "disenar_columna_ramalesY"))
    nb_x     = int(_f(datos_seccion, "disenar_columna_varillasX_2"))
    nb_y     = int(_f(datos_seccion, "disenar_columna_varillasY_2"))
    nb       = 2 * (nb_x - 2) + 2 * nb_y

    fyh = fy

    datos_h_base = (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nr_x, nr_y, None, None)

    fcc = mander_c(
        ec=np.array([0.0]),
        fc0=fc0,
        ec0=ec0,
        esp=esp,
        Ec=Ec,
        datos_h=datos_h_base,
        N=3,
    )

    datos_h_ecu = (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nr_x, nr_y, None, fcc)

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

    return (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nr_x, nr_y, ecu, fcc)


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
    ecu_confinada = None
    fcc_confinada = None

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
            ecu_confinada = datos_h[11]
            fcc_confinada = datos_h[12]
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
        
    if ecu_confinada is not None:
        parametros_mc["ecu_confinada"] = ecu_confinada
        parametros_mc["fcc_confinada"] = fcc_confinada

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