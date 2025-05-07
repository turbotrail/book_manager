

from langchain.prompts import PromptTemplate

SUMMARY_PROMPT_TEMPLATE = PromptTemplate.from_template(
    "You are an expert summarizer. Summarize the following book content clearly and concisely, "
    "preserving the main ideas, plot, or concepts. Highlight the core message and important takeaways.\n\n{text}"
)

RECOMMENDATION_PROMPT = PromptTemplate.from_template(
    "You are an intelligent and friendly book recommender. A user has the following preferences:\n"
    "- Genre: {genre}\n"
    "- Favorite Author: {author}\n"
    "- Preferred Year Range: {min_year} to {max_year}\n\n"
    "Based on these preferences, you matched the following books from the library database: {book_titles}.\n\n"
    "Write a friendly and insightful one-line recommendation summary that encourages the user to explore these books. "
    "Focus on variety, relevance, and appeal."
)