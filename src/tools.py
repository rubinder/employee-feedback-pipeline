import duckdb
from typing import Dict, List, Optional
from graph import OrgGraph

class SurveyTools:
    """Tools for LangGraph agent to query survey data and org structure."""

    def __init__(self, db_path: str, org_graph: OrgGraph):
        self.conn = duckdb.connect(db_path, read_only=True)
        self.graph = org_graph

    def query_team_metrics(self, team_name: str, quarters: Optional[List[str]] = None) -> Dict:
        """Query satisfaction metrics for a team across quarters.

        Args:
            team_name: Name of the team (e.g., 'Engineering')
            quarters: List of quarters (e.g., ['Q1-2024', 'Q2-2024']) or None for all

        Returns:
            Dict with satisfaction_score, response_count, sentiment breakdown
        """
        team_name = team_name.title()  # Normalize

        if quarters:
            quarter_list = ','.join(f"'{q}'" for q in quarters)
            quarter_filter = f"and quarter in ({quarter_list})"
        else:
            quarter_filter = ""

        query = f"""
        select
            quarter,
            team,
            response_count,
            round(avg_satisfaction_score, 2) as satisfaction_score,
            round(pct_positive_sentiment * 100, 1) as pct_positive,
            round(pct_neutral_sentiment * 100, 1) as pct_neutral,
            round(pct_negative_sentiment * 100, 1) as pct_negative
        from analytics.fct_survey_metrics
        where team = '{team_name}'
        {quarter_filter}
        order by quarter
        """

        try:
            result = self.conn.execute(query).fetchall()
            if not result:
                return {'error': f'No data found for team {team_name}'}

            return {
                'team': team_name,
                'metrics': [
                    {
                        'quarter': r[1],
                        'satisfaction_score': r[3],
                        'response_count': r[2],
                        'sentiment_positive': r[4],
                        'sentiment_neutral': r[5],
                        'sentiment_negative': r[6]
                    }
                    for r in result
                ]
            }
        except Exception as e:
            return {'error': str(e)}

    def get_manager_and_team(self, name: str) -> Dict:
        """Get manager, team, and org context for an employee."""
        return self.graph.get_org_structure(name)

    def compare_quarters(self, team_name: str, quarters: List[str]) -> Dict:
        """Compare metrics across quarters to identify trends.

        Returns trend direction (improving/declining/stable) and pct change.
        """
        metrics = self.query_team_metrics(team_name, quarters)

        if 'error' in metrics:
            return metrics

        if len(metrics['metrics']) < 2:
            return {'error': 'Need at least 2 quarters for comparison'}

        scores = [m['satisfaction_score'] for m in metrics['metrics']]
        first, last = scores[0], scores[-1]
        pct_change = ((last - first) / first * 100) if first != 0 else 0

        if pct_change > 5:
            trend = 'improving'
        elif pct_change < -5:
            trend = 'declining'
        else:
            trend = 'stable'

        return {
            'team': team_name,
            'quarters': quarters,
            'trend': trend,
            'pct_change': round(pct_change, 1),
            'first_score': first,
            'last_score': last
        }

    def org_context(self, team_name: str) -> Dict:
        """Get org context for a team: members, structure, collaboration patterns."""
        team_name = team_name.title()
        members = self.graph.get_team_members(team_name)

        if not members:
            return {'error': f'Team {team_name} not found'}

        return {
            'team': team_name,
            'members': members,
            'member_count': len(members),
            'managers': [m for m in members if len(self.graph.get_peers(m)) > 0]
        }
