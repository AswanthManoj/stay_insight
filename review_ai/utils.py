from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
    
    
    
############################
# PYDANTIC MODELS ANALYSIS #
############################
class OverallSentiment(BaseModel):
    average_score:       float = Field(..., description="Average sentiment score on a scale of 1-5 with 1 decimal point precision. This score represents the overall guest satisfaction, where 1 is extremely negative and 5 is extremely positive.")
    positive_percentage: float = Field(..., description="Percentage of positive reviews with 1 decimal point precision. Positive reviews express satisfaction or recommendation.")
    neutral_percentage:  float = Field(..., description="Percentage of neutral reviews with 1 decimal point precision. Neutral reviews express neither strong satisfaction nor dissatisfaction.")
    negative_percentage: float = Field(..., description="Percentage of negative reviews with 1 decimal point precision. Negative reviews express dissatisfaction or advise against staying at the hotel.")

class Accommodation(BaseModel):
    room_quality:      List[str] = Field(..., description="Comments on room quality, including cleanliness, comfort, amenities, and maintenance.")
    common_praises:    List[str] = Field(..., description="Common positive comments about accommodation. Include themes like room size, bed comfort, views, or in-room facilities.")
    common_criticisms: List[str] = Field(..., description="Common negative comments about accommodation. Include issues with cleanliness, noise, maintenance, or lack of amenities.")
    suggestions:       List[str] = Field(..., description="Actionable suggestions for improving accommodation quality based on guest feedback.")

class Service(BaseModel):
    strengths:   Optional[List[str]] = Field(..., description="Positive aspects of service mentioned in reviews, such as staff friendliness, efficiency of check-in/out, or helpfulness with guest requests.")
    weaknesses:  Optional[List[str]] = Field(..., description="Negative aspects of service mentioned in reviews, such as slow response times, unfriendly staff, or issues with reservations.")
    suggestions: Optional[List[str]] = Field(..., description="Detailed actionable suggestions for improving service quality and guest experience.")

class Amenities(BaseModel):
    praised_features:    List[str] = Field(..., description="Hotel features or amenities frequently praised in reviews (e.g., pool, gym, spa, restaurants).")
    criticized_features: List[str] = Field(..., description="Hotel features or amenities frequently criticized or found lacking in reviews.")
    suggestions:         List[str] = Field(..., description="Suggestions for improving or adding amenities based on guest feedback.")

class FoodAndDining(BaseModel):
    restaurant_quality: str = Field(..., description="Overall perception of the hotel's dining options, including quality, variety, and value.")
    breakfast_feedback: str = Field(..., description="Specific feedback on breakfast offerings, if provided by the hotel.")
    praised_items:      List[str] = Field(..., description="Specific food items or dining experiences frequently praised by guests.")
    criticized_items:   List[str] = Field(..., description="Specific food items or dining experiences frequently criticized by guests.")
    suggestions:        List[str] = Field(..., description="Actionable suggestions for improving food and dining experiences.")

class LocationAndAccessibility(BaseModel):
    positive_aspects: List[str] = Field(..., description="Positive comments about the hotel's location, nearby attractions, or transportation access.")
    negative_aspects: List[str] = Field(..., description="Negative comments about the location, such as noise, distance from attractions, or transportation difficulties.")
    suggestions:      List[str] = Field(..., description="Suggestions for improving guest experience related to location or providing better information/services to mitigate location-based issues.")

class ValueForMoney(BaseModel):
    perceived_value:  str = Field(..., description="Overall perception of value for money, considering room rates, amenities, and overall experience.")
    positive_factors: List[str] = Field(..., description="Aspects of the stay that guests felt provided good value.")
    negative_factors: List[str] = Field(..., description="Aspects of the stay that guests felt were overpriced or did not provide good value.")
    suggestions:      List[str] = Field(..., description="Actionable suggestions for improving value perception or justifying pricing.")

class OnlinePresence(BaseModel):
    website_feedback:      List[str] = Field(..., description="Comments about the hotel's website, booking process, or online information accuracy.")
    social_media_feedback: List[str] = Field(..., description="Feedback on the hotel's social media engagement or responsiveness to online reviews.")
    suggestions:           List[str] = Field(..., description="Actionable suggestions for improving online presence and digital guest interactions.")

class ImprovementPriority(BaseModel):
    category:         str = Field(..., description="Category of the improvement (e.g., 'Accommodation', 'Service', 'Amenities', 'Food and Dining', 'Location', 'Value for Money', 'Online Presence').")
    issue:            str = Field(..., description="Specific issue to be addressed based on the review analysis.")
    suggestion:       str = Field(..., description="Actionable suggestion for addressing the issue, providing a practical recommendation for implementation.")
    potential_impact: str = Field(..., description="Estimated impact of implementing the suggestion on guest satisfaction, revenue, or overall hotel performance.")

class HotelAnalysis(BaseModel):
    hotel_name:                 str = Field(..., description="Full, official name of the analyzed hotel.")
    summary:                    str = Field(..., description="Concise summary of the overall guest experience and key points from the analysis.")
    overall_sentiment:          OverallSentiment
    accommodation:              Accommodation
    service:                    Service
    amenities:                  Amenities
    food_and_dining:            FoodAndDining
    location_and_accessibility: LocationAndAccessibility
    value_for_money:            ValueForMoney
    online_presence:            OnlinePresence
    top_improvement_priorities: List[ImprovementPriority] = Field(..., description="Top 5 prioritized improvements based on review frequency and potential impact on guest satisfaction and business performance.")


#######################
# PYDANTIC MODELS API #
#######################
class Review(BaseModel):
    user:        str
    date:        str
    rating:      float
    review_text: str

class Suggestion(BaseModel):
    type:      str
    value:     str
    data_id:   str
    subtext:   str
    latitude:  float
    longitude: float

class AnalysisResult(BaseModel):
    type:          str
    title:         str
    status:        str
    rating:        float
    data_id:       str
    address:       str
    reviews:       List[Review] = []
    created_at:    str
    total_reviews: int
    hotel_analysis:  Optional[HotelAnalysis] = None

class AnalysisRequest(BaseModel):
    value:     str
    data_id:   str
    latitude:  float
    longitude: float

class SuggestionResult(BaseModel):
    status:      str
    created_at:  str
    suggestions: List[Suggestion] = []

class SuggestionRequest(BaseModel):
    value:     str
    latitude:  Optional[float] = None
    longitude: Optional[float] = None



##############
# EXCEPTIONS #
##############
class DataProcessorError(Exception):
    """Base exception class for DataProcessor errors."""
    pass

class APIError(DataProcessorError):
    """Raised when there's an error with the API response."""
    pass

class NoResultsError(DataProcessorError):
    """Raised when no results are found."""
    pass
