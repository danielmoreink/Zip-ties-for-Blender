# Node Zip Ties 0.4.2

Install in unmodified Blender 5.2. Hold Z and drag across two or more wires to create a tie. Drag to move; R rotates freely (click/Enter confirms, Esc/right-click cancels). Shift-drag snaps rotation; add Alt for free rotation. Ctrl-click toggles selection, Shift-click adds. X removes selected ties only; Delete/Backspace also remove selected nodes. Double-click or Z-drag across a strap removes it.

The N sidebar contains selected-tie Color/Remove controls, global Appearance settings, and Maintenance. There are no creation/rotation buttons or Nodes & Ties section. The right-click menu offers creation, rotation, color and removal. Optional box-selection, joint movement and clipboard commands remain available through F3.

Blender draws actual native reroute wires. The add-on draws only straps and gesture indicators. Small native reroute handles remain visible. Removing the last intact tie restores the direct connection. Native routes and stored data survive save/reload and remain functional with the add-on disabled. Older saved ties are migrated automatically.

Gesture socket positions can be approximate on complex custom node layouts. Ordinary Blender movement/clipboard commands do not fully synchronize tie metadata; optional joint commands are available through F3. Automated native routing, evaluation, undo, clipboard and UI-contract tests pass; graphical event/visual checks remain pending.

Reference: https://github.com/safzanpirani/comfyui-zip-ties
Original MIT notice: THIRD_PARTY_NOTICES.txt. Extension license: GPL-3.0-or-later.

G moves the selected ties freely. Press G again (G, G) to slide along a frozen guide of the existing noodle bundle, bounded by neighbouring ties or connected sockets. Sliding does not pass neighbouring ties. Click/Enter confirms; Esc/right-click cancels. Existing click-and-drag movement remains available. Guides average the member noodles and retain the tie angle.

S scales selected ties: strap length and noodle spacing change proportionally around each tie centre, while width and angle stay fixed. Mouse movement sets the factor, or type a number (S, 2, Enter doubles; S, .5, Enter halves). Click/Enter confirms; Esc/right-click cancels. Scale is per tie, persists in the .blend and copies with ties. Existing ties default to scale 1.

Version 0.4.2 restyles the strap with a rounded folded tip, wider locking collar, dark outlines, and body/fold shading. The same geometry drives picking, cuts and box selection. Routing and transform controls are unchanged. A geometry preview is available in docs/tie-style-preview.svg and .png; this is not an editor screenshot.
