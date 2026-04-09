# Icon Placeholder

To add a custom icon for the Crazy Lister .exe:

1. Create or obtain a `.ico` file (256x256 or multi-resolution)
2. Name it `icon.ico`
3. Place it in this `assets/` folder

The PyInstaller spec file will automatically use it when building the .exe.

## Tools to create .ico files:
- https://icoconvert.com/ (online)
- https://favicon.io/ (online)
- GIMP (export as .ico)
- ImageMagick: `convert icon.png icon.ico`

## Recommended icon sizes:
- 16x16 (file explorer small)
- 32x32 (file explorer large)
- 48x48 (taskbar)
- 256x256 (desktop icon)
