# Instrument Scripts and Checkouts

## Goals

An important goal in designing instrument scripts is to make sure that they end up as readable as possible for non-programmers (e.g. SAs and OAs).  For example, a highly abstracted structure would limit who can dive in and make contributions to the code and I think we want to be as inclusive as possible when it comes to who can make edits to these scripts.  At the same time we want to enforce some good practices, so there are tradeoffs to be made in the design.  Below is a list of a few goals:

- Code base is accessible to non-programmers, so they feel empowered to edit
- Encourage documentation (perhaps implement automatic documentation)
- Encourage pre- and post- conditions
- Share common tools wherever possible (reduce duplication of effort), especially for data analysis tasks.


## Relationship to Instrument Checkouts

Assume our intent is to have the three levels of checkout described in the slides presented in the April 7 meeting: Verification, Quick Checkout, and Full Checkout.  I won't re-hash the details here.

I am proposing that the "verification" level (the `testAll` and `ctx` equivalent) entirely reside in the alarm system (such as EMIR plus a web or other graphical interface) and that anything that needs to be in that level of checkout be converted to a keyword in order to be EMIR compatible.

The "quick checkout" scrips and "full checkout" scripts would be built using a template with the features discussed below.


## Proposed Instrument Script Architecture

I think of instrument control in a 4 tiered structure.  For this I’m neglecting everything below the keyword level, there’s obviously additional complexity down there.

#### 1) Keywords

At the lowest level we have keywords.  They are sometimes cryptic in naming and behavior, but offer a solid foundation.

#### 2) Instrument Functions

Instrument “functions" wrap keywords and other simple tools (e.g. ping) and provide a python interface to all instrument actions.  Examples would be something like the current `outdir`, `observer`, or one of the variations on the `exptime` scripts.

In many cases these functions just set a single keyword value, but the utility in building this layer includes:

1. We create a python interface which replaces the sometimes cryptic keyword names with more human readable names (and aliases if we want to maintain older naming conventions).
1. We implement pre- and post- conditions for all functions.  These conditions effectively state our assumptions about the instrument state before and after we issue a command.
1. This layer would also allow us to standardize behavior between instruments.  Something as simple as the units and name for exptime being consistent across all instruments would be a nice improvement.

Here's a realistic example to show how cryptic direct keywords can be and why I think a layer of simple functions can help.  The following pseudocode snippet is from a real script, the second does the same thing using proposed functions.

Using keywords:
```
if dwrn2lv < 25:
    utbn2fil.write('on')
```

Using proposed instrument functions:
```
if dewar_hold_time() < 3*u.hours:
    fill_dewar()
```

Note that in addition to the naming making the logic much easier to follow, we can bring the true intent forward: we're worried about hold time, not the actual level value which is a proxy for that.  In addition, we can make units clear if we want to support that feature.

#### 3) Instrument Scripts

Instrument “scripts” wrap functions and keyword calls.  There’s a big gray area between scripts and functions, it’s really a continuum, but I see scripts as being more complex structures calling multiple functions or keywords.  Scripts would also potentially call data analysis tools.  

Examples:
- A checkout script would be a complex piece of software which calls many smaller functions and would likely include image analysis.  Something containing image analysis would almost certainly be a script and not a function.
- A new script to calibrate the HIRES cross disperser could integrate image analysis in the script and close the loop in software rather than having the user go off an do IRAF analysis of each image.
- A script to measure detector characteristics could be automated to take the appropriate data, analyze it, present a report, and archive the results in a database.

#### 4) GUIs

Instrument GUIs would be the most complex level simply because they are non-linear (asynchronous).  All operations of a GUI should be built out of lower level tools so that no sequencing or logic is built in to the GUI itself.


# Detailed Design Questions

1. Does there need to be a distinction between Instrument Functions (#2 above) and Instrument Scripts (#3) or is that merely confusing the landscape?

1. How do we organize code?  I started a draft which was a single package which could cover all instruments.  Each instrument was a sub-module (e.g. `from instruments import mosfire`).  In principle, this would allow some code sharing, but this may not be very useful in practice.

1. Object oriented vs. functional?  Luca, John P., and I did a little work on this and my current preference is functions for everything unless it clearly maps better to an object (e.g. a MOSFIRE mask is an object in my code).  To provide structure, I have drafted a template which encourages use of pre- and post-conditions.

1. How does the python code (presumably developed using git and GitHub) integrate with `kroot`?

1. How do we make the python code callable from the command line? Using `entry_points` in `setup.py`?  Putting compiled versions of the code in the path using makefiles?
