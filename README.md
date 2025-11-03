# Using-machine-learning-to-control-a-computer-game
Diplomová práce


Využití strojového učení pro ovládání počítačové hry

Tato diplomová práce se zabývá využitím algoritmů strojového učení pro ovládání autonomního agenta ve vlastním herním prostředí. V teoretické části jsou popsány principy strojového učení se zaměřením na učení s posilováním (Reinforcementlearning – RL), jeho algoritmy (zejména Proximal Policy Optimization – PPO), využitív praxi, strukturu odměn, výzvy spojené s RL a možná vývojová prostředí. Praktická část zahrnuje návrh a implementaci tahové strategické hry v Pythonu (Pygame) propojené s knihovnami Gymnasium a Stable Baselines 3 pro vývoj RL. Bylo testováno více konfigurací prostředí – statická, náhodně generovaná i kombinovaná– a různé úrovně složitosti včetně přítomnosti nepřátel. Experimenty ukázaly, žeklíčem k úspěchu je jednoduchý a konzistentní odměnový systém, dostatek cílů, curriculum learning a omezený počet relevantních akcí. Testováno bylo využití hlavně PPO algoritmu. Dále byly zkoušeny tzv. high-level akce, které zapouzdřovalyzákladní pohyby a zvýšily tak efektivitu navigace. Výsledky potvrzují, že RL jev herním kontextu použitelný, vyžaduje však pečlivý návrh prostředí a odměn.

Podrobnější informace na https://theses.cz/id/j421ye/?isshlret=Franti%C5%A1ek%3BMacho%C5%88%3B;zpet=%2Fvyhledavani%2F%3Fsearch%3Dfranti%C5%A1ek%20macho%C5%88%26start%3D1

Složky ke hře a machine learning projektu na https://drive.google.com/drive/folders/1Fjq0vu3WXMbzL-3Dl0ELUWi0VG8XaHpz
