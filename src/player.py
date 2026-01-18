import random


def calculate_hand_score(hand, include_flip7_bonus=False, is_busted=False):
    """Calculate the score for a given hand.
    
    Args:
        hand: List of cards (integers and/or string modifiers like 'x2', '+5')
        include_flip7_bonus: Whether to add the Flip 7 bonus (15 points)
        is_busted: If True, returns 0 regardless of hand
        
    Returns:
        int: The calculated score
        
    Scoring rules:
    1. Sum all number cards.
    2. If an 'x2' card is present, it doubles ONLY the sum of number cards.
    3. All '+N' modifier cards are then added on top (NOT doubled).
    4. The Flip 7 bonus is added after these steps (NOT affected by 'x2').
    """
    if is_busted:
        return 0
    
    # Separate number cards from modifier cards
    number_cards = [card for card in hand if isinstance(card, int)]
    modifier_cards = [card for card in hand if isinstance(card, str)]
    
    # Sum number cards
    score = sum(number_cards)
    
    # Apply x2 multiplier to number cards if present
    if 'x2' in modifier_cards:
        score *= 2
    
    # Add +N modifiers (not multiplied by x2)
    for modifier in modifier_cards:
        if modifier.startswith('+'):
            try:
                score += int(modifier[1:])
            except ValueError:
                continue
    
    # Add Flip 7 bonus if applicable
    if include_flip7_bonus:
        score += 15
    
    return score


class Strategy:
    """Base strategy class for Flip 7 game decisions."""
    
    def __init__(self, parameters=None):
        """Initialize strategy with optional parameters."""
        self.parameters = parameters
    
    def should_stay(self, player_hand, parameters=None):
        """Determine whether a player should stay based on their current hand.
        
        Args:
            player_hand: List of cards currently in the player's hand
            parameters: Optional parameters to override default behavior
            
        Returns:
            bool: True if player should stay, False if they should hit
        """
        # Use instance parameters if no parameters provided
        if parameters is None:
            parameters = self.parameters
            
        if parameters is None:
            # Default strategy: stay if score is high or hand is getting risky
            current_score = calculate_hand_score(player_hand)
            
            # Hand size based only on number cards
            number_cards = [card for card in player_hand if isinstance(card, int)]
            hand_size = len(number_cards)
            
            # Stay conditions:
            # 1. Score is already decent (15+ points)
            # 2. Hand has 5+ number cards (getting risky)
            # 3. Has high-value number cards that might duplicate
            high_value_cards = [card for card in number_cards if card >= 8]
            
            if current_score >= 15 or hand_size >= 5 or len(high_value_cards) >= 2:
                stay_probability = 0.9
            else:
                stay_probability = 0.1
            
            return random.random() < stay_probability
        
        # Parameterized strategy
        current_score = calculate_hand_score(player_hand)
        
        # Hand size and high-value checks based only on number cards
        number_cards = [card for card in player_hand if isinstance(card, int)]
        hand_size = len(number_cards)
        high_value_cards = [card for card in number_cards if card >= parameters.get('high_value_threshold', 8)]
        
        # Check which conditions are enabled
        conditions_met = []
        
        if parameters.get('use_score_condition', False):
            score_threshold = parameters.get('score_threshold', 15)
            if current_score >= score_threshold:
                conditions_met.append('score')
                
        if parameters.get('use_hand_size_condition', False):
            hand_size_limit = parameters.get('hand_size_limit', 5)
            if hand_size >= hand_size_limit:
                conditions_met.append('hand_size')
                
        if parameters.get('use_high_value_condition', False):
            high_value_limit = parameters.get('high_value_limit', 2)
            if len(high_value_cards) >= high_value_limit:
                conditions_met.append('high_value')
        
        # Determine stay probability based on conditions met
        if conditions_met:
            stay_probability = parameters.get('high_risk_probability', 0.9)
        else:
            stay_probability = parameters.get('low_risk_probability', 0.1)
        
        return random.random() < stay_probability
    
    def decide_freeze_target(self, player, opponents):
        """Decide who to freeze (risk-manipulation strategy).
        Frozen player is set to 'stayed' status and is no longer active in the round.
        
        Args:
            player: Current player object
            opponents: Dict of {player_id: player_object} for all other active players
        
        Returns:
            player_id to freeze, or None
        """
        # Priority 1: Freeze players WITH Second Chance (lock them with safety net unused)
        # If multiple have Second Chance, choose the one with smallest hand value
        players_with_sc = {opp_id: opp for opp_id, opp in opponents.items() if opp.second_chance_count > 0}
        
        if players_with_sc:
            min_hand_value = float('inf')
            target = None
            for opp_id, opp in players_with_sc.items():
                hand_value = sum([c for c in opp.current_hand if isinstance(c, int)])
                if hand_value < min_hand_value:
                    min_hand_value = hand_value
                    target = opp_id
            return target
        
        # Priority 2: Freeze player with smallest hand value (deny safe progress)
        min_hand_value = float('inf')
        target = None
        for opp_id, opp in opponents.items():
            hand_value = sum([c for c in opp.current_hand if isinstance(c, int)])
            if hand_value < min_hand_value:
                min_hand_value = hand_value
                target = opp_id
        
        return target
    
    def decide_flip3_target(self, player, opponents):
        """Decide who to use Flip Three on (risk-manipulation strategy).
        FLIP3 must be used when drawn - this only decides the target.
        
        Args:
            player: Current player object
            opponents: Dict of {player_id: player_object} for all other active players
        
        Returns:
            target_player_id (opponent) or None (for self)
        """
        # Target players with HIGH hand values (likely to bust on 3 forced draws)
        max_hand_value = 0
        target = None
        
        if opponents:
            for opp_id, opp in opponents.items():
                hand_value = sum([c for c in opp.current_hand if isinstance(c, int)])
                if hand_value > max_hand_value:
                    max_hand_value = hand_value
                    target = opp_id
            return target
        
        return None  # Use on self
    
    def decide_second_chance_giveaway(self, player, opponents):
        """Decide whether to give away Second Chance (risk-manipulation strategy).
        
        Args:
            player: Current player object
            opponents: Dict of {player_id: player_object} for all other active players
        
        Returns:
            (action: str, target_player_id or None)
            action can be: 'keep', 'give', or 'discard'
        """
        # Check if all active players (including self) already have second chance
        all_have_sc = player.second_chance_count > 0 and all(opp.second_chance_count > 0 for opp in opponents.values())
        
        if all_have_sc:
            return ('discard', None)  # All players have SC, must discard
        
        if player.second_chance_count == 0:
            return ('keep', None)  # Keep it - don't have one yet
        
        # At this point, not all players have SC and player.second_chance_count > 0
        # Give to opponent with SMALLEST hand (waste it on safe players)
        # Only consider opponents who don't have second chance yet
        candidates = {opp_id: opp for opp_id, opp in opponents.items() if opp.second_chance_count == 0}
        
        if not candidates:
            # All opponents have SC, must discard
            return ('discard', None)
        
        min_hand_value = float('inf')
        target = None
        for opp_id, opp in candidates.items():
            hand_value = sum([c for c in opp.current_hand if isinstance(c, int)])
            if hand_value < min_hand_value:
                min_hand_value = hand_value
                target = opp_id
        return ('give', target)
        
        return ('keep', None)


class Player:
    """Represents a player in the Flip 7 game."""
    
    def __init__(self, name, strategy=None):
        self.name = name
        self.total_score = 0
        self.current_hand = []
        self.round_status = "active"  # "active", "stayed", "busted"
        self.strategy = strategy if strategy is not None else Strategy()
        self.second_chance_count = 0
    
    def add_card(self, card):
        """Add a card to the player's current hand."""
        if self.round_status != "active":
            return False
        
        # Action cards are handled separately, not added to hand
        if card in ['FREEZE', 'FLIP3', 'SECOND_CHANCE']:
            return True  # Action cards trigger effects but don't go in hand
            
        if card in self.current_hand:
            # Check for Second Chance
            if self.second_chance_count > 0:
                self.second_chance_count -= 1
                # Don't add duplicate card, don't bust
                return True  # Second Chance used successfully
            else:
                self.round_status = "busted"
                self.current_hand.append(card)
                return False
        
        self.current_hand.append(card)
        
        # Check for Flip 7 (7 unique number cards)
        number_cards = [c for c in self.current_hand if isinstance(c, int)]
        if len(number_cards) == 7:
            self.round_status = "flip_7"
        
        return True
    
    def stay(self):
        """Player chooses to stay and bank their current points."""
        if self.round_status == "active":
            self.round_status = "stayed"
            return True
        return False
    
    def calculate_round_score(self):
        """Calculate the score for the current round."""
        is_flip7 = self.round_status == "flip_7"
        is_busted = self.round_status == "busted"
        return calculate_hand_score(self.current_hand, include_flip7_bonus=is_flip7, is_busted=is_busted)
    
    def end_round(self):
        """End the round and add points to total score."""
        round_score = self.calculate_round_score()
        self.total_score += round_score
        
        # Reset for next round
        self.current_hand = []
        self.round_status = "active"
        self.second_chance_count = 0
        
        return round_score
    
    def is_active(self):
        """Check if player is still active in the current round."""
        return self.round_status == "active"
    
    def has_won_game(self, winning_score=200):
        """Check if player has won the game."""
        return self.total_score >= winning_score
    
    def should_stay(self):
        """Get strategy decision based on current hand."""
        return self.strategy.should_stay(self.current_hand, self.strategy.parameters)
    
    def get_status_display(self):
        """Get a human-readable status for display."""
        status_map = {
            "active": "Active",
            "stayed": "Stayed",
            "busted": "Busted",
            "flip_7": "Flip 7!"
        }
        return status_map.get(self.round_status, "Unknown")
    
    def __str__(self):
        return f"{self.name}: {self.total_score} points, Hand: {self.current_hand}, Status: {self.get_status_display()}"