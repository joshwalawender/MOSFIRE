# Instrument Scripting Overview

I think of instrument control in a 4 tiered structure.  For this I’m neglecting everything below the keyword level, there’s obviously additional complexity down there.

#### 1) Keywords

At the lowest level we have keywords.  They are sometimes cryptic in naming and behavior, but offer a solid foundation.

#### 2) Instrument Functions

Instrument “functions" wrap keywords and other simple tools (e.g. ping) and provide a python interface to all instrument actions.  Examples would be something like the current `outdir`, `observer`, or one of the variations on the `exptime` scripts.

In many cases these functions just set a single keyword value, but the utility in building this layer is two fold.  First, we create a python interface which replaces the sometimes cryptic keyword names with more human readable names (and aliases if we want to maintain older naming conventions).  Second, we implement pre- and post- conditions for all functions.  These conditions effectively state our assumptions about the instrument state before and after we issue a command.

This layer would also allow us to standardize behavior between instruments.  Something as simple as the units and name for exptime being consistent across all instruments would be a nice improvement.

#### 3) Instrument Scripts

Instrument “scripts” wrap functions and keyword calls.  There’s a big gray area between scripts and functions, it’s really a continuum, but I see scripts as being more complex structures calling multiple functions or keywords.  Scripts would also possibly call data analysis tools.  For example, a checkout MOSFIRE script would be a complex piece of software which calls many smaller functions and would likely include image analysis.  Something containing image analysis would almost certainly be a script and not a function.

#### 4) GUIs

Instrument GUIs would be the most complex level simply because they are non-linear (asynchronous).  All operations of a GUI should be built out of lower level tools so that no sequencing or logic is built in to the GUI itself.


# Open Questions

1. Does there need to be a distinction between Instrument Functions (#2 above) and Instrument Scripts (#3) or is that merely confusing the landscape?

1. How do we organize code?  I started a draft which was a single package which could cover all instruments.  Each instrument was a sub-module (e.g. `from instruments import mosfire`).  In principle, this would allow some code sharing, but this may not be very useful in practice.

1. Object oriented vs. functional?  Luca, John P., and I did a little work on this and my current preference is functions for everything unless it clearly maps better to an object (e.g. a MOSFIRE mask is an object in my code).  To provide structure, I have drafted a template which encourages use of pre- and post-conditions.

1. How does the python code (presumably developed using git and GitHub) integrate with `kroot`?

1. How do we make the python code callable from the command line? Using `entry_points` in `setup.py`?  Putting compiled versions of the code in the path using makefiles?
