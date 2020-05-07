import requests
from urllib.parse import quote
from bs4 import BeautifulSoup
from sys import argv
from os.path import exists, basename
from argparse import ArgumentParser, FileType, RawTextHelpFormatter

from movie_result import MovieResult

def _padString(string: str, length: int):
  """
  Pads a given string to the provided length, with spaces

  Parameters
  ----------
  string : str
      The string to pad
  length : int
      The length to pad it
  """
  return ' ' * (length - len(string)) + string

def _isFileValid(parser: ArgumentParser, filePath: str) -> str:
  """
  Checks if a given media file is valid to write chapters to

  Parameters
  ----------
  parser : ArgumentParser
      An argument parser instance
  filePath : str
      The file path to validate

  Returns
  -------
  str
      The file path, if it is valid

  Throws
  ------
  ArgumentParser error
      If the file type is not supported
      If the file does not exist
  """
  # Only supports MKV at this time
  if basename(filePath).split('.')[-1] != 'mkv':
    parser.error('Unsupported file type!')
  elif not exists(filePath):
    parser.error('File %s does not exist!' % filePath)
  else:
    return filePath

def search(title: str) -> MovieResult:
  """
  Searches the chapters DB for a given title

  Parameters
  ----------
  title : str
      The title of the movie to search for

  Returns
  -------
  MovieResult
      The selected movie result, with metadata about it
      Does not include chapters
  """
  results = []

  url = 'https://chapterdb.plex.tv/grid?Criteria.Title=' + quote(title)
  response = requests.get(url)
  # Parse results using the lxml library
  result = BeautifulSoup(response.content, 'lxml')

  for row in result.select('form table tbody tr'):
    isFirst = True

    movie = MovieResult()
    IGNORE_KEY = 'ignore'
    cols = ['starred/has_chapters', 'mediaType', 'name/id', 'duration', IGNORE_KEY, IGNORE_KEY]

    idx = 0
    for cell in row.select('td'):
      if cols[idx] == IGNORE_KEY:
        continue

      if isFirst:
        # The first element has a "star" svg icon indicated higher quality/use
        movie.isStarred = ('star' in cell.select('use')[0].attrs.get('xlink:href', ''))
        # The next element has a "title" indicated if names are or are not detected for chapters
        altText =  cell.select('title')
        altText = altText[0].text.lower() if altText else 'No title element'
        # Starred entries appears to always have names, so this will be for the others
        missingNames = ('no names detected' in altText)
        movie.hasChapterNames = movie.isStarred or (not missingNames)
      # If the column is single-purpose (not containing multiple data points)
      # Set the attribute directly
      elif '/' not in cols[idx]:
        setattr(movie, cols[idx], cell.text)
      # Cell 2 (3 for one-indexing) has both the name and the ID/number of the media result
      elif idx == 2:
        movie.title = cell.text
        # The ID/number of the media result is the last bit of the URL
        # in the format /browse/100 (100 is the ID)
        movie.movieID = int(cell.select('a')[0].attrs['href'].split('/')[-1])

      isFirst = False
      idx += 1

    results.append(movie)

  if len(results) > 1:
    prompt = ['Multiple choices found! Please select from:']
    idx = 1

    # The length of the count of results, e.g. 10 results has length 2 and 100 has length 3
    # For use in padding outputs
    resultCountLength = len(str(len(results)))
    for result in results:
      prompt.append('{0}. {1}'.format(
        _padString(str(idx), resultCountLength),
        result.toString()
      ))
      idx += 1

    choice = 0
    # Choice has to be in the result list
    while not str(choice).isnumeric() or int(choice) < 1 or int(choice) + 1 > len(results):
      print('\n'.join(prompt))
      choice = input('Select movie: ')

  if len(results) == 0:
    print('No movies found! Exiting')
    exit(0)

  return results[int(choice) - 1]

def getChapters(title: str) -> MovieResult:
  """
  Gets chapters for a given movie title

  Parameters
  ----------
  title : str
      The title to search for

  Returns
  -------
  MovieResult
      A fully-populated movie result, with metadata AND chapters
  """
  movie = search(title)

  # Get the chapter table for the media
  url = 'https://chapterdb.plex.tv/browse/' + str(movie.movieID)
  response = requests.get(url)
  result = BeautifulSoup(response.content, 'lxml')
  chapterTable = result.select('table tbody tr')

  data = {}
  for chapter in chapterTable:
    # The  cells just contain straight data, so index directly into a dictionary
    cols = ['number', 'title', 'time']
    idx = 0
    for cell in chapter.select('td'):
      data[cols[idx]] = cell.text
      idx += 1

    movie.addChapter(data['title'], data['time'], data['number'])

  return movie

def saveChapters(movie: MovieResult) -> None:
  """
  Saves the chapers of a given movie

  Parameters
  ----------
  movie : MovieResult
      The movie result to save
  """
  if movie.saveChapters():
    print('Saved!')
  else:
    print('Failed to save!')

def getArguments() -> ArgumentParser:
  docs = '''Looks up and saves chapters for a movie
This is done using https://chapterdb.plex.tv, a user-submitted database
!!Currently only supports working with mkv (Matroska) video files!!

Optionally, will also save the chapters to a file
When selecting media, ** indicates a starred result, and * indicates chapters are named
No asterisks indicates a likely-low-quality chapter set
  '''
  args = ArgumentParser(description=docs, formatter_class=RawTextHelpFormatter)
  args.add_argument(
    'movie_title',
    type=str,
    help='The movie title to look up'
  )
  args.add_argument(
    'movie_file',
    type=lambda f: _isFileValid(args, f),
    default=None,
    help='Optionally, the file to save the chapters to',
    nargs='?'
  )
  args.add_argument(
    '--suffix',
    type=lambda s: s if s else 'chapters',
    required=False,
    default='chapters',
    help='The suffix to append to the media file, cannot be blank'
  )
  return args.parse_args()

if __name__ == '__main__':
  args = getArguments()
  movie = getChapters(args.movie_title)

  print('Saving details for: ')
  print(movie.toString())

  # Check movie file validity (again), and confirm adding chapters to the file
  if args.movie_file and exists(args.movie_file):
    movie.fileName = args.movie_file
    movie.outputSuffix = args.suffix
    print('Would output to: ' + movie.getNewFileName())
    confirm = input('Save to file? (Type YES uppercase, defaults NO) ')
    if confirm == 'YES':
      saveChapters(movie)
    else:
      print('Exiting')
  elif args.movie_file:
    print('Non-existent file!')
