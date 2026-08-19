let lastRows = [];
let chart = null;

const $ = (id) => document.getElementById(id);

function fmt(value) {
    if (value === null || value === undefined) return "—";
    const n = Number(value);
    if (!Number.isFinite(n)) return "—";
    return n.toFixed(8);
}

function showError(message) {
    $("errorBox").textContent = message;
    $("errorBox").classList.remove("hidden");
}

function hideError() {
    $("errorBox").classList.add("hidden");
}

document.querySelectorAll("[data-equation]").forEach(btn => {
    btn.addEventListener("click", () => {
        $("equation").value = btn.dataset.equation;
    });
});

$("resetBtn").addEventListener("click", () => {
    $("equation").value = "x + y";
    $("x0").value = "0";
    $("y0").value = "1";
    $("h").value = "0.1";
    $("iterations").value = "10";
    $("resultsArea").classList.add("hidden");
    hideError();
    lastRows = [];
    if (chart) {
        chart.destroy();
        chart = null;
    }
    window.scrollTo({ top: 0, behavior: "smooth" });
});

$("solverForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    hideError();

    const button = $("solveBtn");
    $("solveText").classList.add("hidden");
    $("spinner").classList.remove("hidden");
    button.disabled = true;

    const payload = {
        equation: $("equation").value.trim(),
        x0: $("x0").value,
        y0: $("y0").value,
        h: $("h").value,
        iterations: $("iterations").value
    };

    try {
        const response = await fetch("/api/solve", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();

        if (!response.ok || !data.success) {
            throw new Error(data.error || "Unable to solve the equation.");
        }

        renderResults(data);
    } catch (error) {
        showError(error.message);
    } finally {
        button.disabled = false;
        $("solveText").classList.remove("hidden");
        $("spinner").classList.add("hidden");
    }
});

function renderResults(data) {
    lastRows = data.rows;
    $("resultsArea").classList.remove("hidden");

    const finalRow = data.rows[data.rows.length - 1];

    $("finalX").textContent = fmt(finalRow.x);
    $("finalY").textContent = fmt(finalRow.y);
    $("stepCount").textContent = data.iterations;

    const body = $("resultBody");
    body.innerHTML = "";

    data.rows.forEach(row => {
        const tr = document.createElement("tr");
        tr.innerHTML = `
            <td>${row.step}</td>
            <td>${fmt(row.x)}</td>
            <td>${fmt(row.y)}</td>
            <td>${fmt(row.k1)}</td>
            <td>${fmt(row.k2)}</td>
            <td>${fmt(row.k3)}</td>
            <td>${fmt(row.k4)}</td>
        `;
        body.appendChild(tr);
    });

    renderChart(data.rows);

    $("exactSolution").textContent =
        data.exact_solution
            ? `y(x) = ${data.exact_solution}`
            : "No symbolic exact solution was found for this equation.";

    if (data.errors && data.errors.length) {
        const valid = data.errors
            .map(x => x.absolute_error)
            .filter(x => x !== null && Number.isFinite(x));

        $("maxError").textContent =
            valid.length ? fmt(Math.max(...valid)) : "—";
    } else {
        $("maxError").textContent = "—";
    }

    populateSimulation(data.rows);

    $("resultsArea").scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderChart(rows) {
    const ctx = $("solutionChart").getContext("2d");

    if (chart) chart.destroy();

    chart = new Chart(ctx, {
        type: "line",
        data: {
            datasets: [{
                label: "RK4 Numerical Solution",
                data: rows.map(r => ({ x: r.x, y: r.y })),
                borderWidth: 3,
                pointRadius: 3,
                tension: 0.2,
                fill: false
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            parsing: false,
            scales: {
                x: {
                    type: "linear",
                    title: { display: true, text: "x" }
                },
                y: {
                    title: { display: true, text: "y" }
                }
            }
        }
    });
}

function populateSimulation(rows) {
    const select = $("stepSelector");
    select.innerHTML = "";

    rows.slice(1).forEach(row => {
        const option = document.createElement("option");
        option.value = row.step;
        option.textContent = `Iteration ${row.step}`;
        select.appendChild(option);
    });

    select.onchange = () => showSimulation(Number(select.value));

    if (rows.length > 1) {
        select.value = "1";
        showSimulation(1);
    }
}

function showSimulation(step) {
    const row = lastRows.find(r => r.step === step);
    if (!row) return;

    $("simStep").textContent = row.step;
    $("simK1").textContent = fmt(row.k1);
    $("simK2").textContent = fmt(row.k2);
    $("simK3").textContent = fmt(row.k3);
    $("simK4").textContent = fmt(row.k4);
}

$("downloadBtn").addEventListener("click", async () => {
    if (!lastRows.length) return;

    try {
        const response = await fetch("/api/csv", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ rows: lastRows })
        });

        if (!response.ok) throw new Error("Could not create CSV.");

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "rk4_results.csv";
        document.body.appendChild(a);
        a.click();
        a.remove();
        URL.revokeObjectURL(url);
    } catch (error) {
        showError(error.message);
    }
});
