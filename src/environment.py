import random
from src.game_controller import GameController
from src.player import Player


class Flip7Environment:
    """Environment class for running Flip 7 game simulations with logging."""
    
    def __init__(self, player_names, winning_score=200, seed=None, enable_logging=True):
        self.game = GameController(player_names, winning_score)
        self.game_log = []
        self.round_logs = []
        self.action_count = 0
        self.enable_logging = enable_logging
        
        if seed is not None:
            random.seed(seed)
        
        if self.enable_logging:
            self._log_action("game_start", {
                "players": player_names,
                "winning_score": winning_score,
                "seed": seed
            })
    
    def _log_action(self, action_type, details):
        """Log an action with timestamp and details."""
        if not self.enable_logging:
            return
        self.action_count += 1
        log_entry = {
            "action_id": self.action_count,
            "action_type": action_type,
            "round": self.game.round_number,
            "details": details
        }
        self.game_log.append(log_entry)
    
    def _get_opponents_dict(self, current_player):
        """Get dictionary of opponent players (excluding current player)."""
        opponents = {}
        for i, p in enumerate(self.game.players):
            if p.name != current_player.name and p.is_active():
                opponents[i] = p
        return opponents
    
    def _handle_freeze_card(self, player):
        """Handle Freeze action card."""
        opponents = self._get_opponents_dict(player)
        
        if not opponents:
            self._log_action("freeze_card", {
                "player": player.name,
                "target": None,
                "reason": "No active opponents"
            })
            return
        
        # Use strategy to decide target
        target_id = player.strategy.decide_freeze_target(player, opponents)
        
        if target_id is not None and target_id in opponents:
            target_player = opponents[target_id]
            target_player.round_status = "stayed"  # Freeze = force stay
            
            self._log_action("freeze_card", {
                "player": player.name,
                "target": target_player.name,
                "status": "stayed"
            })
    
    def _handle_flip3_card(self, player):
        """Handle Flip Three action card. FLIP3 must be used when drawn.
        If target busts or achieves Flip 7 during FLIP3, drawing stops immediately."""
        opponents = self._get_opponents_dict(player)
        
        # Use strategy to decide initial target (opponent or self)
        target_id = player.strategy.decide_flip3_target(player, opponents)
        
        # Determine target player
        if target_id is None:
            target_player = player  # Use on self
        elif target_id in opponents:
            target_player = opponents[target_id]
        else:
            target_player = player  # Default to self
        
        # Draw up to 3 cards for target
        cards_drawn = []
        
        for _ in range(3):
            # Stop if target is no longer active (busted, flip_7, or stayed)
            if not target_player.is_active():
                break
            
            card = self.game.deal_card_to_player(target_player)
            if card is not None:
                cards_drawn.append(card)
        
        self._log_action("flip3_card", {
            "player": player.name,
            "target": target_player.name,
            "cards_drawn": cards_drawn,
            "total_cards": len(cards_drawn),
            "target_status": target_player.get_status_display()
        })
    
    def _handle_second_chance_card(self, player):
        """Handle Second Chance action card."""
        opponents = self._get_opponents_dict(player)
        
        # Use strategy to decide whether to keep, give away, or discard
        action, target_id = player.strategy.decide_second_chance_giveaway(player, opponents)
        
        if action == 'discard':
            # All active players have second chance, discard the card
            self._log_action("second_chance_card", {
                "player": player.name,
                "action": "discarded",
                "reason": "All active players already have Second Chance"
            })
        elif action == 'keep':
            # Keep it for self
            player.second_chance_count += 1
            self._log_action("second_chance_card", {
                "player": player.name,
                "action": "kept",
                "second_chance_count": player.second_chance_count
            })
        elif action == 'give':
            # Give to opponent
            if target_id is not None and target_id in opponents:
                target_player = opponents[target_id]
                target_player.second_chance_count += 1
                
                self._log_action("second_chance_card", {
                    "player": player.name,
                    "action": "gave_away",
                    "target": target_player.name,
                    "target_second_chance_count": target_player.second_chance_count
                })
            else:
                # No valid target, keep it
                player.second_chance_count += 1
                self._log_action("second_chance_card", {
                    "player": player.name,
                    "action": "kept",
                    "reason": "No valid target",
                    "second_chance_count": player.second_chance_count
                })
    
    def run_single_round(self):
        """Run a single round with logging."""
        round_start_log = {
            "round_number": self.game.round_number,
            "dealer": self.game.get_current_dealer().name,
            "initial_state": self.game.get_game_state()
        }
        self._log_action("round_start", round_start_log)
        
        if not self.game.start_new_round():
            return False
        
        # Deal initial cards to all players
        for player in self.game.players:
            card = self.game.deal_card_to_player(player)
            if card is not None:
                self._log_action("card_dealt", {
                    "player": player.name,
                    "card": card,
                    "hand": player.current_hand.copy(),
                    "status": player.get_status_display()
                })
        
        # Continue until round is over
        turn_count = 0
        while not self.game.is_round_over() and turn_count < 100:  # Safety limit
            turn_count += 1
            active_players = self.game.get_active_players()
            
            if not active_players:
                break
            
            self._log_action("turn_start", {
                "turn": turn_count,
                "active_players": [p.name for p in active_players]
            })
            
            # Each active player makes a decision
            for player in active_players[:]:  # Copy list to avoid iteration issues
                if not player.is_active():
                    continue
                
                # Player decides to hit or stay using their strategy
                should_stay = player.should_stay()
                
                if should_stay:
                    success = self.game.player_stay(player.name)
                    self._log_action("player_stay", {
                        "player": player.name,
                        "hand": player.current_hand.copy(),
                        "round_score": player.calculate_round_score()
                    })
                else:
                    # Player hits
                    # Track Second Chance count BEFORE the draw
                    previous_second_chance_count = player.second_chance_count
                    
                    card = self.game.player_hit(player.name)
                    
                    if card is not None:
                        # Handle action cards
                        if card == 'FREEZE':
                            self._handle_freeze_card(player)
                        elif card == 'FLIP3':
                            self._handle_flip3_card(player)
                        elif card == 'SECOND_CHANCE':
                            self._handle_second_chance_card(player)
                        else:
                            # Regular card was successfully added
                            # Check if Second Chance was used (count decreased but still active)
                            second_chance_used = (previous_second_chance_count > player.second_chance_count 
                                                 and player.is_active())
                            
                            if second_chance_used:
                                self._log_action("second_chance_used", {
                                    "player": player.name,
                                    "duplicate_card": card,
                                    "second_chances_remaining": player.second_chance_count
                                })
                            
                            self._log_action("player_hit", {
                                "player": player.name,
                                "card_drawn": card,
                                "hand": player.current_hand.copy(),
                                "status": player.get_status_display()
                            })
                            
                            # Check for Flip 7
                            if player.round_status == "flip_7":
                                self._log_action("flip_7_achieved", {
                                    "player": player.name,
                                    "winning_hand": player.current_hand.copy(),
                                    "bonus_points": 15
                                })
                    else:
                        # card is None means player busted (add_card returned False)
                        self._log_action("player_busted", {
                            "player": player.name,
                            "duplicate_card": player.current_hand[-1] if player.current_hand else "unknown",
                            "final_hand": player.current_hand.copy()
                        })
        
        # End round and calculate scores
        # Capture final hands before round ends
        current_round_number = self.game.round_number  # Capture before increment
        final_hands = {}
        for player in self.game.players:
            final_hands[player.name] = {
                "hand": player.current_hand.copy(),
                "status": player.get_status_display(),
                "round_score": player.calculate_round_score()
            }
        
        round_results = self.game.end_round()
        
        # Log with the correct round number (before increment)
        log_entry = {
            "action_id": self.action_count + 1,
            "action_type": "round_end",
            "round": current_round_number,
            "details": {
                "round_results": round_results,
                "final_hands": final_hands,
                "final_state": self.game.get_game_state()
            }
        }
        self.action_count += 1
        self.game_log.append(log_entry)
        
        return True
    
    def run_complete_game(self):
        """Run a complete game until someone wins."""
        game_start_state = self.game.get_game_state()
        self._log_action("game_simulation_start", game_start_state)
        
        rounds_played = 0
        max_rounds = 50  # Safety limit
        
        while not self.game.is_game_over() and rounds_played < max_rounds:
            self.run_single_round()
            rounds_played += 1
        
        # Log final game state
        final_state = self.game.get_game_state()
        leaderboard = self.game.get_leaderboard()
        
        self._log_action("game_end", {
            "winner": final_state["game_winner"],
            "rounds_played": rounds_played,
            "final_scores": [(p.name, p.total_score) for p in leaderboard],
            "final_state": final_state
        })
        
        return final_state["game_winner"], rounds_played
    
    def get_game_summary(self):
        """Get a summary of the completed game."""
        if not self.game.is_game_over():
            return "Game not yet completed"
        
        leaderboard = self.game.get_leaderboard()
        winner = self.game.game_winner
        
        summary = {
            "winner": winner.name if winner else "No winner",
            "winning_score": winner.total_score if winner else 0,
            "rounds_played": self.game.round_number - 1,
            "total_actions": len(self.game_log),
            "final_standings": [(p.name, p.total_score) for p in leaderboard]
        }
        
        return summary
    
    def get_action_log(self, action_types=None):
        """Get filtered action log."""
        if action_types is None:
            return self.game_log
        
        if isinstance(action_types, str):
            action_types = [action_types]
        
        return [log for log in self.game_log if log["action_type"] in action_types]
    
    def print_game_summary(self):
        """Print a formatted game summary."""
        summary = self.get_game_summary()
        print(f"🎮 FLIP 7 GAME SUMMARY")
        print(f"{'='*40}")
        print(f"🏆 Winner: {summary['winner']}")
        print(f"🎯 Winning Score: {summary['winning_score']}")
        print(f"🔄 Rounds Played: {summary['rounds_played']}")
        print(f"📝 Total Actions: {summary['total_actions']}")
        print(f"\n📊 Final Standings:")
        for i, (name, score) in enumerate(summary['final_standings'], 1):
            print(f"  {i}. {name}: {score} points")