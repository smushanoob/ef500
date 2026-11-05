# What if sharks got 3× bigger and doubled in number? (what-if Short, 2:10)

**Final video:** `what-if-sharks-got-3x-bigger.mp4` (1080x1920, 30 fps, H.264 + AAC, -14 LUFS, 130 s)

Hook in the first second (real footage + "3× BIGGER"), live "SHARKS ON EARTH" counter in the header, word-by-word captions,
and an explicit comment prompt at the end ("Which shark would scare you most at three times the size?").

## Beats
1. Hook: real deep-sea shark footage, "3× BIGGER / 2× MORE"
2. Shark numbers: ~100 million killed by humans per year ≈ 7% of all sharks → ~1.4 billion sharks; doubled → 2.8 billion
3. 3D: a diver next to a 4.5 m great white that grows to 13.5 m (school-bus outline, "1 ton → 27 tons", square-cube law)
4. 3D true-to-scale lineup: whale shark ×3 = 36 m vs blue whale (~30 m record), great white ×3, school bus, you
5. Hunger: food per shark ×12 (metabolism ∝ mass^0.75; 27^0.75 ≈ 12), ×2 sharks → ×24; prey-collapse chart (illustrative)
6. Maps (NASA Blue Marble): seal colonies (South Africa, California, Australia); tiger sharks following humpback whales;
   big-shark range expanding poleward (North Sea, Norway, Alaska); bull shark 1,000+ miles up the Mississippi to Alton, Illinois
7. 3D: a swimmer at the surface with giant sharks passing underneath; "RIGHT WHERE WE SWIM"
8. **Real data**: ISAF 2025 unprovoked bites by country, 65 worldwide (9 fatal): USA 25, Australia 21, Bahamas 5, New Zealand 3, South Africa 1, Mozambique 1
9. What-if estimate (clearly labelled "rough estimate · not real data"): ~6× → ~420/year, new countries (UK, Canada, Norway)
10. Beach closures; 3D: a 13.5 m shark rams an 8 m fishing boat
11. Twist: sharks eat the ocean empty, starve, and crash below today's numbers (boom-and-bust chart)
12. Ending: "the deadliest predator in the ocean... it's us" (real estimate: ~100 million sharks/year), then the comment prompt

Numbers marked as estimates are speculative; real data is labelled REAL DATA / REAL WORLD on screen.

## Data sources
- International Shark Attack File, Florida Museum of Natural History: 2025 worldwide summary (unprovoked bites by country).
- Worm, B. et al. (2013), "Global catches, exploitation rates, and rebuilding options for sharks", *Marine Policy* 40: 194-204
  (~100 million sharks killed per year; exploitation rate 6.4-7.9%/yr; the ~1.4 billion population figure is derived from these two numbers).
- Bull shark record ~1,100 river miles up the Mississippi at Alton, Illinois (1937).

## Footage, imagery, audio and licensing
- Real shark footage: **NOAA Ocean Exploration** (U.S. federal government work, public domain; mirrored on the Internet Archive with a Public Domain Mark):
  bluntnose sixgill shark (EX2206, 2022), deep-sea sharks feeding (2019), smalltooth sand tiger (EX1605), Greenland shark (EX1304), dogfish shark (EX1905).
  Suggested credit: "Footage: NOAA Office of Ocean Exploration and Research."
- 3D scenes (sharks, whale shark, blue whale, boat, bus outline, underwater environment) are procedural and made for this video.
  The diver uses the Mixamo "X Bot" character (royalty-free in rendered video; raw file not redistributed).
- World map: NASA Blue Marble with topography and bathymetry (public domain). Rivers: Natural Earth (public domain).
- Flags: flag-icons (MIT). Voice: Kokoro-82M TTS (Apache-2.0), voice `am_michael`. Font: Montserrat (SIL OFL).
- Music and sound effects: synthesized for this video (no third-party audio; the score deliberately avoids any famous shark-movie motif).

## Upload kit
- **Title:** What if sharks got 3× bigger? 🦈
- **Description:** Every shark on Earth gets three times bigger, and there are twice as many. Here's what happens to the ocean, the coasts and us. Which shark would scare you most? 👇 #sharks #whatif #ocean #science #shorts
  Credits: Footage: NOAA Office of Ocean Exploration and Research. Map: NASA Blue Marble. Data: ISAF (Florida Museum), Worm et al. 2013.
- **Pinned comment:** "Great white, tiger, bull or hammerhead: which one would scare you most at 3× the size? 👇"

## Source (`source/`)
`sharks.html` (scene + overlays, `window.renderFrame(t)`), `render.js` (headless Chromium renderer), `plan.py` + `shotplan.json` (footage edit),
`script.json` + `tts2.py` (narration), `subs.py` (captions), `audio.py` (score/SFX), `mississippi.json` (river path), `voiceover.wav`.
