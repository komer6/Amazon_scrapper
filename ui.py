# Import necessary Kivy UI components and utilities
from kivy.uix.image import Image            # To display the rotating spinner image
from kivy.uix.label import Label            # To show text labels (e.g., title and status)
from kivy.uix.progressbar import ProgressBar  # To show scraping progress
from kivy.uix.boxlayout import BoxLayout    # Layout to stack widgets vertically
from kivy.uix.anchorlayout import AnchorLayout  # Layout to anchor spinner in the center
from kivy.clock import Clock                # Used to schedule regular rotation updates
from kivy.graphics import PushMatrix, PopMatrix, Rotate  # Graphics instructions to rotate images

class Spinner(Image):
    """
    A custom Image widget that continuously rotates to act as a loading spinner.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 0                # Initial rotation angle
        self.rotate_active = True     # Control flag to start/stop spinning

        # Add canvas instructions to allow rotation
        with self.canvas.before:
            PushMatrix()              # Save the current drawing matrix
            self.rot = Rotate(origin=self.center, angle=self.angle)  # Rotation object
        with self.canvas.after:
            PopMatrix()               # Restore the original drawing matrix

        # Update rotation center when widget position/size changes
        self.bind(pos=self.update_origin, size=self.update_origin)

        # Schedule the spinner to rotate every 0.05 seconds
        Clock.schedule_interval(self.rotate_spinner, 0.05)

    def update_origin(self, *args):
        """
        Update the origin (center) of the rotation whenever size/position changes.
        """
        self.rot.origin = self.center

    def rotate_spinner(self, dt):
        """
        Continuously rotate the spinner image while rotate_active is True.
        """
        if self.rotate_active:
            self.angle -= 2  # Rotate counterclockwise by 2 degrees
            self.rot.angle = self.angle % 360  # Keep angle within 0-359 degrees

    def stop_rotation(self):
        """
        Stop the rotation of the spinner.
        """
        self.rotate_active = False

def build_ui():
    """
    Create and return the complete Kivy user interface.

    Returns:
        tuple: (layout, label, progress_bar, spinner) for use in the main app
    """
    # Create the main vertical layout with spacing and padding
    layout = BoxLayout(orientation='vertical', spacing=20, padding=30)

    # Create a container to center the spinner
    spinner_container = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1, 0.3))
    
    # Create the rotating spinner image
    spinner = Spinner(source="spinner.png", size_hint=(None, None), size=(400, 400))
    
    # Add the spinner to its container
    spinner_container.add_widget(spinner)
    
    # Add the container to the main layout
    layout.add_widget(spinner_container)

    # Add the application title
    title_label = Label(text="Amazon Scraper", font_size=28, size_hint_y=None, height=40)
    layout.add_widget(title_label)

    # Add the scraping status label (dynamically updated later)
    label = Label(text="Starting scrape...", font_size=42, size_hint_y=None, height=60)
    layout.add_widget(label)

    # Add a progress bar with a maximum of 50 products
    progress = ProgressBar(max=50, size_hint_y=None, height=30)
    layout.add_widget(progress)

    # Return all necessary widget references for control in the main app
    return layout, label, progress, spinner
