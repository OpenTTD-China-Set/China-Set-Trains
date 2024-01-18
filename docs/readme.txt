China Set: Trains README
===============================

----------
0 Contents
----------

1   About
2   General information
    2.1  Requirements
    2.2  Installation
    2.3  Parameter settings
    2.4  Usage
3   Known issues
4   Background information
5   Frequently Asked Questions
6   Credits
7   Contact information
    7.1  Bug reports
    7.2  Other problems
    7.3  General enquiries
8   License
9   Obtaining the source


-------
1 About
-------

China Set: Trains is the train sector of the China set of OpenTTD.
It is developed by China Set Team, which can be found in Part 6.


---------------------
2 General information
---------------------

2.1 Requirements
----------------
- OpenTTD 1.4.0-beta1 or nightly r26157, or higher
- Not compatible with TTDPatch


2.2 Installation
----------------
OpenTTD:
  see http://wiki.openttd.org/NewGRF
  This NewGRF is available from the ingame Online Content.


2.3 Parameter settings
----------------------

Purchase and running costs can be defined using NewGRF parametres.
Default parametres are:

Purchase cost setting: 25%
Running cost setting: 25%

Cargo age period, which affects the devaluing of cargo as time goes,
can be extended using NewGRF parametres. Default is "Standard".
"Low" is "Standard" doubled, while "Very Low" is "Low" Doubled. Even
in "Standard" mode, cargo age period varies depending on wagon types.


2.4 Usage
---------
Everything in this set is Mainland China rolling stock, in addition of 
several wagon types from international connections.

Locomotives and multiple units featuring refitting are for deciding the
speed and traction effort suitable for freight or passenger operations
and/or livery refitting.

When livery refitting is available, the default setting is
year-dependent livery. That means when the livery is scheduled be
changed between specific years, locomotive, multiple unit or coach will
automatically update to the next livery.

The next option is build year livery, which means that locomotive,
multiple unit or coach will remain on the livery scheme as built. It
overrides the automatic update of livery, enabling former livery being
usable on the time when it's not otherwise available anymore.

The third option is to manually choose a livery from liveries already
introduced.

Speed and traction effort can be choosed at the same time (if locomotive
or multiple unit has one) with year-dependent, build year or manual
livery.

Wagon refitting behaves as in normal OpenTTD, there is cargo-specific
graphics on major part of wagons.

--------------
3 Known issues
--------------

Some wagons will appear too "tubeous" on consist. If you do notice too
tubeous wagons on consist, please report them to the China Set Dev Team.



------------------------
4 Background information
------------------------

Information regarding rolling stock is provided from realiable sources.
Errors may exist, do report them when encountered.


----------------------------
5 Frequently Asked Questions
----------------------------

Q: Why can't I use this in older versions of OpenTTD or TTDPatch?
A: This NewGRF uses some features only available to OpenTTD r26157 and
   newer. Furthermore, the most recent version of NML used to build this
   NewGRF, produces GRF version 8. This is only supported by OpenTTD
   r23166 and newer anyways.



---------
6 Credits
---------

Founder:
- John Franklin

Project leading and management:
- John Franklin
- Ahyangyi
- babel
- NACHN
- wuwu (kaitokiwa)

Information basis:
- NACHN
- wuwu (kaitokiwa)
- babel
- huanfeng
- nengyeqing
- Mikhail
- Haiyan
- FJZer0ich

Graphics (see \docs\voxelsource.txt for details):
- NACHN
- FJZer0ich
- babel 
- John Franklin
- Mikhail
- wuwu (kaitokiwa)
- ctx
- shentie106
- Haiyan
- EMB190

Code:
- John Franklin, NML-based Coding
- Ahyangyi, Co-operator
- wuwu (kaitokiwa), Co-operator

Translations:
- 

GoRender Tools:
- Timberwolf (Matt Kimber)

Makefile system (not by China Set Team):
- planetmaker (Ingo von Borstel)

Code Reference:
- Timberwolf (Matt Kimber)
- Finnish Trainset Team
- JP+ Team
  - KeepinItRail for JP+ Shinkansen
- 2cc Trainset Team
- xUSSR Team

Helpers on Discord:
- andythenorth
- Emperor Jake
- Belaja Lilija
- Simo333
- Garlic_Bread42
- and more...

Special thanks to:

Everyone whom thanks is due;

Patch Pack Developers, especially JGR;

OpenTTD Developers;

Chris Sawyer.


---------------------
7 Contact information
---------------------

7.1 Bug reports
---------------
Please report any bugs you find at
  bug tracker: https://github.com/JohnFranklin523/China-Set-Trains
  or forum topic: http://www.tt-forums.net/viewtopic.php?t=91092

Always included a detailed description of the bug, preferrably with
screenshot and savegame. Also state the exact game version you're using,
as well as the version of this NewGRF.

If you have a savegame that includes NewGRFs not available on OpenTTD's
Online Content, then please try to reproduce the bug in a new game
which has all NewGRFs easily accessible.

If you're using a patched version of the game, please try to reproduce
the bug on an official game build. If you can't reproduce the bug, then
don't report it here but in the forum topic of the patch(pack) instead.


7.2 Other problems
------------------
If you have any problems using this NewGRF that are not covered in the
Frequently Asked Questions above, then you can ask your questions in the
forum topic: https://www.tt-forums.net/viewtopic.php?t=91092


7.3 General enquiries
---------------------

If you have any queries that cannot be asked in the forum topic, then
contact John Franklin (JohnFranklin523) via Private Message at 
www.tt-forums.net.



---------
8 License
---------

China Set: Trains
Copyright (C) 2023 China Set Team

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, please check
https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html



----------------------
9 Obtaining the source
----------------------

The source code can be obtained from GitHub.

1. Install WSL (if you are on Windows)
2. sudo apt install python3;
3. sudo apt install python3-pip;
4. sudo apt install make;
5. pip3 install nml;
6. Unzip China-Set-Trains folder downloaded;
7. Shift-right-click (if you are on Windows) the China-Set-Trains folder;
8. Click "Open Linux Shell";
9. type "make";
10. Compile success.