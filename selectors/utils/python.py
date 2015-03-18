def flatten(x):
    """flatten(sequence) -> list

    Returns a single, flat list which contains all elements retrieved
    from the sequence and all recursively contained sub-sequences
    (iterables).

    Examples:
    >>> [1, 2, [3,4], (5,6)]
    [1, 2, [3, 4], (5, 6)]
    >>> flatten([[[1,2,3], (42,None)], [4,5], [6], 7, (8,9,10)])
    [1, 2, 3, 42, None, 4, 5, 6, 7, 8, 9, 10]"""

    return list(iflatten(x))


def iflatten(x):
    """iflatten(sequence) -> iterator

    Similar to ``.flatten()``, but returns iterator instead"""

    for el in x:
        if hasattr(el, "__iter__"):
            for el_ in flatten(el):
                yield el_
        else:
            yield el
