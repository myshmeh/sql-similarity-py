"""Tree edit distance computation using APTED with ANTLR4 integration."""

from dataclasses import dataclass
from typing import Optional

from apted import APTED, Config
from antlr4.tree.Tree import TerminalNodeImpl


@dataclass
class EditOperation:
    """A single transformation step in the edit sequence.

    Attributes:
        type: One of 'match', 'rename', 'insert', 'delete'.
        source_node: Node label from tree1 (None for insert).
        target_node: Node label from tree2 (None for delete).
        node_type: Type of node - 'rule' or 'terminal' (None for backwards compatibility).
        tree_path: Path from root to this node (None for backwards compatibility).
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
    """

    distance: int
    operations: list[EditOperation]


class ANTLR4Config(Config):
    """APTED config for traversing ANTLR4 parse trees directly.

    This configuration teaches APTED how to work with ANTLR4 parse tree nodes
    without requiring an intermediate transformation layer.
    """

    def children(self, node):
        """Return child nodes of an ANTLR4 node.

        Args:
            node: An ANTLR4 ParserRuleContext or TerminalNode.

        Returns:
            List of child nodes. Empty list for terminal nodes.
        """
        if isinstance(node, TerminalNodeImpl):
            return []
        # ParserRuleContext nodes use getChildren()
        return list(node.getChildren())

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
            node: An ANTLR4 node.

        Returns:
            For rule nodes: class name minus "Context" suffix.
            For terminal nodes: token text.
        """
        if isinstance(node, TerminalNodeImpl):
            return node.getText()
        # For rule nodes, use the class name minus "Context"
        return type(node).__name__.replace("Context", "")


def compute_distance(tree1, tree2) -> tuple[int, list]:
    """Compute tree edit distance between two ANTLR4 parse trees.

    Args:
        tree1: First ANTLR4 parse tree.
        tree2: Second ANTLR4 parse tree.

    Returns:
        Tuple of (distance, mapping) where:
        - distance: Integer tree edit distance.
        - mapping: List of (node1, node2) tuples from APTED.
    """
    config = ANTLR4Config()
    apted = APTED(tree1, tree2, config)
    distance = apted.compute_edit_distance()
    mapping = apted.compute_edit_mapping()
    return distance, mapping


def _get_node_type(node) -> str:
    """Determine if a node is a rule or terminal.

    Args:
        node: An ANTLR4 node.

    Returns:
        'terminal' for TerminalNode, 'rule' for ParserRuleContext.
    """
    if isinstance(node, TerminalNodeImpl):
        return "terminal"
    return "rule"


def _get_tree_path(node) -> str:
    """Extract the path from root to this node.

    Args:
        node: An ANTLR4 node.

    Returns:
        Path string like "Snowflake_file > Select_statement > From_clause".
    """
    config = ANTLR4Config()
    path_parts = []
    current = node

    while current is not None:
        label = config._get_label(current)
        path_parts.append(label)
        # Get parent - ParserRuleContext has parentCtx, TerminalNode has parentCtx too
        current = getattr(current, "parentCtx", None)

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
    config = ANTLR4Config()
    operations = []

    for node1, node2 in mapping:
        if node1 is None:
            # INSERT: node2 was added
            label = config._get_label(node2)
            node_type = _get_node_type(node2)
            tree_path = _get_tree_path(node2)
            operations.append(EditOperation(
                type="insert",
                source_node=None,
                target_node=label,
                node_type=node_type,
                tree_path=tree_path
            ))
        elif node2 is None:
            # DELETE: node1 was removed
            label = config._get_label(node1)
            node_type = _get_node_type(node1)
            tree_path = _get_tree_path(node1)
            operations.append(EditOperation(
                type="delete",
                source_node=label,
                target_node=None,
                node_type=node_type,
                tree_path=tree_path
            ))
        else:
            label1 = config._get_label(node1)
            label2 = config._get_label(node2)
            # Use node1 for type/path (source tree)
            node_type = _get_node_type(node1)
            tree_path = _get_tree_path(node1)
            if label1 == label2:
                # MATCH: nodes are equivalent
                operations.append(EditOperation(
                    type="match",
                    source_node=label1,
                    target_node=label2,
                    node_type=node_type,
                    tree_path=tree_path
                ))
            else:
                # RENAME: node label changed
                operations.append(EditOperation(
                    type="rename",
                    source_node=label1,
                    target_node=label2,
                    node_type=node_type,
                    tree_path=tree_path
                ))

    return operations
