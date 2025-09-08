# calculo_mc_service.py
import numpy as np

# Importa tus funciones existentes y así evitamos cambiar su implementación
from mc_hognestad_viga import ejecutar_mc_hognestad_viga as _run_hognestad_viga
from mc_mander_u_viga import ejecutar_mc_mander_no_confinado_viga as _run_mander_u_viga

class CalculadoraMomentoCurvaturaV:

    def ejecutar(self, datos_hormigon, datos_acero, datos_seccion, datos_fibras):
        # Ejecutar cada modelo con las firmas actuales
    
        M_hog, th_hog = _run_hognestad_viga(datos_hormigon, datos_acero, datos_seccion, datos_fibras)
        M_mu,  th_mu  = _run_mander_u_viga(datos_hormigon, datos_acero, datos_seccion, datos_fibras)
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
            
        return mc_matriz, mc_series
