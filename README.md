# Niko

A 3D Niko from OneShot that lives on your desktop. It's an add-on for [serpantinum](https://github.com/ilyamiro/serpantinum) (Quickshell + Hyprland). You can chat with him, he reacts to what you're doing, sets reminders, controls music and cheers when you level up in Nullscape.

Chatting goes through Claude Code, so you need to be logged in to it (a Claude plan or an API key). Everything else works without.

## Install

You need serpantinum already running.

```bash
git clone https://github.com/lvyrize/niko ~/.config/niko-pet
~/.config/niko-pet/install.sh
```

It checks the packages, logs you in to Claude, patches serpantinum, asks what he should call you and starts him. After a serpantinum update run `./apply.sh` again.

## Commands

```
niko run | kill | restart | status
niko skins        use your own picture instead of the model (the file name becomes his name)
niko personality  default, tsundere, dumb, sarcastic, chaotic, cheerleader or your own
```

## Layout

`niko.patch` has the text changes, `files/` has the model and textures, `tools/` has the scripts I used to convert the model.

## License

Code is MIT, see [LICENSE](LICENSE). The model is a separate work under CC BY 4.0, see [CREDITS.md](CREDITS.md). Niko and OneShot belong to their creators, this is an unofficial fan project.
