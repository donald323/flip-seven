"""
League Results Visualization Module

Creates charts and graphs to analyze league performance and strategy effectiveness.
"""

import matplotlib.pyplot as plt
import json
from collections import defaultdict
import numpy as np

class LeagueVisualizer:
    """Visualizes league simulation results."""
    
    def __init__(self, results_file):
        """Load results from JSON file."""
        with open(results_file, 'r') as f:
            self.data = json.load(f)
        
        self.leaderboard = self.data['leaderboard']['rankings']
        self.game_results = self.data['game_results']
        self.summary_stats = self.data['leaderboard']['summary_stats']
    
    def plot_win_distribution(self):
        """Plot distribution of wins across all players."""
        plt.figure(figsize=(12, 6))
        
        wins = [player['wins'] for player in self.leaderboard]
        names = [player['name'].split('_', 2)[-1][:20] for player in self.leaderboard]
        
        # Create bar plot
        bars = plt.bar(range(len(wins)), wins, alpha=0.7)
        
        # Color top performers differently
        for i, bar in enumerate(bars):
            if i < 5:  # Top 5
                bar.set_color('gold')
            elif i < 10:  # Top 10
                bar.set_color('silver')
            else:
                bar.set_color('lightblue')
        
        plt.xlabel('Players (Strategy Names)')
        plt.ylabel('Total Wins')
        plt.title('Win Distribution Across All Players')
        plt.xticks(range(len(names)), names, rotation=90, ha='right')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
    
    def plot_strategy_performance(self):
        """Plot strategy performance analysis."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Strategy win rates
        strategy_data = self.summary_stats['strategy_performance'][:15]  # Top 15
        strategies = [s['strategy'][:20] for s in strategy_data]
        win_rates = [s['win_rate'] for s in strategy_data]
        
        bars1 = ax1.bar(range(len(strategies)), win_rates, alpha=0.7, color='skyblue')
        ax1.set_xlabel('Strategy')
        ax1.set_ylabel('Win Rate (%)')
        ax1.set_title('Top 15 Strategy Win Rates')
        ax1.set_xticks(range(len(strategies)))
        ax1.set_xticklabels(strategies, rotation=45, ha='right')
        ax1.grid(True, alpha=0.3)
        
        # Win distribution histogram
        all_wins = [player['wins'] for player in self.leaderboard]
        ax2.hist(all_wins, bins=10, alpha=0.7, color='lightgreen', edgecolor='black')
        ax2.set_xlabel('Number of Wins')
        ax2.set_ylabel('Number of Players')
        ax2.set_title('Distribution of Wins')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def plot_score_analysis(self):
        """Plot scoring analysis."""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Average score vs wins scatter plot
        avg_scores = [player['average_score'] for player in self.leaderboard]
        wins = [player['wins'] for player in self.leaderboard]
        
        ax1.scatter(avg_scores, wins, alpha=0.6, s=50)
        ax1.set_xlabel('Average Score per Game')
        ax1.set_ylabel('Total Wins')
        ax1.set_title('Average Score vs Total Wins')
        ax1.grid(True, alpha=0.3)
        
        # Add trend line
        z = np.polyfit(avg_scores, wins, 1)
        p = np.poly1d(z)
        ax1.plot(avg_scores, p(avg_scores), "r--", alpha=0.8)
        
        # Top performers average scores
        top_10 = self.leaderboard[:10]
        top_names = [p['name'].split('_', 2)[-1][:15] for p in top_10]
        top_scores = [p['average_score'] for p in top_10]
        
        bars2 = ax2.bar(range(len(top_names)), top_scores, alpha=0.7, color='orange')
        ax2.set_xlabel('Top 10 Players')
        ax2.set_ylabel('Average Score per Game')
        ax2.set_title('Top 10 Players - Average Scores')
        ax2.set_xticks(range(len(top_names)))
        ax2.set_xticklabels(top_names, rotation=45, ha='right')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def plot_action_analysis(self):
        """Plot action analysis (stays, busts, flip 7s)."""
        plt.figure(figsize=(15, 8))
        
        # Get top 15 players for cleaner visualization
        top_players = self.leaderboard[:15]
        names = [p['name'].split('_', 2)[-1][:15] for p in top_players]
        stays = [p['stays'] for p in top_players]
        busts = [p['busts'] for p in top_players]
        flip_7s = [p['flip_7s'] for p in top_players]
        
        x = np.arange(len(names))
        width = 0.25
        
        plt.bar(x - width, stays, width, label='Stays', alpha=0.8, color='green')
        plt.bar(x, busts, width, label='Busts', alpha=0.8, color='red')
        plt.bar(x + width, flip_7s, width, label='Flip 7s', alpha=0.8, color='gold')
        
        plt.xlabel('Top 15 Players')
        plt.ylabel('Total Actions')
        plt.title('Action Distribution - Top 15 Players')
        plt.xticks(x, names, rotation=45, ha='right')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.show()
    
    def plot_game_progression(self):
        """Plot how scores and winners evolved throughout the tournament."""
        game_numbers = []
        avg_scores = []
        max_scores = []
        rounds_played = []
        
        for game in self.game_results:
            game_numbers.append(game['game_number'])
            scores = list(game['final_scores'].values())
            avg_scores.append(np.mean(scores))
            max_scores.append(max(scores))
            rounds_played.append(game['rounds_played'])
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # Score progression
        ax1.plot(game_numbers, avg_scores, 'b-o', label='Average Score', alpha=0.7)
        ax1.plot(game_numbers, max_scores, 'r-s', label='Winning Score', alpha=0.7)
        ax1.set_xlabel('Game Number')
        ax1.set_ylabel('Score')
        ax1.set_title('Score Progression Throughout Tournament')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Rounds progression
        ax2.plot(game_numbers, rounds_played, 'g-^', alpha=0.7)
        ax2.set_xlabel('Game Number')
        ax2.set_ylabel('Rounds to Complete')
        ax2.set_title('Game Length Progression')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def generate_all_plots(self):
        """Generate all visualization plots."""
        print("📊 Generating League Visualization Plots...")
        
        self.plot_win_distribution()
        self.plot_strategy_performance()
        self.plot_score_analysis()
        self.plot_action_analysis()
        self.plot_game_progression()
        
        print("✅ All plots generated!")

def visualize_championship(results_file="flip7_championship_results.json"):
    """Create visualizations for championship results."""
    visualizer = LeagueVisualizer(results_file)
    visualizer.generate_all_plots()

if __name__ == "__main__":
    # Run visualization on default results file
    visualize_championship()