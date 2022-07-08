MyAudioPanel
=============

<!-- ![banner]() -->
<!-- ![badge]() -->
<!-- ![badge]() -->
This is a small python module I originally made to manage my audio devices easier. Essentially the AudioUtils module is capable of keeping track of "pactl" and "pw-link" commands to chain together virtual devices. There is also added functionality to have Pygame use these virtual devices. My use of it, as seen in Demo.py, is to combine my mic output and a virtual audio player, which is then controlled by Pygame, to make a virtual soundboard.

Inspired from [this](https://superuser.com/questions/1675877/how-to-create-a-new-pipewire-virtual-device-that-to-combines-an-real-input-and-o) StackExchange post.


Table of Contents
-----------------

-   [Setup](#setup)
-   [Usage](#usage)
-   [To-Do](#to-do)
-   [Authors and Credits](#authors&credits)


Setup
---------------

The bulk of this module is really just juggling a bunch of "pactl" commands, thus it does require a "pulseaudio" server. It also requires a working Pygame installation and uses the Inquirer library to get user input. Developed for use on a linux machine (In particular my linux machine).

Usage
-----

```python
#start an audio Manager
AU = AudioManager()
#use the audio manager to make: 
# a virtual mic
# a combined sink
AU.MakeVmic("virt-mic")
AU.MakeInterface("virt-comb")
#link virt-mic -> virt-comb
AU.pwlink("virt-mic","virt-comb")
#selecting an existing device requires some user input
AU.AddDevice("real-mic")
#link real-mic -> virt-comb
AU.pwlink("real-mic","virt-comb")
```
From here it as simple as setting your default input device as "virt-comb" in pulsemixer or something.

To-Do
-------
- [ ] Load up multiple sounds through Pygame-UI
- [ ] Use Pygame channels to play multiple sounds at once
- [ ] Look into PulseAudio documentation, some of the scripts that make and link the devices are very hacked together.

Authors&Credits
-------

* Rodrigo Rios [:email:](rodrigoreyrios@gmail.com)
* Audio Sample from [FreeSound.org](https://freesound.org/)
