# ZenAI PDF fonts

All fonts here are licensed under the **SIL Open Font License 1.1** (commercial use allowed).

| Family | Role | Files | License |
|---|---|---|---|
| Noto Serif SC | Chinese titles & body (formal Song / 宋体风格) | `NotoSerifSC-*.ttf` | `OFL-NotoSerifSC.txt` |
| Noto Serif LGC | Latin / Greek / math fallback (μ、Ω、± 等) | `NotoSerifLGC-*.ttf` | `OFL-NotoSerifLGC.txt` |
| Space Mono | English labels, versions, page numbers | `SpaceMono-*.ttf` | `OFL-SpaceMono.txt` |

Sources: [notofonts/noto-cjk](https://github.com/notofonts/noto-cjk), [notofonts/latin-greek-cyrillic](https://github.com/notofonts/latin-greek-cyrillic) (via Fontsource subsets, merged), [googlefonts/spacemono](https://github.com/googlefonts/spacemono).

The renderer uses SC as the primary face and automatically switches missing glyphs (e.g. Greek `μ`) to the LGC companion so mixed CN / science notation does not tofu.
