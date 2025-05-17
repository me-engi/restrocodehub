# backend/nlp/intent_classifier.py
from .utils import (
    preprocess_text, tokenize_and_lemmatize,
    GREETING_KEYWORDS, ORDER_KEYWORDS, MENU_KEYWORDS,
    STATUS_KEYWORDS, BILL_KEYWORDS, CANCEL_KEYWORDS,
    CUSTOMIZE_KEYWORDS, AFFIRMATIVE_KEYWORDS, NEGATIVE_KEYWORDS
)

# Define your intents
INTENT_GREET = "greet"
INTENT_ORDER_FOOD = "orderFood" # Could be combined with searchFood initially
INTENT_SEARCH_FOOD = "searchFood"
INTENT_VIEW_MENU = "viewMenu"
INTENT_CUSTOMIZE_ITEM = "customizeItem"
INTENT_ADD_TO_CART = "addToCart" # Often implied by orderFood/searchFood + item
INTENT_VIEW_CART = "viewCart"
INTENT_CHECKOUT = "checkout"
INTENT_GET_ORDER_STATUS = "getOrderStatus"
INTENT_REQUEST_BILL = "requestBill"
INTENT_CANCEL_ORDER = "cancelOrder" # Or cancel item
INTENT_AFFIRMATIVE = "affirmative" # User says yes
INTENT_NEGATIVE = "negative"     # User says no
INTENT_UNKNOWN = "unknown"
INTENT_PROVIDE_INFO = "provideInfo" # e.g., user gives table number or address

# More specific intents can be added later, e.g., askRestaurantHours, askDeliveryTime

def classify_intent(query: str, previous_intent: str = None, dialog_context: dict = None) -> str:
    """
    Classifies the intent of a user query.
    Can use previous_intent and dialog_context for more complex dialog management later.
    """
    processed_query = preprocess_text(query)
    tokens = set(tokenize_and_lemmatize(processed_query)) # Use set for faster "in" checks

    # 1. Check for simple, direct intents first
    if any(keyword in tokens for keyword in GREETING_KEYWORDS):
        return INTENT_GREET

    if any(keyword in tokens for keyword in AFFIRMATIVE_KEYWORDS) and \
       not any(keyword in tokens for keyword in ORDER_KEYWORDS + MENU_KEYWORDS): # Avoid "yes i want pizza" being just affirmative
        # Context is important here: "yes" to what?
        if previous_intent == INTENT_ADD_TO_CART: # e.g., AI asked "Add to cart?"
             return INTENT_AFFIRMATIVE # Or directly INTENT_CONFIRM_ADD_TO_CART
        return INTENT_AFFIRMATIVE


    if any(keyword in tokens for keyword in NEGATIVE_KEYWORDS) and \
       not any(keyword in tokens for keyword in ORDER_KEYWORDS + MENU_KEYWORDS):
        # Context is important: "no" to what?
        if previous_intent == INTENT_ADD_TO_CART:
            return INTENT_NEGATIVE # Or directly INTENT_REJECT_ADD_TO_CART
        return INTENT_NEGATIVE

    # More specific intents (order matters - more specific first)
    if any(keyword in tokens for keyword in STATUS_KEYWORDS) and "order" in tokens:
        return INTENT_GET_ORDER_STATUS

    if any(keyword in tokens for keyword in BILL_KEYWORDS) or "check please" in processed_query:
        return INTENT_REQUEST_BILL

    if any(keyword in tokens for keyword in CANCEL_KEYWORDS) and ("order" in tokens or previous_intent in [INTENT_ORDER_FOOD, INTENT_ADD_TO_CART]):
        return INTENT_CANCEL_ORDER

    if any(keyword in tokens for keyword in MENU_KEYWORDS):
        return INTENT_VIEW_MENU

    if any(keyword in tokens for keyword in CUSTOMIZE_KEYWORDS):
        # This might also be part of an orderFood intent if entities are extracted well.
        # If it's a follow-up, it's more clearly customizeItem.
        if previous_intent in [INTENT_ORDER_FOOD, INTENT_SEARCH_FOOD, INTENT_CUSTOMIZE_ITEM] or dialog_context.get("currentItemToCustomize"):
            return INTENT_CUSTOMIZE_ITEM
        # Otherwise, it might be a general query about customization, which could be searchFood too.

    if any(keyword in tokens for keyword in ORDER_KEYWORDS):
        return INTENT_ORDER_FOOD # Or INTENT_SEARCH_FOOD, entity extraction will clarify

    # Fallback to search if common food words are present but no strong order verb
    # This part needs actual menu item keywords or categories for better accuracy
    # For now, just a placeholder
    if "pizza" in tokens or "burger" in tokens or "pasta" in tokens or "salad" in tokens:
        if not previous_intent or previous_intent == INTENT_GREET: # Avoid reclassifying a follow-up
            return INTENT_SEARCH_FOOD


    # Check for providing information based on context (e.g., after AI asks for table number)
    if dialog_context and dialog_context.get("expecting") == "table_number":
        if any(token.isdigit() for token in query.split()): # Simple check for numbers
            return INTENT_PROVIDE_INFO
    if dialog_context and dialog_context.get("expecting") == "address":
        # More complex address parsing needed, for now, assume any text is the address
        if len(query.split()) > 2: # Very basic check
             return INTENT_PROVIDE_INFO


    # Default if no other intent matches
    if previous_intent and previous_intent != INTENT_GREET:
        # If there was a previous food-related intent, assume a follow-up might still be related
        # This is tricky and needs better context management
        pass

    return INTENT_UNKNOWN