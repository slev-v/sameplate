class UnknownIngredientsError(Exception):
    def __init__(self, unknown_ingredient_ids: frozenset[int]) -> None:
        self.unknown_ingredient_ids = tuple(sorted(unknown_ingredient_ids))
        ids_str = ", ".join(map(str, self.unknown_ingredient_ids))
        super().__init__(f"Ingredients not found: {ids_str}")
