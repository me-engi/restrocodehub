# backend/recommendations/rule_based_recommender.py

from typing import List, Dict, Any, Optional, Set

# --- Rule 1: Suggest Alternatives for Out-of-Stock Items ---
def suggest_alternatives_for_out_of_stock(
    out_of_stock_item_id: Any,
    menu_items_dict: Dict[Any, Dict[str, Any]],
    num_suggestions: int = 3
) -> List[Dict[str, Any]]:
    """
    Suggests alternative items if a selected item is out of stock.
    Prioritizes items from the same category, then similar tags or ingredients.

    Args:
        out_of_stock_item_id: The ID of the item that is out of stock.
        menu_items_dict: Dict of all menu items {item_id: item_details}.
                         item_details should include 'id', 'name', 'category', 'tags' (list),
                         'ingredients' (list of ingredient_ids), 'is_available' (bool).
        num_suggestions: Maximum number of alternatives to suggest.

    Returns:
        A list of suggested item detail dictionaries.
    """
    suggestions = []
    out_of_stock_item = menu_items_dict.get(out_of_stock_item_id)

    if not out_of_stock_item or out_of_stock_item.get('is_available', True):
        return [] # Item is available or not found, no need for alternatives

    # 1. Prioritize same category
    for item_id, item_details in menu_items_dict.items():
        if len(suggestions) >= num_suggestions:
            break
        if item_id != out_of_stock_item_id and \
           item_details.get('category') == out_of_stock_item.get('category') and \
           item_details.get('is_available', False):
            suggestions.append(item_details)

    # 2. If not enough, look for items with overlapping tags (if tags exist)
    if len(suggestions) < num_suggestions and 'tags' in out_of_stock_item:
        oos_tags = set(out_of_stock_item.get('tags', []))
        if oos_tags:
            for item_id, item_details in menu_items_dict.items():
                if len(suggestions) >= num_suggestions:
                    break
                if item_id != out_of_stock_item_id and \
                   item_details.get('is_available', False) and \
                   item_id not in [s['id'] for s in suggestions]: # Avoid duplicates
                    item_tags = set(item_details.get('tags', []))
                    if oos_tags.intersection(item_tags): # Check for any common tag
                        suggestions.append(item_details)

    # 3. If still not enough, look for items with overlapping key ingredients (simplistic)
    # This requires more complex ingredient similarity logic for better results.
    # For now, just a placeholder idea.
    # if len(suggestions) < num_suggestions and 'ingredients' in out_of_stock_item:
    #     oos_ingredients = set(out_of_stock_item.get('ingredients', []))
    #     # ... logic to find items with common ingredients ...

    return suggestions[:num_suggestions]


# --- Rule 2: Suggest Add-ons or Complementary Items ---
def suggest_add_ons(
    current_cart_item_ids: List[Any],
    menu_items_dict: Dict[Any, Dict[str, Any]],
    complementary_rules: Dict[Any, List[Any]], # {item_id_A: [complement_id_B, complement_id_C]}
    num_suggestions: int = 3
) -> List[Dict[str, Any]]:
    """
    Suggests add-ons or complementary items based on what's already in the cart.

    Args:
        current_cart_item_ids: List of item IDs currently in the user's cart.
        menu_items_dict: Dict of all menu items.
        complementary_rules: Predefined rules, e.g., {'burger_id': ['fries_id', 'coke_id']}.
        num_suggestions: Maximum number of suggestions.

    Returns:
        A list of suggested item detail dictionaries.
    """
    if not current_cart_item_ids:
        return []

    potential_suggestions: Set[Any] = set()
    for cart_item_id in current_cart_item_ids:
        if cart_item_id in complementary_rules:
            for suggested_id in complementary_rules[cart_item_id]:
                potential_suggestions.add(suggested_id)

    # Filter out items already in cart and unavailable items
    final_suggestions = []
    for item_id in list(potential_suggestions): # Iterate over a copy
        if item_id not in current_cart_item_ids and \
           menu_items_dict.get(item_id, {}).get('is_available', False):
            final_suggestions.append(menu_items_dict[item_id])
            if len(final_suggestions) >= num_suggestions:
                break
                
    return final_suggestions


# --- Rule 3: "Popular Items" or "Trending Now" ---
def suggest_popular_items(
    menu_items_dict: Dict[Any, Dict[str, Any]],
    popularity_scores: Dict[Any, float], # {item_id: score/order_count}
    num_suggestions: int = 5,
    category_filter: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Suggests popular items, optionally filtered by category.

    Args:
        menu_items_dict: Dict of all menu items.
        popularity_scores: Dict where keys are item_ids and values are their popularity scores
                           (e.g., number of times ordered in the last week).
        num_suggestions: Maximum number of suggestions.
        category_filter: Optional category name to filter popular items.

    Returns:
        A list of suggested item detail dictionaries.
    """
    if not popularity_scores:
        return []

    # Sort items by popularity score in descending order
    sorted_popular_ids = sorted(popularity_scores.keys(), key=lambda k: popularity_scores[k], reverse=True)

    suggestions = []
    for item_id in sorted_popular_ids:
        if len(suggestions) >= num_suggestions:
            break
        item_details = menu_items_dict.get(item_id)
        if item_details and item_details.get('is_available', False):
            if category_filter and item_details.get('category') != category_filter:
                continue
            suggestions.append(item_details)
            
    return suggestions


# --- Rule 4: "You Might Also Like" (based on item similarity - simple version) ---
def suggest_similar_items(
    target_item_id: Any,
    menu_items_dict: Dict[Any, Dict[str, Any]],
    num_suggestions: int = 3
) -> List[Dict[str, Any]]:
    """
    Suggests items similar to a target item (e.g., when viewing an item's details).
    Similarity based on category and then tags.

    Args:
        target_item_id: The ID of the item for which to find similar items.
        menu_items_dict: Dict of all menu items.
        num_suggestions: Maximum number of suggestions.

    Returns:
        A list of suggested item detail dictionaries.
    """
    suggestions = []
    target_item = menu_items_dict.get(target_item_id)

    if not target_item:
        return []

    # 1. Same category (excluding self)
    for item_id, item_details in menu_items_dict.items():
        if len(suggestions) >= num_suggestions:
            break
        if item_id != target_item_id and \
           item_details.get('category') == target_item.get('category') and \
           item_details.get('is_available', False):
            suggestions.append(item_details)

    # 2. If not enough, items with overlapping tags (excluding self and already suggested)
    if len(suggestions) < num_suggestions and 'tags' in target_item:
        target_tags = set(target_item.get('tags', []))
        if target_tags:
            current_suggestion_ids = {s['id'] for s in suggestions}
            for item_id, item_details in menu_items_dict.items():
                if len(suggestions) >= num_suggestions:
                    break
                if item_id != target_item_id and \
                   item_id not in current_suggestion_ids and \
                   item_details.get('is_available', False):
                    item_tags = set(item_details.get('tags', []))
                    # Prioritize higher overlap if possible, or just any overlap
                    if target_tags.intersection(item_tags):
                        suggestions.append(item_details)
                        current_suggestion_ids.add(item_id) # Add to avoid re-suggesting

    return suggestions[:num_suggestions]


# --- Rule 5: Based on User's Past Order History (Simple Reorder or Frequently Ordered) ---
def suggest_from_past_orders(
    user_order_history: List[List[Any]], # List of orders, where each order is a list of item_ids
    menu_items_dict: Dict[Any, Dict[str, Any]],
    num_suggestions: int = 5,
    strategy: str = "frequent" # or "recent"
) -> List[Dict[str, Any]]:
    """
    Suggests items based on a user's past order history.

    Args:
        user_order_history: A list of lists, e.g., [[item1_id, item2_id], [item1_id, item3_id]].
        menu_items_dict: Dict of all menu items.
        num_suggestions: Max suggestions.
        strategy: "frequent" (most ordered items) or "recent" (items from most recent orders).

    Returns:
        A list of suggested item detail dictionaries.
    """
    if not user_order_history:
        return []

    candidate_item_ids = []
    if strategy == "frequent":
        from collections import Counter
        all_ordered_items = [item_id for order in user_order_history for item_id in order]
        item_counts = Counter(all_ordered_items)
        # Get items sorted by frequency
        candidate_item_ids = [item_id for item_id, count in item_counts.most_common()]
    elif strategy == "recent":
        # Get unique items from recent orders, maintaining some order
        seen_ids = set()
        for order in reversed(user_order_history): # Start from most recent order
            for item_id in order:
                if item_id not in seen_ids:
                    candidate_item_ids.append(item_id)
                    seen_ids.add(item_id)
    else: # Default to frequent
        from collections import Counter
        all_ordered_items = [item_id for order in user_order_history for item_id in order]
        item_counts = Counter(all_ordered_items)
        candidate_item_ids = [item_id for item_id, count in item_counts.most_common()]


    suggestions = []
    for item_id in candidate_item_ids:
        if len(suggestions) >= num_suggestions:
            break
        item_details = menu_items_dict.get(item_id)
        if item_details and item_details.get('is_available', False):
            suggestions.append(item_details)
            
    return suggestions

# You could add more rules:
# - Special offers / promotions
# - New items on the menu
# - Time-based recommendations (breakfast items in the morning)
# - Weather-based recommendations (hot drinks on a cold day)