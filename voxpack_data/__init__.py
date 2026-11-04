"""Les données de Vox-Pack : langues, textes, listes de phrases de départ.

Ce paquet ne contient que des données et des fonctions pures (aucun Tk,
aucun réseau au chargement). L'application l'importe normalement ; il n'y a
donc ni dossier à joindre à la main, ni chemin ajouté à `sys.path`.

- `langues.py` : les quinze langues d'EdgeTX (nom, dossier SD, voix
  officielle, allure). Vérifiable contre la recette officielle :
  `python -m voxpack_data.langues`.
- `textes.py` : les textes de l'interface, une table par langue.
- `aide.py` : le corps de l'aide (57 clés) dans les douze langues qui
  n'avaient que l'interface ; fusionné par `textes.py` comme un lot.
- `listes-base/` : un CSV `nom;phrase` par langue, pour la liste de départ.
"""
