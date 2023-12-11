import pyautogui
import win32gui
import cv2
import pydirectinput
import time
#from AppOpener import open


class Client:
    
    def __init__(self, handle=None):
        pydirectinput.PAUSE = 0.01
        self._handle = handle

    def register_window(self, name="Discord", nth=0):
        """ Assigns the instance to a window (Required before using any other API functions) """
        def win_enum_callback(handle, param):
            
            if str(win32gui.GetWindowText(handle)).find(name) != -1:
                param.append(handle)
                return handle

        handles = []
        # Get all windows with the name
        win32gui.EnumWindows(win_enum_callback, handles)
        
        handles.sort()
        # Assigns the one at index nth
        self._handle = handles[nth]
        
        return self


    def match_image(self, largeImg, smallImg, threshold=0.2, debug=False):
        """ Finds smallImg in largeImg using template matching """
        """ Adjust threshold for the precision of the match (between 0 and 1, the lowest being more precise """
        """ Returns false if no match was found with the given threshold """
        method = cv2.TM_SQDIFF_NORMED

        # Read the images from the file
        small_image = cv2.imread(smallImg)
        large_image = cv2.imread(largeImg)
        h, w = small_image.shape[:-1]

        result = cv2.matchTemplate(small_image, large_image, method)

        # We want the minimum squared difference
        mn, _, mnLoc, _ = cv2.minMaxLoc(result)

        if (mn >= threshold):
            return False

        # Extract the coordinates of our best match
        x, y = mnLoc

        if debug:
            # Draw the rectangle:
            # Get the size of the template. This is the same size as the match.
            trows, tcols = small_image.shape[:2]

            # Draw the rectangle on large_image
            cv2.rectangle(large_image, (x, y),
                            (x+tcols, y+trows), (0, 0, 255), 2)

            # Display the original image with the rectangle around the match.
            cv2.imshow('output', large_image)

            # The image is only displayed if we call this
            cv2.waitKey(0)

        # Return coordinates to center of match
        return (x + (w * 0.5), y + (h * 0.5))   #return (x + (w * 0.5), y + (h * 0.5))

    def set_active(self):
        """ Sets the window to active if it isn't already """
        if not self.is_active():
            """ Press alt before and after to prevent a nasty bug """
            pyautogui.press('alt')
            win32gui.SetForegroundWindow(self._handle)
            pyautogui.press('alt')
        return self

    def is_active(self):
        """ Returns true if the window is focused """
        return self._handle == win32gui.GetForegroundWindow()
    
    def check_discord(self):
      pyautogui.screenshot("discord.png", region=(1112,1850,500,75))
      if self.match_image("discord.png","discord commands/kill code.png",0.1):
         self.text("killing code...")
         return "kill"
      elif self.match_image("discord.png","discord commands/ping.png",0.1):
          self.text("i am still running")
          return "ping"
      elif self.match_image("discord.png","discord commands/commands.png",0.12):
          self.text("commands are stop, ping, commands, and refresh")
          self.text("choose a command")
          return "help"
      elif self.match_image("discord.png","discord commands/refresh.png",0.12):
          self.text("resetting stocks")
          return "refresh"
     
    def text(self,message):
        for x in message:
            pydirectinput.press(x)
        pydirectinput.press('enter')
        time.sleep(1)
