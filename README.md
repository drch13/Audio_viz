# Audio_viz

Interface graphique de visualisation d'un signal audio.

## Fonctionnalités

- **Chargement multi-format** : `.wav`, `.flac`, `.ogg` (lus nativement) et
  `.mp3`, `.wma`, `.aac`, `.m4a`, `.opus`, etc. (décodés via `ffmpeg`).
- **Sélection d'une fenêtre temporelle** sur la forme d'onde : glisser-déposer
  sur le graphique du haut, ou saisie numérique des temps de début et de fin
  (en secondes, résolution milliseconde — ex. de 1,543 s à 1,843 s).
- **Deux graphiques** :
  1. le signal audio en fonction du temps ;
  2. le spectre des intensités (en dB) de chaque fréquence dans la fenêtre
     sélectionnée, calculé par transformée de Fourier rapide (FFT) avec une
     fenêtre de Hann.

## Mode utilisateur final (exécutable Windows)

Aucune installation de Python n'est nécessaire : téléchargez le fichier
`Audio_viz.exe` puis double-cliquez dessus.

- **Depuis une release** : sur la page GitHub du dépôt, section *Releases*
  (créées automatiquement à chaque tag `v*`, ex. `v1.0.0`), téléchargez
  `Audio_viz.exe` dans les fichiers joints.
- **Depuis l'onglet Actions** : ouvrez l'onglet *Actions*, sélectionnez le workflow
  « Build Audio_viz.exe » le plus récent (vert), puis téléchargez l'artifact
  `Audio_viz-windows` (bouton *Download*) et extrayez `Audio_viz.exe`.

Utilisation :

```text
Audio_viz.exe                  # puis « Ouvrir un fichier audio… »
Audio_viz.exe mon_fichier.mp3  # ouverture directe (glisser-déposer aussi possible)
```

Le binaire `ffmpeg` est embarqué dans l'exécutable : tous les formats
(mp3, wma, aac, m4a, opus, wav, flac, ogg, ...) fonctionnent sans rien installer.

## Mode développeur (ligne de commande)

```bash
python -m venv .venv
source .venv/bin/activate   # sous Windows : .venv\Scripts\activate
pip install -r requirements.txt
```

`imageio-ffmpeg` fournit un binaire `ffmpeg` embarqué utilisé pour décoder les
formats compressés. Un `ffmpeg` installé sur le système est également détecté
automatiquement (ou via la variable d'environnement `FFMPEG_PATH`).

```bash
python main.py                 # puis « Ouvrir un fichier audio… »
python main.py mon_fichier.mp3 # ouverture directe
```

Pour reconstruire soi-même l'exécutable (identique à la CI) :

```bash
pip install pyinstaller
# Linux/macOS (séparateur ':') :
pyinstaller --onefile --windowed --name Audio_viz --add-binary "$(python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())'):." main.py
# Windows (séparateur ';') :
pyinstaller --onefile --windowed --name Audio_viz --add-binary "$(python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())');." main.py
```

Le workflow CI (`.github/workflows/build-exe.yml`) effectue cette compilation
automatiquement à chaque push sur `main`, chaque pull request et chaque tag `v*`.

## Tests

```bash
python -m pytest tests/ -q
```

## Structure

```
main.py                  point d'entrée
audio_viz/
  app.py                 fenêtre PyQt5 + graphiques matplotlib
  audio_loader.py        chargement audio multi-format (soundfile + ffmpeg)
  spectrum.py            FFT (fenêtre de Hann) et sous-échantillonnage
tests/                   tests pytest (chargeur, spectre, GUI en offscreen)
```
