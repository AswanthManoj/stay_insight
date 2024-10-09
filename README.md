## Installation Steps

1. Install poetry: `pip install poetry`
2. Install dependencies: `poetry install`
3. Since we are using playwright do `playwright install`


## Prerequisites

Create a `.env` file and fill with the required api key informations like for example:

```env
OPENAI_MODEL=gpt-4o-2024-08-06
SERPAPI_KEY=<serpapi-key>
OPENAI_API_KEY=<openai-api-key>
```


## Run the app

1. `poetry run python app.py`


## Extra configurations

You can configure the language model used, number of reviews taken for instant analysis and for batching the full analysis within `config.py` file as well as through the `.env` file.

Here are the variables needed to configure if done through `.env`:

- **PORT**: Port to bind the server to
- **HOST**: Host to bind the server to
- **DELAY**: Delay in seconds between paginations through SerpApi reviews to avoid rate limiting
- **RELOAD**: Auto reload on file changes
- **COUNTRY**: Country for searching places based of for autocomplete
- **BATCH_SIZE**: Batch size for doing full analysis
- **NUM_REVIEWS**: Number of reviews to analyze used in instant analysis
- **SERPAPI_KEY**: SerpApi API key
- **OPENAI_MODEL**: OpenAI model to use for analysis
- **NUM_SUGGESTION**: Number of autocomplete suggestions to return
- **OPENAI_API_KEY**: OpenAI API key