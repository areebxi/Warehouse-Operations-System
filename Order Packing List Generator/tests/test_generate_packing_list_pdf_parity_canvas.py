"""Fake reportlab canvas for packing-list PDF parity tests."""


class FakeCanvas:
    created = []

    def __init__(self, filename, pagesize=None):
        self.filename = filename
        self.pagesize = pagesize
        self.title = None
        self.pages_shown = 0
        self.saved = False
        FakeCanvas.created.append(self)

    def setTitle(self, title):
        self.title = title

    def showPage(self):
        self.pages_shown += 1

    def save(self):
        self.saved = True
