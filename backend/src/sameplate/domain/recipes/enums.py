from enum import Enum


class SelectionModeEnum(str, Enum):
    PANTRY = "pantry"
    EXPLORE = "explore"


class DifficultyEnum(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class DishTypeEnum(str, Enum):
    MAIN = "main"
    SALAD = "salad"
    SOUP = "soup"
    DESSERT = "dessert"
    SNACK = "snack"


class UnitEnum(str, Enum):
    GRAM = "g"
    MILLILITER = "ml"
    PIECE = "piece"
    TEASPOON = "tsp"
    TABLESPOON = "tbsp"
