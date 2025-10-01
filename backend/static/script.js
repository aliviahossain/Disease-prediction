// Use preset data from hospital_data.csv via backend /preset route
function usePreset() {
  const diseaseSelect = document.getElementById('diseaseSelect');
  const selectedDisease = diseaseSelect.value;
  const resultDiv = document.getElementById('result');

  if (!selectedDisease) {
    alert('Please select a disease from the dropdown.');
    return;
  }

  fetch('/preset', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ disease: selectedDisease })
  })
  .then(response => response.json())
  .then(data => {
    if (data.error) {
      resultDiv.innerText = 'Error: ' + data.error;
    } else {
      resultDiv.innerText = `Probability of disease given positive test for ${selectedDisease}: ${data.p_d_given_pos}`;
    }
  })
  .catch(error => {
    resultDiv.innerText = 'Fetch error: ' + error;
  });
}

// Calculate disease probability from user input via backend /disease route
function calculateDisease() {
  const pD = parseFloat(document.getElementById('pD').value);
  const sensitivity = parseFloat(document.getElementById('sensitivity').value);
  const falsePositive = parseFloat(document.getElementById('falsePositive').value);
  const resultDiv = document.getElementById('result');

  // Basic validation
  if (
    isNaN(pD) || pD < 0 || pD > 1 ||
    isNaN(sensitivity) || sensitivity < 0 || sensitivity > 1 ||
    isNaN(falsePositive) || falsePositive < 0 || falsePositive > 1
  ) {
    alert('Please enter valid probabilities between 0 and 1.');
    return;
  }

  fetch('/disease', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pD: pD,
      sensitivity: sensitivity,
      falsePositive: falsePositive
    })
  })
  .then(response => response.json())
  .then(data => {
    if (data.error) {
      resultDiv.innerText = 'Error: ' + data.error;
    } else {
      resultDiv.innerText = `Probability of disease given positive test: ${data.p_d_given_result}`;
    }
  })
  .catch(error => {
    resultDiv.innerText = 'Fetch error: ' + error;
  });
}


