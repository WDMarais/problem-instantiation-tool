from enum import Enum


class Kind(Enum):
    INTEGER = "integer"
    FRACTION = "fraction"
    SYMBOL = "symbol"
    VARARG = "vararg"  # f(t) = at + b, find t (arbitrary input variable)
