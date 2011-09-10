Chapter 1 How-To
================
Section 1.1 Installation
------------------------
Download the latest version from the git repository. Drop the 4 files (``pythonbits.py``, ``MultipartPostHandler.py``, ``microdata.py`` and ``BeautifulSoup.py``) in a folder inside your shellpath, or run the provided ``install.sh`` script, which will install the appropriate binaries in ``/usr/local/bin``.
It is suggested to create a directory for user-made scripts in your home directory. We will not go into this in this document.

Section 1.2 Usage
-----------------
Usage:
  ``pythonbits.py "MOVIENAME/SERIESNAME" moviefile > Textfile``
*OR*
  ``pythonbits.py -e 1x5 "TV show name" tv-show-file > Textfile``
*OR*
  ``pythonbits.py -e s01e05 "TV show name" tv-show-file > Textfile``

Section 1.3 Clarification
-------------------------
The MOVIENAME/SERIESNAME is required right now, further versions might make this an optional parameter. The moviefile is required, as this provides the Mediainfo and the 2 screenshots. ">" redirects the output (default STDOUT) to a text file, for easier access, this is not required.

Section 1.4 Help and Bugs
-------------------------
Apollo (The main developer) is usually available on irc (irc.baconbits.org), poke him there to report a bug, or get help with the further usage of the script. This goes for contributing as well.
