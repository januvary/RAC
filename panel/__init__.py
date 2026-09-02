"""
Management panel — standalone, serverless web dashboard.

The panel is decoupled from the RAC operator app: it depends only on the
aggregator reader (``aggregator.reader``) and the rendering layer
(``panel.render``).  ``render`` turns aggregated stats into a single
self-contained HTML file; ``__main__`` builds that file by reading unit
databases directly.
"""
