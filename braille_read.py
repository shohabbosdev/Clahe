import json
from math import fabs

with open('braille.json', 'r') as f:
    data = json.load(f)

def hamming_distance(bi, ci):
    return sum([int(fabs(bi[i] - ci[i])) for i in range(6)])

def find_braille_matches(input_code):
    matches_0 = []
    matches_1 = []
    matches_2 = []
    
    for char, code in data.items():
        distance = hamming_distance(input_code, code)
        if distance == 0:
            matches_0.append(char)
        elif distance == 1:
            matches_1.append(char)
        elif distance == 2:
            matches_2.append(char)
    
    return matches_0, matches_1, matches_2

# CNN modelidan chiqqan misol kod (dinamik kiritish uchun)
input_code = [1, 0, 0, 1, 1, 1]  # Masalan, "f" harfi

# Hamming masofasiga ko'ra belgilarni topish
matches_0, matches_1, matches_2 = find_braille_matches(input_code)

# Natijani chiqarish
print("Hamming masofasi ≤ 2 bo'lgan belgilar:")
if matches_0:
    print(f"Masofa 0: {'", "'.join(matches_0)} ([{', '.join(map(str, data[matches_0[0]]))}]).")
if matches_1:
    print(f"Masofa 1: {'", "'.join(matches_1)}.")
if matches_2:
    print(f"Masofa 2: {'", "'.join(matches_2)}.")