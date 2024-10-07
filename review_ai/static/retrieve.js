const tokenInput = document.getElementById('tokenInput');
const retrieveButton = document.getElementById('retrieveButton');
const analysisContent = document.getElementById('analysisContent');

function retrieveAnalysis() {
    const token = tokenInput.value.trim();
    if (token) {
        analysisContent.innerHTML = createSkeletonLoader();

        fetch(`/api/analysis/${token}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.status === "in_progress") {
                    displayInProgressMessage();
                } else {
                    displayAnalysis(data);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                displayError(error);
            });
    }
}

function displayAnalysis(analysis) {
    // ... (same as in instant_analysis.js)
}

function createSkeletonLoader() {
    // ... (same as in instant_analysis.js)
}

function displayInProgressMessage() {
    analysisContent.innerHTML = `
        <div class="bg-stone-800 p-8 rounded-lg text-center">
            <svg class="mx-auto h-12 w-12 text-[#7fd36e] animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            <h3 class="mt-4 text-xl font-medium text-stone-300">Analysis in progress</h3>
            <p class="mt-2 text-sm text-stone-400">Your analysis is still being processed. Please check back later.</p>
        </div>
    `;
}

function displayError(error) {
    analysisContent.innerHTML = `
        <div class="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative" role="alert">
            <strong class="font-bold">Error:</strong>
            <span class="block sm:inline">${error.message}</span>
        </div>
    `;
}

// Event listener
retrieveButton.addEventListener('click', retrieveAnalysis);