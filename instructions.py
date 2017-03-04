from kivy.adapters.listadapter import ListAdapter
from kivy.app import App
from kivy.app import Widget
from kivy.core.window import Window
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.listview import ListItemButton
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

class ScrollableLabel(ScrollView):
    '''
    label widget for intructions
    '''
    text = StringProperty('')

class InstructionsScreen(Screen):
    '''
    widget for screen of instructoin. controlled by the ScreenManager
    '''
    def __init__(self, **kwargs):
        '''
        Constructor
        :param kwargs:
        '''
        super(InstructionsScreen, self).__init__(**kwargs)


    def goto_main(self):
        '''
        switches to main screen using ScreenManager
        :return:
        '''
        self.manager.current = "loginScreen"
