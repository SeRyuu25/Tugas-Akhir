from django import template
from tournaments.models import round_label
from ratings.models import RatingHistory
from django.utils.safestring import mark_safe

register = template.Library()

@register.simple_tag
def get_round_label(round_number, player_limit):
    return round_label(round_number, player_limit)

@register.filter
def get_attr(obj, attr_name):
    """
    Retrieve attribute by name (for dynamic field access):
      {{ match|get_attr:"set1_p1" }}
    """
    return getattr(obj, attr_name, None)

@register.filter
def get_final_round(player_limit):
    """
    Returns the round number for the final based on the player limit.
    """
    if player_limit == 8:
        return 3  # Final round for 8 players
    elif player_limit == 16:
        return 4  # Final round for 16 players
    else:
        return 0  # Fallback (should not happen)
    
@register.filter
def get_rating(match, athlete):
    try:
        return match.ratinghistory_set.get(athlete=athlete)
    except RatingHistory.DoesNotExist:
        return None
    
@register.filter
def sets_won(match, athlete):
    """Return how many sets that athlete won in this match."""
    return match.total_sets_won(athlete)

@register.filter
def get_loser(match):
    """Return the losing athlete for a match."""
    # Ensure there is a winner before trying to find a loser
    winner = match.winner() # First, determine the winner

    # If there is no winner yet, we can't determine a loser
    if not winner:
        return None

    # Now, check who the winner is and return the other player
    if winner == match.athlete1:
        # If athlete1 won, then athlete2 is the loser
        return match.athlete2
    else:
        # Otherwise, if athlete2 won, then athlete1 is the loser
        return match.athlete1

@register.filter
def form_field(form, field_name):
    """
    Given a bound form and a field-name string, return the BoundField.
    Usage: {{ form|form_field:field_name }}
    """
    return form[field_name]