import aiosqlite
import yaml, os, json
from openai import OpenAI
from pprint import pprint
import asyncio, uuid, httpx
from datetime import datetime
from fastapi import BackgroundTasks
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright
from review_ai.utils import (AnalysisResult, APIError, NoResultsError, 
SuggestionResult, Review, Suggestion, DataProcessorError, HotelAnalysis)
from review_ai.prompt import SYSTEM_PROMPT, DATA_PROMPT, BATCH_ANALYTICS_PROMPT



class DataBase:
    """
    A class to handle asynchronous SQLite database operations for storing and retrieving place reviews for place data_id.
    """
    def __init__(self, database_name: str = "reviews.db") -> None:
        """
        Initialize a `DataBase` instance.

        Args:
        - database_name (str, optional): The name of the SQLite database file to use. Defaults to "reviews.db".
        """
        self.database_name = database_name
        self.full_table_name = "review_analysis_full"
        self.instant_table_name = "review_analysis_instant"

    async def create_tables(self) -> None:
        """
        Create SQLite tables to store review analysis results.

        Two tables are created: review_analysis_instant and review_analysis_full.
        Each table has two columns: `data_id` and `analysis`. 
        The `data_id` column is the primary key.
        The `analysis` column stores the JSON-serialized review analysis result.

        The tables are created if they do not already exist. If the tables already exist, this method does nothing.
        """
        async with aiosqlite.connect(self.database_name) as conn:
            for table_name in [self.instant_table_name, self.full_table_name]:
                await conn.execute(f'''
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        data_id TEXT PRIMARY KEY,
                        analysis TEXT
                    )
                ''')
            await conn.commit()

    async def check_and_retrieve_place(self, data_id: str, data_type: Optional[str] = None) -> List[Dict[str, any]]:
        """
        Check if a review analysis exists in the database and retrieve it if it does.

        Args:
        - data_id (str): The unique identifier for the review analysis to be retrieved.
        - data_type (Optional[str]): The type of analysis to retrieve. If None, both types are retrieved.

        Returns:
        - List[Dict[str, any]]: A list of review analyses matching the criteria. Each item is a dictionary
          with keys "data_id", "type", and "analysis". Returns an empty list if no matching analyses are found.
        """
        result = []
        async with aiosqlite.connect(self.database_name) as conn:
            if data_type in ["instant", None]:
                async with conn.execute(f"SELECT data_id, analysis FROM {self.instant_table_name} WHERE data_id = ?", (data_id,)) as cursor:
                    if row := await cursor.fetchone():
                        result.append({
                            "data_id": row[0],
                            "type": "instant",
                            "analysis": json.loads(row[1])
                        })
            
            if data_type in ["full", None]:
                async with conn.execute(f"SELECT data_id, analysis FROM {self.full_table_name} WHERE data_id = ?", (data_id,)) as cursor:
                    if row := await cursor.fetchone():
                        result.append({
                            "data_id": row[0],
                            "type": "full",
                            "analysis": json.loads(row[1])
                        })
        
        return result

    async def save_new_data(self, data_id: str, data_type: str, data: Dict[str, any]) -> Optional[str]:
        """
        Save new review analysis data in the database.

        Args:
        - data_id (str): The unique identifier for the review analysis to be saved.
        - data_type (str): The type of analysis, either "instant" or "full".
        - data (Dict[str, any]): The review analysis result to be saved.

        Returns:
        - str: The data_id if the data is saved successfully, otherwise None.

        If a review analysis with the same data_id already exists in the respective table, 
        the existing entry will be replaced with the new data.

        Raises:
        - ValueError: If the data_type is not "instant" or "full".
        """
        if data_type not in ["instant", "full"]:
            raise ValueError("data_type must be either 'instant' or 'full'")

        table_name = self.instant_table_name if data_type == "instant" else self.full_table_name
        analysis_json = json.dumps(data)
        
        try:
            async with aiosqlite.connect(self.database_name) as conn:
                await conn.execute(f"INSERT OR REPLACE INTO {table_name} (data_id, analysis) VALUES (?, ?)", 
                                   (data_id, analysis_json))
                await conn.commit()
            return data_id
        except aiosqlite.Error as e:
            print(f"Error saving data: {e}")
            return None



class DataProcessor:
    
    def __init__(self, api_key: str, num_reviews: int=50, max_reviews: int=150, num_suggestion: int=5, language: str="en", country: str="in", delay: float=1, verbosity: bool=False) -> None:
        """
        Initialize a DataProcessor object.

        Args:
        - api_key (str): The SERPAPI key to use for searching Google Reviews.
        - num_reviews (int): The number of reviews to fetch in each search. Defaults to 50.
        - max_reviews (int): The maximum number of reviews to fetch in total. Defaults to 150.
        - num_suggestion (int): The number of autocomplete suggestions to fetch. Defaults to 5.
        - language (str): The language of the reviews to fetch. Defaults to "en".
        - country (str): The country code of the location to search. Defaults to "in".
        - delay (float): The delay in seconds between each search. Defaults to 1.
        - verbosity (bool): Whether to print debug messages. Defaults to False.
        """
        self.delay = delay
        self.api_key = api_key
        self.country = country
        self.language = language
        self.verbosity = verbosity
        self.num_reviews = num_reviews
        self.max_reviews = max_reviews
        self.num_suggestion = num_suggestion
        self.base_url = "https://serpapi.com/search.json"
        
    def convert_datetime(self, dt_string: str) -> str:
        """
        Converts a datetime string from the format "%Y-%m-%dT%H:%M:%SZ"
        to "%B %d, %Y at %I:%M %p UTC".

        Args:
        - dt_string (str): The datetime string to be converted.

        Returns:
        - str: The converted datetime string.
        """
        dt_object = datetime.strptime(dt_string, "%Y-%m-%dT%H:%M:%SZ")
        formatted_dt = dt_object.strftime("%B %d, %Y at %I:%M %p UTC")
        return formatted_dt
      
    def sort_reviews_by_date(self, reviews: List[Review], reverse=False):
        """
        Sorts a list of reviews by date.

        Args:
        - reviews (List[Review]): The list of reviews to be sorted.
        - reverse (bool): Whether to sort in descending order. Defaults to False.

        Returns:
        - List[Review]: The sorted list of reviews.
        """
        def parse_date(date_string):
            return datetime.strptime(date_string, "%B %d, %Y at %I:%M %p UTC")
        return sorted(reviews, key=lambda review: parse_date(review.date), reverse=reverse)
        
    async def get_reviews(self, data_id: str, sort_by: str = "qualityScore", use_full_reviews: bool = False) -> AnalysisResult:
        """
        Retrieves Google Maps reviews for a given data_id.

        Args:
        - data_id (str): The data_id of the location to retrieve reviews for.
        - sort_by (str, optional): The field to sort the reviews by. Defaults to "qualityScore".
        - use_full_reviews (bool, optional): Whether to retrieve all reviews or just the top self.num_reviews. Defaults to False.

        Returns:
        - AnalysisResult: An AnalysisResult object containing the retrieved reviews, sorted by date in descending order.
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
                count = 0
                while True:
                    response = await client.get(self.base_url, params=params)
                    data = response.json()

                    print(data)

                    if not place_info:
                        place_info = data.get("place_info", {})
                    if not search_metadata:
                        search_metadata = data.get("search_metadata", {})
                    if not search_parameters:
                        search_parameters = data.get("search_parameters", {})

                    new_reviews = data.get("reviews", [])
                    _reviews.extend(new_reviews)
                    if self.verbosity:
                        print(f"DataProcessor.get_reviews | {count} | New {len(new_reviews)} reviews fetched for data_id {data_id}")
                        count+=1

                    if use_full_reviews:
                        if len(_reviews) >= self.max_reviews:
                            break
                    elif len(_reviews) >= self.num_reviews:
                        break

                    if "serpapi_pagination" not in data or "next" not in data["serpapi_pagination"]:
                        # No more pages
                        break

                    params["next_page_token"] = data["serpapi_pagination"]["next_page_token"]
                    await asyncio.sleep(self.delay)
                    if self.verbosity:
                        print(f"DataProcessor.get_reviews | Going to visit next review page for data_id {data_id}")

            if not use_full_reviews:
                _reviews = _reviews[:self.num_reviews]

            #print(_reviews)

            reviews = [Review(
                rating=review.get("rating", 0),
                user=review.get("user", {}).get("name", ""),
                date=self.convert_datetime(review.get("iso_date", "")),
                review_text=review.get("extracted_snippet", {}).get("original", "")
            ) for review in _reviews]
            
            if self.verbosity:
                print(f"DataProcessor.get_reviews | Reviews collection completed for data_id {data_id}")

            return AnalysisResult(
                type=place_info.get("type", ""),
                title=place_info.get("title", ""),
                rating=place_info.get("rating", 0.0),
                address=place_info.get("address", ""),
                status=search_metadata.get("status", ""),
                reviews=self.sort_reviews_by_date(reviews),
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
                # if self.verbosity:
                #     print(f"DataProcessor.get_reviews | Failed to fetch reviews for data_id {data_id} due to API error: {str(e)}")
                # Re-raise the APIError if we have no reviews
                raise

        except Exception as e:
            if self.verbosity:
                print(f"DataProcessor.get_reviews | Failed to fetch reviews for data_id {data_id} due to API error: {str(e)}")
            raise DataProcessorError(f"An unexpected error occurred: {str(e)}")

    def _create_partial_result(self, reviews: List[Dict], data_id: str) -> AnalysisResult:
        """
        Creates an AnalysisResult object with the given reviews, marked as a partial result.

        Args:
        - reviews (List[Dict]): The list of reviews to include in the result.
        - data_id (str): The data_id of the location to associate the partial result with.

        Returns:
        - AnalysisResult: An AnalysisResult object with the given reviews, type, title, rating, address, status, total_reviews, data_id, and created_at fields populated.
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
        Retrieves Google Maps Autocomplete suggestions for the given query, filtered by the given longitude and latitude.
        
        Args:
        - query (str): The query to search for.
        - longitude (float): The longitude of the location to filter suggestions by.
        - latitude (float): The latitude of the location to filter suggestions by.
        - filter (str): An optional filter to limit the suggestions to a specific type (e.g. "establishment", "geocode", etc.).
        
        Returns:
        - SuggestionResult: An object containing the status of the request, a list of up to self.num_suggestion Suggestion objects, and the created_at timestamp of the request.
        
        Raises:
        - APIError: If the request to the API fails.
        - NoResultsError: If no suggestions are found for the given query.
        - DataProcessorError: If an unexpected error occurs while fetching suggestions.
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
                raise NoResultsError(f"No suggestions found for query: `{query}`")

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
                if self.verbosity:
                    print(f"DataProcessor.get_suggestions | No suggestions found for query `{query}`")
                raise NoResultsError(f"No matching suggestions found for query: `{query}`")

            return SuggestionResult(
                status=results["search_metadata"]["status"],
                suggestions=suggestions[:self.num_suggestion],
                created_at=results["search_metadata"]["created_at"],
            )

        except (APIError, NoResultsError) as e:
            raise
        except Exception as e:
            if self.verbosity:
                print(f"DataProcessor.get_suggestions | An unexpected error occurred while fetching suggestions for query `{query}`: {str(e)}")
            raise DataProcessorError(f"An unexpected error occurred while fetching suggestions: {str(e)}")



class ReviewAnalyzer:
    def __init__(self, model: str, api_key: str|List[str], system_prompt: str, data_prompt: str, batch_analytics_prompt: str, verbosity: bool=False) -> None:
        """
        Initializes the ReviewAnalyzer object with the given parameters.

        Args:
        - model (str): The name of the OpenAI model to use for analysis.
        - api_key (str|List[str]): The OpenAI API key to use. If a list is provided, the first key will be used for the first request, the second for the second request, and so on.
        - system_prompt (str): The system prompt to send to the model as part of the analysis request.
        - data_prompt (str): The data prompt to send to the model as part of the analysis request.
        - batch_analytics_prompt (str): The batch analytics prompt to send to the model as part of the analysis request.
        - verbosity (bool): Whether to print debug messages during the analysis process. Defaults to False.
        """
        self.model = model
        self.verbosity = verbosity
        self.data_prompt = data_prompt
        self.system_prompt = system_prompt
        self.client = OpenAI(api_key=api_key)
        self.batch_analytics_prompt = batch_analytics_prompt

    def reviews_to_string(self, reviews: List[Review]) -> str:
        """
        Converts a list of Review objects into a string.

        Args:
        - reviews (List[Review]): The list of Review objects to convert.

        Returns:
        - str: A string containing the information from the Review objects, formatted as a list item for each review.
        """
        return "\n".join([f"- {review.user} gave a rating of '{review.rating}/5' on '{review.date}' with comment {review.review_text}" for review in reviews])

    def _generate_(self, messages: List[dict]):
        """
        Uses the OpenAI LLM to generate text based on the provided messages.

        Args:
        - messages (List[dict]): The messages to provide to the LLM, where each message is a dictionary containing the following keys:
            - role (str): The role of the message, either "system" or "user".
            - content (str): The content of the message.

        Returns:
        - AnalysisResult: The generated text, parsed as an AnalysisResult object.
        """
        if self.verbosity:
            print("ReviewAnalyzer._generate_ | LLM Call")
        return self.client.beta.chat.completions.parse(
            messages=messages,
            max_completion_tokens=3000,
            response_format=HotelAnalysis,
            model=self.model or "gpt-4o-mini",
        )

    async def generate_analysis(self, review_analysis: AnalysisResult) -> AnalysisResult:
        """
        Uses the OpenAI LLM to generate an analysis of the provided reviews.

        Args:
        - review_analysis (AnalysisResult): The analysis to generate text for, including the reviews to consider.

        Returns:
        - AnalysisResult: The generated analysis, with the hotel_analysis field populated with the generated text.
        """
        messages = [
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
        ]
        if self.verbosity:
            print("ReviewAnalyzer.generate_analysis | Generating analysis for the reviews")
        loop = asyncio.get_event_loop()
        completion = await loop.run_in_executor(None, self._generate_, messages)
        review_analysis.hotel_analysis = completion.choices[0].message.parsed
        return review_analysis
    
    async def combine_analysis(self, analysis_results: List[AnalysisResult]) -> AnalysisResult:
        """
        Uses the OpenAI LLM to combine the analysis of multiple batches of reviews.

        Args:
        - analysis_results (List[AnalysisResult]): The analysis results to combine, each containing the reviews to consider and the generated analysis.

        Returns:
        - AnalysisResult: The combined analysis, with the hotel_analysis field populated with the generated text.
        """
        if len(analysis_results) == 1:
            return analysis_results[0]
        
        messages = [
            {"role": "system", "content": self.batch_analytics_prompt.format(
                name=analysis_results[0].title, 
                rating=analysis_results[0].rating, 
                address=analysis_results[0].address,
                todays_date=datetime.now().strftime("%Y-%m-%d"),
                total_reviews=analysis_results[0].total_reviews,
            )},
            {"role": "user", "content": "\n---\n\n".join([
                f"[{analysis_results[i].reviews[0].date} to {analysis_results[i].reviews[-1].date}]\n{yaml.dump(result.hotel_analysis.model_dump())}" 
                for i, result in enumerate(analysis_results)])
            }
        ]
        if self.verbosity:
            print("ReviewAnalyzer.combine_analysis | Combining analysis together")
        loop = asyncio.get_event_loop()
        completion = await loop.run_in_executor(None, self._generate_, messages)
        analysis = AnalysisResult(**analysis_results[0].model_dump())
        analysis.hotel_analysis = completion.choices[0].message.parsed
        return analysis
    
    

class TaskManager:
    def __init__(self, data_processor: DataProcessor, review_analyzer: ReviewAnalyzer, batch_size: int=30, verbosity: bool=False) -> None:
        """
        Initializes the TaskManager object.

        Args:
        - data_processor (DataProcessor): The DataProcessor object to use for fetching reviews.
        - review_analyzer (ReviewAnalyzer): The ReviewAnalyzer object to use for analyzing reviews.
        - batch_size (int): The number of reviews to process in each batch. Defaults to 30.
        - verbosity (bool): Whether to print debug messages. Defaults to False.
        """
        self.cleanup_task = None
        self.analysis_results = {}
        self.verbosity = verbosity
        self.batch_size = batch_size
        self.database = get_database()
        self.data_processor = data_processor
        self.review_analyzer = review_analyzer
        
    async def start_cleanup_task(self):
        """
        Start a background task to clean up old analysis results.

        This task periodically checks for any analysis results that are over 24 hours old
        and removes them from the cache. If the task is already running, this function does nothing.
        """
        if self.cleanup_task is None:
            await self.database.create_tables()
            self.cleanup_task = asyncio.create_task(self.cleanup_old_results())

    async def cleanup_old_results(self):
        """
        Periodically clean up old analysis results from the cache.

        This task checks every hour for any analysis results that are over 24 hours old and removes them from the cache.
        """
        while True:
            await asyncio.sleep(3600)  # Check every hour
            current_time = datetime.now()
            to_remove = []
            for token, result in self.analysis_results.items():
                if 'created_at' in result and current_time - result['created_at'] > timedelta(hours=24):
                    to_remove.append(token)
            for token in to_remove:
                del self.analysis_results[token]
        
    async def autocomplete(self, query: str, longitude: float, latitude: float, filter: Optional[str]=None) -> SuggestionResult:
        """
        Autocomplete a search query with location-based suggestions.

        Args:
        - query (str): The search query to autocomplete.
        - longitude (float): The longitude of the location to filter suggestions by.
        - latitude (float): The latitude of the location to filter suggestions by.
        - filter (str): An optional filter to limit the suggestions to a specific type (e.g. "establishment", "geocode", etc.).

        Returns:
        - SuggestionResult: A JSON response containing the autocomplete suggestions.
        """
        return await self.data_processor.get_suggestions(query, longitude, latitude, filter)

    async def get_instant_analysis(self, data_id: str) -> AnalysisResult:
        """
        Get the instant analysis for the given data ID.

        Args:
        - data_id (str): The data ID of the location to get the analysis for.

        Returns:
        - AnalysisResult: A JSON response containing the analysis result.

        Raises:
        - ValueError: If no reviews are found for the given data ID.
        """
        
        # Check if analysis already in db
        existing_data = await self.database.check_and_retrieve_place(data_id, "instant")
        if existing_data:
            return AnalysisResult(**existing_data[0]['analysis'])
        
        if self.verbosity:
            print(f"TaskManager.get_instant_analysis | Starting to fetch reviews for data_id `{data_id}`")
        review_result = await self.data_processor.get_reviews(data_id=data_id) 
        if review_result.reviews == [] or (not review_result.reviews):
            if self.verbosity:
                print(f"TaskManager.get_instant_analysis | No reviews found for data_id `{data_id}`")
            return {"status": "no_reviews", "data_id": data_id}
        
        if self.verbosity:
            print(f"TaskManager.get_instant_analysis | Starting to generate analysis for data_id `{data_id}`")
        review_result = await self.review_analyzer.generate_analysis(review_result)
        review_result.reviews = self.data_processor.sort_reviews_by_date(review_result.reviews, reverse=True)
        if self.verbosity:
            print(f"TaskManager.get_instant_analysis | Finished generating analysis for data_id `{data_id}`")
        
        # Save in db
        await self.database.save_new_data(data_id, "instant", review_result.model_dump())
        
        return review_result
    
    async def get_full_analysis(self, data_id: str, background_tasks: BackgroundTasks) -> dict:
        """
        Run a full analysis of the hotel in the background.

        Args:
        - data_id (str): The data ID of the hotel to get the analysis for.
        - background_tasks (BackgroundTasks): The background task manager for running the full analysis.

        Returns:
        - dict: A JSON response containing the analysis token.

        The full analysis is run asynchronously in the background, and the token can be used to retrieve the result.
        """
    
        # Check if analysis already in db
        existing_data = await self.database.check_and_retrieve_place(data_id, "full")
        if existing_data:
            self.analysis_results[data_id] = {
                "status": "completed",
                "created_at": datetime.now(),
                "data": existing_data[0]['analysis']
            }
            return {"token": data_id}
        
        background_tasks.add_task(self._process_full_analysis_, data_id, data_id)
        self.analysis_results[data_id] = {"status": "in_progress", "created_at": datetime.now()}
        return {"token": data_id}
    
    async def _process_full_analysis_(self, data_id: str, token: str) -> None:
        """
        Process the full analysis of the hotel in the background.

        Args:
        - data_id (str): The data ID of the hotel to get the analysis for.
        - token (str): The analysis token to store the result.

        Returns:
        - None

        The function is run asynchronously in the background, and the result is stored in `self.analysis_results` with the given token.
        The result can be retrieved using the `get_analysis_result` method.
        """
        try:
            # Get full hotel reviews
            if self.verbosity:
                print(f"TaskManager._process_full_analysis_ | Starting to fetch reviews for data_id `{data_id}`")
            review_result = await self.data_processor.get_reviews(data_id=data_id, use_full_reviews=True)
            
            if review_result.reviews == [] or (not review_result.reviews):
                if self.verbosity:
                    print(f"TaskManager._process_full_analysis_ | No reviews found for data_id `{data_id}`")
                raise ValueError("no_reviews")
            
            batches = [review_result.reviews[i:i + self.batch_size] for i in range(0, len(review_result.reviews), self.batch_size)]
            
            async def process_batch(batch):
                if self.verbosity:
                    print(f"TaskManager._process_full_analysis_ | Processing batches of reviews for data_id `{data_id}`")
                batch_result = AnalysisResult(**review_result.model_dump())
                batch_result.reviews = batch
                return await self.review_analyzer.generate_analysis(batch_result)
            
            async def combine_level(results: List[AnalysisResult], batch_size: int=10) -> List[AnalysisResult]:
                if len(results) <= 1:
                    return results
                
                batches = [results[i:i+batch_size] for i in range(0, len(results), batch_size)]
                combined_results = await asyncio.gather(*[self.review_analyzer.combine_analysis(batch) for batch in batches])

                if len(combined_results) > 1:
                    return await combine_level(combined_results)
                else:
                    return combined_results
                
            # Process batches asynchronously
            batch_results = await asyncio.gather(*[process_batch(batch) for batch in batches])
            
            # Combining analysis results
            final_results = await combine_level(batch_results, batch_size=self.batch_size//2)
            final_results[0].reviews = self.data_processor.sort_reviews_by_date(review_result.reviews, reverse=True)
            
            # Save in db
            await self.database.save_new_data(data_id, "full", final_results[0].model_dump())
            
            self.analysis_results[token] = {
                "status": "completed", 
                "created_at": datetime.now(),
                "data": final_results[0].model_dump(),
            }
            if self.verbosity:
                print(f"TaskManager._process_full_analysis_ | Full analysis completed for token: {token}")
        except Exception as e:
            self.analysis_results[token] = {
                "error": str(e),
                "status": "failed", 
                "created_at": datetime.now()
            }
            if self.verbosity:
                print(f"TaskManager._process_full_analysis_ | Full analysis failed for token: {token} with error: {e}")
            
    async def get_analysis_result(self, token: str) -> dict:
        """
        Get the analysis result for the given token.

        Args:
        - token (str): The token of the analysis result to be retrieved.

        Returns:
        - dict: A JSON response containing the analysis result, or a status message if the analysis is still in progress.

        Raises:
        - ValueError: If the token is invalid or expired.
        """
        if token not in self.analysis_results:
            raise ValueError(f"Invalid or expired token: {token}")

        result = self.analysis_results[token]
        
        if result["status"] == "completed":
            return result["data"]
        elif result["status"] == "in_progress":
            return {"status": "in_progress"}
        else:
            return {"status": "failed", "error": "no_reviews"}
  
  
  
async def download_result(host: str, port: int, token: str) -> str:
    url = f"http://{host}:{port}/retrieve"
    pdf_filename = f"/tmp/{uuid.uuid4()}.pdf"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.set_viewport_size({"width": 1920, "height": 1080})
        await page.goto(url)
        await page.fill('#tokenInput', token)
        await page.click('#retrieveButton')
        await page.wait_for_selector('#analysisContent', state='visible', timeout=10000)
        
        await page.evaluate('''() => {
            const element = document.getElementById('analysisContent');
            const rect = element.getBoundingClientRect();
            document.body.innerHTML = '';
            document.body.appendChild(element);
            
            const divToRemove = document.evaluate(
                '//*[@id="analysisContent"]/div/div/div[2]/div',
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;
            if (divToRemove) {
                divToRemove.remove();
            }
            const buttonToRemove = document.evaluate(
                '//*[@id="downloadAnalysis"]',
                document,
                null,
                XPathResult.FIRST_ORDERED_NODE_TYPE,
                null
            ).singleNodeValue;
            if (buttonToRemove) {
                buttonToRemove.remove();
            }
            
            document.body.style.margin = '0';
            document.body.style.width = rect.width + 'px';
            document.body.style.height = rect.height + 'px';
        }''')
        
        await page.pdf(path=pdf_filename, print_background=True)
        await browser.close()
        
    with open(pdf_filename, 'rb') as file:
        pdf_content = file.read()
    os.remove(pdf_filename)

    return pdf_content
    


DATABASE = None
def get_database(database_name: str = "reviews.db") -> DataBase:
    global DATABASE
    if DATABASE is None:
        DATABASE = DataBase(database_name)
    return DATABASE

TASK_MANAGER = None
def get_task_manager(serpapi_key: str, model: str, openai_key: str, num_reviews: int=50, max_reviews: int=150, num_suggestion: int=5, batch_size: int=30, language: str="en", country: str="in", delay: float=1, verbosity: bool=True) -> TaskManager:
    global TASK_MANAGER
    if TASK_MANAGER is None:
        TASK_MANAGER = TaskManager(
            batch_size=batch_size,
            review_analyzer=ReviewAnalyzer(
                model=model,
                api_key=openai_key,
                verbosity=verbosity,
                data_prompt=DATA_PROMPT,
                system_prompt=SYSTEM_PROMPT,
                batch_analytics_prompt=BATCH_ANALYTICS_PROMPT
            ),
            data_processor=DataProcessor(
                delay=delay,
                country=country, 
                language=language,
                verbosity=verbosity,
                api_key=serpapi_key,
                num_reviews=num_reviews, 
                max_reviews=max_reviews,
                num_suggestion=num_suggestion, 
            )
        )
    return TASK_MANAGER