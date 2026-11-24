class LineageGraph:

    def __init__(self):
        self.nodes = set()
        self.edges = set()

    def add_table(self, table):
        self.nodes.add(table)

    def add_dependency(self, source, target):
        self.nodes.update([source, target])
        self.edges.add((source, target))

    def upstream(self, table):
        return sorted(
            source for source, target in self.edges
            if target == table
        )

    def downstream(self, table):
        return sorted(
            target for source, target in self.edges
            if source == table
        )

    def ancestors(self, table):
        visited = set()
        pending = self.upstream(table)

        while pending:
            node = pending.pop()

            if node not in visited:
                visited.add(node)
                pending.extend(self.upstream(node))

        return sorted(visited - {table})

    def descendants(self, table):
        visited = set()
        pending = self.downstream(table)

        while pending:
            node = pending.pop()

            if node not in visited:
                visited.add(node)
                pending.extend(self.downstream(node))

        return sorted(visited - {table})

    def detect_cycles(self):
        visited = set()
        active = set()
        path = []
        cycles = []

        def visit(node):
            if node in active:
                start = path.index(node)
                cycles.append(path[start:] + [node])
                return

            if node in visited:
                return

            active.add(node)
            path.append(node)

            for child in self.downstream(node):
                visit(child)

            path.pop()
            active.remove(node)
            visited.add(node)

        for node in sorted(self.nodes):
            visit(node)

        return cycles

    def orphan_tables(self):
        connected = {
            node for edge in self.edges for node in edge
        }
        return sorted(self.nodes - connected)

    def missing_tables(self, actual_tables):
        return sorted(self.nodes - set(actual_tables))

    def to_dict(self):
        return {
            "nodes": sorted(self.nodes),
            "edges": [
                {"source": source, "target": target}
                for source, target in sorted(self.edges)
            ],
            "cycles": self.detect_cycles(),
            "orphans": self.orphan_tables(),
        }
