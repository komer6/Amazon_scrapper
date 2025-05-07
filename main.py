import threading  # Used to run the scraper in a background thread
from kivy.app import App  # Base class for creating Kivy applications
from kivy.uix.boxlayout import BoxLayout  # Layout that arranges children in a vertical or horizontal box
from kivy.uix.anchorlayout import AnchorLayout  # Layout that anchors children in a corner or center
from kivy.uix.label import Label  # Displays text
from kivy.uix.progressbar import ProgressBar  # Horizontal bar to indicate progress
from kivy.uix.image import Image  # Displays an image
from kivy.clock import Clock  # Kivy’s scheduling utility
from kivy.graphics import PushMatrix, PopMatrix, Rotate  # Used for rotating the spinner

from scraper import Scraper  # Custom class handling scraping logic


class Spinner(Image):
    """
    A rotating image used to indicate loading (a spinner).
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 0  # Rotation angle
        self.rotate_active = True  # Flag to control rotation

        # Add rotation transformation to the canvas
        with self.canvas.before:
            PushMatrix()
            self.rot = Rotate(origin=self.center, angle=self.angle)  # Rotate around center
        with self.canvas.after:
            PopMatrix()

        # Update the rotation origin when the widget position or size changes
        self.bind(pos=self.update_origin, size=self.update_origin)

        # Schedule the spinner to rotate continuously every 0.05 seconds
        Clock.schedule_interval(self.rotate_spinner, 0.05)

    def update_origin(self, *args):
        """Update rotation origin based on the widget's center."""
        self.rot.origin = self.center

    def rotate_spinner(self, dt):
        """Continuously rotate the spinner if active."""
        if self.rotate_active:
            self.angle -= 2  # Rotate counterclockwise
            self.rot.angle = self.angle % 360  # Keep angle between 0-359

    def stop_rotation(self):
        """Stop the spinner from rotating."""
        self.rotate_active = False


class ScraperApp(App):
    """
    The main Kivy application that builds the UI and runs the scraping logic.
    """

    def build(self):
        """
        Set up the UI components and start the scraping process in a background thread.
        """
        self.layout = BoxLayout(orientation='vertical', spacing=20, padding=30)

        # Spinner (rotating loading icon)
        spinner_container = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1, 0.3))
        self.spinner = Spinner(source="spinner.png", size_hint=(None, None), size=(400, 400))
        spinner_container.add_widget(self.spinner)
        self.layout.add_widget(spinner_container)

        # App title label
        self.title_label = Label(text="Amazon Scraper", font_size=28, size_hint_y=None, height=40)
        self.layout.add_widget(self.title_label)

        # Status label showing scraping progress
        self.label = Label(text="Starting scrape...", font_size=42, size_hint_y=None, height=60)
        self.layout.add_widget(self.label)

        # Progress bar (shows how many products are scraped out of 50)
        self.progress = ProgressBar(max=50, size_hint_y=None, height=30)
        self.layout.add_widget(self.progress)

        # Initialize and start the scraper in a separate thread to prevent UI blocking
        self.scraper = Scraper(self.update_progress)
        threading.Thread(target=self.scraper.begin_scraping_process, daemon=True).start()

        return self.layout

    def update_progress(self, count, message="Scraping..."):
        """
        Callback method that updates the UI with scraping progress.

        :param count: Current number of products scraped
        :param message: Message to display in the label
        """
        self.progress.value = count
        self.label.text = f"{message} ({count}/50 products)"
        
        # Stop spinner when done
        if count >= 50:
            self.spinner.stop_rotation()


if __name__ == "__main__":
    # Run the Kivy application
    ScraperApp().run()
