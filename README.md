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

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`imageio-ffmpeg` fournit un binaire `ffmpeg` embarqué utilisé pour décoder les
formats compressés. Un `ffmpeg` installé sur le système est également détecté
automatiquement (ou via la variable d'environnement `FFMPEG_PATH`).

## Utilisation

```bash
python main.py                 # puis « Ouvrir un fichier audio… »
python main.py mon_fichier.mp3 # ouverture directe
```

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
