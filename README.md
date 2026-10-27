# Node Zip Ties

<!-- current-release:start -->
**[Download current release — v0.5.0](https://github.com/danielmoreink/Zip-ties-for-Blender/raw/refs/heads/master/dist/node_zip_ties-0.5.0.zip)**
<!-- current-release:end -->

Bundle node wires into tidy, movable cable ties. Keep busy node graphs readable while preserving each wire’s connection and color.

Works in **Geometry Nodes, Shader Editor, and Compositor**. Requires **Blender 5.2 or newer**.

## Installation

1. Download the add-on ZIP.
2. In Blender, open **Edit → Preferences → Get Extensions**, open the menu, and choose **Install from Disk**.
3. Select the ZIP and enable **Node Zip Ties**.

When updating, restart Blender after installing the new version.

## Quick start

Hold **Z** and drag a line across two or more wires. Release to create a tie, then drag its strap to arrange the bundle. Add more ties to guide the wires through your graph.

Place the mouse over the node editor when using shortcuts.

## Controls

| Action | Shortcut or gesture |
|---|---|
| Create a tie | Hold **Z** and drag across wires |
| Move selected ties | **G**, or drag the strap |
| Slide along the wires | **G**, then **G** again; stops before neighboring ties |
| Rotate selected ties | **R** |
| Rotate in 15° steps | **Shift-drag**; hold **Alt** as well for free rotation |
| Scale tie length and wire spacing | **S** |
| Select multiple ties | **Ctrl-click** to toggle; **Shift-click** to add |
| Name a tie | Select one tie, then choose **Name…** in the sidebar or right-click menu |
| Change color or access more actions | **Right-click** the strap |
| Delete selected ties | **X** |
| Delete selected ties and selected nodes | **Delete** or **Backspace** |
| Remove one tie | **Double-click**, or hold **Z** and drag across its strap |

For keyboard transforms, **click** or press **Enter** to confirm; press **Esc** or **right-click** to cancel. Scaling also accepts numeric input: **S → 2 → Enter** doubles the tie’s length and gaps; **S → .5 → Enter** halves them.

## Settings

Open the node editor sidebar with **N**, then choose **Zip Ties**.

- **Selected Ties:** name a single tie, change color, or remove the selection.
- **Appearance — All Ties:** show or hide straps and names, adjust strand spacing and strap width, and choose a color mode for new ties. These settings apply across node trees.
- **Maintenance:** remove missing wire references after editing connections.

The creation shortcut can be changed in the add-on preferences.

Names appear in small, upright text above their ties and save with the file. Leave the name empty to remove the label, or turn off **Show Names** in Appearance to hide all names.

## Moving and copying nodes with ties

To move nodes and their ties together, use **F3 → Move Selected Nodes and Ties**.

To copy a bundle, select all nodes at both ends of its wires, then use **F3 → Copy Nodes with Ties** and **F3 → Paste Nodes with Ties**. These commands preserve the associated ties; ordinary node copy/paste does not preserve the straps. **Box Select Ties and Nodes** is also available through F3.

## Notes

- Ties and their wire routes save with your `.blend` file.
- The add-on uses native reroute nodes, whose small handles may remain visible. Removing the last tie restores the direct connection when its route is intact.
- Disabling the add-on hides the straps; the routed connections continue to work.
- Gesture picking can be less precise on complex custom node layouts.

## Credits and license

Based on [ComfyUI Zip Ties by Safzan Pirani](https://github.com/safzanpirani/comfyui-zip-ties). The original MIT license notice is included with the add-on.

Node Zip Ties is licensed under [GPL-3.0-or-later](LICENSE).
