class Conflict(Exception):
    """A write broke a uniqueness / in-use rule. Routers turn it into 409."""
