from .parser import Reader
from .views import DrugBank43RevisionExportView

views = {
    "export": DrugBank43RevisionExportView.as_view()
}
