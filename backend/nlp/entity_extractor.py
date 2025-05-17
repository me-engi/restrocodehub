# backend/nlp/entity_extractor.py
import re
from .utils import (
    preprocess_text, get_spacy_doc,
    FOOD_CATEGORIES_KEYWORDS, INGREDIENT_KEYWORDS_GENERIC, QUANTITY_WORDS
)
from spacy.matcher import Matcher, PhraseMatcher # For more advanced matching

# This should be dynamically loaded from your menu database (menu.models.MenuItem)
# For now, a placeholder. Structure: {'lower_case_item_name': 'Canonical Item Name'}
# Or a list of spaCy Doc objects for PhraseMatcher
DYNAMIC_MENU_ITEMS = {} # Populate this from your database (e.g., at app startup or on demand)
DYNAMIC_INGREDIENTS = {} # Populate this too

def load_menu_data_for_nlp(menu_items_from_db, ingredients_from_db):
    """
    Call this function when your app starts or when menu changes significantly
    to populate DYNAMIC_MENU_ITEMS and DYNAMIC_INGREDIENTS.
    menu_items_from_db: list of strings (item names)
    ingredients_from_db: list of strings (ingredient names)
    """
    global DYNAMIC_MENU_ITEMS, DYNAMIC_INGREDIENTS, nlp_spacy # Ensure nlp_spacy is from utils
    from .utils import nlp_spacy as spacy_nlp_instance # Import from utils
    
    DYNAMIC_MENU_ITEMS.clear()
    for item_name in menu_items_from_db:
        DYNAMIC_MENU_ITEMS[item_name.lower()] = item_name
        # For phrase matcher, pre-process them into spaCy docs
        # DYNAMIC_MENU_ITEMS_PATTERNS.append(spacy_nlp_instance(item_name))

    DYNAMIC_INGREDIENTS.clear()
    for ing_name in ingredients_from_db:
        DYNAMIC_INGREDIENTS[ing_name.lower()] = ing_name
        # DYNAMIC_INGREDIENTS_PATTERNS.append(spacy_nlp_instance(ing_name))

    # Initialize PhraseMatchers (do this once after loading data)
    # global phrase_matcher_menu, phrase_matcher_ingredients
    # phrase_matcher_menu = PhraseMatcher(spacy_nlp_instance.vocab, attr='LOWER')
    # phrase_matcher_ingredients = PhraseMatcher(spacy_nlp_instance.vocab, attr='LOWER')
    # if DYNAMIC_MENU_ITEMS_PATTERNS:
    #    phrase_matcher_menu.add("MENU_ITEM", DYNAMIC_MENU_ITEMS_PATTERNS)
    # if DYNAMIC_INGREDIENTS_PATTERNS:
    #    phrase_matcher_ingredients.add("INGREDIENT", DYNAMIC_INGREDIENTS_PATTERNS)


def extract_entities(query: str, intent: str, menu_items_master_list: list = None, ingredients_master_list: list = None) -> dict:
    """
    Extracts entities from a user query based on the detected intent.
    menu_items_master_list: A list of canonical menu item names from your DB.
    ingredients_master_list: A list of canonical ingredient names from your DB.
    """
    processed_query = preprocess_text(query)
    doc = get_spacy_doc(processed_query) # Use spaCy doc for linguistic features
    entities = {}

    # --- Populate dynamic lists if provided (better than global for testing/flexibility) ---
    # This simulates loading DYNAMIC_MENU_ITEMS and DYNAMIC_INGREDIENTS
    # In a real app, these would be populated from the DB once, or passed in.
    
    # For robust matching, use PhraseMatcher with actual menu/ingredient names
    from .utils import nlp_spacy # Get the loaded spaCy instance
    phrase_matcher_menu = PhraseMatcher(nlp_spacy.vocab, attr='LOWER')
    if menu_items_master_list:
        menu_patterns = [nlp_spacy.make_doc(name) for name in menu_items_master_list]
        if menu_patterns:
            phrase_matcher_menu.add("MENU_ITEM", menu_patterns)

    phrase_matcher_ingredients = PhraseMatcher(nlp_spacy.vocab, attr='LOWER')
    if ingredients_master_list:
        ingredient_patterns = [nlp_spacy.make_doc(name) for name in ingredients_master_list]
        if ingredient_patterns:
            phrase_matcher_ingredients.add("INGREDIENT", ingredient_patterns)


    # --- Entity Extraction Logic based on Intent ---

    if intent in ["orderFood", "searchFood", "customizeItem", "addToCart"]:
        # 1. Extract Food Items using PhraseMatcher (more robust)
        food_items_found = []
        if menu_items_master_list:
            matches = phrase_matcher_menu(doc)
            for match_id, start, end in matches:
                span = doc[start:end]
                food_items_found.append(span.text) # Use span.text to get the exact matched phrase
        
        if food_items_found:
            entities["foodItems"] = list(set(food_items_found)) # list of canonical names

        # 2. Extract Quantities (simple approach)
        # Look for numbers before or after food items or using quantity words
        quantities = []
        for token in doc:
            if token.like_num: # "2", "two" (spaCy handles this)
                quantities.append(int(token.orth_) if token.orth_.isdigit() else QUANTITY_WORDS.get(token.lower_, 1))
            elif token.lower_ in QUANTITY_WORDS:
                 quantities.append(QUANTITY_WORDS[token.lower_])
        if quantities:
            entities["quantities"] = quantities # This is a list, needs association with foodItems

        # TODO: Associate quantities with specific food items if multiple items are mentioned.
        # This requires more complex parsing (e.g., "2 pizzas and 1 coke")

    if intent == "customizeItem" or (intent == "orderFood" and "foodItems" in entities):
        # Extract Ingredients to add/remove (using PhraseMatcher)
        added_ingredients = []
        removed_ingredients = []
        
        if ingredients_master_list:
            ingredient_matches = phrase_matcher_ingredients(doc)
            # Check context around ingredient matches (e.g., "add cheese", "no onions", "without pickles")
            for match_id, start, end in ingredient_matches:
                ingredient_span = doc[start:end]
                ingredient_name = ingredient_span.text # Canonical name

                # Check preceding tokens for "add", "extra", "with"
                # Check preceding tokens for "remove", "no", "without", "hold"
                # This is a simplified example, dependency parsing with spaCy would be more robust
                
                # Example: "add extra cheese" or "burger with cheese"
                # Example: "no onions" or "burger without onions"
                
                # Simple check: iterate tokens and look for keywords around the entity
                action = None
                for i in range(max(0, ingredient_span.start - 3), ingredient_span.start): # Look 3 tokens before
                    token_text = doc[i].lemma_.lower()
                    if token_text in ["add", "extra", "with"]:
                        action = "add"
                        break
                    if token_text in ["remove", "no", "without", "hold", "less"]:
                        action = "remove"
                        break
                
                if action == "add":
                    added_ingredients.append(ingredient_name)
                elif action == "remove":
                    removed_ingredients.append(ingredient_name)
                else:
                    # If no clear action keyword, but intent is customize, what to do?
                    # It might be an implicit add if context implies it (e.g. "burger, cheese, lettuce")
                    # For now, only explicit adds/removes
                    pass


        if added_ingredients:
            entities["addedIngredients"] = list(set(added_ingredients))
        if removed_ingredients:
            entities["removedIngredients"] = list(set(removed_ingredients))

    if intent == "provideInfo":
        # Example: Extract table number if AI asked for it
        # This would typically be driven by dialog_context
        # For now, a simple number extraction if numbers are present
        table_numbers = [token.text for token in doc if token.like_num and token.pos_ == "NUM"]
        if table_numbers:
            entities["tableNumber"] = table_numbers[0] # Assume first number is table

        # Address extraction is very complex. For now, we'd assume the whole query is the address
        # if dialog_context.get("expecting") == "address":
        # entities["deliveryAddress"] = query # The raw query

    # Add more entity extraction logic for other intents as needed
    # e.g., for getOrderStatus, try to extract an order ID or token number

    return entities