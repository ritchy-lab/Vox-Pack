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
    codes = [langue.code for langue in voxpack2._LANGUES_TABLE]
    index_fr = codes.index("fr")
    verifier("la langue courante est marquée",
             fenetre._focus_i == index_fr, fenetre._focus_i)
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

    app.destroy()

    print()
    if ECHECS:
        print(f"{len(ECHECS)} échec(s) :", ", ".join(ECHECS))
        return 1
    print("tout est vert")
    return 0


if __name__ == "__main__":
    sys.exit(main())
