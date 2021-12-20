import os
import re
from typing import Tuple, Optional

import mutagen
import unidecode
from logzero import logger


def read_tags_from_file(file: str) -> Optional[Tuple[str, str, int, str]]:
    """
    Read the artist and title information from a music file
    Currently supported file formats are .mp3 and .flac
    :param file: Input music file
    :return: Artist name and title as strings
    """
    try:
        logger.debug(f"Trying to load '{file}'")

        tags = mutagen.File(file)

        match type(tags):
            case mutagen.mp3.MP3:
                try:
                    artist = tags.tags.getall('TPE1')[0].text[0]
                except IndexError as e:
                    logger.debug(e)
                    artist = ''

                try:
                    album = tags.tags.getall('TALB')[0].text[0]
                except IndexError as e:
                    logger.debug(e)
                    album = ''

                try:
                    track = int(re.match(r"(\d+)(?:/\d+)?", tags.tags.getall('TRCK')[0].text[0])[1])
                except IndexError as e:
                    logger.debug(e)
                    track = 0

                title = tags.tags.getall('TIT2')[0].text[0]
                logger.debug(f"Loaded MP3 file: '{artist} / {album} / {track} - {title}'")
                return artist, album, track, title

            case mutagen.flac.FLAC | mutagen.oggopus.OggOpus:
                try:
                    artist = tags['artist'][0]
                except (KeyError, IndexError) as e:
                    logger.debug(e)
                    artist = ''

                try:
                    album = tags['album'][0]
                except (KeyError, IndexError) as e:
                    logger.debug(e)
                    album = ''

                try:
                    track = int(re.match(r"(\d+)(?:/\d+)?", tags['tracknumber'][0])[1])
                except (KeyError, IndexError) as e:
                    logger.debug(e)
                    track = 0

                title = tags['title'][0]
                logger.debug(f"Loaded FLAC/Opus file: '{artist} / {album} / {track} - {title}'")
                return artist, album, track, title

            case mutagen.mp4.MP4:
                try:
                    artist = tags['\xa9ART'][0]
                except (KeyError, IndexError) as e:
                    logger.debug(e)
                    artist = ''

                try:
                    album = tags['\xa9alb'][0]
                except (KeyError, IndexError) as e:
                    logger.debug(e)
                    album = ''

                try:
                    track = int(tags['trkn'][0][0])
                except (KeyError, IndexError) as e:
                    logger.debug(e)
                    track = ''

                title = tags['\xa9nam'][0]
                logger.debug(f"Loaded MP4/M4A file: '{artist} / {album} / {track} - {title}'")
                return artist, album, track, title
            case _:
                logger.info(f"Found unsupported file: '{tags}'")

    except mutagen.MutagenError as e:
        logger.exception(e)

    return None


def sanitize_string(s: str) -> str:
    s = unidecode.unidecode(s)

    forbidden_chars = ' \\/:*?"<>|~&{}%#.'
    replacement_char = '_'
    for c in forbidden_chars:
        s = s.replace(c, replacement_char)

    return s


def tags_to_path(artist: str, album: str, track: int, title: str) -> str:
    artist = sanitize_string(artist)
    album = sanitize_string(album)
    title = sanitize_string(title)
    return f"\\{artist}\\{album}\\{track:02}_{title}"


def rename_recursive(path: str):
    for subdir, dirs, files in os.walk(path):
        for file in files:
            if file[-3:] == 'lrc' or file[-3:] == 'm3u':
                # Skip existing lyrics or playlist files
                continue

            sound_file = os.path.join(subdir, file)
            basename, extension = os.path.splitext(file)
            lyrics_file = os.path.join(subdir, basename + '.lrc')
            logger.debug(f"Discovered file {sound_file} and lyrics {lyrics_file}")

            tags = read_tags_from_file(sound_file)
            if not tags:
                continue

            basename_from_tags = tags_to_path(*tags)
            new_sound_file = os.path.normpath(path + basename_from_tags + extension)
            new_lyrics_file = os.path.normpath(path + basename_from_tags + '.lrc')
            logger.debug(f"New path for file is {new_sound_file}")

            if sound_file == new_sound_file:
                logger.debug(f"Nothing to do for {new_sound_file}")
                continue

            logger.info(f"Renaming {sound_file} to {new_sound_file}")
            os.renames(sound_file, new_sound_file)
            if os.path.isfile(lyrics_file):
                logger.info(f"Renaming {lyrics_file} to {new_lyrics_file}")
                os.renames(lyrics_file, new_lyrics_file)


if __name__ == '__main__':
    # Setup Logging
    # logzero.logfile("logs/logfile.log", maxBytes=1e9, backupCount=1)
    logzero.loglevel(level=20)  # logging.INFO
    # logzero.loglevel(level=10)  # logging.DEBUG
    rename_recursive("D:\\Music\\")
