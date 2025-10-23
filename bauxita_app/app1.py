from flask import Flask, request, render_template
from pulp import *

app = Flask(_name_)

@app.route("/")

def hello_world():

    modelo=LpProblem("ejemplo_incial",LpMinimize)

    x1 = LpVariable("Porcentaje de pollo",0)
    x2 = LpVariable("Porcentaje de carne",0)

    modelo+= 0.013*x1 + 0.008*x2 # Función objetivo

    #Restricciones
    modelo += x1 + x2==100
    modelo += 0.100 * x1 + 0.200 * x2 >= 8.0, "Requerimiento de proteina"
    modelo += 0.080 * x1 + 0.100 * x2 >= 6.0, "Requerimiento de grasa"
    modelo += 0.001 * x1 + 0.005 * x2 <= 2.0, "Requerimiento de fibra"
    modelo += 0.002 * x1 + 0.005 * x2 <= 0.4, "Requerimiento de sal"

    modelo.solve() 
   
    #return f"El resultado de la función objetivo es: {value(modelo.objective)}, El valor de x1 es: {x1.varValue}, el valor de x2 es: {x2.varValue}"
    return render_template("mezcla.html")