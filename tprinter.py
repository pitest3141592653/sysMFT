# from mft import pyMftParser, pyFlatMftEntryWithName
import mft

parser = mft.PyMftParser('./mft2.bin')
# ['attributes', 'base_entry_id', 'base_entry_sequence', 'entry_id', 'file_size', 'flags', 'full_path', 'hard_link_count', 'sequence', 'total_entry_size', 'used_entry_size']

with open('./out2.csv', 'w', encoding = 'utf-8') as file:
    file.write(f'Number,FileSize,Flags,FullPath\n')
    for i in parser.entries():
        if i.entry_id % 10000 == 0: print(i.entry_id)
        if isinstance(i, RuntimeError):
            print('here', i.entry_id)
        file.write(f'"{i.entry_id}","{i.file_size}","{i.flags}","{i.full_path}"\n')
