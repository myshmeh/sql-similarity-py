"""SQL comparison using sqlglot diff."""

from dataclasses import dataclass
from typing import Optional

from sqlglot import diff, exp
from sqlglot.diff import Insert, Remove, Move, Update, Keep


@dataclass
class EditOperation:
    """A single transformation step in the edit sequence.

    Attributes:
        type: One of 'match', 'rename', 'insert', 'delete', 'move'.
        source_node: Node label from tree1 (None for insert).
        target_node: Node label from tree2 (None for delete).
        node_type: Type of node (expression class name).
        tree_path: Path from root to this node.
    """

    type: str
    source_node: Optional[str]
    target_node: Optional[str]
    node_type: Optional[str] = None
    tree_path: Optional[str] = None


@dataclass
class ComparisonResult:
    """Result of comparing two SQL parse trees.

    Attributes:
        edit_count: Number of edit operations (excluding matches).
        operations: Sequence of edit operations.
        score: Normalized similarity score (0.0-1.0).
    """

    edit_count: int
    operations: list[EditOperation]
    score: float


def count_nodes(expr: exp.Expression | None) -> int:
    """Count total nodes in a sqlglot expression tree.

    Args:
        expr: Root of sqlglot expression tree.

    Returns:
        Total number of nodes in the tree, 0 if expr is None.
    """
    if expr is None:
        return 0
    return sum(1 for _ in expr.walk())


def compute_score(keeps: int, total: int) -> float:
    """Compute normalized similarity score.

    Formula: keeps / total

    Args:
        keeps: Number of Keep (match) operations.
        total: Total number of operations.

    Returns:
        Score between 0.0 (completely different) and 1.0 (identical).
        Returns 1.0 if total is 0 (both trees empty = identical).
    """
    if total == 0:
        return 1.0
    return keeps / total


def _get_label(expr: exp.Expression) -> str:
    """Get a label for an expression node.

    Args:
        expr: A sqlglot Expression node.

    Returns:
        SQL representation of the node (truncated if too long).
    """
    sql = expr.sql()
    if len(sql) > 50:
        return sql[:47] + "..."
    return sql


def interpret_edits(edits: list) -> list[EditOperation]:
    """Convert sqlglot edits to list of EditOperation objects.

    Args:
        edits: List of sqlglot diff edit operations.

    Returns:
        List of EditOperation objects representing the transformation.
    """
    operations = []

    for edit in edits:
        if isinstance(edit, Keep):
            operations.append(
                EditOperation(
                    type="match",
                    source_node=_get_label(edit.source),
                    target_node=_get_label(edit.target),
                    node_type=type(edit.source).__name__,
                )
            )
        elif isinstance(edit, Update):
            operations.append(
                EditOperation(
                    type="rename",
                    source_node=_get_label(edit.source),
                    target_node=_get_label(edit.target),
                    node_type=type(edit.source).__name__,
                )
            )
        elif isinstance(edit, Insert):
            operations.append(
                EditOperation(
                    type="insert",
                    source_node=None,
                    target_node=_get_label(edit.expression),
                    node_type=type(edit.expression).__name__,
                )
            )
        elif isinstance(edit, Remove):
            operations.append(
                EditOperation(
                    type="delete",
                    source_node=_get_label(edit.expression),
                    target_node=None,
                    node_type=type(edit.expression).__name__,
                )
            )
        elif isinstance(edit, Move):
            operations.append(
                EditOperation(
                    type="move",
                    source_node=_get_label(edit.source),
                    target_node=_get_label(edit.target),
                    node_type=type(edit.source).__name__,
                )
            )

    return operations


def compare_trees(
    tree1: exp.Expression | None, tree2: exp.Expression | None
) -> ComparisonResult:
    """Compare two SQL expression trees and return comparison result.

    Args:
        tree1: First sqlglot expression tree (or None).
        tree2: Second sqlglot expression tree (or None).

    Returns:
        ComparisonResult with edit_count, operations, and score.
    """
    # Handle None cases
    if tree1 is None and tree2 is None:
        return ComparisonResult(edit_count=0, operations=[], score=1.0)

    if tree1 is None or tree2 is None:
        # One tree is None, the other is not - completely different
        return ComparisonResult(edit_count=1, operations=[], score=0.0)

    # Get edit operations using sqlglot diff
    edits = diff(tree1, tree2)

    # Convert to EditOperation objects
    operations = interpret_edits(edits)

    # Calculate score based on Keep ratio
    keeps = sum(1 for op in operations if op.type == "match")
    total = len(operations)
    edit_count = total - keeps
    score = compute_score(keeps, total)

    return ComparisonResult(edit_count=edit_count, operations=operations, score=score)
