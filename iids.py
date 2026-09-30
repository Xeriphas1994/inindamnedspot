print("""
    iids.py: draw markers on map images for doomwiki.org walkthroughs

    License: GPLv3+ - see https://www.gnu.org/licenses/#GPL
    There is ABSOLUTELY NO WARRANTY, not even for MERCHANTIBILITY or
    FITNESS FOR A PARTICULAR PURPOSE.

""")
import sys
import os
import subprocess
import shutil
from ctypes import windll
# import copy
import tkinter
from tkinter import *
# looks redundant but removal is a fatal error
from tkinter import ttk
from tkinter.ttk import *
from tkinter.scrolledtext import ScrolledText
import math
# EDIT: this makes it nonportable, right?  Jiminy christmas, I thought I was
# trying so hard.  I didn't even use transparency commands.
from PIL import Image
# Reluctantly including this in anticipation of more complex operations on pixel
# colors.  The current version (end of 2025) probably doesn't need it.
import numpy

# Parse launch command.
def validate_params(params): # params
    # if len(params) < 5:
    #     raise RuntimeError("Too few arguments")
    if ('-input' not in params) or ('-input' == params[-1]):
        raise RuntimeError("Input file name missing")
    inputfile = params[params.index('-input') + 1]
    if ('-output' not in params) or ('-output' == params[-1]):
        raise RuntimeError("Output file name missing")
    outputfile = params[params.index('-output') + 1]
    if ('-pane' in params) and (params.index('-pane') != len(params)-1):
        panefile = params[params.index('-pane') + 1]
    else:
        panefile = ''
    if ('-magick' not in params) or ('-magick' == params[-1]):
        raise RuntimeError("ImageMagick location missing")
    magick_path = params[params.index('-magick') + 1]
    dot_radius = 7
    if ('-dotradius' in params) and (params.index('-dotradius') != len(params)-1):
        try:
            dot_radius = int(float(params[params.index('-dotradius') + 1]))
        except:
            print("Warning: couldn't parse -dotradius value, retaining default value.\n")
    dot_color = r'#800080'
    if ('-dotcolor' in params) and (params.index('-dotcolor') != len(params)-1):
        color_attempt = params[params.index('-dotcolor') + 1].ljust(6)
        try:
            color_parse = int(color_attempt, 16)
        except:
            print("Warning: couldn't parse -dotcolor value, retaining default value.\n")
        else:
            dot_color = r'#' + color_attempt.lower()
    label_size = 12
    if ('-labelsize' in params) and (params.index('-labelsize') != len(params)-1):
        try:
            label_size = int(float(params[params.index('-labelsize') + 1]))
        except:
            print("Warning: couldn't parse -labelsize value, retaining default value.\n")
    label_color = r'#ffffff'
    if ('-labelcolor' in params) and (params.index('-labelcolor') != len(params)-1):
        color_attempt = params[params.index('-labelcolor') + 1].ljust(6)
        try:
            color_parse = int(color_attempt, 16)
        except:
            print("Warning: couldn't parse -labelcolor value, retaining default value.\n")
        else:
            label_color = r'#' + color_attempt.lower()
    line_width = 4
    if ('-linewidth' in params) and (params.index('-linewidth') != len(params)-1):
        try:
            line_width = int(float(params[params.index('-linewidth') + 1]))
        except:
            print("Warning: couldn't parse -linewidth value, retaining default value.\n")
    # os.remove(outputfile)
    return inputfile, outputfile, magick_path, panefile, dot_radius, dot_color, label_size, label_color, line_width

# Get next label in sequence (which is defined implicitly, apologies if
# you're trying to customize the labels and this makes it more difficult).
def next_letter(lettre):
    if lettre[0] == 'Z':
        final = 'A' * (len(lettre) + 1)
    else:
        ancilla = chr(ord(lettre[0]) + 1)
        final = ancilla * len(lettre)
    return final

# Put the next label as a "prompt" at the bottom of the coordinate
# array which is not necessarily fully refreshed yet.
def reset_letter(coord_buffer_list):
    # Prevent backspacing past the beginning.
    if len(coord_buffer_list) == 0:
        return [ [ 'A', '', '' ] ]
    lettre = ''
    jj = -1
    while lettre == '':
        lettre = coord_buffer_list[jj][0]
        jj = jj - 1
    lettre = next_letter(lettre)
    coord_buffer_list.append( [ lettre , '' , '' ] )
    return coord_buffer_list

# Flatten coordinate array into a string for more predictable printing.
def unexplode(coord_buffer_list):
    coord_buffer = ''
    for ii in coord_buffer_list:
        coord_buffer = coord_buffer + "\t".join(ii) + "\n"
    return coord_buffer

# Refresh text pane.
def update_array():
    w2.config(state='normal')
    w2.delete("1.0", tkinter.END)
    w2.insert(tkinter.END, coord_buffer)
    w2.see(tkinter.END)
    w2.config(state='disabled')
    # root.update_idletasks()

# Overall "effect of clicking" routine,
# amalgamated from tiny flecks of pages cited in credits.txt > tkinter.
def callback(event):
    # My textbook definitely says not to do this.
    global coord_buffer_list
    global coord_buffer
    global pane_flag
    speck_color = r'#800080'
    speck_radius = 3
    # this is a total guess
    scribble_font_size = 18
    # If there's something in the first position of the last row, then
    # we're a dot and coordinates go in the third position.
    # If there isn't, but the second position of the last row contains
    # the line symbol, then we're a line and the click
    # represents the coordinates of the sharp end, which still go in
    # the third position.
    if ( coord_buffer_list[-1][0] != '' ) or ( coord_buffer_list[-1][1] == '~~~>' ):
        coord_buffer_list[-1][2] = "(" + str(event.x) + "," + str(event.y) + ")"
        # Either way assume the next click will be a new letter, which is overwhelmingly
        # often true, and refresh the displayed "prompt".
        coord_buffer_list = reset_letter(coord_buffer_list)
        if not(pane_flag):
            if coord_buffer_list[-2][0] == '':
                # draw placeholder dot for line destination
                w1.create_oval(
                    event.x - speck_radius, event.y - speck_radius, 
                    event.x + speck_radius, event.y + speck_radius, 
                    fill=speck_color, 
                    outline=speck_color
                )
            else:
                # write placeholder text label
                w1.create_text(event.x, event.y, text=coord_buffer_list[-2][0], font=("Courier", scribble_font_size), fill=speck_color)
    # Otherwise, we're within a dashed path and the click is an "anchor" coordinate,
    # which goes in the second position.
    else:
        coord_buffer_list.append( [ '' , '(' + str(event.x) + ',' + str(event.y) + ')' , '' ] )
        if not(pane_flag):
            # draw placeholder dot for line destination
            w1.create_oval(
                event.x - speck_radius, event.y - speck_radius, 
                event.x + speck_radius, event.y + speck_radius, 
                fill=speck_color, 
                outline=speck_color
            )
    # Refresh cumulative coordinates displayed.
    coord_buffer = unexplode(coord_buffer_list)
    update_array()

# Stop displaying widget.
def close_window(event):
    global coord_buffer_list
    # Block exiting if a line or path is currently incompletely specified.
    if coord_buffer_list[-1][0] != '':
        root.destroy()

# Erase a row in coordinate array.
def backspace(event):
    global coord_buffer_list
    global coord_buffer
    # Prevent backspacing past the beginning.
    # If a line command is in progress, don't do anything yet, to avoid off-by-one error.
    if len(coord_buffer_list) > 1 and coord_buffer_list[-1][1] != '~~~>':
        # If we are in a path, there is no prompt, so only remove one line.
        # Exception: if we just backed into a path sequence to modify it, do not
        # prompt for a new letter until it ends again.
        # Exception to exception: if we just erased the start of a path, we do need
        # the prompt.
        if coord_buffer_list[-1][0] == '' and coord_buffer_list[-1][1] == 'PATH START':
            del coord_buffer_list[-1]
            coord_buffer_list = reset_letter(coord_buffer_list)
        elif coord_buffer_list[-1][0] == '':
            del coord_buffer_list[-1]
        elif coord_buffer_list[-2][1] == 'PATH END':
            del coord_buffer_list[-1]
            del coord_buffer_list[-1]
        else:
            del coord_buffer_list[-1]
            del coord_buffer_list[-1]
            coord_buffer_list = reset_letter(coord_buffer_list)
        coord_buffer = unexplode(coord_buffer_list)
        update_array()

# Add pointing solid line onto a dot, to which a second set of coordinates will
# be tacked on later representing the sharp end.
def linestart(event):
    global coord_buffer_list
    global coord_buffer
    # Assume we need to place at least one dot before a line can have meaning.
    if len(coord_buffer_list) > 1:
        del coord_buffer_list[-1]
        coord_buffer_list.append( [ '' , '~~~>' , '' ] )
        coord_buffer = unexplode(coord_buffer_list)
    update_array()

# Demark start and end of a dashed line in UI ("path" named from GIMP even though
# we're not using GIMP).
def pathing(event):
    global coord_buffer_list
    global coord_buffer
    # If prompt is waiting, it's the start of a path.
    if coord_buffer_list[-1][1:3] == [ '', '' ]:
        coord_buffer_list[-1][0] = ''
        coord_buffer_list[-1][1] = 'PATH START'
        coord_buffer = unexplode(coord_buffer_list)
    # If prompt is not waiting and the middle column is a coordinate,
    # we're within a path (because a dot or solid line would have the
    # coordinate in the right column), so hitting P ends it.
    # Exception: the middle column has to be a coordinate in
    # the last 3 rows, not just 1, because bezier functionality in
    # ImageMagick requires at least 3 points.
    elif coord_buffer_list[-1][0] == '' and coord_buffer_list[-1][1][0] == '(' and coord_buffer_list[-2][1][0] == '(' and coord_buffer_list[-3][1][0] == '(':
        coord_buffer_list.append( [ '' , 'PATH END' , '' ] )
        coord_buffer_list = reset_letter(coord_buffer_list)
        coord_buffer = unexplode(coord_buffer_list)
    # At other junctures it shouldn't be syntactically the right time to
    # insert this command, so no action is default.
    update_array()

# Make the label prompt duplicate the previous one (will be rendered smaller
# in the final image to distinguish them visually, or at least that's
# what our few published precedents did).
def reuse_letter(event):
    global coord_buffer_list
    global coord_buffer
    rr = -2
    while coord_buffer_list[rr][0] == '':
        rr = rr - 1
    # Hmm, should be a way to undo this without erasing the entire
    # line you entered earlier.  How about hitting R a second time?
    if coord_buffer_list[-1][0] == coord_buffer_list[rr][0]:
        coord_buffer_list[-1][0] = next_letter(coord_buffer_list[rr][0])
    else:
        coord_buffer_list[-1][0] = coord_buffer_list[rr][0]
    coord_buffer = unexplode(coord_buffer_list)
    update_array()

# Map mouse click data to their intended locations on full-size unmarked image.
# For huge maps some roundoff error is possible, but pixel-exact dot locations
# would be false precision anyway for a game walkthrough.
def coord_inflate(c, zoom_factor):
    # Python alias superglue skins my hand again
    # final = [['','','']]*len(c)
    final = []
    for iii in range(len(c)):
        final.append(['','',''])
        for jjj in range(3):
            if c[iii][jjj] != '':
                if c[iii][jjj][0] == '(':
                    (x_old, y_old) = c[iii][jjj][1:-1].split(',')
                    x_new = str(round(int(x_old) * zoom_factor))
                    y_new = str(round(int(y_old) * zoom_factor))
                    final[iii][jjj] = '(' + x_new + ',' + y_new + ')'
                # Labels and other non-coordinate entries don't change
                else:
                    final[iii][jjj] = c[iii][jjj]
    return final

# Assemble overall ImageMagick command line based on final array of coordinates with bounding punctuation,
# plus dimensional constants.
def build_magick(coord_buffer_list, magick_path, extra_magick, dot_radius_base, dot_color, line_width, dash_lengths, label_font, label_size_base, label_color, inputfile, outputfile):

    # Measure dimensions of each label, so they can be centered on the circles
    # more reliably than ImageMagick's standoffish "-gravity" command or trying to
    # read geometrical metadata from the font package.
    def center_letter(label_value, label_font, label_size, magick_path, outputfile_dir):
        # In hindsight this factor of 4 is futureproofing for different
        # ways of reducing font size when label is long.  (Can't make the
        # factor dynamic because we don't know the pixel dimensions of
        # letters in advance; if we did, we could just center using those
        # and not have this function.)
        square_dim = (4 * label_size) + 1
        center_dim = (2 * label_size) + 1
        calibrate_save = outputfile_dir + r'calibrate_' + label_value + r'.png'
        # 16-bit grays are probably overkill  :>  although I can envision a
        # bigger phase space where the label and dot can vary in colors and
        # you're somehow accounting for the visual contrast per combination
        # when deciding how to handle the antialiased pixels.  Hmm, maybe you
        # have to center it multiple times, one per channel?
        calibrate_command = magick_path + r' -size ' + str(square_dim) + r'x' + str(square_dim) + r' canvas:black -font "' + label_font + r'" -pointsize ' + str(label_size) + r' -fill "#ffffff" -draw "text ' + str(center_dim) + r',' + str(center_dim) + r' ' + chr(39) + label_value + chr(39) + r'" -compress none -depth 16 "' + calibrate_save + r'"'
        # print(calibrate_command)
        subprocess.run(calibrate_command)
        calibrate_handle = Image.open(outputfile_dir + r"calibrate_" + label_value + r".png")
        calibrate_line = numpy.asarray(list(calibrate_handle.getdata()))
        calibrate_array = numpy.reshape(calibrate_line, (square_dim, square_dim))
        ext = numpy.argwhere(calibrate_array)
        # For half pixel averages, this rounds toward the left and/or upward.
        # Represents another proxy for weighted averaging, perhaps, in the
        # manual compositing, but in this case it was based on nothing but my
        # 2006 self's intuition (graphology?).
        x_offset = -round(((max(ext[:,1])-min(ext[:,1]))/2) + 0.5)
        y_offset = round((max(ext[:,0])-min(ext[:,0]))/2)
        os.remove(calibrate_save)
        return x_offset, y_offset

    # Save individual label+dot images as files.
    def create_stickers(coord_buffer_list, smaller_labels, smallest_labels, dot_radius_base, dot_color, label_font, label_size_base, magick_path, outputfile_dir):
        print("Saving individual dots as images:")
        used_letters = ['']
        used_letters_radii = ['']
        for ll in coord_buffer_list:
            if ll[0] not in used_letters:
                # Reset from previous passes.
                dot_radius = dot_radius_base
                # This is very approximate (and not at all what I did in 2006); will be replaced
                # later by an adaptive approach I hope.
                label_size = round(label_size_base / math.sqrt(len(ll[0])))
                if ll[0] in smaller_labels:
                    dot_radius = round(dot_radius / math.sqrt(2))
                    label_size = round(label_size / math.sqrt(2))
                elif ll[0] in smallest_labels:
                    dot_radius = round(dot_radius / 2)
                    label_size = round(label_size / 2)
                else:
                    dot_radius = dot_radius_base
                    label_size = label_size_base
                (x_offset, y_offset) = center_letter(ll[0], label_font, label_size, magick_path, outputfile_dir)
                # Seems to need some fudge factor to avoid off-by-one errors while antialiasing.
                sticker_radius = dot_radius + 3
                sticker_filename = ll[0] + r'.png'
                component_command = magick_path + r' -size ' + str(2 * sticker_radius) + r'x' + str(2 * sticker_radius) + r' canvas:transparent -fill "' + dot_color + r'" -draw "circle ' + str(sticker_radius) + r',' + str(sticker_radius) + r' ' + str(sticker_radius) + r',' + str(sticker_radius + dot_radius) + r'" -font "' + label_font + r'" -pointsize ' + str(label_size) + r' -fill "' + label_color + r'" -draw "text ' + str(sticker_radius + x_offset) + r',' + str(sticker_radius + y_offset) + chr(39) + ll[0] + chr(39) + r'" ' + sticker_filename
                print("\t", ll[0] + r'.png')
                subprocess.run(component_command)
                used_letters.append(ll[0])
                used_letters_radii.append(sticker_radius)
        del used_letters[0]
        del used_letters_radii[0]
        # Oops, also remember radius with "error margin" added, because you have to offset the
        # destination position too.
        return used_letters, used_letters_radii

    # Provisional/silly approach to making dots slightly smaller when
    # labels are duplicated, as in the current map of 1SQUARES.WAD:
    # -- labels occurring once each are unchanged in radius
    # -- next smallest incidence is 1/sqrt(2) that size, including if multiple labels share that count
    # -- all other reused labels become 1/2 size
    label_list_scr = []
    count_list_scr = []
    smaller_labels = []
    smallest_labels = []
    for hh in coord_buffer_list:
        if hh[0] != '':
            if label_list_scr == [] or label_list_scr[-1] != hh[0]:
                label_list_scr.append(hh[0])
                count_list_scr.append(1)
            else:
                count_list_scr[-1] = count_list_scr[-1] + 1
    buckets = sorted(list(set(count_list_scr)))
    if len(buckets) > 1:
        for vv in range(len(label_list_scr)):
            if count_list_scr[vv] == buckets[1]:
                smaller_labels.append(label_list_scr[vv])
            if count_list_scr[vv] > buckets[1]:
                smallest_labels.append(label_list_scr[vv])
    # Create individual dot images.
    # I'm pretty sure I could do everything in memory with a much longer magick_command.  Hopefully this
    # way is more maintainable.  Also, IN 2025, CLIS CAN HAVE CHARACTER LENGTH LIMITS.
    outputfile_dir = outputfile[:(outputfile.rfind('\\') + 1)]
    (sticker_list, sticker_radius_list) = create_stickers(coord_buffer_list, smaller_labels, smallest_labels, dot_radius_base, dot_color, label_font, label_size_base, magick_path, outputfile_dir)
    # Build final ImageMagick call from the sticker files and line/path commands.
    magick_command = magick_path + r' "' + inputfile + r'"' + extra_magick
    in_path = False
    for cc in coord_buffer_list:
        if cc[0].isalpha():
            dot_label = cc[0]
            coord_string = cc[2]
            coord_x = coord_string[coord_string.index('(')+1:coord_string.index(',')]
            coord_y = coord_string[coord_string.index(',')+1:coord_string.index(')')]
            sticker_filename = dot_label + r'.png'
            sticker_radius = sticker_radius_list[sticker_list.index(dot_label)]
            magick_command = magick_command + r' ( -page +' + str(int(coord_x) - sticker_radius) + r'+' + str(int(coord_y) - sticker_radius) + r' ' + sticker_filename + r' )'
            # print(component_command, "\n")
        if cc[1] == '~~~>':
            coord_string_line = cc[2]
            coord_x_line = coord_string_line[coord_string_line.index('(')+1:coord_string_line.index(',')]
            coord_y_line = coord_string_line[coord_string_line.index(',')+1:coord_string_line.index(')')]
            magick_command = magick_command + r' -stroke "' + dot_color + r'" -strokewidth ' + str(line_width) + r' -draw "line ' + coord_x + r',' + coord_y + r' ' + coord_x_line + r',' + coord_y_line + r'"'
        if cc[1][0:4] == 'PATH':
            in_path = not(in_path)
            if in_path:
                magick_command = magick_command + r' -fill none -strokewidth ' + str(line_width) + r' -draw "stroke ' + dot_color + r' stroke-dasharray ' + str(dash_lengths[0]) + r' ' + str(dash_lengths[1]) + r' bezier'
            if not in_path:
                magick_command = magick_command + r' "'
        if in_path and cc[1][0] == '(':
            coord_string_curve = cc[1]
            coord_x_curve = coord_string_curve[coord_string_curve.index('(')+1:coord_string_curve.index(',')]
            coord_y_curve = coord_string_curve[coord_string_curve.index(',')+1:coord_string_curve.index(')')]
            magick_command = magick_command + r' ' + coord_x_curve + r',' + coord_y_curve
    # print("\n")
    magick_command = magick_command + r' -layers flatten "' + outputfile + r'"'
    # Track unique labels also, to mop up working directory at the end.
    return magick_command, sticker_list


            ############################################################
            ##                                                        ##
            ## INITIALIZE CONSTANTS, MOSTLY RELATED TO DRAWING SHAPES ##
            ##                                                        ##
            ############################################################

(inputfile, outputfile, magick_path, panefile, dot_radius, dot_color, label_size, label_color, line_width) = validate_params(sys.argv)
# Should use absolute path because if we make the temp directory the
# app directory in the system area, user might not be able to write.
# magick_path = r"C:\Program Files\ImageMagick-7.1.2-Q16-HDRI\magick.exe"
# Show some debug info because I'm an ImageMagick newbie.
# Don't compress PNGs because XymphBot already has, and you may create artifacts.
# (Doesn't entirely work, it seems, with no dots at all.  There is an open
# bug in ImageMagick about that.)
extra_magick = r' -verbose -quality 100'
# dot_radius = 7
# dot_color = r'#800080'
# line_width = 4
dash_lengths = [9,9]
label_font = r'Franklin-Gothic-Heavy'
# label_size = 12
# label_color = r'#ffffff'
coord_buffer_list = [ [ 'A', '', '' ] ]
# Hmm, actually we need to refresh before any input occurs, so the "A" is
# sitting there at the top corner to show we're ready.
coord_buffer = unexplode(coord_buffer_list)
pane1_weight = 3
pane2_weight = 1
# DEBUG 20251011
# dot_radius = 48
# label_size = 60


            ##################################
            ##                              ##
            ## INITIALIZE DATA ENTRY WIDGET ##
            ##                              ##
            ##################################

print("Building Python widget for entering marker coordinates.\n")
# Windows-specific shim
# If you don't use Windows, please test to find out if this type of command needs to be
# wrapped in a conditional that detects the OS.
windll.shcore.SetProcessDpiAwareness(1)
root = tkinter.Tk()
# Whatever "layering" approach eventually works for this, need to allow like 15px at the top
# for window titlebar, and 5px for margin to the screen corner.
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = int(screen_width * 0.9)
window_height = int(screen_height * 0.9)
# Windows-specific shim: a small invisible border is imposed around any window not fullscreen.
root.geometry(f"{window_width}x{window_height}+0+0")
root.resizable(width=False, height=False)
# A cheap hack, I suppose -- keeps window from encroaching 2nd display.  User should have
# optionality ideally.
root.attributes('-fullscreen', True)
root.wm_state('normal')
# Might want to change to 'vertical' if your display is in portrait orientation; can fit more coordinates that way.
main = ttk.PanedWindow(root, orient='horizontal')
# main.pack(expand=True, fill="both")


            ###################################################
            ##                                               ##
            ## LOAD BLANK MAP AND DEFINE DATA ENTRY COMMANDS ##
            ##                                               ##
            ###################################################

# -pane option is not really meant to be used; it's a workaround
# for the few cases where a finished map already existed, just didn't
# use the new and improved "crisp" XymphBot map view as background, which
# Xymph has said should ideally happen.  So they were good test cases for
# this script, whereas the walkthrough *prose* was written
# years ago and is stable.
# EDIT: I guess it's possible that people would use it to make small
# changes when an improvement is identified after upload, assuming there's
# still no way of resuming mid-map or editing coordinates in place.
# Which there should be.
if panefile == '':
    panefile = inputfile
    # if pane image is being used, we probably don't want the temp markers,
    # so the user isn't seeing two illegible labels in each location
    pane_flag = False
else:
    pane_flag = True
# No close command like Python's handles, according to the docs(!).  Have to trust them to
# free everything when the script and/or python.exe exits.
pane_handle = Image.open(panefile)
(x_nominal, y_nominal) = pane_handle.size
# If the pane image or base image is too large for the window,
# scale it down and remember the scale factor for later, because the
# coordinates you click (calculated automatically by the library) are no
# longer the coordinates on the base image.
# Horizontal inflation is capped so we still have room for the text pane
# even if the raw image is of similar dimensions to the display.
# (n.b. I still don't totally understand the weight feature; docs imply
# 3 and 1 means the image pane takes up an invariable 75% of content
# width on first paint, but clearly it does not.  Change this part with
# extreme caution if people already like it.)
zoom_factor = max(1, 1.0*x_nominal/(window_width * pane1_weight / (pane1_weight + pane2_weight)), 1.0*y_nominal/window_height)
if zoom_factor > 1:
    print("Scaling base image to fit window:")
    split_index = panefile.rfind('\\') + 1
    zoomfile = panefile[:split_index] + r'zoomed_' + panefile[split_index:]
    # Line drawings like this should NOT be resized with the -liquid-rescale
    # feature.
    # White space around the outside is apparently interpreted as "fat" to be
    # trimmed, distorting the outer walls, so individual coordinates (rooms)
    # end up in the wrong places even though the SUM of the distortions along
    # each axis cancels out to give the requested image size.
    zoom_command = magick_path + r' "' + panefile + r'"' + extra_magick + r' -adaptive-resize ' + str(1.0/zoom_factor*100) + r'% "' + zoomfile + r'"'
    print(zoom_command)
    subprocess.run(zoom_command)
    # Probably some scar tissue here because I added the temp markers last.
    # Instantiation used to say things like w1 = Label(image=photo), which
    # seemed functional, right up until we needed to draw on it!
    photo = PhotoImage(file=zoomfile)
else:
    photo = PhotoImage(file=panefile)
# w1 = Canvas(width = 1200, height = 1200, bg='white')
# w1.create_image(600,500,image=photo)
w1 = tkinter.Canvas(root, width=photo.width(), height=photo.height())
w2 = ScrolledText(root)
main.add(w1)
main.add(w2)
# main.add(w1, weight=3)
# main.add(w2, weight=1)
# w1.grid(row=0, column=0, sticky=NSEW)
# w2.grid(row=0, column=1, sticky=NSEW)
# If I try to peg this in the upper left, will the coordinate zooming work better?
# w1.grid(row=0, column=0, sticky=NW)
w1.grid(row=0, column=0, sticky=N)
# NS makes it automatically stretch vertically to the bottom of the map;
# avoids having to use the height parameter in defining w2, and thus
# converting characters to pixels in a font-independent way which seems
# to baffle the finest minds of reddit.
w2.grid(row=0, column=1, sticky=NS)
# more shotgun debugging, if I put two handles in the same frame will they be
# overlapping?
main.rowconfigure(0, weight=1)
main.columnconfigure(0, weight=pane1_weight)
main.columnconfigure(1, weight=pane2_weight)
w1.create_image(0, 0, anchor=tkinter.NW, image=photo)
# w1.pack(fill=tkinter.BOTH, expand=False)
w2.config(font=("Helvetica", 12, "bold"))
w2.insert(tkinter.END, coord_buffer)
w2.config(state='disabled')
# After all this... user commands!
w1.bind("<Button-1>", callback)
root.bind("<KeyPress-q>", close_window)
root.bind("<KeyPress-Q>", close_window)
root.bind("<KeyPress-d>", backspace)
root.bind("<KeyPress-D>", backspace)
root.bind("<KeyPress-l>", linestart)
root.bind("<KeyPress-L>", linestart)
root.bind("<KeyPress-p>", pathing)
root.bind("<KeyPress-P>", pathing)
root.bind("<KeyPress-r>", reuse_letter)
root.bind("<KeyPress-R>", reuse_letter)


            ########################
            ##                    ##
            ## INTERACTIVITY PART ##
            ##                    ##
            ########################

# root.after(1,w2.update())
root.mainloop()
print("Widget closed.\n")
# "prompting" final label no longer needed
if coord_buffer_list[-1][1:3] == ['','']:
    del coord_buffer_list[-1]
# re-map coords to full size base image before compositing
if zoom_factor > 1:
    coord_buffer_list = coord_inflate(coord_buffer_list, zoom_factor)


            ########################
            ##                    ##
            ## CREATE FINAL IMAGE ##
            ##                    ##
            ########################

(magick_command, sticker_list) = build_magick(coord_buffer_list, magick_path, extra_magick, dot_radius, dot_color, line_width, dash_lengths, label_font, label_size, label_color, inputfile, outputfile)
# No way of knowing whether the user has already attempted this run, so unlike the
# stickers, actually drunken-boxing around the fatal.
try:
    os.remove(outputfile)
except FileNotFoundError:
    pass
print("Creating final image:\n")
# Corner case: no dots added but ImageMagick still alters image somehow.
# Don't do that, sounds lossy.
if len(coord_buffer_list) == 0:
    shutil.copy2(inputfile, outputfile)
else:
    print(magick_command)
    subprocess.run(magick_command)
# Documentation claims all compositing functions delete source images after
# saving destination file, but this did not.  An argument could be made for
# retaining them in a temp directory or whatnot, for debugging or downstream
# image editing.
if zoom_factor > 1:
    os.remove(zoomfile)
for ff in sticker_list:
    os.remove(ff + r'.png')

# Debug step, conceivably might need to be exhumed if
# a major functionality change happens.  -output argument in this
# situation should be a text file, not an image.
# coord_buffer = "\n".join(coord_buffer_list) + "\n"
# f_coords = open(outputfile, 'w')
# f_coords.write(coord_buffer)
# f_coords.close()

