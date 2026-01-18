"""
Flip 7 League Championship Simulation

This script runs a comprehensive league tournament with all 35 available strategies.
Each strategy plays as a unique player across 20 games with random matchmaking.
"""

from src.league_simulation import LeagueSimulation

def run_championship():
    """Run the Flip 7 League Championship."""
    print("🏆 FLIP 7 LEAGUE CHAMPIONSHIP")
    print("="*50)
    print("Loading strategies and setting up tournament...")
    
    # Create league with all strategies
    league = LeagueSimulation('config/strategy_configurations.json', seed=42)
    
    print(f"✅ {len(league.players)} players registered")
    print("🎮 Starting tournament...")
    
    # Run 20 games with 5 players each
    leaderboard = league.run_league(num_games=20, players_per_game=5)
    
    # Show detailed results
    league.print_detailed_stats(leaderboard)
    
    # Export results
    filename = league.export_results("flip7_championship_results.json")
    
    print(f"\n🎉 Championship Complete!")
    print(f"🏆 Champion: {leaderboard['rankings'][0]['name']}")
    print(f"📊 Strategy: {leaderboard['rankings'][0]['strategy']}")
    print(f"🎯 Performance: {leaderboard['rankings'][0]['wins']} wins, {leaderboard['rankings'][0]['win_percentage']:.1f}% win rate")
    print(f"💾 Full results saved to: {filename}")

if __name__ == "__main__":
    run_championship()