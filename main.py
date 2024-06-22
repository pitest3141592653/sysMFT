from io import StringIO
import ctypes
import struct
import binascii

LONG_LONG_SIZE = ctypes.sizeof(ctypes.c_longlong)
BYTE_SIZE = ctypes.sizeof(ctypes.c_byte)
WORD_SIZE = 2

# decode ATRHeader from 
# analyzeMFT.py routines
# Copyright (c) 2010 David Kovar.
def decodeATRHeader(s):
    d = {}
    d['type'] = struct.unpack("<L",s[:4])[0]
    if d['type'] == 0xffffffff:
        return d
    d['len'] = struct.unpack("<L",s[4:8])[0]
    # d['res'] = struct.unpack("B",s[8])[0]
    d['res'] = s[8]

    if d['res'] != 0:
        d['run_off'] = struct.unpack("<H",s[32:34])[0]

    return d

def twos_comp(val, bits):
    """compute the 2's compliment of int value val"""
    if ((val & (1 << (bits - 1))) != 0):
        val = val - (1 << bits)
    return val


# decode NTFS data runs from a MFT type 0x80 record ala: 
# http://inform.pucp.edu.pe/~inf232/Ntfs/ntfs_doc_v0.5/concepts/data_runs.html
def decodeDataRuns(dataruns):
    decodePos = 0
    header = hex(ord(chr(dataruns[decodePos])))
    while header != '0x00' and header != '0x0':
        offset = int(header[2], 16)
        runlength = int(header[3], 16)

        # move into the length data for the run
        decodePos += 1

        length = dataruns[decodePos:decodePos + runlength][::-1]
        length = int(binascii.hexlify(length), 16)
        
        hexoffset = dataruns[decodePos+runlength:decodePos+offset+runlength][::-1]
        cluster = twos_comp(int(binascii.hexlify(hexoffset), 16), offset * 8)
        
        yield (length, cluster)
        decodePos = decodePos + offset + runlength
        header = hex(ord(chr(dataruns[decodePos])))

DriveLetter = 'C'
theDrive = r'\\' + '.\\' + DriveLetter + ':'

outputPath = './mft2.bin'

with open(theDrive, 'rb') as ntfsDrive, open(outputPath, 'wb') as outputFile:
    ntfs = ntfsDrive.read(512)
    ntfsFile = StringIO(ntfs.decode('latin-1'))

    # parse the MBR for this drive to get the bytes per sector,sectors per cluster and MFT location. 
    # bytes per sector
    ntfsFile.seek(0x0b)
    bytesPerSector = ntfsFile.read(WORD_SIZE)
    bytesPerSector = struct.unpack('<h', bytesPerSector.encode('latin-1'))[0]    

    # sectors per cluster
    ntfsFile.seek(0x0d)
    sectorsPerCluster = ntfsFile.read(BYTE_SIZE)
    sectorsPerCluster = struct.unpack('<b', sectorsPerCluster.encode('latin-1'))[0]

    # get mftlogical cluster number
    ntfsFile.seek(0x30)
    cno = ntfsFile.read(LONG_LONG_SIZE)
    mftClusterNumber = struct.unpack('<q', cno.encode('latin-1'))[0]

    # MFT is then at NTFS + (bytesPerSector*sectorsPerCluster*mftClusterNumber)
    mftloc = int(bytesPerSector * sectorsPerCluster * mftClusterNumber)   
    ntfsDrive.seek(0)
    ntfsDrive.seek(mftloc)
    mftraw = ntfsDrive.read(1024)

    #We've got the MFT record for the MFT itself.
    #parse it to the DATA section, decode the data runs and send the MFT over TCP
    ReadPtr = 0
    mftDict = {}
    mftDict['attr_off'] = struct.unpack("<H",mftraw[20:22])[0]
    ReadPtr = mftDict['attr_off']    

    while ReadPtr < len(mftraw):    
        ATRrecord = decodeATRHeader(mftraw[ReadPtr:])

        if ATRrecord['type'] == 0x80:
            dataruns = mftraw[ReadPtr + ATRrecord['run_off'] : ReadPtr + ATRrecord['len']]
            prevCluster = None
            prevSeek = 0
            
            for length, cluster in decodeDataRuns(dataruns):
                if prevCluster == None:
                    ntfsDrive.seek(cluster * bytesPerSector * sectorsPerCluster)
                else:
                    ntfsDrive.seek(prevSeek)
                    newpos = prevSeek + (cluster * bytesPerSector * sectorsPerCluster)
                    ntfsDrive.seek(newpos)

                prevSeek = ntfsDrive.tell()                    
                data = ntfsDrive.read(length * bytesPerSector * sectorsPerCluster)
                outputFile.write(data)
                prevCluster = cluster
            break
        if ATRrecord['len'] > 0:
            ReadPtr = ReadPtr + ATRrecord['len']


