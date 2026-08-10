# ADR-0006 — Isolated Writable Workspaces

Status: Accepted

Concurrent write Agents must not share one mutable code tree.

Use WorkspaceLease + worktree/sandbox.

Large datasets/artifacts live outside Git and are mounted/read via stable refs.
