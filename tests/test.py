import os, asyncio
from review_ai.analysis import get_data_processor


processor = get_data_processor(
    delay=1,
    country="uk",
    language="en",
    num_reviews=25,
    num_suggestion=5,
    api_key=os.getenv("SERPAPI_KEY"),
)


#######################
# Test Suggestion API #
#######################
suggestion = asyncio.run(processor.get_suggestions(
    query="Sea Shore",
    latitude=9.9185,
    longitude=76.2558,
))
print("""
***********************
* Test Suggestion API *
***********************
""")
print(suggestion)


###################
# Test Review API #
###################
# reviews = asyncio.run(processor.get_reviews(
#     sort_by="qualityScore",
#     data_id="0x89c259af336b3341:0xa4969e07ce3108de"
# ))
# print("""
# *******************
# * Test Review API *
# *******************
# """)
# print(reviews)

