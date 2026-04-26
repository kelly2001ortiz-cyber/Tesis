import numpy as np
from materiales_copia import modelos

class CurvasMateriales:
    def __init__(self, datos_hormigon=None, datos_acero=None, datos_seccion=None):
        self.datos_hormigon = datos_hormigon or {}
        self.datos_acero = datos_acero or {}
        self.datos_seccion = datos_seccion or {}

    @staticmethod
    def _f(datos, clave):
        return float(datos.get(clave))

    def park(self):
        fy = self._f(self.datos_acero, "esfuerzo_fy")
        fsu = self._f(self.datos_acero, "esfuerzo_ultimo_acero")
        Es = self._f(self.datos_acero, "modulo_Es")
        ey = self._f(self.datos_acero, "def_fluencia_acero")
        esh = self._f(self.datos_acero, "def_inicio_endurecimiento")
        esu = self._f(self.datos_acero, "def_ultima_acero")

        es = np.linspace(-esu, esu, 96)
        es = np.concatenate((es, [-esh, esh, -ey, ey]))
        es.sort()
        fs = modelos.park(es, fy, fsu, Es, ey, esh, esu)
        return es, fs

    def hognestad(self):
        fc0 = self._f(self.datos_hormigon, "esfuerzo_fc")
        Ec = self._f(self.datos_hormigon, "modulo_Ec")
        ec0 = self._f(self.datos_hormigon, "def_max_sin_confinar")
        esp = self._f(self.datos_hormigon, "def_ultima_sin_confinar")

        ec = np.linspace(-esp, 0.0, 100)
        fc = modelos.hognestad(ec, fc0, ec0, esp, Ec)
        return -ec, -fc

    def mander_no_confinado(self):
        fc0 = self._f(self.datos_hormigon, "esfuerzo_fc")
        Ec = self._f(self.datos_hormigon, "modulo_Ec")
        ec0 = self._f(self.datos_hormigon, "def_max_sin_confinar")
        esp = self._f(self.datos_hormigon, "def_ultima_sin_confinar")

        ec = np.linspace(-esp, 0.0, 100)
        fc = modelos.mander_u(ec, fc0, ec0, esp, Ec)
        return -ec, -fc

    def mander_confinado(self):
        fc0 = self._f(self.datos_hormigon, "esfuerzo_fc")
        Ec = self._f(self.datos_hormigon, "modulo_Ec")
        ec0 = self._f(self.datos_hormigon, "def_max_sin_confinar")
        esp = self._f(self.datos_hormigon, "def_ultima_sin_confinar")

        fy = self._f(self.datos_acero, "esfuerzo_fy")
        fsu = self._f(self.datos_acero, "esfuerzo_ultimo_acero")
        Es = self._f(self.datos_acero, "modulo_Es")
        ey = self._f(self.datos_acero, "def_fluencia_acero")
        esh = self._f(self.datos_acero, "def_inicio_endurecimiento")
        esu = self._f(self.datos_acero, "def_ultima_acero")

        b = self._f(self.datos_seccion, "disenar_columna_base")
        h = self._f(self.datos_seccion, "disenar_columna_altura")
        r = self._f(self.datos_seccion, "disenar_columna_recubrimiento")
        Sc = self._f(self.datos_seccion, "disenar_columna_espaciamiento")
        de = self._f(self.datos_seccion, "disenar_columna_diametro_transversal") / 10.0
        d_edge = self._f(self.datos_seccion, "disenar_columna_diametro_longitudinal_2") / 10.0
        d_corner = self._f(self.datos_seccion, "disenar_columna_diametro_longitudinal_esq") / 10.0
        nl_x = int(self._f(self.datos_seccion, "disenar_columna_ramalesX"))
        nl_y = int(self._f(self.datos_seccion, "disenar_columna_ramalesY"))
        nb_x = int(self._f(self.datos_seccion, "disenar_columna_varillasX_2"))
        nb_y = int(self._f(self.datos_seccion, "disenar_columna_varillasY_2"))
        nb = (nb_x - 2) * 2 + nb_y * 2

        fyh = fy
        fcc = None
        ecu = None

        datos_h = (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nl_x, nl_y, ecu, fcc)
        ecu = modelos.buscar_ecu(
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
            datos_h=datos_h,
        )
        datos_h = (fyh, b, h, r, Sc, de, d_corner, d_edge, nb, nl_x, nl_y, ecu, fcc)

        ec = np.linspace(-ecu, 0.0, 100)
        fc = modelos.mander_c(ec, fc0, ec0, esp, Ec, datos_h, 1)
        return -ec, -fc
