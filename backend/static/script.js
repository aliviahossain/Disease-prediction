let probabilityChart = null;

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
// Dark Mode Toggle Functionality
// ============================================

function initDarkMode() {
  const darkModeToggle = document.getElementById('darkModeToggle');
  const body = document.body;
  const sunIcon = document.querySelector('.sun-icon');
  const moonIcon = document.querySelector('.moon-icon');

  // Check for saved dark mode preference or default to light mode
  const isDarkMode = localStorage.getItem('darkMode') === 'enabled';

  // Apply dark mode if previously enabled
  if (isDarkMode) {
    body.classList.add('dark-mode');
    if (sunIcon) sunIcon.style.display = 'block';
    if (moonIcon) moonIcon.style.display = 'none';
  }

  // Toggle dark mode on button click
  if (darkModeToggle) {
    darkModeToggle.addEventListener('click', () => {
      body.classList.toggle('dark-mode');

      const isDark = body.classList.contains('dark-mode');

      // Update icons
      if (sunIcon && moonIcon) {
        sunIcon.style.display = isDark ? 'block' : 'none';
        moonIcon.style.display = isDark ? 'none' : 'block';
      }

      // Save preference to localStorage
      localStorage.setItem('darkMode', isDark ? 'enabled' : 'disabled');
    });
  }
}


// Initialize dark mode on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initDarkMode);
} else {
  initDarkMode();
}

// ============================================
// Dashboard Menu Functionality
// ============================================
function initDashboardMenu() {
  const menuToggle = document.getElementById('dashboardMenuToggle');
  const dropdown = document.getElementById('dashboardDropdown');

  if (menuToggle && dropdown) {
    // Toggle menu on click
    menuToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      dropdown.classList.toggle('show');
      const isExpanded = dropdown.classList.contains('show');
      menuToggle.setAttribute('aria-expanded', isExpanded);
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
      if (!menuToggle.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.classList.remove('show');
        menuToggle.setAttribute('aria-expanded', 'false');
      }
    });

    // Close menu on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && dropdown.classList.contains('show')) {
        dropdown.classList.remove('show');
        menuToggle.setAttribute('aria-expanded', 'false');
        menuToggle.focus();
      }
    });
  }
}

// Initialize dashboard menu
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

// Hide result box whenever user edits input
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

// Smoothly show result and scroll down
function showResult(message) {
  const resultDiv = document.getElementById('result');
  resultDiv.textContent = message;
  resultDiv.classList.add('visible');

  // Smooth scroll into view
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

  // Use visibility classes for smooth transition
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

        // Update the sliders and inputs with preset values
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

        // --- EXPLICIT INTERACTION CHANGE ---
        // We no longer call calculateInteractive() or showResult/renderProbabilityChart here.
        // Instead, we just reset the display to clear potentially stale results.
        resetResultDisplay();

        // Optional: Provide subtle visual cue to click Check
        const checkBtn = document.getElementById('checkButton');
        if (checkBtn) {
          checkBtn.classList.add('pulse-highlight');
          setTimeout(() => checkBtn.classList.remove('pulse-highlight'), 1500);
        }

        // Store data for AI recommendations (will be used after manual Check)
        lastCalculationData = {
          diseaseName: selectedDisease,
          priorProbability: data.prior,
          posteriorProbability: data.p_d_given_pos,
          testResult: 'positive'
        };

        // Recommendations will now appear ONLY after Check is clicked
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
        console.log("-----------------------------------------------------------------------");
        console.log(`Probability of disease given ${data.test_result} test: ${data.p_d_given_result}`);
        console.log("-----------------------------------------------------------------------");
        showResult(`Probability of disease given ${data.test_result} test: ${data.p_d_given_result}`);
        renderProbabilityChart(prior, data.p_d_given_result);

        // Store data for AI recommendations
        lastCalculationData = {
          diseaseName: null, // No disease name for custom input
          priorProbability: prior,
          posteriorProbability: data.p_d_given_result,
          testResult: data.test_result
        };

        // Store data for download
        lastCalculationData = {
          diseaseName: diseaseSelect.value || 'Custom Disease',
          priorProbability: parseFloat(document.getElementById('pD').value),
          posteriorProbability: data.p_d_given_result,
          testResult: testResult
        };

        // Show download section
        showDownloadSection();

        // Show recommendations container with button
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

    // Smooth scroll to recommendations container
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

  // Show loading state
  btn.style.display = 'none';
  loadingDiv.style.display = 'block';
  contentDiv.style.display = 'none';
  disclaimerDiv.style.display = 'none';

  // Prepare request data
  const requestData = {
    disease_name: lastCalculationData.diseaseName,
    prior_probability: lastCalculationData.priorProbability,
    posterior_probability: lastCalculationData.posteriorProbability,
    test_result: lastCalculationData.testResult,
    language: languageSelect.value
  };

  // Call Gemini API
  fetch('/gemini-recommendations', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(requestData)
  })
    .then(response => response.json())
    .then(data => {
      loadingDiv.style.display = 'none';

      if (data.success) {
        // Format and display recommendations using marked.js or simple HTML conversion
        contentDiv.innerHTML = formatMarkdownToHTML(data.recommendations);
        contentDiv.style.display = 'block';
        disclaimerDiv.style.display = 'block';
        contentGenerated = true; // Mark content as generated
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

      // Scroll to see the content
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

// Handle language change for recommendations
async function changeRecommendationLanguage() {
  if (!contentGenerated) return;

  // showing the recommendations container again
  await showRecommendationsContainer();
  // Call the recommendations function again after changing language
  await getAIRecommendations();
}

// Simple markdown-to-HTML converter for AI responses
function formatMarkdownToHTML(text) {
  if (!text) return '';

  // Convert markdown-style formatting to HTML
  let html = text
    // Bold text: **text** or __text__
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    // Italic text: *text* or _text_
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>')
    // Line breaks
    .replace(/\n\n/g, '</p><p>')
    .replace(/\n/g, '<br>');

  // Wrap in paragraph tags
  html = '<p>' + html + '</p>';

  // Clean up empty paragraphs
  html = html.replace(/<p><\/p>/g, '');
  html = html.replace(/<p>\s*<\/p>/g, '');

  return html;
}

// Attach reset logic after page loads
window.addEventListener("DOMContentLoaded", attachResetOnInput);

// $('#diseaseSelect').select2({
//   placeholder: "Type to search disease...",
//   width: '100%',
//   allowClear: true,
//   dropdownParent: $('#diseaseSelect').parent(),
// }).on('select2:open', function () {
//   // Use a timeout to ensure the search field is fully rendered
//   setTimeout(function () {
//     // Find the search field inside the currently open dropdown
//     const searchField = $('.select2-container--open .select2-search__field');

//     // Set the placeholder text for the search box
//     searchField.attr('placeholder', 'Type here to search...');

//     // Set focus to place the cursor in the search box
//     searchField.focus();

//   }, 50); // A 50ms delay for reliability
// });

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

// Reset interactivity: Hide results when inputs change
function resetResultDisplay() {
  const interactiveResult = document.getElementById('interactiveResult');
  const chartContainer = document.getElementById('chartContainer');
  const recommendationsContainer = document.getElementById('recommendationsContainer');
  const resultAlert = document.getElementById('result');

  const containers = [interactiveResult, chartContainer, recommendationsContainer, resultAlert];

  containers.forEach(container => {
    if (container) {
      container.classList.remove('visible');
      container.classList.add('hidden');
      // For legacy alerts using style.display
      if (container.id === 'result' || container.id === 'recommendationsContainer') {
        container.style.display = 'none';
      }
    }
  });
}

// Initialize interactive sliders
function initInteractiveSliders() {
  // Get all slider and input elements (using the existing form IDs)
  const pDSlider = document.getElementById('pDSlider');
  const pDInput = document.getElementById('pD');
  const sensitivitySlider = document.getElementById('sensitivitySlider');
  const sensitivityInput = document.getElementById('sensitivity');
  const falsePositiveSlider = document.getElementById('falsePositiveSlider');
  const falsePositiveInput = document.getElementById('falsePositive');
  const testResultSelect = document.getElementById('testResult');

  // Check if elements exist (only run on calculator page)
  if (!pDSlider || !sensitivitySlider || !falsePositiveSlider) {
    return;
  }

  // Sync sliders with number inputs for Prior Probability
  if (pDSlider && pDInput) {
    pDSlider.addEventListener('input', function () {
      pDInput.value = this.value;
      updateSliderValue('pDValue', this.value);
      resetResultDisplay();
    });

    // Allow partial typing states
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

  // Sync sliders with number inputs for Sensitivity
  if (sensitivitySlider && sensitivityInput) {
    sensitivitySlider.addEventListener('input', function () {
      sensitivityInput.value = this.value;
      updateSliderValue('sensitivityValue', this.value);
      resetResultDisplay();
    });

    // Allow partial typing states
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

  // Sync sliders with number inputs for False Positive Rate
  if (falsePositiveSlider && falsePositiveInput) {
    falsePositiveSlider.addEventListener('input', function () {
      falsePositiveInput.value = this.value;
      updateSliderValue('falsePositiveValue', this.value);
      resetResultDisplay();
    });

    // Allow partial typing states
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

  // Handle test result select changes
  if (testResultSelect) {
    testResultSelect.addEventListener('change', function () {
      resetResultDisplay();
    });
  }

  const diseaseSelect = document.getElementById('diseaseSelect');
  if (diseaseSelect) {
    diseaseSelect.addEventListener('change', resetResultDisplay);
  }

  // Restore previous calculator state if available
  const savedState = localStorage.getItem(STORAGE_KEY);

  if (savedState) {
    try {
      const state = JSON.parse(savedState);

      // Restore Prior Probability
      pDSlider.value = state.pD;
      pDInput.value = state.pD;
      updateSliderValue("pDValue", state.pD);

      // Restore Sensitivity
      sensitivitySlider.value = state.sensitivity;
      sensitivityInput.value = state.sensitivity;
      updateSliderValue("sensitivityValue", state.sensitivity);

      // Restore False Positive Rate
      falsePositiveSlider.value = state.falsePositive;
      falsePositiveInput.value = state.falsePositive;
      updateSliderValue("falsePositiveValue", state.falsePositive);

      // Restore Test Result
      testResultSelect.value = state.testResult;

      // Restore Result + Chart
      updateInteractiveResult(state.pD, state.posterior, state.testResult);
      renderProbabilityChart(state.pD, state.posterior);

    } catch (err) {
      console.warn("Failed to restore calculator state", err);
    }
  } else {
    // No saved state → start clean
    resetResultDisplay();
  }
}
/**
 * Handle "Check" button click
 * Implements loading state and triggers calculation
 */
function handleCheck() {
  const btn = document.getElementById('checkButton');
  const btnText = document.getElementById('buttonText');
  const resultContainer = document.getElementById('interactiveResult');

  if (!btn || !btnText) return;

  // 1. Enter Loading State
  btn.classList.add('btn-loading');
  btn.disabled = true;
  btnText.textContent = 'Calculating...';

  // Optional: Hide old results during calculation for cleaner feel
  resultContainer.classList.remove('visible');
  resultContainer.classList.add('hidden');

  // 2. Simulate small delay for "Professional" feel and ensure calculation finishes
  setTimeout(() => {
    calculateInteractive();

    // 3. Exit Loading State & Show results
    btn.classList.remove('btn-loading');
    btn.disabled = false;
    btnText.innerHTML = '<i class="fas fa-check-circle me-2"></i>Check Result';

    resultContainer.classList.remove('hidden');
    resultContainer.classList.add('visible');
  }, 600);
}

// Update slider value display
function updateSliderValue(elementId, value) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = parseFloat(value).toFixed(2);
  }
}

// Calculate posterior probability in real-time
function calculateInteractive() {
  // 1. Show feedback immediately
  showUpdatingState();

  // 2. Clear existing timeout (debounce)
  if (interactiveCalculationTimeout) {
    clearTimeout(interactiveCalculationTimeout);
  }

  // 3. Set new timeout
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

    // Validate numeric and range [0,1]
    if (
      isNaN(prior) || prior < 0 || prior > 1 ||
      isNaN(sensitivity) || sensitivity < 0 || sensitivity > 1 ||
      isNaN(falsePositive) || falsePositive < 0 || falsePositive > 1
    ) {
      hideUpdatingState();
      return;
    }


    // Calculate posterior probability using Bayes' Theorem
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

    // Update UI and store data for recommendations
    updateInteractiveResult(prior, posterior, testResult);

    // Render chart as well
    renderProbabilityChart(prior, posterior);

    // 4. Hide feedback
    hideUpdatingState();

  }, 250); // 250ms debounce

  // Enforce probability bounds on input blur
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
}

// Update the interactive result display
function updateInteractiveResult(prior, posterior, testResult = 'positive') {
  const resultContainer = document.getElementById('interactiveResult');
  const priorValueDisplay = document.getElementById('priorValueDisplay');
  const posteriorValue = document.getElementById('posteriorValue');
  const posteriorProgressBar = document.getElementById('posteriorProgressBar');
  const posteriorPercentage = document.getElementById('posteriorPercentage');
  const riskLevelBadge = document.getElementById('riskLevelBadge');
  const riskLevelText = document.getElementById('riskLevelText');

  if (!resultContainer) return;

  // Show result container via classes
  resultContainer.classList.remove('hidden');
  resultContainer.classList.add('visible');

  // Update prior value display
  const priorPercent = prior * 100;
  if (priorValueDisplay) {
    priorValueDisplay.textContent = prior.toFixed(4) + ' (' + priorPercent.toFixed(2) + '%)';
  }

  // Update posterior value
  const posteriorPercent = posterior * 100;
  if (posteriorValue) {
    posteriorValue.textContent = posterior.toFixed(4) + ' (' + posteriorPercent.toFixed(2) + '%)';
  }

  // Update progress bar
  if (posteriorProgressBar && posteriorPercentage) {
    posteriorProgressBar.style.width = posteriorPercent + '%';
    posteriorProgressBar.setAttribute('aria-valuenow', posteriorPercent);
    posteriorPercentage.textContent = posteriorPercent.toFixed(1) + '%';

    // Update progress bar color based on risk level
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

  // Store data for AI recommendations
  lastCalculationData = {
    diseaseName: null,
    priorProbability: prior,
    posteriorProbability: posterior,
    testResult: testResult
  };

  // Show recommendations container
  showRecommendationsContainer();
  // Persist calculator state after successful calculation
  localStorage.setItem(STORAGE_KEY, JSON.stringify({
    pD: prior,
    sensitivity: Number(document.getElementById("sensitivity")?.value),
    falsePositive: Number(document.getElementById("falsePositive")?.value),
    testResult: testResult,
    posterior: posterior
  }));
}

// Fully reset calculator state (UI + storage)
function resetCalculator() {
  // Clear localStorage
  localStorage.removeItem(STORAGE_KEY);

  // Default values (as per UI design)
  const DEFAULTS = {
    pD: 0.01,
    sensitivity: 0.99,
    falsePositive: 0.05,
    testResult: "positive"
  };

  // Reset inputs
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

  // Reset result UI
  resetResultDisplay();

  // Destroy chart if exists
  if (probabilityChart) {
    probabilityChart.destroy();
    probabilityChart = null;
  }

  // Clear last calculation data
  lastCalculationData = {
    diseaseName: null,
    priorProbability: null,
    posteriorProbability: null,
    testResult: 'positive'
  };
}


// Show download section after calculation
function showDownloadSection() {
  const downloadSection = document.getElementById('downloadSection');
  if (downloadSection) {
    downloadSection.style.display = 'block';
    downloadSection.scrollIntoView({ behavior: "smooth", block: "center" });
  }
}

// Download results
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

    // Get filename from response headers or generate default
    let filename = `disease_results_${new Date().getTime()}.${format}`;
    const contentDisposition = response.headers.get('content-disposition');
    if (contentDisposition && contentDisposition.includes('filename')) {
      const matches = contentDisposition.match(/filename="?([^"\n]+)"?/);
      if (matches && matches[1]) {
        filename = matches[1];
      }
    }

    // Create blob and download
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    console.log(`Downloaded: ${filename}`);

  } catch (error) {
    console.error('Download error:', error);
    alert('Error downloading results: ' + error.message);
  }
}

// Initialize on page load
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initInteractiveSliders);
} else {
  initInteractiveSliders();
}