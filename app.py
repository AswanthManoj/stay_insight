import os, uuid, asyncio
from typing import Optional
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from review_ai.analysis import get_task_manager
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request, HTTPException, BackgroundTasks
from review_ai.utils import SuggestionRequest, SuggestionResult


load_dotenv()

# Example location to check on full review analysis (only has 30 reviews) for faster testing
"Pleasant Homes Junction, near Kangrappady, Kangarappady, Ernakulam, Kerala, India"


app = FastAPI()
manager = get_task_manager(
    delay=0.5,                              # Delay in seconds between paginations through SerpApi reviews to avoid rate limiting
    country="uk",                           # Country for searching places based of for autocomplete
    language="en",                          # Language for quering for places
    batch_size=10,                          # Batch size for doing full analysis
    num_reviews=8,                          # Number of reviews to analyze used in instant analysis
    num_suggestion=5,                       # Number of autocomplete suggestions to return
    model=os.getenv("OPENAI_MODEL"),        # OpenAI model to use for analysis
    serpapi_key=os.getenv("SERPAPI_KEY"),   # SerpApi API key
    openai_key=os.getenv("OPENAI_API_KEY"), # OpenAI API key
)
templates = Jinja2Templates(directory="review_ai/templates")
app.mount("/static", StaticFiles(directory="review_ai/static"), name="static")



@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """
    Return the index.html template for the home page.

    Args:
        request (Request): The request object.
    """
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/analyze", response_class=HTMLResponse)
async def analyze(request: Request):
    """
    Return the analyze.html template for getting an analysis result.

    Args:
        request (Request): The request object.

    Returns:
        HTMLResponse: The rendered template as an HTML response.
    """
    return templates.TemplateResponse("analyze.html", {"request": request})


@app.get("/retrieve", response_class=HTMLResponse)
async def retrieve(request: Request):
    """
    Return the retrieve.html template for retrieving an analysis result.

    Args:
        request (Request): The request object.

    Returns:
        HTMLResponse: The rendered template as an HTML response.
    """
    return templates.TemplateResponse("retrieve.html", {"request": request})


@app.post("/api/suggestions", response_model=SuggestionResult)
async def autocomplete(request: SuggestionRequest):
    """
    Autocomplete a search query with location-based suggestions.

    Args:
        request (SuggestionRequest): The request object containing the search query and location.

    Returns:
        JSONResponse: A JSON response containing the autocomplete suggestions.
    """
    try:
        suggestion = await manager.autocomplete(
            query=request.value,
            latitude=request.latitude if request.latitude is not None else 9.9185,
            longitude=request.longitude if request.longitude is not None else 76.2558,
        )
        return JSONResponse(content=suggestion.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/analyze")
async def analyze_restaurant(request: Request, background_tasks: BackgroundTasks):
    """
    Analyze a restaurant based on the provided dataId and analysisType.

    Args:
        request (Request): The request object containing the dataId and analysisType.
        background_tasks (BackgroundTasks): The background task manager for running the full analysis.

    Returns:
        JSONResponse: A JSON response containing the analysis result or an error message if any exceptions occur.

    Raises:
        HTTPException: If the analysisType is not "instant" or "full", or if any exceptions occur during the analysis.
    """
    data = await request.json()
    data_id = data.get("dataId")
    analysis_type = data.get("analysisType")

    if analysis_type == "instant":
        try:
            review_result = await manager.get_instant_analysis(data_id) 
            return JSONResponse(content=review_result.model_dump())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    elif analysis_type == "full":
        try:
            token = await manager.get_full_analysis(data_id, background_tasks)
            return JSONResponse(content=token)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(status_code=400, detail="Invalid analysis type")


@app.get("/api/analysis/{token}")
async def get_analysis_result(token: str):
    """
    Retrieve the analysis result for the given token.

    Args:
        token (str): The token of the analysis result to be retrieved.

    Returns:
        JSONResponse: A JSON response containing the analysis result or an error message if any exceptions occur.

    Raises:
        HTTPException: If any exceptions occur during the retrieval of the analysis result.
    """
    try:
        result = await manager.get_analysis_result(token)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)