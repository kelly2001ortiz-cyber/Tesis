import numpy as np
from mc_asce import ejecutar_mc_asce as run_asce

class CalculadoraASCE:
    @staticmethod
    def _texto(widget_o_texto):
        try:
            return widget_o_texto.currentText().strip()
        except Exception:
            return str(widget_o_texto).strip()

    def calcular(self, tipo_seccion, direccion,
                 datos_hormigon, datos_acero, datos_seccion, datos_asce):
        tipo  = self._texto(tipo_seccion)
        direc = self._texto(direccion)

        M, thetas, Mr, rots, parametros = run_asce(
            tipo,
            direc,
            datos_hormigon,
            datos_acero,
            datos_seccion,
            datos_asce,
        )
        return {
            "rotacion":  (np.asarray(rots,   float), np.asarray(Mr, float)),
            "curvatura": (np.asarray(thetas, float), np.asarray(M,  float)),
            "parametros": parametros,
        }
