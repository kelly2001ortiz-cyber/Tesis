import numpy as np

# Importa tus funciones existentes y así evitamos cambiar su implementación
from mc_hognestad_columnaY import ejecutar_mc_hognestad_columnaY as _run_hognestad_columnaY
from mc_mander_u_columnaY import ejecutar_mc_mander_no_confinado_columnaY as _run_mander_u_columnaY
from mc_hognestad_columnaX import ejecutar_mc_hognestad_columnaX as _run_hognestad_columnaX
from mc_mander_u_columnaX import ejecutar_mc_mander_no_confinado_columnaX as _run_mander_u_columnaX

# === DI  c_phi, phiPn, phiMn, c_n, Pn, Mn (en ese orden)
from di_columnaY import ejecutar_di_columnaY as _run_di_columnaY
from di_columnaX import ejecutar_di_columnaX as _run_di_columnaX

class CalculadoraMomentoCurvatura:
    def _texto_direccion(self, direccion):
        """Acepta un widget con .currentText() o un str directamente."""
        if hasattr(direccion, "currentText"):
            return direccion.currentText()
        return str(direccion)
    
    def ejecutar(self, datos_hormigon, datos_acero, datos_seccion, datos_fibras, direccion):
        # Ejecutar cada modelo con las firmas actuales
        texto = self._texto_direccion(direccion).strip()
        if texto == "Dirección Y":
            M_hog, th_hog = _run_hognestad_columnaY(datos_hormigon, datos_acero, datos_seccion, datos_fibras)
            M_mu,  th_mu  = _run_mander_u_columnaY(datos_hormigon, datos_acero, datos_seccion, datos_fibras)
            c, phi_P, phi_M, P, M = _run_di_columnaY(datos_hormigon, datos_acero, datos_seccion)
        elif texto == "Dirección X":
            M_hog, th_hog = _run_hognestad_columnaX(datos_hormigon, datos_acero, datos_seccion, datos_fibras)
            M_mu,  th_mu  = _run_mander_u_columnaX(datos_hormigon, datos_acero, datos_seccion, datos_fibras)
            c, phi_P, phi_M, P, M = _run_di_columnaX(datos_hormigon, datos_acero, datos_seccion)


        # Alinear longitudes por seguridad (tomamos la mínima)
        m = min(len(th_hog), len(th_mu))
        th_hog, M_hog = np.asarray(th_hog[:m]), np.asarray(M_hog[:m])
        th_mu,  M_mu  = np.asarray(th_mu[:m]),  np.asarray(M_mu[:m])

        # Matriz lista para uso posterior
        mc_matriz = np.column_stack([th_hog, M_hog, th_mu, M_mu])

        # Series individuales por si quieres graficar/exportar por separado
        mc_series = {
            "hognestad":        (th_hog, M_hog),
            "mander_no_conf":   (th_mu,  M_mu),
        }

        # Alinear longitudes por seguridad (tomamos la mínima)
        m = len(c)
        phi_M, phi_P = np.asarray(phi_M[:m]), np.asarray(phi_P[:m])
        M, P = np.asarray(M[:m]),  np.asarray(P[:m])
        # Matriz lista para uso posterior
        di_matriz = np.column_stack([c, phi_M, phi_P, M, P])

        # Series individuales por si quieres graficar/exportar por separado
        di_series = {
            "con_phi":   (phi_M, phi_P),
            "sin_phi":   (M, P),
        }

        return mc_matriz, mc_series, di_matriz, di_series
