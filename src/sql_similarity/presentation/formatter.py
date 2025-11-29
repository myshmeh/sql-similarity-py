"""Output formatters for comparison results."""

import json

from sql_similarity.domain.comparator import ComparisonResult


def format_human(result: ComparisonResult) -> str:
    """Format comparison result for human-readable output.

    Args:
        result: ComparisonResult with distance and operations.

    Returns:
        Human-readable string with distance and operations list.
    """
    lines = [f"Tree Edit Distance: {result.distance}", "", "Operations:"]

    for op in result.operations:
        if op.type == "match":
            lines.append(f"  MATCH:  {op.source_node}")
        elif op.type == "rename":
            lines.append(f"  RENAME: {op.source_node} -> {op.target_node}")
        elif op.type == "insert":
            lines.append(f"  INSERT: {op.target_node}")
        elif op.type == "delete":
            lines.append(f"  DELETE: {op.source_node}")

    return "\n".join(lines)


def format_json(result: ComparisonResult) -> str:
    """Format comparison result as JSON.

    Args:
        result: ComparisonResult with distance and operations.

    Returns:
        JSON string with distance and operations array.
    """
    data = {
        "distance": result.distance,
        "operations": [
            {
                "type": op.type,
                "source": op.source_node,
                "target": op.target_node,
            }
            for op in result.operations
        ],
    }
    return json.dumps(data, indent=2)
