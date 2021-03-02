
def compare_lists(a: list, b: list, key = None) -> bool:
    if(len(a) != len(b)):
        return False

    return all([a == b for a,b in zip(sorted(a, key=key), sorted(b, key=key))])