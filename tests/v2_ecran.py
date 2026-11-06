"""Contrôles de l'écran v2, sans réseau et sans toucher aux données de Richard.

    python tests/v2_ecran.py

Le script se donne un dossier personnel temporaire (HOME) pour que la liste
et les réglages de l'utilisateur ne soient ni lus ni écrits. Il ouvre la
fenêtre, la retire aussitôt, vérifie ce qui peut l'être sans œil humain,
puis la détruit.

Ce qui est vérifié : la fenêtre sans barre de titre, les objets que le
moteur attend (liste, compteur, barre, boutons, curseurs), les lignes
chargées, l'ajout et la suppression, le menu, le changement de langue, et
le fait qu'un clic sur un curseur ne déplace pas la fenêtre.
"""

import json
import os
import sys
import threading
import tkinter as tk
import tempfile
import time

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RACINE)

# Données de test : surtout pas ~/Documents/Vox-Pack (HOME sous macOS,
# USERPROFILE sous Windows — voir isolement.py).
from isolement import isoler  # noqa: E402

DOSSIER = isoler()

# Un réglage volontairement hors de l'ancienne borne ±50 : il doit être relu
# tel quel, puisque le curseur ALLURE va de -100 à +100.
os.makedirs(os.path.join(DOSSIER, "Documents", "Vox-Pack"), exist_ok=True)
with open(os.path.join(DOSSIER, "Documents", "Vox-Pack", "reglages.json"),
          "w", encoding="utf-8") as fichier:
    json.dump({"langue_ui": "fr", "allure": 80, "niveau": 0}, fichier)

import voxpack2  # noqa: E402

ECHECS = []


def verifier(nom, condition, detail=""):
    if condition:
        print(f"  ok    {nom}")
    else:
        print(f"  ÉCHEC {nom} {detail}")
        ECHECS.append(nom)


def main() -> int:
    app = voxpack2.VoxPackApp()
    app.withdraw()
    app.update()

    print("Réglages")
    verifier("l'allure 80 % est relue telle quelle", app._allure == 80,
             f"({app._allure})")
    verifier("le curseur d'allure va de -100 à +100",
             (app._allure_v2._mini, app._allure_v2._maxi) == (-100, 100),
             f"({app._allure_v2._mini}, {app._allure_v2._maxi})")

    print("Fenêtre")
    verifier("sans barre de titre", bool(app.overrideredirect()))
    # La taille dépend de l'écran (820 au plus, moins sur un écran court) :
    # on vérifie qu'elle est carrée et égale à celle que l'écran a calculée,
    # pas une valeur fixe — sinon le test échouerait sur un PC 1366 x 768.
    # winfo_width() donne la taille RÉELLE ; geometry() est une chaîne que
    # customtkinter réécrit parfois avec son échelle. Le 3 novembre, le test
    # annonçait 972 x 972 pour une fenêtre de 648 : c'était la chaîne, pas la
    # fenêtre.
    verifier("fenêtre carrée à la taille calculée",
             (app.winfo_width(), app.winfo_height())
             == (app._format, app._format),
             f"({app.winfo_width()}x{app.winfo_height()}, "
             f"format {app._format})")
    print(f"        écran {app.winfo_screenwidth()}x{app.winfo_screenheight()}"
          f" | fenêtre {app.winfo_width()}x{app.winfo_height()}"
          f" | format {app._format}")
    # Le 5 novembre, `overrideredirect(True)` recréait la fenêtre et lui
    # faisait perdre sa géométrie : elle s'ouvrait en haut à gauche (34, 96
    # sur un écran 2560 x 1440). On vérifie le centre, avec une tolérance
    # pour les arrondis de Tk et les écrans Windows à l'échelle.
    attendu_x = max((app.winfo_screenwidth() - app._format) // 2, 0)
    attendu_y = max((app.winfo_screenheight() - app._format) // 2 - 15, 0)
    verifier("la fenêtre est centrée",
             abs(app.winfo_x() - attendu_x) <= 12
             and abs(app.winfo_y() - attendu_y) <= 12,
             f"({app.winfo_x()}, {app.winfo_y()}) "
             f"au lieu de ({attendu_x}, {attendu_y})")
    verifier("pastille de fermeture", getattr(app, "_pastille", None)
             is not None and app._pastille.winfo_exists())
    verifier("bouton de menu", getattr(app, "_bouton_menu", None)
             is not None and app._bouton_menu.winfo_exists())

    print("Objets attendus par le moteur")
    for nom in ("lignes", "_toile", "_barre", "progress", "lbl_compteur",
                "lbl_etat", "combo_voice", "btn_ajouter", "btn_supprimer",
                "btn_apercu", "btn_letsgo", "lbl_col_nom", "lbl_col_phrase",
                "lbl_robot", "_boutons_robot", "btn_aide", "_champ_langue"):
        verifier(nom, hasattr(app, nom))

    print("Liste")
    verifier("des lignes sont chargées", len(app.lignes) > 0, len(app.lignes))
    # Le 5 novembre, une erreur de découpage avait laissé la liste chargée
    # mais jamais dessinée : la fenêtre s'ouvrait sur une liste vide. Ce
    # contrôle-ci le voit, alors que « des lignes sont chargées » ne le
    # voyait pas.
    verifier("la liste est dessinée dès l'ouverture",
             len(app._toile.find_all()) > 0, len(app._toile.find_all()))
    verifier("le nom est rempli", bool(app.lignes[0]["nom"]))
    verifier("la phrase est remplie", bool(app.lignes[0]["texte"]))
    avant = len(app.lignes)
    app.ajouter_ligne()
    app.update()
    verifier("ajouter une ligne", len(app.lignes) == avant + 1)
    verifier("la ligne ajoutée est active", bool(app.lignes[-1]["coche"]))
    # Elle est cochée d'office : « Supprimer » la prend sans autre geste.
    app.supprimer_selection()
    app.update()
    verifier("supprimer la ligne", len(app.lignes) == avant)

    print("Variables Tk")
    # Une variable abandonnée au ramasse-miettes pouvait être détruite depuis
    # le fil réseau (« main thread is not in main loop », vu sur le PC le
    # 3 novembre). L'application garde donc celles qui restent.
    verifier("la variable du menu Langue est retenue",
             app._var_langue_ui in app._variables)
    verifier("la liste ne retient plus une variable par ligne",
             not any(isinstance(v, tk.BooleanVar) for v in app._variables),
             [type(v).__name__ for v in app._variables])

    print("Compteur et barre")
    verifier("compteur au repos",
             "/" in app.lbl_compteur.itemcget(app.lbl_compteur._item, "text"))
    app._total_v2 = 10
    app.progress.set(0.5)
    fin = time.time() + 1.2
    while time.time() < fin:
        app.update()
        time.sleep(0.02)
    verifier("le compteur suit la barre",
             app.lbl_compteur.itemcget(app.lbl_compteur._item, "text")
             == "5 / 10")

    print("Jauge")
    hauteur = app.progress._hauteur
    verifier("les couleurs sont celles de la jauge du matin",
             (app.progress.JAUGE, app.progress.OMBRE,
              app.progress.ESPACE) == ("#FF0D00", "#324C51", 1),
             (app.progress.JAUGE, app.progress.OMBRE,
              app.progress.ESPACE))
    if app.progress._image_mode:
        motif = app.progress._motifs
        verifier("le rond est plein, symétrique et de la hauteur de la fente",
                 len(motif) == hauteur
                 and all(len(ligne) == hauteur for ligne in motif)
                 and all(ligne == ligne[::-1] for ligne in motif)
                 and motif == motif[::-1],
                 motif)
        verifier("l'image de la jauge fait exactement la taille du canevas",
                 app.progress._photo is not None
                 and app.progress._photo.width() == app.progress._largeur
                 and app.progress._photo.height() == hauteur,
                 (app.progress._photo.width(), app.progress._photo.height()))
    else:
        verifier("les ronds sont répartis sur toute la largeur",
                 len(app.progress._ronds) > 1
                 and app.progress._places[-1] > app.progress._largeur * 0.9,
                 len(app.progress._ronds))
        verifier("le premier rond est centré dans la fente",
                 abs(app.progress._places[0] - hauteur / 2) <= 1,
                 app.progress._places[0])
    app.progress.set(0.5)
    fin = time.time() + 1.0
    while time.time() < fin:
        app.update()
        time.sleep(0.02)
    verifier("seuls les ronds faits sont dessinés",
             0 < app.progress._allumes < len(app.progress._ronds),
             app.progress._allumes)
    if not app.progress._image_mode:
        verifier("le premier rond est allumé, le dernier éteint",
                 app.progress.itemcget(app.progress._ronds[0],
                                       "fill").lower()
                 == app.progress.JAUGE.lower()
                 and app.progress.itemcget(app.progress._ronds[-1],
                                           "fill").lower()
                 == app.progress.CREUX.lower(),
                 (app.progress.itemcget(app.progress._ronds[0], "fill"),
                  app.progress.itemcget(app.progress._ronds[-1], "fill")))

    print("File d'attente des fils")
    # Un fil de travail ne doit jamais appeler Tk directement : il dépose
    # dans la file, et le fil principal exécute. C'est ce qui évite le gel
    # quand une fenêtre ouvre une boucle modale pendant une génération.
    def travail():
        for i in range(50):
            app._dire(f"fil {i}")
        app._poster(app.progress.set, 0.25)

    fil = threading.Thread(target=travail)
    fil.start()
    fil.join()
    fin = time.time() + 1.0
    while time.time() < fin:
        app.update()
        time.sleep(0.01)
    verifier("un fil de travail met la ligne d'état à jour",
             app.lbl_etat.cget("text") == "fil 49",
             app.lbl_etat.cget("text"))
    verifier("la file d'attente est vidée", app._ui_queue.empty())

    print("Géométrie")
    # Ces trois contrôles ont été ajoutés après un essai Windows où la liste
    # débordait sur le bandeau « Let's Go » : customtkinter appliquait sa
    # propre échelle DPI par-dessus une mise en page en pixels.
    verifier("le fond fait la taille de la fenêtre",
             app._fond_image.size == (app._format, app._format),
             f"({app._fond_image.size} pour {app._format})")
    liste = app._toile
    verifier("la liste a la hauteur prévue",
             liste.winfo_height() == app._pv(538),
             f"({liste.winfo_height()} au lieu de {app._pv(538)})")
    verifier("la bande est sous la liste",
             app.btn_letsgo.winfo_y() >= app._pv(794),
             f"({app.btn_letsgo.winfo_y()} pour un seuil de {app._pv(794)})")
    verifier("le bas de la fenêtre est libre",
             app.btn_letsgo.winfo_y() + app.btn_letsgo.winfo_height()
             <= app._format,
             f"({app.btn_letsgo.winfo_y()} + {app.btn_letsgo.winfo_height()}"
             f" pour {app._format})")

    print("Aide")
    app._ouvrir_aide()
    app.update()
    fenetres = [w for w in app.winfo_children() if isinstance(w, tk.Toplevel)]
    aide = fenetres[-1] if fenetres else None
    verifier("l'aide s'ouvre", aide is not None)
    if aide is not None:
        croix = []

        def chercher(widget):
            for enfant in widget.winfo_children():
                if (isinstance(enfant, tk.Label)
                        and str(enfant.cget("text")) == "×"):
                    croix.append(enfant)
                chercher(enfant)

        chercher(aide)
        verifier("la croix de fermeture est là", bool(croix))
        if croix:
            # Ce qu'on reproduit : fermer l'aide au clic laissait la fenêtre
            # principale en état de déplacement, et elle suivait la souris.
            app._deplacement = (app.winfo_x(), app.winfo_y())
            croix[0].event_generate("<Button-1>", x=2, y=2)
            app.update()
            verifier("fermer l'aide ne laisse pas la fenêtre collée",
                     app._deplacement is None, f"({app._deplacement})")

    print("Aide : avertissement de traduction")
    for code in ("ja", "tw", "hk"):
        app.changer_langue_ui(code)
        app.update()
        # Ces deux titres étaient restés en français dans les captures
        # anglaises et allemandes de la v2.
        verifier(f"{code} : le titre LANGUE est traduit",
                 app._titre_langue.itemcget(app._titre_langue._item, "text")
                 == voxpack2.t("langue").upper())
        verifier(f"{code} : le titre VOIX est traduit",
                 app._titre_voix.itemcget(app._titre_voix._item, "text")
                 == voxpack2.t("voix").upper())
        # On repère l'aide par la fenêtre qui vient de s'ouvrir, et non par
        # « la dernière de la liste » : sous Windows, l'ordre des fenêtres
        # rendues par winfo_children() n'est pas celui de leur création, et
        # une autre fenêtre (alerte de mise à jour) peut s'inviter entre-temps.
        # C'est ce qui faisait échouer le test sur `hk` alors que l'aide
        # s'ouvrait parfaitement à la main (Richard, 3 novembre).
        avant = {str(fenetre) for fenetre in app.winfo_children()
                 if isinstance(fenetre, tk.Toplevel)}
        app._ouvrir_aide()
        app.update()
        nouvelles = [fenetre for fenetre in app.winfo_children()
                     if isinstance(fenetre, tk.Toplevel)
                     and str(fenetre) not in avant]

        def texte_de(fenetre):
            morceaux = []

            def ramasser(widget):
                for enfant in widget.winfo_children():
                    if isinstance(enfant, tk.Text):
                        morceaux.append(enfant.get("1.0", "end"))
                    ramasser(enfant)

            ramasser(fenetre)
            return "".join(morceaux)

        # L'aide est celle qui porte du texte ; une alerte n'en a pas.
        aide = None
        for fenetre in nouvelles:
            if texte_de(fenetre):
                aide = fenetre
        contenu = texte_de(aide) if aide is not None else ""
        verifier(f"{code} : l'avertissement est dans l'aide",
                 voxpack2.AVERTISSEMENT_AIDE[code] in contenu,
                 f"(nouvelles fenêtres : {len(nouvelles)}, "
                 f"longueurs : {[len(texte_de(f)) for f in nouvelles]})")
        if aide is not None:
            aide.destroy()
            app.update()
    app.changer_langue_ui("fr")
    app.update()

    print("Robots")
    app._robot = 0
    app._maj_robot()
    app._choisir_robot(1)
    app.update()
    verifier("le robot choisi allume sa led",
             app._boutons_robot[1]._allume
             and not any(app._boutons_robot[n]._allume for n in (2, 3, 4)))
    verifier("les voyants sont cyan sauf HAL",
             all(app._boutons_robot[n]._c["allume"] != "#FF3B30"
                 for n in (1, 2, 3))
             and app._boutons_robot[4]._c["allume"] == "#FF3B30")
    app._choisir_robot(1)
    app.update()
    verifier("un second clic éteint la led",
             not app._boutons_robot[1]._allume)

    print("Déplacement")
    # Ce qu'on reproduit : un mouvement « bouton enfoncé » arrive alors que le
    # bouton est physiquement relâché (capture restée accrochée). La fenêtre
    # ne doit pas bouger, et l'état doit se solder.
    avant = app.geometry()
    app._deplacement = (app.winfo_x(), app.winfo_y())
    # On force « bouton relâché » : la vraie fonction interroge le système, et
    # l'essai échouait si quelqu'un tenait la souris à ce moment-là.
    vrai_enfonce = voxpack2.bouton_enfonce
    voxpack2.bouton_enfonce = lambda: False
    try:
        app.event_generate("<B1-Motion>", x=40, y=40, state=0x100)
        app.update()
    finally:
        voxpack2.bouton_enfonce = vrai_enfonce
    verifier("un mouvement sans bouton ne déplace pas la fenêtre",
             app.geometry() == avant and app._deplacement is None,
             f"({app.geometry()} au lieu de {avant}, "
             f"état {app._deplacement})")

    print("Bouton Arrêter")
    bouton = app.btn_letsgo
    bouton.dire("Stop", arret=True)
    verifier("l'icône stop est dessinée", len(bouton._icone_items) == 1)
    bouton.dire(voxpack2.t("lets_go"), arret=False)
    verifier("l'icône disparaît au repos", not bouton._icone_items)

    apercu = app.btn_apercu
    apercu.dire("Stop", arret=True)
    verifier("l'aperçu prend l'icône stop",
             bool(apercu._icone_items)
             and apercu.type(apercu._icone_items[0]) == "rectangle")
    apercu.dire(voxpack2.t("ecouter"), arret=False)
    verifier("l'aperçu reprend l'icône lecture",
             bool(apercu._icone_items)
             and apercu.type(apercu._icone_items[0]) == "polygon")

    print("Clavier désactivé")
    # Décision de Richard (4 novembre au soir) : plus de parcours clavier.
    # Un liseré apparaissait sans raison, et rien de tout cela ne sert quand
    # on travaille à la souris. Ce qui compte, c'est que plus rien ne prenne
    # le focus : ni les boutons dessinés, ni la liste, ni les menus.
    bouton = app.btn_ajouter
    verifier("un bouton dessiné ne prend pas le focus",
             str(bouton.cget("takefocus")) in ("", "0"),
             bouton.cget("takefocus"))
    verifier("aucune touche n'est liée sur un bouton dessiné",
             not any(bouton.bind(touche) for touche in
                     ("<Return>", "<KP_Enter>", "<space>")))
    verifier("le liseré de clavier a disparu",
             not hasattr(bouton, "_focus")
             and not hasattr(voxpack2.BoutonV2, "FOCUS"))

    print("Liste dessinée")
    # Le test est passé par le japonais et le chinois : on revient au
    # français, et l'échec dira dans quelle langue on se trouvait.
    app.changer_langue_ui("fr")
    app.update()
    verifier("quarante-quatre lignes en français", len(app.lignes) == 44,
             f"{len(app.lignes)} lignes en {voxpack2.LANGUE_UI}")
    objets = len(app._toile.find_all())
    verifier("plusieurs objets de canevas par ligne",
             objets >= 5 * len(app.lignes), objets)
    debut_dessin = time.perf_counter()
    app._dessiner_liste()
    duree_dessin = (time.perf_counter() - debut_dessin) * 1000
    verifier("redessiner les quarante-quatre lignes prend moins de 100 ms",
             duree_dessin < 100, "%.1f ms" % duree_dessin)
    app._editer_ligne(0, 1)
    verifier("un clic ouvre un vrai champ", app._edition is not None)
    entree = app._edition[2]
    entree.delete(0, "end")
    entree.insert(0, "phrase corrigée")
    app._valider_edition()
    verifier("le champ écrit dans la liste",
             app.lignes[0]["texte"] == "phrase corrigée")
    verifier("le champ se referme après validation",
             app._edition is None and not app._toile.find_withtag("edition"))
    app._editer_ligne(0, 1)
    app._edition[2].delete(0, "end")
    app._edition[2].insert(0, "autre chose")
    app._annuler_edition()
    verifier("Échap jette la saisie",
             app.lignes[0]["texte"] == "phrase corrigée")

    # Le message de nom doit suivre la frappe, comme dans la 1.5.1. On ne
    # réécrit pas la liste pour autant : le contrôle en direct ne touche
    # qu'au dessin de la ligne.
    app._editer_ligne(1, 0)
    entree = app._edition[2]
    entree.delete(0, "end")
    entree.insert(0, "beaucouptroplong")
    app._verifier_nom_live(1)
    app.update()
    verifier("le message de nom suit la frappe",
             "caractères" in app.lignes[1]["souci"], app.lignes[1]["souci"])
    entree.delete(0, "end")
    entree.insert(0, "court")
    app._verifier_nom_live(1)
    app.update()
    verifier("le message disparaît quand le nom redevient valide",
             app.lignes[1]["souci"] == "", app.lignes[1]["souci"])
    app._annuler_edition()

    # Sous Windows, un champ créé juste après un clic sur un bouton dessiné
    # ne recevait rien : « focus_set » ne fait rien quand la fenêtre n'est pas
    # encore la fenêtre active du système. C'est « focus_force » qui sauve.
    vrai_set = voxpack2.tk.Entry.focus_set
    vrai_force = voxpack2.tk.Entry.focus_force
    forces = []
    # La fenêtre du test est retirée : le vrai focus ne peut pas être pris.
    # On vérifie donc l'appel — c'est lui qui manquait sous Windows.
    voxpack2.tk.Entry.focus_set = lambda self: None
    voxpack2.tk.Entry.focus_force = lambda self: forces.append(self)
    try:
        app._editer_ligne(1, 0)
        app.update()
        verifier("le champ redemande le clavier même si focus_set échoue",
                 len(forces) == 1, len(forces))
        echo_focus = []
        vrai_rendre = app._toile.focus_set
        app._toile.focus_set = lambda: echo_focus.append(True)
        try:
            app._valider_edition()
        finally:
            app._toile.focus_set = vrai_rendre
        verifier("fermer un champ rend le focus à la liste",
                 bool(echo_focus), len(echo_focus))
    finally:
        voxpack2.tk.Entry.focus_set = vrai_set
        voxpack2.tk.Entry.focus_force = vrai_force

    print("Bouton de l'aperçu")
    bouton = app.btn_apercu
    bouton._pointer_dedans = False
    bouton.dire(voxpack2.t("arreter"), arret=True)
    app._fin_apercu()
    app.update()
    verifier("la fin de l'aperçu remet le bouton sur « Écouter »",
             bouton._texte_brut == voxpack2.t("ecouter"),
             bouton._texte_brut)

    print("Liste : plus de clavier")
    verifier("la liste ne prend pas le focus",
             str(app._toile.cget("takefocus")) in ("", "0"),
             app._toile.cget("takefocus"))
    verifier("la liste n'a plus de touches de navigation",
             not any(app._toile.bind(touche) for touche in
                     ("<Tab>", "<Shift-Tab>", "<Up>", "<Down>",
                      "<Prior>", "<Next>", "<Home>", "<End>")))
    print("Flèches dans la liste")
    app._toile.yview_moveto(0.0)
    app.update_idletasks()
    app._fleche_liste(1)
    app.update_idletasks()
    verifier("une flèche bas fait défiler d'une ligne",
             abs(app._toile.canvasy(0) - app._hauteur_ligne) < 1,
             app._toile.canvasy(0))
    app._fleche_liste(-1)
    app.update_idletasks()
    verifier("une flèche haut remonte d'une ligne",
             abs(app._toile.canvasy(0)) < 1, app._toile.canvasy(0))
    app._editer_ligne(1, 0)
    avant = app._toile.canvasy(0)
    app._fleche_liste(1)
    verifier("les flèches ne défilent pas pendant une saisie",
             abs(app._toile.canvasy(0) - avant) < 1)
    app._annuler_edition()
    # Ne doit pas lever d'erreur quand la liste n'est pas affichée.
    app._montrer_ligne(len(app.lignes) - 1)
    verifier("le suivi de la ligne supporte une liste non affichée", True)

    print("Menu")
    app._ouvrir_menu_fenetre()
    app.update()
    lignes = app._menu_lignes
    verifier("le menu s'ouvre sur ses sept entrées", len(lignes) == 7,
             len(lignes))
    verifier("les entrées du menu ne prennent pas le focus",
             all(str(ligne.cget("takefocus")) in ("", "0")
                 for ligne in lignes))
    verifier("les entrées du menu répondent au clic",
             all(ligne.bind("<Button-1>") for ligne in lignes))
    app._fermer_menus()
    app.update()
    verifier("refermer le menu vide sa liste d'entrées",
             not app._menu_lignes)

    # Le passage dans une autre application : on simule la réponse du
    # système au lieu de cliquer ailleurs — un test ne doit pas voler le
    # clavier à celui qui le lance.
    vraie_reponse = voxpack2.application_activee
    voxpack2.application_activee = lambda fenetre: False
    try:
        app._ouvrir_menu_fenetre()
        app.update()
        app._veiller_activation()
        app.update()
        verifier("le menu se referme quand l'application passe derrière",
                 app._menu_habillage is None)
        verifier("la surveillance s'arrête avec le menu",
                 not app._veille_active, app._veille_active)
    finally:
        voxpack2.application_activee = vraie_reponse

    print("Fenêtre des langues")
    prises = []
    fenetre = voxpack2.FenetreLanguesV2(app, "fr", prises.append)
    # La langue courante se marque par son cadre cyan, et rien d'autre : le
    # liseré blanc du clavier restait affiché en permanence (vu le 5
    # novembre au matin, alors que le parcours clavier est retiré).
    bordures = {str(cellule.cget("highlightbackground")).upper()
                for cellule, _titre, _detail, _bord in fenetre._cellules}
    verifier("la langue courante est marquée",
             fenetre.ACCENT.upper() in bordures, bordures)
    verifier("aucun cadre blanc ne reste affiché",
             "#FFFFFF" not in bordures, bordures)
    verifier("les cellules ne prennent pas le focus",
             all(str(cellule[0].cget("takefocus")) in ("", "0")
                 for cellule in fenetre._cellules))
    verifier("aucune touche de navigation n'est liée aux cellules",
             not any(fenetre._cellules[0][0].bind(touche) for touche in
                     ("<Return>", "<Left>", "<Right>", "<Up>", "<Down>")))
    # Le geste qui reste : le clic.
    fenetre._prendre("it")
    verifier("un clic choisit la langue", prises == ["it"], prises)
    app.update()
    try:
        existe = fenetre.winfo_exists()
    except tk.TclError:
        existe = False
    verifier("la fenêtre se referme après le choix", not existe)

    # Le PC de Richard (Windows 10) refuse « ISO_Left_Tab » : lier ce nom
    print("Fenêtre de confirmation")
    app._message("C'est fait.", icone="succes", boutons=[("Compris", None)])
    app.update()
    alerte = app._alertes[-1] if app._alertes else None
    verifier("la confirmation s'ouvre et reste suivie", alerte is not None)
    # Le cas du Mac : la petite fenêtre sans cadre ne prend pas le clavier,
    # Échap arrive donc à la fenêtre principale. Ce chemin doit la fermer.
    app._echapper()
    app.update()
    try:
        vivante = alerte.winfo_exists()
    except tk.TclError:
        vivante = False
    verifier("Échap ferme la confirmation", not vivante)
    verifier("la confirmation fermée sort de la liste", not app._alertes,
             len(app._alertes))

    # Le clavier ayant été retiré, plus rien ne lie « ISO_Left_Tab » : le
    # piège du 3 novembre (ce nom X11 n'existe pas sous Windows, le lier
    # levait une TclError et l'application ne démarrait pas) ne peut plus se
    # reproduire. On garde la vérification qu'une ligne s'ajoute.
    print("Ajout d'une ligne")
    avant = len(app.lignes)
    app._ajouter_ligne_ui("essai", "phrase d'essai")
    app._dessiner_liste()
    verifier("une ligne s'ajoute toujours", len(app.lignes) == avant + 1)

    print("Changement de langue pendant une saisie")
    # Deux listes distinctes, puis une saisie non validée dans la première.
    # Le 5 novembre, changer de langue à ce moment-là écrivait la liste
    # française dans le fichier anglais et effaçait la liste anglaise.
    with open(voxpack2.chemin_liste("en"), "w", encoding="utf-8") as fichier:
        fichier.write("english-one,My English phrase\n")
    app.changer_langue_ui("fr")
    app.update()
    app._editer_ligne(0, 1)
    app.update()
    entree = app._edition[2]
    entree.delete(0, "end")
    entree.insert(0, "saisie non validée")
    app.changer_langue_ui("en")
    app.update()
    contenu_en = open(voxpack2.chemin_liste("en"), encoding="utf-8").read()
    contenu_fr = open(voxpack2.chemin_liste("fr"), encoding="utf-8").read()
    verifier("changer de langue n'écrase pas l'autre liste",
             "english-one" in contenu_en, contenu_en[:60])
    verifier("la saisie en cours est enregistrée dans sa langue",
             "saisie non validée" in contenu_fr)
    app.changer_langue_ui("fr")
    app.update()

    print("Aide unique")
    app._ouvrir_aide()
    app.update()
    aide = app._aide
    app._ouvrir_aide()
    app.update()
    verifier("un second appel ne crée pas une deuxième aide",
             app._aide is aide,
             f"({app._aide} au lieu de {aide})")
    app.focus_force()
    app.update()
    app.event_generate("<Escape>")
    app.update()
    time.sleep(0.1)
    app.update()
    try:
        vivante = aide.winfo_exists()
    except tk.TclError:
        vivante = False
    verifier("Échap ferme l'aide depuis la fenêtre principale", not vivante)

    print("Menu des voix")
    voxpack2.VOIX["en"] = list(voxpack2.VOIX_ORIGINE["en"])
    app.changer_langue_ui("en")
    app.update()
    app.combo_voice._clic()
    app.update()
    panneau = app.combo_voice._panneau
    canevas = app.combo_voice._canevas
    verifier("le menu des voix tient dans la fenêtre",
             panneau is not None
             and panneau.winfo_y() + panneau.winfo_height()
             <= app.winfo_height(),
             f"({panneau.winfo_y()}+{panneau.winfo_height()} "
             f"pour {app.winfo_height()})" if panneau is not None else "")
    verifier("le menu des dix-neuf voix défile", canevas is not None)
    if canevas is not None:
        canevas.yview_moveto(1.0)
        app.update()
        verifier("la dernière voix est atteignable",
                 canevas.yview()[1] >= 0.999, canevas.yview())
    app.combo_voice.fermer()
    app.update()

    print("Annuler une suppression")
    app.changer_langue_ui("fr")
    app.update()
    total = len(app.lignes)
    app._ajouter_ligne_ui("temp-un", "un")
    app._ajouter_ligne_ui("temp-deux", "deux")
    app._dessiner_liste()
    cibles = app.lignes[-2:]
    supprimees = app._supprimer_lignes(cibles)
    verifier("deux lignes supprimées", len(app.lignes) == total)
    app._restaurer_lignes(supprimees)
    verifier("les deux lignes sont restaurées", len(app.lignes) == total + 2)
    verifier("elles retrouvent leur place",
             [ligne["nom"] for ligne in app.lignes[-2:]]
             == ["temp-un", "temp-deux"])
    app._supprimer_lignes(app.lignes[-2:])

    print("Annuler au clavier")
    touche = "<Command-z>" if sys.platform == "darwin" else "<Control-z>"
    total = len(app.lignes)
    app._ajouter_ligne_ui("undo-un", "un")
    app._dessiner_liste()
    app._supprimer_et_proposer([app.lignes[-1]])
    verifier("une ligne supprimée", len(app.lignes) == total)
    app.focus_force()
    app.update()
    app.event_generate(touche)
    app.update()
    verifier("Cmd/Ctrl+Z restaure une ligne", len(app.lignes) == total + 1)
    verifier("l'annulation est consommée", app._annulation is None)

    app._ajouter_ligne_ui("undo-deux", "deux")
    app._ajouter_ligne_ui("undo-trois", "trois")
    app._dessiner_liste()
    app._supprimer_et_proposer(app.lignes[-2:])
    app.update()
    verifier("deux lignes supprimées", len(app.lignes) == total + 1)
    verifier("le message d'annulation est ouvert", len(app._alertes) == 1)
    app.focus_force()
    app.update()
    app.event_generate("<Return>")
    app.update()
    verifier("Entrée annule la suppression", len(app.lignes) == total + 3)
    verifier("le message d'annulation est fermé", not app._alertes)
    app._supprimer_lignes(app.lignes[-3:])

    print("Entrée dans les fenêtres de message")
    marques = []
    app._message("Essai", boutons=[("Oui", lambda: marques.append("oui")),
                                   ("Non", None)])
    app.update()
    alerte = app._alertes[-1]
    app.focus_force()
    app.update()
    app.event_generate("<Return>")
    app.update()
    verifier("Entrée valide le bouton par défaut", marques == ["oui"], marques)
    verifier("la fenêtre de message est fermée", not alerte.winfo_exists())

    print("Entrée sur une confirmation destructive")
    total = len(app.lignes)
    app.tout_cocher()
    app.update()
    app.supprimer_selection()
    app.update()
    verifier("la confirmation « Tout supprimer » est ouverte",
             len(app._alertes) == 1)
    app.focus_force()
    app.update()
    app.event_generate("<Return>")
    app.update()
    # Le bouton par défaut de cette confirmation est « Annuler » : une touche
    # Entrée ne doit pas vider la liste.
    verifier("Entrée annule « Tout supprimer »",
             len(app.lignes) == total, f"{len(app.lignes)} au lieu de {total}")
    verifier("la confirmation est fermée", not app._alertes)
    app.rien_cocher()
    app.update()

    print("Bouton désactivé")
    app.btn_letsgo.configure(state="disabled", fg_color="#083137")
    app.update()
    couleur = str(app.btn_letsgo.itemcget(app.btn_letsgo._forme, "fill"))
    verifier("la couleur d'un bouton désactivé est appliquée",
             couleur.lower() == "#083137", couleur)
    app.btn_letsgo.configure(state="normal", fg_color="#0B2E36")
    app.update()

    app.destroy()

    print()
    if ECHECS:
        print(f"{len(ECHECS)} échec(s) :", ", ".join(ECHECS))
        return 1
    print("tout est vert")
    return 0


if __name__ == "__main__":
    sys.exit(main())
