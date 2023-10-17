from quokka_editor_back.models.operation import (
    OperationSchema,
    OperationType,
)

# TODO: Use OperationSchema in transform function and apply new operation types
# def transform(new_op: Operation, prev_op: Operation) -> Operation:
#     if new_op.type == OperationType.INSERT and prev_op.type == OperationType.INSERT:
#         if new_op.pos < prev_op.pos:
#             return new_op
#         return Operation(
#             pos=prev_op.pos + 1, content=new_op.content, type=OperationType.INSERT
#         )

#     if new_op.type == OperationType.INSERT and prev_op.type == OperationType.DELETE:
#         if new_op.pos <= prev_op.pos:
#             return new_op
#         return Operation(
#             pos=new_op.pos - 1, content=new_op.content, type=OperationType.INSERT
#         )

#     if new_op.type == OperationType.DELETE and prev_op.type == OperationType.INSERT:
#         if new_op.pos < prev_op.pos:
#             return new_op
#         return Operation(pos=new_op.pos + 1, type=OperationType.DELETE)

#     if new_op.type == OperationType.DELETE and prev_op.type == OperationType.DELETE:
#         if new_op.pos <= prev_op.pos:
#             return new_op
#         elif new_op.pos > prev_op.pos:
#             return Operation(pos=new_op.pos, type=OperationType.DELETE)
#     raise Exception("Invalid operations")


def apply_operation(document_content: list[str], op: OperationSchema) -> list[str]:
    start_line, start_ch = op.from_pos.line, op.from_pos.ch
    end_line, end_ch = op.to_pos.line, op.to_pos.ch

    before = document_content[start_line][:start_ch]
    middle = op.text
    after = document_content[end_line][end_ch:]
    combined = []
    if op.type in (OperationType.INPUT, OperationType.PASTE, OperationType.UNDO):
        if len(middle) == 2:
            combined = [before + middle[0]] + [middle[-1] + after]
        elif len(middle) > 2:
            combined = [before + middle[0]] + middle[1:-1] + [middle[-1] + after]
        else:
            combined = [before + middle[0] + after]
    elif op.type == OperationType.DELETE:
        combined = [before + middle[0] + after]
    else:
        raise Exception("Invalid Operation!!!!")
    document_content[start_line : end_line + 1] = combined
    return document_content
