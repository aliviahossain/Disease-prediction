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

function renderChart(prior, posterior) {
  const canvas = document.getElementById('probChart');
  if (!canvas) return;

  if (typeof prior !== 'number' || isNaN(prior) || typeof posterior !== 'number' || isNaN(posterior)) {
      // Optionally, clear chart or show empty chart
      if (window.probChart && typeof window.probChart.destroy === 'function') {
          window.probChart.destroy();
      }
      return;
  }

  const ctx = document.getElementById('probChart').getContext('2d');

  if (window.probChart && typeof window.probChart.destroy === 'function') {
      window.probChart.destroy();
  }

  window.probChart = new Chart(ctx, {
      type: 'bar',
      data: {
          labels: ['Prior Probability', 'Posterior Probability'],
          datasets: [{
              label: 'Probability (%)',
              data: [prior * 100, posterior * 100],
              backgroundColor: ['#60a5fa', '#34d399']
          }]
      },
      options: {
          scales: {
              y: {
                  beginAtZero: true,
                  max: 100
              }
          }
      }
  });
}


// Attach reset logic after page loads
window.addEventListener("DOMContentLoaded", attachResetOnInput);

$('#diseaseSelect').select2({
    placeholder: "Type to search disease...",
    width: '100%',
    allowClear: true,
    dropdownParent: $('#diseaseSelect').parent(),
}).on('select2:open', function() {
    // Use a timeout to ensure the search field is fully rendered
    setTimeout(function() {
        // Find the search field inside the currently open dropdown
        const searchField = $('.select2-container--open .select2-search__field');

        // Set the placeholder text for the search box
        searchField.attr('placeholder', 'Type here to search...');

        // Set focus to place the cursor in the search box
        searchField.focus();
        
    }, 50); // A 50ms delay for reliability
});