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


class Player:
    """Represents a player in the Flip 7 game."""
    
    def __init__(self, name, strategy=None):
        self.name = name
        self.total_score = 0
        self.current_hand = []
        self.round_status = "active"  # "active", "stayed", "busted"
        self.strategy = strategy if strategy is not None else Strategy()
    
    def add_card(self, card):
        """Add a card to the player's current hand."""
        if self.round_status != "active":
            return False
            
        if card in self.current_hand:
            self.round_status = "busted"
            self.current_hand.append(card)
            return False
        
        self.current_hand.append(card)
        
        # Check for Flip 7 (7 unique cards)
        if len(self.current_hand) == 7:
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