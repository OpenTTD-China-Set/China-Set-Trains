# China Set: Trains README

1. General Information
2. Building
3. Credits
4. License

## 1. General Information

China Set: Trains is the train sector of the China set of OpenTTD.
China Set: Trains is licensed under GPL v2.

Everything in this set is Mainland China rolling stock, in addition of
several wagon types from international/interregional connections.

Locomotives and multiple units featuring refitting are for liveries.

The default setting should be build year livery, which means that
locomotive, multiple unit or coach will remain on the livery scheme as
built. Another option is to manually choose a livery from liveries
already introduced.

Wagon refitting behaves as in normal OpenTTD, there is cargo-specific
graphics on major part of wagons.

List of available parameters:
  Loading speed: change wagon loading speed; default to be Normal.
  Purchase cost: change purchase cost; default to be 25%.
  Running cost: change running cost; default to be 25%.
  Cargo age period: change the rate cargo gets aged; default to be 100%.
  Cargo age period for freight wagons: change the rate cargo in mail and freight wagons gets aged; independent from the parameter above; default to be 100%.
  25-Series coaches built after 2014 default to be green: change whether the Type 25 Series Coaches purchased after 2014 default to be olive green. In reality, before 2014, they had different colours. Default to be Yes.

## 2. Building

The source is available on [GitHub](https://github.com/OpenTTD-China-Set/China-Set-Trains). These tools are required to build the GRF:

- nml
- make
- gcc
- gorender, or renderobject

You would need to render all models first, then you can build the GRF.

> [!NOTE]
> The first build will be slow since all models have to be rendered, which is a slow process.
> You can use `make -j n` to speed up the process by running multiple tasks at once where `n` is the task limit.

Using Linux or WSL:

```bash
#!/bin/bash
# you'll have to install gorender from https://github.com/mattkimber/gorender
# here we use apt for demo

# dependencies
sudo apt install python3
sudo apt install python3-pip
sudo apt install make
pip3 install nml
# we would also need gcc, but that should be already included in most distros

# compiling
make
# alternatively, you could use "make -j n" where n is the total number of parallel tasks you want to run at once.
```

Using Windows (Scoop is advised here, but non-scoop compilations are also possible):

```powershell
# we suggest you to use scoop; you can get scoop @ https://scoop.sh

# dependencies
scoop bucket add main
scoop bucket add openttd https://github.com/WenSimEHRP/OpenTTD-Bucket
scoop install python
scoop install make
scoop install openttd/nml
scoop install openttd/gorender
# we would need the gcc compiler in from mingw
scoop install mingw

# compiling
make
# alternatively, you could use "make -j n" where n is the total number of parallel tasks you want to run at once.
```

## 3. Credits

Contributors (in alphabetical order):

- Ahyangyi
- babel
- ctx
- DF43110
- EMB190
- FJZer0ich
- Haiyan
- huanfeng
- John Franklin
- Mikhail
- NACHN
- nengyeqing
- shentie106
- WenSim
- wuwu (kaitokiwa)

Thanks to:

- andythenorth
- Belaja Lilija
- dP
- Emperor Jake
- Garlic_Bread42
- KeepinItRail
- peter1138
- planetmaker
- Simo333
- Timberwolf
- 2cc Trainset Team
- Finnish Trainset Team
- JP+ Team
- xUSSR Team

Special thanks to everyone whom thanks is due;
Patch Pack Developers, especially JGR;
OpenTTD Developers; and Chris Sawyer.

## 4. License

China Set: Trains

Copyright (C) 2024 China Set Team

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
