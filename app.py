import os, uuid, asyncio
from typing import Optional
from fastapi import FastAPI
from dotenv import load_dotenv
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi import Request, HTTPException, BackgroundTasks
from review_ai.analysis import get_data_processor, get_analyzer
from review_ai.utils import SuggestionRequest, SuggestionResult


load_dotenv()


app = FastAPI()
data_processor = get_data_processor(
    delay=1,
    country="uk",
    language="en",
    num_reviews=10,
    num_suggestion=5,
    api_key=os.getenv("SERPAPI_KEY"),
)
analyzer = get_analyzer(
    model=os.getenv("OPENAI_MODEL"),
    api_key=os.getenv("OPENAI_API_KEY")
)
templates = Jinja2Templates(directory="review_ai/templates")
app.mount("/static", StaticFiles(directory="review_ai/static"), name="static")


analysis_results = {}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/analyze", response_class=HTMLResponse)
async def analyze(request: Request):
    return templates.TemplateResponse("analyze.html", {"request": request})

@app.get("/retrieve", response_class=HTMLResponse)
async def retrieve(request: Request):
    return templates.TemplateResponse("retrieve.html", {"request": request})

@app.post("/api/suggestions", response_model=SuggestionResult)
async def get_suggestions(request: SuggestionRequest):
    try:
        print(request)
        suggestion = await data_processor.get_suggestions(
            query=request.value,
            # filter="place",
            latitude=request.latitude if request.latitude is not None else 9.9185,
            longitude=request.longitude if request.longitude is not None else 76.2558,
        )
        return JSONResponse(content=suggestion.model_dump())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_restaurant(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    data_id = data.get("dataId")
    analysis_type = data.get("analysisType")

    if analysis_type == "instant":
        try:
            review_result = await data_processor.get_reviews(data_id=data_id) 
            if review_result.reviews == []:
                raise HTTPException(status_code=404, detail="Data not found")
            review_result = await analyzer.generate_analysis(review_result)
            review_result.reviews = data_processor.sort_reviews_by_date(review_result.reviews, reverse=True)
            return JSONResponse(content=review_result.model_dump())
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    elif analysis_type == "full":
        token = str(uuid.uuid4())
        background_tasks.add_task(perform_full_analysis, data_id, token)
        return JSONResponse(content={"token": token})
    else:
        raise HTTPException(status_code=400, detail="Invalid analysis type")

@app.get("/api/analysis/{token}")
async def get_analysis_result(token: str):
    if token not in analysis_results:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    result = analysis_results[token]
    if result["status"] == "completed":
        return JSONResponse(content=result["data"])
    elif result["status"] == "in_progress":
        return JSONResponse(content={"status": "in_progress"})
    else:
        raise HTTPException(status_code=500, detail="Analysis failed")

async def perform_full_analysis(data_id: str, token: str):
    print(data_id, token)
    analysis_results[token] = {"status": "in_progress"}
    # Implement your full analysis logic here
    # When completed, update the result:
    # analysis_results[token] = {"status": "completed", "data": analysis_data}
    pass


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)