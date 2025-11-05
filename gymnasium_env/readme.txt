požadavky viz requirements.txt

důležité soubory
test_ppo.py - testovaci soubor, v komentářích v kódu je popsáno jak spustit jednotlivé natrénované modely
train_ppo.py - pro trénování
main.py - spustí prostředí s náhodnými akcemi, pouze pro ověření správnosti instalace

env/base_env.py - metoda _step_low_level - modifikací proměné reward dle proměny lze upravovat odměny které agent dostane
více instrukcí na případné modifikace jsou popsány v oficialní dokumentaic gymnasium - https://gymnasium.farama.org/tutorials/gymnasium_basics/

většina modelů z práce je plně spustitelná viz. test_ppo
výjimkou je náhodné 5x5 prostředí - funkčně je identické, trénováno jak low level tak i high level přidání i nepřátelé, odměny jsou však jinak nastaveny, lze je však dle tabulek v práci přenastavit
cnn a dqn testování se nachází ve složce old_builds, jedná se však o starší verze a jsou tak přidána spíše pro úplnost 

vytvoreni vlastní mapy - pridat do slozky level_layouts
S - start pozice
E - prvek prostředí, blokuje pohyb
# - zed
B - bonus
M - nepratelska postava
G - cíl
R - dmg tile
. - prázné pole
A - náhodné (dmg,bonus,nepritel)

vysledna mapa musí být v obdélníkovém tvaru
