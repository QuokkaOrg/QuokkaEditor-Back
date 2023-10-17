from quokka_editor_back.models.operation import Operation, OperationType


def apply_operation(doc: str, op: Operation) -> str:
    if op.type == OperationType.INSERT:
        doc = doc[: op.pos] + op.content + doc[op.pos :]
    elif op.type == OperationType.DELETE:
        doc = doc[: op.pos] + doc[op.pos + 1 :]
    return doc


def transform(new_op: Operation, prev_op: Operation) -> Operation:
    if new_op.type == OperationType.INSERT and prev_op.type == OperationType.INSERT:
        if new_op.pos < prev_op.pos:
            return new_op
        return Operation(
            pos=prev_op.pos + 1, content=new_op.content, type=OperationType.INSERT
        )

    if new_op.type == OperationType.INSERT and prev_op.type == OperationType.DELETE:
        if new_op.pos <= prev_op.pos:
            return new_op
        return Operation(
            pos=new_op.pos - 1, content=new_op.content, type=OperationType.INSERT
        )

    if new_op.type == OperationType.DELETE and prev_op.type == OperationType.INSERT:
        if new_op.pos < prev_op.pos:
            return new_op
        return Operation(pos=new_op.pos + 1, type=OperationType.DELETE)

    if new_op.type == OperationType.DELETE and prev_op.type == OperationType.DELETE:
        if new_op.pos <= prev_op.pos:
            return new_op
        elif new_op.pos > prev_op.pos:
            return Operation(pos=new_op.pos, type=OperationType.DELETE)
    raise Exception("Invalid operations")
