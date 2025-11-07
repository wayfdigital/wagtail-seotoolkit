from wagtail.admin.ui.side_panels import ChecksSidePanel

from wagtail_seotoolkit.core.ui.side_panels import CustomChecksSidePanel


def get_side_panels(self):
    side_panels = self.get_side_panels_og()

    for index, side_panel in enumerate(side_panels):
        if isinstance(side_panel, ChecksSidePanel):
            side_panels[index] = CustomChecksSidePanel(
                self.page,
                self.request,
            )

    return side_panels
