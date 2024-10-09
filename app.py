import config, os, json
from fastapi import FastAPI
from dotenv import load_dotenv
from config import get_settings
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request, HTTPException, BackgroundTasks
from review_ai.utils import SuggestionRequest, SuggestionResult
from review_ai.analysis import get_task_manager, download_result


# Example location to check on full review analysis (only has 30 reviews) for faster testing
"Pleasant Homes Junction, near Kangrappady, Kangarappady, Ernakulam, Kerala, India"

# Hotel with 126 reviews
"Gypsy Hotel CUSAT"


app = FastAPI()
manager = get_task_manager(
    model =          get_settings().openai_model,
    delay =          get_settings().delay,                              
    country =        get_settings().country,                                                    
    batch_size =     get_settings().batch_size, 
    openai_key =     get_settings().openai_api_key,                          
    num_reviews =    get_settings().num_reviews,  
    serpapi_key =    get_settings().serpapi_key,                          
    num_suggestion = get_settings().num_suggestion,                       
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
        print(f"query: {request.value}, lat: {request.latitude}, long: {request.longitude}")
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
    
    print(f"data_id: {data_id}, analysis_type: {analysis_type}")

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
        # with open("output.json", "w") as f:
        #     f.write(json.dumps(result, indent=4))
        # with open("output.json", "r") as f:
        #     result = json.load(f)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.get("/api/download/{token}")
async def download_analysis_result(token: str):
    """
    Download the analysis result for the given token.

    Args:
        token (str): The token of the analysis result to be downloaded.

    Returns:
        Response: A response containing the analysis result or an error message if any exceptions occur.

    Raises:
        HTTPException: If any exceptions occur during the download of the analysis result.
    """
    try:
        pdf_content = await download_result(
            token=token,
            host=get_settings().host, 
            port=get_settings().port, 
        )
        return Response(content=pdf_content, media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=analysis.pdf"})
        pass
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app", 
        host=get_settings().host, 
        port=get_settings().port, 
        reload=get_settings().reload
    )