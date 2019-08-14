# sequencelib
A Python library for querying and manipulating file sequences.

This is still pretty barebones... more functionality to come.

## Usage:

To search a directory for file sequences:

```
seqs = sequencelib.find_sequences("/path/to/files")
# or optionally with a file extension mask:
seqs = sequencelib.find_sequences("/path/to/files", extensions=['jpg','tif','png','exr'])
```

This returns a list of Sequence objects. To see a list of file paths in each sequence:

```
for seq in seqs:
    print(seq.files())
```

To print a list of missing frames in a sequence:

```
print(mySeq.find_missing_frames())
```

You can optionally define a start, end, and framestep manually:

```
print(mySeq.find_missing_frames(1, 100, 1))
```

If you want to just blast out everything about a specific Sequence object:

```
mySeq.debug()
```