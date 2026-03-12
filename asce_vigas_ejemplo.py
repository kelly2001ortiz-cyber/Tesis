import numpy as np
import matplotlib.pyplot as plt

# =========================================================
# FUNCIONES
# =========================================================

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

    My = (0.5 * fc * 10 * b / 100 * (d / 100) ** 2) * (
        ((1 + Bc - niu) * niu0 + (2 - niu) * pt + (niu - 2 * Bc) * alfac * ptl)
    )

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
            0.020, 0.015
        )
        b = _interp_bilineal(
            x, y,
            0.0, 0.5,
            3.0, 6.0,
            0.050, 0.030,
            0.040, 0.020
        )
    else:
        a = _interp_bilineal(
            x, y,
            0.0, 0.5,
            3.0, 6.0,
            0.020, 0.010,
            0.010, 0.005
        )
        b = _interp_bilineal(
            x, y,
            0.0, 0.5,
            3.0, 6.0,
            0.030, 0.015,
            0.015, 0.010
        )

    c = 0.20
    return a, b, c


def calcular_lp_viga_paulay_priestley_1992(z, fy_mpa, db_m):
    """
    Paulay & Priestley (1992):
        Lp = 0.08*z + 0.022*fy*db

    z     : m
    fy    : MPa
    db    : m
    Lp    : m
    """
    return 0.08 * z + 0.022 * fy_mpa * db_m


def calcular_momentos_extremo_desde_lp(My, Long, Lp):
    """
    Lp = ((Mi - My) / (Mi + Mj)) * Long
    suponiendo Mi = Mj = alpha*My
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
    ey, ec0, ecu, Long, P0=0, n_puntos=100
):
    # Geometría efectiva
    d = h - rec - d_est - (d_var_sup / 10) / 2   # cm
    dl = h - d                                   # cm

    # Propiedades geométricas
    A = b * h
    I = b * h**3 / 12
    EA = Ec * 10 * A / 100**2
    EI = Ec * 10 * I / 100**4

    # Áreas de acero
    As = n_var_inf * (np.pi / 4 * (d_var_inf / 10) ** 2)   # cm2
    Asl = n_var_sup * (np.pi / 4 * (d_var_sup / 10) ** 2)  # cm2
    Av = 2 * np.pi / 4 * (d_est) ** 2                      # cm2

    # Factor beta1
    B1 = 1.05 - fc / 1400 if fc > 280 else 0.85
    B1 = max(B1, 0.65)

    # Fluencia
    My, phy_y = calcular_fluencia(b, d, dl, fc, fy, ey, ec0, ecu, As, Asl, P0)

    # Cuantía relativa
    p = As / (b * d)
    pl = Asl / (b * d)
    pb = 0.85 * fc / fy * B1 * (6120 / (6120 + fy))
    cuantia = (p - pl) / pb

    # Longitud plástica
    z = Long / 2.0
    fy_mpa = fy * 0.0980665
    db_m = d_var_inf / 1000.0
    Lp = calcular_lp_viga_paulay_priestley_1992(z=z, fy_mpa=fy_mpa, db_m=db_m)

    # Mi, Mj, cortante
    Mi, Mj, alpha = calcular_momentos_extremo_desde_lp(My, Long, Lp)
    V_calc = calcular_cortante_diseno_desde_momentos(Mi, Mj, Long)

    # Clasificación del refuerzo transversal
    Vs = Av * fy * d / s_est
    confinado = (s_est <= d / 3.0) and (Vs >= 0.75 * V_calc)

    # Cortante normalizado
    bw = b / 100.0
    d_m = d / 100.0
    v_norma = 1.1926 * (V_calc / (bw * d_m * np.sqrt(fc)))

    # Parámetros de modelación
    a, b_par, c = obtener_parametros_modelado_viga_asce41_17(
        cuantia_relativa=cuantia,
        confinado=confinado,
        v_norma=v_norma
    )

    # Diagrama momento-rotación
    roty = Long * My / (6 * EI)
    rotu = roty + a
    Mu = My + 0.05 * EI * (rotu - roty)
    MR = c * My
    rotR = roty + b_par

    Rotacion = np.array([0, roty, rotu, rotu + 0.1 * (rotR - rotu), rotR], dtype=float)
    Momento = np.array([0, My, Mu, MR, MR], dtype=float)

    # Diagrama momento-curvatura
    cury = phy_y
    curu = cury + rotu / Lp
    curR = cury + rotR / Lp
    Curvatura = np.array([0, cury, curu, curu + 0.1 * (curR - curu), curR], dtype=float)

    thetas = np.linspace(Curvatura.min(), Curvatura.max(), n_puntos)
    M = np.interp(thetas, Curvatura, Momento)

    rots = np.linspace(Rotacion.min(), Rotacion.max(), n_puntos)
    Mr = np.interp(rots, Rotacion, Momento)

    resultados = {
        "A_cm2": A,
        "I_cm4": I,
        "EA": EA,
        "EI": EI,
        "d_cm": d,
        "As_cm2": As,
        "Asl_cm2": Asl,
        "Av_cm2": Av,
        "cuantia_relativa": cuantia,
        "Lp_m": Lp,
        "Mi": Mi,
        "Mj": Mj,
        "alpha": alpha,
        "V_calc": V_calc,
        "Vs": Vs,
        "confinado": confinado,
        "v_norma": v_norma,
        "a": a,
        "b": b_par,
        "c": c,
        "My": My,
        "phy_y": phy_y,
        "M": M,
        "thetas": thetas,
        "Mr": Mr,
        "rots": rots
    }

    return resultados


# =========================================================
# DATOS DE ENTRADA DEL EJEMPLO (SEGÚN LAS IMÁGENES)
# =========================================================

# Hormigón
fc = 240.0                 # kg/cm2
Ec = 150000.0              # kg/cm2

# Acero
fy = 2530.0                # kg/cm2
Es = 2043000.0             # kg/cm2
ey = 0.0021               # deformación de fluencia

# Deformaciones del hormigón
ec0 = 0.002
ecu = 0.003

# Sección
b = 40.0                   # cm
h = 40.0                   # cm
rec = 6.0                  # cm

# Refuerzo transversal
d_est = 1.0                # cm  (Ø10 mm)
s_est = 10.0               # cm

# Refuerzo longitudinal
n_var_inf = 3
d_var_inf = 20.0           # mm   -> 3Ø20 inferior

n_var_sup = 3
d_var_sup = 16.0           # mm   -> 3Ø16 superior

# Carga axial
P0 = 0.0

# IMPORTANTE:
# La imagen NO muestra la luz de la viga.
# Debes colocar aquí la luz real de tu ejemplo en metros.
LONG_VIGA_M = 4.0


# =========================================================
# EJECUCIÓN
# =========================================================

if __name__ == "__main__":
    resultados = calcular_respuesta_seccion(
        fc=fc, fy=fy, Ec=Ec,
        b=b, h=h, rec=rec,
        d_est=d_est, s_est=s_est,
        d_var_sup=d_var_sup, n_var_sup=n_var_sup,
        d_var_inf=d_var_inf, n_var_inf=n_var_inf,
        ey=ey, ec0=ec0, ecu=ecu,
        Long=LONG_VIGA_M,
        P0=P0,
        n_puntos=100
    )

    print("=== RESULTADOS DEL EJEMPLO ===")
    print(f"A   = {resultados['A_cm2']:.4f} cm2")
    print(f"I   = {resultados['I_cm4']:.4f} cm4")
    print(f"EA  = {resultados['EA']:.6f}")
    print(f"EI  = {resultados['EI']:.6f}")
    print(f"d   = {resultados['d_cm']:.4f} cm")
    print(f"As  = {resultados['As_cm2']:.4f} cm2")
    print(f"As' = {resultados['Asl_cm2']:.4f} cm2")
    print(f"Av  = {resultados['Av_cm2']:.4f} cm2")
    print(f"cuantia_relativa = {resultados['cuantia_relativa']:.6f}")
    print(f"Lp  = {resultados['Lp_m']:.6f} m")
    print(f"Mi  = {resultados['Mi']:.6f}")
    print(f"Mj  = {resultados['Mj']:.6f}")
    print(f"alpha = {resultados['alpha']:.6f}")
    print(f"V_calc = {resultados['V_calc']:.6f}")
    print(f"Vs = {resultados['Vs']:.6f}")
    print(f"confinado = {resultados['confinado']}")
    print(f"v_norma = {resultados['v_norma']:.6f}")
    print(f"a = {resultados['a']:.6f}")
    print(f"b = {resultados['b']:.6f}")
    print(f"c = {resultados['c']:.6f}")
    print(f"My = {resultados['My']:.6f}")
    print(f"phi_y = {resultados['phy_y']:.8f}")
    
    # ==============================
    # GRÁFICOS
    # ==============================
    plt.figure(figsize=(8, 5))
    plt.plot(resultados["rots"], resultados["Mr"], linewidth=2)
    plt.xlabel("Rotación [rad]")
    plt.ylabel("Momento")
    plt.title("Diagrama Momento-Rotación")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(8, 5))
    plt.plot(resultados["thetas"], resultados["M"], linewidth=2)
    plt.xlabel("Curvatura [rad/m]")
    plt.ylabel("Momento")
    plt.title("Diagrama Momento-Curvatura")
    plt.grid(True)
    plt.tight_layout()
    plt.show()