"""Tree edit distance computation using APTED with sqlparse integration."""

from dataclasses import dataclass
from typing import Optional

from apted import APTED, Config
from sqlparse.sql import TokenList


@dataclass
class EditOperation:
    """A single transformation step in the edit sequence.

    Attributes:
        type: One of 'match', 'rename', 'insert', 'delete'.
        source_node: Node label from tree1 (None for insert).
        target_node: Node label from tree2 (None for delete).
        node_type: Type of node - 'group' or 'token'.
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
        distance: Tree edit distance (minimum edit operations).
        operations: Sequence of edit operations.
        score: Normalized similarity score (0.0-1.0).
    """

    distance: int
    operations: list[EditOperation]
    score: float


class SqlparseConfig(Config):
    """APTED config for traversing sqlparse token trees directly.

    This configuration teaches APTED how to work with sqlparse tokens
    without requiring an intermediate transformation layer.
    """

    def children(self, node):
        """Return child tokens of a sqlparse node.

        Args:
            node: A sqlparse Token or TokenList.

        Returns:
            List of child tokens for TokenList, empty list for Token (leaf).
        """
        if isinstance(node, TokenList):
            return list(node.tokens)
        # Leaf Token has no children
        return []

    def delete(self, node):
        """Cost of deleting a node.

        Args:
            node: The node to delete.

        Returns:
            Uniform cost of 1.
        """
        return 1

    def insert(self, node):
        """Cost of inserting a node.

        Args:
            node: The node to insert.

        Returns:
            Uniform cost of 1.
        """
        return 1

    def rename(self, node1, node2):
        """Cost of renaming node1 to node2.

        Args:
            node1: Source node.
            node2: Target node.

        Returns:
            0 if labels match, 1 otherwise.
        """
        label1 = self._get_label(node1)
        label2 = self._get_label(node2)
        return 0 if label1 == label2 else 1

    def _get_label(self, node):
        """Extract a label for comparison.

        Args:
            node: A sqlparse Token or TokenList.

        Returns:
            For TokenList (groups): class name (e.g., "Statement", "Where").
            For Token (leaf): normalized value (e.g., "SELECT", "id", "users").
        """
        if isinstance(node, TokenList):
            return type(node).__name__
        # For Token: use the actual normalized value for accurate comparison
        return node.normalized


def tree_size(node) -> int:
    """Count total nodes in a sqlparse token tree.

    Args:
        node: Root of sqlparse token tree.

    Returns:
        Total number of nodes (groups + leaf tokens).
    """
    config = SqlparseConfig()
    children = config.children(node)
    return 1 + sum(tree_size(child) for child in children)


def compute_score(distance: int, size1: int, size2: int) -> float:
    """Compute normalized similarity score.

    Formula: 1 - (distance / max(size1, size2))

    Args:
        distance: Tree edit distance.
        size1: Size of first tree.
        size2: Size of second tree.

    Returns:
        Score between 0.0 (completely different) and 1.0 (identical).
        Returns 1.0 if both trees are empty (max size = 0).
    """
    max_size = max(size1, size2)
    if max_size == 0:
        return 1.0
    return 1.0 - (distance / max_size)


def compute_distance(tree1, tree2) -> tuple[int, list]:
    """Compute tree edit distance between two sqlparse token trees.

    Args:
        tree1: First sqlparse token tree.
        tree2: Second sqlparse token tree.

    Returns:
        Tuple of (distance, mapping) where:
        - distance: Integer tree edit distance.
        - mapping: List of (node1, node2) tuples from APTED.
    """
    config = SqlparseConfig()
    apted = APTED(tree1, tree2, config)
    distance = apted.compute_edit_distance()
    mapping = apted.compute_edit_mapping()
    return distance, mapping


def _get_node_type(node) -> str:
    """Determine if a node is a group or token.

    Args:
        node: A sqlparse node.

    Returns:
        'group' for TokenList, 'token' for Token (leaf).
    """
    if isinstance(node, TokenList):
        return "group"
    return "token"


def _get_tree_path(node) -> str:
    """Extract the path from root to this node.

    Args:
        node: A sqlparse node.

    Returns:
        Path string like "Statement > Identifier > Name".
    """
    config = SqlparseConfig()
    path_parts = []
    current = node

    while current is not None:
        label = config._get_label(current)
        path_parts.append(label)
        # Get parent - sqlparse tokens have parent attribute
        current = getattr(current, "parent", None)

    # Reverse to get root-to-node order, exclude the current node itself
    path_parts.reverse()
    if len(path_parts) > 1:
        return " > ".join(path_parts[:-1])
    return ""


def interpret_mapping(mapping: list) -> list[EditOperation]:
    """Convert APTED mapping to list of EditOperation objects.

    Args:
        mapping: List of (node1, node2) tuples from APTED.compute_edit_mapping().

    Returns:
        List of EditOperation objects representing the transformation.
    """
    config = SqlparseConfig()
    operations = []

    for node1, node2 in mapping:
        if node1 is None:
            # INSERT: node2 was added
            label = config._get_label(node2)
            node_type = _get_node_type(node2)
            tree_path = _get_tree_path(node2)
            operations.append(
                EditOperation(
                    type="insert",
                    source_node=None,
                    target_node=label,
                    node_type=node_type,
                    tree_path=tree_path,
                )
            )
        elif node2 is None:
            # DELETE: node1 was removed
            label = config._get_label(node1)
            node_type = _get_node_type(node1)
            tree_path = _get_tree_path(node1)
            operations.append(
                EditOperation(
                    type="delete",
                    source_node=label,
                    target_node=None,
                    node_type=node_type,
                    tree_path=tree_path,
                )
            )
        else:
            label1 = config._get_label(node1)
            label2 = config._get_label(node2)
            # Use node1 for type/path (source tree)
            node_type = _get_node_type(node1)
            tree_path = _get_tree_path(node1)
            if label1 == label2:
                # MATCH: nodes are equivalent
                operations.append(
                    EditOperation(
                        type="match",
                        source_node=label1,
                        target_node=label2,
                        node_type=node_type,
                        tree_path=tree_path,
                    )
                )
            else:
                # RENAME: node label changed
                operations.append(
                    EditOperation(
                        type="rename",
                        source_node=label1,
                        target_node=label2,
                        node_type=node_type,
                        tree_path=tree_path,
                    )
                )

    return operations
