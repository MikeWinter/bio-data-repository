from .views import Drugbank43RevisionExportView

views = {
    "export": Drugbank43RevisionExportView.as_view()
}
