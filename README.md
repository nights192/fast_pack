# Blender FastPack
A generic texture atlasing tool that, given a selection of objects, packs all of their shader inputs into a set of texture atlases, allowing an artist to limit the number of materials used on their model without requiring further thought on their part.

## Usage:
Leveraging FastPack is fairly painless; to begin atlasing your mesh, you need only:

1. Select all of the objects you intend to atlas together.
2. Open your sidebar.
3. Navigate to the "FastPack" section.
4. Hit the "Process Objects" button.
5. Set texture groups you want to render together to the same group number.
6. (If Necessary) Alter the maximum resolution.
7. Click "Pack Textures" and wait for the process to finish.
8. Remove redundant materials.

## Features to be Added:
This addon is currently in alpha--as such, there are a few minor features missing.

1. Currently, the addon does not signal an error upon packing failure; this will be addressed in the next major update.
2. All resulting atlases are square; this will be rectified in the near-term future.
3. There ought to be a way to name the target groups; this should be present in the next major update.

## License
Though as-of-now source-available solely, as of now I intend for the project to open-source following release of its version 1.0, after the core architecture has occified. The addon is entirely free to use.



*Copyright 2022 nights192*