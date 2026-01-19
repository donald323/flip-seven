import json
import os
import random
from collections import defaultdict
from src.environment import Flip7Environment
from src.player import Player, Strategy


class LeaguePlayer:
    """Extended player class for league play with strategy configuration."""
    
    def __init__(self, name, strategy_config):
        self.name = name
        self.strategy_config = strategy_config
        self.strategy = Strategy(strategy_config)
        self.total_score = 0
        self.games_played = 0
        self.wins = 0
        self.total_rounds_played = 0
        self.total_points_scored = 0
        self.busts = 0
        self.stays = 0
        self.flip_7s = 0
        
    def reset_for_game(self):
        """Reset player state for a new game."""
        self.total_score = 0
        self.current_hand = []
        self.round_status = "active"
    
    def update_game_stats(self, game_winner, final_score, rounds_played, game_stats):
        """Update player statistics after a game."""
        self.games_played += 1
        self.total_rounds_played += rounds_played
        self.total_points_scored += final_score
        
        if game_winner == self.name:
            self.wins += 1
            
        # Update action stats
        if self.name in game_stats:
            stats = game_stats[self.name]
            self.busts += stats.get('busts', 0)
            self.stays += stats.get('stays', 0)
            self.flip_7s += stats.get('flip_7s', 0)
    
    def get_win_rate(self):
        """Calculate win percentage."""
        return (self.wins / self.games_played * 100) if self.games_played > 0 else 0
    
    def get_average_score(self):
        """Calculate average score per game."""
        return self.total_points_scored / self.games_played if self.games_played > 0 else 0
    
    def get_strategy_name(self):
        """Get the strategy name."""
        return self.strategy_config.get('name', 'Unknown Strategy')


class LeagueSimulation:
    """Manages a league-style tournament with multiple games."""
    
    def __init__(self, strategy_config_file, seed=None):
        self.players = []
        self.game_results = []
        self.seed = seed
        
        if seed is not None:
            random.seed(seed)
            
        self._load_strategies(strategy_config_file)
        self._create_players()
    
    def _load_strategies(self, config_file):
        """Load strategy configurations from JSON file and generate all combinations.

        Generates:
        - Single-class strategies (as-is from config)
        - Two-class combinations (one strategy from each of two distinct classes)
        - Three-class combinations (one strategy from each of all three classes)
        """
        with open(config_file, 'r') as f:
            data = json.load(f)

        self.strategies = []

        # Pull single-condition classes from configuration
        combinations = data['strategy_configurations']['combinations']
        single = combinations.get('single_condition', {})

        score_only = single.get('score_only', [])
        hand_size_only = single.get('hand_size_only', [])
        high_value_only = single.get('high_value_only', [])

        # Helper to create a unified parameters dict from selected components
        def base_probs(*configs):
            # Prefer explicit probabilities from the first config, else defaults
            for cfg in configs:
                if cfg is not None:
                    hrp = cfg.get('high_risk_probability')
                    lrp = cfg.get('low_risk_probability')
                    if hrp is not None and lrp is not None:
                        return hrp, lrp
            return 0.9, 0.1

        def combine_configs(name, score_cfg=None, hand_cfg=None, high_cfg=None):
            hrp, lrp = base_probs(score_cfg, hand_cfg, high_cfg)
            combined = {
                'name': name,
                'use_score_condition': bool(score_cfg),
                'use_hand_size_condition': bool(hand_cfg),
                'use_high_value_condition': bool(high_cfg),
                'high_risk_probability': hrp,
                'low_risk_probability': lrp,
            }
            if score_cfg:
                combined['score_threshold'] = score_cfg.get('score_threshold', 15)
            if hand_cfg:
                combined['hand_size_limit'] = hand_cfg.get('hand_size_limit', 5)
            if high_cfg:
                combined['high_value_threshold'] = high_cfg.get('high_value_threshold', 8)
                combined['high_value_limit'] = high_cfg.get('high_value_limit', 2)
            return combined

        # 1) Single-class strategies: add directly
        for s in score_only:
            self.strategies.append(combine_configs(f"Single: Score | {s.get('name','Unnamed')}", score_cfg=s))
        for h in hand_size_only:
            self.strategies.append(combine_configs(f"Single: Hand | {h.get('name','Unnamed')}", hand_cfg=h))
        for hv in high_value_only:
            self.strategies.append(combine_configs(f"Single: High | {hv.get('name','Unnamed')}", high_cfg=hv))

        # 2) Two-class combinations: one from each selected pair of classes
        # Score + Hand
        for s in score_only:
            for h in hand_size_only:
                name = f"TwoClass: Score+Hand | {s.get('name','Unnamed')} + {h.get('name','Unnamed')}"
                self.strategies.append(combine_configs(name, score_cfg=s, hand_cfg=h))

        # Score + High
        for s in score_only:
            for hv in high_value_only:
                name = f"TwoClass: Score+High | {s.get('name','Unnamed')} + {hv.get('name','Unnamed')}"
                self.strategies.append(combine_configs(name, score_cfg=s, high_cfg=hv))

        # Hand + High
        for h in hand_size_only:
            for hv in high_value_only:
                name = f"TwoClass: Hand+High | {h.get('name','Unnamed')} + {hv.get('name','Unnamed')}"
                self.strategies.append(combine_configs(name, hand_cfg=h, high_cfg=hv))

        # 3) Three-class combinations: one from each of Score, Hand, High
        for s in score_only:
            for h in hand_size_only:
                for hv in high_value_only:
                    name = (
                        f"ThreeClass: Score+Hand+High | "
                        f"{s.get('name','Unnamed')} + {h.get('name','Unnamed')} + {hv.get('name','Unnamed')}"
                    )
                    self.strategies.append(combine_configs(name, score_cfg=s, hand_cfg=h, high_cfg=hv))

        # Summary (useful for sanity checks during development)
        print(
            f"Loaded strategies: single={len(score_only)+len(hand_size_only)+len(high_value_only)}, "
            f"two_class={len(score_only)*len(hand_size_only) + len(score_only)*len(high_value_only) + len(hand_size_only)*len(high_value_only)}, "
            f"three_class={len(score_only)*len(hand_size_only)*len(high_value_only)}, "
            f"total={len(self.strategies)}"
        )
    
    def _create_players(self):
        """Create league players with unique strategies."""
        for i, strategy_config in enumerate(self.strategies):
            player_name = f"Player_{i+1:02d}_{strategy_config['name'].replace(' ', '_')}"
            league_player = LeaguePlayer(player_name, strategy_config)
            self.players.append(league_player)
        
        print(f"Created {len(self.players)} players with unique strategies")
    
    def run_single_game(self, selected_players, game_number):
        """Run a single game with selected players."""
        # Only print every 50 games to avoid slowdown
        if game_number % 50 == 1 or game_number % 50 == 0:
            print(f"\n🎮 Game {game_number}: {[p.name.split('_', 2)[-1][:15] for p in selected_players]}")
        
        # Reset players for this game
        for player in selected_players:
            player.reset_for_game()
        
        # Create Player objects for the game environment
        player_names = [p.name for p in selected_players]
        
        # Create custom environment with minimal logging for performance
        env = Flip7Environment(player_names, winning_score=200, seed=self.seed, enable_logging=False)
        
        # Replace the default players with our league players that have strategies
        for i, league_player in enumerate(selected_players):
            game_player = Player(league_player.name, league_player.strategy)
            env.game.players[i] = game_player
        
        # Run the game
        winner, rounds_played = env.run_complete_game()
        
        # Collect game statistics
        game_stats = self._extract_game_stats(env, selected_players)
        final_scores = {p.name: p.total_score for p in env.game.players}
        
        # Update player statistics
        for league_player in selected_players:
            final_score = final_scores.get(league_player.name, 0)
            league_player.update_game_stats(winner, final_score, rounds_played, game_stats)
        
        game_result = {
            'game_number': game_number,
            'players': [p.name for p in selected_players],
            'winner': winner,
            'rounds_played': rounds_played,
            'final_scores': final_scores,
            'game_stats': game_stats
        }
        
        self.game_results.append(game_result)
        # Only print winner for sampled games
        if game_number % 50 == 1 or game_number % 50 == 0:
            print(f"Winner: {winner.split('_', 2)[-1][:20]} in {rounds_played} rounds")
        
        return game_result
    
    def _extract_game_stats(self, env, selected_players):
        """Extract detailed statistics from a completed game."""
        stats = {}
        
        # Get round end logs to count actions
        round_ends = env.get_action_log(["round_end"])
        
        for player in selected_players:
            player_stats = {'stays': 0, 'busts': 0, 'flip_7s': 0}
            
            # Count from final_hands data in round_end logs
            for round_log in round_ends:
                if 'final_hands' in round_log['details']:
                    final_hands = round_log['details']['final_hands']
                    hand_info = final_hands.get(player.name, {})
                    status = hand_info.get('status', 'Unknown')
                    
                    if status == 'Stayed':
                        player_stats['stays'] += 1
                    elif status == 'Busted':
                        player_stats['busts'] += 1
                    elif status == 'Flip 7!':
                        player_stats['flip_7s'] += 1
            
            stats[player.name] = player_stats
        
        return stats
    
    def run_league(self, num_turns=20, players_per_game=5):
        """Run the complete league simulation with turn-based grouping."""
        print(f"🏆 Starting League Simulation")
        print(f"{'='*50}")
        print(f"Players: {len(self.players)}")
        print(f"Turns: {num_turns}")
        print(f"Players per game: {players_per_game}")
        print(f"Games per turn: {len(self.players) // players_per_game}")
        print(f"Total games: {num_turns * (len(self.players) // players_per_game)}")
        print(f"Random seed: {self.seed}")
        
        if len(self.players) % players_per_game != 0:
            raise ValueError(f"Player count ({len(self.players)}) must be divisible by players per game ({players_per_game})")
        
        games_per_turn = len(self.players) // players_per_game
        game_counter = 0
        
        for turn_num in range(1, num_turns + 1):
            print(f"\n🔄 TURN {turn_num}/{num_turns}")
            print("-" * 30)
            
            # Shuffle the player pool for this turn
            shuffled_players = self.players.copy()
            random.shuffle(shuffled_players)
            
            # Create groups of 5 players each
            for group_num in range(games_per_turn):
                start_idx = group_num * players_per_game
                end_idx = start_idx + players_per_game
                group_players = shuffled_players[start_idx:end_idx]
                
                game_counter += 1
                print(f"  Game {game_counter}: Group {group_num + 1}")
                
                # Run the game for this group
                self.run_single_game(group_players, game_counter)
        
        print(f"\n🎉 League Complete!")
        print(f"Total turns: {num_turns}")
        print(f"Total games played: {len(self.game_results)}")
        print(f"Each player participated in: {num_turns} games")
        
        return self.generate_leaderboard()
    
    def generate_leaderboard(self):
        """Generate comprehensive leaderboard and statistics."""
        # Sort players by wins (primary) and average score (secondary)
        sorted_players = sorted(
            self.players, 
            key=lambda p: (p.wins, p.get_average_score()), 
            reverse=True
        )
        
        leaderboard = {
            'rankings': [],
            'summary_stats': self._calculate_summary_stats()
        }
        
        print(f"\n🏆 FINAL LEADERBOARD")
        print(f"{'='*100}")
        print(f"{'Rank':<4} {'Player':<35} {'Wins':<5} {'Games':<5} {'Win%':<6} {'Avg Score':<9} {'Strategy':<25}")
        print(f"{'-'*100}")
        
        for rank, player in enumerate(sorted_players, 1):
            strategy_short = player.get_strategy_name()[:24]
            
            player_data = {
                'rank': rank,
                'name': player.name,
                'wins': player.wins,
                'games_played': player.games_played,
                'win_percentage': player.get_win_rate(),
                'average_score': player.get_average_score(),
                'total_points': player.total_points_scored,
                'total_rounds': player.total_rounds_played,
                'busts': player.busts,
                'stays': player.stays,
                'flip_7s': player.flip_7s,
                'strategy': player.get_strategy_name()
            }
            
            leaderboard['rankings'].append(player_data)
            
            print(f"{rank:<4} {player.name:<35} {player.wins:<5} {player.games_played:<5} "
                  f"{player.get_win_rate():<6.1f} {player.get_average_score():<9.1f} {strategy_short:<25}")
        
        return leaderboard
    
    def _calculate_summary_stats(self):
        """Calculate overall league statistics."""
        total_games = len(self.game_results)
        total_rounds = sum(result['rounds_played'] for result in self.game_results)
        
        # Strategy performance analysis
        strategy_wins = defaultdict(int)
        strategy_games = defaultdict(int)
        
        for player in self.players:
            strategy_name = player.get_strategy_name()
            strategy_wins[strategy_name] += player.wins
            strategy_games[strategy_name] += player.games_played
        
        strategy_performance = []
        for strategy, wins in strategy_wins.items():
            games = strategy_games[strategy]
            win_rate = (wins / games * 100) if games > 0 else 0
            strategy_performance.append({
                'strategy': strategy,
                'wins': wins,
                'games': games,
                'win_rate': win_rate
            })
        
        strategy_performance.sort(key=lambda x: x['win_rate'], reverse=True)
        
        return {
            'total_games': total_games,
            'total_rounds': total_rounds,
            'average_rounds_per_game': total_rounds / total_games if total_games > 0 else 0,
            'strategy_performance': strategy_performance[:10]  # Top 10 strategies
        }
    
    def print_detailed_stats(self, leaderboard):
        """Print detailed statistics and analysis."""
        print(f"\n📊 DETAILED LEAGUE STATISTICS")
        print(f"{'='*60}")
        
        summary = leaderboard['summary_stats']
        print(f"Total games played: {summary['total_games']}")
        print(f"Total rounds played: {summary['total_rounds']}")
        print(f"Average rounds per game: {summary['average_rounds_per_game']:.1f}")
        
        print(f"\n🎯 Top 10 Strategy Performance (by win rate):")
        print(f"{'-'*60}")
        for i, strategy in enumerate(summary['strategy_performance'], 1):
            print(f"{i:2}. {strategy['strategy']:<35} {strategy['win_rate']:5.1f}% "
                  f"({strategy['wins']}/{strategy['games']})")
        
        # Most successful players
        top_players = leaderboard['rankings'][:5]
        print(f"\n🏆 Top 5 Players:")
        print(f"{'-'*60}")
        for player in top_players:
            print(f"{player['rank']}. {player['name']}: {player['wins']} wins, "
                  f"{player['win_percentage']:.1f}% win rate, {player['average_score']:.1f} avg score")
    
    def export_results(self, filename="league_results.json", include_game_details=False):
        """Export league results to JSON file.
        
        Args:
            filename: Output filename
            include_game_details: If True, includes all individual game results (large file)
                                 If False, only exports summary statistics (minimal file)
        """
        leaderboard = self.generate_leaderboard()
        
        results = {
            'league_info': {
                'total_players': len(self.players),
                'total_games': len(self.game_results),
                'seed': self.seed,
                'export_mode': 'full' if include_game_details else 'summary'
            },
            'leaderboard': leaderboard
        }
        
        # Only include detailed game results if requested
        if include_game_details:
            results['game_results'] = self.game_results
        
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
        
        file_size_kb = os.path.getsize(filename) / 1024
        print(f"\n💾 Results exported to: {filename} ({file_size_kb:.1f} KB)")
        return filename


def main():
    """Run a sample league simulation."""
    # Create and run league
    league = LeagueSimulation('strategy_configurations.json', seed=42)
    leaderboard = league.run_league(num_turns=20, players_per_game=5)
    
    # Print detailed statistics
    league.print_detailed_stats(leaderboard)
    
    # Export results
    league.export_results()


if __name__ == "__main__":
    main()