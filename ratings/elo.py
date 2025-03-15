# Buat perhitungan ELO Rating

"""
Buat ngitung Expected Score Atlet A terhadap Atlet B.
"""
def calculate_expected_score(rating_a, rating_b):
    return 1 / (1 + 10 ** ((rating_b - rating_a) / 400))


"""
Buat update ELO rating Atlet A.
score_a buat hasil pertandingan A, 1 buat menang & 0 buat kalah.
Return nya yaitu new rating Atlet A setelah adjustment.
"""
def update_elo(rating_a, rating_b, score_a, k=32):
    expected_a = calculate_expected_score(rating_a, rating_b)
    new_rating_a = rating_a + k * (score_a - expected_a)
    return round(new_rating_a)


"""
Buat process hasil 1 pertandingan (bukan 1 turnament).
score1 & score2 angka hasil pertandingannya.
Return nya yaitu new ELO rating buat Atlet 1 & Atlet 2.
"""
def process_match(athlete1_profile, athlete2_profile, score1, score2):
    # Buat nentuin hasil pertandingan, siapa yang menang
    if score1 > score2:
        outcome1, outcome2 = 1, 0
    elif score1 < score2:
        outcome1, outcome2 = 0, 1
    else:
        outcome1 = outcome2 = 0.5  # Draw -> harusnya ga ada si

    new_rating1 = update_elo(athlete1_profile.current_rating, athlete2_profile.current_rating, outcome1)
    new_rating2 = update_elo(athlete2_profile.current_rating, athlete1_profile.current_rating, outcome2)
    
    # Return nya yaitu new ELO rating buat kedua atlet
    return new_rating1, new_rating2
