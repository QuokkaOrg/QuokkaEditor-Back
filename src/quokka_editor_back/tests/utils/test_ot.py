import pytest

from quokka_editor_back.models.operation import (
    OperationSchema,
    OperationType,
    PosSchema,
)
from quokka_editor_back.utils.ot import adjust_position, apply_operation, transform


@pytest.mark.parametrize(
    "new_pos_ch, new_pos_line, expected_pos_ch, expected_pos_line",
    [
        (0, 0, 0, 0),
        (0, 1, 0, 1),
        (0, 2, 0, 2),
        (11, 1, 15, 1),
        (11, 2, 11, 2),
    ],
)
def test_adjust_position(
    new_pos_ch: int, new_pos_line: int, expected_pos_ch: int, expected_pos_line: int
):
    # Given
    new_pos = PosSchema(ch=new_pos_ch, line=new_pos_line)
    prev_pos = PosSchema(ch=10, line=1)
    prev_text = "text"

    # When
    result = adjust_position(new_pos, prev_pos, prev_text)

    # Then
    assert result == PosSchema(ch=expected_pos_ch, line=expected_pos_line)


@pytest.mark.parametrize(
    "new_op_type, prev_op_type",
    [
        (OperationType.INPUT, OperationType.INPUT),
        (OperationType.UNDO, OperationType.UNDO),
        (OperationType.PASTE, OperationType.PASTE),
        (OperationType.INPUT, OperationType.UNDO),
        (OperationType.INPUT, OperationType.PASTE),
        (OperationType.UNDO, OperationType.INPUT),
        (OperationType.UNDO, OperationType.PASTE),
        (OperationType.PASTE, OperationType.INPUT),
        (OperationType.PASTE, OperationType.UNDO),
    ],
)
def test_transform_both_input_operation_types(new_op_type, prev_op_type):
    # Given
    prev_op_from_pos = PosSchema(ch=0, line=0)
    prev_op_to_pos = PosSchema(ch=4, line=0)
    prev_op = OperationSchema(
        from_pos=prev_op_from_pos,
        to_pos=prev_op_to_pos,
        text=["text"],
        type=prev_op_type,
        revision=0,
    )
    new_op_from_pos = PosSchema(ch=4, line=0)
    new_op_to_pos = PosSchema(ch=8, line=0)
    new_op = OperationSchema(
        from_pos=new_op_from_pos,
        to_pos=new_op_to_pos,
        text=["text"],
        type=new_op_type,
        revision=1,
    )

    # When
    result = transform(new_op, prev_op)

    # Then
    # I have some questions about that
    result_from_pos = PosSchema(ch=8, line=0)
    result_to_pos = PosSchema(ch=12, line=0)
    assert result == OperationSchema(
        from_pos=result_from_pos,
        to_pos=result_to_pos,
        text=new_op.text,
        type=new_op_type,
        revision=new_op.revision,
    )


@pytest.mark.parametrize(
    "new_op_type, new_op_from_pos",
    [
        (
            OperationType.INPUT,
            PosSchema(ch=0, line=1),
        ),
        (
            OperationType.INPUT,
            PosSchema(ch=2, line=0),
        ),
        (
            OperationType.UNDO,
            PosSchema(ch=0, line=1),
        ),
        (
            OperationType.UNDO,
            PosSchema(ch=2, line=0),
        ),
        (
            OperationType.PASTE,
            PosSchema(ch=0, line=1),
        ),
        (
            OperationType.PASTE,
            PosSchema(ch=2, line=0),
        ),
    ],
)
def test_transform_prev_op_delete(new_op_type, new_op_from_pos):
    # Given
    prev_op = OperationSchema(
        from_pos=PosSchema(ch=0, line=0),
        to_pos=PosSchema(ch=0, line=0),
        text=["text"],
        type=OperationType.DELETE,
        revision=0,
    )
    new_op = OperationSchema(
        from_pos=new_op_from_pos,
        to_pos=PosSchema(ch=0, line=0),
        text=["text"],
        type=new_op_type,
        revision=1,
    )

    # When
    result = transform(new_op, prev_op)

    # Then
    assert result == OperationSchema(
        from_pos=PosSchema(line=new_op.from_pos.line - 1, ch=new_op.from_pos.ch),
        to_pos=new_op.to_pos,
        text=new_op.text,
        type=new_op.type,
        revision=new_op.revision,
    )


@pytest.mark.parametrize(
    "new_op_type, prev_op_from_pos",
    [
        (
            OperationType.INPUT,
            PosSchema(ch=0, line=1),
        ),
        (
            OperationType.INPUT,
            PosSchema(ch=0, line=0),
        ),
        (
            OperationType.INPUT,
            PosSchema(ch=1, line=0),
        ),
        (
            OperationType.UNDO,
            PosSchema(ch=0, line=1),
        ),
        (
            OperationType.UNDO,
            PosSchema(ch=0, line=0),
        ),
        (
            OperationType.UNDO,
            PosSchema(ch=1, line=0),
        ),
        (
            OperationType.PASTE,
            PosSchema(ch=0, line=1),
        ),
        (
            OperationType.PASTE,
            PosSchema(ch=0, line=0),
        ),
        (
            OperationType.PASTE,
            PosSchema(ch=1, line=0),
        ),
    ],
)
def test_transform_prev_op_delete_with_specific_conditions(
    new_op_type, prev_op_from_pos
):
    # Given
    prev_op = OperationSchema(
        from_pos=prev_op_from_pos,
        to_pos=PosSchema(ch=0, line=0),
        text=["text"],
        type=OperationType.DELETE,
        revision=0,
    )
    new_op = OperationSchema(
        from_pos=PosSchema(ch=0, line=0),
        to_pos=PosSchema(ch=0, line=0),
        text=["text"],
        type=new_op_type,
        revision=1,
    )

    # When
    result = transform(new_op, prev_op)

    # Then
    assert result == new_op


@pytest.mark.parametrize(
    "prev_op_type",
    [
        OperationType.INPUT,
        OperationType.UNDO,
        OperationType.PASTE,
    ],
)
def test_new_op_delete(prev_op_type):
    # Given
    prev_op = OperationSchema(
        from_pos=PosSchema(ch=0, line=0),
        to_pos=PosSchema(ch=4, line=0),
        text=["text"],
        type=prev_op_type,
        revision=0,
    )
    new_op = OperationSchema(
        from_pos=PosSchema(ch=4, line=0),
        to_pos=PosSchema(ch=8, line=0),
        text=["text"],
        type=OperationType.DELETE,
        revision=1,
    )

    # When
    result = transform(new_op, prev_op)

    # Then
    assert result == OperationSchema(
        from_pos=PosSchema(ch=8, line=0),
        to_pos=new_op.to_pos,
        text=new_op.text,
        type=OperationType.DELETE,
        revision=new_op.revision,
    )


@pytest.mark.parametrize("from_pos_line", [0, 1, 2])
def test_both_delete_operation(from_pos_line):
    # Given
    prev_op = OperationSchema(
        from_pos=PosSchema(ch=0, line=1),
        to_pos=PosSchema(ch=4, line=1),
        text=["text"],
        type=OperationType.DELETE,
        revision=0,
    )
    new_op = OperationSchema(
        from_pos=PosSchema(ch=4, line=from_pos_line),
        to_pos=PosSchema(ch=8, line=1),
        text=["text"],
        type=OperationType.DELETE,
        revision=1,
    )

    # When
    result = transform(new_op, prev_op)

    # Then
    assert result == new_op


@pytest.fixture
def sample_document_content():
    return ["abc def", "ghi jkl", "mno pqr"]


@pytest.mark.parametrize("operation_type", [
    OperationType.INPUT,
    OperationType.PASTE,
    OperationType.UNDO
])
def test_apply_operation_input(sample_document_content, operation_type):
    # Given
    op = OperationSchema(
        from_pos=PosSchema(ch=3, line=0),
        to_pos=PosSchema(ch=3, line=0),
        text=["XYZ"],
        type=operation_type,
        revision=1,
    )

    # When
    result = apply_operation(sample_document_content.copy(), op)

    # Then
    assert result == ["abcXYZ def", "ghi jkl", "mno pqr"]


@pytest.mark.parametrize("operation_type", [
    OperationType.INPUT,
    OperationType.PASTE,
    OperationType.UNDO
])
def test_apply_operation_input_1(sample_document_content, operation_type):
    # Given
    op = OperationSchema(
        from_pos=PosSchema(ch=3, line=0),
        to_pos=PosSchema(ch=6, line=0),
        text=["XYZ"],
        type=operation_type,
        revision=1,
    )

    # When
    result = apply_operation(sample_document_content.copy(), op)

    # Then
    assert result == ["abcXYZf", "ghi jkl", "mno pqr"]


def test_apply_operation_delete(sample_document_content):
    # Given
    op = OperationSchema(
        from_pos=PosSchema(ch=0, line=0),
        to_pos=PosSchema(ch=3, line=0),
        text=[""],
        type=OperationType.DELETE,
        revision=1,
    )

    # When
    result = apply_operation(sample_document_content.copy(), op)

    # Then
    assert result == [" def", "ghi jkl", "mno pqr"]
