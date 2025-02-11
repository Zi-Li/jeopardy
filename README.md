# jeopardy
Basic display for a Jeopardy game

Disclaimer: I do not own Jeopardy or have any affiliation with the show.

How to use:
1. Create game data (JSON file)
1. Change the DATAFILE value (near the top of jeopardy.py) to the game data you want
1. Ensure requirements are met (mainly Pillow, most libraries I used are usually included in a Python distribution)
1. run jeopardy.py

Description:
This is a basic display to use for a game of Jeopardy.
I built this to use at my church's youth ministry as I did not want to use a slideshow
(since I did not want to have to manually edit values during the game).
I've left space to add a second Jeopardy stage if I ever revisit this project,
but I didn't make it because I didn't want the game to drag on too long.
It is intended that someone is manning the game to decide which team's turn it is,
who gets to answer, and who answers correctly.

Requirements:
Pillow was used for the icons and small images.
Tkinter is usually included in Python distributions as the basic GUI library.