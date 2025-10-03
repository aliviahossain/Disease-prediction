let probabilityChart = null;



function validateInput(inputEl) {
  const value = parseFloat(inputEl.value);
  let errorMsg = inputEl.nextElementSibling;

  if (!errorMsg || !errorMsg.classList.contains("error-message")) {
    errorMsg = document.createElement("span");
    errorMsg.classList.add("error-message");
    inputEl.insertAdjacentElement("afterend", errorMsg);
  }

  if (isNaN(value) || value < 0 || value > 1) {
    inputEl.classList.add("error");
    errorMsg.textContent = "Enter a value between 0 and 1.";
    return false;
  } else {
    inputEl.classList.remove("error");
    errorMsg.textContent = "";
    return true;
  }
}

// Hide result box whenever user edits input
function attachResetOnInput() {
  const resultDiv = document.getElementById('result');
  const inputs = document.querySelectorAll("input, select");

  inputs.forEach(input => {
    input.addEventListener("input", () => {
      resultDiv.style.display = "none";
      resultDiv.textContent = "";
      document.getElementById('chartContainer').style.display = "none";

    });
  });
}

// Smoothly show result and scroll down
function showResult(message) {
  const resultDiv = document.getElementById('result');
  resultDiv.style.display = "block";
  resultDiv.textContent = message;

  // Smooth scroll into view
  resultDiv.scrollIntoView({ behavior: "smooth", block: "center" });
}

function renderProbabilityChart(prior, posterior) {
    const chartContainer = document.getElementById('chartContainer');
    const ctx = document.getElementById('probabilityChartCanvas').getContext('2d');

    if (probabilityChart) {
        probabilityChart.destroy();
    }

    chartContainer.style.display = 'block';

    probabilityChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Prior Probability', 'Posterior Probability'],
            datasets: [{
                label: 'Probability (%)',
                data: [prior * 100, posterior * 100],
                backgroundColor: ['rgba(54, 162, 235, 0.6)', 'rgba(75, 192, 192, 0.6)'],
                borderColor: ['rgba(54, 162, 235, 1)', 'rgba(75, 192, 192, 1)'],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    ticks: { callback: function(value) { return value + '%' } }
                }
            }
        }
    });
    chartContainer.scrollIntoView({ behavior: "smooth", block: "center" });
}

// Use preset hospital data
function usePreset() {
  const diseaseSelect = document.getElementById('diseaseSelect');
  const selectedDisease = diseaseSelect.value;

  if (!selectedDisease) {
    diseaseSelect.classList.add("error");
    return;
  } else {
    diseaseSelect.classList.remove("error");
  }

  fetch('/preset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ disease: selectedDisease })
  })
  .then(response => response.json())
  .then(data => {
    if (data.error) {
      showResult('Error: ' + data.error);
    } else {
      console.log("-----------------------------------------------------------------------");
      console.log(`Probability of disease given positive test for ${selectedDisease}: ${data.p_d_given_pos}`);
      console.log("-----------------------------------------------------------------------");
      showResult(`Probability of disease given positive test for ${selectedDisease}: ${data.p_d_given_pos}`);
      renderProbabilityChart(data.prior, data.p_d_given_pos);

    }
  })
  .catch(error => {
    showResult('Fetch error: ' + error);
  });
}

// Calculate disease probability from custom input
function calculateDisease() {
  const pDInput = document.getElementById('pD');
  const sensInput = document.getElementById('sensitivity');
  const fpInput = document.getElementById('falsePositive');

  const validP = validateInput(pDInput);
  const validSens = validateInput(sensInput);
  const validFP = validateInput(fpInput);

  if (!(validP && validSens && validFP)) return;

  fetch('/disease', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pD: parseFloat(pDInput.value),
      sensitivity: parseFloat(sensInput.value),
      falsePositive: parseFloat(fpInput.value)
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.error) {
      showResult('Error: ' + data.error);
    } else {
      console.log("-----------------------------------------------------------------------");
      console.log(`++++++++++++++  Probability of disease given positive test: ${data.p_d_given_result}`);
      console.log("-----------------------------------------------------------------------");
      showResult(`Probability of disease given positive test: ${data.p_d_given_result}`);
      const prior = parseFloat(pDInput.value);
        renderProbabilityChart(prior, data.p_d_given_result);
    }
  })
  .catch(error => {
    showResult('Fetch error: ' + error);
  }); 
}

// Attach reset logic after page loads
window.addEventListener("DOMContentLoaded", attachResetOnInput);
