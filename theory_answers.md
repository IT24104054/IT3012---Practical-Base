# Practical 05: Theory-to-Implementation Mapping

## 1. Reachability vs. Feasibility

The `_neighbors` method checks reachability: the tile must be inside the grid and not be a wall. A reachable tile is not automatically safe. Before A* places a neighbor in its frontier, `_is_feasible` clears the current facts, tells the percept facts for that tile, and runs forward chaining. If the KB derives `Retreat`, A* skips the tile even though it is physically reachable.

## 2. Declarative vs. Procedural Paradigms

The rules are stored as data in the `KnowledgeBase`, while the inference algorithm stays the same. Movement code does not need a new conditional for every domain rule. Adding 50 rules therefore mostly adds 50 declarative rule entries instead of making the agent's procedural movement method grow into a large, tightly coupled decision tree.

## 3. Modus Ponens and Horn Clauses

For each rule, `forward_chain` checks whether every premise is present. When `TargetVisible` and `HasDust` are present, it adds `SafeToEngage`, which is the conclusion of the Horn clause. A later pass can then use that new fact with `BloodseekerMissing` to derive `Retreat`. Repeating passes until no new facts appear computes the fixed point of these Modus Ponens deductions.