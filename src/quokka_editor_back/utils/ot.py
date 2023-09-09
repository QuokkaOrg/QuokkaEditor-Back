from quokka_editor_back.models.operation import Operation, OperationType


def apply_operation(doc: str, op: Operation) -> str:
    if op.type == OperationType.INSERT:
        doc = doc[: op.pos] + op.content + doc[op.pos :]
    elif op.type == OperationType.DELETE:
        doc = doc[: op.pos] + doc[op.pos + 1 :]
    return doc


def transform(recent_op: Operation, prev_op: Operation) -> Operation:
    if recent_op.type == OperationType.INSERT and prev_op.type == OperationType.INSERT:
        if recent_op.pos < prev_op.pos:
            return recent_op
        return Operation(
            pos=prev_op.pos + 1, content=recent_op.content, type=OperationType.INSERT
        )

    if recent_op.type == OperationType.INSERT and prev_op.type == OperationType.DELETE:
        if recent_op.pos <= prev_op.pos:
            return recent_op
        return Operation(
            pos=recent_op.pos - 1, content=recent_op.content, type=OperationType.INSERT
        )

    if recent_op.type == OperationType.DELETE and prev_op.type == OperationType.INSERT:
        if recent_op.pos < prev_op.pos:
            return recent_op
        return Operation(pos=recent_op.pos + 1, type=OperationType.DELETE)

    if recent_op.type == OperationType.DELETE and prev_op.type == OperationType.DELETE:
        if recent_op.pos <= prev_op.pos:
            return recent_op
        elif recent_op.pos > prev_op.pos:
            return Operation(pos=recent_op.pos, type=OperationType.DELETE)
    raise Exception("Invalid operations")
