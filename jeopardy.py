from json import load
from os.path import join, dirname
from tkinter import *
from PIL import Image, ImageTk
from sys import argv

# GLOBAL CONSTANTS FOR EASY ACCESS
# file and folder names
DATAFOLDER = "jeopardy_data"
DATAFILE = "ya_social.json"
ICONFOLDER = "icons"
IMAGEFOLDER = "images"
# the values the question takes (array [100, 200, ..., 500])
QUESTIONVALUES = [str(i) for i in range(100,501,100)]

# what colour to assign each team
TEAMCOLOURING = ["Red", "Green", "Blue", "#C07401"]

# what colour to assign the tiles on the main board
ACTIVE_COLOUR = "#0108a0"
DISABLE_COLOUR = "#3439b3"
TEXT_COLOUR = "Yellow"

# what colour to give the scoreboard at the bottom
SCORE_BG_COLOUR = "#b3b5e3"
# what colour the 'end stage' button will take
END_BUTTON_COLOUR = "#999cd9"
END_BUTTON_TEXTCOLOUR = "Yellow"

# whether we allow final jeoardy bets to exceed the team's score
NO_NEG_BETS = False
# whether only one team can earn the points of a question
ONLY_ONE_ANSWER = True

# the text wrap length for the questions and answers
WRAPLENGTH_QA = 800

# the height, width and wrap length of each 'line' in the final scoreboard at the end
FSCOREBOARD_WIDTH = 10
FSCOREBOARD_HEIGHT = 2
FSCOREBOARD_WARP = 200

# buffer space between stuff
HEADING_Q_BUFFER = 150
Q_A_BUFFER = 50
CONT_SCORE_BUFFER = 20
END_BOTTOM_BUFFER = 2
BET_BUFFER = 50
MENU_RBUTTON_BUFFER = 30
MENU_START_BUFFER = 20
TITLE_MAIN_BUFFER = 10
TOPSCOREBOARD_BUFFER = 2

# Load the game data
gamedata_folder = DATAFOLDER
gamedata_file = DATAFILE # for test code TODO parameterise this!
icon_folder = ICONFOLDER
image_folder = IMAGEFOLDER

if (len(argv) == 2): # TODO do a more complete parameterisation with options
    gamedata_file = argv[1]

# gets the file pointer to the json file containing the questions
gamedata_fp = open(join(dirname(__file__), gamedata_folder, gamedata_file))
gamedata_json = load(gamedata_fp) # load a json into a python object
gamedata_fp.close()
# TODO verify opened json file meets the right format

# set the title of the game
TITLE = gamedata_json["title"]
# create the base gui window using tkinter
tk = Tk(TITLE)
tk.title(TITLE) # set window title
tk.state('zoomed') # set window to start expanded

HAVEIMG = False
TITLEIMG = None
TITLEIMAGE_HEIGHT = 65
TITLEIMAGE_WIDTH = 60
DEFAULTIMAGE_HEIGHT = 100
DEFAULTIMAGE_WIDTH = 100
IMAGEMAX_HEIGHT = 175
IMAGEMAX_WIDTH = 175

IMAGEBUFFER = []

# get icon
try:
    icon_path = join(dirname(__file__), icon_folder, gamedata_json["icon"])
    ico = Image.open(icon_path)
    photo = ImageTk.PhotoImage(ico)
    tk.wm_iconphoto(False, photo)
    ico.close()
except:
    pass
# get title img
try:
    icon_path = join(dirname(__file__), icon_folder, gamedata_json["titleimg"])# Read the Image
    TITLEIMG = ImageTk.PhotoImage(Image.open(icon_path).resize((TITLEIMAGE_WIDTH,TITLEIMAGE_HEIGHT)))
    HAVEIMG = True
except:
    pass

def create_buffer(widget, buffersize):
    return Canvas(widget, height=buffersize)

# class to contain the main game data after the main menu
class MainGame():
    # initialisation
    # qa_data is a dictionary where the keys are the categories and the values are dictionaries
    #   the subdictionaries contain keys "questions" and "answers" which are dictionaries with the score values as keys and the questions/answers as values
    # final jeopardy data is a simple dictionary containing "question" and "answer"
    # title is the title to display
    def __init__(self, qa_data: dict, final_jeopardy_data: dict, title: str) -> None:
        self.team_names = [] # stores the names of teams
        self.qa = qa_data # stores the questions and answers
        self.final_data = final_jeopardy_data # stores the question and answer of final jeopardy
        self.remaining = {cat: {qv : True for qv in QUESTIONVALUES} for cat in qa_data.keys()} # tracks remaining questions (unused, may delete later)
        self.scores = {} # tracks the team scores
        self.team_colours = {} # tracks which colour to assign each team
        self.mainboard = None # stores the tkinter frame for the main board
        self.showmain = False # tracks whether the main board is shown or hidden
        self.title = title # stores the title
        self.footer = None # stores the tkinter frame for the main board footer (using .pack(side=BOTTOM))
    
    # sets the team names
    # team_name_array is an array of StringVar, so .get() needs to be called to get the string representation
    def set_team_names(self, team_name_array: list):
        # gets the string representation of each StringVar
        for sv in team_name_array:
            self.team_names.append(sv.get())
        assert self.mainboard is not None # mainboard should've been initialised by now
        # initialise scores to $0
        # note: probably should change self.mainboard to instead just use the main Tk window
        self.scores = {tn: StringVar(self.mainboard, "$0") for tn in self.team_names}
        # assign team colours
        ctr = 0
        for tname in self.team_names:
            self.team_colours[tname] = TEAMCOLOURING[ctr]
            ctr += 1
            
    # get the integer representation of the team's score
    def get_score(self, tname: str) -> int:
        stringscore = self.scores[tname].get()
        # check if the score is negative
        is_pos = 1
        if stringscore[0] == '-':
            is_pos = -1
        # if negative, we multiply the number component by -1
        numval = int(stringscore[stringscore.find("$")+1:]) * is_pos
        return numval
        
    # modify a team's score by increment
    # to subtract score, just use a negative increment
    def modify_score(self, tname: str, increment: int):
        stringscore = self.scores[tname].get()
        # check if value is positive/negative
        is_pos = 1
        if stringscore[0] == '-':
            is_pos = -1
        # get the numerical value
        # could probably neaten this up by just calling self.get_score, but I wrote this before I wrote that
        numval = int(stringscore[stringscore.find("$")+1:]) * is_pos
        numval += increment # increment the score
        # ensure we convert it properly back to a string: -$num if negative score or $num if positive
        if numval < 0:
            self.scores[tname].set(f"-${numval * -1}")
        else:
            self.scores[tname].set(f"${numval}")
    
    # display the mainboard and footer
    def show_mainboard(self):
        if not self.showmain:
            self.mainboard.pack(side=TOP)
            self.footer.pack(side=BOTTOM)
            self.showmain = True
    # hide the mainboard and footer (does not destroy the widgets, just 'detaches' it)
    def hide_mainboard(self):
        if self.showmain:
            self.mainboard.pack_forget()
            self.footer.pack_forget()
            self.showmain = False
    # reset mainboard and footer to blank frames
    def reset_mainboard(self, tk):
        self.mainboard.destroy()
        self.footer.destroy()
        self.mainboard = Frame(tk)
        self.footer = Frame(tk)
        self.showmain = False
        
    # generates the initial mainboard
    # written to return a function that does it so that we can pass it as a button callback function
    # tk is the main Tkinter window
    # junk is the old frame we want to delete
    # teamnames is the array of StringVar storing the teamnames
    # note that this is a messy way of doing it
    # it would've been better if I decided earlier on to put the main menu in this class
    # so that we can just reuse self.reset_mainboard to clean it
    def initial_board_gen(self, tk: Tk, junk: Frame, teamnames: list):
        def initial_board():
            # creates the main board frames
            self.mainboard = Frame(tk)
            self.footer = Frame(tk)
            self.showmain = False
            self.set_team_names(teamnames) # set team names
            junk.destroy() # remove old frames
            # create title
            tf = LabelFrame(self.mainboard) # a frame to hold the title element (not really necessary to do this)
            tf.pack(side=TOP, fill=X)
            title = Label(tf, text=self.title, font=("Arial",24,'bold'))
            if HAVEIMG:
                title.config(image=TITLEIMG, compound=LEFT, text=" "+self.title)
            title.pack(side=TOP) # create a title and pack it
            # create board
            create_buffer(self.mainboard, TITLE_MAIN_BUFFER).pack(side=TOP)
            bf = Frame(self.mainboard) # a frame to store all the main game tiles
            bf.pack(side=TOP, fill=X)
            cat_labels = Frame(bf) # kind of uncecessary, I initially was making a separate frame for the category labels and game tiles
            # but then decided against that and this is a leftover from that
            cat_labels.pack(side=TOP, fill=X)
            ctr = 0
            WIDTH = 10 # TODO should move these to global variables
            HEIGHT = 2
            WRAPLENGTH = 160
            # place all the category labels in
            # note the use of the borderwidth and relief parameters to make the gridlines appear
            # note that we also use grid instead of pack to arrange the elements
            for cat in self.qa.keys():
                lbl = Label(cat_labels, text=cat, font=("Arial",20,'bold'), justify=CENTER, borderwidth=1, relief=SOLID, wraplength=WRAPLENGTH, width=WIDTH, height=HEIGHT, bg=DISABLE_COLOUR, fg=TEXT_COLOUR, pady=2, padx=2)
                lbl.grid(column=ctr,row=0,columnspan=1,rowspan=1, ipadx=10, ipady=5)
                ctr += 1
            rctr = 1
            # place the question tiles in
            # rctr and cctr tracks rows and columns for the grid
            # we use buttons as they are the easiest way to make clickables
            # note the use of config to set the command after making the element as we need
            # to pass the button itself into its callback function so it can disable itself
            for val in QUESTIONVALUES:
                cctr = 0
                for cat in self.qa.keys():
                    lbl = Button(cat_labels, text=f"${val}", font=("Arial",20), justify=CENTER, width=WIDTH, height=HEIGHT, borderwidth=1, relief=SOLID, bg=ACTIVE_COLOUR, fg=TEXT_COLOUR)
                    lbl.config(command=self.question_gen(tk, cat, val, lbl))
                    lbl.grid(column=cctr, row=rctr, ipadx=10, ipady=5, columnspan=1, rowspan=1)
                    cctr += 1
                rctr += 1
            # create scores at the bottom
            create_buffer(self.footer, TOPSCOREBOARD_BUFFER).pack(side=TOP)
            self.team_score_gen(self.footer).pack(side=TOP, anchor=CENTER)
            self.show_mainboard()
            # create continue button 
            cont_button = Button(self.footer, text="End Stage", font=("Arial", 20, 'bold'), bg=END_BUTTON_COLOUR, fg=END_BUTTON_TEXTCOLOUR)
            cont_button.config(command=self.double_jeopardy_boardgen(tk))
            create_buffer(self.footer, END_BOTTOM_BUFFER).pack(side=BOTTOM)
            cont_button.pack(side=BOTTOM, anchor=CENTER, fill=X)
            
        return initial_board
    
    # TODO when I want to include a double jeopardy then fill this function in
    # for now it just skips and calls final jeopardy
    def double_jeopardy_boardgen(self, tk: Tk):
        def double_jeopardy():
            self.reset_mainboard(tk)
            # reset board TODO (skip for this week)
            # go to final jeopardy TODO replace this with a button that does it instead
            self.final_jeopardy_boardgen(tk)()
        return double_jeopardy
    
    # handles making the display for final jeopardy
    # note it's also written as a function that returns a function in order to have it be usable as a callback function
    def final_jeopardy_boardgen(self, tk: Tk):
        def final_jeopardy():
            self.reset_mainboard(tk)
            # create title and heading
            tf = LabelFrame(self.mainboard)
            tf.pack(side=TOP, fill=X)
            title = Label(tf, text=self.title, font=("Arial",24,'bold'))
            title.pack(side=TOP)
            if HAVEIMG:
                title.config(image=TITLEIMG, compound=LEFT, text=" "+self.title)
            heading = Label(self.mainboard, text="Final Jeopardy!", font=("Arial",32,'bold'))
            heading.pack(side=TOP, anchor=CENTER, ipady=10)
            # create prompt for each team to bet
            create_buffer(self.mainboard, BET_BUFFER).pack(side=TOP)
            bet_frame = Frame(self.mainboard) # frame to hold the betting lines
            bet_frame.pack(side=TOP, anchor=CENTER)
            # get order of teams from highest score
            # this one-liner produces a sorted list of team names from highest to lowest scores
            # sorted takes 3 parameters:
            # iterable (e.g., list) to be sorted
            # key= function that produces comparable things
            # reverse= boolean indicating to sort highest to lowest or vice versa
            # the "lambda" is an anonymous function
            # it has a similar effect if I had a function:
            # def somefunction(tn):
            #   return self.get_score(tn)
            team_order = sorted(self.team_names, key=lambda tn : self.get_score(tn), reverse=True)
            # initialise the StringVar for each team's bet
            team_bet = {tname: StringVar(tk, "0") for tname in self.team_names}
            WIDTH = 10 # TODO move this to global variables
            HEIGHT = 2
            WRAPLENGTH = 160
            # a validation function for checking if a string value only contains numbers
            def is_num(val):
                if val.isdecimal():
                    return True
                elif val == "":
                    return True
                else:
                    return False
            val_cmd = tk.register(is_num) # we need to register the validation function to use it
            # a function for the continue button to process the bets
            def process_bet(strval, tname, no_negatives):
                if strval == "": # interpret empty string as a $0 bet
                    return 0
                numval = int(strval)
                if no_negatives: # if no_negatives was set then we need to do a few more checks
                    if numval < 0 or self.get_score(tname) <= 0: # if team is broke or bet negative, set bet to $0
                        return 0
                    if numval > self.get_score(tname): # if team bet more than they have, set bet to all they have
                        score = self.get_score(tname)
                        self.modify_score(tname, -score) # we handle bets by subtracting it from the score for now
                        return score
                self.modify_score(tname, -numval)
                return numval
            # make the entries for each team to bet in order of the most to the least points
            for tn in team_order:
                # Frame to group all elements of one team together
                betsubframe = Frame(bet_frame)
                betsubframe.pack(side=TOP, anchor=CENTER)
                # labels for the team name and the colon
                # note we separate the two as it looks nicer like this if the teamname takes multiple lines
                Label(betsubframe, text=f"{tn}", font=("Arial",20,'bold'),fg=self.team_colours[tn], width=WIDTH, height=HEIGHT, wraplength=WRAPLENGTH).pack(side=LEFT)
                Label(betsubframe, text=f":  ", font=("Arial",20,'bold'),fg=self.team_colours[tn], height=HEIGHT).pack(side=LEFT)
                # Entry widget for entering a text field
                # note the use of validate and validate command
                # "key" just means it validates on keystrokes
                # validate command tells it to run the above defined validation function and return using the P format code
                Entry(betsubframe, textvariable=team_bet[tn], font=("Arial", 20), validate="key", validatecommand=(val_cmd, "%P")).pack(side=LEFT)
                # score label at the end so teams know how much they have
                # note we set the width so that each line has the same width
                Label(betsubframe, text=f"({self.scores[tn].get()})", font=("Arial",20,'bold'),fg=self.team_colours[tn], width=8).pack(side=LEFT)
            # create button to continue to next stage
            next_stage = Button(self.mainboard, pady=5, text="Continue", font=("Arial",20,'bold'))
            # moves on from the betting screen to the question screen
            def final_jeopardy_questiongen(bets):
                def final_jeopardy_question():
                    # save bet values in case we lose it when resetting the board
                    bet_vals = {tn: process_bet(bets[tn].get(), tn, NO_NEG_BETS) for tn in self.team_names}
                    # reset board
                    self.reset_mainboard(tk)
                    # create title and heading
                    tf = LabelFrame(self.mainboard)
                    tf.pack(side=TOP, fill=X)
                    title = Label(tf, text=self.title, font=("Arial",24,'bold'))
                    title.pack(side=TOP)
                    if HAVEIMG:
                        title.config(image=TITLEIMG, compound=LEFT, text=" "+self.title)
                    heading = Label(self.mainboard, text="Final Jeopardy!", font=("Arial",32,'bold'))
                    heading.pack(side=TOP, anchor=CENTER, ipady=10)
                    # generate question
                    create_buffer(self.mainboard, HEADING_Q_BUFFER).pack(side=TOP)
                    Label(self.mainboard, text=self.final_data["question"], font=("Arial", 24), justify=CENTER, wraplength=WRAPLENGTH_QA).pack(side=TOP, ipadx=10, ipady=10)
                    # generate team points display
                    pointframe = self.team_score_gen(self.footer, rowoffset=2)
                    pointframe.pack(side=BOTTOM, anchor=CENTER)
                    # put bet amounts in points display
                    bet_lbls = {tn : Label(pointframe, text=f"${bet_vals[tn]}", fg=self.team_colours[tn], font=("Arial", 24, 'bold'), bg=SCORE_BG_COLOUR) for tn in self.team_names}
                    ctr = 0
                    for tn in self.team_names:
                        bet_lbls[tn].grid(column=ctr, row=1, columnspan=1, rowspan=1)
                        ctr += 1
                    # put reveal answer button
                    reveal_button = Button(self.footer, text="Reveal Answer", font=("Arial",20,'bold'))
                    # function for the reveal answer button
                    # displays the answer, removes itself, bring up the ui for marking teams and continuing
                    def reveal_function_gen(rb:Button):
                        def reveal_function():
                            # display answer
                            create_buffer(self.mainboard, Q_A_BUFFER).pack(side=TOP)
                            Label(self.mainboard, text=self.final_data["answer"], font=("Arial",24,'italic'), justify=CENTER, wraplength=WRAPLENGTH_QA).pack(side=TOP,ipady=10,ipadx=10)
                            # generate right/wrong buttons
                            ctr = 0
                            for tname in self.team_names:
                                button_frame = Frame(pointframe) # single frame for the buttons so that both take up (half) the same grid space
                                button_frame.grid(row=0,column=ctr, columnspan=1, rowspan=1)
                                ctr += 1
                                plus_button = Button(button_frame, text="+", font=("Arial",20,'bold'), bg="green", fg="white")
                                minus_button = Button(button_frame, text="-", font=("Arial",20,'bold'), bg="red", fg="white")
                                # function for the plus and minus buttons
                                # disables themself and their pair
                                # note it is written generically for both plus and minus buttons
                                def button_func_gen(scoreval, team, pbutton, mbutton):
                                    def button_func():
                                        pbutton.config(state=DISABLED, bg="grey")
                                        mbutton.config(state=DISABLED, bg="grey")
                                        self.modify_score(team, scoreval)
                                        bet_lbls[team].config(text="$0")
                                    return button_func
                                plus_button.config(command=button_func_gen(bet_vals[tname]*2, tname, plus_button, minus_button))
                                minus_button.config(command=button_func_gen(0, tname, plus_button, minus_button))
                                minus_button.pack(side=LEFT)
                                plus_button.pack(side=RIGHT)
                            # generate continue button
                            def cont_button_func():
                                # go to final victor screen
                                self.podium(tk)
                            create_buffer(self.footer, CONT_SCORE_BUFFER).pack(side=BOTTOM)
                            cont_button = Button(self.footer, text="Continue", font=("Arial", 24, 'bold'), command=cont_button_func).pack(side=BOTTOM)
                            # delete button
                            rb.destroy()
                        return reveal_function
                    reveal_button.config(command=reveal_function_gen(reveal_button))
                    reveal_button.pack(side=TOP, anchor=CENTER)
                    create_buffer(self.footer, CONT_SCORE_BUFFER).pack(side=TOP)
                    self.show_mainboard()
                return final_jeopardy_question
            next_stage.config(command=final_jeopardy_questiongen(team_bet))
            next_stage.pack(side=TOP, anchor=CENTER)
            self.show_mainboard()
        return final_jeopardy
    
    # generates the final victor screen
    def podium(self, tk:Tk):
        self.reset_mainboard(tk)
        # place title
        tf = LabelFrame(self.mainboard)
        tf.pack(side=TOP, fill=X)
        title = Label(tf, text=self.title, font=("Arial",24,'bold'))
        title.pack(side=TOP)
        if HAVEIMG:
            title.config(image=TITLEIMG, compound=LEFT, text=" "+self.title)
        # get winning team(s)
        # note we reuse our one-liner for sorting, might be better to make a separate function and call that
        team_order = sorted(self.team_names, key=lambda tn : self.get_score(tn), reverse=True)
        winning_score = self.get_score(team_order[0])
        winners = []
        # there may be more than one team with the winning score
        for tn in self.team_names:
            if self.get_score(tn) == winning_score:
                winners.append(tn)
        # winners[0] should never index error as there should always be at least one team with a winning score (the team in team_order[0])
        winnertext = f"{winners[0]} Wins!" # set winner message (overridden if there are ties)
        fg_colour = self.team_colours[winners[0]] # set colour of text to winning team's colour
        # check for ties
        if len(winners) == len(self.team_names) and len(self.team_names) > 2:
            # tie between all teams
            winnertext = f"It's a Tie!"
            fg_colour="Black"
        elif len(winners) > 1 and len(self.team_names) > 2:
            # multi-way tie but not between all teams
            winnertext = f"{len(winners)}-Way Tie!"
            fg_colour="Black"
        elif len(winners) == 2 and len(self.team_names) == 2:
            # two-way tie between two teams TODO this is kind of pointless, can be merged with the first condition
            winnertext = "It's a Tie!"
            fg_colour="Black"
        # display winner message
        Label(self.mainboard, text=winnertext, font=("Arial",24,'bold'),fg=fg_colour).pack(side=TOP,anchor=CENTER,ipady=10)
        # display scoreboard
        scoreframe = LabelFrame(self.mainboard, pady=10) # frame to contain the scoreboard
        scoreframe.pack(side=TOP, anchor=CENTER)
        rctr = 0
        # for each team, in order of highest to lowest points
        # note we use grid for this as it is easier to manage
        # pack can work as well, but will require us to make a container frame for each line
        for tn in team_order:
            # write team name
            Label(scoreframe, text=f"{tn}", pady=5, font=("Arial",20,"bold"),
                  fg=self.team_colours[tn], justify=CENTER, anchor=E,
                  width=FSCOREBOARD_WIDTH, height=FSCOREBOARD_HEIGHT, wraplength=FSCOREBOARD_WARP).grid(row=rctr, column=0, rowspan=1, columnspan=1)
            # write colon
            Label(scoreframe, text=f": ", pady=5, font=("Arial",20,"bold"),
                  fg=self.team_colours[tn],
                  height=FSCOREBOARD_HEIGHT).grid(row=rctr, column=1, rowspan=1, columnspan=1)
            # write team score
            Label(scoreframe, text=f"{self.scores[tn].get()}", pady=5, font=("Arial",20,"bold"),
                  fg=self.team_colours[tn], justify=LEFT,
                  width=FSCOREBOARD_WIDTH, height=FSCOREBOARD_HEIGHT, wraplength=FSCOREBOARD_WARP).grid(row=rctr, column=2, rowspan=1, columnspan=1)
            rctr += 1
        self.show_mainboard()
    
    # generate the scores in a frame (mainly to place at self.footer)
    # rowoffset allows us to make it start from a different grid row to make space for inserting elements above the scoreboard
    def team_score_gen(self, parent, rowoffset=0) -> Frame:
        # create scores
        scf = Frame(parent, bg=SCORE_BG_COLOUR) # frame for the scoreboard
        ctr = 0
        WIDTH = 10 # TODO make this into a global variable
        HEIGHT = 2
        WRAPLENGTH = 160
        # for each team name
        for tname in self.team_names:
            # create the team name label
            lbl = Label(scf, text=f"{tname}:", font=("Arial", 20, 'bold'), fg=self.team_colours[tname], width=WIDTH, height=HEIGHT, justify=CENTER, wraplength=WRAPLENGTH, bg=SCORE_BG_COLOUR)
            lbl.grid(column=ctr, row=0+rowoffset, columnspan=1, rowspan=1, ipadx=10, ipady=0)
            # create the score labels
            # note the use of textvariable pointing to a StringVar instead of a static python string
            # this allows the scoreboard to update itself as long as the value stored in the StringVar changes
            sclbl = Label(scf, font=("Arial", 20, 'bold'), fg=self.team_colours[tname], textvariable=self.scores[tname], bg=SCORE_BG_COLOUR)
            sclbl.grid(column=ctr, row=1+rowoffset, columnspan=1, rowspan=1)
            ctr += 1
        return scf
        
    # simple function to describe what to do when disabling a tile
    def disable_mainbutton(self, button: Button):
        button.config(state=DISABLED, text="", bg=DISABLE_COLOUR)
    
    # creates the disaply for a question page
    def question_gen(self, tk:Tk, cat: str, val: str, activator: Button):
        def question_display(): 
            imgbufferreset = []
            self.disable_mainbutton(activator) # disables the button that was use to go to this question
            self.remaining[cat][val] = False
            self.hide_mainboard() # hides the main board
            questionboard_top = Frame(tk) # frame for 'mainboard' here
            questionboard_top.pack(side=TOP)
            questionboard_bot = Frame(tk) # frame for 'footer' here
            questionboard_bot.pack(side=BOTTOM)
            # generate heading
            text_static = Frame(questionboard_top)
            text_static.pack(side=TOP)
            Label(text_static, text=f"{cat} - ${val}", font=("Arial",20,'bold')).pack(side=TOP, anchor=CENTER, ipady=10, ipadx=10)
            # generate question prompt
            create_buffer(text_static, HEADING_Q_BUFFER).pack(side=TOP) # buffer
            question_text = self.qa[cat]["questions"][val]
            # handling different formats
            # if question prompt is just a string, then just place it in
            if type(question_text) == str:
                Label(text_static, text=question_text, font=("Arial", 24), justify=CENTER, wraplength=WRAPLENGTH_QA).pack(side=TOP, ipadx=5, ipady=5)
            elif type(question_text) == list:
                # otherwise, if it is a list
                for qtxt in question_text:
                    # check if there is a < > tag at the start
                    if qtxt[0] == "<" and qtxt[2] == ">":
                        # interpret <l> as a 'list' - left justify instead of center so that elements are inline with each other
                        if qtxt[1] == "l":
                            Label(text_static, text=qtxt[3:], font=("Arial", 24), justify=LEFT, wraplength=WRAPLENGTH_QA).pack(side=TOP, ipadx=5, ipady=5)
                        # <i>=filename\\> tag to indicate picture/image
                        if qtxt[1] == "i":
                            # qtxt[3] should be '='
                            # then we need to find the index of '\\>'
                            # note, for now we assume it is only a single image with nothing else
                            filenamepart = qtxt[3:][(qtxt[3:].find("=")+1):qtxt[3:].find("\\>")]
                            image_width = DEFAULTIMAGE_WIDTH
                            image_height = DEFAULTIMAGE_HEIGHT
                            if (qtxt[3:].find("{height=") != -1):
                                heightstart = qtxt[3:].find("{height=") + len("{height=") + 3
                                heightend = qtxt[heightstart:].find("}") + heightstart
                                try:
                                    image_height = min(int(qtxt[heightstart:heightend]),IMAGEMAX_HEIGHT)
                                except:
                                    pass
                            
                            if (qtxt[3:].find("{width=") != -1):
                                widthstart = qtxt[3:].find("{width=") + len("{width=") + 3
                                widthend = qtxt[widthstart:].find("}") + widthstart
                                try:
                                    image_width = min(int(qtxt[widthstart:widthend]),IMAGEMAX_WIDTH)
                                except:
                                    pass
                            try:
                                image_path = join(dirname(__file__), image_folder, filenamepart)
                                image = ImageTk.PhotoImage(Image.open(image_path).resize((image_width,image_height)))
                                IMAGEBUFFER.append(image)
                                imgbufferreset.append(image)
                                Label(text_static, image=image, justify=CENTER, compound="center", text='').pack(side=TOP, ipadx=5, ipady=5)
                            except Exception as e:
                                print(e)
                                Label(text_static, text=filenamepart, font=("Arial", 24, 'italic'), justify=CENTER, wraplength=WRAPLENGTH_QA).pack(side=TOP, ipadx=5, ipady=5)
                    else: # no tag, treat as string
                        Label(text_static, text=qtxt, font=("Arial", 24), justify=CENTER, wraplength=WRAPLENGTH_QA).pack(side=TOP, ipadx=5, ipady=5)
            # generate team point display
            pointframe = self.team_score_gen(questionboard_bot, rowoffset=1)
            pointframe.pack(side=BOTTOM, anchor=CENTER)
            # generate answer display button
            create_buffer(text_static, Q_A_BUFFER).pack(side=TOP)
            ans_frame = Frame(questionboard_top)
            ans_frame.pack(side=TOP,anchor=CENTER)
            ans_button = Button(questionboard_bot,text="Reveal Answer", font=("Arial",20,'bold'))
            def reveal_answer():
                # create answer field
                Label(ans_frame, text=self.qa[cat]["answers"][val], font=("Arial",24,'italic'), justify=CENTER, wraplength=WRAPLENGTH_QA).pack(side=TOP,ipady=10,ipadx=10)
                # destroy button
                ans_button.destroy()
                # generate team point giver (include no team and +/- points)
                ctr = 0
                # for each team, generate the + and - points button
                for tname in self.team_names:
                    button_frame = Frame(pointframe, name=f"bframe{ctr}")
                    button_frame.grid(row=0,column=ctr, columnspan=1, rowspan=1)
                    plus_button = Button(button_frame, text="+", font=("Arial",20,'bold'), bg="green", fg="white", name=f"pbutton{ctr}")
                    minus_button = Button(button_frame, text="-", font=("Arial",20,'bold'), bg="red", fg="white")
                    def button_func_gen(scoreval, team, pbutton, mbutton):
                        def button_func():
                            # if only one answer value is set, disable all positive buttons when one is pressed
                            if (ONLY_ONE_ANSWER and scoreval > 0):
                                for ct in range(len(self.team_names)):
                                    pointframe.nametowidget(f"bframe{ct}").nametowidget(f"pbutton{ct}").config(state=DISABLED, bg="grey")
                            # disable button pair
                            pbutton.config(state=DISABLED, bg="grey")
                            mbutton.config(state=DISABLED, bg="grey")
                            self.modify_score(team, scoreval)
                        return button_func
                    plus_button.config(command=button_func_gen(int(val), tname, plus_button, minus_button))
                    minus_button.config(command=button_func_gen(-int(val), tname, plus_button, minus_button))
                    minus_button.pack(side=LEFT)
                    plus_button.pack(side=RIGHT)
                    ctr += 1
                # create continue button (return to mainboard)
                def cont_button_func():
                    self.show_mainboard()
                    questionboard_bot.destroy()
                    questionboard_top.destroy()
                    for img in imgbufferreset:
                        IMAGEBUFFER.remove(img)
                print("making cont button")
                cont_button = Button(questionboard_top, text="Continue", font=("Arial", 24, 'bold'), command=cont_button_func)
                cont_button.pack(side=TOP)
                create_buffer(questionboard_bot, CONT_SCORE_BUFFER).pack(side=TOP)
            ans_button.config(command=reveal_answer)
            ans_button.pack(side=TOP, anchor=CENTER, ipadx=10, ipady=10)
            create_buffer(questionboard_bot, CONT_SCORE_BUFFER).pack(side=TOP)
        return question_display

# create team name menu (menu for entering the team names)
def mm_transition(tk: Tk, num_teams: IntVar, mmframe: Frame, maingame: MainGame):
    def create_team_name_menu():
        mmframe.destroy() # remove the main menu
        mm = Frame(tk) # create a new frame for this menu
        mm.pack(fill='both', anchor=N,side=TOP)
        # make title
        mm_tf = LabelFrame(mm)
        mm_tf.pack(anchor=N,fill='x', side=TOP)
        mm_title = Label(mm_tf,text=TITLE,justify='center', anchor='center', font=("Arial",32,'bold'))
        mm_title.pack(anchor='center')
        if HAVEIMG:
            mm_title.config(image=TITLEIMG, compound=LEFT, text=" "+TITLE)
        create_buffer(mm, MENU_RBUTTON_BUFFER).pack(side=TOP)
        team_names = []
        tn_frame = Frame(mm)
        tn_frame.pack(side=TOP)
        # for each team, initialise a StringVar with default name Team _
        for i in range(num_teams.get()):
            tn_var = StringVar(tk,f"Team {i+1}")
            team_names.append(tn_var)
            # create text field to enter team name
            # note the use of textvariable
            # this stores the value so we can use it later without needing to do a fickly get on the Entry widget itself
            Entry(tn_frame, textvariable=tn_var, font=("Arial",24)).pack(side=TOP, pady=10, ipady=10)
        # make start button
        create_buffer(mm, MENU_START_BUFFER).pack(side=TOP)
        mm_bf = Frame(mm)
        mm_bf.pack(side=TOP)
        mm_sb = Button(mm_bf, text="Start", font=("Arial",20,'bold'),fg='white',bg='green', command=maingame.initial_board_gen(tk, mm,team_names)).pack(side=TOP,ipadx=5)       
    return create_team_name_menu

# create main menu (select number of teams)
def create_main_menu(tk: Tk, maingame: MainGame):
    mm = Frame(tk)
    mm.pack(fill='both', anchor='n',side=TOP)
    # make title
    mm_tf = LabelFrame(mm)
    mm_tf.pack(anchor="n",fill='x', side=TOP)
    mm_title = Label(mm_tf,text=TITLE,justify='center', anchor='center', font=("Arial",32,'bold'))
    mm_title.pack(anchor='center')
    if HAVEIMG:
        mm_title.config(image=TITLEIMG, compound=LEFT, text=" "+TITLE)
    create_buffer(mm, MENU_RBUTTON_BUFFER).pack(side=TOP)
    # make num team selection
    mm_rbf = Frame(mm) # frame to store all the radio buttons
    mm_rbf.pack(side=TOP)
    mm_rbl = Label(mm_rbf, text="Number of teams:", font=("Arial",24,'underline')).pack(side=TOP)
    rb_return = IntVar(tk, 2) # intvar stores the integer value the radio buttons will give us
    rb_value = {
        "2 teams": 2,
        "3 teams": 3,
        "4 teams": 4
    }
    # for each key-value we specified just above, we create a radio button
    for (text, value) in rb_value.items():
        # note the use of variable and value
        # value tells us what value the radio button will give variable when it is clicked
        # variable tells us where to store the value
        Radiobutton(mm_rbf, text=text, variable=rb_return, value=value, font=("Arial",20)).pack(side=TOP, ipady=5)
    # we initialise the value to 2 teams
    rb_return.set(2)
    # make start button
    create_buffer(mm, MENU_START_BUFFER).pack(side=TOP)
    mm_bf = Frame(mm)
    mm_bf.pack(side=TOP)
    mm_sb = Button(mm_bf, text="Start", font=("Arial",20,'bold'),fg='white',bg='green', command=mm_transition(tk,rb_return,mm, maingame)).pack(side=TOP,ipadx=5)

# The important part that actually calls the functions to begin with
tk.bind("<F11>", lambda x: tk.attributes("-fullscreen",True))
tk.bind("<Escape>", lambda x: tk.attributes("-fullscreen",False))
MAINGAME = MainGame(gamedata_json["categories"], gamedata_json["final"], title=TITLE) # generates the class that stores game data
create_main_menu(tk, MAINGAME) # create main menu generates the elements of the first page
tk.mainloop() # mainloop starts tkinter's gui