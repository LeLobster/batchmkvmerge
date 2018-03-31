#!/usr/bin/env python3
# coding=utf-8

import os
import sys
import getopt as go
import subprocess as sp
import json
import atexit
import shlex
# Cross platform terminal colors
# https://pypi.python.org/pypi/colorama
# https://github.com/tartley/colorama
import colorama as cr
# Cross platform trashing of files
# https://pypi.python.org/pypi/Send2Trash
from send2trash import send2trash

cr.init(autoreset=True)
# Deinitialize colorama colors
atexit.register(cr.deinit)

# Use colorama to print ascii color codes with status messages
stat_m = {
    'file': cr.Fore.YELLOW,
    'err': cr.Fore.RED + '[ERROR] ',
    'warn': cr.Fore.RED + '[WARNING] ',
    'info': cr.Fore.CYAN + '[INFO] ',
    'succ': cr.Fore.GREEN + '[SUCCES] ' + cr.Fore.RESET,
    'cmd': cr.Fore.CYAN,
    'perc': cr.Fore.GREEN}


def get_user_input(argvs):
    # Tuples are sorted, which is easier for printing a help page
    arg_tup = (
        (
            '-h, --help',
            'Display this help section'),
        (
            '-i, --in-path', 
            'Input path'),
        (
            '-o, --out-path', 
            'Output path\n\t-o can not be the same as -i, but can be a new folder inside -i\n' +
            '\tWhen not specified -i will be the current working dir\n\tand -o will be a new folder named [REMUXED] inside that dir\n'),
        (
            '-a, --audio-lang', 
            'Keep audio of this language (Example: -a jpn)'),
        (
            '-s, --sub-lang', 
            'Keep subtitle(s) of this language (Example: -s eng)'),
        (
            '-S, --keep-all-sub', 
            'Keep all subtitles (overrides --no-dupe)'),
        (
            '-x, --extract-sub', 
            'Extract subtitle(s) of this language (Example: -x eng) (overrides -s\-S)'),
        (
            '-X, --extract-all-sub', 
            'Extract all subtitles (overrides -s\-S)'),
        (
            '-k, --keepatt-type', 
            'Only keep attachments of this type (Example: -k font)'),
        (
            '-K, --keep-att', 
            'Keep all attachments'),
        (
            '-t, --keep-track-titles', 
            'Keep track titles'),
        (
            '-T, --keep-title', 
            'Keep file title'),
        (
            '-c, --keep-chapt', 
            'Keep chapters\n\tFor -a, -s, -x and -k multiple values can be specified (Example: -s eng,jpn)\n'),
        (
            '--no-dupe', 
            'If multiple types of the same language are found only keep the first'),
        (
            '--new-folder', 
            'Create a new folder in -o for each processed file (uses file name)'),
        (
            '--sub-folders', 
            'Also check in any subfolders of -i for mkv files to process'),
        (
            '--trash-files',
            'Move original files to the trash when a remux is finished'),
        (
            '-v, --verbose', 
            'Prints extra information during the process'),
        (   
            '--nc',
            'Disables colored output'),
        (
            '--simulate', 
            'Do a test run which doesn\'t process any files, just outputs information\n\t--simulate includes the verbose argument\n'),
        (
            '--pass-along', 
            'Optional \'global\' commands to pass along to MKVMerge, wrapped in "\'s\n\tExample: --pass-along "--default-language eng"\n')
    )
    
    # Options which require a string
    valid_options = {
        '-i': 'in_path',
        '--in-path': 'in_path',
        '-o': 'out_path',
        '--out-path': 'out_path',
        '-a': 'audio_lang',
        '--audio-lang': 'audio_lang',
        '-s': 'sub_lang',
        '--sub-lang': 'sub_lang',
        '-x': 'extract_sub',
        '--extract-sub': 'extract_sub',
        '-k': 'keepatt_type',
        '--keepatt-type': 'keepatt_type',
        '--pass-along': 'pass_along'
    }
    
    # Options which are True or False
    valid_options_bool = {
        '-X': 'extract_all_sub',
        '--extract-all-sub': 'extract_all_sub',
        '-S': 'keep_sub',
        '--keep-all-sub': 'keep_sub',
        '--no-dupe': 'no_dupe',
        '--new-folder': 'new_folder',
        '-c': 'keep_chapt',
        '--keep-chapt': 'keep_chapt',
        '-t': 'keep_ttitle',
        '--keep-track-titles': 'keep_title',
        '-T': 'keep_title',
        '--keep-title': 'keep_title',
        '-K': 'keep_att',
        '--keep-att': 'keep_att',
        '--sub-folders': 'sub_folders',
        '--simulate': 'simulate',
        '-v': 'verbose',
        '--verbose': 'verbose',
        '--trash-files': 'trash_files',
        '--nc': 'no_color'
    }

    # Arguments which can contain multiple values are seperated by a comma
    list_argvs = [
        '-a',
        '--audio-lang',
        '-s',
        '--sub-lang',
        '-x',
        '--extract-sub',
        '-k',
        '--keepatt-type'
    ]


    # Will be populated by looping through the getopt arguments
    user_given_options = {}

    try:
        opts, _ = go.getopt(argvs, 'hi:o:a:s:Sx:XctTk:Kv',
                            ['help', 'in-path', 'out-path', 'audio-lang', 'sub-lang', 'extract_sub',
                             'extract-all-sub', 'keep-all-sub', 'keep-track-titles', 'keep-title', 'no-dupe',
                             'new-folder', 'keep-chapt', 'keep-att', 'keepatt-type=', 'sub-folders', 'pass-along=',
                             'simulate', 'verbose', 'trash-files', 'nc'])
    except go.GetoptError as error:
        sys.exit(stat_m['err'] + str(error) + '\nType \'-h\' or \'--help\' to display help')

    for opt, arg in opts:
        if opt == '-h' or opt == '--help':
            print('''Usage: batchmkvmerge [DIRS]... [OPTIONS]...

Helper script to easily batch remux .mkv files using MKVToolNix
By default it will discard everything but the first video and audio track and it\'s flags
''')
            for k, v in arg_tup:
                print(k.ljust(30), v)
            sys.exit()
        elif opt in valid_options:
            if opt in list_argvs:
                user_given_options[(valid_options[opt])] = arg.split(',')
            else:
                user_given_options[(valid_options[opt])] = arg
        elif opt in valid_options_bool:
            user_given_options[(valid_options_bool[opt])] = True
    
    if 'no_color' in user_given_options:
        # Just replace the ASCI color codes with nothing
        for a in stat_m.keys():
            if a == 'err':
                stat_m[a] = '[ERROR] '
            if a == 'warn':
                stat_m[a] = '[WARNING] '
            if a == 'info':
                stat_m[a] = '[INFO] '
            if a == 'succ':
                stat_m[a] = '[SUCCES] '
            else:
                stat_m[a] = ''

    if '-i' not in argvs:
        # if the user didn't specify an in_path use curent working dir
        user_given_options['in_path'] = os.getcwd() + os.sep
    else:
        user_given_options['in_path'] = validate_path(user_given_options['in_path'])

    if '-o' not in argvs:
        # if the user didn't specify an out path just make a new folder in in_path
        user_given_options['out_path'] = user_given_options['in_path'] + 'REMUXED'
    
    # Just a check to see if the user didn't accidentally use the same in as out folder
    # That would cause the new file to overwrite the original while it's being used
    if os.path.normcase(user_given_options['in_path']).rstrip('/\\') == os.path.normcase(
            user_given_options['out_path']).rstrip('/\\'):
        sys.exit(stat_m['warn'] + '-i and -o can not be the same folder')

    if 'keep_title' in user_given_options and '--title' in user_given_options.get('pass_along', ''):
        sys.exit(stat_m['warn'] + 'Two title options set (\'-T\' and \'--title\').'
                                  '\nThis would cause one to overwrite the other ')

    if 'simulate' in user_given_options:
        user_given_options['verbose'] = True
    
    # Print the dict which contains all the user options
    if 'verbose' in user_given_options:
        print(stat_m['cmd'] + str(user_given_options) + '\n')

    return user_given_options


def scan_for_files():
    # Scan for mkv files in the user given in path
    scanned_files = 0

    if 'simulate' in user_options:
        print(stat_m['info'] + '\'--simulate\' was passed, no actual files will be processed')

    if 'sub_folders' not in user_options:
        print('Searching in "' + user_options['in_path'] + '" for compatible files')
    else:
        print('Searching in "' + user_options['in_path'] + '" and subfolders for compatible files')

    for root, _, files in os.walk(user_options['in_path']):
        if 'sub_folders' in user_options:
            for f in files:
                if f.endswith('.mkv'):
                    print('\n' + stat_m['file'] + 'Found file: "' + f + '" \nin "' + root + '"')
                    file_info = get_mkv_info((root + '/'), f)
                    scanned_files += 1
                    create_command(f, file_info, root)
                    if 'trash_files' in user_options:
                        trash_file(root, f)

        else:
            if root == user_options['in_path']:
                for f in files:
                    if f.endswith('.mkv'):
                        print('\n' + stat_m['file'] + 'Found file: "' + f + '" \nin "' + root + '"')
                        file_info = get_mkv_info((root + '/'), f)
                        scanned_files += 1
                        create_command(f, file_info, root)
                        if 'trash_files' in user_options:
                            trash_file(root, f)

    if scanned_files == 0:
        print('\n' + stat_m['err'] + 'No compatible files found')
    else:
        print('\n' + stat_m['succ'] + str(scanned_files) + ' file(s) processed')


def validate_path(f_path):
    if os.path.exists(f_path):
        return f_path
    else:
        sys.exit(stat_m['err'] + 'Given path "' + f_path + '" doesn\'t exist.')


def trash_file(path, file):
    if 'simulate' in user_options:
        print(stat_m['file'] + 'Would trash file "' + path + os.sep + file + '"')
        pass
    else:
        print(stat_m['file'] + 'Trashing file "' + path + os.sep + file + '"')
        send2trash(path + os.sep + file)


def get_mkv_info(f_path, file):
    file_path = os.path.join(f_path, file)
    cmd = 'mkvmerge -i -F json "' + file_path + '"'
    new_process = sp.Popen(shlex.split(cmd), stdout=sp.PIPE)

    try:
        json_out = json.loads(new_process.communicate(timeout=30)[0].decode())
        if new_process.returncode != 0:
            new_process.kill()

        file_info = process_stdout(json_out)
        return file_info

    # TODO: Handle errors I don't know about because I can't get any to show up
    except TimeoutError as error:
        new_process.kill()
        sys.exit(stat_m['err'] + str(error))
    except sp.TimeoutExpired as error:
        new_process.kill()
        sys.exit(stat_m['err'] + str(error))


def process_stdout(json_out):
    print('Processing track info')
    track_dict, att_dict = {}, {}
    has_att, has_chapt = False, False
    file_info = []

    for t in json_out['tracks']:
        for i in str(t['id']):
            track_dict[i] = {'type': t['type'],
                             'codec_id': t['properties']['codec_id'],
                             'default_track': t['properties']['default_track'],
                             'language': t['properties']['language']}
            try:
                track_dict[i]['track_name'] = t['properties']['track_name']
            except KeyError:
                track_dict[i]['track_name'] = ''

    if json_out['attachments']:
        has_att = True
        for a in json_out['attachments']:
            att_dict[str(a['id'])] = {'type': a['content_type'],
                                      'name': a['file_name']}
    if json_out['chapters']:
        has_chapt = True

    file_info.append(track_dict)
    file_info.append(has_att)
    file_info.append(att_dict)
    file_info.append(has_chapt)

    try:
        mkv_title = json_out['container']['properties']['title']
    except KeyError:
        mkv_title = ''
    file_info.append(mkv_title)

    return file_info


def create_command(file, file_info, root):
    track_dict, has_att, att_dict, has_chapt, mkv_title = file_info

    mkvmerge_cmd = ['mkvmerge']
    mkvextract_cmd = ['mkvextract tracks "' + os.path.join(root, file) + '" ']

    procd_v, options_v = [], []
    procd_a, options_a = [], []
    procd_s, options_s = [], []

    if 'pass_along' in user_options:
        mkvmerge_cmd.append(user_options['pass_along'])

    if 'new_folder' in user_options:
        mkvmerge_cmd.append('-o "' + os.path.join(user_options['out_path'], file.rsplit('.mkv')[0], file) + '"')
    else:
        mkvmerge_cmd.append('-o "' + os.path.join(user_options['out_path'], file) + '"')

    for track in track_dict:
        name = track_dict[track]['track_name']
        lang = track_dict[track]['language']
        is_def = 'no'
        if (track_dict[track]['default_track']) is True:
            is_def = 'yes'

        # Can't remember why I decided to use a while loop here but it works so I don't care
        while True:
            if track_dict[track]['type'] == 'video':
                if len(procd_v) == 0:
                    options_v.append(add_param(track, lang, is_def, name))
                    procd_v.append(track)
                    break
                else:
                    break
            elif track_dict[track]['type'] == 'audio':
                if 'no_dupe' not in user_options and 'audio_lang' not in user_options:
                    if len(procd_a) == 0:
                        options_a.append(add_param(track, lang, is_def, name))
                        procd_a.append(track)
                        break
                    else:
                        break
                elif 'no_dupe' in user_options:
                    if 'audio_lang' in user_options and lang in user_options['audio_lang']:
                        if len(procd_a) == 0:
                            options_a.append(add_param(track, lang, is_def, name))
                            procd_a.append(track)
                            break
                        else:
                            break
                    elif 'audio_lang' not in user_options and len(procd_a) == 0:
                        options_a.append(add_param(track, lang, is_def, name))
                        procd_a.append(track)
                        break
                    else:
                        break
                elif 'audio_lang' in user_options:
                    if lang in user_options['audio_lang']:
                        options_a.append(add_param(track, lang, is_def, name))
                        procd_a.append(track)
                        break
                    else:
                        break
            elif track_dict[track]['type'] == 'subtitles':
                if 'extract_all_sub' in user_options:
                    mkvextract_cmd.append(create_sub_cmd(file, track, track_dict[track]))
                    break
                elif 'extract_sub' in user_options:
                    if lang in user_options['extract_sub']:
                        mkvextract_cmd.append(create_sub_cmd(file, track, track_dict[track]))
                        break
                    else:
                        break
                elif 'extract_sub' not in user_options:
                    if 'keep_sub' in user_options:
                        options_s.append(add_param(track, lang, is_def, name))
                        procd_s.append(track)
                        break
                    elif 'no_dupe' not in user_options and 'sub_lang' not in user_options:
                        break
                    elif 'no_dupe' in user_options:
                        if 'sub_lang' not in user_options:
                            break
                        elif 'sub_lang' in user_options and len(procd_s) == 0:
                            options_s.append(add_param(track, lang, is_def, name))
                            procd_s.append(track)
                            break
                        else:
                            break
                    elif 'sub_lang' in user_options:
                        if lang in user_options['sub_lang']:
                            options_s.append(add_param(track, lang, is_def, name))
                            procd_s.append(track)
                            break
                        else:
                            break
                    else:
                        break

    if len(procd_v) > 0:
        mkvmerge_cmd.append('--video-tracks ' + (','.join(procd_v)) + ' ' + (' '.join(options_v)))
    else:
        mkvmerge_cmd.append('--no-video')
    
    if len(procd_a) > 0:
        mkvmerge_cmd.append('--audio-tracks ' + (','.join(procd_a)) + ' ' + (' '.join(options_a)))
    else:
        mkvmerge_cmd.append('--no-audio')
    
    if len(procd_s) > 0:
        mkvmerge_cmd.append('--subtitle-tracks ' + (','.join(procd_s)) + ' ' + (' '.join(options_s)))
    else:
        mkvmerge_cmd.append('--no-subtitles')

    for a in (procd_v + procd_a + procd_s):
        print('  Keeping track "' + a + ' - ' + track_dict[a]['type'] + ': ' + track_dict[a]['codec_id'] + ' [' +
              track_dict[a]['language'] + ']"')

    mkvmerge_cmd.append(process_options(mkv_title, att_dict))
    mkvmerge_cmd.append('"' + os.path.join(root, file) + '"')
    call_program(mkvmerge_cmd, '[MKVMerge] ')

    if 'extract_sub' in user_options and len(mkvextract_cmd) > 1 \
            or 'extract_all_sub' in user_options and len(mkvextract_cmd) > 1:
        call_program(mkvextract_cmd, '[MKVExtract] ')
    elif 'extract_sub' in user_options or 'extract_all_sub' in user_options:
        print('[MKVExtract] No matching subtitles found, skipping the call to MKVExtract')


def add_param(track, lang, is_def, name):
    if 'keep_ttitle' in user_options and name is not False:
        cmd = '--language ' + track + ':' + lang + ' --track-name ' + track + ':"' + name + \
              '" --default-track ' + track + ':' + is_def
    else:
        cmd = '--language ' + track + ':' + lang + ' --track-name ' + track + ':""' + \
              ' --default-track ' + track + ':' + is_def
    return cmd


def process_options(mkv_title, att):
    infile_options = []

    if 'keep_chapt' not in user_options:
        infile_options.append('--no-chapters')

    if 'keepatt_type' in user_options:
        if 'verbose' in user_options:
            print('Checking attachments')
        keep_att = []
        for a in att:
            for at in user_options['keepatt_type']:
                if at in att[a]['type']:
                    if 'verbose' in user_options:
                        print('  Found match "' + a + ' - ' + att[a]['type'] + ': ' + att[a]['name'] + '"')
                    keep_att.append(a)
        if keep_att:
            infile_options.append('--attachments ' + ','.join(keep_att))
        else:
            t = 'type'
            if len(user_options['keepatt_type']) > 1:
                t = 'types'
            if 'verbose' in user_options:
                print('  No attachments found which match ' + t + ' "' + '/'.join(user_options['keepatt_type']) + '"')
            infile_options.append('--no-attachments')
    else:
        infile_options.append('--no-attachments')

    if 'keep_title' not in user_options and '--title' not in user_options.get('pass_along', 'None'):
        infile_options.append('--title ""')
    elif 'keep_title' in user_options:
        infile_options.append('--title "' + mkv_title + '"')

    cmd = ' '.join(infile_options)
    return cmd


def create_sub_cmd(file, track, track_info):
    codec = track_info['codec_id']
    codec_ext = {'S_TEXT/UTF8': '.srt',
                 'S_TEXT/SSA': '.ssa',
                 'S_TEXT/ASS': '.ass',
                 'S_TEXT/USF': '.usf',
                 'S_TEXT/WEBVTT': '.vtt',
                 'S_VOBSUB': '.idx',
                 'S_HDMV/PGS': '.sup'}
    try:
        ext = codec_ext[codec]
        if 'new_folder' in user_options:
            cmd = track + ':"' + \
                  os.path.join(user_options['out_path'], file.rsplit('.mkv')[0], file.rsplit('.mkv')[0]) + \
                  '.' + track + '_' + track_info['language'] + ext + '"'
        else:
            cmd = track + ':"' + \
                  os.path.join(user_options['out_path'], file.rsplit('.mkv')[0]) + \
                  '.' + track + '_' + track_info['language'] + ext + '"'
        print('  Adding subtitle "' + track + '_' + track_info['language'] + ext + '" to MKVExtract call')
        return cmd
    except KeyError:
        print(stat_m['err'] + 'Unknown subtitle codec (' + codec + '), or is not supported by MKVMerge')


def call_program(cmd, program):
    line = ''
    if program == '[MKVMerge] ':
        cmd = ' '.join(cmd)
        if 'verbose' in user_options:
            print('\n' + stat_m['cmd'] + cmd)
    else:
        cmd = list(filter(None, cmd))
        if len(cmd) > 1:
            cmd = ' '.join(cmd)
            if 'verbose' in user_options:
                print(stat_m['cmd'] + cmd)

    if 'simulate' in user_options:
        pass
    else:
        try:
            with sp.Popen(shlex.split(cmd), stdout=sp.PIPE, stderr=sp.PIPE, universal_newlines=True) as p:
                for line in p.stdout:
                    if 'verbose' not in user_options and line.startswith('Progress:'):
                        if '100%' in line:
                            print('\r' + program + stat_m['perc'] + line.rstrip('\n'), end='')
                        else:
                            print('\r' + program + line.rstrip('\n'), end='')
                    if 'verbose' in user_options:
                        if line.startswith('Progress:'):
                            if '100%' in line:
                                print('\r' + program + stat_m['perc'] + line.rstrip('\n'), end='')
                            else:
                                print('\r' + program + line.rstrip('\n'), end='')
                        elif line == '\n':
                            print('')
                        elif line.startswith('Error'):
                            continue
                        else:
                            print(program + line, end='')
            print('')

            if p.returncode != 0:
                p.kill()
                sys.exit(stat_m['err'] + str(line).lstrip('Error:'))

        except Exception as error:  # TODO: What Exceptions to handle here?
            sys.exit(stat_m['err'] + str(error))


if __name__ == '__main__':
    user_options = get_user_input(sys.argv[1:])
    scan_for_files()

