let debounceTimer;
let userLocation = null;
let selectedDataId = null;

const searchInput = document.getElementById('searchInput');
const suggestionsList = document.getElementById('suggestionsList');
const generateButton = document.getElementById('generateButton');
const analysisContent = document.getElementById('analysisContent');


function getLocation() {
    return new Promise((resolve, reject) => {
        if ("geolocation" in navigator) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const lat = position.coords.latitude;
                    const lng = position.coords.longitude;
                    userLocation = { latitude: lat, longitude: lng };
                    console.log(`Latitude: ${lat}, Longitude: ${lng}`);
                    resolve(userLocation);
                },
                (error) => {
                    console.error("Error getting location:", error.message);
                    reject(error);
                },
                {
                    enableHighAccuracy: true,
                    timeout: 5000,
                    maximumAge: 0
                }
            );
        } else {
            console.error("Geolocation is not supported by this browser.");
            reject(new Error("Geolocation is not supported"));
        }
    });
}

function requestLocation() {
    getLocation()
        .then((location) => {
            console.log("Location obtained:", location);
            // You can update UI here to show that location is available
        })
        .catch((error) => {
            console.error("Error getting location:", error);
            // You can update UI here to show that location is not available
        });
}

function getSuggestions() {
    const query = searchInput.value;
    if (query.length > 2) {
        const payload = {
            value: query,
            latitude: userLocation ? userLocation.latitude : null,
            longitude: userLocation ? userLocation.longitude : null
        };

        fetch('/api/suggestions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            if (data.suggestions && data.suggestions.length > 0) {
                displaySuggestions(data.suggestions);
            } else {
                displayNoResults();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            displayNoResults();
        });
    } else {
        suggestionsList.innerHTML = '';
    }
}

function displayNoResults() {
    suggestionsList.innerHTML = `
        <li class="px-4 sm:px-6 py-2 sm:py-3 text-stone-400 text-center">
            No results found
        </li>
    `;
}

function displaySuggestions(suggestions) {
    console.log("Displaying suggestions:", suggestions);
    suggestionsList.innerHTML = '';
    suggestions.forEach(suggestion => {
        const li = document.createElement('li');
        li.className = 'px-4 sm:px-6 py-2 sm:py-3 hover:bg-stone-600 cursor-pointer text-left';
        
        // Create a div for the place name
        const nameDiv = document.createElement('div');
        nameDiv.textContent = suggestion.value;
        nameDiv.className = 'font-semibold text-base sm:text-lg';
        
        // Create a div for the address (subtext)
        const addressDiv = document.createElement('div');
        addressDiv.textContent = suggestion.subtext;
        addressDiv.className = 'text-sm text-stone-400';
        
        // Append name and address to the list item
        li.appendChild(nameDiv);
        li.appendChild(addressDiv);
        
        li.addEventListener('click', () => selectSuggestion(suggestion));
        suggestionsList.appendChild(li);
    });
}

function selectSuggestion(suggestion) {
    searchInput.value = suggestion.value + ' ' + suggestion.subtext;
    selectedDataId = suggestion.data_id;
    suggestionsList.innerHTML = '';
    generateButton.disabled = false;
}

function createSkeletonLoader() {
    return `
        <div class="bg-stone-900 p-4 animate-pulse">
            <header class="mb-8">
                <div class="h-8 bg-stone-700 rounded w-3/4 mb-2"></div>
                <div class="h-6 bg-stone-700 rounded w-1/2 mb-2"></div>
                <div class="h-6 bg-stone-700 rounded w-1/4"></div>
            </header>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <!-- Summary Section (2/3 width) -->
                <div class="lg:col-span-2">
                    <div class="bg-stone-800 p-4 rounded-lg h-64">
                        <div class="h-6 bg-stone-700 rounded w-1/4 mb-4"></div>
                        <div class="h-4 bg-stone-700 rounded w-full mb-2"></div>
                        <div class="h-4 bg-stone-700 rounded w-full mb-2"></div>
                        <div class="h-4 bg-stone-700 rounded w-3/4"></div>
                    </div>
                </div>

                <!-- Reviews Section (1/3 width) -->
                <div class="lg:col-span-1">
                    <div class="bg-stone-800 p-4 rounded-lg">
                        <div class="h-6 bg-stone-700 rounded w-1/4 mb-4"></div>
                        ${Array(3).fill().map(() => `
                            <div class="mb-4">
                                <div class="h-4 bg-stone-700 rounded w-3/4 mb-2"></div>
                                <div class="h-4 bg-stone-700 rounded w-full mb-2"></div>
                                <div class="h-4 bg-stone-700 rounded w-1/2"></div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
}

function getAnalysis() {
    if (selectedDataId) {
        const analysisContent = document.getElementById('analysisContent');
        analysisContent.innerHTML = createSkeletonLoader();
        
        // Add the new loader overlay
        analysisContent.insertAdjacentHTML('afterbegin', `
            <div id="loaderOverlay" class="fixed inset-0 bg-stone-900 bg-opacity-75 z-50 flex items-center justify-center">
                <div class="loader-card">
                    <div class="loader">
                        <p>Analyzing</p>
                        <div class="words">
                            <span class="word">reviews</span>
                            <span class="word">sentiment</span>
                            <span class="word">food quality</span>
                            <span class="word">service</span>
                            <span class="word">ambiance</span>
                        </div>
                    </div>
                </div>
            </div>
        `);
        
        fetch(`/api/analysis/${selectedDataId}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                displayAnalysis(data);
            })
            .catch(error => {
                console.error('Error:', error);
                displayNoReviews();
            });
    }
}

function displayNoReviews() {
    const loaderOverlay = document.getElementById('loaderOverlay');
    if (loaderOverlay) {
        loaderOverlay.remove();
    }

    const analysisContent = document.getElementById('analysisContent');
    analysisContent.innerHTML = `
        <div class="bg-stone-800 p-8 rounded-lg text-center">
            <svg class="mx-auto h-12 w-12 text-stone-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <h3 class="mt-2 text-sm font-medium text-stone-400">No reviews found</h3>
            <p class="mt-1 text-sm text-stone-500">We couldn't find any reviews for this restaurant.</p>
            <div class="mt-6">
                <button type="button" onclick="resetSearch()" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-stone-900 bg-[#7fd36e] hover:bg-[#6ac259] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#7fd36e]">
                    Try another search
                </button>
            </div>
        </div>
    `;
}

function resetSearch() {
    searchInput.value = '';
    selectedDataId = null;
    suggestionsList.innerHTML = '';
    document.getElementById('analysisContent').innerHTML = '';
    searchInput.focus();
}

function displayAnalysis(analysis) {
    const starRating = '★'.repeat(Math.floor(analysis.rating)) + 
                       (analysis.rating % 1 >= 0.5 ? '½' : '') + 
                       '☆'.repeat(5 - Math.ceil(analysis.rating));

    let analysisHTML = `
        <div class="bg-stone-900 p-4">
            <header class="mb-8">
                <h1 class="text-4xl font-bold mb-2">${analysis.title}</h1>
                <p class="text-xl text-stone-400">${analysis.address}</p>
                <div class="text-2xl text-yellow-400 mt-2">${starRating} (${analysis.rating})</div>
                <span class="text-stone-500 sm:text-md md:text-lg lg:text-xl mt-2">Total reviews: ${analysis.total_reviews}</span>
            </header>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                <!-- Summary Section (2/3 width) -->
                <div class="lg:col-span-2">
                    <div class="bg-stone-800 p-4 rounded-lg h-auto mb-8">
                        <h2 class="text-2xl font-bold mb-4">Summary</h2>
                        <div>${analysis.hotel_analysis.summary}</div>
                    </div>

                    <!-- Overall Sentiment -->
                    <div class="bg-stone-800 p-4 rounded-lg h-auto mb-8">
                        <h2 class="text-2xl font-bold mb-4">Overall Sentiment</h2>
                        <div class="grid grid-cols-2 gap-4">
                            <div class="border border-[#7fd36e] rounded-lg p-4">
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Average Score</h3>
                                <p class="text-3xl font-bold">${analysis.hotel_analysis.overall_sentiment.average_score}/5</p>
                            </div>
                            <div class="border border-[#7fd36e] rounded-lg p-4">
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Sentiment Distribution</h3>
                                <p>Positive: ${analysis.hotel_analysis.overall_sentiment.positive_percentage}%</p>
                                <p>Neutral: ${analysis.hotel_analysis.overall_sentiment.neutral_percentage}%</p>
                                <p>Negative: ${analysis.hotel_analysis.overall_sentiment.negative_percentage}%</p>
                            </div>
                        </div>
                    </div>

                    <!-- Accommodation -->
                    <div class="bg-stone-800 p-4 rounded-lg h-auto mb-8">
                        <h2 class="text-2xl font-bold mb-4">Accommodation</h2>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Room Quality</h3>
                                <ul class="list-disc pl-5">
                                    ${analysis.hotel_analysis.accommodation.room_quality.map(item => `<li>${item}</li>`).join('')}
                                </ul>
                            </div>
                            <div>
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Common Praises</h3>
                                <ul class="list-disc pl-5">
                                    ${analysis.hotel_analysis.accommodation.common_praises.map(praise => `<li>${praise}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="mt-4">
                            <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Common Criticisms</h3>
                            <ul class="list-disc pl-5">
                                ${analysis.hotel_analysis.accommodation.common_criticisms.map(criticism => `<li>${criticism}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="mt-4">
                            <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Suggestions for Improvement</h3>
                            <ul class="list-disc pl-5">
                                ${analysis.hotel_analysis.accommodation.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                            </ul>
                        </div>
                    </div>

                    <!-- Service -->
                    <div class="bg-stone-800 p-4 rounded-lg h-auto mb-8">
                        <h2 class="text-2xl font-bold mb-4">Service</h2>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Strengths</h3>
                                <ul class="list-disc pl-5">
                                    ${analysis.hotel_analysis.service.strengths.map(strength => `<li>${strength}</li>`).join('')}
                                </ul>
                            </div>
                            <div>
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Weaknesses</h3>
                                <ul class="list-disc pl-5">
                                    ${analysis.hotel_analysis.service.weaknesses.map(weakness => `<li>${weakness}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="mt-4">
                            <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Suggestions for Improvement</h3>
                            <ul class="list-disc pl-5">
                                ${analysis.hotel_analysis.service.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                            </ul>
                        </div>
                    </div>

                    <!-- Amenities -->
                    <div class="bg-stone-800 p-4 rounded-lg h-auto mb-8">
                        <h2 class="text-2xl font-bold mb-4">Amenities</h2>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Praised Features</h3>
                                <ul class="list-disc pl-5">
                                    ${analysis.hotel_analysis.amenities.praised_features.map(feature => `<li>${feature}</li>`).join('')}
                                </ul>
                            </div>
                            <div>
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Criticized Features</h3>
                                <ul class="list-disc pl-5">
                                    ${analysis.hotel_analysis.amenities.criticized_features.map(feature => `<li>${feature}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="mt-4">
                            <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Suggestions for Improvement</h3>
                            <ul class="list-disc pl-5">
                                ${analysis.hotel_analysis.amenities.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                            </ul>
                        </div>
                    </div>

                    <!-- Food and Dining -->
                    <div class="bg-stone-800 p-4 rounded-lg h-auto mb-8">
                        <h2 class="text-2xl font-bold mb-4">Food and Dining</h2>
                        <p class="mb-4">${analysis.hotel_analysis.food_and_dining.restaurant_quality}</p>
                        <p class="mb-4">${analysis.hotel_analysis.food_and_dining.breakfast_feedback}</p>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Praised Items</h3>
                                <ul class="list-disc pl-5">
                                    ${analysis.hotel_analysis.food_and_dining.praised_items.map(item => `<li>${item}</li>`).join('')}
                                </ul>
                            </div>
                            <div>
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Criticized Items</h3>
                                <ul class="list-disc pl-5">
                                    ${analysis.hotel_analysis.food_and_dining.criticized_items.map(item => `<li>${item}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="mt-4">
                            <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Suggestions for Improvement</h3>
                            <ul class="list-disc pl-5">
                                ${analysis.hotel_analysis.food_and_dining.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                            </ul>
                        </div>
                    </div>

                    <!-- Location and Accessibility -->
                    <div class="bg-stone-800 p-4 rounded-lg h-auto mb-8">
                        <h2 class="text-2xl font-bold mb-4">Location and Accessibility</h2>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Positive Aspects</h3>
                                <ul class="list-disc pl-5">
                                    ${analysis.hotel_analysis.location_and_accessibility.positive_aspects.map(aspect => `<li>${aspect}</li>`).join('')}
                                </ul>
                            </div>
                            <div>
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Negative Aspects</h3>
                                <ul class="list-disc pl-5">
                                    ${analysis.hotel_analysis.location_and_accessibility.negative_aspects.map(aspect => `<li>${aspect}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="mt-4">
                            <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Suggestions for Improvement</h3>
                            <ul class="list-disc pl-5">
                                ${analysis.hotel_analysis.location_and_accessibility.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                            </ul>
                        </div>
                    </div>

                    <!-- Value for Money -->
                    <div class="bg-stone-800 p-4 rounded-lg h-auto mb-8">
                        <h2 class="text-2xl font-bold mb-4">Value for Money</h2>
                        <p class="mb-4">${analysis.hotel_analysis.value_for_money.perceived_value}</p>
                        <div class="grid grid-cols-2 gap-4">
                            <div>
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Positive Factors</h3>
                                <ul class="list-disc pl-5">
                                    ${analysis.hotel_analysis.value_for_money.positive_factors.map(factor => `<li>${factor}</li>`).join('')}
                                </ul>
                            </div>
                            <div>
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Negative Factors</h3>
                                <ul class="list-disc pl-5">
                                    ${analysis.hotel_analysis.value_for_money.negative_factors.map(factor => `<li>${factor}</li>`).join('')}
                                </ul>
                            </div>
                        </div>
                        <div class="mt-4">
                            <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Suggestions for Improvement</h3>
                            <ul class="list-disc pl-5">
                                ${analysis.hotel_analysis.value_for_money.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                            </ul>
                        </div>
                    </div>

                    <!-- Online Presence -->
                    <div class="bg-stone-800 p-4 rounded-lg h-auto mb-8">
                        <h2 class="text-2xl font-bold mb-4">Online Presence</h2>
                        <div>
                            <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Website Feedback</h3>
                            <ul class="list-disc pl-5">
                                ${analysis.hotel_analysis.online_presence.website_feedback.map(feedback => `<li>${feedback}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="mt-4">
                            <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Social Media Feedback</h3>
                            <ul class="list-disc pl-5">
                                ${analysis.hotel_analysis.online_presence.social_media_feedback.map(feedback => `<li>${feedback}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="mt-4">
                            <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Suggestions for Improvement</h3>
                            <ul class="list-disc pl-5">
                                ${analysis.hotel_analysis.online_presence.suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                            </ul>
                        </div>
                    </div>

                    <!-- Top Improvement Priorities -->
                    <div class="bg-stone-800 p-4 rounded-lg h-auto">
                        <h2 class="text-2xl font-bold mb-4">Top Improvement Priorities</h2>
                        ${analysis.hotel_analysis.top_improvement_priorities.map((priority, index) => `
                            <div class="mb-4 p-4 border border-[#7fd36e] rounded-lg">
                                <h3 class="text-lg font-semibold text-[#7fd36e] mb-2">Priority ${index + 1}: ${priority.category}</h3>
                                <p><strong>Issue:</strong> ${priority.issue}</p>
                                <p><strong>Suggestion:</strong> ${priority.suggestion}</p>
                                <p><strong>Potential Impact:</strong> ${priority.potential_impact}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>

                <!-- Reviews Section (1/3 width) -->
                <div class="lg:col-span-1">
                    <div class="bg-stone-800 p-4 rounded-lg">
                        <h2 class="text-2xl font-bold mb-4">Reviews</h2>
                        <div id="reviewsList" class="space-y-4">
                            ${renderReviews(analysis.reviews.slice(0, 10))}
                        </div>
                        <div id="hiddenReviews" class="hidden space-y-4">
                            ${renderReviews(analysis.reviews.slice(10))}
                        </div>
                        ${analysis.reviews.length > 10 ? 
                            `<button id="loadMoreBtn" class="mt-4 bg-[#7fd36e] hover:bg-[#6ac259] text-stone-800 font-bold py-2 px-4 rounded">
                                Load More
                            </button>` : ''
                        }
                    </div>
                </div>
            </div>
        </div>
    `;

    // Remove the loader overlay
    const loaderOverlay = document.getElementById('loaderOverlay');
    if (loaderOverlay) {
        loaderOverlay.remove();
    }

    const analysisContent = document.getElementById('analysisContent');
    analysisContent.innerHTML = analysisHTML;

    // Scroll to the analysis content
    setTimeout(() => {
        analysisContent.scrollIntoView({ behavior: 'smooth' });
    }, 100);

    // Add event listener for "Load More" button
    const loadMoreBtn = document.getElementById('loadMoreBtn');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', () => {
            const hiddenReviews = document.getElementById('hiddenReviews');
            document.getElementById('reviewsList').innerHTML += hiddenReviews.innerHTML;
            hiddenReviews.remove();
            loadMoreBtn.remove();
        });
    }
}

function renderReviews(reviews) {
    return reviews.map(review => `
        <div class="bg-stone-800 p-4 rounded-lg border border-stone-700">
            <div class="flex justify-between items-center mb-2">
                <span class="font-bold">${review.user}</span>
                <span class="text-stone-400">${review.date}</span>
            </div>
            <div class="text-yellow-400 mb-2">
                ${'★'.repeat(Math.floor(review.rating))}
                ${review.rating % 1 >= 0.5 ? '½' : ''}
                ${'☆'.repeat(5 - Math.ceil(review.rating))}
            </div>
            <p>${review.review_text}</p>
        </div>
    `).join('');
}



// Call requestLocation when the page loads
window.addEventListener('load', requestLocation);

// Add event listener for input changes
searchInput.addEventListener('input', function() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(getSuggestions, 500);
});

generateButton.addEventListener('click', getAnalysis);
