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


function displayAnalysis(analysis) {
    const starRating = '★'.repeat(Math.floor(analysis.rating)) + 
                       (analysis.rating % 1 >= 0.5 ? '½' : '') + 
                       '☆'.repeat(5 - Math.ceil(analysis.rating));

    let analysisHTML = `
        <div class="bg-stone-900 p-4">
            <header class="mb-8 flex justify-between items-start">
                <div>
                    <h1 class="text-4xl font-bold mb-2">${analysis.title}</h1>
                    <p class="text-xl text-stone-400">${analysis.address}</p>
                    <div class="text-2xl text-yellow-400 mt-2">${starRating} (${analysis.rating})</div>
                    <span class="text-stone-500 sm:text-md md:text-lg lg:text-xl mt-2">Total reviews: ${analysis.total_reviews}</span>
                </div>
                <button id="downloadAnalysis" class="bg-[#7fd36e] hover:bg-[#6ac259] text-stone-800 font-bold py-2 px-4 rounded">
                    Download Analysis
                </button>
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

    document.getElementById('downloadAnalysis').addEventListener('click', async (e) => {
        const token = tokenInput.value.trim();
        try {
            window.location.href = `/api/download/${token}`;
        } catch (error) {
            console.error('Error:', error);
            alert('Error downloading PDF');
        }
    });

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
            <span class="block sm:inline">Your token has been expired!</span>
        </div>
    `;
}

// Event listener
retrieveButton.addEventListener('click', retrieveAnalysis);