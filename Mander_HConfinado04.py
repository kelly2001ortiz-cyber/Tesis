import numpy as np

# --- Modelo constitutivo del hormigon confinado de Mander ---
def mander_confinado(datos_hormigon, datos_acero, datos_seccion):

    """ Nomograma Mander """
    def fccfco (n1, n2):
        tabla = {
            'x1':  [1.0, 1.040296496, 1.080592992, 1.113881402, 1.140161725, 1.162938005, 1.182210243, 1.20148248, 1.219002695, 1.233018868, 1.245283019, 1.255795148, 1.264555256, 1.276819407, 1.282075472, 1.29083558],
            'x2':  [1.0, 1.124393531, 1.178706199, 1.215498652, 1.245283019, 1.268059299, 1.289083558, 1.311859838, 1.332884097, 1.348652291, 1.362668464, 1.374932615, 1.388948787, 1.401212938, 1.411725067, 1.420485175],
            'x3':  [1.0, 1.124393531, 1.243530997, 1.294339623, 1.329380054, 1.35916442, 1.388948787, 1.411725067, 1.436253369, 1.453773585, 1.467789757, 1.485309973, 1.502830189, 1.516846361, 1.527358491, 1.539622642],
            'x4':  [1.0, 1.124393531, 1.243530997, 1.353908356, 1.401212938, 1.438005391, 1.466037736, 1.494070081, 1.518598383, 1.539622642, 1.557142857, 1.576415094, 1.59393531, 1.609703504, 1.623719677, 1.634231806],
            'x5':  [1.0, 1.124393531, 1.243530997, 1.353908356, 1.455525606, 1.501078167, 1.53787062, 1.569407008, 1.599191375, 1.623719677, 1.644743935, 1.662264151, 1.679784367, 1.699056604, 1.711320755, 1.720080863],
            'x6':  [1.0, 1.124393531, 1.243530997, 1.353908356, 1.455525606, 1.557142857, 1.600943396, 1.635983827, 1.667520216, 1.695552561, 1.716576819, 1.7393531, 1.758625337, 1.777897574, 1.791913747, 1.805929919],
            'x7':  [1.0, 1.124393531, 1.243530997, 1.353908356, 1.455525606, 1.557142857, 1.651752022, 1.690296496, 1.727088949, 1.756873315, 1.78490566, 1.807681941, 1.830458221, 1.849730458, 1.865498652, 1.877762803],
            'x8':  [1.0, 1.124393531, 1.243530997, 1.353908356, 1.455525606, 1.557142857, 1.651752022, 1.741105121, 1.783153639, 1.812938005, 1.835714286, 1.858490566, 1.881266846, 1.904043127, 1.921563342, 1.939083558],   
            'x9':  [1.0, 1.124393531, 1.243530997, 1.353908356, 1.455525606, 1.557142857, 1.651752022, 1.741105121, 1.823450135, 1.863746631, 1.893530997, 1.919811321, 1.944339623, 1.967115903, 1.984636119, 2.003908356],
            'x10': [1.0, 1.124393531, 1.243530997, 1.353908356, 1.455525606, 1.557142857, 1.651752022, 1.741105121, 1.823450135, 1.904043127, 1.933827493, 1.958355795, 1.984636119, 2.010916442, 2.033692722, 2.05296496],
            'x11': [1.0, 1.124393531, 1.243530997, 1.353908356, 1.455525606, 1.557142857, 1.651752022, 1.741105121, 1.823450135, 1.904043127, 1.970619946, 2.002156334, 2.030188679, 2.058221024, 2.080997305, 2.105525606],
            'x12': [1.0, 1.124393531, 1.243530997, 1.353908356, 1.455525606, 1.557142857, 1.651752022, 1.741105121, 1.823450135, 1.904043127, 1.970619946, 2.040700809, 2.070485175, 2.103773585, 2.128301887, 2.15458221],
            'x13': [1.0, 1.124393531, 1.243530997, 1.353908356, 1.455525606, 1.557142857, 1.651752022, 1.741105121, 1.823450135, 1.904043127, 1.970619946, 2.040700809, 2.105525606, 2.137061995, 2.163342318, 2.189622642],
            'x14': [1.0, 1.124393531, 1.243530997, 1.353908356, 1.455525606, 1.557142857, 1.651752022, 1.741105121, 1.823450135, 1.904043127, 1.970619946, 2.040700809, 2.105525606, 2.175606469, 2.201838275, 2.224663073],
            'x15': [1.0, 1.124393531, 1.243530997, 1.353908356, 1.455525606, 1.557142857, 1.651752022, 1.741105121, 1.823450135, 1.904043127, 1.970619946, 2.040700809, 2.105525606, 2.175606469, 2.235175202, 2.257951482],
            'x16': [1.0, 1.124393531, 1.243530997, 1.353908356, 1.455525606, 1.557142857, 1.651752022, 1.741105121, 1.823450135, 1.904043127, 1.970619946, 2.040700809, 2.105525606, 2.175606469, 2.235175202, 2.3],
            'y':   [0.0, 0.017828571, 0.038057143, 0.057257143, 0.077485714, 0.097714286, 0.117600000, 0.138171429, 0.157714286, 0.177257143, 0.197142857, 0.217028571, 0.23760000, 0.258514286, 0.278400000, 0.3]}
        n2interp = np.array([1.29083558, 1.420485175, 1.539622642, 1.634231806, 1.720080863, 1.805929919, 1.877762803, 1.939083558, 2.003908356, 2.05296496, 2.105525606, 2.1545822, 2.189622642, 2.224663073, 2.257951482, 2.3])
        log_n2_final = np.array([0,	0.030217856132183404, 0.043907390934601435, 0.05914069957428035, 0.07669599849765889, 0.1, 0.118697957, 0.136568755, 0.157742049, 0.175922121,	0.2, 0.219665655, 0.237465214,	0.256707074, 0.276431578, 0.3])
        # Verificar rango
        if n2 < log_n2_final[0] or n2 > log_n2_final[-1]:
            return "El valor está fuera del rango permitido"
        
        # Interpolacion
        n2_equiv = np.interp(n2, log_n2_final, n2interp)
        y_vals = tabla['y']
        x_interpolada = []
        
        for i in range(len(y_vals)):
            x_vals = [tabla[f'x{j+1}'][i] for j in range(16)]
            x_interp = np.interp(n2_equiv, n2interp, x_vals)
            x_interpolada.append(x_interp)
        
        # INTERSECCION
        for i in range(len(y_vals) - 1):
            if (y_vals[i] - n1) * (y_vals[i+1] - n1) <= 0:
                x0, x1_ = x_interpolada[i], x_interpolada[i+1]
                y0, y1_ = y_vals[i], y_vals[i+1]
                t = (n1 - y0) / (y1_ - y0)
                n3= x0 + t * (x1_ - x0)
                return n3
        return "No hay interseccion"

    # Obtener parametros de sección, materiales y armado
    fc0 = float(datos_hormigon.get("esfuerzo_fc"))              # Esfuerzo máximo (kg/cm² o MPa)
    Ec = float(datos_hormigon.get("modulo_Ec"))                 # Módulo de elasticidad (kg/cm² o MPa)
    ec0 = float(datos_hormigon.get("def_max_sin_confinar"))     # Deformación máxima (pico)
    esu = float(datos_hormigon.get("def_ultima_confinada"))     # Deformación última
    fy = float(datos_acero.get("esfuerzo_fy"))     # Esfuerzo de fluencia
    b = float(datos_seccion.get("disenar_columna_base"))     # Esfuerzo de fluencia
    h = float(datos_seccion.get("disenar_columna_altura"))     # Esfuerzo de fluencia
    rec = float(datos_seccion.get("disenar_columna_recubrimiento"))     # Esfuerzo de fluencia
    Sc = float(datos_seccion.get("disenar_columna_espaciamiento"))     # Esfuerzo de fluencia
    de = float(datos_seccion.get("disenar_columna_diametro_transversal"))/10     # Esfuerzo de fluencia
    dbe = float(datos_seccion.get("disenar_columna_diametro_longitudinal_2"))/10  # Diametro de refuerzo esquinas
    dbi = float(datos_seccion.get("disenar_columna_diametro_longitudinal_2"))/10  # Diametro de refuerzo interior
    Nb1 = float(datos_seccion.get("disenar_columna_varillasX_2"))  # N° varillas de refuerzo
    Nb2 = float(datos_seccion.get("disenar_columna_varillasY_2"))  # N° varillas de refuerzo
    Nb = (Nb1-2)*2 + Nb2*2             # N° varillas de refuerzo
    NLx = float(datos_seccion.get("disenar_columna_ramalesX"))
    NLy = float(datos_seccion.get("disenar_columna_ramalesY"))

    """ Dimensiones del nucleo """
    dc = h - 2*rec - de              # Altura confinada
    bc = b - 2*rec - de              # Base confinada
    Ss = Sc - de                     # Longitud libre del estribo
    
    # --- Area inefectiva (zona no confinada) ---
    Wx = (bc - de - 2*dbe - (NLx - 2) * dbi) / (NLx - 1)
    Wy = (dc - de - 2*dbe - (NLy - 2) * dbi) / (NLy - 1)
    Ainef = 2 * (NLx - 1) * Wx ** 2 / 6 + 2 * (NLy - 1) * Wy ** 2 / 6

    # --- Area confinada efectiva ---
    Ae = (bc * dc - Ainef) * (1 - Ss / (2 * bc)) * (1 - Ss / (2 * dc))
    
    # --- Cuantia de acero longitudinal (para el nucleo) ---
    pcc = np.pi * (dbe ** 2 + (Nb - 4) * dbi ** 2) / (4 * (dc - de) * (bc - de))
    Acc = bc * dc * (1 - pcc)
    ke = Ae / Acc                     # Coeficiente de confinamiento efectivo
    
    # --- Presiones laterales de confinamiento ---
    psx = (NLx * np.pi * de ** 2) / (4 * dc * Sc)
    psy = (NLy * np.pi * de ** 2) / (4 * bc * Sc)
    f1x = ke * psx * fy
    f1y = ke * psy * fy
    
    # --- Incremento de resistencia por confinamiento -
    f1xfc0 = f1x / fc0
    f1yfc0 = f1y / fc0
    fccfc0 = fccfco(f1xfc0, f1yfc0)
    fcc = fccfc0 * fc0
    ecc = (5 * (fccfc0 - 1) + 1) * ec0
    
    # --- Modulo secante y parámetro r ---
    Esec = fcc / ecc         # Modulo elastico secante
    r = Ec / (Ec - Esec)     # Parámetro r de Mander
    
    # --- Deformacion ultima ecu (modelo Mander) ---
    As_est = np.pi * de**2 / 4
    ps = (As_est * (NLx * dc + NLy * bc)) / (dc * bc * Sc)
    ecu = 0.004 + 1.4 * ps * fy * esu / fcc

    # --- Diagrama esfuerzo-deformacion ---
    ec = np.linspace(0, ecu, 100)
    fc = np.zeros_like(ec)
    x = ec / ecc
    fc = fcc * (x * r) / (r - 1 + x ** r)
    
    return ec, fc
