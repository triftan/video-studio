# video-studio

A Claude Code plugin for making videos with an AI agent: edit real footage, add motion graphics, and produce narrated explainer videos. It comes with a one-time setup, Fish Audio voiceovers, a style advisor for when you don't know what look to use, and an offline catalog of every template and style.

## Install

In Claude Code:

```
/plugin marketplace add triftan/video-studio
/plugin install video-studio@video-studio
```

Restart Claude Code, then run the one-time setup:

```
/video-studio:setup
```

Setup checks ffmpeg, Node and Python, creates a workspace in `~/video-studio`, signs you in to Fish Audio for voiceovers and opens the style catalog.

Full documentation: [plugins/video-studio/README.md](plugins/video-studio/README.md)

## License

MIT. See [LICENSE](LICENSE). Third-party components keep their own licenses: the blue tint LUT is CC0 (Kdenlive), fonts load from Google Fonts under their own licenses, and Remotion has its own [license terms](https://www.remotion.dev/license).
