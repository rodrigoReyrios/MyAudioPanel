#import the AudioUtils module
import AudioUtils as AU
import pygame
import subprocess
from pygame import mixer, _sdl2 as sdl2
import atexit

class Game:
    def __init__(self,AudMan):
        '''
        Sets up properties of the pygame.
        Initalizes pygame then defines the screen, then sets 
        boolean variables used in controll sequence
        '''
        #set the AudioManager as a property
        self.AU = AudMan
        #initalize pygame
        pygame.init()
        #initalize font module
        pygame.font.init()
        #boolean to controll the game running
        self.running = True

        #some display params for the pygame window
        BLACK = (0,0,0)
        WIDTH = 1280/2
        HEIGHT = 1024/2

        #actualy make the screen
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT), 0, 32)
        self.screen.fill(BLACK)

    def EventCheck(self):
        '''
        Defines the event checking loop over pygame events.
        Loops over all events, uses boolean controls defined in
        self.__init__ to check wheather or not something is done.
        '''
        #loop over pygame events
        for event in pygame.event.get():
            #keydown event
            if event.type == pygame.KEYDOWN:
                #escape key
                if event.key == pygame.K_ESCAPE:
                    #unload devices made by the audio manager
                    self.AU.unloadDevices()
                    #designate the gameloop to end
                    self.running = False
                #[q]
                if event.key == pygame.K_q:
                    #play a sound on the mixer
                    mixer.music.play()

    def Drawing(self):
        pass


    def GameLoop(self):
        '''
        Defines the GameLoop, uses class methods.
        sets time delta, then checks for events, then draws, then flips display.
        '''
        #the game loop is defined by the running property
        while self.running:
            #check for events
            self.EventCheck()
            #draw any screen elements
            self.Drawing()
            #flip the display
            pygame.display.flip()
        #once were not in the maingame loop quit pygame
        pygame.quit()


if __name__ == "__main__":
    #make an audio manager
    VMM = AU.AudioManager()
    #load up a real device
    VMM.AddDevice("RealMic")
    #make a spotify dummy output
    VMM.MakeVplayer("virt-player")
    #make a virtual mic
    VMM.MakeVmic("virt-mic")
    #make an interface
    VMM.MakeInterface("virt-comb")
    #connect the RealMic->virt-comb
    VMM.pwlink("RealMic", "virt-comb")
    #connect the virt-player -> realmic
    VMM.pwlink("virt-player", "RealMic")
    #link the player to combined interface
    VMM.pwlink("virt-player", "virt-comb")
    #link the combined interface to the virtual mic
    VMM.pwlink("virt-comb", "virt-mic")
    #use pygame to start a mixer at the virtual player
    VMM.pygameControll("virt-player")
    #load a sound onto the mixer
    mixer.music.load("Samples/studio-kik.wav")

    #make UI with pygame
    UI = Game(VMM)
    #make the pygame gameloop run
    #The Game class auto sets up the game loop and maps
    #[Esc] to quit pygame and [q] to play the loaded sound
    UI.GameLoop()