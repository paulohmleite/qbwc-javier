def adjust_numeric_value(value):
    if isinstance(value, str):
        return float(value.replace(",", "."))
    return value