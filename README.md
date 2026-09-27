# Vanadinite Barrage

Full-colour **Python 3 + pygame** tower-lite arcade for [ElbowOS](https://x.com/ElbowOS).
Slide a vanadinite mortar across five ember lanes and lob charged shells at descending scout / heavy drones.

Featured: **https://x.com/ElbowOS**

## Play

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 vanadinite_barrage.py --play
```

Controls: **← →** move battery, **SPACE** fire, **R** reset, **Esc** quit.

## Record a 9:16 reel (headless)

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python3 vanadinite_barrage.py --record
```

Writes `/home/workdir/artifacts/VANADINITE_BARRAGE_ElbowOS.mp4` (1080×1920, 15s, 30fps, H.264).

## Links

- Reel on Drive: https://drive.google.com/file/d/1EVBgNuykB59vsbKpwaocLkZPu6xAnRtN/view?usp=drivesdk
- x.com/ElbowOS: https://x.com/ElbowOS
