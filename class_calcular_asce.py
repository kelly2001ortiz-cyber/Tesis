import numpy as np

# Importa tus funciones existentes y así evitamos cambiar su implementación
from mc_asce_columnaY import ejecutar_mc_asce_columnaY as _run_asce_columnaY
from mc_asce_columnaX import ejecutar_mc_asce_columnaX as _run_asce_columnaX
from mc_asce_viga import ejecutar_mc_asce_viga as _run_asce_viga

class CalculadoraASCE:
    @staticmethod
    def _texto(widget_o_texto):
        try:
            return widget_o_texto.currentText().strip()
        except Exception:
            return str(widget_o_texto).strip()

    def calcular(self, tipo_seccion, direccion, condicion,
                 datos_hormigon, datos_acero, datos_seccion, datos_asce):
        tipo  = self._texto(tipo_seccion)
        direc = self._texto(direccion)

        if tipo.lower() == "viga":
            M, thetas, Mr, rots = _run_asce_viga(datos_hormigon, datos_acero, datos_seccion, datos_asce, condicion)
        else:
            if direc == "Dirección X":
                M, thetas, Mr, rots = _run_asce_columnaX(datos_hormigon, datos_acero, datos_seccion, datos_asce, condicion)
            else:
                M, thetas, Mr, rots = _run_asce_columnaY(datos_hormigon, datos_acero, datos_seccion, datos_asce, condicion)

        return {
            "rotacion":  (np.asarray(rots,   float), np.asarray(Mr, float)),
            "curvatura": (np.asarray(thetas, float), np.asarray(M,  float)),
        }
