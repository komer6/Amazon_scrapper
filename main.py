import threading
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics import PushMatrix, PopMatrix, Rotate

from scraper import Scraper

class Spinner(Image):
    """
    A custom Kivy Image widget that displays a continuously rotating spinner.

    This is used as a visual indicator of background activity (i.e., scraping in progress).
    """

    def __init__(self, **kwargs):
        """
        Initialize the spinner with rotation capabilities.
        """
        super().__init__(**kwargs)
        self.angle = 0                 # Initial rotation angle
        self.rotate_active = True     #  enabling/disabling rotation

        # Apply rotation instructions to the canvas
        with self.canvas.before:
            PushMatrix()              # Save the current graphics state
            self.rot = Rotate(origin=self.center, angle=self.angle)  # Initialize rotation
        with self.canvas.after:
            PopMatrix()               # Restore the original graphics state

        # Ensure rotation origin stays centered if the widget resizes or moves
        self.bind(pos=self.update_origin, size=self.update_origin)

        # Schedule periodic rotation updates (every 0.05 seconds)
        Clock.schedule_interval(self.rotate_spinner, 0.05)

    def update_origin(self, *args):
        """
        Update the rotation origin whenever the spinner's size or position changes.
        """
        self.rot.origin = self.center

    def rotate_spinner(self, dt):
        """
        Continuously rotate the spinner while `rotate_active` is True.
        """
        if self.rotate_active:
            self.angle -= 2  # Rotate counterclockwise
            self.rot.angle = self.angle % 360  # Keep angle within 0–359

    def stop_rotation(self):
        """
        Stop the rotation of the spinner.
        """
        self.rotate_active = False


class ScraperApp(App):
    """
    The main application class for the Amazon product scraper.

    This class initializes the Kivy UI, launches the background scraping process,
    and updates the UI with scraping progress.
    """

    def build(self):
        """
        Build and return the application's root widget (UI layout).
        """
        # Main vertical layout container
        self.layout = BoxLayout(orientation='vertical', spacing=20, padding=30)

        # Add rotating spinner (centered)
        spinner_container = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1, 0.3))
        self.spinner = Spinner(source="spinner.png", size_hint=(None, None), size=(400, 400))
        spinner_container.add_widget(self.spinner)
        self.layout.add_widget(spinner_container)

        # Title label for the app
        self.title_label = Label(text="Amazon Scraper", font_size=28, size_hint_y=None, height=40)
        self.layout.add_widget(self.title_label)

        # Dynamic label showing scraping progress
        self.label = Label(text="Starting scrape...", font_size=42, size_hint_y=None, height=60)
        self.layout.add_widget(self.label)

        # Progress bar with maximum of 50 items
        self.progress = ProgressBar(max=50, size_hint_y=None, height=30)
        self.layout.add_widget(self.progress)

        # Initialize scraper with callback and start scraping in a background thread
        self.scraper = Scraper(self.update_progress)
        threading.Thread(target=self.scraper.begin_scraping_process, daemon=True).start()

        return self.layout

    def update_progress(self, count, message="Scraping..."):
        """
        Update the progress bar and status label from the scraper callback.

        Args:
            count (int): Number of products scraped so far.
            message (str): Status message to display.
        """
        # Ensure UI updates occur on the main thread using Clock
        Clock.schedule_once(lambda dt: self._update_ui(count, message))

    def _update_ui(self, count, message):
        """
        Helper method to update UI components safely from the main thread.

        Args:
            count (int): Current product count.
            message (str): Status message.
        """
        self.progress.value = count
        self.label.text = f"{message} ({count}/50 products)"
        if count >= 50:
            self.spinner.stop_rotation()


# Run the Kivy application
if __name__ == "__main__":
    ScraperApp().run()
