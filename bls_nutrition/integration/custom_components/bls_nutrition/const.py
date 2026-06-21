"""Constants for BLS Nährwertdatenbank integration."""

DOMAIN = "bls_nutrition"
DEFAULT_HOST = "bls_nutrition"
DEFAULT_PORT = 8090

SERVICE_SEARCH_FOOD = "search_food"
SERVICE_LOOKUP_BARCODE = "lookup_barcode"
SERVICE_CALCULATE_PORTION = "calculate_portion"
SERVICE_CALCULATE_RECIPE = "calculate_recipe"
SERVICE_SAVE_RECIPE = "save_recipe"
SERVICE_SAVE_CUSTOM_FOOD = "save_custom_food"

EVENT_SEARCH_RESULT = "bls_nutrition_search_result"
EVENT_CALCULATION_RESULT = "bls_nutrition_calculation_result"
