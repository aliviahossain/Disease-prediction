let probabilityChart = null;
let sensitivityChart = null;

// Store last calculation data for AI recommendations
let lastCalculationData = {
  diseaseName: null,
  priorProbability: null,
  posteriorProbability: null,
  testResult: 'positive'
};

// LocalStorage key for persisting calculator state
const STORAGE_KEY = "calculator_last_state";

// Tracks whether AI-generated recommendations have already been created
let contentGenerated = false;

// ============================================
// Dark Mode Toggle Functionality (Removed - handled globally in base.html)
// ============================================

// ============================================
// Dashboard Menu Functionality
// ============================================
function initDashboardMenu() {
  const menuToggle = document.getElementById('dashboardMenuToggle');
  const dropdown = document.getElementById('dashboardDropdown');

  if (menuToggle && dropdown) {
    menuToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('show');
      const isExpanded = dropdown.classList.contains('show');
      menuToggle.setAttribute('aria-expanded', isExpanded);
    });

    document.addEventListener('click', (e) => {
      if (!menuToggle.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove('show');
        menuToggle.setAttribute('aria-expanded', 'false');
      }
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && dropdown.classList.contains('show')) {
        dropdown.classList.remove('show');
        menuToggle.setAttribute('aria-expanded', 'false');
        menuToggle.focus();
      }
    });
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDashboardMenu);
} else {
  initDashboardMenu();
}

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

function attachResetOnInput() {
  const resultDiv = document.getElementById('result');
  const recommendationsContainer = document.getElementById('recommendationsContainer');
  const inputs = document.querySelectorAll("input, select");

  inputs.forEach(input => {
    input.addEventListener("input", () => {
      resultDiv.style.display = "none";
      resultDiv.textContent = "";
      document.getElementById('chartContainer').style.display = "none";
      if (recommendationsContainer) {
        recommendationsContainer.style.display = "none";
      }
    });
  });
}

function showResult(message) {
  const resultDiv = document.getElementById('result');
  resultDiv.textContent = message;
  resultDiv.classList.add('visible');
  setTimeout(() => {
    resultDiv.scrollIntoView({ behavior: "smooth", block: "center" });
  }, 100);
}

function renderProbabilityChart(prior, posterior) {
  const chartContainer = document.getElementById('chartContainer');
  const ctx = document.getElementById('probabilityChartCanvas').getContext('2d');

  if (probabilityChart) {
    probabilityChart.destroy();
  }

  chartContainer.classList.remove('hidden');
  chartContainer.classList.add('visible');

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
          ticks: { callback: function (value) { return value + '%' } }
        }
      }
    }
  });
}

// ============================================
// Prior Sensitivity Analysis
// ============================================

function renderSensitivityChart(currentPrior, sensitivity, falsePositive, testResult) {
  const sensCont = document.getElementById('sensitivityContainer');
  const sensCanvas = document.getElementById('sensitivityChartCanvas');
  if (!sensCont || !sensCanvas) return;
  sensCont.style.display = 'block';
  sensCont.classList.remove('hidden');
  sensCont.classList.add('visible');
  const sensitivityContainer = document.getElementById('sensitivityContainer');
  const sensitivityCanvas = document.getElementById('sensitivityChartCanvas');

  if (!sensCont || !sensCanvas) return;

  if (!sensCont || !sensCanvas) return;

  const posteriors = [];
  const labels = [];
  let currentIndex = Math.round(currentPrior * 100) - 1;
  if (currentIndex < 0) currentIndex = 0;
  if (currentIndex > 49) currentIndex = 49;

  for (let i = 1; i <= 50; i++) {
    const prior = i / 100;
    const specificity = 1 - falsePositive;
    let numerator, denominator;

    if (testResult === 'positive') {
      numerator = sensitivity * prior;
      denominator = numerator + (falsePositive * (1 - prior));
    } else {
      numerator = (1 - sensitivity) * prior;
      denominator = numerator + (specificity * (1 - prior));
    }

    const posterior = denominator === 0 ? 0 : numerator / denominator;
    posteriors.push(posterior * 100);
    labels.push(i + '%');
  }

  const currentPosterior = posteriors[currentIndex] || 0;

  if (sensitivityChart) {
    sensitivityChart.destroy();
  }

  sensCont.classList.remove('hidden');
  sensCont.classList.add('visible');

  const ctx = sensCanvas.getContext('2d');
  sensitivityChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Posterior Probability',
          data: posteriors,
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.4,
          pointRadius: 0
        },
        {
          label: 'Your Current Prior',
          data: Array(50).fill(null).map((_, i) =>
            i === currentIndex ? currentPosterior : null
          ),
          borderColor: 'rgba(255, 99, 132, 1)',
          backgroundColor: 'rgba(255, 99, 132, 1)',
          pointRadius: Array(50).fill(0).map((_, i) =>
            i === currentIndex ? 10 : 0
          ),
          pointHoverRadius: 12,
          showLine: false
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: true },
        tooltip: {
          callbacks: {
            label: function (context) {
              return context.dataset.label + ': ' +
                context.parsed.y.toFixed(1) + '%';
            }
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          title: {
            display: true,
            text: 'Posterior Probability (%)'
          },
          ticks: { callback: value => value + '%' }
        },
        x: {
          title: {
            display: true,
            text: 'Prior Probability (Disease Prevalence)'
          }
        }
      }
    }
  });

  const fixedSensitivityEl = document.getElementById('fixedSensitivity');
  const fixedFPREl = document.getElementById('fixedFPR');
  const currentPriorDisplayEl = document.getElementById('currentPriorDisplay');

  if (fixedSensitivityEl) fixedSensitivityEl.textContent = (sensitivity * 100).toFixed(0) + '%';
  if (fixedFPREl) fixedFPREl.textContent = (falsePositive * 100).toFixed(0) + '%';
  if (currentPriorDisplayEl) currentPriorDisplayEl.textContent = (currentPrior * 100).toFixed(0) + '%';
}

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
        const pDSlider = document.getElementById('pDSlider');
        const pDInput = document.getElementById('pD');
        const sensitivitySlider = document.getElementById('sensitivitySlider');
        const sensitivityInput = document.getElementById('sensitivity');
        const falsePositiveSlider = document.getElementById('falsePositiveSlider');
        const falsePositiveInput = document.getElementById('falsePositive');

        if (pDSlider && pDInput && data.prior !== undefined) {
          pDSlider.value = data.prior;
          pDInput.value = data.prior;
          updateSliderValue('pDValue', data.prior);
        }

        if (sensitivitySlider && sensitivityInput && data.sensitivity !== undefined) {
          sensitivitySlider.value = data.sensitivity;
          sensitivityInput.value = data.sensitivity;
          updateSliderValue('sensitivityValue', data.sensitivity);
        }

        if (falsePositiveSlider && falsePositiveInput && data.falsePositive !== undefined) {
          falsePositiveSlider.value = data.falsePositive;
          falsePositiveInput.value = data.falsePositive;
          updateSliderValue('falsePositiveValue', data.falsePositive);
        }

        resetResultDisplay();

        const checkBtn = document.getElementById('checkButton');
        if (checkBtn) {
          checkBtn.classList.add('pulse-highlight');
          setTimeout(() => checkBtn.classList.remove('pulse-highlight'), 1500);
        }

        lastCalculationData = {
          diseaseName: selectedDisease,
          priorProbability: data.prior,
          posteriorProbability: data.p_d_given_pos,
          testResult: 'positive'
        };
      }
    })
    .catch(error => {
      showResult('Fetch error: ' + error);
    });
}

function calculateDisease() {
  const pDInput = document.getElementById('pD');
  const sensInput = document.getElementById('sensitivity');
  const fpInput = document.getElementById('falsePositive');
  const testResultInput = document.getElementById('testResult');

  const validP = validateInput(pDInput);
  const validSens = validateInput(sensInput);
  const validFP = validateInput(fpInput);

  if (!(validP && validSens && validFP)) return;

  const prior = parseFloat(pDInput.value);

  fetch('/disease', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      pD: prior,
      sensitivity: parseFloat(sensInput.value),
      falsePositive: parseFloat(fpInput.value),
      testResult: testResultInput.value
    })
  })
    .then(response => response.json())
    .then(data => {
      if (data.error) {
        showResult('Error: ' + data.error);
      } else {
        showResult(`Probability of disease given ${data.test_result} test: ${data.p_d_given_result}`);
        renderProbabilityChart(prior, data.p_d_given_result);

        lastCalculationData = {
          diseaseName: 'Custom Disease',
          priorProbability: parseFloat(document.getElementById('pD').value),
          posteriorProbability: data.p_d_given_result,
          testResult: testResultInput.value
        };

        showDownloadSection();
        showRecommendationsContainer();
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
        y: { beginAtZero: true, max: 100 }
      }
    }
  });
}

// ============================================
// AI Recommendations Functionality
// ============================================

function showRecommendationsContainer() {
  const container = document.getElementById('recommendationsContainer');
  const contentDiv = document.getElementById('recommendationsContent');
  const loadingDiv = document.getElementById('recommendationsLoading');
  const disclaimerDiv = document.getElementById('recommendationsDisclaimer');
  const btn = document.getElementById('getRecommendationsBtn');

  if (container) {
    container.style.display = 'block';
    contentDiv.style.display = 'none';
    loadingDiv.style.display = 'none';
    disclaimerDiv.style.display = 'none';
    btn.style.display = 'inline-block';

    setTimeout(() => {
      container.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 300);
  }
}

function getAIRecommendations() {
  const contentDiv = document.getElementById('recommendationsContent');
  const loadingDiv = document.getElementById('recommendationsLoading');
  const disclaimerDiv = document.getElementById('recommendationsDisclaimer');
  const btn = document.getElementById('getRecommendationsBtn');
  const languageSelect = document.getElementById('languageSelect');

  btn.style.display = 'none';
  loadingDiv.style.display = 'block';
  contentDiv.style.display = 'none';
  disclaimerDiv.style.display = 'none';

  const requestData = {
    disease_name: lastCalculationData.diseaseName,
    prior_probability: lastCalculationData.priorProbability,
    posterior_probability: lastCalculationData.posteriorProbability,
    test_result: lastCalculationData.testResult,
    language: languageSelect.value
  };

  fetch('/gemini-recommendations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData)
  })
    .then(response => response.json())
    .then(data => {
      loadingDiv.style.display = 'none';

      if (data.success) {
        contentDiv.innerHTML = formatMarkdownToHTML(data.recommendations);
        contentDiv.style.display = 'block';
        disclaimerDiv.style.display = 'block';
        contentGenerated = true;

        const language = languageSelect ? languageSelect.value : 'english';
        const existingAudio = document.getElementById('ttsAudioPlayer');
        if (existingAudio) existingAudio.remove();

        fetch('/text-to-speech', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ text: data.recommendations, language: language })
        })
          .then(function (res) { return res.blob(); })
          .then(function (blob) {
            const audioUrl = URL.createObjectURL(blob);
            const audioEl = document.createElement('audio');
            audioEl.id = 'ttsAudioPlayer';
            audioEl.controls = true;
            audioEl.src = audioUrl;
            audioEl.className = 'mt-3 w-100';
            audioEl.style.borderRadius = '8px';
            contentDiv.appendChild(audioEl);
          })
          .catch(function (err) {
            console.warn('TTS audio generation failed:', err);
          });

      } else {
        contentDiv.innerHTML = `
          <div class="alert alert-warning">
            <strong>Unable to generate recommendations:</strong><br>
            ${data.recommendations || data.error || 'Unknown error occurred'}
            <br><br>
            <small>Make sure the GEMINI_API_KEY environment variable is set correctly.</small>
          </div>
        `;
        contentDiv.style.display = 'block';
        btn.style.display = 'inline-block';
      }

      contentDiv.scrollIntoView({ behavior: "smooth", block: "nearest" });
    })
    .catch(error => {
      loadingDiv.style.display = 'none';
      contentDiv.innerHTML = `
        <div class="alert alert-danger">
          <strong>Error:</strong> Failed to fetch recommendations. ${error.message}
        </div>
      `;
      contentDiv.style.display = 'block';
      btn.style.display = 'inline-block';
    });
}

async function changeRecommendationLanguage() {
  if (!contentGenerated) return;
  await showRecommendationsContainer();
  await getAIRecommendations();
}

function formatMarkdownToHTML(text) {
  if (!text) return '';

  let html = text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');

  html = '<p>' + html + '</p>';
  html = html.replace(/<p><\/p>/g, '');
  html = html.replace(/<p>\s*<\/p>/g, '');

  return html;
}

window.addEventListener("DOMContentLoaded", attachResetOnInput);

function initDiseaseSelect() {
  if (typeof window.$ === 'undefined' || !$.fn.select2) {
    console.warn("jQuery or Select2 not loaded");
    return;
  }

  const $el = $('#diseaseSelect');
  if (!$el.length) return;

  $el.select2({
    width: '100%',
    allowClear: true,
    placeholder: $el.data('placeholder'),
    dropdownParent: $el.parent()
  }).on('select2:open', function () {
    setTimeout(() => {
      const searchField = $('.select2-container--open .select2-search__field');
      searchField.attr('placeholder', 'Type here to search...');
      searchField.focus();
    }, 50);
  });
}

document.addEventListener('DOMContentLoaded', initDiseaseSelect);

// ============================================
// Interactive Real-Time Slider Functionality
// ============================================

let interactiveCalculationTimeout = null;

function showUpdatingState() {
  const indicator = document.getElementById('updatingIndicator');
  const resultContainer = document.getElementById('interactiveResult');
  if (indicator) indicator.style.display = 'inline-block';
  if (resultContainer) resultContainer.classList.add('updating');
}

function hideUpdatingState() {
  const resultContainer = document.getElementById('interactiveResult');
  if (resultContainer) resultContainer.classList.remove('updating');
}

function resetResultDisplay() {
  const interactiveResult = document.getElementById('interactiveResult');
  const chartContainer = document.getElementById('chartContainer');
  const sensitivityContainer = document.getElementById('sensitivityContainer');
  const recommendationsContainer = document.getElementById('recommendationsContainer');
  const resultAlert = document.getElementById('result');

  const containers = [interactiveResult, chartContainer, sensitivityContainer, recommendationsContainer, resultAlert];

  containers.forEach(container => {
    if (container) {
      container.classList.remove('visible');
      container.classList.add('hidden');
      if (container.id === 'result' || container.id === 'recommendationsContainer') {
        container.style.display = 'none';
      }
    }
  });
}

function initInteractiveSliders() {
  const pDSlider = document.getElementById('pDSlider');
  const pDInput = document.getElementById('pD');
  const sensitivitySlider = document.getElementById('sensitivitySlider');
  const sensitivityInput = document.getElementById('sensitivity');
  const falsePositiveSlider = document.getElementById('falsePositiveSlider');
  const falsePositiveInput = document.getElementById('falsePositive');
  const testResultSelect = document.getElementById('testResult');

  if (!pDSlider || !sensitivitySlider || !falsePositiveSlider) {
    return;
  }

  if (pDSlider && pDInput) {
    pDSlider.addEventListener('input', function () {
      pDInput.value = this.value;
      updateSliderValue('pDValue', this.value);
      resetResultDisplay();
    });

    pDInput.addEventListener('input', function () {
      const raw = this.value;
      if (raw === '' || raw === '.' || raw === '0.') return;
      const value = Number(raw);
      if (isNaN(value)) return;
      if (value >= 0 && value <= 1) {
        pDSlider.value = value;
        updateSliderValue('pDValue', value);
      }
    });
  }

  if (sensitivitySlider && sensitivityInput) {
    sensitivitySlider.addEventListener('input', function () {
      sensitivityInput.value = this.value;
      updateSliderValue('sensitivityValue', this.value);
      resetResultDisplay();
    });

    sensitivityInput.addEventListener('input', function () {
      const raw = this.value;
      if (raw === '' || raw === '.' || raw === '0.') return;
      const value = Number(raw);
      if (isNaN(value)) return;
      if (value >= 0 && value <= 1) {
        sensitivitySlider.value = value;
        updateSliderValue('sensitivityValue', value);
      }
    });
  }

  if (falsePositiveSlider && falsePositiveInput) {
    falsePositiveSlider.addEventListener('input', function () {
      falsePositiveInput.value = this.value;
      updateSliderValue('falsePositiveValue', this.value);
      resetResultDisplay();
    });

    falsePositiveInput.addEventListener('input', function () {
      const raw = this.value;
      if (raw === '' || raw === '.' || raw === '0.') return;
      const value = Number(raw);
      if (isNaN(value)) return;
      if (value >= 0 && value <= 1) {
        falsePositiveSlider.value = value;
        updateSliderValue('falsePositiveValue', value);
      }
    });
  }

  if (testResultSelect) {
    testResultSelect.addEventListener('change', function () {
      resetResultDisplay();
    });
  }

  const diseaseSelect = document.getElementById('diseaseSelect');
  if (diseaseSelect) {
    diseaseSelect.addEventListener('change', resetResultDisplay);
  }

  const savedState = localStorage.getItem(STORAGE_KEY);

  if (savedState) {
    try {
      const state = JSON.parse(savedState);

      pDSlider.value = state.pD;
      pDInput.value = state.pD;
      updateSliderValue("pDValue", state.pD);

      sensitivitySlider.value = state.sensitivity;
      sensitivityInput.value = state.sensitivity;
      updateSliderValue("sensitivityValue", state.sensitivity);

      falsePositiveSlider.value = state.falsePositive;
      falsePositiveInput.value = state.falsePositive;
      updateSliderValue("falsePositiveValue", state.falsePositive);

      testResultSelect.value = state.testResult;

      updateInteractiveResult(state.pD, state.posterior, state.testResult);
      renderProbabilityChart(state.pD, state.posterior);
      renderSensitivityChart(state.pD, state.sensitivity, state.falsePositive, state.testResult);

    } catch (err) {
      console.warn("Failed to restore calculator state", err);
    }
  } else {
    resetResultDisplay();
  }
}

function handleCheck() {
  const btn = document.getElementById('checkButton');
  const btnText = document.getElementById('buttonText');
  const resultContainer = document.getElementById('interactiveResult');

  if (!btn || !btnText) return;

  btn.classList.add('btn-loading');
  btn.disabled = true;
  btnText.textContent = 'Calculating...';

  resultContainer.classList.remove('visible');
  resultContainer.classList.add('hidden');

  setTimeout(() => {
    calculateInteractive();

    btn.classList.remove('btn-loading');
    btn.disabled = false;
    btnText.innerHTML = '<i class="fas fa-check-circle me-2"></i>Check Result';

    resultContainer.classList.remove('hidden');
    resultContainer.classList.add('visible');
  }, 600);
}

function updateSliderValue(elementId, value) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = parseFloat(value).toFixed(2);
  }
}

function calculateInteractive() {
  showUpdatingState();

  if (interactiveCalculationTimeout) {
    clearTimeout(interactiveCalculationTimeout);
  }

  interactiveCalculationTimeout = setTimeout(() => {
    const pDSlider = document.getElementById('pDSlider');
    const sensitivitySlider = document.getElementById('sensitivitySlider');
    const falsePositiveSlider = document.getElementById('falsePositiveSlider');
    const testResultSelect = document.getElementById('testResult');

    if (!pDSlider || !sensitivitySlider || !falsePositiveSlider) {
      hideUpdatingState();
      return;
    }

    const prior = parseFloat(pDSlider.value || 0);
    const sensitivity = parseFloat(sensitivitySlider.value || 0);
    const falsePositive = parseFloat(falsePositiveSlider.value || 0);
    const testResult = testResultSelect ? testResultSelect.value : 'positive';

    if (
      isNaN(prior) || prior < 0 || prior > 1 ||
      isNaN(sensitivity) || sensitivity < 0 || sensitivity > 1 ||
      isNaN(falsePositive) || falsePositive < 0 || falsePositive > 1
    ) {
      hideUpdatingState();
      return;
    }

    const specificity = 1 - falsePositive;
    let numerator, denominator;

    if (testResult === 'positive') {
      numerator = sensitivity * prior;
      denominator = numerator + (falsePositive * (1 - prior));
    } else {
      numerator = (1 - sensitivity) * prior;
      denominator = numerator + (specificity * (1 - prior));
    }

    if (denominator === 0) {
      hideUpdatingState();
      return;
    }

    const posterior = numerator / denominator;

    updateInteractiveResult(prior, posterior, testResult);
    renderProbabilityChart(prior, posterior);

    // Render sensitivity analysis curve
    renderSensitivityChart(prior, sensitivity, falsePositive, testResult);

    hideUpdatingState();

    document.querySelectorAll("#pD, #sensitivity, #falsePositive").forEach(input => {
      input.addEventListener("blur", () => {
        const value = parseFloat(input.value);
        if (isNaN(value)) {
          input.value = "";
          return;
        }
        if (value < 0) input.value = 0;
        if (value > 1) input.value = 1;
      });
    });

  }, 250);
}

function updateInteractiveResult(prior, posterior, testResult = 'positive') {
  const resultContainer = document.getElementById('interactiveResult');
  const priorValueDisplay = document.getElementById('priorValueDisplay');
  const posteriorValue = document.getElementById('posteriorValue');
  const posteriorProgressBar = document.getElementById('posteriorProgressBar');
  const posteriorPercentage = document.getElementById('posteriorPercentage');
  const riskLevelBadge = document.getElementById('riskLevelBadge');
  const riskLevelText = document.getElementById('riskLevelText');

  if (!resultContainer) return;

  resultContainer.classList.remove('hidden');
  resultContainer.classList.add('visible');

  const priorPercent = prior * 100;
  if (priorValueDisplay) {
    priorValueDisplay.textContent = prior.toFixed(4) + ' (' + priorPercent.toFixed(2) + '%)';
  }

  const posteriorPercent = posterior * 100;
  if (posteriorValue) {
    posteriorValue.textContent = posterior.toFixed(4) + ' (' + posteriorPercent.toFixed(2) + '%)';
  }

  if (posteriorProgressBar && posteriorPercentage) {
    posteriorProgressBar.style.width = posteriorPercent + '%';
    posteriorProgressBar.setAttribute('aria-valuenow', posteriorPercent);
    posteriorPercentage.textContent = posteriorPercent.toFixed(1) + '%';

    posteriorProgressBar.className = 'progress-bar progress-bar-striped progress-bar-animated';
    if (posteriorPercent < 25) {
      posteriorProgressBar.classList.add('bg-success');
      if (riskLevelBadge && riskLevelText) {
        riskLevelBadge.className = 'badge fs-6 p-2 risk-low';
        riskLevelText.textContent = 'Low Risk';
      }
    } else if (posteriorPercent < 50) {
      posteriorProgressBar.classList.add('bg-warning');
      if (riskLevelBadge && riskLevelText) {
        riskLevelBadge.className = 'badge fs-6 p-2 risk-medium';
        riskLevelText.textContent = 'Medium Risk';
      }
    } else if (posteriorPercent < 75) {
      posteriorProgressBar.classList.add('bg-danger');
      if (riskLevelBadge && riskLevelText) {
        riskLevelBadge.className = 'badge fs-6 p-2 risk-high';
        riskLevelText.textContent = 'High Risk';
      }
    } else {
      posteriorProgressBar.classList.add('bg-dark');
      if (riskLevelBadge && riskLevelText) {
        riskLevelBadge.className = 'badge fs-6 p-2 risk-very-high';
        riskLevelText.textContent = 'Very High Risk';
      }
    }
  }

  lastCalculationData = {
    diseaseName: null,
    priorProbability: prior,
    posteriorProbability: posterior,
    testResult: testResult
  };

  showRecommendationsContainer();

  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    pD: prior,
    sensitivity: Number(document.getElementById("sensitivity")?.value),
    falsePositive: Number(document.getElementById("falsePositive")?.value),
    testResult: testResult,
    posterior: posterior
  }));
}

function resetCalculator() {
  localStorage.removeItem(STORAGE_KEY);

  const DEFAULTS = {
    pD: 0.01,
    sensitivity: 0.99,
    falsePositive: 0.05,
    testResult: "positive"
  };

  const pDSlider = document.getElementById('pDSlider');
  const pDInput = document.getElementById('pD');
  const sensitivitySlider = document.getElementById('sensitivitySlider');
  const sensitivityInput = document.getElementById('sensitivity');
  const falsePositiveSlider = document.getElementById('falsePositiveSlider');
  const falsePositiveInput = document.getElementById('falsePositive');
  const testResultSelect = document.getElementById('testResult');

  if (pDSlider && pDInput) {
    pDSlider.value = DEFAULTS.pD;
    pDInput.value = DEFAULTS.pD;
    updateSliderValue('pDValue', DEFAULTS.pD);
  }

  if (sensitivitySlider && sensitivityInput) {
    sensitivitySlider.value = DEFAULTS.sensitivity;
    sensitivityInput.value = DEFAULTS.sensitivity;
    updateSliderValue('sensitivityValue', DEFAULTS.sensitivity);
  }

  if (falsePositiveSlider && falsePositiveInput) {
    falsePositiveSlider.value = DEFAULTS.falsePositive;
    falsePositiveInput.value = DEFAULTS.falsePositive;
    updateSliderValue('falsePositiveValue', DEFAULTS.falsePositive);
  }

  if (testResultSelect) {
    testResultSelect.value = DEFAULTS.testResult;
  }

  resetResultDisplay();

  if (probabilityChart) {
    probabilityChart.destroy();
    probabilityChart = null;
  }

  // Destroy sensitivity chart
  if (sensitivityChart) {
    sensitivityChart.destroy();
    sensitivityChart = null;
  }

  lastCalculationData = {
    diseaseName: null,
    priorProbability: null,
    posteriorProbability: null,
    testResult: 'positive'
  };
}

function showDownloadSection() {
  const downloadSection = document.getElementById('downloadSection');
  if (downloadSection) {
    downloadSection.style.display = 'block';
    downloadSection.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

async function downloadResults(format) {
  if (!lastCalculationData.posteriorProbability) {
    alert('Please calculate results first before downloading.');
    return;
  }

  try {
    const response = await fetch('/download-results', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        format: format,
        prior_probability: lastCalculationData.priorProbability,
        posterior_probability: lastCalculationData.posteriorProbability,
        disease_name: lastCalculationData.diseaseName,
        test_result: lastCalculationData.testResult,
        sensitivity: document.getElementById('sensitivity').value,
        false_positive: document.getElementById('falsePositive').value
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || 'Download failed');
    }

    let filename = `disease_results_${new Date().getTime()}.${format}`;
    const contentDisposition = response.headers.get('content-disposition');
    if (contentDisposition && contentDisposition.includes('filename')) {
      const matches = contentDisposition.match(/filename="?([^"\n]+)"?/);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

  } catch (error) {
    console.error('Download error:', error);
    alert('Error downloading results: ' + error.message);
  }
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initInteractiveSliders);
} else {
  initInteractiveSliders();
}