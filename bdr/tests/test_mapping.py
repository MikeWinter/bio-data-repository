import datetime
import re

IDENTIFIER_RE = re.compile(r"^[\w:.-]+$")
# sources = ("UniProtKB-ID", "Entrez-GeneID", "RefSeq", "GI", "PDB", "GO", "UniRef100", "UniRef90",
#            "UniRef50", "UniParc", "PIR", "NCBI-taxon", "MIM", "UniGene", "PubMed", "EMBL", "EMBL-CDS", "Ensembl",
#            "Ensembl-TRS", "Ensembl-PRO", "PubMed-Additional")
sources = {"BioGrid", "EMBL", "EMBL-CDS", "Ensembl", "Ensembl_PRO", "Ensembl_TRS", "GI", "GeneID", "MIM", "MINT",
           "NCBI_TaxID", "PDB", "RefSeq", "UniGene", "UniParc", "UniProtKB-ID", "UniRef100", "UniRef50", "UniRef90"}


class Timer(object):
    def __init__(self):
        self.__start = None
        self.__end = None

    @property
    def delta(self):
        delta = self.__end - self.__start
        return delta.total_seconds()

    def __enter__(self):
        self.__start = datetime.datetime.now()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__end = datetime.datetime.now()


def build_mappings(records):
    from bdr.models.base import Mapping

    # Mapping.objects.all().delete()

    for record in records:
        accession_number, source, alias = record

        if source not in sources:
            continue

        Mapping.objects.get_or_create(alias=alias, source=source, accession_number=accession_number)

        # instance, created = Mapping.objects.get_or_create(alias=alias, source=source,
        #                                                   defaults=dict(accession_numbers=accession_number))
        # if not created and accession_number not in instance.accession_numbers.split("|"):
        #     instance.accession_numbers = instance.accession_numbers + "|" + accession_number
        #     instance.save()

        # identifier, alias_list = record[0], record[1:]
        #
        # for index, aliases in enumerate(alias_list):
        #     if index == 20:
        #         continue
        #     for alias in aliases.split("; "):
        #         if alias:
        #             instance, created = Mapping.objects.get_or_create(alias=alias, source=index,
        #                                                               defaults=dict(accession_numbers=identifier))
        #             if not created and identifier not in instance.accession_numbers.split("|"):
        #                 instance.accession_numbers = instance.accession_numbers + "|" + identifier
        #                 instance.save()

                        # raise ValueError("The alias {0:s} from {1:s} to {2:s} already exists:"
                        #                  " {0:s} is mapped to {3:s}".format(alias, sources[index], identifier,
                        #                                                     instance.accession_numbers))

                    # from django.db.utils import IntegrityError
                    # try:
                    #     Mapping.objects.create(alias=alias, source=index, accession_numbers=identifier)
                    # except IntegrityError:
                    #     existing = Mapping.objects.get(alias=alias, source=index).accession_numbers
                    #     print "The alias {0:s} from {1:s} to {2:s} already exists:" \
                    #           " {0:s} is mapped to {3:s}".format(alias, sources[index], identifier, existing)
                    #     raise


if __name__ == "__main__":
    import csv
    import io
    import os

    os.environ["DJANGO_SETTINGS_MODULE"] = "repository.settings"
    fp = io.open("/Users/Michael/Downloads/HUMAN_9606_idmapping.dat", "rb")
    records = csv.reader(fp, delimiter="\t")
    with Timer() as timer:
        build_mappings(records)
    print "Parsing took {:f} seconds.".format(timer.delta)
