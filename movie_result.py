from chapter import Chapter
from os import system

class MovieResult():
  movieID: int
  title: str
  mediaType: str
  duration: str
  chapters: list = []
  hasChapterNames: bool
  isStarred: bool
  fileName: str = None
  outputSuffix: str = 'chapters'

  def addChapter(self, chapterName: str, chapterTime: str, chapterNumber: int=None) -> None:
    """
    Adds a chapter to the movie

    Parameters
    ----------
    chapterName : str
        The name of the chapter
    chapterTime : str
        The time of the chapter
    chapterNumber = None : int
        Optionally, a chapter number.
        Defaults to the number of chapters added so far + 1
    """
    chapter = Chapter()
    chapter.number = chapterNumber if chapterNumber else len(self.chapters + 1)
    chapter.name = chapterName
    chapter.time = chapterTime

    self.chapters.append(chapter)

  def toString(self) -> str:
    """
    Returns a string representation of this object
    Single line for metadata, indented line for each chapter


    Returns
    -------
    str
        This movie in string form
    """
    string = '{0}{1} ({2} [{3}])'.format(
      '** ' if self.isStarred else ('* ' if self.hasChapterNames else ''),
      self.title,
      self.mediaType,
      self.duration
    )

    if self.chapters: string += '\n'

    for chapter in self.chapters:
      string += '  {0}. {1} [{2}]'.format(
        chapter.number,
        chapter.name,
        chapter.time
      )
      string += '\n'

    return string

  def getNewFileName(self) -> str:
    """
    Creates the new file name from the current file name
    Also appends the outputSuffix between the file name and extension

    Returns
    -------
    str
        An updated file name
    """
    filenameParts = self.fileName.rsplit('.', -1)
    return filenameParts[0] + '-' + self.outputSuffix + '.' + filenameParts[1]

  def saveChapters(self) -> bool:
    """
    Multiplexes the input file with the chapter data into the output file

    Returns
    -------
    bool
        True if metadata is valid for save and no exception was thrown
        False otherwise
    """
    if not self.fileName or not self.chapters: return False

    chapterFile = 'chapters.txt'

    # Create a file with chapter data to merge into the MKV
    chapterData = ''
    with open(chapterFile, 'w') as textChapters:
      for chapter in self.chapters:
        chapterData += chapter.toChapterFileString()

      textChapters.write(chapterData)

    system('mkvmerge --chapters "{0}" -o "{1}" "{2}"'.format(chapterFile, self.getNewFileName(), self.fileName))
    return True
