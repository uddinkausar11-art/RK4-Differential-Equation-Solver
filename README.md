# RK4 Differential Equation Solver

A complete Python Flask web application for solving first-order ordinary differential equations using the fourth-order Runge-Kutta (RK4) numerical method.

## Features

- Modern responsive web UI
- User-defined differential equation `dy/dx = f(x,y)`
- Initial x and y values
- Step size and iterations
- RK4 K1, K2, K3, K4 calculations
- Numerical result table
- Interactive solution graph
- Exact symbolic solution when SymPy can find one
- Absolute error analysis when an exact solution is available
- CSV export
- Built-in example equations
- Step-by-step RK4 explanation

## Supported equation examples

```text
x + y
x - y
x*y
x**2 + y
sin(x) + y
cos(x) - y
exp(x) + y
sqrt(x) + y
```

Use `**` for powers, for example `x**2`. The application also converts `^` to `**`.

## Run on Windows

1. Install Python 3.
2. Open this folder in VS Code.
3. Open Terminal.
4. Create a virtual environment:

```bash
python -m venv venv
```

5. Activate it:

```bash
venv\Scripts\activate
```

6. Install packages:

```bash
pip install -r requirements.txt
```

7. Run:

```bash
python app.py
```

8. Open:

```text
http://127.0.0.1:5000
```

## Recommended presentation demo

Equation:
`x + y`

Initial x:
`0`

Initial y:
`1`

Step size:
`0.1`

Iterations:
`10`

The application shows the RK4 calculation table, graph, exact solution when available, and error analysis.

## Algorithm

For dy/dx = f(x,y):

K1 = h f(xn, yn)

K2 = h f(xn + h/2, yn + K1/2)

K3 = h f(xn + h/2, yn + K2/2)

K4 = h f(xn + h, yn + K3)

yn+1 = yn + (K1 + 2K2 + 2K3 + K4)/6

xn+1 = xn + h
