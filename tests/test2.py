from typing import List
from datetime import datetime
from review_ai.utils import Review

def sort_reviews_by_date(reviews: List[Review]):
    def parse_date(date_string):
        return datetime.strptime(date_string, "%B %d, %Y at %I:%M %p UTC")
    
    return sorted(reviews, key=lambda review: parse_date(review.date), reverse=True)

sample_reviews = [
    Review(
        user="Alice",
        date="August 03, 2024 at 03:53 PM UTC",
        rating=4.5,
        review_text="Great product!"
    ),
    Review(
        user="Bob",
        date="January 13, 2024 at 06:29 AM UTC",
        rating=3.0,
        review_text="It's okay, but could be better."
    ),
    Review(
        user="Charlie",
        date="August 12, 2024 at 01:50 PM UTC",
        rating=5.0,
        review_text="Absolutely love it!"
    ),
    Review(
        user="Diana",
        date="March 25, 2024 at 11:15 AM UTC",
        rating=4.0,
        review_text="Very satisfying purchase."
    )
]

# Use the sorting function
sorted_reviews = sort_reviews_by_date(sample_reviews)

# Print the sorted reviews
for review in sorted_reviews:
    print(f"{review.user}: {review.date}")
