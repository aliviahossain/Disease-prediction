let probabilityChart = null;

// Store last calculation data for AI recommendations
let lastCalculationData = {
  diseaseName: null,
  priorProbability: null,
  posteriorProbability: null,
  testResult: 'positive'
};

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
        if (sunIcon) sunIcon.style.display = 'none';
        if (moonIcon) moonIcon.style.display = 'block';
    }
    
    // Toggle dark mode on button click
    if (darkModeToggle) {
        darkModeToggle.addEventListener('click', () => {
            body.classList.toggle('dark-mode');
            
            const isDark = body.classList.contains('dark-mode');
            
            // Update icons
            if (sunIcon && moonIcon) {
                sunIcon.style.display = isDark ? 'none' : 'block';
                moonIcon.style.display = isDark ? 'block' : 'none';
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

      // Store data for AI recommendations
      lastCalculationData = {
        diseaseName: selectedDisease,
        priorProbability: data.prior,
        posteriorProbability: data.p_d_given_pos,
        testResult: 'positive'
      };
      
      // Show recommendations container with button
      showRecommendationsContainer();
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