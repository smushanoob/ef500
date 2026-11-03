# What if WW3 broke out on the Moon? (fictional map-war Short, 2:56)

**Final video:** `ww3-on-the-moon.mp4` (1080x1920, 30 fps, H.264 + AAC, -14 LUFS, 176 s, just under the 3-minute Shorts limit)

> **This is a fictional scenario.** Every battle, unit, number, quote and headline is invented. The video carries a
> permanent "FICTIONAL SCENARIO" tag, and the news panel is a made-up channel ("LNN · Lunar News Network", marked
> "(FICTIONAL)"). No real news outlets or real people are named.

Built for the channel analytics: the cold open is already mid-battle at t=0 (flash-forward), there are on-screen
stakes in the first 1.5 s, word-by-word captions, and an explicit comment prompt at the end ("Which side would you have joined?").

## Sides
| Team | Members | Map colour |
|---|---|---|
| Artemis Coalition | United States, United Kingdom, France, Italy, Israel, South Korea, Australia, New Zealand (+ India from Day 19) | blue |
| Lunar Pact | China, Russia, North Korea, Iran | red |
| Non-aligned | India (until its Shiv Shakti base is shelled) | orange |
| Neutral / mediator | Brazil (hosts the Rio talks) | green |
| Shared zone (after the treaty) | both poles | cyan stripes |

## Timeline shown
1. Day 1: standoff over the Shackleton ice field (south pole)
2. Day 3: Pact armor seizes Shoemaker and Haworth craters
3. Coalition digs in on Shackleton's rim; on Earth, satellites go dark, markets crash, fleets face off
4. Day 19: Pact artillery hits India's Shiv Shakti Point base, and India joins the Coalition
5. Day 24-33: North Korean landing at Mare Crisium (Australia, New Zealand, South Korea respond)
6. Day 31-35: Russian far-side mass driver, destroyed by a British/Israeli commando raid
7. Day 40: Coalition counterattack from Tranquility Base, retaking Haworth
8. Iranian supply convoys; Day 62 the front freezes; Day 70 the failed Pact push at de Gerlache
9. Solar storm forces both sides underground → Brazil hosts talks in Rio → Treaty of Tranquility (poles shared, Moon weapon-free)

On-screen panels: day counter, "Forces on the Moon" and "Casualties" bars (top 6 countries + team totals; ~20,000
troops and ~4,400 casualties by the end), flag counters with NATO-style unit symbols for divisions and brigades, advance arrows,
battle flashes, lines of control that redraw as territory changes, and the LNN news feed (war / Earth / peace / misc headlines).
The battle cut-ins (Shackleton, Haworth, Crisium) are 3D scenes with armored rovers, artillery and landers. They use
lunar physics: no smoke, muzzle flashes only, and dust in low ballistic arcs at 1.62 m/s².

## Imagery, audio and licensing
- Moon colour map: NASA LRO / LROC via NASA SVS "CGI Moon Kit" (`lroc_color_poles_8k`), public domain.
- Moon relief: normal map computed from the NASA LRO LOLA elevation model (`ldem_16`) from the same kit, public domain.
- Place names and coordinates are real lunar features (Shackleton, Haworth, Shoemaker, de Gerlache, Mare Crisium, Shiv Shakti Point, etc.).
- Flags: [flag-icons](https://github.com/lipis/flag-icons) (MIT).
- Star background: Solar System Scope (CC BY 4.0).
- Earth texture (short "Back on Earth" beat): bundled texture from the `earth-visualization` npm package (MIT).
- Battle vehicles, landers, map overlay, music and all sound effects: procedurally generated for this video.
- Voice: Kokoro-82M TTS (Apache-2.0), voice `am_michael`. Font: Montserrat (SIL OFL).

Suggested description credit: "Moon imagery: NASA LRO / SVS CGI Moon Kit. Stars: Solar System Scope (CC BY 4.0). Flags: flag-icons (MIT). Fictional scenario; all events, numbers and headlines are made up."

## Upload kit
- **Title:** What if WW3 broke out on the Moon? 🌕
- **Description:** March 2049. Fourteen nations live on the Moon, and they all want the same frozen water. Which side would you have joined? 👇  #moon #space #whatif #ww3 #map #shorts
  (plus the credit line above)
- **Pinned comment:** "Coalition 🔵, Pact 🔴, or neutral like Brazil 🟢? Which side would you have joined? 👇"

## Source (`source/`)
- `moonwar.html`: three.js scene and overlay (territory Voronoi shader, units, arrows, battles, cut-ins, news, bars, camera); `window.renderFrame(t)`
- `render5.js`: headless Chromium frame renderer (`node render5.js frames --range 0 5280 30`)
- `script.json`, `tts2.py`: narration text and TTS script; `voiceover.wav` is the generated narration
- `subs6.py`: ASS caption builder; `audio7.py`: procedural score and SFX
