"""Les textes de l'interface, dans les quinze langues de la v2.

Même principe que `langues.py` : une seule table, quinze langues, et une
fonction de lecture qui ne laisse jamais un trou à l'écran. Si une clé
manque dans une langue, on retombe sur l'anglais, puis sur le français, puis
sur le nom de la clé — jamais sur du vide.

Deux règles de rédaction, héritées de la 1.5.1 :

- « Let's Go » ne se traduit pas, dans aucune langue (décision de Richard).
- Les libellés sont courts et en capitales dans la maquette ; le texte est
  donné ici en casse normale et c'est l'affichage qui met en capitales, pour
  que les langues sans majuscules (chinois, japonais) ne soient pas
  malmenées.

Le français garde « Sons system », sans « e » et sans accent : c'est une
demande de Richard, pas une faute.
"""

from __future__ import annotations

from .aide import LOT_AIDE

# L'ordre n'a pas d'importance ; les clés, si.
LANGUES_TEXTES = ("fr", "en", "de", "es", "it", "pt", "ru", "sv", "uk",
                  "cs", "da", "ja", "cn", "tw", "hk")

TEXTES: dict[str, dict[str, str]] = {
    "fr": {
        "liste_indisponible": "Liste indisponible : le réseau n'a pas répondu.",
        "maj_titre": 'Mise à jour disponible',
        "maj_texte": 'La version {version} est disponible. Vous utilisez la {actuelle}.',
        "maj_telecharger": 'Télécharger',
        "maj_plus_tard": 'Plus tard',
        "menu_sortie": 'Choisir le dossier de sortie',
        "soutien_titre": 'Soutenir Vox-Pack',
        "soutien_texte": 'Mon application te sert ou te plaît ? Offre-moi un café.',
        "soutien_cafe": 'Offre-moi un café',
        "soutien_jamais": 'Ne plus demander',
        "soutien_non": 'Pas maintenant',
        "menu_importer": 'Importer une liste…',
        "menu_exporter": 'Exporter la liste…',
        "menu_dossier": 'Ouvrir le dossier de sortie',
        "menu_quitter": 'Quitter',
                "liste_importee": 'Liste importée — lignes : {n}.',
        "liste_exportee": 'Liste exportée.',
        "aide_titre": 'Aide',
        "aide_1": "La langue choisie ici commande les voix et les annonces : elles viennent de la liste officielle d'EdgeTX.",
        "aide_2": 'La liste se corrige directement : cliquez une ligne, tapez, puis Ajouter ou Supprimer.',
        "aide_3": "Let's Go fabrique les fichiers des lignes cochées, avec la voix et les réglages choisis.",
        "aide_4": "Sons system fabrique les annonces de l'interface, dans la langue et le dossier de la carte.",
        "aide_5": "Un nom de fichier tient en huit caractères, sans espace ni accent : c'est la limite de la radio.",
        "arreter": 'Arrêter',
        "fabrication": 'Fabrication ({i}/{n}) — {phrase}…',
        "langue": "Langue",
        "voix": "Voix",
        "niveau": "Niveau du son",
        "vitesse": "Vitesse",
        "robot": "Robot",
        "ajouter": "Ajouter",
        "supprimer": "Supprimer",
        "ecouter": "Écouter",
        "nom": "Nom",
        "phrase": "Phrase",
        "lets_go": "Let's Go",
        "sons_system": "Sons system",
        "pret": "Prêt.",
        "preparation": "Préparation…",
        "recherche": "Recherche de la voix ({i}/{n}) — {phrase}…",
                "termine": 'Terminé — fichiers écrits : {n}.',
        "titre_langues": "Langue des sons",
        "titre_sons": "Sons système",
        "creer_titre": "Créer les sons système en {langue}",
        "creer_detail": "Ils iront dans SOUNDS/{dossier} de la carte.",
        "destination": "Dossier de destination",
        "annuler": "Annuler",
        "creer_fichiers": "Créer les fichiers",
        "dossier_sortie": 'Dossier de sortie',
    },
    "en": {
        "liste_indisponible": 'List unavailable: the network did not answer.',
        "maj_titre": 'Update available',
        "maj_texte": 'Version {version} is available. You are using {actuelle}.',
        "maj_telecharger": 'Download',
        "maj_plus_tard": 'Later',
        "menu_sortie": 'Choose the output folder',
        "soutien_titre": 'Support Vox-Pack',
        "soutien_texte": 'Is this app useful to you? Buy me a coffee.',
        "soutien_cafe": 'Buy me a coffee',
        "soutien_jamais": "Don't ask again",
        "soutien_non": 'Not now',
        "menu_importer": 'Import a list…',
        "menu_exporter": 'Export the list…',
        "menu_dossier": 'Open the output folder',
        "menu_quitter": 'Quit',
                "liste_importee": 'List imported — rows: {n}.',
        "liste_exportee": 'List exported.',
        "aide_titre": 'Help',
        "aide_1": 'The language chosen here drives the voices and the announcements: they come from the official EdgeTX list.',
        "aide_2": 'The list is edited in place: click a row, type, then Add or Delete.',
        "aide_3": "Let's Go builds the files for the ticked rows, with the chosen voice and settings.",
        "aide_4": 'System sounds builds the interface announcements, in the language and card folder.',
        "aide_5": "A file name holds eight characters, without spaces or accents: that is the radio's limit.",
        "arreter": 'Stop',
        "fabrication": 'Building ({i}/{n}) — {phrase}…',
        "langue": "Language",
        "voix": "Voice",
        "niveau": "Sound level",
        "vitesse": "Speed",
        "robot": "Robot",
        "ajouter": "Add",
        "supprimer": "Delete",
        "ecouter": "Listen",
        "nom": "Name",
        "phrase": "Phrase",
        "lets_go": "Let's Go",
        "sons_system": "System sounds",
        "pret": "Ready.",
        "preparation": "Preparing…",
        "recherche": "Looking for the voice ({i}/{n}) — {phrase}…",
                "termine": 'Done — files written: {n}.',
        "titre_langues": "Sound language",
        "titre_sons": "System sounds",
        "creer_titre": "Create the system sounds in {langue}",
        "creer_detail": "They will go to SOUNDS/{dossier} on the card.",
        "destination": "Destination folder",
        "annuler": "Cancel",
        "creer_fichiers": "Create the files",
        "dossier_sortie": 'Output folder',
    },
    "de": {
        "liste_indisponible": 'Liste nicht verfügbar: das Netzwerk hat nicht geantwortet.',
        "maj_titre": 'Aktualisierung verfügbar',
        "maj_texte": 'Version {version} ist verfügbar. Sie nutzen {actuelle}.',
        "maj_telecharger": 'Herunterladen',
        "maj_plus_tard": 'Später',
        "menu_sortie": 'Ausgabeordner wählen',
        "soutien_titre": 'Vox-Pack unterstützen',
        "soutien_texte": 'Nützt Ihnen die Anwendung? Spendieren Sie mir einen Kaffee.',
        "soutien_cafe": 'Einen Kaffee spendieren',
        "soutien_jamais": 'Nicht mehr fragen',
        "soutien_non": 'Jetzt nicht',
        "menu_importer": 'Liste importieren…',
        "menu_exporter": 'Liste exportieren…',
        "menu_dossier": 'Ausgabeordner öffnen',
        "menu_quitter": 'Beenden',
                "liste_importee": 'Liste importiert — Zeilen: {n}.',
        "liste_exportee": 'Liste exportiert.',
        "aide_titre": 'Hilfe',
        "aide_1": 'Die hier gewählte Sprache bestimmt Stimmen und Ansagen: sie stammen aus der offiziellen EdgeTX-Liste.',
        "aide_2": 'Die Liste wird direkt bearbeitet: Zeile anklicken, tippen, dann Hinzufügen oder Löschen.',
        "aide_3": "Let's Go erzeugt die Dateien der markierten Zeilen mit der gewählten Stimme und den Einstellungen.",
        "aide_4": 'Systemtöne erzeugt die Ansagen der Oberfläche, in der Sprache und im Kartenordner.',
        "aide_5": 'Ein Dateiname hat acht Zeichen, ohne Leerzeichen und Akzente: das ist die Grenze der Funke.',
        "arreter": 'Anhalten',
        "fabrication": 'Erzeuge ({i}/{n}) — {phrase}…',
        "langue": "Sprache",
        "voix": "Stimme",
        "niveau": "Lautstärke",
        "vitesse": "Geschwindigkeit",
        "robot": "Roboter",
        "ajouter": "Hinzufügen",
        "supprimer": "Löschen",
        "ecouter": "Anhören",
        "nom": "Name",
        "phrase": "Satz",
        "lets_go": "Let's Go",
        "sons_system": "Systemtöne",
        "pret": "Bereit.",
        "preparation": "Vorbereitung…",
        "recherche": "Stimme wird gesucht ({i}/{n}) — {phrase}…",
                "termine": 'Fertig — geschriebene Dateien: {n}.',
        "titre_langues": "Sprache der Töne",
        "titre_sons": "Systemtöne",
        "creer_titre": "Systemtöne auf {langue} erstellen",
        "creer_detail": "Sie kommen nach SOUNDS/{dossier} auf der Karte.",
        "destination": "Zielordner",
        "annuler": "Abbrechen",
        "creer_fichiers": "Dateien erstellen",
        "dossier_sortie": 'Ausgabeordner',
    },
    "es": {
        "liste_indisponible": 'Lista no disponible: la red no respondió.',
        "maj_titre": 'Actualización disponible',
        "maj_texte": 'La versión {version} está disponible. Usa la {actuelle}.',
        "maj_telecharger": 'Descargar',
        "maj_plus_tard": 'Más tarde',
        "menu_sortie": 'Elegir la carpeta de salida',
        "soutien_titre": 'Apoyar Vox-Pack',
        "soutien_texte": '¿Le sirve la aplicación? Invíteme a un café.',
        "soutien_cafe": 'Invíteme a un café',
        "soutien_jamais": 'No volver a preguntar',
        "soutien_non": 'Ahora no',
        "menu_importer": 'Importar una lista…',
        "menu_exporter": 'Exportar la lista…',
        "menu_dossier": 'Abrir la carpeta de salida',
        "menu_quitter": 'Salir',
                "liste_importee": 'Lista importada — filas: {n}.',
        "liste_exportee": 'Lista exportada.',
        "aide_titre": 'Ayuda',
        "aide_1": 'El idioma elegido aquí decide las voces y los avisos: vienen de la lista oficial de EdgeTX.',
        "aide_2": 'La lista se corrige directamente: haga clic en una fila, escriba y use Añadir o Eliminar.',
        "aide_3": "Let's Go crea los archivos de las filas marcadas, con la voz y los ajustes elegidos.",
        "aide_4": 'Sonidos del sistema crea los avisos de la interfaz, en el idioma y la carpeta de la tarjeta.',
        "aide_5": 'Un nombre de archivo tiene ocho caracteres, sin espacios ni acentos: es el límite de la emisora.',
        "arreter": 'Detener',
        "fabrication": 'Creando ({i}/{n}) — {phrase}…',
        "langue": "Idioma",
        "voix": "Voz",
        "niveau": "Nivel de sonido",
        "vitesse": "Velocidad",
        "robot": "Robot",
        "ajouter": "Añadir",
        "supprimer": "Eliminar",
        "ecouter": "Escuchar",
        "nom": "Nombre",
        "phrase": "Frase",
        "lets_go": "Let's Go",
        "sons_system": "Sonidos del sistema",
        "pret": "Listo.",
        "preparation": "Preparando…",
        "recherche": "Buscando la voz ({i}/{n}) — {phrase}…",
                "termine": 'Terminado — archivos escritos: {n}.',
        "titre_langues": "Idioma de los sonidos",
        "titre_sons": "Sonidos del sistema",
        "creer_titre": "Crear los sonidos del sistema en {langue}",
        "creer_detail": "Irán a SOUNDS/{dossier} de la tarjeta.",
        "destination": "Carpeta de destino",
        "annuler": "Cancelar",
        "creer_fichiers": "Crear los archivos",
        "dossier_sortie": 'Carpeta de salida',
    },
    "it": {
        "liste_indisponible": 'Lista non disponibile: la rete non ha risposto.',
        "maj_titre": 'Aggiornamento disponibile',
        "maj_texte": 'La versione {version} è disponibile. Usa la {actuelle}.',
        "maj_telecharger": 'Scarica',
        "maj_plus_tard": 'Più tardi',
        "menu_sortie": 'Scegli la cartella di uscita',
        "soutien_titre": 'Sostenere Vox-Pack',
        "soutien_texte": "L'applicazione le è utile? Offrimi un caffè.",
        "soutien_cafe": 'Offrimi un caffè',
        "soutien_jamais": 'Non chiedere più',
        "soutien_non": 'Non ora',
        "menu_importer": 'Importa una lista…',
        "menu_exporter": 'Esporta la lista…',
        "menu_dossier": 'Apri la cartella di uscita',
        "menu_quitter": 'Esci',
                "liste_importee": 'Lista importata — righe: {n}.',
        "liste_exportee": 'Lista esportata.',
        "aide_titre": 'Aiuto',
        "aide_1": 'La lingua scelta qui decide voci e annunci: vengono dalla lista ufficiale di EdgeTX.',
        "aide_2": 'La lista si corregge sul posto: fare clic su una riga, scrivere, poi Aggiungi o Elimina.',
        "aide_3": "Let's Go crea i file delle righe spuntate, con la voce e le impostazioni scelte.",
        "aide_4": "Suoni di sistema crea gli annunci dell'interfaccia, nella lingua e nella cartella della scheda.",
        "aide_5": 'Un nome di file ha otto caratteri, senza spazi né accenti: è il limite della radio.',
        "arreter": 'Interrompi',
        "fabrication": 'Creazione ({i}/{n}) — {phrase}…',
        "langue": "Lingua",
        "voix": "Voce",
        "niveau": "Livello del suono",
        "vitesse": "Velocità",
        "robot": "Robot",
        "ajouter": "Aggiungi",
        "supprimer": "Elimina",
        "ecouter": "Ascolta",
        "nom": "Nome",
        "phrase": "Frase",
        "lets_go": "Let's Go",
        "sons_system": "Suoni di sistema",
        "pret": "Pronto.",
        "preparation": "Preparazione…",
        "recherche": "Ricerca della voce ({i}/{n}) — {phrase}…",
                "termine": 'Finito — file scritti: {n}.',
        "titre_langues": "Lingua dei suoni",
        "titre_sons": "Suoni di sistema",
        "creer_titre": "Crea i suoni di sistema in {langue}",
        "creer_detail": "Andranno in SOUNDS/{dossier} della scheda.",
        "destination": "Cartella di destinazione",
        "annuler": "Annulla",
        "creer_fichiers": "Crea i file",
        "dossier_sortie": 'Cartella di uscita',
    },
    "pt": {
        "liste_indisponible": 'Lista indisponível: a rede não respondeu.',
        "maj_titre": 'Atualização disponível',
        "maj_texte": 'A versão {version} está disponível. Você usa a {actuelle}.',
        "maj_telecharger": 'Baixar',
        "maj_plus_tard": 'Mais tarde',
        "menu_sortie": 'Escolher a pasta de saída',
        "soutien_titre": 'Apoiar o Vox-Pack',
        "soutien_texte": 'O aplicativo lhe é útil? Pague-me um café.',
        "soutien_cafe": 'Pague-me um café',
        "soutien_jamais": 'Não perguntar mais',
        "soutien_non": 'Agora não',
        "menu_importer": 'Importar uma lista…',
        "menu_exporter": 'Exportar a lista…',
        "menu_dossier": 'Abrir a pasta de saída',
        "menu_quitter": 'Sair',
                "liste_importee": 'Lista importada — linhas: {n}.',
        "liste_exportee": 'Lista exportada.',
        "aide_titre": 'Ajuda',
        "aide_1": 'O idioma escolhido aqui decide as vozes e os avisos: eles vêm da lista oficial do EdgeTX.',
        "aide_2": 'A lista é corrigida no lugar: clique numa linha, escreva e use Adicionar ou Excluir.',
        "aide_3": "Let's Go cria os arquivos das linhas marcadas, com a voz e os ajustes escolhidos.",
        "aide_4": 'Sons do sistema cria os avisos da interface, no idioma e na pasta do cartão.',
        "aide_5": 'Um nome de arquivo tem oito caracteres, sem espaços nem acentos: é o limite do rádio.',
        "arreter": 'Parar',
        "fabrication": 'Criando ({i}/{n}) — {phrase}…',
        "langue": "Idioma",
        "voix": "Voz",
        "niveau": "Nível do som",
        "vitesse": "Velocidade",
        "robot": "Robô",
        "ajouter": "Adicionar",
        "supprimer": "Excluir",
        "ecouter": "Ouvir",
        "nom": "Nome",
        "phrase": "Frase",
        "lets_go": "Let's Go",
        "sons_system": "Sons do sistema",
        "pret": "Pronto.",
        "preparation": "Preparando…",
        "recherche": "Buscando a voz ({i}/{n}) — {phrase}…",
                "termine": 'Concluído — arquivos escritos: {n}.',
        "titre_langues": "Idioma dos sons",
        "titre_sons": "Sons do sistema",
        "creer_titre": "Criar os sons do sistema em {langue}",
        "creer_detail": "Eles irão para SOUNDS/{dossier} do cartão.",
        "destination": "Pasta de destino",
        "annuler": "Cancelar",
        "creer_fichiers": "Criar os arquivos",
        "dossier_sortie": 'Pasta de saída',
    },
    "ru": {
        "liste_indisponible": 'Список недоступен: сеть не ответила.',
        "maj_titre": 'Доступно обновление',
        "maj_texte": 'Доступна версия {version}. Вы используете {actuelle}.',
        "maj_telecharger": 'Скачать',
        "maj_plus_tard": 'Позже',
        "menu_sortie": 'Выбрать папку вывода',
        "soutien_titre": 'Поддержать Vox-Pack',
        "soutien_texte": 'Программа вам полезна? Угостите меня кофе.',
        "soutien_cafe": 'Угостить кофе',
        "soutien_jamais": 'Больше не спрашивать',
        "soutien_non": 'Не сейчас',
        "menu_importer": 'Импорт списка…',
        "menu_exporter": 'Экспорт списка…',
        "menu_dossier": 'Открыть папку вывода',
        "menu_quitter": 'Выход',
                "liste_importee": 'Список импортирован — строк: {n}.',
        "liste_exportee": 'Список экспортирован.',
        "aide_titre": 'Справка',
        "aide_1": 'Выбранный здесь язык определяет голоса и объявления: они берутся из официального списка EdgeTX.',
        "aide_2": 'Список правится на месте: щёлкните строку, наберите текст, затем «Добавить» или «Удалить».',
        "aide_3": "Let's Go создаёт файлы отмеченных строк с выбранным голосом и настройками.",
        "aide_4": 'Системные звуки создаёт объявления интерфейса — на этом языке и в папку карты.',
        "aide_5": 'Имя файла — восемь знаков, без пробелов и ударений: таков предел аппаратуры.',
        "arreter": 'Остановить',
        "fabrication": 'Создание ({i}/{n}) — {phrase}…',
        "langue": "Язык",
        "voix": "Голос",
        "niveau": "Уровень звука",
        "vitesse": "Скорость",
        "robot": "Робот",
        "ajouter": "Добавить",
        "supprimer": "Удалить",
        "ecouter": "Прослушать",
        "nom": "Имя",
        "phrase": "Фраза",
        "lets_go": "Let's Go",
        "sons_system": "Системные звуки",
        "pret": "Готово.",
        "preparation": "Подготовка…",
        "recherche": "Поиск голоса ({i}/{n}) — {phrase}…",
                "termine": 'Готово — записано файлов: {n}.',
        "titre_langues": "Язык звуков",
        "titre_sons": "Системные звуки",
        "creer_titre": "Создать системные звуки на языке {langue}",
        "creer_detail": "Они будут в SOUNDS/{dossier} на карте.",
        "destination": "Папка назначения",
        "annuler": "Отмена",
        "creer_fichiers": "Создать файлы",
        "dossier_sortie": 'Папка вывода',
    },
    "sv": {
        "liste_indisponible": 'Listan är inte tillgänglig: nätet svarade inte.',
        "maj_titre": 'Uppdatering tillgänglig',
        "maj_texte": 'Version {version} finns. Du använder {actuelle}.',
        "maj_telecharger": 'Hämta',
        "maj_plus_tard": 'Senare',
        "menu_sortie": 'Välj utmapp',
        "soutien_titre": 'Stöd Vox-Pack',
        "soutien_texte": 'Har du nytta av programmet? Bjud mig på en kaffe.',
        "soutien_cafe": 'Bjud på en kaffe',
        "soutien_jamais": 'Fråga inte igen',
        "soutien_non": 'Inte nu',
        "menu_importer": 'Importera en lista…',
        "menu_exporter": 'Exportera listan…',
        "menu_dossier": 'Öppna utmappen',
        "menu_quitter": 'Avsluta',
                "liste_importee": 'Lista importerad — rader: {n}.',
        "liste_exportee": 'Lista exporterad.',
        "aide_titre": 'Hjälp',
        "aide_1": 'Språket som väljs här styr rösterna och meddelandena: de kommer från EdgeTX officiella lista.',
        "aide_2": 'Listan rättas direkt: klicka på en rad, skriv, använd sedan Lägg till eller Ta bort.',
        "aide_3": "Let's Go skapar filerna för de ikryssade raderna, med vald röst och inställningar.",
        "aide_4": 'Systemljud skapar gränssnittets meddelanden, på språket och i kortets mapp.',
        "aide_5": 'Ett filnamn rymmer åtta tecken, utan mellanslag och accenter: det är radions gräns.',
        "arreter": 'Stoppa',
        "fabrication": 'Skapar ({i}/{n}) — {phrase}…',
        "langue": "Språk",
        "voix": "Röst",
        "niveau": "Ljudnivå",
        "vitesse": "Hastighet",
        "robot": "Robot",
        "ajouter": "Lägg till",
        "supprimer": "Ta bort",
        "ecouter": "Lyssna",
        "nom": "Namn",
        "phrase": "Fras",
        "lets_go": "Let's Go",
        "sons_system": "Systemljud",
        "pret": "Klar.",
        "preparation": "Förbereder…",
        "recherche": "Söker rösten ({i}/{n}) — {phrase}…",
                "termine": 'Klart — filer skrivna: {n}.',
        "titre_langues": "Ljudspråk",
        "titre_sons": "Systemljud",
        "creer_titre": "Skapa systemljuden på {langue}",
        "creer_detail": "De hamnar i SOUNDS/{dossier} på kortet.",
        "destination": "Målmapp",
        "annuler": "Avbryt",
        "creer_fichiers": "Skapa filerna",
        "dossier_sortie": 'Utmapp',
    },
    "uk": {
        "liste_indisponible": 'Список недоступний: мережа не відповіла.',
        "maj_titre": 'Доступне оновлення',
        "maj_texte": 'Доступна версія {version}. Ви використовуєте {actuelle}.',
        "maj_telecharger": 'Завантажити',
        "maj_plus_tard": 'Пізніше',
        "menu_sortie": 'Вибрати папку виводу',
        "soutien_titre": 'Підтримати Vox-Pack',
        "soutien_texte": 'Програма вам корисна? Пригостіть мене кавою.',
        "soutien_cafe": 'Пригостити кавою',
        "soutien_jamais": 'Більше не питати',
        "soutien_non": 'Не зараз',
        "menu_importer": 'Імпорт списку…',
        "menu_exporter": 'Експорт списку…',
        "menu_dossier": 'Відкрити папку виводу',
        "menu_quitter": 'Вихід',
                "liste_importee": 'Список імпортовано — рядків: {n}.',
        "liste_exportee": 'Список експортовано.',
        "aide_titre": 'Довідка',
        "aide_1": 'Обрана тут мова визначає голоси й оголошення: вони беруться з офіційного списку EdgeTX.',
        "aide_2": 'Список правиться на місці: клацніть рядок, наберіть текст, потім «Додати» або «Видалити».',
        "aide_3": "Let's Go створює файли позначених рядків із вибраним голосом і налаштуваннями.",
        "aide_4": 'Системні звуки створює оголошення інтерфейсу — цією мовою і в теку картки.',
        "aide_5": 'Назва файлу — вісім знаків, без пробілів і наголосів: така межа апаратури.',
        "arreter": 'Зупинити',
        "fabrication": 'Створення ({i}/{n}) — {phrase}…',
        "langue": "Мова",
        "voix": "Голос",
        "niveau": "Рівень звуку",
        "vitesse": "Швидкість",
        "robot": "Робот",
        "ajouter": "Додати",
        "supprimer": "Видалити",
        "ecouter": "Прослухати",
        "nom": "Назва",
        "phrase": "Фраза",
        "lets_go": "Let's Go",
        "sons_system": "Системні звуки",
        "pret": "Готово.",
        "preparation": "Підготовка…",
        "recherche": "Пошук голосу ({i}/{n}) — {phrase}…",
                "termine": 'Готово — записано файлів: {n}.',
        "titre_langues": "Мова звуків",
        "titre_sons": "Системні звуки",
        "creer_titre": "Створити системні звуки мовою {langue}",
        "creer_detail": "Вони будуть у SOUNDS/{dossier} на карті.",
        "destination": "Папка призначення",
        "annuler": "Скасувати",
        "creer_fichiers": "Створити файли",
        "dossier_sortie": 'Папка виводу',
    },
    "cs": {
        "liste_indisponible": 'Seznam není k dispozici: síť neodpověděla.',
        "maj_titre": 'Dostupné aktualizace',
        "maj_texte": 'Verze {version} je k dispozici. Používáte {actuelle}.',
        "maj_telecharger": 'Stáhnout',
        "maj_plus_tard": 'Později',
        "menu_sortie": 'Vybrat výstupní složku',
        "soutien_titre": 'Podpořit Vox-Pack',
        "soutien_texte": 'Je vám aplikace užitečná? Kup mi kávu.',
        "soutien_cafe": 'Kup mi kávu',
        "soutien_jamais": 'Už se neptat',
        "soutien_non": 'Teď ne',
        "menu_importer": 'Importovat seznam…',
        "menu_exporter": 'Exportovat seznam…',
        "menu_dossier": 'Otevřít výstupní složku',
        "menu_quitter": 'Ukončit',
                "liste_importee": 'Seznam importován — řádků: {n}.',
        "liste_exportee": 'Seznam exportován.',
        "aide_titre": 'Nápověda',
        "aide_1": 'Zvolený jazyk určuje hlasy i hlášení: pocházejí z oficiálního seznamu EdgeTX.',
        "aide_2": 'Seznam se opravuje přímo: klikněte na řádek, pište, pak Přidat nebo Smazat.',
        "aide_3": "Let's Go vytvoří soubory zaškrtnutých řádků se zvoleným hlasem a nastavením.",
        "aide_4": 'Systémové zvuky vytvoří hlášení rozhraní, v tomto jazyce a do složky na kartě.',
        "aide_5": 'Název souboru má osm znaků, bez mezer a diakritiky: to je limit vysílačky.',
        "arreter": 'Zastavit',
        "fabrication": 'Vytvářím ({i}/{n}) — {phrase}…',
        "langue": "Jazyk",
        "voix": "Hlas",
        "niveau": "Úroveň zvuku",
        "vitesse": "Rychlost",
        "robot": "Robot",
        "ajouter": "Přidat",
        "supprimer": "Smazat",
        "ecouter": "Přehrát",
        "nom": "Název",
        "phrase": "Věta",
        "lets_go": "Let's Go",
        "sons_system": "Systémové zvuky",
        "pret": "Připraveno.",
        "preparation": "Příprava…",
        "recherche": "Hledání hlasu ({i}/{n}) — {phrase}…",
                "termine": 'Hotovo — zapsáno souborů: {n}.',
        "titre_langues": "Jazyk zvuků",
        "titre_sons": "Systémové zvuky",
        "creer_titre": "Vytvořit systémové zvuky v jazyce {langue}",
        "creer_detail": "Půjdou do SOUNDS/{dossier} na kartě.",
        "destination": "Cílová složka",
        "annuler": "Zrušit",
        "creer_fichiers": "Vytvořit soubory",
        "dossier_sortie": 'Výstupní složka',
    },
    "da": {
        "liste_indisponible": 'Listen er ikke tilgængelig: netværket svarede ikke.',
        "maj_titre": 'Opdatering tilgængelig',
        "maj_texte": 'Version {version} er tilgængelig. Du bruger {actuelle}.',
        "maj_telecharger": 'Hent',
        "maj_plus_tard": 'Senere',
        "menu_sortie": 'Vælg outputmappe',
        "soutien_titre": 'Støt Vox-Pack',
        "soutien_texte": 'Har du gavn af programmet? Køb en kaffe til mig.',
        "soutien_cafe": 'Køb en kaffe',
        "soutien_jamais": 'Spørg ikke igen',
        "soutien_non": 'Ikke nu',
        "menu_importer": 'Importér en liste…',
        "menu_exporter": 'Eksportér listen…',
        "menu_dossier": 'Åbn outputmappen',
        "menu_quitter": 'Afslut',
                "liste_importee": 'Liste importeret — rækker: {n}.',
        "liste_exportee": 'Liste eksporteret.',
        "aide_titre": 'Hjælp',
        "aide_1": "Sproget her bestemmer stemmerne og meddelelserne: de kommer fra EdgeTX' officielle liste.",
        "aide_2": 'Listen rettes direkte: klik på en række, skriv, brug derefter Tilføj eller Slet.',
        "aide_3": "Let's Go opretter filerne for de markerede rækker med den valgte stemme og indstillinger.",
        "aide_4": 'Systemlyde opretter grænsefladens meddelelser, på sproget og i kortets mappe.',
        "aide_5": 'Et filnavn har otte tegn, uden mellemrum og accenter: det er radioens grænse.',
        "arreter": 'Stop',
        "fabrication": 'Opretter ({i}/{n}) — {phrase}…',
        "langue": "Sprog",
        "voix": "Stemme",
        "niveau": "Lydniveau",
        "vitesse": "Hastighed",
        "robot": "Robot",
        "ajouter": "Tilføj",
        "supprimer": "Slet",
        "ecouter": "Afspil",
        "nom": "Navn",
        "phrase": "Sætning",
        "lets_go": "Let's Go",
        "sons_system": "Systemlyde",
        "pret": "Klar.",
        "preparation": "Forbereder…",
        "recherche": "Søger stemmen ({i}/{n}) — {phrase}…",
                "termine": 'Færdig — filer skrevet: {n}.',
        "titre_langues": "Lydsprog",
        "titre_sons": "Systemlyde",
        "creer_titre": "Opret systemlydene på {langue}",
        "creer_detail": "De lægges i SOUNDS/{dossier} på kortet.",
        "destination": "Destinationsmappe",
        "annuler": "Annuller",
        "creer_fichiers": "Opret filerne",
        "dossier_sortie": 'Outputmappe',
    },
    "ja": {
        "liste_indisponible": 'リストを取得できません。ネットワークが応答しませんでした。',
        "maj_titre": 'アップデートがあります',
        "maj_texte": 'バージョン {version} が利用できます。現在は {actuelle} です。',
        "maj_telecharger": 'ダウンロード',
        "maj_plus_tard": '後で',
        "menu_sortie": '出力フォルダーを選ぶ',
        "soutien_titre": 'Vox-Pack を支援',
        "soutien_texte": 'このアプリは役に立っていますか。コーヒーをごちそうしてください。',
        "soutien_cafe": 'コーヒーをおごる',
        "soutien_jamais": '今後表示しない',
        "soutien_non": '今はしない',
        "menu_importer": 'リストを読み込む…',
        "menu_exporter": 'リストを書き出す…',
        "menu_dossier": '出力フォルダーを開く',
        "menu_quitter": '終了',
                "liste_importee": '読み込みました — 行数: {n}',
        "liste_exportee": 'リストを書き出しました。',
        "aide_titre": 'ヘルプ',
        "aide_1": 'ここで選んだ言語が音声とアナウンスを決めます。EdgeTX の公式リストから取得します。',
        "aide_2": 'リストはその場で直せます。行をクリックして入力し、追加または削除を使います。',
        "aide_3": "Let's Go はチェックした行のファイルを、選んだ音声と設定で作成します。",
        "aide_4": 'システム音は、この言語とカードのフォルダーにインターフェースのアナウンスを作成します。',
        "aide_5": 'ファイル名は8文字まで、空白もアクセントも使えません。送信機の制限です。',
        "arreter": '停止',
        "fabrication": '作成中 ({i}/{n}) — {phrase}…',
        "langue": "言語",
        "voix": "音声",
        "niveau": "音量",
        "vitesse": "速度",
        "robot": "ロボット",
        "ajouter": "追加",
        "supprimer": "削除",
        "ecouter": "試聴",
        "nom": "名前",
        "phrase": "フレーズ",
        "lets_go": "Let's Go",
        "sons_system": "システム音",
        "pret": "準備完了。",
        "preparation": "準備中…",
        "recherche": "音声を検索中 ({i}/{n}) — {phrase}…",
                "termine": '完了 — 書き出したファイル: {n}',
        "titre_langues": "音声の言語",
        "titre_sons": "システム音",
        "creer_titre": "システム音を{langue}で作成",
        "creer_detail": "カードの SOUNDS/{dossier} に保存されます。",
        "destination": "保存先フォルダー",
        "annuler": "キャンセル",
        "creer_fichiers": "ファイルを作成",
        "dossier_sortie": '出力フォルダー',
    },
    "cn": {
        "liste_indisponible": '列表不可用：网络没有响应。',
        "maj_titre": '有可用更新',
        "maj_texte": '版本 {version} 已发布，您正在使用 {actuelle}。',
        "maj_telecharger": '下载',
        "maj_plus_tard": '稍后',
        "menu_sortie": '选择输出文件夹',
        "soutien_titre": '支持 Vox-Pack',
        "soutien_texte": '这个程序对您有帮助吗？请我喝杯咖啡吧。',
        "soutien_cafe": '请我喝杯咖啡',
        "soutien_jamais": '不再询问',
        "soutien_non": '暂时不用',
        "menu_importer": '导入列表…',
        "menu_exporter": '导出列表…',
        "menu_dossier": '打开输出文件夹',
        "menu_quitter": '退出',
                "liste_importee": '已导入 — 行数：{n}',
        "liste_exportee": '列表已导出。',
        "aide_titre": '帮助',
        "aide_1": '此处选择的语言决定语音和播报，它们来自 EdgeTX 的官方列表。',
        "aide_2": '列表可直接修改：点击一行，输入内容，然后使用添加或删除。',
        "aide_3": "Let's Go 用所选语音和设置生成已勾选行的文件。",
        "aide_4": '系统声音会用该语言在存储卡的文件夹中生成界面播报。',
        "aide_5": '文件名最多八个字符，不能有空格和重音符号，这是遥控器的限制。',
        "arreter": '停止',
        "fabrication": '正在创建 ({i}/{n}) — {phrase}…',
        "langue": "语言",
        "voix": "语音",
        "niveau": "音量",
        "vitesse": "速度",
        "robot": "机器人",
        "ajouter": "添加",
        "supprimer": "删除",
        "ecouter": "试听",
        "nom": "名称",
        "phrase": "短语",
        "lets_go": "Let's Go",
        "sons_system": "系统声音",
        "pret": "就绪。",
        "preparation": "正在准备…",
        "recherche": "正在查找语音 ({i}/{n}) — {phrase}…",
                "termine": '完成 — 已写入文件：{n}',
        "titre_langues": "语音语言",
        "titre_sons": "系统声音",
        "creer_titre": "创建{langue}系统声音",
        "creer_detail": "它们会写入卡上的 SOUNDS/{dossier}。",
        "destination": "目标文件夹",
        "annuler": "取消",
        "creer_fichiers": "创建文件",
        "dossier_sortie": '输出文件夹',
    },
    "tw": {
        "liste_indisponible": '清單無法取得：網路沒有回應。',
        "maj_titre": '有可用更新',
        "maj_texte": '版本 {version} 已發布，您正在使用 {actuelle}。',
        "maj_telecharger": '下載',
        "maj_plus_tard": '稍後',
        "menu_sortie": '選擇輸出資料夾',
        "soutien_titre": '支持 Vox-Pack',
        "soutien_texte": '這個程式對您有幫助嗎？請我喝杯咖啡吧。',
        "soutien_cafe": '請我喝杯咖啡',
        "soutien_jamais": '不再詢問',
        "soutien_non": '暫時不用',
        "menu_importer": '匯入清單…',
        "menu_exporter": '匯出清單…',
        "menu_dossier": '開啟輸出資料夾',
        "menu_quitter": '結束',
                "liste_importee": '已匯入 — 列數：{n}',
        "liste_exportee": '清單已匯出。',
        "aide_titre": '說明',
        "aide_1": '此處選擇的語言決定語音和播報，它們來自 EdgeTX 的官方清單。',
        "aide_2": '清單可直接修改：點擊一行，輸入內容，然後使用新增或刪除。',
        "aide_3": "Let's Go 用所選語音和設定產生已勾選列的檔案。",
        "aide_4": '系統音效會用該語言在記憶卡的資料夾中產生介面播報。',
        "aide_5": '檔案名稱最多八個字元，不能有空格和重音符號，這是遙控器的限制。',
        "arreter": '停止',
        "fabrication": '正在建立 ({i}/{n}) — {phrase}…',
        "langue": "語言",
        "voix": "語音",
        "niveau": "音量",
        "vitesse": "速度",
        "robot": "機器人",
        "ajouter": "新增",
        "supprimer": "刪除",
        "ecouter": "試聽",
        "nom": "名稱",
        "phrase": "短句",
        "lets_go": "Let's Go",
        "sons_system": "系統音效",
        "pret": "就緒。",
        "preparation": "正在準備…",
        "recherche": "正在尋找語音 ({i}/{n}) — {phrase}…",
                "termine": '完成 — 已寫入檔案：{n}',
        "titre_langues": "語音語言",
        "titre_sons": "系統音效",
        "creer_titre": "建立{langue}系統音效",
        "creer_detail": "它們會寫入記憶卡上的 SOUNDS/{dossier}。",
        "destination": "目標資料夾",
        "annuler": "取消",
        "creer_fichiers": "建立檔案",
        "dossier_sortie": '輸出資料夾',
    },
    "hk": {
        "liste_indisponible": '攞唔到清單：網絡冇回應。',
        "maj_titre": '有可用更新',
        "maj_texte": '版本 {version} 已推出，你而家用緊 {actuelle}。',
        "maj_telecharger": '下載',
        "maj_plus_tard": '遲啲',
        "menu_sortie": '揀輸出資料夾',
        "soutien_titre": '支持 Vox-Pack',
        "soutien_texte": '呢個程式對你有幫助嗎？請我飲杯咖啡啦。',
        "soutien_cafe": '請我飲杯咖啡',
        "soutien_jamais": '唔好再問',
        "soutien_non": '暫時唔使',
        "menu_importer": '匯入清單…',
        "menu_exporter": '匯出清單…',
        "menu_dossier": '開啟輸出資料夾',
        "menu_quitter": '結束',
                "liste_importee": '已匯入 — 列數：{n}',
        "liste_exportee": '清單已匯出。',
        "aide_titre": '說明',
        "aide_1": '此處選擇的語言決定語音和廣播，它們來自 EdgeTX 的官方清單。',
        "aide_2": '清單可直接修改：點擊一行，輸入內容，然後使用新增或刪除。',
        "aide_3": "Let's Go 用所選語音和設定產生已勾選列的檔案。",
        "aide_4": '系統音效會用該語言在記憶卡的資料夾中產生介面廣播。',
        "aide_5": '檔案名稱最多八個字元，不能有空格和重音符號，這是遙控器的限制。',
        "arreter": '停止',
        "fabrication": '正在建立 ({i}/{n}) — {phrase}…',
        "langue": "語言",
        "voix": "語音",
        "niveau": "音量",
        "vitesse": "速度",
        "robot": "機械人",
        "ajouter": "新增",
        "supprimer": "刪除",
        "ecouter": "試聽",
        "nom": "名稱",
        "phrase": "短句",
        "lets_go": "Let's Go",
        "sons_system": "系統音效",
        "pret": "就緒。",
        "preparation": "正在準備…",
        "recherche": "正在尋找語音 ({i}/{n}) — {phrase}…",
                "termine": '完成 — 已寫入檔案：{n}',
        "titre_langues": "語音語言",
        "titre_sons": "系統音效",
        "creer_titre": "建立{langue}系統音效",
        "creer_detail": "它們會寫入記憶卡上的 SOUNDS/{dossier}。",
        "destination": "目標資料夾",
        "annuler": "取消",
        "creer_fichiers": "建立檔案",
        "dossier_sortie": '輸出資料夾',
    },
}

# ---------------------------------------------------------------------
# Les lots de traduction
# ---------------------------------------------------------------------
# Les quinze tables ci-dessus sont celles de l'écran principal (96 clés).
# Le reste de l'application — menus, dialogues, aide, messages — est ajouté
# ici, écran par écran, pour ne pas traduire 159 textes d'un coup. Une clé
# absente retombe en anglais ; une langue peut donc être complétée par lots
# sans jamais afficher de trou.
#
# Un lot = un écran = une vérification visuelle. Pour en ajouter un, copier
# le bloc, changer les clés, et relancer `python tests/v2_langues.py --maj`
# pour enregistrer l'état (voir la passation).
LOT_0 = {'es': {'menu_fichier': 'Archivo',
        'menu_langue': 'Idioma',
        'menu_defaut': 'Cargar la lista por defecto',
        'menu_sons_systeme': 'Crear los sonidos del sistema…',
        'entete_nom': 'nombre',
        'entete_phrase': 'frase',
        'titre_aide': 'Ayuda — Vox-Pack',
        'titre_dossier': 'Carpeta de destino de los WAV',
        'titre_dossier_systeme': 'Carpeta donde crear SYSTEM',
        'titre_export': 'Exportar la lista',
        'titre_import': 'Importar una lista',
        'titre_soutien': 'Apoyar el proyecto',
        'type_csv': 'Archivo CSV',
        'type_tous': 'Todos los archivos',
        'type_txt': 'Archivo de texto',
        'tout': 'Todo',
        'rien': 'Nada',
        'nouvelle_ligne': 'nuevo',
        'texte_a_dire': 'Texto que se va a pronunciar',
        'btn_supprimer': 'Eliminar',
        'voix_normale': 'Voz normal',
        'choisir': 'Elegir',
        'compris': 'Entendido',
        'fermer': 'Cerrar',
        'oui_remplacer': 'Sí, reemplazar',
        'ouvrir_dossier': 'Abrir la carpeta'},
 'it': {'menu_fichier': 'File',
        'menu_langue': 'Lingua',
        'menu_defaut': 'Carica la lista predefinita',
        'menu_sons_systeme': 'Crea i suoni di sistema…',
        'entete_nom': 'nome',
        'entete_phrase': 'frase',
        'titre_aide': 'Aiuto — Vox-Pack',
        'titre_dossier': 'Cartella di destinazione dei WAV',
        'titre_dossier_systeme': 'Cartella in cui creare SYSTEM',
        'titre_export': "Esporta l'elenco",
        'titre_import': 'Importa un elenco',
        'titre_soutien': 'Sostieni il progetto',
        'type_csv': 'File CSV',
        'type_tous': 'Tutti i file',
        'type_txt': 'File di testo',
        'tout': 'Tutto',
        'rien': 'Niente',
        'nouvelle_ligne': 'nuovo',
        'texte_a_dire': 'Testo da pronunciare',
        'btn_supprimer': 'Elimina',
        'voix_normale': 'Voce normale',
        'choisir': 'Scegli',
        'compris': 'Ho capito',
        'fermer': 'Chiudi',
        'oui_remplacer': 'Sì, sostituisci',
        'ouvrir_dossier': 'Apri la cartella'},
 'pt': {'menu_fichier': 'Arquivo',
        'menu_langue': 'Idioma',
        'menu_defaut': 'Carregar a lista padrão',
        'menu_sons_systeme': 'Criar os sons do sistema…',
        'entete_nom': 'nome',
        'entete_phrase': 'frase',
        'titre_aide': 'Ajuda — Vox-Pack',
        'titre_dossier': 'Pasta de destino dos WAV',
        'titre_dossier_systeme': 'Pasta onde criar SYSTEM',
        'titre_export': 'Exportar a lista',
        'titre_import': 'Importar uma lista',
        'titre_soutien': 'Apoiar o projeto',
        'type_csv': 'Arquivo CSV',
        'type_tous': 'Todos os arquivos',
        'type_txt': 'Arquivo de texto',
        'tout': 'Tudo',
        'rien': 'Nada',
        'nouvelle_ligne': 'novo',
        'texte_a_dire': 'Texto a pronunciar',
        'btn_supprimer': 'Excluir',
        'voix_normale': 'Voz normal',
        'choisir': 'Escolher',
        'compris': 'Entendi',
        'fermer': 'Fechar',
        'oui_remplacer': 'Sim, substituir',
        'ouvrir_dossier': 'Abrir a pasta'},
 'ru': {'menu_fichier': 'Файл',
        'menu_langue': 'Язык',
        'menu_defaut': 'Загрузить список по умолчанию',
        'menu_sons_systeme': 'Создать системные звуки…',
        'entete_nom': 'имя',
        'entete_phrase': 'фраза',
        'titre_aide': 'Справка — Vox-Pack',
        'titre_dossier': 'Папка для WAV-файлов',
        'titre_dossier_systeme': 'Папка для создания SYSTEM',
        'titre_export': 'Экспортировать список',
        'titre_import': 'Импортировать список',
        'titre_soutien': 'Поддержать проект',
        'type_csv': 'Файл CSV',
        'type_tous': 'Все файлы',
        'type_txt': 'Текстовый файл',
        'tout': 'Все',
        'rien': 'Ничего',
        'nouvelle_ligne': 'новый',
        'texte_a_dire': 'Текст для озвучивания',
        'btn_supprimer': 'Удалить',
        'voix_normale': 'Обычный голос',
        'choisir': 'Выбрать',
        'compris': 'Понятно',
        'fermer': 'Закрыть',
        'oui_remplacer': 'Да, заменить',
        'ouvrir_dossier': 'Открыть папку'},
 'sv': {'menu_fichier': 'Arkiv',
        'menu_langue': 'Språk',
        'menu_defaut': 'Läs in standardlistan',
        'menu_sons_systeme': 'Skapa systemsljud…',
        'entete_nom': 'namn',
        'entete_phrase': 'fras',
        'titre_aide': 'Hjälp — Vox-Pack',
        'titre_dossier': 'Mapp för WAV-filerna',
        'titre_dossier_systeme': 'Mapp där SYSTEM skapas',
        'titre_export': 'Exportera listan',
        'titre_import': 'Importera en lista',
        'titre_soutien': 'Stöd projektet',
        'type_csv': 'CSV-fil',
        'type_tous': 'Alla filer',
        'type_txt': 'Textfil',
        'tout': 'Alla',
        'rien': 'Inga',
        'nouvelle_ligne': 'ny',
        'texte_a_dire': 'Text som ska läsas upp',
        'btn_supprimer': 'Ta bort',
        'voix_normale': 'Normal röst',
        'choisir': 'Välj',
        'compris': 'Uppfattat',
        'fermer': 'Stäng',
        'oui_remplacer': 'Ja, ersätt',
        'ouvrir_dossier': 'Öppna mappen'},
 'uk': {'menu_fichier': 'Файл',
        'menu_langue': 'Мова',
        'menu_defaut': 'Завантажити типовий список',
        'menu_sons_systeme': 'Створити системні звуки…',
        'entete_nom': "ім'я",
        'entete_phrase': 'фраза',
        'titre_aide': 'Довідка — Vox-Pack',
        'titre_dossier': 'Тека для WAV-файлів',
        'titre_dossier_systeme': 'Тека для створення SYSTEM',
        'titre_export': 'Експортувати список',
        'titre_import': 'Імпортувати список',
        'titre_soutien': 'Підтримати проєкт',
        'type_csv': 'Файл CSV',
        'type_tous': 'Усі файли',
        'type_txt': 'Текстовий файл',
        'tout': 'Усі',
        'rien': 'Нічого',
        'nouvelle_ligne': 'новий',
        'texte_a_dire': 'Текст для озвучення',
        'btn_supprimer': 'Видалити',
        'voix_normale': 'Звичайний голос',
        'choisir': 'Вибрати',
        'compris': 'Зрозуміло',
        'fermer': 'Закрити',
        'oui_remplacer': 'Так, замінити',
        'ouvrir_dossier': 'Відкрити теку'},
 'cs': {'menu_fichier': 'Soubor',
        'menu_langue': 'Jazyk',
        'menu_defaut': 'Načíst výchozí seznam',
        'menu_sons_systeme': 'Vytvořit systémové zvuky…',
        'entete_nom': 'název',
        'entete_phrase': 'fráze',
        'titre_aide': 'Nápověda — Vox-Pack',
        'titre_dossier': 'Složka pro soubory WAV',
        'titre_dossier_systeme': 'Složka, kde vytvořit SYSTEM',
        'titre_export': 'Exportovat seznam',
        'titre_import': 'Importovat seznam',
        'titre_soutien': 'Podpořit projekt',
        'type_csv': 'Soubor CSV',
        'type_tous': 'Všechny soubory',
        'type_txt': 'Textový soubor',
        'tout': 'Vše',
        'rien': 'Nic',
        'nouvelle_ligne': 'nový',
        'texte_a_dire': 'Text k předčítání',
        'btn_supprimer': 'Smazat',
        'voix_normale': 'Normální hlas',
        'choisir': 'Vybrat',
        'compris': 'Rozumím',
        'fermer': 'Zavřít',
        'oui_remplacer': 'Ano, nahradit',
        'ouvrir_dossier': 'Otevřít složku'},
 'da': {'menu_fichier': 'Fil',
        'menu_langue': 'Sprog',
        'menu_defaut': 'Indlæs standardlisten',
        'menu_sons_systeme': 'Opret systemlyde…',
        'entete_nom': 'navn',
        'entete_phrase': 'sætning',
        'titre_aide': 'Hjælp — Vox-Pack',
        'titre_dossier': 'Mappe til WAV-filerne',
        'titre_dossier_systeme': 'Mappe hvor SYSTEM oprettes',
        'titre_export': 'Eksporter listen',
        'titre_import': 'Importer en liste',
        'titre_soutien': 'Støt projektet',
        'type_csv': 'CSV-fil',
        'type_tous': 'Alle filer',
        'type_txt': 'Tekstfil',
        'tout': 'Alle',
        'rien': 'Ingen',
        'nouvelle_ligne': 'ny',
        'texte_a_dire': 'Tekst der skal læses op',
        'btn_supprimer': 'Slet',
        'voix_normale': 'Normal stemme',
        'choisir': 'Vælg',
        'compris': 'Forstået',
        'fermer': 'Luk',
        'oui_remplacer': 'Ja, erstat',
        'ouvrir_dossier': 'Åbn mappen'},
 'ja': {'menu_fichier': 'ファイル',
        'menu_langue': '言語',
        'menu_defaut': '既定のリストを読み込む',
        'menu_sons_systeme': 'システム音声を作成…',
        'entete_nom': '名前',
        'entete_phrase': 'フレーズ',
        'titre_aide': 'ヘルプ — Vox-Pack',
        'titre_dossier': 'WAV の保存先フォルダー',
        'titre_dossier_systeme': 'SYSTEM を作成するフォルダー',
        'titre_export': 'リストを書き出す',
        'titre_import': 'リストを読み込む',
        'titre_soutien': 'プロジェクトを支援',
        'type_csv': 'CSV ファイル',
        'type_tous': 'すべてのファイル',
        'type_txt': 'テキストファイル',
        'tout': 'すべて',
        'rien': 'なし',
        'nouvelle_ligne': '新規',
        'texte_a_dire': '読み上げるテキスト',
        'btn_supprimer': '削除',
        'voix_normale': '通常の声',
        'choisir': '選択',
        'compris': '了解',
        'fermer': '閉じる',
        'oui_remplacer': 'はい、置き換える',
        'ouvrir_dossier': 'フォルダーを開く'},
 'cn': {'menu_fichier': '文件',
        'menu_langue': '语言',
        'menu_defaut': '加载默认列表',
        'menu_sons_systeme': '创建系统提示音…',
        'entete_nom': '名称',
        'entete_phrase': '短语',
        'titre_aide': '帮助 — Vox-Pack',
        'titre_dossier': 'WAV 文件的目标文件夹',
        'titre_dossier_systeme': '创建 SYSTEM 的文件夹',
        'titre_export': '导出列表',
        'titre_import': '导入列表',
        'titre_soutien': '支持项目',
        'type_csv': 'CSV 文件',
        'type_tous': '所有文件',
        'type_txt': '文本文件',
        'tout': '全选',
        'rien': '全不选',
        'nouvelle_ligne': '新建',
        'texte_a_dire': '要朗读的文本',
        'btn_supprimer': '删除',
        'voix_normale': '正常嗓音',
        'choisir': '选择',
        'compris': '知道了',
        'fermer': '关闭',
        'oui_remplacer': '是，替换',
        'ouvrir_dossier': '打开文件夹'},
 'tw': {'menu_fichier': '檔案',
        'menu_langue': '語言',
        'menu_defaut': '載入預設清單',
        'menu_sons_systeme': '建立系統音效…',
        'entete_nom': '名稱',
        'entete_phrase': '短句',
        'titre_aide': '說明 — Vox-Pack',
        'titre_dossier': 'WAV 檔案的目標資料夾',
        'titre_dossier_systeme': '建立 SYSTEM 的資料夾',
        'titre_export': '匯出清單',
        'titre_import': '匯入清單',
        'titre_soutien': '支持專案',
        'type_csv': 'CSV 檔案',
        'type_tous': '所有檔案',
        'type_txt': '文字檔',
        'tout': '全選',
        'rien': '全不選',
        'nouvelle_ligne': '新增',
        'texte_a_dire': '要朗讀的文字',
        'btn_supprimer': '刪除',
        'voix_normale': '正常嗓音',
        'choisir': '選擇',
        'compris': '知道了',
        'fermer': '關閉',
        'oui_remplacer': '是，取代',
        'ouvrir_dossier': '開啟資料夾'},
 'hk': {'menu_fichier': '檔案',
        'menu_langue': '語言',
        'menu_defaut': '載入預設清單',
        'menu_sons_systeme': '建立系統音效…',
        'entete_nom': '名稱',
        'entete_phrase': '短句',
        'titre_aide': '說明 — Vox-Pack',
        'titre_dossier': 'WAV 檔案的目標資料夾',
        'titre_dossier_systeme': '建立 SYSTEM 的資料夾',
        'titre_export': '匯出清單',
        'titre_import': '匯入清單',
        'titre_soutien': '支持專案',
        'type_csv': 'CSV 檔案',
        'type_tous': '所有檔案',
        'type_txt': '文字檔',
        'tout': '全選',
        'rien': '全不選',
        'nouvelle_ligne': '新增',
        'texte_a_dire': '要朗讀的文字',
        'btn_supprimer': '刪除',
        'voix_normale': '正常聲線',
        'choisir': '選擇',
        'compris': '明白',
        'fermer': '關閉',
        'oui_remplacer': '是，取代',
        'ouvrir_dossier': '開啟資料夾'}}

# ----- Dialogues : mise à jour, import, soutien -----
LOT_DIALOGUES = {'es': {'maj_echec': 'La descarga ha fallado. Puedes abrir la página de '
                     'versiones.',
        'maj_fermer': 'Cerrar',
        'maj_ouvrir_dossier': 'Abrir la carpeta',
        'maj_page': 'Ver la página',
        'maj_telecharge_mac': 'Descargado en:\n'
                              '{chemin}\n'
                              '\n'
                              'Abre la carpeta y sustituye la aplicación '
                              'antigua por la nueva.',
        'maj_telecharge_win': 'Descargado en:\n'
                              '{chemin}\n'
                              '\n'
                              'Cierra Vox-Pack y ejecuta el nuevo archivo.',
        'maj_telechargement': 'Descargando…',
        'question_defaut': '¿Sustituir tu lista por las {n} frases en '
                           '{langue} incluidas con la aplicación?',
        'soutien_ne_plus': 'No volver a preguntar',
        'soutien_oui': '¡Sí, con mucho gusto!',
        'soutien_plus_tard': 'Quizá en otra ocasión',
        'soutien_question': '¿Te resulta útil mi aplicación?'},
 'it': {'maj_echec': 'Il download non è riuscito. Puoi aprire la pagina '
                     'delle versioni.',
        'maj_fermer': 'Chiudi',
        'maj_ouvrir_dossier': 'Apri la cartella',
        'maj_page': 'Vedi la pagina',
        'maj_telecharge_mac': 'Scaricato in:\n'
                              '{chemin}\n'
                              '\n'
                              'Apri la cartella e sostituisci la vecchia '
                              'applicazione con quella nuova.',
        'maj_telecharge_win': 'Scaricato in:\n'
                              '{chemin}\n'
                              '\n'
                              'Chiudi Vox-Pack e avvia il nuovo file.',
        'maj_telechargement': 'Download in corso…',
        'question_defaut': 'Sostituire la tua lista con le {n} frasi in '
                           "{langue} incluse nell'applicazione?",
        'soutien_ne_plus': 'Non chiedere più',
        'soutien_oui': 'Sì, con piacere!',
        'soutien_plus_tard': "Un'altra volta",
        'soutien_question': 'La mia applicazione ti è utile?'},
 'pt': {'maj_echec': 'O download falhou. Você pode abrir a página de '
                     'versões.',
        'maj_fermer': 'Fechar',
        'maj_ouvrir_dossier': 'Abrir a pasta',
        'maj_page': 'Ver a página',
        'maj_telecharge_mac': 'Baixado em:\n'
                              '{chemin}\n'
                              '\n'
                              'Abra a pasta e substitua o aplicativo antigo '
                              'pelo novo.',
        'maj_telecharge_win': 'Baixado em:\n'
                              '{chemin}\n'
                              '\n'
                              'Feche o Vox-Pack e execute o novo arquivo.',
        'maj_telechargement': 'Baixando…',
        'question_defaut': 'Substituir sua lista pelas {n} frases em '
                           '{langue} incluídas no aplicativo?',
        'soutien_ne_plus': 'Não perguntar mais',
        'soutien_oui': 'Sim, com prazer!',
        'soutien_plus_tard': 'Talvez na próxima',
        'soutien_question': 'Meu aplicativo é útil para você?'},
 'ru': {'maj_echec': 'Не удалось скачать. Можно открыть страницу версий.',
        'maj_fermer': 'Закрыть',
        'maj_ouvrir_dossier': 'Открыть папку',
        'maj_page': 'Открыть страницу',
        'maj_telecharge_mac': 'Скачано в:\n'
                              '{chemin}\n'
                              '\n'
                              'Откройте папку и замените старое приложение '
                              'новым.',
        'maj_telecharge_win': 'Скачано в:\n'
                              '{chemin}\n'
                              '\n'
                              'Закройте Vox-Pack и запустите новый файл.',
        'maj_telechargement': 'Скачивание…',
        'question_defaut': 'Заменить ваш список на {n} фраз на языке '
                           '{langue}, поставляемых с приложением?',
        'soutien_ne_plus': 'Больше не спрашивать',
        'soutien_oui': 'Да, с удовольствием!',
        'soutien_plus_tard': 'В следующий раз',
        'soutien_question': 'Вам полезно моё приложение?'},
 'sv': {'maj_echec': 'Nedladdningen misslyckades. Du kan öppna sidan med '
                     'versioner.',
        'maj_fermer': 'Stäng',
        'maj_ouvrir_dossier': 'Öppna mappen',
        'maj_page': 'Visa sidan',
        'maj_telecharge_mac': 'Nedladdat till:\n'
                              '{chemin}\n'
                              '\n'
                              'Öppna mappen och ersätt det gamla programmet '
                              'med det nya.',
        'maj_telecharge_win': 'Nedladdat till:\n'
                              '{chemin}\n'
                              '\n'
                              'Stäng Vox-Pack och kör den nya filen.',
        'maj_telechargement': 'Laddar ner…',
        'question_defaut': 'Ersätta din lista med de {n} fraserna på '
                           '{langue} som följer med programmet?',
        'soutien_ne_plus': 'Fråga inte igen',
        'soutien_oui': 'Ja, gärna!',
        'soutien_plus_tard': 'Kanske nästa gång',
        'soutien_question': 'Har du nytta av mitt program?'},
 'uk': {'maj_echec': 'Не вдалося завантажити. Можна відкрити сторінку '
                     'версій.',
        'maj_fermer': 'Закрити',
        'maj_ouvrir_dossier': 'Відкрити теку',
        'maj_page': 'Переглянути сторінку',
        'maj_telecharge_mac': 'Завантажено до:\n'
                              '{chemin}\n'
                              '\n'
                              'Відкрийте теку та замініть старий застосунок '
                              'новим.',
        'maj_telecharge_win': 'Завантажено до:\n'
                              '{chemin}\n'
                              '\n'
                              'Закрийте Vox-Pack і запустіть новий файл.',
        'maj_telechargement': 'Завантаження…',
        'question_defaut': 'Замінити ваш список на {n} фраз мовою {langue}, '
                           'що постачаються із застосунком?',
        'soutien_ne_plus': 'Більше не питати',
        'soutien_oui': 'Так, із задоволенням!',
        'soutien_plus_tard': 'Наступного разу',
        'soutien_question': 'Вам корисний мій застосунок?'},
 'cs': {'maj_echec': 'Stahování se nezdařilo. Můžete otevřít stránku verzí.',
        'maj_fermer': 'Zavřít',
        'maj_ouvrir_dossier': 'Otevřít složku',
        'maj_page': 'Zobrazit stránku',
        'maj_telecharge_mac': 'Staženo do:\n'
                              '{chemin}\n'
                              '\n'
                              'Otevřete složku a nahraďte starou aplikaci '
                              'novou.',
        'maj_telecharge_win': 'Staženo do:\n'
                              '{chemin}\n'
                              '\n'
                              'Zavřete Vox-Pack a spusťte nový soubor.',
        'maj_telechargement': 'Stahování…',
        'question_defaut': 'Nahradit váš seznam {n} frázemi v jazyce '
                           '{langue}, které jsou součástí aplikace?',
        'soutien_ne_plus': 'Už se neptat',
        'soutien_oui': 'Ano, rád!',
        'soutien_plus_tard': 'Možná příště',
        'soutien_question': 'Je vám moje aplikace užitečná?'},
 'da': {'maj_echec': 'Downloadet mislykkedes. Du kan åbne siden med '
                     'versioner.',
        'maj_fermer': 'Luk',
        'maj_ouvrir_dossier': 'Åbn mappen',
        'maj_page': 'Se siden',
        'maj_telecharge_mac': 'Downloadet til:\n'
                              '{chemin}\n'
                              '\n'
                              'Åbn mappen, og erstat det gamle program med '
                              'det nye.',
        'maj_telecharge_win': 'Downloadet til:\n'
                              '{chemin}\n'
                              '\n'
                              'Luk Vox-Pack, og start den nye fil.',
        'maj_telechargement': 'Downloader…',
        'question_defaut': 'Erstatte din liste med de {n} sætninger på '
                           '{langue}, som følger med programmet?',
        'soutien_ne_plus': 'Spørg ikke igen',
        'soutien_oui': 'Ja, meget gerne!',
        'soutien_plus_tard': 'Måske næste gang',
        'soutien_question': 'Har du gavn af mit program?'},
 'ja': {'maj_echec': 'ダウンロードに失敗しました。リリースページを開けます。',
        'maj_fermer': '閉じる',
        'maj_ouvrir_dossier': 'フォルダーを開く',
        'maj_page': 'ページを見る',
        'maj_telecharge_mac': 'ダウンロード先:\n'
                              '{chemin}\n'
                              '\n'
                              'フォルダーを開き、古いアプリを新しいものに置き換えてください。',
        'maj_telecharge_win': 'ダウンロード先:\n'
                              '{chemin}\n'
                              '\n'
                              'Vox-Pack を終了して、新しいファイルを起動してください。',
        'maj_telechargement': 'ダウンロード中…',
        'question_defaut': 'リストを、アプリに付属の{langue}のフレーズ {n} 件に置き換えますか？',
        'soutien_ne_plus': '今後表示しない',
        'soutien_oui': 'はい、喜んで！',
        'soutien_plus_tard': 'また今度',
        'soutien_question': 'このアプリはお役に立っていますか？'},
 'cn': {'maj_echec': '下载失败。你可以打开版本页面。',
        'maj_fermer': '关闭',
        'maj_ouvrir_dossier': '打开文件夹',
        'maj_page': '查看页面',
        'maj_telecharge_mac': '已下载到：\n{chemin}\n\n打开文件夹，用新版本替换旧应用。',
        'maj_telecharge_win': '已下载到：\n{chemin}\n\n关闭 Vox-Pack，然后运行新文件。',
        'maj_telechargement': '正在下载…',
        'question_defaut': '用应用自带的 {n} 条{langue}短语替换你的列表吗？',
        'soutien_ne_plus': '不再询问',
        'soutien_oui': '好的，非常乐意！',
        'soutien_plus_tard': '下次吧',
        'soutien_question': '我的应用对你有帮助吗？'},
 'tw': {'maj_echec': '下載失敗。你可以開啟版本頁面。',
        'maj_fermer': '關閉',
        'maj_ouvrir_dossier': '開啟資料夾',
        'maj_page': '查看頁面',
        'maj_telecharge_mac': '已下載到：\n{chemin}\n\n開啟資料夾，用新版本取代舊應用程式。',
        'maj_telecharge_win': '已下載到：\n{chemin}\n\n關閉 Vox-Pack，然後執行新檔案。',
        'maj_telechargement': '正在下載…',
        'question_defaut': '用應用程式內建的 {n} 句{langue}短句取代你的清單嗎？',
        'soutien_ne_plus': '不要再問',
        'soutien_oui': '好，非常樂意！',
        'soutien_plus_tard': '下次吧',
        'soutien_question': '我的應用程式對你有幫助嗎？'},
 'hk': {'maj_echec': '下載失敗。你可以開啟版本頁面。',
        'maj_fermer': '關閉',
        'maj_ouvrir_dossier': '開啟資料夾',
        'maj_page': '查看頁面',
        'maj_telecharge_mac': '已下載到：\n{chemin}\n\n開啟資料夾，用新版本取代舊應用程式。',
        'maj_telecharge_win': '已下載到：\n{chemin}\n\n關閉 Vox-Pack，然後執行新檔案。',
        'maj_telechargement': '正在下載…',
        'question_defaut': '用應用程式內建的 {n} 句{langue}短句取代你的清單嗎？',
        'soutien_ne_plus': '唔好再問',
        'soutien_oui': '好，好樂意！',
        'soutien_plus_tard': '下次先',
        'soutien_question': '我嘅應用程式對你有幫助嗎？'}}

# ----- Noms de fichiers : les avertissements de la liste -----
LOT_NOMS = {'es': {'pb_accent': 'sin acentos',
        'pb_caractere': 'carácter «{c}» no permitido',
        'pb_doublon': 'ya usado (línea {n})',
        'pb_espace': 'sin espacios',
        'pb_long': '{n} caracteres (máx. {max})',
        'pb_vide': 'nombre vacío'},
 'it': {'pb_accent': 'niente accenti',
        'pb_caractere': 'carattere «{c}» non consentito',
        'pb_doublon': 'già usato (riga {n})',
        'pb_espace': 'niente spazi',
        'pb_long': '{n} caratteri (max {max})',
        'pb_vide': 'nome vuoto'},
 'pt': {'pb_accent': 'sem acentos',
        'pb_caractere': 'caractere «{c}» não permitido',
        'pb_doublon': 'já usado (linha {n})',
        'pb_espace': 'sem espaços',
        'pb_long': '{n} caracteres (máx. {max})',
        'pb_vide': 'nome vazio'},
 'ru': {'pb_accent': 'без диакритики',
        'pb_caractere': 'символ «{c}» запрещён',
        'pb_doublon': 'уже используется (строка {n})',
        'pb_espace': 'без пробелов',
        'pb_long': '{n} символов (макс. {max})',
        'pb_vide': 'пустое имя'},
 'sv': {'pb_accent': 'inga accenter',
        'pb_caractere': 'tecknet ”{c}” är inte tillåtet',
        'pb_doublon': 'används redan (rad {n})',
        'pb_espace': 'inga mellanslag',
        'pb_long': '{n} tecken (max {max})',
        'pb_vide': 'tomt namn'},
 'uk': {'pb_accent': 'без діакритики',
        'pb_caractere': 'символ «{c}» заборонено',
        'pb_doublon': 'уже використовується (рядок {n})',
        'pb_espace': 'без пробілів',
        'pb_long': '{n} символів (макс. {max})',
        'pb_vide': "порожнє ім'я"},
 'cs': {'pb_accent': 'bez diakritiky',
        'pb_caractere': 'znak „{c}“ není povolen',
        'pb_doublon': 'už použito (řádek {n})',
        'pb_espace': 'bez mezer',
        'pb_long': '{n} znaků (max. {max})',
        'pb_vide': 'prázdný název'},
 'da': {'pb_accent': 'ingen accenter',
        'pb_caractere': 'tegnet »{c}« er ikke tilladt',
        'pb_doublon': 'allerede brugt (linje {n})',
        'pb_espace': 'ingen mellemrum',
        'pb_long': '{n} tegn (maks. {max})',
        'pb_vide': 'tomt navn'},
 'ja': {'pb_accent': 'アクセント記号なし',
        'pb_caractere': '文字「{c}」は使えません',
        'pb_doublon': 'すでに使用中（{n} 行目）',
        'pb_espace': 'スペースなし',
        'pb_long': '{n} 文字（最大 {max}）',
        'pb_vide': '名前が空です'},
 'cn': {'pb_accent': '不能有重音符号',
        'pb_caractere': '不允许字符“{c}”',
        'pb_doublon': '已被使用（第 {n} 行）',
        'pb_espace': '不能有空格',
        'pb_long': '{n} 个字符（最多 {max}）',
        'pb_vide': '名称为空'},
 'tw': {'pb_accent': '不能有重音符號',
        'pb_caractere': '不允許字元「{c}」',
        'pb_doublon': '已被使用（第 {n} 行）',
        'pb_espace': '不能有空格',
        'pb_long': '{n} 個字元（最多 {max}）',
        'pb_vide': '名稱為空'},
 'hk': {'pb_accent': '唔可以有重音符號',
        'pb_caractere': '唔准用字元「{c}」',
        'pb_doublon': '已經用咗（第 {n} 行）',
        'pb_espace': '唔可以有空格',
        'pb_long': '{n} 個字元（最多 {max}）',
        'pb_vide': '名稱係空'}}

# ----- Voix : accents et genres, pour les libellés -----
LOT_VOIX = {'es': {'accent_allemagne': 'Alemania',
        'accent_belgique': 'Bélgica',
        'accent_france': 'Francia',
        'accent_irlande': 'Irlanda',
        'accent_quebec': 'Quebec',
        'accent_suisse': 'Suiza',
        'accent_uk': 'Reino Unido',
        'accent_usa': 'EE. UU.',
        'genre_e': 'Niño',
        'genre_f': 'Mujer',
        'genre_h': 'Hombre'},
 'it': {'accent_allemagne': 'Germania',
        'accent_belgique': 'Belgio',
        'accent_france': 'Francia',
        'accent_irlande': 'Irlanda',
        'accent_quebec': 'Québec',
        'accent_suisse': 'Svizzera',
        'accent_uk': 'Regno Unito',
        'accent_usa': 'USA',
        'genre_e': 'Bambino',
        'genre_f': 'Donna',
        'genre_h': 'Uomo'},
 'pt': {'accent_allemagne': 'Alemanha',
        'accent_belgique': 'Bélgica',
        'accent_france': 'França',
        'accent_irlande': 'Irlanda',
        'accent_quebec': 'Quebec',
        'accent_suisse': 'Suíça',
        'accent_uk': 'Reino Unido',
        'accent_usa': 'EUA',
        'genre_e': 'Criança',
        'genre_f': 'Mulher',
        'genre_h': 'Homem'},
 'ru': {'accent_allemagne': 'Германия',
        'accent_belgique': 'Бельгия',
        'accent_france': 'Франция',
        'accent_irlande': 'Ирландия',
        'accent_quebec': 'Квебек',
        'accent_suisse': 'Швейцария',
        'accent_uk': 'Великобритания',
        'accent_usa': 'США',
        'genre_e': 'Ребёнок',
        'genre_f': 'Женщина',
        'genre_h': 'Мужчина'},
 'sv': {'accent_allemagne': 'Tyskland',
        'accent_belgique': 'Belgien',
        'accent_france': 'Frankrike',
        'accent_irlande': 'Irland',
        'accent_quebec': 'Québec',
        'accent_suisse': 'Schweiz',
        'accent_uk': 'Storbritannien',
        'accent_usa': 'USA',
        'genre_e': 'Barn',
        'genre_f': 'Kvinna',
        'genre_h': 'Man'},
 'uk': {'accent_allemagne': 'Німеччина',
        'accent_belgique': 'Бельгія',
        'accent_france': 'Франція',
        'accent_irlande': 'Ірландія',
        'accent_quebec': 'Квебек',
        'accent_suisse': 'Швейцарія',
        'accent_uk': 'Велика Британія',
        'accent_usa': 'США',
        'genre_e': 'Дитина',
        'genre_f': 'Жінка',
        'genre_h': 'Чоловік'},
 'cs': {'accent_allemagne': 'Německo',
        'accent_belgique': 'Belgie',
        'accent_france': 'Francie',
        'accent_irlande': 'Irsko',
        'accent_quebec': 'Québec',
        'accent_suisse': 'Švýcarsko',
        'accent_uk': 'Spojené království',
        'accent_usa': 'USA',
        'genre_e': 'Dítě',
        'genre_f': 'Žena',
        'genre_h': 'Muž'},
 'da': {'accent_allemagne': 'Tyskland',
        'accent_belgique': 'Belgien',
        'accent_france': 'Frankrig',
        'accent_irlande': 'Irland',
        'accent_quebec': 'Québec',
        'accent_suisse': 'Schweiz',
        'accent_uk': 'Storbritannien',
        'accent_usa': 'USA',
        'genre_e': 'Barn',
        'genre_f': 'Kvinde',
        'genre_h': 'Mand'},
 'ja': {'accent_allemagne': 'ドイツ',
        'accent_belgique': 'ベルギー',
        'accent_france': 'フランス',
        'accent_irlande': 'アイルランド',
        'accent_quebec': 'ケベック',
        'accent_suisse': 'スイス',
        'accent_uk': 'イギリス',
        'accent_usa': 'アメリカ',
        'genre_e': '子ども',
        'genre_f': '女性',
        'genre_h': '男性'},
 'cn': {'accent_allemagne': '德国',
        'accent_belgique': '比利时',
        'accent_france': '法国',
        'accent_irlande': '爱尔兰',
        'accent_quebec': '魁北克',
        'accent_suisse': '瑞士',
        'accent_uk': '英国',
        'accent_usa': '美国',
        'genre_e': '儿童',
        'genre_f': '女声',
        'genre_h': '男声'},
 'tw': {'accent_allemagne': '德國',
        'accent_belgique': '比利時',
        'accent_france': '法國',
        'accent_irlande': '愛爾蘭',
        'accent_quebec': '魁北克',
        'accent_suisse': '瑞士',
        'accent_uk': '英國',
        'accent_usa': '美國',
        'genre_e': '兒童',
        'genre_f': '女聲',
        'genre_h': '男聲'},
 'hk': {'accent_allemagne': '德國',
        'accent_belgique': '比利時',
        'accent_france': '法國',
        'accent_irlande': '愛爾蘭',
        'accent_quebec': '魁北克',
        'accent_suisse': '瑞士',
        'accent_uk': '英國',
        'accent_usa': '美國',
        'genre_e': '小朋友',
        'genre_f': '女聲',
        'genre_h': '男聲'}}

# ----- Divers -----
LOT_DIVERS = {'es': {'nom_export': 'mi-lista-vox-pack.csv'},
 'it': {'nom_export': 'la-mia-lista-vox-pack.csv'},
 'pt': {'nom_export': 'minha-lista-vox-pack.csv'},
 'ru': {'nom_export': 'moy-spisok-vox-pack.csv'},
 'sv': {'nom_export': 'min-lista-vox-pack.csv'},
 'uk': {'nom_export': 'miy-spysok-vox-pack.csv'},
 'cs': {'nom_export': 'muj-seznam-vox-pack.csv'},
 'da': {'nom_export': 'min-liste-vox-pack.csv'},
 'ja': {'nom_export': '私のvox-packリスト.csv'},
 'cn': {'nom_export': '我的vox-pack列表.csv'},
 'tw': {'nom_export': '我的vox-pack清單.csv'},
 'hk': {'nom_export': '我嘅vox-pack清單.csv'}}

# ----- Génération, états, erreurs -----
LOT_GENERATION = {'es': {'err_illisible': 'El servicio de voz devolvió una respuesta '
                         'ilegible. Inténtalo de nuevo en un momento.',
        'err_lent': 'el servicio no respondió a tiempo (¿conexión lenta?)',
        'err_refus': 'servicio rechazado (voz no disponible o actualización '
                     'pendiente)',
        'err_reseau': 'sin conexión a Internet',
        'err_reseau_detail': 'No se puede contactar con el servicio de voz '
                             'de Microsoft. Comprueba tu conexión a Internet '
                             '(VPN, cortafuegos, DNS) y vuelve a intentarlo.',
        'err_voix_absente': 'voz eliminada por el servicio: elige otra',
        'etat_avance': '{fait} de {total} archivos — {nom}',
        'etat_csv_telechargement': 'Descargando la lista oficial de EdgeTX…',
        'etat_ecoute': 'Escuchando {rang}/{total} — {nom}',
        'etat_generation_wav': 'Creando el archivo WAV ({fait}/{total}) — '
                               '{nom}…',
        'etat_langue_voix': 'Idioma: {langue} — {n} voces disponibles',
        'etat_recherche_service': 'Buscando las voces en el servicio TTS…',
        'etat_recherche_voix': 'Buscando la voz ({fait}/{total}) — {nom}…',
        'etat_sons_arret': 'Detención solicitada: terminando el archivo '
                           'actual…',
        'etat_voix_remises': 'Voces no disponibles: se ha restaurado la '
                             'lista predeterminada',
        'etat_voix_retirees': 'Voces retiradas por el servicio: {n} — lista '
                              'actualizada',
        'msg_apercu_echec': 'No se pudo reproducir la vista previa.\n\n{err}',
        'msg_audio_absent': 'Este ordenador no tiene salida de audio: no se '
                            'puede reproducir la vista previa. Los archivos '
                            'se crean igualmente.',
        'msg_autres': '• … y {n} más',
        'msg_bilan_echecs': 'Archivos creados: {reussis} de {total}.\n'
                            '\n'
                            'Problemas: {problemes}\n'
                            '{detail}',
        'msg_csv_aucun_systeme': 'La lista oficial de EdgeTX no contiene '
                                 'ningún sonido del sistema.\n'
                                 '\n'
                                 'Inténtalo más tarde: puede que el archivo '
                                 'haya cambiado.',
        'msg_csv_officiel_echec': 'No se pudo descargar la lista oficial de '
                                  'EdgeTX.\n'
                                  '\n'
                                  'Comprueba la conexión a Internet y vuelve '
                                  'a intentarlo.\n'
                                  '\n'
                                  '{err}',
        'msg_dossier_echec': 'No se pudo crear la carpeta de destino.\n'
                             '\n'
                             '{err}',
        'msg_ecouter_rien': 'Marca una línea para escucharla.',
        'msg_export_echec': 'La exportación ha fallado.\n\n{err}',
        'msg_export_ok': 'Líneas exportadas: {n}\n\n{chemin}',
        'msg_genere_deja': 'Ya hay una generación en curso.\n'
                           '\n'
                           'Espera a que termine.',
        'msg_generer_aucune': 'No hay ninguna línea válida para generar.\n'
                              '\n'
                              'Hace falta un nombre de archivo correcto Y '
                              'una frase.',
        'msg_generer_rien': 'Marca al menos una línea para generar.',
        'msg_import_confirmer': '¿Sustituir la lista actual ({avant}) por '
                                'estas {apres} líneas?',
        'msg_import_illisible': 'No se puede leer este archivo.\n\n{err}',
        'msg_import_ok': 'Líneas importadas: {n}.',
        'msg_import_oui': 'Sí, sustituir',
        'msg_import_vide': 'Este archivo no contiene ninguna línea.',
        'msg_reseau_coupe': 'Conexión a Internet interrumpida: la generación '
                            'se ha detenido. Comprueba la conexión y vuelve '
                            'a empezar.',
        'msg_sauvegarde_echec': 'No se pudo guardar la lista.\n'
                                '\n'
                                '{err}\n'
                                '\n'
                                'Otro programa puede estar usando este '
                                'archivo (antivirus, OneDrive), o Windows '
                                'protege la carpeta Documentos: en Seguridad '
                                'de Windows → «Acceso controlado a '
                                'carpetas», autoriza Vox-Pack.',
        'msg_sons_arrete': 'Generación detenida.\n'
                           '\n'
                           'Archivos creados: {n}\n'
                           '\n'
                           '{dossier}',
        'msg_sons_bilan': 'Archivos de sistema creados: {reussis} de '
                          '{total}.\n'
                          '\n'
                          'Problemas: {problemes}\n'
                          '{detail}',
        'msg_sons_cache': 'Lista oficial no descargada: se ha usado la copia '
                          'guardada.',
        'msg_sons_copier': 'Copia esta carpeta SYSTEM en SOUNDS/{langue}/ de '
                           'tu tarjeta, sustituyendo la anterior.',
        'msg_sons_problemes': 'Problemas: {problemes}\n{detail}',
        'msg_sons_succes': 'Archivos de sistema creados: {n}\n\n{dossier}',
        'msg_succes': 'Tus voces están listas.\n\n{dossier}',
        'msg_supprimer_rien': 'Marca al menos una línea para eliminar.',
        'msg_supprimer_tout': 'Vas a eliminar TODA la lista.\n'
                              '\n'
                              'Se reconstruirá automáticamente la próxima '
                              'vez que abras la aplicación.\n'
                              '\n'
                              '¿Quieres continuar?'},
 'it': {'err_illisible': 'Il servizio vocale ha restituito una risposta '
                         'illeggibile. Riprova tra un momento.',
        'err_lent': 'il servizio non ha risposto in tempo (connessione '
                    'lenta?)',
        'err_refus': 'servizio rifiutato (voce non disponibile o '
                     'aggiornamento da fare)',
        'err_reseau': 'nessuna connessione a Internet',
        'err_reseau_detail': 'Impossibile raggiungere il servizio vocale '
                             'Microsoft. Controlla la connessione a Internet '
                             '(VPN, firewall, DNS) e riprova.',
        'err_voix_absente': "voce rimossa dal servizio: scegline un'altra",
        'etat_avance': '{fait} file su {total} — {nom}',
        'etat_csv_telechargement': "Download dell'elenco ufficiale EdgeTX…",
        'etat_ecoute': 'Ascolto {rang}/{total} — {nom}',
        'etat_generation_wav': 'Creazione del file WAV ({fait}/{total}) — '
                               '{nom}…',
        'etat_langue_voix': 'Lingua: {langue} — {n} voci disponibili',
        'etat_recherche_service': 'Ricerca delle voci nel servizio TTS…',
        'etat_recherche_voix': 'Ricerca della voce ({fait}/{total}) — {nom}…',
        'etat_sons_arret': 'Arresto richiesto: fine del file in corso…',
        'etat_voix_remises': 'Voci non disponibili: elenco ripristinato a '
                             'quello predefinito',
        'etat_voix_retirees': 'Voci rimosse dal servizio: {n} — elenco '
                              'aggiornato',
        'msg_apercu_echec': "Impossibile riprodurre l'anteprima.\n\n{err}",
        'msg_audio_absent': 'Nessuna uscita audio su questo computer: '
                            "l'anteprima non può essere riprodotta. I file "
                            'vengono creati comunque.',
        'msg_autres': '• … e altri {n}',
        'msg_bilan_echecs': 'File creati: {reussis} su {total}.\n'
                            '\n'
                            'Problemi: {problemes}\n'
                            '{detail}',
        'msg_csv_aucun_systeme': "L'elenco ufficiale EdgeTX non contiene "
                                 'suoni di sistema.\n'
                                 '\n'
                                 'Riprova più tardi: il file potrebbe essere '
                                 'cambiato.',
        'msg_csv_officiel_echec': "Impossibile scaricare l'elenco ufficiale "
                                  'EdgeTX.\n'
                                  '\n'
                                  'Controlla la connessione a Internet e '
                                  'riprova.\n'
                                  '\n'
                                  '{err}',
        'msg_dossier_echec': 'Impossibile creare la cartella di '
                             'destinazione.\n'
                             '\n'
                             '{err}',
        'msg_ecouter_rien': 'Seleziona una riga da ascoltare.',
        'msg_export_echec': "L'esportazione non è riuscita.\n\n{err}",
        'msg_export_ok': 'Righe esportate: {n}\n\n{chemin}',
        'msg_genere_deja': 'Una generazione è già in corso.\n'
                           '\n'
                           'Attendi che finisca.',
        'msg_generer_aucune': 'Nessuna riga valida da generare.\n'
                              '\n'
                              'Serve un nome di file corretto E una frase.',
        'msg_generer_rien': 'Seleziona almeno una riga da generare.',
        'msg_import_confirmer': "Sostituire l'elenco attuale ({avant}) con "
                                'queste {apres} righe?',
        'msg_import_illisible': 'Impossibile leggere questo file.\n\n{err}',
        'msg_import_ok': 'Righe importate: {n}.',
        'msg_import_oui': 'Sì, sostituisci',
        'msg_import_vide': 'Questo file non contiene righe.',
        'msg_reseau_coupe': 'Connessione a Internet interrotta: la '
                            'generazione è stata fermata. Controlla la '
                            'connessione e riavvia.',
        'msg_sauvegarde_echec': "Impossibile salvare l'elenco.\n"
                                '\n'
                                '{err}\n'
                                '\n'
                                'Un altro programma potrebbe usare questo '
                                'file (antivirus, OneDrive), oppure Windows '
                                'protegge la cartella Documenti: in '
                                'Sicurezza di Windows → «Accesso controllato '
                                'alle cartelle», autorizza Vox-Pack.',
        'msg_sons_arrete': 'Generazione fermata.\n'
                           '\n'
                           'File creati: {n}\n'
                           '\n'
                           '{dossier}',
        'msg_sons_bilan': 'File di sistema creati: {reussis} su {total}.\n'
                          '\n'
                          'Problemi: {problemes}\n'
                          '{detail}',
        'msg_sons_cache': 'Elenco ufficiale non scaricato: è stata usata la '
                          'copia salvata.',
        'msg_sons_copier': 'Copia questa cartella SYSTEM in SOUNDS/{langue}/ '
                           'della tua scheda, sostituendo quella vecchia.',
        'msg_sons_problemes': 'Problemi: {problemes}\n{detail}',
        'msg_sons_succes': 'File di sistema creati: {n}\n\n{dossier}',
        'msg_succes': 'Le tue voci sono pronte.\n\n{dossier}',
        'msg_supprimer_rien': 'Seleziona almeno una riga da eliminare.',
        'msg_supprimer_tout': "Stai per eliminare TUTTO l'elenco.\n"
                              '\n'
                              'Verrà ricostruito automaticamente al prossimo '
                              "avvio dell'applicazione.\n"
                              '\n'
                              'Vuoi continuare?'},
 'pt': {'err_illisible': 'O serviço de voz devolveu uma resposta ilegível. '
                         'Tente novamente em instantes.',
        'err_lent': 'o serviço não respondeu a tempo (conexão lenta?)',
        'err_refus': 'serviço recusado (voz indisponível ou atualização '
                     'pendente)',
        'err_reseau': 'sem conexão com a Internet',
        'err_reseau_detail': 'Não foi possível contactar o serviço de voz da '
                             'Microsoft. Verifique sua conexão com a '
                             'Internet (VPN, firewall, DNS) e tente '
                             'novamente.',
        'err_voix_absente': 'voz removida pelo serviço: escolha outra',
        'etat_avance': '{fait} de {total} arquivos — {nom}',
        'etat_csv_telechargement': 'Baixando a lista oficial do EdgeTX…',
        'etat_ecoute': 'Ouvindo {rang}/{total} — {nom}',
        'etat_generation_wav': 'Criando o arquivo WAV ({fait}/{total}) — '
                               '{nom}…',
        'etat_langue_voix': 'Idioma: {langue} — {n} vozes disponíveis',
        'etat_recherche_service': 'Procurando as vozes no serviço TTS…',
        'etat_recherche_voix': 'Procurando a voz ({fait}/{total}) — {nom}…',
        'etat_sons_arret': 'Parada solicitada: terminando o arquivo atual…',
        'etat_voix_remises': 'Vozes indisponíveis: lista restaurada para o '
                             'padrão',
        'etat_voix_retirees': 'Vozes removidas pelo serviço: {n} — lista '
                              'atualizada',
        'msg_apercu_echec': 'Não foi possível reproduzir a prévia.\n\n{err}',
        'msg_audio_absent': 'Este computador não tem saída de áudio: a '
                            'prévia não pode ser reproduzida. Os arquivos '
                            'são criados normalmente.',
        'msg_autres': '• … e mais {n}',
        'msg_bilan_echecs': 'Arquivos criados: {reussis} de {total}.\n'
                            '\n'
                            'Problemas: {problemes}\n'
                            '{detail}',
        'msg_csv_aucun_systeme': 'A lista oficial do EdgeTX não contém '
                                 'nenhum som do sistema.\n'
                                 '\n'
                                 'Tente mais tarde: talvez o arquivo tenha '
                                 'mudado.',
        'msg_csv_officiel_echec': 'Não foi possível baixar a lista oficial '
                                  'do EdgeTX.\n'
                                  '\n'
                                  'Verifique a conexão com a Internet e '
                                  'tente novamente.\n'
                                  '\n'
                                  '{err}',
        'msg_dossier_echec': 'Não foi possível criar a pasta de destino.\n'
                             '\n'
                             '{err}',
        'msg_ecouter_rien': 'Marque uma linha para ouvir.',
        'msg_export_echec': 'A exportação falhou.\n\n{err}',
        'msg_export_ok': 'Linhas exportadas: {n}\n\n{chemin}',
        'msg_genere_deja': 'Já há uma geração em andamento.\n'
                           '\n'
                           'Aguarde até terminar.',
        'msg_generer_aucune': 'Nenhuma linha válida para gerar.\n'
                              '\n'
                              'É preciso um nome de arquivo correto E uma '
                              'frase.',
        'msg_generer_rien': 'Marque pelo menos uma linha para gerar.',
        'msg_import_confirmer': 'Substituir a lista atual ({avant}) por '
                                'estas {apres} linhas?',
        'msg_import_illisible': 'Não é possível ler este arquivo.\n\n{err}',
        'msg_import_ok': 'Linhas importadas: {n}.',
        'msg_import_oui': 'Sim, substituir',
        'msg_import_vide': 'Este arquivo não contém nenhuma linha.',
        'msg_reseau_coupe': 'Conexão com a Internet interrompida: a geração '
                            'foi parada. Verifique a conexão e comece de '
                            'novo.',
        'msg_sauvegarde_echec': 'Não foi possível salvar a lista.\n'
                                '\n'
                                '{err}\n'
                                '\n'
                                'Outro programa pode estar usando este '
                                'arquivo (antivírus, OneDrive), ou o Windows '
                                'protege a pasta Documentos: em Segurança do '
                                'Windows → «Acesso controlado a pastas», '
                                'autorize o Vox-Pack.',
        'msg_sons_arrete': 'Geração parada.\n'
                           '\n'
                           'Arquivos criados: {n}\n'
                           '\n'
                           '{dossier}',
        'msg_sons_bilan': 'Arquivos de sistema criados: {reussis} de '
                          '{total}.\n'
                          '\n'
                          'Problemas: {problemes}\n'
                          '{detail}',
        'msg_sons_cache': 'Lista oficial não baixada: foi usada a cópia '
                          'salva.',
        'msg_sons_copier': 'Copie esta pasta SYSTEM para SOUNDS/{langue}/ do '
                           'seu cartão, substituindo a antiga.',
        'msg_sons_problemes': 'Problemas: {problemes}\n{detail}',
        'msg_sons_succes': 'Arquivos de sistema criados: {n}\n\n{dossier}',
        'msg_succes': 'Suas vozes estão prontas.\n\n{dossier}',
        'msg_supprimer_rien': 'Marque pelo menos uma linha para excluir.',
        'msg_supprimer_tout': 'Você vai excluir TODA a lista.\n'
                              '\n'
                              'Ela será reconstruída automaticamente na '
                              'próxima vez que abrir o aplicativo.\n'
                              '\n'
                              'Quer continuar?'},
 'ru': {'err_illisible': 'Служба голоса вернула нечитаемый ответ. Повторите '
                         'попытку через мгновение.',
        'err_lent': 'служба не ответила вовремя (медленное подключение?)',
        'err_refus': 'служба отклонила запрос (голос недоступен или нужно '
                     'обновление)',
        'err_reseau': 'нет подключения к Интернету',
        'err_reseau_detail': 'Не удаётся связаться со службой голоса '
                             'Microsoft. Проверьте подключение к Интернету '
                             '(VPN, брандмауэр, DNS) и повторите попытку.',
        'err_voix_absente': 'голос удалён службой: выберите другой',
        'etat_avance': 'Файлов: {fait} из {total} — {nom}',
        'etat_csv_telechargement': 'Загрузка официального списка EdgeTX…',
        'etat_ecoute': 'Прослушивание {rang}/{total} — {nom}',
        'etat_generation_wav': 'Создание WAV-файла ({fait}/{total}) — {nom}…',
        'etat_langue_voix': 'Язык: {langue} — доступно голосов: {n}',
        'etat_recherche_service': 'Поиск голосов в службе TTS…',
        'etat_recherche_voix': 'Поиск голоса ({fait}/{total}) — {nom}…',
        'etat_sons_arret': 'Запрошена остановка — завершается текущий файл…',
        'etat_voix_remises': 'Голоса недоступны: список восстановлен по '
                             'умолчанию',
        'etat_voix_retirees': 'Голосов удалено службой: {n} — список '
                              'обновлён',
        'msg_apercu_echec': 'Не удалось воспроизвести предпрослушивание.\n'
                            '\n'
                            '{err}',
        'msg_audio_absent': 'На этом компьютере нет аудиовыхода: '
                            'предпрослушивание невозможно. Файлы всё равно '
                            'создаются.',
        'msg_autres': '• … и ещё {n}',
        'msg_bilan_echecs': 'Файлов создано: {reussis} из {total}.\n'
                            '\n'
                            'Проблем: {problemes}\n'
                            '{detail}',
        'msg_csv_aucun_systeme': 'В официальном списке EdgeTX нет системных '
                                 'звуков.\n'
                                 '\n'
                                 'Попробуйте позже: возможно, файл '
                                 'изменился.',
        'msg_csv_officiel_echec': 'Не удалось скачать официальный список '
                                  'EdgeTX.\n'
                                  '\n'
                                  'Проверьте подключение к Интернету и '
                                  'повторите попытку.\n'
                                  '\n'
                                  '{err}',
        'msg_dossier_echec': 'Не удалось создать папку назначения.\n\n{err}',
        'msg_ecouter_rien': 'Отметьте строку для прослушивания.',
        'msg_export_echec': 'Не удалось экспортировать.\n\n{err}',
        'msg_export_ok': 'Строк экспортировано: {n}\n\n{chemin}',
        'msg_genere_deja': 'Генерация уже идёт.\n\nДождитесь её завершения.',
        'msg_generer_aucune': 'Нет ни одной строки, которую можно создать.\n'
                              '\n'
                              'Нужны правильное имя файла И фраза.',
        'msg_generer_rien': 'Отметьте хотя бы одну строку для создания.',
        'msg_import_confirmer': 'Заменить текущий список ({avant}) на эти '
                                'строки ({apres})?',
        'msg_import_illisible': 'Не удалось прочитать этот файл.\n\n{err}',
        'msg_import_ok': 'Строк импортировано: {n}.',
        'msg_import_oui': 'Да, заменить',
        'msg_import_vide': 'В этом файле нет ни одной строки.',
        'msg_reseau_coupe': 'Подключение к Интернету прервано: генерация '
                            'остановлена. Проверьте соединение и запустите '
                            'снова.',
        'msg_sauvegarde_echec': 'Не удалось сохранить список.\n'
                                '\n'
                                '{err}\n'
                                '\n'
                                'Возможно, файл использует другая программа '
                                '(антивирус, OneDrive), или Windows защищает '
                                'папку «Документы»: в «Безопасность Windows» '
                                '→ «Контролируемый доступ к папкам» '
                                'разрешите Vox-Pack.',
        'msg_sons_arrete': 'Генерация остановлена.\n'
                           '\n'
                           'Файлов создано: {n}\n'
                           '\n'
                           '{dossier}',
        'msg_sons_bilan': 'Системных файлов создано: {reussis} из {total}.\n'
                          '\n'
                          'Проблем: {problemes}\n'
                          '{detail}',
        'msg_sons_cache': 'Официальный список не загружен: использована '
                          'сохранённая копия.',
        'msg_sons_copier': 'Скопируйте эту папку SYSTEM в SOUNDS/{langue}/ '
                           'на карте, заменив старую.',
        'msg_sons_problemes': 'Проблем: {problemes}\n{detail}',
        'msg_sons_succes': 'Системных файлов создано: {n}\n\n{dossier}',
        'msg_succes': 'Ваши голоса готовы.\n\n{dossier}',
        'msg_supprimer_rien': 'Отметьте хотя бы одну строку для удаления.',
        'msg_supprimer_tout': 'Вы удалите ВЕСЬ список.\n'
                              '\n'
                              'Он будет восстановлен автоматически при '
                              'следующем запуске приложения.\n'
                              '\n'
                              'Продолжить?'},
 'sv': {'err_illisible': 'Rösttjänsten svarade med ett oläsbart svar. Försök '
                         'igen om en stund.',
        'err_lent': 'tjänsten svarade inte i tid (långsam anslutning?)',
        'err_refus': 'tjänsten nekade (rösten är otillgänglig eller '
                     'uppdatering behövs)',
        'err_reseau': 'ingen internetanslutning',
        'err_reseau_detail': 'Det gick inte att nå Microsofts rösttjänst. '
                             'Kontrollera internetanslutningen (VPN, '
                             'brandvägg, DNS) och försök igen.',
        'err_voix_absente': 'rösten har tagits bort av tjänsten: välj en '
                            'annan',
        'etat_avance': '{fait} av {total} filer — {nom}',
        'etat_csv_telechargement': 'Laddar ner EdgeTX officiella lista…',
        'etat_ecoute': 'Lyssnar {rang}/{total} — {nom}',
        'etat_generation_wav': 'Skapar WAV-filen ({fait}/{total}) — {nom}…',
        'etat_langue_voix': 'Språk: {langue} — {n} röster tillgängliga',
        'etat_recherche_service': 'Söker rösterna i TTS-tjänsten…',
        'etat_recherche_voix': 'Söker rösten ({fait}/{total}) — {nom}…',
        'etat_sons_arret': 'Stopp begärt – avslutar aktuell fil…',
        'etat_voix_remises': 'Röster otillgängliga: listan återställd till '
                             'standard',
        'etat_voix_retirees': 'Röster borttagna av tjänsten: {n} — listan '
                              'uppdaterad',
        'msg_apercu_echec': 'Det gick inte att spela upp förhandsvisningen.\n'
                            '\n'
                            '{err}',
        'msg_audio_absent': 'Datorn har ingen ljudutgång: förhandsvisningen '
                            'kan inte spelas upp. Filerna skapas ändå.',
        'msg_autres': '• … och {n} till',
        'msg_bilan_echecs': 'Skapade filer: {reussis} av {total}.\n'
                            '\n'
                            'Problem: {problemes}\n'
                            '{detail}',
        'msg_csv_aucun_systeme': 'EdgeTX officiella lista innehåller inga '
                                 'systemljud.\n'
                                 '\n'
                                 'Försök igen senare: filen kan ha ändrats.',
        'msg_csv_officiel_echec': 'Det gick inte att ladda ner EdgeTX '
                                  'officiella lista.\n'
                                  '\n'
                                  'Kontrollera internetanslutningen och '
                                  'försök igen.\n'
                                  '\n'
                                  '{err}',
        'msg_dossier_echec': 'Det gick inte att skapa målmappen.\n\n{err}',
        'msg_ecouter_rien': 'Markera en rad att lyssna på.',
        'msg_export_echec': 'Exporten misslyckades.\n\n{err}',
        'msg_export_ok': 'Exporterade rader: {n}\n\n{chemin}',
        'msg_genere_deja': 'En generering pågår redan.\n'
                           '\n'
                           'Vänta tills den är klar.',
        'msg_generer_aucune': 'Ingen giltig rad att generera.\n'
                              '\n'
                              'Det krävs ett korrekt filnamn OCH en fras.',
        'msg_generer_rien': 'Markera minst en rad att generera.',
        'msg_import_confirmer': 'Ersätta den aktuella listan ({avant}) med '
                                'dessa {apres} rader?',
        'msg_import_illisible': 'Det gick inte att läsa filen.\n\n{err}',
        'msg_import_ok': 'Importerade rader: {n}.',
        'msg_import_oui': 'Ja, ersätt',
        'msg_import_vide': 'Filen innehåller inga rader.',
        'msg_reseau_coupe': 'Internetanslutningen bröts: genereringen '
                            'stoppades. Kontrollera anslutningen och starta '
                            'igen.',
        'msg_sauvegarde_echec': 'Listan kunde inte sparas.\n'
                                '\n'
                                '{err}\n'
                                '\n'
                                'Ett annat program använder kanske filen '
                                '(antivirus, OneDrive), eller så skyddar '
                                'Windows mappen Dokument: i Windows-säkerhet '
                                '→ ”Kontrollerad mappåtkomst”, tillåt '
                                'Vox-Pack.',
        'msg_sons_arrete': 'Genereringen stoppad.\n'
                           '\n'
                           'Skapade filer: {n}\n'
                           '\n'
                           '{dossier}',
        'msg_sons_bilan': 'Skapade systemfiler: {reussis} av {total}.\n'
                          '\n'
                          'Problem: {problemes}\n'
                          '{detail}',
        'msg_sons_cache': 'Officiella listan laddades inte ner: den sparade '
                          'kopian användes.',
        'msg_sons_copier': 'Kopiera mappen SYSTEM till SOUNDS/{langue}/ på '
                           'ditt kort och ersätt den gamla.',
        'msg_sons_problemes': 'Problem: {problemes}\n{detail}',
        'msg_sons_succes': 'Skapade systemfiler: {n}\n\n{dossier}',
        'msg_succes': 'Dina röster är klara.\n\n{dossier}',
        'msg_supprimer_rien': 'Markera minst en rad att ta bort.',
        'msg_supprimer_tout': 'Du är på väg att ta bort HELA listan.\n'
                              '\n'
                              'Den återskapas automatiskt nästa gång '
                              'programmet startas.\n'
                              '\n'
                              'Vill du fortsätta?'},
 'uk': {'err_illisible': 'Служба голосу повернула нечитабельну відповідь. '
                         'Спробуйте ще раз за мить.',
        'err_lent': 'служба не відповіла вчасно (повільне підключення?)',
        'err_refus': 'служба відхилила запит (голос недоступний або потрібне '
                     'оновлення)',
        'err_reseau': 'немає підключення до Інтернету',
        'err_reseau_detail': "Не вдається зв'язатися зі службою голосу "
                             'Microsoft. Перевірте підключення до Інтернету '
                             '(VPN, брандмауер, DNS) і спробуйте ще раз.',
        'err_voix_absente': 'голос видалено службою: виберіть інший',
        'etat_avance': 'Файлів: {fait} із {total} — {nom}',
        'etat_csv_telechargement': 'Завантаження офіційного списку EdgeTX…',
        'etat_ecoute': 'Прослуховування {rang}/{total} — {nom}',
        'etat_generation_wav': 'Створення WAV-файлу ({fait}/{total}) — '
                               '{nom}…',
        'etat_langue_voix': 'Мова: {langue} — доступно голосів: {n}',
        'etat_recherche_service': 'Пошук голосів у службі TTS…',
        'etat_recherche_voix': 'Пошук голосу ({fait}/{total}) — {nom}…',
        'etat_sons_arret': 'Запитано зупинку — завершується поточний файл…',
        'etat_voix_remises': 'Голоси недоступні: список відновлено до '
                             'типового',
        'etat_voix_retirees': 'Голосів видалено службою: {n} — список '
                              'оновлено',
        'msg_apercu_echec': 'Не вдалося відтворити попереднє '
                            'прослуховування.\n'
                            '\n'
                            '{err}',
        'msg_audio_absent': "На цьому комп'ютері немає аудіовиходу: "
                            'попереднє прослуховування неможливе. Файли все '
                            'одно створюються.',
        'msg_autres': '• … і ще {n}',
        'msg_bilan_echecs': 'Файлів створено: {reussis} із {total}.\n'
                            '\n'
                            'Проблем: {problemes}\n'
                            '{detail}',
        'msg_csv_aucun_systeme': 'Офіційний список EdgeTX не містить '
                                 'системних звуків.\n'
                                 '\n'
                                 'Спробуйте пізніше: можливо, файл змінився.',
        'msg_csv_officiel_echec': 'Не вдалося завантажити офіційний список '
                                  'EdgeTX.\n'
                                  '\n'
                                  'Перевірте підключення до Інтернету і '
                                  'спробуйте ще раз.\n'
                                  '\n'
                                  '{err}',
        'msg_dossier_echec': 'Не вдалося створити теку призначення.\n\n{err}',
        'msg_ecouter_rien': 'Позначте рядок для прослуховування.',
        'msg_export_echec': 'Не вдалося експортувати.\n\n{err}',
        'msg_export_ok': 'Рядків експортовано: {n}\n\n{chemin}',
        'msg_genere_deja': 'Генерація вже триває.\n'
                           '\n'
                           'Зачекайте на її завершення.',
        'msg_generer_aucune': 'Немає жодного рядка, який можна створити.\n'
                              '\n'
                              "Потрібні правильне ім'я файлу І фраза.",
        'msg_generer_rien': 'Позначте принаймні один рядок для створення.',
        'msg_import_confirmer': 'Замінити поточний список ({avant}) на ці '
                                'рядки ({apres})?',
        'msg_import_illisible': 'Не вдалося прочитати цей файл.\n\n{err}',
        'msg_import_ok': 'Рядків імпортовано: {n}.',
        'msg_import_oui': 'Так, замінити',
        'msg_import_vide': 'У цьому файлі немає жодного рядка.',
        'msg_reseau_coupe': 'Підключення до Інтернету перервано: генерацію '
                            "зупинено. Перевірте з'єднання і запустіть "
                            'знову.',
        'msg_sauvegarde_echec': 'Не вдалося зберегти список.\n'
                                '\n'
                                '{err}\n'
                                '\n'
                                'Можливо, файл використовує інша програма '
                                '(антивірус, OneDrive), або Windows захищає '
                                'теку «Документи»: у «Безпека Windows» → '
                                '«Контрольований доступ до тек» дозвольте '
                                'Vox-Pack.',
        'msg_sons_arrete': 'Генерацію зупинено.\n'
                           '\n'
                           'Файлів створено: {n}\n'
                           '\n'
                           '{dossier}',
        'msg_sons_bilan': 'Системних файлів створено: {reussis} із {total}.\n'
                          '\n'
                          'Проблем: {problemes}\n'
                          '{detail}',
        'msg_sons_cache': 'Офіційний список не завантажено: використано '
                          'збережену копію.',
        'msg_sons_copier': 'Скопіюйте цю теку SYSTEM у SOUNDS/{langue}/ на '
                           'карті, замінивши стару.',
        'msg_sons_problemes': 'Проблем: {problemes}\n{detail}',
        'msg_sons_succes': 'Системних файлів створено: {n}\n\n{dossier}',
        'msg_succes': 'Ваші голоси готові.\n\n{dossier}',
        'msg_supprimer_rien': 'Позначте принаймні один рядок для видалення.',
        'msg_supprimer_tout': 'Ви видалите ВЕСЬ список.\n'
                              '\n'
                              'Його буде відновлено автоматично під час '
                              'наступного запуску застосунку.\n'
                              '\n'
                              'Продовжити?'},
 'cs': {'err_illisible': 'Hlasová služba vrátila nečitelnou odpověď. Zkuste '
                         'to za chvíli znovu.',
        'err_lent': 'služba neodpověděla včas (pomalé připojení?)',
        'err_refus': 'služba odmítla (hlas není k dispozici nebo je potřeba '
                     'aktualizace)',
        'err_reseau': 'žádné připojení k internetu',
        'err_reseau_detail': 'Nelze se spojit s hlasovou službou Microsoft. '
                             'Zkontrolujte připojení k internetu (VPN, '
                             'firewall, DNS) a zkuste to znovu.',
        'err_voix_absente': 'hlas byl službou odstraněn: vyberte jiný',
        'etat_avance': 'Souborů: {fait} z {total} — {nom}',
        'etat_csv_telechargement': 'Stahování oficiálního seznamu EdgeTX…',
        'etat_ecoute': 'Přehrávání {rang}/{total} — {nom}',
        'etat_generation_wav': 'Vytváření souboru WAV ({fait}/{total}) — '
                               '{nom}…',
        'etat_langue_voix': 'Jazyk: {langue} — dostupných hlasů: {n}',
        'etat_recherche_service': 'Hledání hlasů ve službě TTS…',
        'etat_recherche_voix': 'Hledání hlasu ({fait}/{total}) — {nom}…',
        'etat_sons_arret': 'Požadováno zastavení – dokončuje se aktuální '
                           'soubor…',
        'etat_voix_remises': 'Hlasy nejsou k dispozici: seznam obnoven na '
                             'výchozí',
        'etat_voix_retirees': 'Hlasů odstraněno službou: {n} — seznam '
                              'aktualizován',
        'msg_apercu_echec': 'Náhled se nepodařilo přehrát.\n\n{err}',
        'msg_audio_absent': 'Tento počítač nemá zvukový výstup: náhled nelze '
                            'přehrát. Soubory se přesto vytvářejí.',
        'msg_autres': '• … a další {n}',
        'msg_bilan_echecs': 'Vytvořeno souborů: {reussis} z {total}.\n'
                            '\n'
                            'Problémů: {problemes}\n'
                            '{detail}',
        'msg_csv_aucun_systeme': 'Oficiální seznam EdgeTX neobsahuje žádné '
                                 'systémové zvuky.\n'
                                 '\n'
                                 'Zkuste to později: soubor se mohl změnit.',
        'msg_csv_officiel_echec': 'Oficiální seznam EdgeTX se nepodařilo '
                                  'stáhnout.\n'
                                  '\n'
                                  'Zkontrolujte připojení k internetu a '
                                  'zkuste to znovu.\n'
                                  '\n'
                                  '{err}',
        'msg_dossier_echec': 'Cílovou složku se nepodařilo vytvořit.\n'
                             '\n'
                             '{err}',
        'msg_ecouter_rien': 'Označte řádek k přehrání.',
        'msg_export_echec': 'Export se nezdařil.\n\n{err}',
        'msg_export_ok': 'Exportováno řádků: {n}\n\n{chemin}',
        'msg_genere_deja': 'Generování už probíhá.\n\nPočkejte, až skončí.',
        'msg_generer_aucune': 'Žádný platný řádek k vytvoření.\n'
                              '\n'
                              'Je potřeba správný název souboru A věta.',
        'msg_generer_rien': 'Označte alespoň jeden řádek k vytvoření.',
        'msg_import_confirmer': 'Nahradit aktuální seznam ({avant}) těmito '
                                'řádky ({apres})?',
        'msg_import_illisible': 'Tento soubor nelze přečíst.\n\n{err}',
        'msg_import_ok': 'Importováno řádků: {n}.',
        'msg_import_oui': 'Ano, nahradit',
        'msg_import_vide': 'Tento soubor neobsahuje žádné řádky.',
        'msg_reseau_coupe': 'Připojení k internetu bylo přerušeno: '
                            'generování bylo zastaveno. Zkontrolujte '
                            'připojení a spusťte znovu.',
        'msg_sauvegarde_echec': 'Seznam se nepodařilo uložit.\n'
                                '\n'
                                '{err}\n'
                                '\n'
                                'Soubor možná používá jiný program '
                                '(antivirus, OneDrive), nebo Windows chrání '
                                'složku Dokumenty: v Zabezpečení Windows → '
                                '„Řízený přístup ke složkám“ povolte '
                                'Vox-Pack.',
        'msg_sons_arrete': 'Generování zastaveno.\n'
                           '\n'
                           'Vytvořeno souborů: {n}\n'
                           '\n'
                           '{dossier}',
        'msg_sons_bilan': 'Vytvořeno systémových souborů: {reussis} z '
                          '{total}.\n'
                          '\n'
                          'Problémů: {problemes}\n'
                          '{detail}',
        'msg_sons_cache': 'Oficiální seznam nestáhnut: použita uložená '
                          'kopie.',
        'msg_sons_copier': 'Zkopírujte tuto složku SYSTEM do '
                           'SOUNDS/{langue}/ na kartě a nahraďte starou.',
        'msg_sons_problemes': 'Problémů: {problemes}\n{detail}',
        'msg_sons_succes': 'Vytvořeno systémových souborů: {n}\n\n{dossier}',
        'msg_succes': 'Vaše hlasy jsou hotové.\n\n{dossier}',
        'msg_supprimer_rien': 'Označte alespoň jeden řádek ke smazání.',
        'msg_supprimer_tout': 'Chystáte se smazat CELÝ seznam.\n'
                              '\n'
                              'Při příštím spuštění aplikace bude '
                              'automaticky obnoven.\n'
                              '\n'
                              'Chcete pokračovat?'},
 'da': {'err_illisible': 'Stemmetjenesten returnerede et ulæseligt svar. '
                         'Prøv igen om lidt.',
        'err_lent': 'tjenesten svarede ikke i tide (langsom forbindelse?)',
        'err_refus': 'tjenesten afviste (stemmen er utilgængelig, eller '
                     'opdatering er nødvendig)',
        'err_reseau': 'ingen internetforbindelse',
        'err_reseau_detail': 'Kan ikke få forbindelse til Microsofts '
                             'stemmetjeneste. Tjek internetforbindelsen '
                             '(VPN, firewall, DNS), og prøv igen.',
        'err_voix_absente': 'stemmen er fjernet af tjenesten: vælg en anden',
        'etat_avance': '{fait} af {total} filer — {nom}',
        'etat_csv_telechargement': 'Downloader den officielle EdgeTX-liste…',
        'etat_ecoute': 'Afspiller {rang}/{total} — {nom}',
        'etat_generation_wav': 'Opretter WAV-filen ({fait}/{total}) — {nom}…',
        'etat_langue_voix': 'Sprog: {langue} — {n} stemmer tilgængelige',
        'etat_recherche_service': 'Søger efter stemmerne i TTS-tjenesten…',
        'etat_recherche_voix': 'Søger efter stemmen ({fait}/{total}) — '
                               '{nom}…',
        'etat_sons_arret': 'Stop anmodet – afslutter den aktuelle fil…',
        'etat_voix_remises': 'Stemmer utilgængelige: listen gendannet til '
                             'standard',
        'etat_voix_retirees': 'Stemmer fjernet af tjenesten: {n} — listen '
                              'opdateret',
        'msg_apercu_echec': 'Forhåndsvisningen kunne ikke afspilles.\n'
                            '\n'
                            '{err}',
        'msg_audio_absent': 'Denne computer har ingen lydudgang: '
                            'forhåndsvisningen kan ikke afspilles. Filerne '
                            'oprettes alligevel.',
        'msg_autres': '• … og {n} mere',
        'msg_bilan_echecs': 'Oprettede filer: {reussis} af {total}.\n'
                            '\n'
                            'Problemer: {problemes}\n'
                            '{detail}',
        'msg_csv_aucun_systeme': 'Den officielle EdgeTX-liste indeholder '
                                 'ingen systemlyde.\n'
                                 '\n'
                                 'Prøv igen senere: filen kan være ændret.',
        'msg_csv_officiel_echec': 'Den officielle EdgeTX-liste kunne ikke '
                                  'downloades.\n'
                                  '\n'
                                  'Tjek internetforbindelsen, og prøv igen.\n'
                                  '\n'
                                  '{err}',
        'msg_dossier_echec': 'Målmappen kunne ikke oprettes.\n\n{err}',
        'msg_ecouter_rien': 'Markér en linje, der skal afspilles.',
        'msg_export_echec': 'Eksporten mislykkedes.\n\n{err}',
        'msg_export_ok': 'Eksporterede linjer: {n}\n\n{chemin}',
        'msg_genere_deja': 'Der er allerede en generering i gang.\n'
                           '\n'
                           'Vent, til den er færdig.',
        'msg_generer_aucune': 'Ingen gyldig linje at generere.\n'
                              '\n'
                              'Der kræves et korrekt filnavn OG en sætning.',
        'msg_generer_rien': 'Markér mindst én linje, der skal genereres.',
        'msg_import_confirmer': 'Erstatte den aktuelle liste ({avant}) med '
                                'disse {apres} linjer?',
        'msg_import_illisible': 'Denne fil kan ikke læses.\n\n{err}',
        'msg_import_ok': 'Importerede linjer: {n}.',
        'msg_import_oui': 'Ja, erstat',
        'msg_import_vide': 'Denne fil indeholder ingen linjer.',
        'msg_reseau_coupe': 'Internetforbindelsen blev afbrudt: genereringen '
                            'blev stoppet. Tjek forbindelsen, og start igen.',
        'msg_sauvegarde_echec': 'Listen kunne ikke gemmes.\n'
                                '\n'
                                '{err}\n'
                                '\n'
                                'Et andet program bruger måske filen '
                                '(antivirus, OneDrive), eller Windows '
                                'beskytter mappen Dokumenter: i '
                                'Windows-sikkerhed → »Kontrolleret mappe '
                                'adgang«, tillad Vox-Pack.',
        'msg_sons_arrete': 'Generering stoppet.\n'
                           '\n'
                           'Oprettede filer: {n}\n'
                           '\n'
                           '{dossier}',
        'msg_sons_bilan': 'Oprettede systemfiler: {reussis} af {total}.\n'
                          '\n'
                          'Problemer: {problemes}\n'
                          '{detail}',
        'msg_sons_cache': 'Den officielle liste blev ikke downloadet: den '
                          'gemte kopi blev brugt.',
        'msg_sons_copier': 'Kopier mappen SYSTEM til SOUNDS/{langue}/ på dit '
                           'kort, og erstat den gamle.',
        'msg_sons_problemes': 'Problemer: {problemes}\n{detail}',
        'msg_sons_succes': 'Oprettede systemfiler: {n}\n\n{dossier}',
        'msg_succes': 'Dine stemmer er klar.\n\n{dossier}',
        'msg_supprimer_rien': 'Markér mindst én linje, der skal slettes.',
        'msg_supprimer_tout': 'Du er ved at slette HELE listen.\n'
                              '\n'
                              'Den genskabes automatisk, næste gang '
                              'programmet starter.\n'
                              '\n'
                              'Vil du fortsætte?'},
 'ja': {'err_illisible': '音声サービスから読み取れない応答が返されました。しばらくしてからもう一度お試しください。',
        'err_lent': 'サービスが時間内に応答しませんでした（接続が遅い？）',
        'err_refus': 'サービスに拒否されました（音声が利用できないか、更新が必要です）',
        'err_reseau': 'インターネット接続がありません',
        'err_reseau_detail': 'Microsoft '
                             'の音声サービスに接続できません。インターネット接続（VPN、ファイアウォール、DNS）を確認して、もう一度お試しください。',
        'err_voix_absente': 'サービスから音声が削除されました。別の音声を選んでください',
        'etat_avance': '{fait}/{total} ファイル — {nom}',
        'etat_csv_telechargement': 'EdgeTX の公式リストをダウンロード中…',
        'etat_ecoute': '試聴 {rang}/{total} — {nom}',
        'etat_generation_wav': 'WAV ファイルを作成中（{fait}/{total}）— {nom}…',
        'etat_langue_voix': '言語: {langue} — 利用できる声: {n}',
        'etat_recherche_service': 'TTS サービスで声を検索中…',
        'etat_recherche_voix': '声を検索中（{fait}/{total}）— {nom}…',
        'etat_sons_arret': '停止要求 — 現在のファイルを終了しています…',
        'etat_voix_remises': '声が利用できません：リストを既定に戻しました',
        'etat_voix_retirees': 'サービスが削除した声: {n} — リストを更新しました',
        'msg_apercu_echec': '試聴を再生できませんでした。\n\n{err}',
        'msg_audio_absent': 'このコンピューターには音声出力がありません。試聴は再生できません。ファイルは通常どおり作成されます。',
        'msg_autres': '• … ほか {n} 件',
        'msg_bilan_echecs': '作成したファイル: {total} 件中 {reussis} 件\n'
                            '\n'
                            '問題: {problemes} 件\n'
                            '{detail}',
        'msg_csv_aucun_systeme': 'EdgeTX の公式リストにシステム音がありません。\n'
                                 '\n'
                                 '後でもう一度お試しください。ファイルが変わった可能性があります。',
        'msg_csv_officiel_echec': 'EdgeTX の公式リストをダウンロードできませんでした。\n'
                                  '\n'
                                  'インターネット接続を確認して、もう一度お試しください。\n'
                                  '\n'
                                  '{err}',
        'msg_dossier_echec': '保存先フォルダーを作成できません。\n\n{err}',
        'msg_ecouter_rien': '試聴する行にチェックを入れてください。',
        'msg_export_echec': '書き出しに失敗しました。\n\n{err}',
        'msg_export_ok': '書き出した行: {n}\n\n{chemin}',
        'msg_genere_deja': 'すでに生成中です。\n\n終わるまでお待ちください。',
        'msg_generer_aucune': '生成できる有効な行がありません。\n\n正しいファイル名とフレーズの両方が必要です。',
        'msg_generer_rien': '生成する行を少なくとも 1 つ選んでください。',
        'msg_import_confirmer': '現在のリスト（{avant} 行）を、この {apres} 行に置き換えますか？',
        'msg_import_illisible': 'このファイルを読み取れません。\n\n{err}',
        'msg_import_ok': '読み込んだ行: {n}',
        'msg_import_oui': 'はい、置き換える',
        'msg_import_vide': 'このファイルには行がありません。',
        'msg_reseau_coupe': 'インターネット接続が切れたため、生成を停止しました。接続を確認して、もう一度開始してください。',
        'msg_sauvegarde_echec': 'リストを保存できませんでした。\n'
                                '\n'
                                '{err}\n'
                                '\n'
                                '別のプログラム（ウイルス対策、OneDrive）がこのファイルを使用しているか、Windows '
                                'が「ドキュメント」フォルダーを保護しています。Windows セキュリティ → '
                                '「フォルダー アクセスの制御」で Vox-Pack を許可してください。',
        'msg_sons_arrete': '生成を停止しました。\n\n作成したファイル: {n}\n\n{dossier}',
        'msg_sons_bilan': '作成したシステム音: {total} 件中 {reussis} 件\n'
                          '\n'
                          '問題: {problemes} 件\n'
                          '{detail}',
        'msg_sons_cache': '公式リストをダウンロードできなかったため、保存済みのコピーを使いました。',
        'msg_sons_copier': 'この SYSTEM フォルダーをカードの SOUNDS/{langue}/ '
                           'にコピーし、古いものを置き換えてください。',
        'msg_sons_problemes': '問題: {problemes} 件\n{detail}',
        'msg_sons_succes': '作成したシステム音: {n}\n\n{dossier}',
        'msg_succes': '音声の準備ができました。\n\n{dossier}',
        'msg_supprimer_rien': '削除する行を少なくとも 1 つ選んでください。',
        'msg_supprimer_tout': 'リスト全体を削除しようとしています。\n'
                              '\n'
                              '次回アプリを起動したときに自動で再作成されます。\n'
                              '\n'
                              '続けますか？'},
 'cn': {'err_illisible': '语音服务返回了无法读取的响应。请稍后再试。',
        'err_lent': '服务未能及时响应（网络很慢？）',
        'err_refus': '服务拒绝了请求（语音不可用或需要更新）',
        'err_reseau': '没有网络连接',
        'err_reseau_detail': '无法连接 Microsoft 语音服务。请检查网络连接（VPN、防火墙、DNS），然后重试。',
        'err_voix_absente': '该语音已被服务删除：请选择其他语音',
        'etat_avance': '第 {fait} / {total} 个文件 — {nom}',
        'etat_csv_telechargement': '正在下载 EdgeTX 官方列表…',
        'etat_ecoute': '试听 {rang}/{total} — {nom}',
        'etat_generation_wav': '正在生成 WAV 文件（{fait}/{total}）— {nom}…',
        'etat_langue_voix': '语言：{langue} — 可用语音：{n}',
        'etat_recherche_service': '正在 TTS 服务中查找语音…',
        'etat_recherche_voix': '正在查找语音（{fait}/{total}）— {nom}…',
        'etat_sons_arret': '已请求停止：正在结束当前文件…',
        'etat_voix_remises': '语音不可用：已恢复默认列表',
        'etat_voix_retirees': '服务已删除的语音：{n} — 列表已更新',
        'msg_apercu_echec': '无法播放试听。\n\n{err}',
        'msg_audio_absent': '这台电脑没有音频输出：无法播放试听。文件仍会正常生成。',
        'msg_autres': '• … 另有 {n} 条',
        'msg_bilan_echecs': '已创建文件：{reussis} / {total}\n'
                            '\n'
                            '问题：{problemes} 个\n'
                            '{detail}',
        'msg_csv_aucun_systeme': 'EdgeTX 官方列表中没有系统提示音。\n\n请稍后再试：文件可能已经变化。',
        'msg_csv_officiel_echec': '无法下载 EdgeTX 官方列表。\n'
                                  '\n'
                                  '请检查网络连接，然后重试。\n'
                                  '\n'
                                  '{err}',
        'msg_dossier_echec': '无法创建目标文件夹。\n\n{err}',
        'msg_ecouter_rien': '请勾选一行要试听的内容。',
        'msg_export_echec': '导出失败。\n\n{err}',
        'msg_export_ok': '已导出行数：{n}\n\n{chemin}',
        'msg_genere_deja': '已有生成任务正在进行。\n\n请等待完成。',
        'msg_generer_aucune': '没有可生成的有效行。\n\n需要正确的文件名和短语。',
        'msg_generer_rien': '请至少勾选一行来生成。',
        'msg_import_confirmer': '用这 {apres} 行替换当前列表（{avant} 行）吗？',
        'msg_import_illisible': '无法读取此文件。\n\n{err}',
        'msg_import_ok': '已导入行数：{n}',
        'msg_import_oui': '是，替换',
        'msg_import_vide': '此文件没有任何行。',
        'msg_reseau_coupe': '网络连接中断：生成已停止。请检查连接后重新开始。',
        'msg_sauvegarde_echec': '无法保存列表。\n'
                                '\n'
                                '{err}\n'
                                '\n'
                                '可能有其他程序（杀毒软件、OneDrive）正在使用此文件，或者 Windows '
                                '保护了“文档”文件夹：请在 Windows 安全中心 →“受控文件夹访问”中允许 '
                                'Vox-Pack。',
        'msg_sons_arrete': '生成已停止。\n\n已创建文件：{n}\n\n{dossier}',
        'msg_sons_bilan': '已创建系统文件：{reussis} / {total}\n'
                          '\n'
                          '问题：{problemes} 个\n'
                          '{detail}',
        'msg_sons_cache': '未下载官方列表：使用了已保存的副本。',
        'msg_sons_copier': '将此 SYSTEM 文件夹复制到存储卡的 SOUNDS/{langue}/，替换旧的。',
        'msg_sons_problemes': '问题：{problemes} 个\n{detail}',
        'msg_sons_succes': '已创建系统文件：{n}\n\n{dossier}',
        'msg_succes': '你的语音已准备好。\n\n{dossier}',
        'msg_supprimer_rien': '请至少勾选一行要删除的内容。',
        'msg_supprimer_tout': '你将删除整个列表。\n\n下次启动应用时会自动重建。\n\n要继续吗？'},
 'tw': {'err_illisible': '語音服務傳回了無法讀取的回應。請稍後再試。',
        'err_lent': '服務未能及時回應（網路很慢？）',
        'err_refus': '服務拒絕了請求（語音無法使用或需要更新）',
        'err_reseau': '沒有網路連線',
        'err_reseau_detail': '無法連線到 Microsoft '
                             '語音服務。請檢查網路連線（VPN、防火牆、DNS），然後再試一次。',
        'err_voix_absente': '該語音已被服務刪除：請選擇其他語音',
        'etat_avance': '第 {fait} / {total} 個檔案 — {nom}',
        'etat_csv_telechargement': '正在下載 EdgeTX 官方清單…',
        'etat_ecoute': '試聽 {rang}/{total} — {nom}',
        'etat_generation_wav': '正在產生 WAV 檔案（{fait}/{total}）— {nom}…',
        'etat_langue_voix': '語言：{langue} — 可用語音：{n}',
        'etat_recherche_service': '正在 TTS 服務中尋找語音…',
        'etat_recherche_voix': '正在尋找語音（{fait}/{total}）— {nom}…',
        'etat_sons_arret': '已要求停止：正在結束目前檔案…',
        'etat_voix_remises': '語音無法使用：已還原預設清單',
        'etat_voix_retirees': '服務已刪除的語音：{n} — 清單已更新',
        'msg_apercu_echec': '無法播放試聽。\n\n{err}',
        'msg_audio_absent': '這台電腦沒有音訊輸出：無法播放試聽。檔案仍會正常產生。',
        'msg_autres': '• … 另有 {n} 條',
        'msg_bilan_echecs': '已建立檔案：{reussis} / {total}\n'
                            '\n'
                            '問題：{problemes} 個\n'
                            '{detail}',
        'msg_csv_aucun_systeme': 'EdgeTX 官方清單中沒有系統音效。\n\n請稍後再試：檔案可能已經變更。',
        'msg_csv_officiel_echec': '無法下載 EdgeTX 官方清單。\n'
                                  '\n'
                                  '請檢查網路連線，然後再試一次。\n'
                                  '\n'
                                  '{err}',
        'msg_dossier_echec': '無法建立目標資料夾。\n\n{err}',
        'msg_ecouter_rien': '請勾選一行要試聽的內容。',
        'msg_export_echec': '匯出失敗。\n\n{err}',
        'msg_export_ok': '已匯出行數：{n}\n\n{chemin}',
        'msg_genere_deja': '已有產生作業正在進行。\n\n請等待完成。',
        'msg_generer_aucune': '沒有可產生的有效行。\n\n需要正確的檔案名稱和短句。',
        'msg_generer_rien': '請至少勾選一行來產生。',
        'msg_import_confirmer': '用這 {apres} 行取代目前清單（{avant} 行）嗎？',
        'msg_import_illisible': '無法讀取這個檔案。\n\n{err}',
        'msg_import_ok': '已匯入行數：{n}',
        'msg_import_oui': '是，取代',
        'msg_import_vide': '這個檔案沒有任何行。',
        'msg_reseau_coupe': '網路連線中斷：產生已停止。請檢查連線後重新開始。',
        'msg_sauvegarde_echec': '無法儲存清單。\n'
                                '\n'
                                '{err}\n'
                                '\n'
                                '可能有其他程式（防毒軟體、OneDrive）正在使用這個檔案，或 Windows '
                                '保護了「文件」資料夾：請在 Windows 安全性 →「受控資料夾存取權」中允許 '
                                'Vox-Pack。',
        'msg_sons_arrete': '產生已停止。\n\n已建立檔案：{n}\n\n{dossier}',
        'msg_sons_bilan': '已建立系統檔案：{reussis} / {total}\n'
                          '\n'
                          '問題：{problemes} 個\n'
                          '{detail}',
        'msg_sons_cache': '未下載官方清單：使用了已儲存的副本。',
        'msg_sons_copier': '將此 SYSTEM 資料夾複製到記憶卡的 SOUNDS/{langue}/，取代舊的。',
        'msg_sons_problemes': '問題：{problemes} 個\n{detail}',
        'msg_sons_succes': '已建立系統檔案：{n}\n\n{dossier}',
        'msg_succes': '你的語音已準備好。\n\n{dossier}',
        'msg_supprimer_rien': '請至少勾選一行要刪除的內容。',
        'msg_supprimer_tout': '你將刪除整個清單。\n\n下次啟動應用程式時會自動重建。\n\n要繼續嗎？'},
 'hk': {'err_illisible': '語音服務回傳咗讀唔到嘅回應。請遲啲再試。',
        'err_lent': '服務未能及時回應（網絡好慢？）',
        'err_refus': '服務拒絕咗請求（語音用唔到或者要更新）',
        'err_reseau': '冇網絡連線',
        'err_reseau_detail': '連唔到 Microsoft 語音服務。請檢查網絡連線（VPN、防火牆、DNS），然後再試。',
        'err_voix_absente': '呢個語音俾服務刪咗：請揀第二個',
        'etat_avance': '第 {fait} / {total} 個檔案 — {nom}',
        'etat_csv_telechargement': '正在下載 EdgeTX 官方清單…',
        'etat_ecoute': '試聽 {rang}/{total} — {nom}',
        'etat_generation_wav': '正在產生 WAV 檔案（{fait}/{total}）— {nom}…',
        'etat_langue_voix': '語言：{langue} — 可用語音：{n}',
        'etat_recherche_service': '正在 TTS 服務度搵緊語音…',
        'etat_recherche_voix': '正在搵緊語音（{fait}/{total}）— {nom}…',
        'etat_sons_arret': '已要求停止：正在完成而家嘅檔案…',
        'etat_voix_remises': '語音用唔到：已還原預設清單',
        'etat_voix_retirees': '服務刪除咗嘅語音：{n} — 清單已更新',
        'msg_apercu_echec': '播唔到試聽。\n\n{err}',
        'msg_audio_absent': '呢部電腦冇音訊輸出：播唔到試聽。檔案照樣會產生。',
        'msg_autres': '• … 仲有 {n} 條',
        'msg_bilan_echecs': '已建立檔案：{reussis} / {total}\n'
                            '\n'
                            '問題：{problemes} 個\n'
                            '{detail}',
        'msg_csv_aucun_systeme': 'EdgeTX 官方清單冇系統音效。\n\n請遲啲再試：檔案可能已經變咗。',
        'msg_csv_officiel_echec': '下載唔到 EdgeTX 官方清單。\n'
                                  '\n'
                                  '請檢查網絡連線，然後再試。\n'
                                  '\n'
                                  '{err}',
        'msg_dossier_echec': '建立唔到目標資料夾。\n\n{err}',
        'msg_ecouter_rien': '請勾選一行要試聽嘅內容。',
        'msg_export_echec': '匯出失敗。\n\n{err}',
        'msg_export_ok': '已匯出行數：{n}\n\n{chemin}',
        'msg_genere_deja': '已經有產生緊。\n\n等佢完成先。',
        'msg_generer_aucune': '冇可以產生嘅有效行。\n\n要有正確檔案名同短句。',
        'msg_generer_rien': '請至少勾選一行嚟產生。',
        'msg_import_confirmer': '用呢 {apres} 行取代而家嘅清單（{avant} 行）？',
        'msg_import_illisible': '讀唔到呢個檔案。\n\n{err}',
        'msg_import_ok': '已匯入行數：{n}',
        'msg_import_oui': '係，取代',
        'msg_import_vide': '呢個檔案冇任何行。',
        'msg_reseau_coupe': '網絡連線中斷：產生已停止。請檢查連線再重新開始。',
        'msg_sauvegarde_echec': '儲存唔到清單。\n'
                                '\n'
                                '{err}\n'
                                '\n'
                                '可能有其他程式（防毒、OneDrive）用緊呢個檔案，或者 Windows '
                                '保護咗「文件」資料夾：請喺 Windows 安全性 →「受控資料夾存取權」度允許 '
                                'Vox-Pack。',
        'msg_sons_arrete': '產生已停止。\n\n已建立檔案：{n}\n\n{dossier}',
        'msg_sons_bilan': '已建立系統檔案：{reussis} / {total}\n'
                          '\n'
                          '問題：{problemes} 個\n'
                          '{detail}',
        'msg_sons_cache': '未下載官方清單：用咗已儲存嘅副本。',
        'msg_sons_copier': '將呢個 SYSTEM 資料夾複製到記憶卡嘅 SOUNDS/{langue}/，取代舊嘅。',
        'msg_sons_problemes': '問題：{problemes} 個\n{detail}',
        'msg_sons_succes': '已建立系統檔案：{n}\n\n{dossier}',
        'msg_succes': '你嘅語音準備好喇。\n\n{dossier}',
        'msg_supprimer_rien': '請至少勾選一行要刪除嘅內容。',
        'msg_supprimer_tout': '你會刪除成個清單。\n\n下次開應用程式時會自動重建。\n\n繼續？'}}

for _lot in (LOT_0, LOT_DIALOGUES, LOT_NOMS, LOT_VOIX, LOT_DIVERS,
             LOT_GENERATION, LOT_AIDE):
    for _code, _textes in _lot.items():
        TEXTES[_code].update(_textes)


def verifier() -> list[str]:
    """Signale une table absente et un texte vide.

    La complétude, elle, se mesure sur les tables fusionnées de
    l'application (celles de la 1.5.1 + ces lots) : c'est le rôle de
    `tests/v2_langues.py`. Ici on ne peut vérifier que le paquet lui-même,
    puisque les textes de la 1.5.1 vivent encore dans voxpack2.py.
    """
    ecarts = []
    for code in LANGUES_TEXTES:
        if code not in TEXTES:
            ecarts.append(f"{code} : pas de table")
    for code, table in TEXTES.items():
        for cle, texte in table.items():
            if not str(texte).strip():
                ecarts.append(f"{code} : « {cle} » est vide")
    return ecarts


if __name__ == "__main__":
    import sys

    problemes = verifier()
    total = sum(len(table) for table in TEXTES.values())
    print(f"{len(TEXTES)} langues, {len(TEXTES['fr'])} clés, "
          f"{total} chaînes")
    if problemes:
        for probleme in problemes:
            print("  écart :", probleme)
        sys.exit(1)
    print("aucune table absente, aucun texte vide")
