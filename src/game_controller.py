import random
from .player import Player


class GameController:
    """Controls the Flip 7 game flow and logic."""
    
    def __init__(self, player_names, winning_score=200):
        self.players = [Player(name) for name in player_names]
        self.winning_score = winning_score
        self.deck = []
        self.discard_pile = []
        self.current_dealer_index = 0
        self.round_number = 1
        self.game_winner = None
        self._create_deck()
    
    def _create_deck(self):
        """Create a deck with number cards 0-12, quantities matching their values, plus modifier cards."""
        self.deck = []
        for number in range(13):  # 0 through 12
            if number == 0:
                self.deck.append(0)  # Only 1 card of value 0
            else:
                self.deck.extend([number] * number)  # n cards of value n
        
        # Add modifier cards (one of each)
        self.deck.extend(['+2', '+4', '+6', '+8', '+10', 'x2'])
        random.shuffle(self.deck)
    
    def _reshuffle_if_needed(self):
        """Reshuffle discard pile into deck if deck is empty."""
        if not self.deck and self.discard_pile:
            self.deck = self.discard_pile.copy()
            self.discard_pile = []
            random.shuffle(self.deck)
    
    def start_new_round(self):
        """Start a new round of the game."""
        if self.game_winner:
            return False
        
        # Reset all players for new round
        for player in self.players:
            player.current_hand = []
            player.round_status = "active"
        
        return True
    
    def deal_card_to_player(self, player):
        """Deal one card to a specific player."""
        self._reshuffle_if_needed()
        
        if not self.deck:
            return None
        
        card = self.deck.pop()
        success = player.add_card(card)
        return card if success else None
    
    def get_active_players(self):
        """Get list of players still active in the current round."""
        return [p for p in self.players if p.is_active()]
    
    def is_round_over(self):
        """Check if the current round is over."""
        active_players = self.get_active_players()
        
        # Round is over if no players are active, or someone got Flip 7
        if not active_players:
            return True
        
        # Check if any player got Flip 7
        for player in self.players:
            if player.round_status == "flip_7":
                return True
        
        return False
    
    def end_round(self):
        """End the current round and calculate scores."""
        round_results = {}
        
        # Collect all played cards to discard pile
        for player in self.players:
            self.discard_pile.extend(player.current_hand)
            round_score = player.end_round()
            round_results[player.name] = round_score
        
        # Check for game winner
        for player in self.players:
            if player.has_won_game(self.winning_score):
                self.game_winner = player
                break
        
        # Move to next dealer
        self.current_dealer_index = (self.current_dealer_index + 1) % len(self.players)
        self.round_number += 1
        
        return round_results
    
    def get_current_dealer(self):
        """Get the current dealer."""
        return self.players[self.current_dealer_index]
    
    def get_game_state(self):
        """Get current game state summary."""
        return {
            "round_number": self.round_number,
            "dealer": self.get_current_dealer().name,
            "players": [(p.name, p.total_score, p.get_status_display(), p.current_hand) 
                       for p in self.players],
            "active_players": len(self.get_active_players()),
            "game_winner": self.game_winner.name if self.game_winner else None,
            "deck_size": len(self.deck),
            "discard_pile_size": len(self.discard_pile)
        }
    
    def is_game_over(self):
        """Check if the game is over."""
        return self.game_winner is not None
    
    def get_leaderboard(self):
        """Get players sorted by total score."""
        return sorted(self.players, key=lambda p: p.total_score, reverse=True)
    
    def can_player_hit(self, player):
        """Check if a player can take another card."""
        return player.is_active() and not self.is_round_over()
    
    def player_hit(self, player_name):
        """Player chooses to hit (take another card)."""
        player = self._get_player_by_name(player_name)
        if not player or not self.can_player_hit(player):
            return None
        
        return self.deal_card_to_player(player)
    
    def player_stay(self, player_name):
        """Player chooses to stay."""
        player = self._get_player_by_name(player_name)
        if not player:
            return False
        
        return player.stay()
    
    def _get_player_by_name(self, name):
        """Get player object by name."""
        for player in self.players:
            if player.name == name:
                return player
        return None
    
    def get_round_summary(self):
        """Get a summary of the current round."""
        summary = []
        for player in self.players:
            round_score = player.calculate_round_score()
            summary.append({
                "name": player.name,
                "hand": player.current_hand,
                "status": player.get_status_display(),
                "round_score": round_score,
                "total_score": player.total_score
            })
        return summary