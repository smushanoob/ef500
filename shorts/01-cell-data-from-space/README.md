# How your phone gets data from space (YouTube Short, 30s)

**Final video:** `cell-data-from-space.mp4` (1080x1920, 30 fps, 30.0 s, H.264 + AAC, mixed to -14 LUFS)

## Narration
> Your phone just talked to something moving 17,000 miles an hour.
> It's a cell tower... in space.
> A few hundred miles up, thousands of satellites are falling around Earth. Nonstop.
> They fly sideways so fast, they keep missing the ground. That's an orbit.
> Your phone fires radio waves, light you can't see, straight up.
> A satellite catches it, and passes it to the next one... with lasers.
> Down to a ground station, into the internet, and back to you.
> Faster than you can blink.
> So next time you've got no bars... look up.

## Suggested title / description
- Title: **Your Phone Is Talking to Space Right Now 🛰️**
- Description: How satellites beam cell service straight to your phone: orbits, radio waves, laser links and ground stations, in 30 seconds. #space #satellite #physics #science #shorts

## Credits and licensing (monetization safe)
- Earth imagery: NASA Blue Marble / Black Marble / city lights / cloud maps (NASA, public domain), plus NASA Blue Marble shaded-relief tiles for the Southeast US close-ups.
- Voice: Kokoro-82M neural TTS (Apache-2.0), voice `af_heart`. Swap `source/voiceover.wav` for your own AI voice and re-mix if you want.
- Music and sound effects: synthesized from scratch (`source/sfx.py`), no samples.
- 3D scene, satellites, captions: rendered with three.js (`source/scene.html`).

## Rebuild
`source/render.js` renders frames from `source/scene.html` (served locally) using headless Chromium; `source/tts.py` makes the voiceover plus word timings; `source/sfx.py` builds music and SFX; ffmpeg muxes everything together.
