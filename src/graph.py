import csv
import networkx as nx
from typing import Dict, List, Optional

class OrgGraph:
    """Build and query organizational hierarchy using NetworkX."""

    def __init__(self, employees_path: str, teams_path: str):
        self.graph = nx.MultiDiGraph()
        self.employees = {}  # name -> {id, team, manager_id}
        self.teams = {}  # team_name -> {id, department}

        self._load_employees(employees_path)
        self._load_teams(teams_path)
        self._build_graph()

    def _load_employees(self, path: str):
        """Load employees from CSV."""
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                emp_id = int(row['id'])
                name = row['name']
                manager_id = row['manager_id']
                # Handle NULL manager_id
                manager_id = int(manager_id) if manager_id and manager_id != 'NULL' else None
                self.employees[name] = {
                    'id': emp_id,
                    'team': row['team'],
                    'manager_id': manager_id
                }

    def _load_teams(self, path: str):
        """Load teams from CSV."""
        with open(path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.teams[row['team_name']] = {
                    'id': int(row['team_id']),
                    'department': row['department']
                }

    def _build_graph(self):
        """Build the directed graph of org hierarchy."""
        # Add employee nodes
        for name, info in self.employees.items():
            self.graph.add_node(name, node_type='employee', team=info['team'])

        # Add manager -> employee edges (reporting structure)
        name_by_id = {v['id']: k for k, v in self.employees.items()}
        for name, info in self.employees.items():
            if info['manager_id'] and info['manager_id'] in name_by_id:
                manager_name = name_by_id[info['manager_id']]
                self.graph.add_edge(manager_name, name, edge_type='manages')

        # Add peer edges (same team)
        team_members = {}
        for name, info in self.employees.items():
            team = info['team']
            if team not in team_members:
                team_members[team] = []
            team_members[team].append(name)

        for team, members in team_members.items():
            for i, name1 in enumerate(members):
                for name2 in members[i+1:]:
                    self.graph.add_edge(name1, name2, edge_type='peer')
                    self.graph.add_edge(name2, name1, edge_type='peer')

    def get_org_structure(self, name: str) -> Dict:
        """Get org info for an employee: manager, team, direct reports."""
        if name not in self.employees:
            return {'error': f'Employee {name} not found'}

        info = self.employees[name]

        # Get direct reports (people who report to this person)
        reports = []
        for successor in self.graph.successors(name):
            # In MultiDiGraph, self.graph[u][v] returns a dict of edge keys
            edge_dict = self.graph[name][successor]
            for edge_key, edge_data in edge_dict.items():
                if edge_data.get('edge_type') == 'manages':
                    reports.append(successor)
                    break

        # Get manager
        manager_name = None
        for pred in self.graph.predecessors(name):
            edge_dict = self.graph[pred][name]
            for edge_key, edge_data in edge_dict.items():
                if edge_data.get('edge_type') == 'manages':
                    manager_name = pred
                    break
            if manager_name:
                break

        return {
            'name': name,
            'team': info['team'],
            'manager': manager_name,
            'direct_reports': reports,
            'org_level': self._get_org_level(name)
        }

    def get_peers(self, name: str) -> List[str]:
        """Get peer employees (same team)."""
        if name not in self.employees:
            return []
        peers = []
        for neighbor in self.graph.successors(name):
            edge_dict = self.graph[name][neighbor]
            for edge_key, edge_data in edge_dict.items():
                if edge_data.get('edge_type') == 'peer':
                    peers.append(neighbor)
                    break
        return peers

    def get_team_members(self, team_name: str) -> List[str]:
        """Get all members of a team."""
        return [n for n, info in self.employees.items() if info['team'] == team_name]

    def find_path(self, from_emp: str, to_emp: str) -> Optional[List[str]]:
        """Find shortest path between two employees in the org graph."""
        if from_emp not in self.employees or to_emp not in self.employees:
            return None

        try:
            # Use undirected version for path finding (treats all edges as bidirectional)
            undirected = self.graph.to_undirected()
            path = nx.shortest_path(undirected, from_emp, to_emp)
            return path
        except nx.NetworkXNoPath:
            return None

    def _get_org_level(self, name: str) -> int:
        """Calculate org level (0 = CEO, 1 = direct report, etc)."""
        # Level is longest path to a manager with no manager
        level = 0
        current = name
        visited = set()

        while current in self.employees and current not in visited:
            visited.add(current)
            mgr_id = self.employees[current]['manager_id']
            if not mgr_id:
                return level
            mgr_name = next((n for n, i in self.employees.items() if i['id'] == mgr_id), None)
            if not mgr_name:
                return level
            current = mgr_name
            level += 1
        return level
