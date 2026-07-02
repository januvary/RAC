"""
Management panel — standalone, serverless web dashboard.

The panel is decoupled from the RAC operator app: it depends only on the pure
data core (``src.sync``, ``src.models``, ``src.constants``) and never on
``src.gui``. ``render`` turns merged stats into a single self-contained HTML
file; ``__main__`` builds that file from the local database.
"""
