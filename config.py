import os
from pprint import pprint
from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


class Settings(BaseModel):
    port:           int                       # port to bind the server to
    host:           str                       # host to bind the server to
    delay:          float = 0.5               # Delay in seconds between paginations through SerpApi reviews to avoid rate limiting
    reload:         bool                      # Auto reload on file changes
    country:        str = "uk"                # Country for searching places based of for autocomplete
    batch_size:     int = 30                  # Batch size for doing full analysis
    num_reviews:    int = 40                  # Number of reviews to analyze used in instant analysis
    max_reviews:    int = 150                 # Maximum number of reviews to consider for full analysis
    serpapi_key:    str                       # SerpApi API key
    openai_model:   str = "gpt-4o-mini" # OpenAI model to use for analysis
    num_suggestion: int = 5                   # Number of autocomplete suggestions to return
    openai_api_key: str                       # OpenAI API key
    
    def __init__(self, **data):
        if isinstance(data.get("port"), str):
            data["port"] = int(data["port"])
            data["delay"] = float(data["delay"])
            data["batch_size"] = int(data["batch_size"])
            data["num_reviews"] = int(data["num_reviews"])
            data["max_reviews"] = int(data["max_reviews"])
            data["num_suggestion"] = int(data["num_suggestion"])
        super().__init__(**data)
        
    
    
SETTINGS = None
def get_settings() -> Settings:
    global SETTINGS
    if SETTINGS is None:
        SETTINGS = Settings(
            port =           os.getenv("PORT", 8000),
            host =           os.getenv("HOST", "0.0.0.0"),
            delay =          os.getenv("DELAY", 0.5),
            reload =         os.getenv("RELOAD", False),
            country =        os.getenv("COUNTRY", "uk"),
            batch_size =     os.getenv("BATCH_SIZE", 25),
            num_reviews =    os.getenv("NUM_REVIEWS", 30),
            max_reviews =    os.getenv("MAX_REVIEWS", 150),
            serpapi_key =    os.getenv("SERPAPI_KEY"),
            openai_model =   os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            num_suggestion = os.getenv("NUM_SUGGESTION", 5),
            openai_api_key = os.getenv("OPENAI_API_KEY"),
            
        )
    return SETTINGS

get_settings()

pprint(SETTINGS.model_dump())