# vh17 design (Claude Sonnet 5.5 High, 15-Oct-2026)

New: the shown board is two panels, left and right, and only the live one takes clicks. ACTION3 makes the left
live, ACTION4 the right (free, one frame); the live panel has a yellow one-pixel frame, the other maroon; a click in
the dead panel is refused with a pink flash of its frame, no change and no step spent. Every level starts with the
right panel live. Level one was rebuilt as a row of three tiles and two cards laid across both panels, so the left
tile cannot be pressed until the player chooses the left panel; levels two to seven each have winning presses in
both halves (levels two to six are the control copy's, the stored lines now carry the arrow presses). Colours: the
empty board is the allowed black, nothing the player reads is grey or black (equal pixels white, pattern markers
maroon). Forced changes: level one's budget is 200 so random play cannot run it dry (vetting gate), and a seventh
level (Son's generator, seed 17) was appended because the gate wants seven. Needed-check run: the stored lines with
the arrow presses removed clear no level. One vet pass: glowup PASS; strips opened once.
