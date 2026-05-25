import math
from flask import Flask, render_template, request, jsonify
import sympy as sp

app = Flask(__name__)

def get_newton_iterations(expr_str, x0, max_iter=10, tolerance=1e-7):
    """
    Computes Newton-Raphson iterations and returns both raw numerical matrix 
    data and structured LaTeX string descriptions of the step-by-step substitution.
    """
    try:
        x = sp.Symbol('x')
        # Standardize power syntax cleanly
        expr = sp.sympify(expr_str.replace('^', '**'))
        deriv = sp.diff(expr, x)
        
        f = sp.lambdify(x, expr, 'math')
        df = sp.lambdify(x, deriv, 'math')
    except Exception as e:
        return {"error": f"Invalid mathematical expression syntax: {str(e)}"}

    iterations = []
    xn = float(x0)
    
    for n in range(max_iter):
        try:
            fxn = f(xn)
            dfxn = df(xn)
        except Exception as e:
            return {"error": f"Mathematical evaluation fault at iteration step {n}: {str(e)}"}
        
        # Guard against vertical asymptotes or flat stationary points
        if abs(dfxn) < 1e-12:
            iterations.append({
                "step": n,
                "xn": round(xn, 6),
                "fxn": round(fxn, 6),
                "dfxn": round(dfxn, 6),
                "next_x": "N/A",
                "process_text": f"\\text{{Step }}{n}\\text{{: Slope }} f'({round(xn, 4)}) \\approx 0 \\text{{. Process terminated to avoid division by zero.}}"
            })
            break
            
        next_x = xn - (fxn / dfxn)
        
        # Construct exact substitution rendering string for the UI step panel
        process_text = (
            f"x_{{{n+1}}} = {round(xn, 5)} - \\frac{{{round(fxn, 5)}}}{{{round(dfxn, 5)}}} "
            f"= {round(xn, 5)} - ({round(fxn/dfxn, 5)}) = {round(next_x, 5)}"
        )
        
        iterations.append({
            "step": n,
            "xn": round(xn, 6),
            "fxn": round(fxn, 6),
            "dfxn": round(dfxn, 6),
            "next_x": round(next_x, 6),
            "process_text": process_text
        })
        
        if abs(next_x - xn) < tolerance:
            break
            
        xn = next_x
        
    return {
        "iterations": iterations, 
        "expression": str(sp.latex(expr)), 
        "derivative": str(sp.latex(deriv))
    }

@app.route('/')
def index():
    examples = [
        {
            "id": 1,
            "title": "Finding Cubic Polynomial Roots",
            "equation": "x^3 - 2*x - 5 = 0",
            "expr": "x^3 - 2*x - 5",
            "x0": 2.0,
            "desc": "Newton's historically native example. It begins near x₀ = 2 and showcases devastatingly fast linear convergence."
        },
        {
            "id": 2,
            "title": "Trigonometric Transcendental Roots",
            "equation": "x - 2*sin(x) = 0",
            "expr": "x - 2*sin(x)",
            "x0": 1.5,
            "desc": "Demonstrates solving transcendental formulas. Beware: starting at x₀ = 1.1 hits local bumps/flat areas, throwing values off radically before recovering."
        }
    ]
    return render_template('index.html', examples=examples)

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.get_json() or {}
    expr_str = data.get('expression', 'x^2 - 2')
    try:
        x0 = float(data.get('x0', 1.0))
    except ValueError:
        return jsonify({"error": "Initial guess parameter vector input must be numerical."}), 400
        
    result = get_newton_iterations(expr_str, x0)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)