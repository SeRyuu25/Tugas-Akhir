from django import template
from tournaments.models import round_label

register = template.Library()

@register.simple_tag
def get_round_label(round_number, player_limit):
    return round_label(round_number, player_limit)

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