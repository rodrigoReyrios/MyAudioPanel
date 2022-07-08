#import pygame audio modules
from pygame import mixer, _sdl2 as sdl2
import subprocess
import os
from pathlib import Path
import copy
import atexit
import curses
import pygame
import inquirer

#simple set list diffrence function
listdiff = lambda x,y: list(set(x) - set(y))

class AudioDevice:
    """
    Simple Super Class for how I juggle audio devices, really just has a name parameter, a parameter for input/output channels, 
    and a simple method that wraps pactl commands.
    """
    def __init__(self,name):
        """
        Sets the user decided name of the audio device and preps an attribute to store the pactl id

        Args:
            name - string that refers to the Audio device
        Returns:
            N/A
        Raises:
            N/A
        """
        #any audio device needs a name
        self.name = name
        #an audio device wont have a pactl id until its made
        self.pactl_id = None
        #spits for inputs and outputs as known by pipewire
        self.ins = None
        self.outs = None

    def pactlMake(self,mediaclass,channelmap):
        """
        Makes the audio device by wrapping pactl, has options for what media device and how 
        we wanna make the channel map. Also tries and detects what input/output ports are associated with this
        device.
        Args:
            mediaclass - string that goes into the mediaclass argument of pactl
            channelmap - string that goes into the channelmap argument of pactl
        Returns:
            N/A
        Raises:
            N/A
        """

        #get the list of current pipewire i/o
        inspre = PipewireGetPorts(False)
        outspre = PipewireGetPorts(True)

        #I need to run the appropriate command and save the output
        cmd = ["pactl","load-module","module-null-sink",f"media.class={mediaclass}",f"sink_name={self.name}",f"channel_map={channelmap}"]
        VmicCall = subprocess.run(cmd,stdout=subprocess.PIPE,text=True)
        #save the pactl id
        self.pactl_id = int(VmicCall.stdout)

        #get the list of inputs and outputs after making the device
        inspost = PipewireGetPorts(False)
        outspost = PipewireGetPorts(True)

        #get the diffrence in devices
        inscand = listdiff(inspost,inspre)
        outscand = listdiff(outspost,outspre)
        self.ins = inscand
        self.outs = outscand

class Vmic(AudioDevice):
    """
    class that keeps track of details as they pertain to Virtual mic.
    """
    def __init__(self,name,channelmap="front-left,front-right"):
        """
        constructor that sets the name of the Vmic and uses pactl to actualy make the device.

        Args:
            name - string that refers to the virtual Mic
            chennelmap="front-left,front-right" - gets passed into the channelmap= of the pactl command.
        Returns:
            N/A
        Raises:
            N/A
        """
        #set the properties of the super class
        super().__init__(name)

        #once an instance of the Vmic is declared actually make the device using pactl
        #in pipewire mic = source so i need to use the Audio/Source/Virtual media class
        #will be made with FL and FR channel map
        self.pactlMake("Audio/Source/Virtual",channelmap)

class Vplayer(AudioDevice):
    """
    class that keeps track of details as they pertain to Virtual players.
    """
    def __init__(self, name, channelmap="sterio"):
        """
        constructor that sets the name of the Vplayer and uses pactl to actualy make the device.

        Args:
            name - string that refers to the virtual Mic
            chennelmap="sterio" - gets passed into the channelmap= of the pactl command.
        Returns:
            N/A
        Raises:
            N/A
        """
        #set the properties of the super class
        super().__init__(name)
        #in pipewire players = sinks so i need the Audio/Sink media class
        #will be made with surround-51 channel map
        self.pactlMake("Audio/Sink", channelmap)

class Interface(AudioDevice):
    def __init__(self,name,channelmap="sterio"):
        """
        constructor that sets the name of the combined source/sink interface and uses pactl to actualy make the device.

        Args:
            name - string that refers to the interface
            chennelmap="sterio" - gets passed into the channelmap= of the pactl command.
        Returns:
            N/A
        Raises:
            N/A
        """
        super().__init__(name)
        self.pactlMake("Audio/Sink", channelmap)

class ExistingDevice(AudioDevice):
    def __init__(self,name):
        """
        Constructs the device and associates it to a string name. Note that since this is a existing device, an 
        instance wont have a self.pactl_id property (It technicaly does in pulseaudio but for the purposes of this module
        it wont matter).
        """
        #use the super constructor and pass in the name
        super().__init__(name)
        #usualy hear pactl can be ran but since this is an existing device this has to be more manual
        #ask user to identify the device to get the input and output ports from
        self.ins = self.SelectIO(False)
        self.outs = self.SelectIO(True)
        #note that at this point self.pactl_id is going to be None

    def SelectIO(self,io):
        """
        This method is meant to ask the user what audio ports their device is associated with
        Args:
            io - boolean that determines if the user is selecting from input ports or output ports
        Returns:
            a dictionary mapping "device name" -> [port1,port2,...]
        Raises:
            NA
        """
        #get the list of ports using pw-link -i/o
        ports = PipewireGetPorts(io)
        #try and identify which devices go to which ports
        dev_port = PipewireGetDevices(ports)

        iostring = ""
        if io:
            iostring+="Output"
        else:
            iostring+="Input"

        #use inquirer to ask user to identify the device they want
        questions = [
        inquirer.List("Device",
                        message="What Device would you like to use to get "+iostring+" Ports from?",
                        choices=dev_port.keys(),
                    )
        ]
        answer = inquirer.prompt(questions)["Device"]
        #return a list of ports
        return dev_port[answer]

class AudioManager:
    """
    Audio Manager class to handle multiple devices made by the children of the AudioDevice class.
    """
    def __init__(self):
        """
        Constructor for the AudioManager class, sets 3 empty list each meant to contain the diffrent audio devices
        Args:
            N/A
        Returns:
            N/A
        Raises:
            N/A
        """
        #initate list to keep track of devices meant to act as virtual mics, players, and interfaces
        self.Vmics = []
        self.Vplayers = []
        self.interfaces = []
        #also an additional list to keep track of existing devices
        self.ExistingDevices = []

    def MakeVmic(self,name):
        """
        Makes an instance of the Vmic and associate it to the AudioManager class via list
        Args:
            name - string name associated with the Vmic
        Returns:
            N/A
        Raises:
            N/A
        """
        #make a Vmic instance appended to the list
        self.Vmics.append(Vmic(name))

    def MakeVplayer(self,name):
        """
        Makes an instance of the Vplayer and associate it to the AudioManager class via list
        Args:
            name - string name associated with the Vplayer
        Returns:
            N/A
        Raises:
            N/A
        """
        #make a vplayer and append to the list
        self.Vplayers.append(Vplayer(name))

    def MakeInterface(self,name):
        """
        Makes an instance of the Interface and associate it to the AudioManager class via list
        Args:
            name - string name associated with the interface
        Returns:
            N/A
        Raises:
            N/A
        """
        #make an interface and add to the classes list
        self.interfaces.append(Interface(name))

    def AddDevice(self,name):
        """
        Makes an instance of an ExistingDevice and associate it to the AudioManager class via list
        Args:
            name - string name associated with the existing device
        Returns:
            N/A
        Raises:
            N/A
        """
        #make an existing device and add to the ExistingDevices list
        self.ExistingDevices.append(ExistingDevice(name))

    def resetList(self):
        """
        resets the members list of the AudioManager. Note: this command does not unload the virtual devices,
        it just makes them unknown to the AudioManager instance
        Args:
            N/A
        Returns:
            N/A
        Raises:
            N/A
        """
        self.Vmics = []
        self.Vplayers = []
        self.interfaces = []
        self.ExistingDevices = []

    def unloadDevices(self):
        """
        Unloads the pactl devices associated with this Audio Manager instance, then resets the members list.
        Args:
            N/A
        Returns:
            N/A
        Raises:
            N/A
        """
        #loop over all the devices of the three types
        for d in self.Vmics+self.Vplayers+self.interfaces:
            id = d.pactl_id
            #run the command to unload by id
            cmd = ["pactl","unload-module",f"{id}"]
            subprocess.run(cmd)

        #once all devices are unloaded just reset the lists
        self.resetList()

    def unloadAll(self):
        """
        Unloads the entire module-null-sink using pactl. This may mess up configurations with peoples audio.
        Args:
            N/A
        Returns:
            N/A
        Raises:
            N/A
        """
        #run the command to unload the entire null-sink module
        cmd = ["pactl","unload-module","module-null-sink"]
        subprocess.run(cmd)
        #reset the devices lists
        self.resetList()

    def lookfor(self,name):
        """
        Look through the devices list and tries to return the associated device class using the name. 
        Will return None if not found.
        Args:
            name - the string name used to find devices
        Returns:
            AudioDevice or None if an AudioDevice with the same string is not found
        Raises:
            N/A
        """
        #look through the Vmics, then Vplayers, then Interfaces for the thing titled 'name'
        for d in self.Vmics+self.Vplayers+self.interfaces+self.ExistingDevices:
            if d.name == name:
                return d
        return None

    def gen_pwlinkcommands(self,Outs,Ins):
        """
        Generates pactl linking commands, "pw-link #### ####" based on diffrent channel maps. Currently 
        can handle linking 1 output port to 1 input port, multiple output ports to 1 input port, and 
        1 output port to multiple input ports.
        Args:
            Outs - array of the string names associated with the Output ports
            Ins - array of string names associated with the input ports
        Returns:
            Array of arrays, each element being a command that is meant to be run by subrpocesses
        Raises:
            N/A
        """
        #count the number of ins and outs
        li = len(Ins)
        lo = len(Outs)
        #in the case that |Ins|=1 and |Outs|=1 the pwlinks are simple
        if (li==1) and (lo==1):
            #since theres only 1 in and out we can just return an array containing 1 command
            return [ ["pw-link",Outs[0],Ins[0]] ]
        #another easy case is when |Ins|=1 and |Outs|>1
        elif (li==1) and (lo>1):
            #in this case we have to loop over the input devices making a command each loop
            coms = []
            for out_dev in Outs:
                cmd = ["pw-link",out_dev,Ins[0]]
                coms.append(cmd)
            return coms
        #and a symetric case when |Ins|>1 and |Outs|=1
        elif (li>1) and (lo==1):
            coms = []
            for in_dev in Ins:
                cmd = ["pw-link",Outs[0],in_dev]
                coms.append(cmd)
            return coms
        #a case for when we have a device with FR,FL ports and another device with FL,FR ports

        #if weve caught nothing just return an empty list
        return []

    def pwlink(self,name1,name2):
        """
        runs pwlink commands by reffering to devices as their string names. Through other class methods automaicly
        generates the pw-link commands for the appropriate output/input ports.

        Args:
            name1 - the string name of the output device
            name2 - the string name of the input device
        Returns:
            N/A
        Raises:
            N/A
        """
        #look for device 1
        dev1 = self.lookfor(name1)
        dev2 = self.lookfor(name2)
        #verify that we found both devices
        if dev1 is None:
            print(f"{name1} device not found")
        elif dev2 is None:
            print(f"{name2} device not found")
        #generate the pw-link commands based on device 1's outs and device 2's ins
        coms = self.gen_pwlinkcommands(dev1.ins,dev2.outs)
        print(coms)
        for cmd in coms:
            subprocess.run(cmd)
        #now outputs from device 1 should be connected properly to the inputs of device 2

    def pygameControll(self,name):
        """
        Opens a pygame mixer at the specified device. Since pygames devices arent exatly the same as 
        how the devices are named from pactl, it tries to find a pygame device that starts with the same name
        Args:
            name - string name of the device
        Returns:
            N/A
        Raises:
            N/A
        """
        #get the devices as seen by pygame
        ins,outs = PygameGetDevices()
        #look in outs for something that starts with name
        pg_dev = None
        for ind,candidate in outs.items():
            if candidate.startswith(name):
                print(f"Pygame succesfully found {name} as {candidate}")
                pg_dev = candidate
        #if we cant find the device just dont do anything
        if pg_dev is None:
            print(f"Pygame unable to find {name} in outputs")
            return None
        #initalize the mixer at the found device
        mixer.init(devicename=pg_dev)

def PygameGetDevices():
    """
    Uses pygames mixer _sdl2 capacities to list input and output names for devices

    Args:
        NA
    
    Returns:
        input_dict, output_dict : a pair of dictionaries each mapping an integer to the respected device name

    Raises:
        NA
    """
    #start a mixer
    mixer.init()
    #get the devices
    inputs = sdl2.get_audio_device_names(True)
    outputs = sdl2.get_audio_device_names(False)
    #make dictionaries to avoid the need for having to use string names
    inputs_dict = {i:inputs[i] for i in range(len(inputs))}
    outputs_dict = {i:outputs[i] for i in range(len(outputs))}
    #return both dictionaries
    mixer.quit()
    return inputs_dict,outputs_dict

def PipewireGetPorts(io):
    """
    Gets pipewire (input or output) ports by using the pw-link -i/-o command.
    Args:
        io - boolean, True lists the -i ports and False lists the -o ports
    Returns:
        devlist - a list of port names
    Raises:
        N/A
    """
    #make arg either the -i or -o flag
    arg = ""
    if io:
        arg += "-i"
    elif not io:
        arg += "-o"
    #run the following command to get the devices of corresponding inpu or output
    cmd = ["pw-link",arg]
    devlist = subprocess.run(cmd,stdout=subprocess.PIPE,text=True).stdout
    #trim the last \n character at the end if there is one
    if devlist[-1]=='\n':
        devlist = devlist[0:-1]
    #split by the \n characters
    devlist = devlist.split("\n")
    return devlist

def PipewireGetDevices(devlist):
    """
    Tries to identify devices (not ports) by looking at a list of ports (idealy from PipeWireGetPorts).
    This is done by splitting a port name into 'device':'port'.
    Args:
        devlist - a dictionary that maps a device to the according ports
    Returns:
        A list of unique device list
    Raises:
        N/A
    """
    devices_ports = {}
    for fullport in devlist:
        #use rpartition to seperate into [device,':',port]
        dev,_,port = fullport.rpartition(':')
        #see if dev is already a key in devices_no_ports dictionary
        if dev not in devices_ports.keys():
            #if the dev is novel add the dev as a key mapping to a list with the full port name
            devices_ports[dev] = [fullport]
        else:
            #when the dev is a key add the full port name in the value list
            devices_ports[dev].append(fullport)
        
    return devices_ports
