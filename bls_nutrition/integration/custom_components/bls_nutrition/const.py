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
SIGNAL_RESULT_UPDATED = f"{DOMAIN}_result_updated"

# Stable entity IDs for dashboard (via suggested_object_id)
ENTITY_FOOD_COUNT = "bls_nutrition_food_count"
ENTITY_BLS_VERSION = "bls_nutrition_bls_version"
ENTITY_LAST_FOOD = "bls_nutrition_last_food"
ENTITY_G_KH = "bls_nutrition_g_kh"
ENTITY_BE = "bls_nutrition_be"
ENTITY_KE = "bls_nutrition_ke"
ENTITY_FPE = "bls_nutrition_fpe"
ENTITY_SEARCH_HITS = "bls_nutrition_search_hits"
ENTITY_ENERGY = "bls_nutrition_energy_kcal"
ENTITY_PROTEIN = "bls_nutrition_protein"
ENTITY_FAT = "bls_nutrition_fat"
ENTITY_CARBS = "bls_nutrition_carbs"
