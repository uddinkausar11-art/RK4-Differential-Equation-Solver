from flask import Flask, render_template, request, jsonify, Response
import sympy as sp
import math
import csv
import io

app = Flask(__name__)

ALLOWED_LOCALS = {
    "x": sp.Symbol("x"),
    "y": sp.Symbol("y"),
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
    "exp": sp.exp,
    "log": sp.log,
    "ln": sp.log,
    "sqrt": sp.sqrt,
    "abs": sp.Abs,
    "pi": sp.pi,
    "E": sp.E,
}

X = ALLOWED_LOCALS["x"]
Y = ALLOWED_LOCALS["y"]


def parse_equation(equation):
    equation = equation.strip().replace("^", "**")
    if not equation:
        raise ValueError("Please enter an equation.")

    expression = sp.sympify(equation, locals=ALLOWED_LOCALS)

    # Only x and y are allowed as variables.
    unknowns = expression.free_symbols - {X, Y}
    if unknowns:
        names = ", ".join(sorted(str(s) for s in unknowns))
        raise ValueError(f"Unsupported variable(s): {names}")

    return expression


def make_function(expression):
    return sp.lambdify((X, Y), expression, modules=["math"])


def rk4(f, x0, y0, h, iterations):
    rows = [{
        "step": 0,
        "x": x0,
        "y": y0,
        "k1": None,
        "k2": None,
        "k3": None,
        "k4": None
    }]

    x, y = x0, y0

    for i in range(1, iterations + 1):
        try:
            k1 = h * float(f(x, y))
            k2 = h * float(f(x + h / 2, y + k1 / 2))
            k3 = h * float(f(x + h / 2, y + k2 / 2))
            k4 = h * float(f(x + h, y + k3))
        except Exception as exc:
            raise ValueError(
                f"Could not evaluate the equation at iteration {i}. "
                f"Check the domain of your equation."
            ) from exc

        new_y = y + (k1 + 2*k2 + 2*k3 + k4) / 6
        new_x = x + h

        values = [k1, k2, k3, k4, new_x, new_y]
        if not all(math.isfinite(v) for v in values):
            raise ValueError(
                f"The calculation became invalid at iteration {i}. "
                "Try a smaller step size."
            )

        x, y = new_x, new_y

        rows.append({
            "step": i,
            "x": x,
            "y": y,
            "k1": k1,
            "k2": k2,
            "k3": k3,
            "k4": k4
        })

    return rows


def exact_solution(expression, x0, y0):
    try:
        ode = sp.Eq(sp.diff(Y, X), expression)
        sol = sp.dsolve(ode, ics={Y.subs(X, x0): y0})
        if sol and sol.rhs is not None:
            return sp.sstr(sp.simplify(sol.rhs))
    except Exception:
        pass
    return None


def calculate_error(rows, exact_expr):
    if exact_expr is None:
        return None

    exact_fn = sp.lambdify(X, exact_expr, modules=["math"])
    errors = []

    try:
        for row in rows:
            exact_value = float(exact_fn(row["x"]))
            if math.isfinite(exact_value):
                errors.append({
                    "x": row["x"],
                    "numerical": row["y"],
                    "exact": exact_value,
                    "absolute_error": abs(row["y"] - exact_value)
                })
            else:
                errors.append({
                    "x": row["x"],
                    "numerical": row["y"],
                    "exact": None,
                    "absolute_error": None
                })
    except Exception:
        return None

    return errors


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/solve")
def solve():
    try:
        data = request.get_json(force=True)

        equation = str(data.get("equation", "")).strip()
        x0 = float(data.get("x0"))
        y0 = float(data.get("y0"))
        h = float(data.get("h"))
        iterations = int(data.get("iterations"))

        if not math.isfinite(x0) or not math.isfinite(y0):
            raise ValueError("Initial x and y must be finite numbers.")

        if not math.isfinite(h) or h <= 0:
            raise ValueError("Step size must be greater than 0.")

        if iterations < 1 or iterations > 1000:
            raise ValueError("Iterations must be between 1 and 1000.")

        expression = parse_equation(equation)
        f = make_function(expression)

        # Test initial point.
        test = float(f(x0, y0))
        if not math.isfinite(test):
            raise ValueError("The equation is not valid at the initial point.")

        rows = rk4(f, x0, y0, h, iterations)
        exact_expr = exact_solution(expression, x0, y0)
        errors = calculate_error(rows, exact_expr)

        return jsonify({
            "success": True,
            "equation": sp.sstr(expression),
            "initial": {"x": x0, "y": y0},
            "step_size": h,
            "iterations": iterations,
            "rows": rows,
            "exact_solution": exact_expr,
            "errors": errors
        })

    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception as exc:
        return jsonify({
            "success": False,
            "error": f"Unable to solve the equation: {exc}"
        }), 400


@app.post("/api/csv")
def csv_export():
    try:
        data = request.get_json(force=True)
        rows = data.get("rows", [])

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Step", "x", "y", "K1", "K2", "K3", "K4"])

        for row in rows:
            writer.writerow([
                row.get("step"),
                row.get("x"),
                row.get("y"),
                row.get("k1"),
                row.get("k2"),
                row.get("k3"),
                row.get("k4")
            ])

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition":
                    "attachment; filename=rk4_results.csv"
            }
        )
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 400


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
