class Insert:
    def __init__(self, pos, char):
        self.pos = pos
        self.char = char


class Delete:
    def __init__(self, pos):
        self.pos = pos


def transform(op1, op2):
    """
    Transformuje op1 względem op2, tak aby operacje mogły być bezpiecznie stosowane w dowolnej kolejności.
    Zwraca przekształconą operację op1.
    """
    if isinstance(op1, Insert) and isinstance(op2, Insert):
        if op1.pos < op2.pos or (op1.pos == op2.pos and op1.char < op2.char):
            return op1
        return Insert(op1.pos + 1, op1.char)

    if isinstance(op1, Insert) and isinstance(op2, Delete):
        if op1.pos <= op2.pos:
            return op1
        return Insert(op1.pos - 1, op1.char)

    if isinstance(op1, Delete) and isinstance(op2, Insert):
        if op1.pos < op2.pos:
            return op1
        return Delete(op1.pos + 1)

    if isinstance(op1, Delete) and isinstance(op2, Delete):
        if op1.pos < op2.pos:
            return op1
        elif op1.pos > op2.pos:
            return Delete(op1.pos - 1)


def apply_operation(doc, op):
    """
    Stosuje daną operację (wstawianie lub usuwanie) na dokumencie.
    """
    if isinstance(op, Insert):
        doc = doc[: op.pos] + op.char + doc[op.pos :]
    elif isinstance(op, Delete):
        doc = doc[: op.pos] + doc[op.pos + 1 :]
    return doc


# Przykład użycia
doc = "hello, world!"

op_bartek = [Insert(i, ch) for i, ch in enumerate("Bartek")]
op_damian = [Insert(i, ch) for i, ch in enumerate("Damian")]
# op1 = Insert(0, "A ")
# op2 = Insert(len(doc), " B")
# op3 = Delete(0)
for op in op_bartek:
    doc = apply_operation(doc, op)
for op in op_damian:
    doc = apply_operation(doc, op)
# op1_prime = transform(transform(op1, op2), op3)

# # doc = apply_operation(doc, op1)
# doc = apply_operation(doc, op2)
# doc = apply_operation(doc, op3)
# doc = apply_operation(doc, op1_prime)

print(doc)
# [
#     ["A dupa FD dupa dupa SDA"]
#     ["kaka kaka"]
#     []
#     []
# ]
"hello, world!"
"A ello, world! B"
"world! B"
"A , world! B"
