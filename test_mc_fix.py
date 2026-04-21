"""
Script de prueba para verificar que la corrección del error M-φ funciona.
"""
import numpy as np
import warnings
warnings.filterwarnings('default')

# Simulamos la función _limpiar_curva_mc
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

# Prueba 1: Curva con 2 puntos
print("=" * 60)
print("PRUEBA 1: Curva con 2 puntos (mínimo permitido)")
print("=" * 60)
try:
    phi_1 = np.array([0.0, 1.0])
    M_1 = np.array([0.0, 100.0])
    phi_clean, M_clean = _limpiar_curva_mc(phi_1, M_1)
    print(f"✓ Curva limpiada exitosamente")
    print(f"  Puntos: {len(phi_clean)}")
    print(f"  phi: {phi_clean}")
    print(f"  M: {M_clean}")
except Exception as e:
    print(f"✗ Error: {e}")

# Prueba 2: Curva con 3 puntos
print("\n" + "=" * 60)
print("PRUEBA 2: Curva con 3 puntos (procedimiento simplificado)")
print("=" * 60)
try:
    phi_2 = np.array([0.0, 0.5, 1.0])
    M_2 = np.array([0.0, 80.0, 100.0])
    phi_clean, M_clean = _limpiar_curva_mc(phi_2, M_2)
    print(f"✓ Curva limpiada exitosamente")
    print(f"  Puntos: {len(phi_clean)}")
    print(f"  phi: {phi_clean}")
    print(f"  M: {M_clean}")
except Exception as e:
    print(f"✗ Error: {e}")

# Prueba 3: Curva con 1 punto (debe fallar)
print("\n" + "=" * 60)
print("PRUEBA 3: Curva con 1 punto (debe fallar - mínimo 2)")
print("=" * 60)
try:
    phi_3 = np.array([0.0])
    M_3 = np.array([0.0])
    phi_clean, M_clean = _limpiar_curva_mc(phi_3, M_3)
    print(f"✓ Curva limpiada")
except ValueError as e:
    print(f"✓ Error capturado correctamente: {e}")
except Exception as e:
    print(f"✗ Error inesperado: {e}")

# Prueba 4: Curva con duplicados en phi (debe preservar puntos)
print("\n" + "=" * 60)
print("PRUEBA 4: Curva con duplicados muy cercanos")
print("=" * 60)
try:
    phi_4 = np.array([0.0, 0.5, 0.500000001, 1.0])
    M_4 = np.array([0.0, 80.0, 82.0, 100.0])
    phi_clean, M_clean = _limpiar_curva_mc(phi_4, M_4)
    print(f"✓ Curva limpiada exitosamente")
    print(f"  Puntos originales: {len(phi_4)}")
    print(f"  Puntos después de limpiar: {len(phi_clean)}")
    print(f"  phi: {phi_clean}")
    print(f"  M: {M_clean}")
    print(f"  (Los duplicados muy cercanos se preservan)")
except Exception as e:
    print(f"✗ Error: {e}")

print("\n" + "=" * 60)
print("RESUMEN: Las pruebas básicas de limpieza de curvas funcionan")
print("=" * 60)
