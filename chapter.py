class Chapter:
  number: int
  name: str
  time: str

  def _getPrefix(self) -> str:
    """
    Creates the chapter file prefix, which is CHAPTERXX per the mkvmerge manual specification


    Returns
    -------
    str
        The chapter prefix
    """
    return 'CHAPTER' + ('0' if int(self.number) < 10 else '') + str(self.number)

  def toChapterFileString(self) -> str:
    """
    Creates a string for a chapter file from the data in this class
    See mkvmerge manual specs for formatting

    Note that time is expected to be in millisecond precision, which is not always
    how chapter DB stores the chapter timestamps

    Returns
    -------
    str
        A chapter file format encoded version of this class
    """
    prefix = self._getPrefix()
    # If missing the millisecond portion, use zeroes
    if '.' not in self.time: self.time += '.000'

    # If millisecond portion too long, truncate to 3 digits
    timeParts = self.time.split('.')
    if len(timeParts[-1]) > 3:
      self.time = '.'.join(timeParts[:-1]) + '.' + timeParts[-1][:3]

    string = prefix + '=' + self.time + '\n'
    string += prefix + 'NAME=' + self.name + '\n'

    return string
