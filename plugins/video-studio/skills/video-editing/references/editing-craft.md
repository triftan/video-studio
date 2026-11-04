# Editing craft

## Talking head and interviews

1. **Find the story** in the transcript before cutting: hook, 2 to 4 points, payoff, call to action.
2. **Retakes:** when the speaker repeats a sentence, keep the last complete, confident take. Search `words.json` for repeated 3-word sequences to find them.
3. **Fillers:** cut "um", "uh", "er", "like" (as filler), "you know", "sort of", false starts. Don't cut fillers that carry rhythm or meaning.
4. **Pauses:** trim gaps over ~0.6 s down to ~0.25 s. Keep a longer pause before a punchline or reveal.
5. **Padding:** 80 to 150 ms before the first phoneme and after the last. Clipped consonants are the most common amateur tell.
6. **Jump cuts:** alternate framing on each cut (wide, then 1.12x punch, then wide). Or cover with B-roll that illustrates the line.
7. **Multi-cam:** cut to the listener for reactions, to the speaker for content. Never cut mid-word.

## Pacing by format

| Format | Typical shot length | Notes |
| --- | --- | --- |
| TikTok / Reels / Shorts | 1.5 to 3 s | Hook in 1 to 2 s. Captions always on. Loop the ending into the start if possible. |
| YouTube long form | 4 to 10 s | Pattern interrupt every 20 to 40 s (B-roll, graphic, zoom, music change). |
| Podcast clip | 3 to 6 s | Pull a self-contained 30 to 90 s moment that starts mid-energy. |
| Tutorial / screen demo | Follows the action | Speed up waiting (2x to 8x), zoom into the cursor area, cut dead mouse movement. |

## Making shorts from long footage

1. Score candidate moments in the transcript: a clear claim, a story with a turn, a strong opinion, a surprising number.
2. Each short must stand alone: no "as I said earlier".
3. Start on the most interesting sentence, even if it's mid-thought. Add context with an on-screen title instead of a slow intro.
4. Reframe to 9:16 around the speaker's face. Big captions (1 to 3 words per page).

## B-roll

- Illustrate the noun or verb being said, landing 0 to 6 frames before the word.
- Hold B-roll at least 1.5 s, and no longer than the sentence it covers.
- Keep the speaker's audio continuous underneath.

## Music

- Pick music by energy first, genre second. Start at a musical phrase, not in the middle of a bar.
- Cut on beats for montage sections. Detect beats with `aubio beat music.mp3` or `librosa.beat.beat_track`.
- End on the musical resolution. Fade 1 to 2 s if you can't.

## Transitions

Default is the hard cut. Use effects with intent:

- **Cross dissolve / organic light dissolve:** time passing, a softer mood.
- **Dip to black:** chapter break.
- **Whip pan, flash, impact shake, anticipation zoom:** energy, hype, a beat drop.
- **Push / slide / wipe:** listicles, step changes, screen demos.
- **Rack focus, luma blend:** cinematic or emotional.

Full list with parameters: `../../../styles/transitions.json`.

## Final checklist

- [ ] First 3 s hook works with the sound off (captions or a title).
- [ ] No clipped words, no audio pops at cuts (use 10 to 20 ms audio fades at every cut).
- [ ] Captions match the final audio. Re-time after every cut.
- [ ] Loudness: -14 LUFS (social) or -16 (podcast), true peak at or below -1 dB.
- [ ] Nothing important in the platform's UI zones (9:16: keep text out of the bottom ~20% and the right ~12%).
- [ ] Ends cleanly: no black tail and no cut-off music.
