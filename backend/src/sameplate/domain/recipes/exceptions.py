class InvalidIngredientName(ValueError):
    """An ingredient name does not meet the catalog's naming rules."""


class IngredientNameConflict(ValueError):
    """A search name already belongs to a different ingredient."""


class InvalidSelectionPreferences(ValueError):
    """Recipe selection preferences are inconsistent with the chosen mode."""
