# Super fast disk scanner for NTFS on Windows

It dumps out the MFT (Master File Table) from system and parse it.

Usage:
1. Dump the MFT file of C drive (requires an admin terminal)
> python3 main.py

2. Parse the output file
> pip install mft
> python3 tprinter.py

Credits to:
1. PyMFTGrabber
   - https://github.com/jeffbryner/pyMFTGrabber
3. Rust based MFT Parser and its Python bindings
   - https://github.com/omerbenamram/mft/
   - https://pypi.org/project/mft/

What I have did:
- Upgraded PyMFTGrabber from python 2 to python 3
- Removed debug-only codes from PyMFTGrabber (as I don't understand them)
- Researched the Rust-based parser (as almost all parser that I cound find are not able to parse my output file)

Thanks :) I love open-source
