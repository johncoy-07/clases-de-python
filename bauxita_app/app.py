from flask import Flask, request, Response
from pulp import *

app = Flask(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# GET: muestra un formulario mínimo
# POST: resuelve el modelo y devuelve TEXTO PLANO con el resultado
# ──────────────────────────────────────────────────────────────────────────────
@app.route("/", methods=["GET", "POST"])
def modelo_bauxita():
    if request.method == "GET":
        # Formulario mínimo (HTML simple)
        html = """
        <h2>Problema de la Bauxita</h2>
        <form method="POST">
          <label>Coste fijo planta B: <input type="number" step="any" name="costoB" required></label><br>
          <label>Coste fijo planta C: <input type="number" step="any" name="costoC" required></label><br>
          <label>Coste fijo planta D: <input type="number" step="any" name="costoD" required></label><br>
          <label>Coste fijo planta E: <input type="number" step="any" name="costoE" required></label><br><br>
          <button type="submit">Ejecutar modelo</button>
        </form>
        """
        return html

    # POST: toma datos y resuelve
    try:
        costo_fijo_B = float(request.form["costoB"])
        costo_fijo_C = float(request.form["costoC"])
        costo_fijo_D = float(request.form["costoD"])
        costo_fijo_E = float(request.form["costoE"])
    except Exception:
        return Response("Error: ingrese números válidos.", mimetype="text/plain")

    # ------------------ MODELO ------------------
    modelo = LpProblem("Problema_Bauxita", LpMinimize)

    MINAS = ["A", "B", "C"]
    PLANTAS = ["B", "C", "D", "E"]
    ESMALTADO = ["D", "E"]

    cap_mina = {"A": 36000, "B": 52000, "C": 28000}
    cap_planta = {"B": 40000, "C": 20000, "D": 30000, "E": 80000}
    cap_esmaltado = {"D": 4000, "E": 7000}

    costo_explotacion = {"A": 420, "B": 360, "C": 540}
    costo_fijo = {"B": costo_fijo_B, "C": costo_fijo_C, "D": costo_fijo_D, "E": costo_fijo_E}
    costo_produccion = {"B": 330, "C": 320, "D": 380, "E": 240}
    costo_esmaltado = {"D": 8500, "E": 5200}

    ctran_b = {
        ("A", "B"): 400, ("A", "C"): 2010, ("A", "D"): 510, ("A", "E"): 1920,
        ("B", "B"): 10, ("B", "C"): 630, ("B", "D"): 220, ("B", "E"): 1510,
        ("C", "B"): 1630, ("C", "C"): 10, ("C", "D"): 620, ("C", "E"): 940
    }

    ctran_a = {
        ("B", "D"): 220, ("B", "E"): 1510,
        ("C", "D"): 620, ("C", "E"): 940,
        ("D", "D"): 0, ("D", "E"): 1615,
        ("E", "D"): 1465, ("E", "E"): 0
    }

    demanda = {"D": 1000, "E": 1200}
    rend_bauxita = {"A": 0.06, "B": 0.08, "C": 0.062}

    # Variables
    x = LpVariable.dicts("x", (MINAS, PLANTAS), lowBound=0)
    y = LpVariable.dicts("y", (PLANTAS, ESMALTADO), lowBound=0)
    w = LpVariable.dicts("w", PLANTAS, lowBound=0, upBound=1, cat=LpBinary)

    # Objetivo
    modelo += (
        lpSum(costo_explotacion[i] * x[i][j] for i in MINAS for j in PLANTAS)
        + lpSum(costo_produccion[j] * y[j][k] for j in PLANTAS for k in ESMALTADO)
        + lpSum(costo_esmaltado[k] * y[j][k] for j in PLANTAS for k in ESMALTADO)
        + lpSum(ctran_b[(i, j)] * x[i][j] for i in MINAS for j in PLANTAS)
        + lpSum(ctran_a[(j, k)] * y[j][k] for j in PLANTAS for k in ESMALTADO)
        + lpSum(costo_fijo[j] * w[j] for j in PLANTAS)
    )

    # Restricciones
    for i in MINAS:
        modelo += lpSum(x[i][j] for j in PLANTAS) <= cap_mina[i]

    for j in PLANTAS:
        modelo += lpSum(x[i][j] for i in MINAS) <= cap_planta[j] * w[j]

    for k in ESMALTADO:
        modelo += lpSum(y[j][k] for j in PLANTAS) == demanda[k]

    for j in PLANTAS:
        modelo += lpSum(rend_bauxita[i] * x[i][j] for i in MINAS) == lpSum(y[j][k] for k in ESMALTADO)

    # Resolver
    modelo.solve(PULP_CBC_CMD(msg=0))
    estado = LpStatus[modelo.status]
    z = value(modelo.objective)
    plantas_abiertas = {j: int(w[j].value()) for j in PLANTAS}
    x_vals = {(i, j): x[i][j].value() for i in MINAS for j in PLANTAS}
    y_vals = {(j, k): y[j][k].value() for j in PLANTAS for k in ESMALTADO}

    # Respuesta en TEXTO PLANO
    lines = []
    lines.append(f"Estado: {estado}")
    lines.append(f"Costo total: ${z:,.2f}\n")
    lines.append("Plantas abiertas:")
    for j in PLANTAS:
        lines.append(f"  {j}: {plantas_abiertas[j]}")
    lines.append("\nFlujos de bauxita:")
    for i in MINAS:
        for j in PLANTAS:
            if x_vals[(i, j)] and x_vals[(i, j)] > 1e-6:
                lines.append(f"  {i} -> {j}: {x_vals[(i, j)]:.2f}")
    lines.append("\nFlujos de alúmina:")
    for j in PLANTAS:
        for k in ESMALTADO:
            if y_vals[(j, k)] and y_vals[(j, k)] > 1e-6:
                lines.append(f"  {j} -> {k}: {y_vals[(j, k)]:.2f}")

    txt = "\n".join(lines)
    return Response(txt, mimetype="text/plain")


if __name__ == "__main__":
    app.run(debug=True)

