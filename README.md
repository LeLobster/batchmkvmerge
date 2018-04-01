# batchmkvmerge
Helper script to easily batch remux .mkv files using MKVToolNix

---
Requires MKVToolNix to be installed.  
https://mkvtoolnix.download/downloads.html  

**ONLY TESTED ON LINUX** but should work on Windows/Mac as well

Probably need to install `colorama` and `send2trash` via `pip3 install` first.  
Then run the scipt with `-h` or `--help` to see usage information.

```
By default it will discard everything but the first video and audio track and it's flags

-h, --help                     Display this help section
-i, --in-path                  Input path
-o, --out-path                 Output path
	-o can not be the same as -i, but can be a new folder inside -i
	When not specified -i will be the current working dir
	and -o will be a new folder named [REMUXED] inside that dir

-a, --audio-lang               Keep audio of this language (Example: -a jpn)
-s, --sub-lang                 Keep subtitle(s) of this language (Example: -s eng)
-S, --keep-all-sub             Keep all subtitles (overrides --no-dupe)
-x, --extract-sub              Extract subtitle(s) of this language (Example: -x eng) (overrides -s\-S)
-X, --extract-all-sub          Extract all subtitles (overrides -s\-S)
-k, --keepatt-type             Only keep attachments of this type (Example: -k font)
-K, --keep-att                 Keep all attachments
-t, --keep-track-titles        Keep track titles
-T, --keep-title               Keep file title
-c, --keep-chapt               Keep chapters
	For -a, -s, -x and -k multiple values can be specified (Example: -s eng,jpn)

--no-dupe                      If multiple types of the same language are found only keep the first
--new-folder                   Create a new folder in -o for each processed file (uses file name)
--sub-folders                  Also check in any subfolders of -i for mkv files to process
--trash-files                  Move original files to the trash when a remux is finished
-v, --verbose                  Prints extra information during the process
--nc                           Disables colored output
--simulate                     Do a test run which doesn't process any files, just outputs information
	--simulate includes the verbose argument

--pass-along                   Optional 'global' commands to pass along to MKVMerge, wrapped in "'s
	Example: --pass-along "--default-language eng"
```
