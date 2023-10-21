from quokka_editor_back.models.operation import (
    OperationSchema,
    OperationType,
    PosSchema,
)


def adjust_position(
    new_pos: PosSchema, prev_pos: PosSchema, prev_text: str
) -> PosSchema:
    if new_pos.line < prev_pos.line or (
        new_pos.line == prev_pos.line and new_pos.ch <= prev_pos.ch
    ):
        return new_pos
    if new_pos.line == prev_pos.line:
        return PosSchema(
            line=new_pos.line,
            ch=new_pos.ch + len(prev_text),
        )
    return PosSchema(line=new_pos.line + 1, ch=new_pos.ch)


def transform(new_op: OperationSchema, prev_op: OperationSchema) -> OperationSchema:
    if new_op.type == OperationType.INPUT and prev_op.type == OperationType.INPUT:
        adjusted_from_pos = adjust_position(
            new_op.from_pos, prev_op.from_pos, prev_op.text[0]
        )
        return OperationSchema(
            from_pos=adjusted_from_pos,
            to_pos=new_op.to_pos,
            text=new_op.text,
            type=OperationType.INPUT,
            revision=new_op.revision,
        )

    if new_op.type == OperationType.INPUT and prev_op.type == OperationType.DELETE:
        if new_op.from_pos.line < prev_op.from_pos.line or (
            new_op.from_pos.line == prev_op.from_pos.line
            and new_op.from_pos.ch <= prev_op.from_pos.ch
        ):
            return new_op
        return OperationSchema(
            from_pos=PosSchema(line=new_op.from_pos.line - 1, ch=new_op.from_pos.ch),
            to_pos=new_op.to_pos,
            text=new_op.text,
            type=OperationType.INPUT,
            revision=new_op.revision,
        )

    if new_op.type == OperationType.DELETE and prev_op.type == OperationType.INPUT:
        adjusted_from_pos = adjust_position(
            new_op.from_pos, prev_op.from_pos, prev_text=prev_op.text[0]
        )
        return OperationSchema(
            from_pos=adjusted_from_pos,
            to_pos=new_op.to_pos,
            text=new_op.text,
            type=OperationType.DELETE,
            revision=new_op.revision,
        )

    if new_op.type == OperationType.DELETE and prev_op.type == OperationType.DELETE:
        if new_op.from_pos.line <= prev_op.from_pos.line:
            return new_op
        return OperationSchema(
            from_pos=PosSchema(line=new_op.from_pos.line, ch=new_op.from_pos.ch),
            to_pos=new_op.to_pos,
            text=new_op.text,
            type=OperationType.DELETE,
            revision=new_op.revision,
        )

    raise Exception("Invalid operations")


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
