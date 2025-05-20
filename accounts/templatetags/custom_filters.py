from django import template

register = template.Library()

@register.filter
def mask_email(value):
    if value:
        local_part, domain_part = value.split('@')

        # Handle different local part lengths
        local_length = len(local_part)
        
        if local_length == 1:
            # Fully mask if local part has 1 character
            masked_local = '*'  
        elif local_length == 2:
            # Show first character, mask second character
            masked_local = local_part[0] + '*'
        elif local_length == 3:
            # Show first and last character, mask middle character
            masked_local = local_part[0] + '*' + local_part[2]
        else:
            # Show first and last character, mask middle part for local part > 3
            masked_local = local_part[0] + '***' + local_part[-1]
        
        # Combine the masked local part with the domain
        return f"{masked_local}@{domain_part}"
    return value
