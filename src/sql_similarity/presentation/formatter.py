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
        # Build the base operation line
        if op.type == "match":
            op_line = f"  MATCH:  {op.source_node}"
        elif op.type == "rename":
            op_line = f"  RENAME: {op.source_node} -> {op.target_node}"
        elif op.type == "insert":
            op_line = f"  INSERT: {op.target_node}"
        elif op.type == "delete":
            op_line = f"  DELETE: {op.source_node}"
        else:
            op_line = f"  {op.type.upper()}: {op.source_node or op.target_node}"

        # Add detailed info if available
        details = []
        if op.node_type:
            details.append(f"[{op.node_type}]")
        if op.tree_path:
            details.append(f"at {op.tree_path}")

        if details:
            op_line += f" {' '.join(details)}"

        lines.append(op_line)

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
                "node_type": op.node_type,
                "tree_path": op.tree_path,
            }
            for op in result.operations
        ],
    }
    return json.dumps(data, indent=2)
