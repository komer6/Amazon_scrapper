from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.progressbar import ProgressBar
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.clock import Clock
from kivy.graphics import PushMatrix, PopMatrix, Rotate


class Spinner(Image):
    """
    Spinner widget that rotates to indicate loading.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.angle = 0
        self.rotate_active = True
        with self.canvas.before:
            PushMatrix()
            self.rot = Rotate(origin=self.center, angle=self.angle)
        with self.canvas.after:
            PopMatrix()
        self.bind(pos=self.update_origin, size=self.update_origin)
        Clock.schedule_interval(self.rotate_spinner, 0.05)

    def update_origin(self, *args):
        self.rot.origin = self.center

    def rotate_spinner(self, dt):
        if self.rotate_active:
            self.angle -= 2
            self.rot.angle = self.angle % 360

    def stop_rotation(self):
        self.rotate_active = False


def build_ui():
    """
    Build and return the entire Kivy layout and key widget references.

    Returns:
        tuple: (layout, label, progress_bar, spinner)
    """
    layout = BoxLayout(orientation='vertical', spacing=20, padding=30)

    # Spinner
    spinner_container = AnchorLayout(anchor_x='center', anchor_y='center', size_hint=(1, 0.3))
    spinner = Spinner(source="spinner.png", size_hint=(None, None), size=(400, 400))
    spinner_container.add_widget(spinner)
    layout.add_widget(spinner_container)

    # Title
    title_label = Label(text="Amazon Scraper", font_size=28, size_hint_y=None, height=40)
    layout.add_widget(title_label)

    # Scraping Status Label
    label = Label(text="Starting scrape...", font_size=42, size_hint_y=None, height=60)
    layout.add_widget(label)

    # Progress Bar
    progress = ProgressBar(max=50, size_hint_y=None, height=30)
    layout.add_widget(progress)

    return layout, label, progress, spinner
