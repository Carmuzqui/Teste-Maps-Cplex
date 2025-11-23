import sys
import os

print("--- Configurando Entorno CPLEX Manualmente ---")

# ---------------------------------------------------------
# PASO 1: INYECCIÓN DE VARIABLES (El truco clave)
# ---------------------------------------------------------
# Definimos la ruta raíz donde está instalado CPLEX Studio
cplex_root = r"C:\Program Files\IBM\ILOG\CPLEX_Studio2212"

# Inyectamos la variable que docplex busca desesperadamente
os.environ['CPLEX_STUDIO_DIR2212'] = cplex_root

# También añadimos la carpeta bin al PATH de este proceso python específico
cplex_bin = os.path.join(cplex_root, r"cplex\bin\x64_win64")
os.environ['PATH'] = cplex_bin + os.pathsep + os.environ['PATH']

print(f"Ruta inyectada: {cplex_root}")
print("Importando docplex...")

# ---------------------------------------------------------
# PASO 2: EJECUCIÓN DEL MODELO
# ---------------------------------------------------------
from docplex.mp.model import Model

try:
    mdl = Model(name='Test_Final_Mina')
    x = mdl.continuous_var(name='x')
    y = mdl.continuous_var(name='y')
    
    mdl.maximize(x + y)
    mdl.add_constraint(x + 2*y <= 30)
    mdl.add_constraint(x - y >= 5)

    # Solo pedimos que nos muestre el log para confirmar que corre
    mdl.context.solver.log_output = True
    
    print("\nIntentando resolver (Docplex debería auto-detectar el exe ahora)...")
    sol = mdl.solve()

    if sol:
        print("\n✅ ¡VICTORIA! CPLEX Local funcionó correctamente.")
        print(f"Objetivo: {sol.objective_value}")
    else:
        print("\n⚠️ El modelo no se resolvió. Detalles:")
        print(mdl.get_solve_details())

except Exception as e:
    print("\n❌ Error:")
    print(e)