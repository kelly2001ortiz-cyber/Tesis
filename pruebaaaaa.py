import numpy as np
from scipy.optimize import root_scalar
from materiales import modelos
from seccion import utilidades
import matplotlib.pyplot as plt

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

    if nombre == "hognestad":
        def wrapper(ec, fc0, ec0, esp, Ec, datos_h, N):
            return hognestad(ec, fc0, ec0, esp, Ec, datos_h, N)
        return wrapper

    elif nombre == "mander_u":
        return mander_u

    elif nombre == "mander_c":
        return mander_c

    else:
        raise ValueError(f"Modelo de hormigón desconocido: {nombre_modelo}")


def resultantes_hormigon(fibras, sigma_c, c, phi, fc0, ec0, esp, Ec, datos_h):
    yi = fibras[:, 0]
    Ai = fibras[:, 1]
    ec = -phi * (yi - c)
    sigma = sigma_c(ec, fc0, ec0, esp, Ec, datos_h, 1)
    N = np.sum(sigma * Ai)
    M = np.sum(sigma * Ai * yi)
    return N, M


def resultantes_acero(As, sigma_s, c, phi, fy, fsu, Es, ey, esh, esu):
    yi = As[:, 0]
    Ai = As[:, 1]
    es = -phi * (yi - c)
    sigma = sigma_s(es, fy, fsu, Es, ey, esh, esu)
    N = np.sum(sigma * Ai)
    M = np.sum(sigma * Ai * yi)
    return N, M


def resultantes(c, phi, cover, core, As, sg_cover, sg_core,
                fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, P, datos_h):
    N_uc, M_uc = resultantes_hormigon(cover, sg_cover, c, phi, fc0, ec0, esp, Ec, datos_h)
    N_cc, M_cc = resultantes_hormigon(core, sg_core, c, phi, fc0, ec0, esp, Ec, datos_h)
    N_s, M_s = resultantes_acero(As, park, c, phi, fy, fsu, Es, ey, esh, esu)

    N_total = N_uc + N_cc + N_s - P
    M_total = M_uc + M_cc + M_s
    return N_total, M_total


def momrot(c_min, c_max, phi, cover, core, As, tol, h, sg_cover, sg_core,
           fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, P, datos_h,
           c_prev=None, phi_prev=None):

    def N_equilibrio(c):
        return resultantes(
            c, phi, cover, core, As, sg_cover, sg_core,
            fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, P, datos_h
        )[0]

    def es_max(c_eval, phi_eval):
        yi = As[:, 0]
        e_s = -phi_eval * (yi - c_eval)
        es_validas = e_s[np.abs(e_s) < esu]
        if es_validas.size == 0:
            return -np.inf
        return np.max(np.abs(es_validas))

    def filtro(roots, es_prev):
        raices = []
        for c_root in roots:
            es = es_max(c_root, phi)
            if es >= 0.90 * es_prev:
                raices.append(c_root)
        return raices

    def encontrar_raices(a, b, npts):
        c_vals = np.linspace(a, b, npts)
        N_vals = np.array([N_equilibrio(c_i) for c_i in c_vals], dtype=float)
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
        if c_prev is None:
            return encontrar_raices(c_min, c_max, npts=80)

        es_prev = es_max(c_prev, phi_prev)

        dc0 = 0.02 * h
        a0 = max(c_min, c_prev - dc0)
        b0 = min(c_max, c_prev + dc0)

        N_a0 = N_equilibrio(a0)
        N_b0 = N_equilibrio(b0)

        if abs(N_a0) < tol:
            roots = filtro([a0], es_prev)
            if roots:
                return roots

        if abs(N_b0) < tol:
            roots = filtro([b0], es_prev)
            if roots:
                return roots

        if N_a0 * N_b0 < 0.0:
            try:
                sol = root_scalar(N_equilibrio, bracket=[a0, b0], method="brentq")
                if sol.converged and abs(N_equilibrio(sol.root)) <= tol:
                    roots = filtro([sol.root], es_prev)
                    if roots:
                        return roots
            except ValueError:
                pass

        ventanas = [0.04*h, 0.08*h, 0.10*h, 0.15*h, 0.25*h, 0.35*h, 0.50*h]

        for dc in ventanas:
            a = max(c_min, c_prev - dc)
            b = min(c_max, c_prev + dc)
            roots = encontrar_raices(a, b, npts=20)
            roots = filtro(roots, es_prev)
            if roots:
                return roots

        return encontrar_raices(c_min, c_max, npts=120)

    c_posibles = buscar_c()
    if not c_posibles:
        return None, None

    if c_prev is None:
        c = min(c_posibles, key=lambda x: abs(x))
    else:
        c = min(c_posibles, key=lambda x: abs(x - c_prev))

    M = resultantes(
        c, phi, cover, core, As, sg_cover, sg_core,
        fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, P, datos_h
    )[1]

    return M, c


def diagrama_MC(cover, core, As, tol, h, sg_cover, sg_core,
                fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, P, datos_h):

    dphi_min, dphi_max = 2e-8, 5e-5
    phi_ini, dphi_ini = 2e-5, 1e-6

    phi_vals = [0.0]
    M_vals = [0.0]
    c_vals = [0.0]

    phi = phi_ini
    dphi = dphi_ini

    # Para vigas conviene permitir que el eje neutro pueda salir de la sección
    c_min = -1.5 * h
    c_max =  1.5 * h

    c_prev = None
    phi_prev = None
    Mmax = 0.0
    post_pico = False
    pts_extra = None
    n_pts_extra = 4

    for _ in range(1000):
        Mi, ci = momrot(
            c_min, c_max, phi, cover, core, As, tol, h, sg_cover, sg_core,
            fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, P, datos_h, c_prev, phi_prev
        )

        if Mi is None:
            if dphi > dphi_min:
                dphi = max(0.80 * dphi, dphi_min)
                continue
            break

        Mi = -Mi

        phi_vals.append(phi)
        M_vals.append(Mi)
        c_vals.append(ci)

        if Mi > Mmax:
            Mmax = Mi
        elif Mi < 0.90 * Mmax:
            post_pico = True

        if post_pico and Mi < 0.70 * Mmax:
            dphi = max(0.80 * dphi, dphi_min)
            if pts_extra is None:
                pts_extra = n_pts_extra
            pts_extra -= 1
            if pts_extra < 0:
                break

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
# DATOS DE MATERIALES
# =========================

fc0 = 240
Ec = 15100 * fc0 ** 0.5
ec0 = 0.0021
esp = 0.004

fcc = None
ecu = None

fy = 4587
fsu = 6096
Es = 2099898
ey = 0.0022
esh = 0.023
esu = 0.13

# =========================
# DATOS GEOMÉTRICOS
# =========================

seccion = "viga"

m_cover = "Hognestad"
m_core = "Hognestad"

b = 35
h = 60
r = 4
de = 1.0
Sc = 10

# En vigas estos valores no afectan barras_viga, pero sí pueden quedar en datos_h
d_edge = 2.5
d_corner = 2.5

# Para confinamiento tipo mander_c, esto depende de tu modelo
nl_x = 2
nl_y = 2

nf_x = 10
nf_y = 10

# IMPORTANTE:
# Para viga, barras_viga devuelve coordenadas verticales y_i,
# así que la malla debe generarse con el eje que también use coordenada vertical.
eje = "x"

# Refuerzo de viga
nb_sup = 3
nb_inf = 4
d_sup = 1.8
d_inf = 2.5
nb = nb_sup + nb_inf

# =========================
# GEOMETRÍA DE FIBRAS Y ACERO
# =========================

cover, core = malla(b, h, r, de, nf_x, nf_y, eje)
As = barras_viga(h, r, de, nb_sup, nb_inf, d_sup, d_inf)

tol = 1e-5
P = 0.0

# =========================
# MODELOS DE HORMIGÓN
# =========================

sg_cover = sigma_hormigon(m_cover)
sg_core = sigma_hormigon(m_core)

datos_h = (fy, b, h, r, Sc, de, d_corner, d_edge, nb, nl_x, nl_y, ecu, fcc)

if m_core.lower().strip() == "mander_c":
    ecu = buscar_ecu(fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, datos_h)
    fcc = mander_c(0, fc0, ec0, esp, Ec, datos_h, 3)
    datos_h = (fy, b, h, r, Sc, de, d_corner, d_edge, nb, nl_x, nl_y, ecu, fcc)

# =========================
# DIAGRAMA MOMENTO-CURVATURA
# =========================

M, phi, c = diagrama_MC(
    cover, core, As, tol, h, sg_cover, sg_core,
    fc0, ec0, esp, Ec, fy, fsu, Es, ey, esh, esu, P, datos_h
)

# Escalas de salida
M = M / 10**5
phi = phi * 100

for curvatura, momento in zip(phi, M):
    print(f"{curvatura:.8f}\t{momento:.6f}")
    
plt.plot(phi, M)
plt.xlabel("Curvatura φ (1/100 rad)")
plt.ylabel("Momento M (kN·m)")
plt.title("Diagrama Momento-Curvatura")
plt.show()