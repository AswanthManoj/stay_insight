import os, time
from openai import OpenAI
from pprint import pprint
import asyncio, json, httpx
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from review_ai.prompt import SYSTEM_PROMPT, DATA_PROMPT
from review_ai.utils import (AnalysisResult, APIError, NoResultsError, 
SuggestionResult, Review, Suggestion, DataProcessorError, HotelAnalysis)



class DataProcessor:
    
    def __init__(self, api_key: str, num_reviews: int=50, num_suggestion: int=5, language: str="en", country: str="in", delay: float=1) -> None:
        """
        Initializes the DataProcessor with the given parameters.

        Parameters:
        api_key (str): The SerpApi API key to use for requests.
        num_reviews (int): The number of reviews to fetch. Defaults to 50.
        num_suggestion (int): The number of suggestions to fetch. Defaults to 5.
        language (str): The language to use for the search. Defaults to "en".
        country (str): The country to use for the search. Defaults to "in".
        delay (float): The delay in seconds between requests. Defaults to 1 second.
        """
        self.delay = delay
        self.api_key = api_key
        self.country = country
        self.language = language
        self.num_reviews = num_reviews
        self.num_suggestion = num_suggestion
        self.base_url = "https://serpapi.com/search.json"
        
    def convert_datetime(self, dt_string: str) -> str:
        """
        Converts a datetime string in the format %Y-%m-%dT%H:%M:%SZ to a human-readable format.

        Parameters:
        dt_string (str): The datetime string to convert.

        Returns:
        str: The formatted datetime string.
        """
        dt_object = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%SZ")
        formatted_dt = dt_object.strftime("%B %d, %Y at %I:%M %p UTC")
        return formatted_dt
        
    async def get_reviews(self, data_id: str, sort_by: str = "qualityScore") -> AnalysisResult:
        """
        Fetches reviews for a given data_id and returns an AnalysisResult with the extracted information.

        Parameters:
        data_id (str): The data_id to fetch reviews for.
        sort_by (str): The field to sort the reviews by. Defaults to "qualityScore".

        Returns:
        AnalysisResult: An AnalysisResult with the extracted information.
        """
        _reviews = []
        params = {
            "data_id": data_id,
            "sort_by": sort_by,
            "hl": self.language,
            "api_key": self.api_key,
            "engine": "google_maps_reviews",
        }
        
        place_info = None
        search_metadata = None
        search_parameters = None

        try:
            async with httpx.AsyncClient() as client:
                while len(_reviews) < self.num_reviews:
                    response = await client.get(self.base_url, params=params)
                    data = response.json()

                    if not place_info:
                        place_info = data.get("place_info", {})
                    if not search_metadata:
                        search_metadata = data.get("search_metadata", {})
                    if not search_parameters:
                        search_parameters = data.get("search_parameters", {})

                    new_reviews = data.get("reviews", [])
                    _reviews.extend(new_reviews)

                    if "serpapi_pagination" not in data or "next" not in data["serpapi_pagination"]:
                        # No more pages
                        break

                    params["next_page_token"] = data["serpapi_pagination"]["next_page_token"]
                    
                    if len(_reviews) >= self.num_reviews:
                        break

                    await asyncio.sleep(self.delay)
                    
            _reviews = _reviews[:self.num_reviews]

            reviews = [Review(
                rating=review.get("rating", 0),
                user=review.get("user", {}).get("name", ""),
                date=self.convert_datetime(review.get("iso_date", "")),
                review_text=review.get("extracted_snippet", {}).get("original", "")
            ) for review in _reviews]

            return AnalysisResult(
                reviews=reviews,
                type=place_info.get("type", ""),
                title=place_info.get("title", ""),
                rating=place_info.get("rating", 0.0),
                address=place_info.get("address", ""),
                status=search_metadata.get("status", ""),
                total_reviews=place_info.get("reviews", 0),
                data_id=search_parameters.get("data_id", ""),
                created_at=search_metadata.get("created_at", ""),
            )   
                

        except APIError as e:
            # If we have partial results, return them
            if _reviews:
                print(f"Warning: Partial results due to API error: {str(e)}")
                return self._create_partial_result(_reviews, data_id)
            else:
                # Re-raise the APIError if we have no reviews
                raise

        except Exception as e:
            raise DataProcessorError(f"An unexpected error occurred: {str(e)}")

    def _create_partial_result(self, reviews: List[Dict], data_id: str) -> AnalysisResult:
        """
        Creates an AnalysisResult from a list of reviews, to be used in the event of an API error.
        The result will be marked as "Partial" and will not contain any location-specific information.

        Args:
            reviews (List[Dict]): A list of review dictionaries, with keys "iso_date", "rating", "user", and "extracted_snippet".
            data_id (str): The data ID of the location.

        Returns:
            AnalysisResult: An AnalysisResult object containing the reviews.
        """
        formatted_reviews = [Review(
            date=review.get("iso_date", ""),
            rating=review.get("rating", 0),
            user=review.get("user", {}).get("name", ""),
            review_text=review.get("extracted_snippet", {}).get("original", ""),
        ) for review in reviews]

        return AnalysisResult(
            reviews=formatted_reviews,
            type="",
            title="",
            rating=0,
            address="",
            status="Partial",
            total_reviews=len(formatted_reviews),
            data_id=data_id,
            created_at="",
        )
            
    async def get_suggestions(self, query: str, longitude: float, latitude: float, filter: Optional[str]=None) -> SuggestionResult:
        """
        Fetches suggestions for a given query and location, and returns a SuggestionResult with the extracted information.

        Parameters:
        query (str): The query to search for.
        longitude (float): The longitude of the location.
        latitude (float): The latitude of the location.
        filter (Optional[str]): The type of suggestion to filter the results by. Defaults to None, which returns all types of suggestions.

        Returns:
        SuggestionResult: A SuggestionResult with the extracted information.
        """
        try:
            location = f"@{latitude},{longitude},3z"
            params = {
                "q": query,
                "ll": location,
                "hl": self.language,
                "api_key": self.api_key,
                "engine": "google_maps_autocomplete",
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params)
                results = response.json()

            if "suggestions" not in results:
                raise NoResultsError(f"No suggestions found for query: {query}")

            suggestions = []
            for suggestion in results["suggestions"]:
                if "data_id" in suggestion:
                    if filter is None or suggestion["type"] == filter:
                        suggestions.append(Suggestion(
                            type=suggestion.get("type", ""),
                            value=suggestion.get("value", ""),
                            data_id=suggestion["data_id"],
                            subtext=suggestion.get("subtext", ""),
                            latitude=suggestion.get("latitude", 0.0),
                            longitude=suggestion.get("longitude", 0.0)
                        ))

            if not suggestions:
                raise NoResultsError(f"No matching suggestions found for query: {query}")

            return SuggestionResult(
                status=results["search_metadata"]["status"],
                suggestions=suggestions[:self.num_suggestion],
                created_at=results["search_metadata"]["created_at"],
            )

        except (APIError, NoResultsError) as e:
            raise
        except Exception as e:
            raise DataProcessorError(f"An unexpected error occurred while fetching suggestions: {str(e)}")



class ReviewAnalyzer:
    def __init__(self, model: str, api_key: str|List[str], system_prompt: str, data_prompt: str) -> None:
        self.model = model
        self.data_prompt = data_prompt
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=api_key)

    def reviews_to_string(self, reviews: List[Review]) -> str:
        return "\n".join([f"- {review.user} gave a rating of '{review.rating}/5' on '{review.date}' with comment {review.review_text}" for review in reviews])

    async def generate_analysis(self, review_analysis: AnalysisResult) -> AnalysisResult:
        """
        Generates a hotel analysis based on the given review_analysis.

        Parameters:
        review_analysis (AnalysisResult): The AnalysisResult object to generate the hotel analysis for.

        Returns:
        AnalysisResult: The modified AnalysisResult object with the hotel_analysis field populated.
        """
        completion = self.client.beta.chat.completions.parse(
            model=self.model or "gpt-4o-mini",
            max_completion_tokens=4000,
            messages=[
                {"role": "system", "content": self.system_prompt.format(
                    name=review_analysis.title, 
                    rating=review_analysis.rating, 
                    address=review_analysis.address,
                    todays_date=datetime.now().strftime("%Y-%m-%d"),
                    total_reviews=review_analysis.total_reviews,
                )},
                {"role": "user", "content": self.data_prompt.format(
                    reviews=self.reviews_to_string(review_analysis.reviews)
                )}
            ],
            response_format=HotelAnalysis,
        )
        review_analysis.hotel_analysis = completion.choices[0].message.parsed
        return review_analysis



DATA_PROCESSOR = None
def get_data_processor(api_key: str, num_reviews: int=50, num_suggestion: int=5, language: str="en", country: str="in", delay: float=1) -> DataProcessor:
    """
    Returns an instance of DataProcessor with the given parameters.

    Parameters:
    api_key (str): The SerpApi API key to use for requests.
    num_reviews (int): The number of reviews to fetch. Defaults to 50.
    num_suggestion (int): The number of suggestions to fetch. Defaults to 5.
    language (str): The language to use for the search. Defaults to "en".
    country (str): The country to use for the search. Defaults to "in".
    delay (float): The delay in seconds between requests. Defaults to 1 second.

    Returns:
    DataProcessor: An instance of DataProcessor with the given parameters.
    """
    global DATA_PROCESSOR
    if DATA_PROCESSOR is None:
        DATA_PROCESSOR = DataProcessor(
            delay=delay,
            api_key=api_key, 
            country=country, 
            language=language,
            num_reviews=num_reviews, 
            num_suggestion=num_suggestion, 
        )
    return DATA_PROCESSOR


ANALYZER = None
def get_analyzer(model: str, api_key: str) -> ReviewAnalyzer:
    """
    Returns an instance of ReviewAnalyzer with the given model and API key.

    Parameters:
    model (str): The model to use for analysis. Defaults to "gpt-4o-mini".
    api_key (str): The OpenAI API key to use for requests.

    Returns:
    ReviewAnalyzer: An instance of ReviewAnalyzer with the given model and API key.
    """
    global ANALYZER
    if ANALYZER is None:
        ANALYZER = ReviewAnalyzer(
            model=model,
            api_key=api_key,
            data_prompt=DATA_PROMPT,
            system_prompt=SYSTEM_PROMPT
        )
    return ANALYZER