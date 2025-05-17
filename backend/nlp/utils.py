# backend/nlp/utils.py
import re
import spacy

# Load spaCy model once. Consider lazy loading or loading at app startup.
# Using a try-except block for environments where it might not be pre-downloaded.
try:
    nlp_spacy = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'...")
    spacy.cli.download("en_core_web_sm")
    nlp_spacy = spacy.load("en_core_web_sm")


def preprocess_text(text: str) -> str:
    """
    Basic text preprocessing: lowercase, remove extra whitespace.
    You can add more steps like removing punctuation if needed for specific rules,
    but spaCy often handles punctuation well.
    """
    if not text:
        return ""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with a single space
    return text

def tokenize_and_lemmatize(text: str) -> list[str]:
    """
    Tokenizes and lemmatizes text using spaCy.
    Returns a list of lemma strings.
    """
    if not text:
        return []
    doc = nlp_spacy(text)
    return [token.lemma_ for token in doc if not token.is_punct and not token.is_space]

def get_spacy_doc(text: str) -> spacy.tokens.Doc:
    """
    Returns a spaCy Doc object for more advanced processing.
    """
    if not text:
        return nlp_spacy("") # Return empty doc for empty string
    return nlp_spacy(text)

# --- Keywords for simple matching ---
# These would ideally be managed more dynamically or come from your menu data

GREETING_KEYWORDS = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening"]
ORDER_KEYWORDS = ["order", "get", "want", "like", "have", "buy", "need"]
MENU_KEYWORDS = ["menu", "see what you have", "options", "dishes", "food list"]
STATUS_KEYWORDS = ["status", "track", "where is my", "update on my"]
BILL_KEYWORDS = ["bill", "check", "pay", "receipt"]
CANCEL_KEYWORDS = ["cancel", "stop", "don't want", "change my mind"]
CUSTOMIZE_KEYWORDS = ["add", "remove", "extra", "no", "without", "with", "less", "more", "make it"]
AFFIRMATIVE_KEYWORDS = ["yes", "yeah", "yep", "ok", "okay", "sure", "alright", "confirm"]
NEGATIVE_KEYWORDS = ["no", "nope", "nah", "don't", "do not", "cancel that"]

# You might have categories of food items for broader matching
FOOD_CATEGORIES_KEYWORDS = {
    "pizza": ["pizza", "pizzas"],
    "burger": ["burger", "burgers", "cheeseburger", "hamburger"],
    "pasta": ["pasta", "spaghetti", "lasagna", "fettuccine"],
    "salad": ["salad", "salads"],
    "drink": ["drink", "soda", "coke", "pepsi", "water", "juice"],
    "dessert": ["dessert", "cake", "ice cream", "brownie"],
}

# Example generic ingredients (expand significantly or load from DB/menu)
INGREDIENT_KEYWORDS_GENERIC = [
    "cheese", "onion", "tomato", "lettuce", "pickle", "mushroom", "pepperoni",
    "chicken", "beef", "bacon", "jalapeno", "olive", "sauce", "dressing"
]

QUANTITY_WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "a": 1, "an": 1,
    "single": 1, "double": 2, "triple": 3,
}