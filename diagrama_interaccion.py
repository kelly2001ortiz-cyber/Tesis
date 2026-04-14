import numpy as np
from scipy.optimize import root_scalar
from seccion import utilidades

barras_columna = utilidades.barras_columna

def prop_eje(b, h, eje):
	"""
	Retorna las dimensiones efectivas según el eje de análisis.

	bw : ancho del bloque de compresión de Whitney
	d  : profundidad en la dirección de la deformación
	"""
	eje = eje.lower().strip()

	if eje == "x":
		bw = b
		d = h
	elif eje == "y":
		bw = h
		d = b

	return bw, d

def acero_bilineal(es, fy, Es):
	"""
	Modelo blineal para acero de refuerzo.

	Parámetros:
		es  : deformación del acero
		fy  : esfuerzo de fluencia
		Es  : módulo elástico del acero

	Retorna:
		fs  : esfuerzo del acero
	"""
	es = np.asarray(es, dtype=float)
	fs = np.zeros_like(es, dtype=float)

	ey = fy/Es
	abs_es = np.abs(es)
	sign = np.sign(es)

	# Rama elástica lineal
	z1 = (abs_es <= ey)
	fs[z1] = Es * es[z1]

	# Rama perfectamente plástica
	z2 = (abs_es > ey)
	fs[z2] = fy * sign[z2]
	return fs

def hormigon_whitney(fc0, bw, d, c, b1):
	"""
	Resultantes del bloque equivalente de compresión de Whitney.

	Parámetros:
		fc0 : resistencia máxima a compresión del hormigón
		bw  : ancho del bloque comprimido según el eje de análisis
		d   : profundidad de la sección en la dirección de deformación
		c   : profundidad del eje neutro
		b1  : factor beta1

	Retorna:
		P   : carga axial aportada por el hormigón
		M   : momento aportado por el hormigón respecto al centroide
	"""
	fc = 0.85 * fc0
	a = b1 * c

	P = fc * bw * a
	M = P * (d/2 - a/2)
	return P, M

def resultantes(bw, d, As, c, fc0, e_cu, fy, Es):
	"""
	Calcula la carga axial y el momento nominal para una profundidad c.

	As[:, 0] : coordenada de cada barra medida sobre el eje de análisis
	As[:, 1] : área de cada barra
	"""
	b1 = max(min(0.85, 0.85 - 0.05 * (fc0 - 280) / 70), 0.65)
	P_c, M_c = hormigon_whitney(fc0, bw, d, c, b1)

	es = e_cu * (c + As[:, 0] - d/2) / c
	sigma_s = acero_bilineal(es, fy, Es)
	P_s = np.sum(sigma_s * As[:, 1])
	M_s = np.sum(sigma_s * As[:, 1] * As[:, 0])

	P = P_c + P_s
	M = M_c + M_s
	return P, M, c

def compresion_pura(bw, d, As, fc0, fy):
	"""
	Resistencia nominal a compresión pura.
	"""
	Ag = bw * d
	As_tot = np.sum(As[:, 1])
	P0 = 0.85 * fc0 * (Ag - As_tot) + fy * As_tot
	return P0

def tension_pura(As, fy):
	As_tot = np.sum(As[:, 1])
	P1 = - fy * As_tot
	return P1

def di(bw, d, As, fc0, e_cu, fy, Es):
	"""
	Calcula el diagrama de interacción nominal.
	"""
	def maxima_c(c):
		M = resultantes(bw, d, As, c, fc0, e_cu, fy, Es)[1]
		return M

	# Para calcular el c donde M = 0
	c_max = root_scalar(maxima_c, bracket=[1e-6, 2*d], method="brentq")
	c_max = c_max.root
	c = np.linspace(1e-6, c_max, 100)
	
	c_val = [0.0]
	P_val = [tension_pura(As, fy)]
	M_val = [0.0]

	for i in range(1, len(c)):
		Pi, Mi, ci = resultantes(bw, d, As, c[i], fc0, e_cu, fy, Es)

		c_val.append(ci)
		P_val.append(Pi)
		M_val.append(Mi)

		if Mi <= 0:
			break

	return np.array(P_val) / 10**3, np.array(M_val) / 10**5, np.array(c_val)

def factor_phi(As, d, e_cu, c, fy, Es):
	"""
	Calcula phi a partir de la deformación del acero más traccionado.
	"""
	ey = fy/Es
	d_t = np.min(As[:, 0])
	c = np.asarray(c, dtype=float)

	es_t = -e_cu * (c + d_t - d/2) / np.maximum(c, 1e-9)
	es_t = np.maximum(es_t, 0.0)

	phi = np.where(es_t <= ey, 0.65,
		np.where(es_t >= ey + 0.003, 
			0.90,
			0.65 + 0.25 * (es_t - ey) / 0.003
		)
	)
	return phi

def d_iteracion(b, h, r, de, nb_x, nb_y, d_corner, d_edge, 
				fc0, e_cu, fy, Es,  eje):
	bw, d = prop_eje(b, h, eje)
	As = barras_columna(b, h, r, de, nb_x, nb_y, d_corner, d_edge, eje)

	P, M, c = di(bw, d, As, fc0, e_cu, fy, Es)
	P0 = compresion_pura(bw, d, As, fc0, fy) / 1000
	phi = factor_phi(As, d, e_cu, c, fy, Es)

	Pn_max = 0.80 * P0
	phi_Pn_max = 0.65 * Pn_max

	phi_P = np.minimum(phi * P, phi_Pn_max)
	P = np.minimum(P, Pn_max)
	phi_M = phi * M

	return P, M, c, phi_P, phi_M


def _f(datos, clave, default=None):
	valor = datos.get(clave, default)
	if valor is None or valor == "":
		raise ValueError(f"Falta el dato '{clave}'")
	return float(valor)


def calcular_series_di(datos_hormigon, datos_acero, datos_seccion, eje):
	fc0 = _f(datos_hormigon, "esfuerzo_fc")
	e_cu = _f(datos_hormigon, "def_ultima_sin_confinar", 0.003)

	fy = _f(datos_acero, "esfuerzo_fy")
	Es = _f(datos_acero, "modulo_Es")

	b = _f(datos_seccion, "disenar_columna_base")
	h = _f(datos_seccion, "disenar_columna_altura")
	r = _f(datos_seccion, "disenar_columna_recubrimiento")
	nb_x = int(_f(datos_seccion, "disenar_columna_varillasX_2"))
	nb_y = int(_f(datos_seccion, "disenar_columna_varillasY_2"))
	de = _f(datos_seccion, "disenar_columna_diametro_transversal") / 10.0
	d_edge = _f(datos_seccion, "disenar_columna_diametro_longitudinal_2") / 10.0
	d_corner = _f(datos_seccion, "disenar_columna_diametro_longitudinal_esq") / 10.0

	eje = eje.strip().lower()

	P, M, c, phi_P, phi_M = d_iteracion(
		b, h, r, de, nb_x, nb_y, d_corner, d_edge,
		fc0, e_cu, fy, Es, eje
	)

	di_series = {
		"sin_phi": (M, P),
		"con_phi": (phi_M, phi_P),
	}

	di_matriz = np.column_stack([c, phi_M, phi_P, M, P])

	return di_matriz, di_series