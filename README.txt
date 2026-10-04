iids.py: add navigational "markup" to level maps on doomwiki.org
================================================================

This is unfinished.  There are some extremely juvenile omissions, see e.g. the "Interface" section of the todo.  I'm posting it for bus factor, and more importantly because SOMEONE COMPETENT SHOULD BE IN CHARGE if this code is ever used at scale.

Obviously best practice is for the user never to edit the script, all setup done through CLI switches.  Right now that's not always the case.  Hopefully todo.txt includes all steps from here to there.

Did my best to limit libraries to those bundled with Python, apart from ImageMagick, hoping it would thus work immediately on non-Windows computers.  Not that I really know what I'm doing there either, I hope someone can eventually test more thoroughly.  I am sure there are modern streamlined ways of defining widgets, especially nowadays when code has to work without a developer on the payroll to debug it.

Dots, spots, markers, stickers (the latter from 3DS Kirby not social media) are the same thing and hopefully that's not too confusing.

v0.0.1 was released after testing with:
	Windows 11 (24H2 and 25H2 I think)
	Python 3.14.0
	numpy 2.3.3
	Pillow 11.3.0
	ImageMagick 7.1.2-3 Q16-HDRI x64

