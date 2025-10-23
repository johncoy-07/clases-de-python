from flask import Flask
from pulp import LpProblem, LpMinimize, LpVariable, LpBinary, LpStatus, lpSum, value, PULP_CBC_CMD

app = Flask(__name__)

@app.route("/")
def modelo_bauxita():
    modelo = LpProblem("Problema_Bauxita", LpMinimize)

    MINAS = ["A", "B", "C"]
    PLANTAS = ["B", "C", "D", "E"]
    ESMALTADO = ["D", "E"]

    cap_mina = {"A": 36000, "B": 52000, "C": 28000}
    cap_planta = {"B": 40000, "C": 20000, "D": 30000, "E": 80000}
    cap_esmaltado = {"D": 4000, "E": 7000}

    costo_explotacion = {"A": 420, "B": 360, "C": 540}
    costo_fijo = {"B": 3000000, "C": 2500000, "D": 4800000, "E": 6000000}
    costo_produccion = {"B": 330, "C": 320, "D": 380, "E": 240}
    costo_esmaltado = {"D": 8500, "E": 5200}

    ctran_b = {
        ("A","B"):400, ("A","C"):2010, ("A","D"):510,  ("A","E"):1920,
        ("B","B"):10,  ("B","C"):630,  ("B","D"):220,  ("B","E"):1510,
        ("C","B"):1630,("C","C"):10,   ("C","D"):620,  ("C","E"):940
    }

    ctran_a = {
        ("B","D"):220,  ("B","E"):1510,
        ("C","D"):620,  ("C","E"):940,
        ("D","D"):0,    ("D","E"):1615,
        ("E","D"):1465, ("E","E"):0
    }

    demanda = {"D": 1000, "E": 1200}
    rend_bauxita = {"A": 0.06, "B": 0.08, "C": 0.062}
    rend_alumina = 0.4

    x = LpVariable.dicts("x", (MINAS, PLANTAS), lowBound=0)
    y = LpVariable.dicts("y", (PLANTAS, ESMALTADO), lowBound=0)
    w = LpVariable.dicts("w", PLANTAS, lowBound=0, upBound=1, cat=LpBinary)

    modelo += (
        lpSum(costo_explotacion[i] * x[i][j] for i in MINAS for j in PLANTAS)
      + lpSum(costo_produccion[j]  * y[j][k] for j in PLANTAS for k in ESMALTADO)
      + lpSum(costo_esmaltado[k]   * y[j][k] for j in PLANTAS for k in ESMALTADO)
      + lpSum(ctran_b[(i, j)]      * x[i][j] for i in MINAS for j in PLANTAS)
      + lpSum(ctran_a[(j, k)]      * y[j][k] for j in PLANTAS for k in ESMALTADO)
      + lpSum(costo_fijo[j]        * w[j]    for j in PLANTAS)
    )

    for i in MINAS:
        modelo += lpSum(x[i][j] for j in PLANTAS) <= cap_mina[i]
    for j in PLANTAS:
        modelo += lpSum(x[i][j] for i in MINAS) <= cap_planta[j] * w[j]
    for k in ESMALTADO:
        modelo += lpSum(y[j][k] for j in PLANTAS) <= cap_esmaltado[k]
    for k in ESMALTADO:
        modelo += lpSum(rend_alumina * y[j][k] for j in PLANTAS) == demanda[k]
    for j in PLANTAS:
        modelo += lpSum(rend_bauxita[i] * x[i][j] for i in MINAS) == lpSum(y[j][k] for k in ESMALTADO)

    modelo.solve(PULP_CBC_CMD(msg=False))

    estado = LpStatus[modelo.status]
    costo = value(modelo.objective)

    resultado = [f"Estado: {estado}", f"Costo total: ${costo:,.2f}\n"]
    resultado.append("Plantas abiertas:")
    for j in PLANTAS:
        resultado.append(f"  {j}: {int(value(w[j]))}")
    resultado.append("\nFlujos de bauxita:")
    for i in MINAS:
        for j in PLANTAS:
            if value(x[i][j]) > 0:
                resultado.append(f"  {i} → {j}: {value(x[i][j]):.2f}")
    resultado.append("\nFlujos de alúmina:")
    for j in PLANTAS:
        for k in ESMALTADO:
            if value(y[j][k]) > 0:
                resultado.append(f"  {j} → {k}: {value(y[j][k]):.2f}")

    return f"<pre>{'<br>'.join(resultado)}</pre>"

if __name__ == "__main__":
    app.run(debug=True)
