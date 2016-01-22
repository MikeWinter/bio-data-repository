from io import StringIO

from django.test import TestCase

from ...formats.drugbank43.parser import Reader, Record


class ReaderTest(TestCase):
    def test_no_drugs_produces_no_records(self):
        expected_records = []
        stream = StringIO(u'<drugbank />')
        reader = Reader(stream, selected=['drug@created'])

        actual_records = list(reader)

        self.assertItemsEqual(expected_records, actual_records)

    def test_can_read_attribute_from_drug(self):
        attribute = 'drug@type', 'biotech'
        expected_records = [Record([attribute])]
        stream = StringIO(u'<drugbank>'
                          u'  <drug type="{:s}" created="2005-06-13" updated="2015-02-23" />'
                          u'</drugbank>'.format(attribute[1]))
        reader = Reader(stream, selected=[attribute[0]])

        actual_records = list(reader)

        self.assertItemsEqual(expected_records, actual_records)

    def test_can_read_attributes_from_drug(self):
        attributes = [('drug@type', 'biotech'), ('drug@created', '2005-06-13')]
        expected_records = [Record(attributes)]
        stream = StringIO(u'<drugbank>'
                          u'  <drug type="{0}" created="{1}" updated="2015-02-23" />'
                          u'</drugbank>'.format(*[value for _, value in attributes]))
        reader = Reader(stream, selected=[attribute for attribute, _ in attributes])

        actual_records = list(reader)

        self.assertItemsEqual(expected_records, actual_records)

    def test_can_read_drug_child_element_value(self):
        element = 'drug/name', 'Lepirudin'
        expected_records = [Record([element])]
        stream = StringIO(u'<drugbank>'
                          u'  <drug created="2005-06-13" updated="2015-02-23">'
                          u'    <name>{:s}</name>'
                          u'  </drug>'
                          u'</drugbank>'.format(element[1]))
        reader = Reader(stream, selected=[element[0]])

        actual_records = list(reader)

        self.assertItemsEqual(expected_records, actual_records)

    def test_can_read_repeated_drug_child_element_values(self):
        element = 'drug/drugbank-id'
        values = 'DB00001', 'BIOD00024'
        expected_records = [Record([(element, value)]) for value in values]
        stream = StringIO(u'<drugbank>'
                          u'  <drug created="2005-06-13" updated="2015-02-23">'
                          u'    <drugbank-id>{:s}</drugbank-id>'
                          u'    <drugbank-id>{:s}</drugbank-id>'
                          u'  </drug>'
                          u'</drugbank>'.format(*values))
        reader = Reader(stream, selected=[element])

        actual_records = list(reader)

        self.assertItemsEqual(expected_records, actual_records)

    def test_repeated_drug_child_elements_duplicate_siblings(self):
        persistent_element = 'drug/name'
        persistent_value = 'Lepirudin'
        repeating_element = 'drug/drugbank-id'
        repeating_values = 'DB00001', 'BIOD00024'
        expected_records = [Record([(repeating_element, value), (persistent_element, persistent_value)])
                            for value in repeating_values]
        stream = StringIO(u'<drugbank>'
                          u'  <drug created="2005-06-13" updated="2015-02-23">'
                          u'    <drugbank-id primary="true">{:s}</drugbank-id>'
                          u'    <drugbank-id>{:s}</drugbank-id>'
                          u'    <name>{name}</name>'
                          u'  </drug>'
                          u'</drugbank>'.format(*repeating_values, name=persistent_value))
        reader = Reader(stream, selected=[repeating_element, persistent_element])

        actual_records = list(reader)

        self.assertItemsEqual(expected_records, actual_records)

    def test_can_read_drug_child_element_and_attribute_values(self):
        drug_type = 'drug@type', 'biotech'
        drug_name = 'drug/name', 'Lepirudin'
        identifiers = [{'drug/drugbank-id': 'DB00001', 'drug/drugbank-id@primary': 'true'},
                       {'drug/drugbank-id': 'BIOD00024'}]
        expected_records = [Record([drug_type, drug_name] + identifier.items()) for identifier in identifiers]
        stream = StringIO(u'<drugbank>'
                          u'  <drug type="{type}" created="2005-06-13" updated="2015-02-23">'
                          u'    <drugbank-id primary="true">{[drug/drugbank-id]}</drugbank-id>'
                          u'    <drugbank-id>{[drug/drugbank-id]}</drugbank-id>'
                          u'    <name>{name}</name>'
                          u'  </drug>'
                          u'</drugbank>'.format(*identifiers, name=drug_name[1], type=drug_type[1]))
        reader = Reader(stream, selected=[drug_type[0], drug_name[0]] + identifiers[0].keys())

        actual_records = list(reader)

        self.assertItemsEqual(expected_records, actual_records)

    def test_can_read_descendant_element_values(self):
        drug_type = 'drug@type', 'biotech'
        drug_name = 'drug/name', 'Lepirudin'
        drug_group = 'drug/groups/group', 'approved'
        identifiers = [{'drug/drugbank-id': 'DB00001', 'drug/drugbank-id@primary': 'true'},
                       {'drug/drugbank-id': 'BIOD00024'}]
        expected_records = [Record([drug_type, drug_name, drug_group] + identifier.items())
                            for identifier in identifiers]
        stream = StringIO(u'<drugbank>'
                          u'  <drug type="{type}" created="2005-06-13" updated="2015-02-23">'
                          u'    <drugbank-id primary="true">{[drug/drugbank-id]}</drugbank-id>'
                          u'    <drugbank-id>{[drug/drugbank-id]}</drugbank-id>'
                          u'    <name>{name}</name>'
                          u'    <groups>'
                          u'      <group>{group}</group>'
                          u'    </groups>'
                          u'  </drug>'
                          u'</drugbank>'.format(*identifiers, name=drug_name[1], type=drug_type[1],
                                                group=drug_group[1]))
        reader = Reader(stream, selected=[drug_type[0], drug_name[0], drug_group[0]] + identifiers[0].keys())

        actual_records = list(reader)

        self.assertItemsEqual(expected_records, actual_records)

    def test_can_read_repeated_descendant_element_values(self):
        drug_type = 'drug@type', 'biotech'
        drug_name = 'drug/name', 'Lepirudin'
        drug_groups = [{'drug/groups/group': 'approved'}, {'drug/groups/group': 'nutraceutical'}]
        identifiers = [{'drug/drugbank-id': 'DB00001', 'drug/drugbank-id@primary': 'true'},
                       {'drug/drugbank-id': 'BIOD00024'}]
        expected_records = [Record([drug_type, drug_name] + identifier.items() + group.items())
                            for identifier in identifiers for group in drug_groups]
        stream = StringIO(u'<drugbank>'
                          u'  <drug type="{type}" created="2005-06-13" updated="2015-02-23">'
                          u'    <drugbank-id primary="true">{[drug/drugbank-id]}</drugbank-id>'
                          u'    <drugbank-id>{[drug/drugbank-id]}</drugbank-id>'
                          u'    <name>{name}</name>'
                          u'    <groups>'
                          u'      <group>{[drug/groups/group]}</group>'
                          u'      <group>{[drug/groups/group]}</group>'
                          u'    </groups>'
                          u'  </drug>'
                          u'</drugbank>'.format(*(identifiers + drug_groups), name=drug_name[1], type=drug_type[1]))
        reader = Reader(stream, selected=[drug_type[0], drug_name[0]] + identifiers[0].keys() + drug_groups[0].keys())

        actual_records = list(reader)

        self.assertItemsEqual(expected_records, actual_records)

    def test_cartesian_product_recurses_over_descendants(self):
        drug_type = 'drug@type', 'biotech'
        identifiers = [{'drug/drugbank-id': 'DB00001', 'drug/drugbank-id@primary': 'true'},
                       {'drug/drugbank-id': 'BIOD00024'}]
        drug_name = 'drug/name', 'Lepirudin'
        drug_groups = [{'drug/groups/group': 'approved'}, {'drug/groups/group': 'nutraceutical'}]
        pathway_name = 'drug/pathways/pathway/name', 'Lepirudin Action Pathway'
        pathway_drugs = [{'drug/pathways/pathway/drugs/drug/drugbank-id': 'DB00001',
                          'drug/pathways/pathway/drugs/drug/name': 'Lepirudin'},
                         {'drug/pathways/pathway/drugs/drug/drugbank-id': 'DB01022',
                          'drug/pathways/pathway/drugs/drug/name': 'Phylloquinone'},
                         {'drug/pathways/pathway/drugs/drug/drugbank-id': 'DB01373',
                          'drug/pathways/pathway/drugs/drug/name': 'Calcium'}]
        pathway_enzymes = [{'drug/pathways/pathway/enzymes/uniprot-id': 'P00734'},
                           {'drug/pathways/pathway/enzymes/uniprot-id': 'P00748'},
                           {'drug/pathways/pathway/enzymes/uniprot-id': 'P02452'}]
        expected_records = [Record([drug_type, drug_name, pathway_name] + identifier.items() + group.items() +
                                   pathway_drug.items() + pathway_enzyme.items())
                            for identifier in identifiers for group in drug_groups for pathway_drug in pathway_drugs
                            for pathway_enzyme in pathway_enzymes]
        stream = StringIO(u'<drugbank>'
                          u'  <drug type="{type}" created="2005-06-13" updated="2015-02-23">'
                          u'    <drugbank-id primary="true">{0[drug/drugbank-id]}</drugbank-id>'
                          u'    <drugbank-id>{1[drug/drugbank-id]}</drugbank-id>'
                          u'    <name>{name}</name>'
                          u'    <groups>'
                          u'      <group>{2[drug/groups/group]}</group>'
                          u'      <group>{3[drug/groups/group]}</group>'
                          u'    </groups>'
                          u'    <pathways>'
                          u'      <pathway>'
                          u'        <smpdb-id>SMP00278</smpdb-id>'
                          u'        <name>{pathway}</name>'
                          u'        <drugs>'
                          u'          <drug>'
                          u'            <drugbank-id>{4[drug/pathways/pathway/drugs/drug/drugbank-id]}</drugbank-id>'
                          u'            <name>{4[drug/pathways/pathway/drugs/drug/name]}</name>'
                          u'          </drug>'
                          u'          <drug>'
                          u'            <drugbank-id>{5[drug/pathways/pathway/drugs/drug/drugbank-id]}</drugbank-id>'
                          u'            <name>{5[drug/pathways/pathway/drugs/drug/name]}</name>'
                          u'          </drug>'
                          u'          <drug>'
                          u'            <drugbank-id>{6[drug/pathways/pathway/drugs/drug/drugbank-id]}</drugbank-id>'
                          u'            <name>{6[drug/pathways/pathway/drugs/drug/name]}</name>'
                          u'          </drug>'
                          u'        </drugs>'
                          u'        <enzymes>'
                          u'          <uniprot-id>{7[drug/pathways/pathway/enzymes/uniprot-id]}</uniprot-id>'
                          u'          <uniprot-id>{8[drug/pathways/pathway/enzymes/uniprot-id]}</uniprot-id>'
                          u'          <uniprot-id>{9[drug/pathways/pathway/enzymes/uniprot-id]}</uniprot-id>'
                          u'          <!-- ... -->'
                          u'        </enzymes>'
                          u'      </pathway>'
                          u'    </pathways>'
                          u'  </drug>'
                          u'</drugbank>'.format(*(identifiers + drug_groups + pathway_drugs + pathway_enzymes),
                                                name=drug_name[1], type=drug_type[1], pathway=pathway_name[1]))
        reader = Reader(stream, selected=[drug_type[0], drug_name[0], pathway_name[0]] + identifiers[0].keys() +
                                         drug_groups[0].keys() + pathway_drugs[0].keys() + pathway_enzymes[0].keys())

        actual_records = list(reader)

        self.assertItemsEqual(expected_records, actual_records)

    def test_can_process_singleton_sequence(self):
        drug_type = 'drug@type', 'biotech'
        identifiers = [{'drug/drugbank-id': 'DB00002', 'drug/drugbank-id@primary': 'true'},
                       {'drug/drugbank-id': 'BIOD00071'},
                       {'drug/drugbank-id': 'BTD00071'}]
        drug_name = 'drug/name', 'Cetuximab'
        drug_group = 'drug/groups/group', 'approved'
        external_links = [{'drug/external-links/external-link/resource': 'RxList',
                           'drug/external-links/external-link/url': 'http://www.rxlist.com/cgi/generic3/erbitux.htm'},
                          {'drug/external-links/external-link/resource': 'Drugs.com',
                           'drug/external-links/external-link/url': 'http://www.drugs.com/cdi/cetuximab.html'}]
        effects = [{'drug/snp-effects/effect/protein-name': 'Low affinity immunoglobulin gamma Fc region receptor II-a',
                    'drug/snp-effects/effect/gene-symbol': 'FCGR2A',
                    'drug/snp-effects/effect/uniprot-id': 'P12318',
                    'drug/snp-effects/effect/rs-id': 'rs1801274',
                    'drug/snp-effects/effect/defining-change': 'H allelle',
                    'drug/snp-effects/effect/description': 'Increased progression free survival',
                    'drug/snp-effects/effect/pubmed-id': '17704420'},
                   {'drug/snp-effects/effect/protein-name': 'Low affinity immunoglobulin gamma Fc region receptor'
                                                            ' III-A',
                    'drug/snp-effects/effect/gene-symbol': 'FCGR3A',
                    'drug/snp-effects/effect/uniprot-id': 'P08637',
                    'drug/snp-effects/effect/rs-id': 'rs396991',
                    'drug/snp-effects/effect/defining-change': 'A - C',
                    'drug/snp-effects/effect/description': 'Better response to drug therapy (longer progression free'
                                                           ' survival) with the F allele',
                    'drug/snp-effects/effect/pubmed-id': '17704420'}]
        expected_records = [Record([drug_type, drug_name, drug_group] + identifier.items() + link.items() +
                                   effect.items())
                            for identifier in identifiers for link in external_links for effect in effects]
        stream = StringIO(u'<drug type="{type}" created="2005-06-13" updated="2015-11-10">'
                          u'  <drugbank-id primary="true">{id[0][drug/drugbank-id]}</drugbank-id>'
                          u'  <drugbank-id>{id[1][drug/drugbank-id]}</drugbank-id>'
                          u'  <drugbank-id>{id[2][drug/drugbank-id]}</drugbank-id>'
                          u'  <name>{name}</name>'
                          u'  <groups>'
                          u'    <group>{group}</group>'
                          u'  </groups>'
                          u'  <external-links>'
                          u'    <external-link>'
                          u'      <resource>{link[0][drug/external-links/external-link/resource]}</resource>'
                          u'      <url>{link[0][drug/external-links/external-link/url]}</url>'
                          u'    </external-link>'
                          u'    <external-link>'
                          u'      <resource>{link[1][drug/external-links/external-link/resource]}</resource>'
                          u'      <url>{link[1][drug/external-links/external-link/url]}</url>'
                          u'    </external-link>'
                          u'  </external-links>'
                          u'  <snp-effects>'
                          u'    <effect>'
                          u'      <protein-name>{effect[0][drug/snp-effects/effect/protein-name]}</protein-name>'
                          u'      <gene-symbol>{effect[0][drug/snp-effects/effect/gene-symbol]}</gene-symbol>'
                          u'      <uniprot-id>{effect[0][drug/snp-effects/effect/uniprot-id]}</uniprot-id>'
                          u'      <rs-id>{effect[0][drug/snp-effects/effect/rs-id]}</rs-id>'
                          u'      <allele/>'
                          u'      <defining-change>{effect[0][drug/snp-effects/effect/defining-change]}</defining-change>'
                          u'      <description>{effect[0][drug/snp-effects/effect/description]}</description>'
                          u'      <pubmed-id>{effect[0][drug/snp-effects/effect/pubmed-id]}</pubmed-id>'
                          u'    </effect>'
                          u'    <effect>'
                          u'      <protein-name>{effect[1][drug/snp-effects/effect/protein-name]}</protein-name>'
                          u'      <gene-symbol>{effect[1][drug/snp-effects/effect/gene-symbol]}</gene-symbol>'
                          u'      <uniprot-id>{effect[1][drug/snp-effects/effect/uniprot-id]}</uniprot-id>'
                          u'      <rs-id>{effect[1][drug/snp-effects/effect/rs-id]}</rs-id>'
                          u'      <allele/>'
                          u'      <defining-change>{effect[1][drug/snp-effects/effect/defining-change]}</defining-change>'
                          u'      <description>{effect[1][drug/snp-effects/effect/description]}</description>'
                          u'      <pubmed-id>{effect[1][drug/snp-effects/effect/pubmed-id]}</pubmed-id>'
                          u'    </effect>'
                          u'  </snp-effects>'
                          u'</drug>'.format(type=drug_type[1], id=identifiers, name=drug_name[1], group=drug_group[1],
                                            link=external_links, effect=effects))
        reader = Reader(stream, selected=[drug_type[0], drug_name[0], drug_group[0]] + identifiers[0].keys() +
                                         external_links[0].keys() + effects[0].keys())

        actual_records = list(reader)

        self.assertItemsEqual(expected_records, actual_records)


    def test_can_process_repeating_sequence(self):
        drug_type = 'drug@type', 'biotech'
        identifiers = [{'drug/drugbank-id': 'DB00002', 'drug/drugbank-id@primary': 'true'},
                       {'drug/drugbank-id': 'BIOD00071'},
                       {'drug/drugbank-id': 'BTD00071'}]
        drug_name = 'drug/name', 'Cetuximab'
        drug_group = 'drug/groups/group', 'approved'
        external_links = [{'drug/external-links/external-link/resource': 'RxList',
                           'drug/external-links/external-link/url': 'http://www.rxlist.com/cgi/generic3/erbitux.htm'},
                          {'drug/external-links/external-link/resource': 'Drugs.com',
                           'drug/external-links/external-link/url': 'http://www.drugs.com/cdi/cetuximab.html'}]
        effects = [{'drug/snp-effects/effect/protein-name': 'Low affinity immunoglobulin gamma Fc region receptor II-a',
                    'drug/snp-effects/effect/gene-symbol': 'FCGR2A',
                    'drug/snp-effects/effect/uniprot-id': 'P12318',
                    'drug/snp-effects/effect/rs-id': 'rs1801274',
                    'drug/snp-effects/effect/defining-change': 'H allelle',
                    'drug/snp-effects/effect/description': 'Increased progression free survival',
                    'drug/snp-effects/effect/pubmed-id': '17704420'},
                   {'drug/snp-effects/effect/protein-name': 'Low affinity immunoglobulin gamma Fc region receptor'
                                                            ' III-A',
                    'drug/snp-effects/effect/gene-symbol': 'FCGR3A',
                    'drug/snp-effects/effect/uniprot-id': 'P08637',
                    'drug/snp-effects/effect/rs-id': 'rs396991',
                    'drug/snp-effects/effect/defining-change': 'A - C',
                    'drug/snp-effects/effect/description': 'Better response to drug therapy (longer progression free'
                                                           ' survival) with the F allele',
                    'drug/snp-effects/effect/pubmed-id': '17704420'}]
        expected_records = [Record([drug_type, drug_name, drug_group] + identifier.items() + link.items() +
                                   effect.items())
                            for identifier in identifiers for link in external_links for effect in effects]
        stream = StringIO(u'<drug type="{type}" created="2005-06-13" updated="2015-11-10">'
                          u'  <drugbank-id primary="true">{id[0][drug/drugbank-id]}</drugbank-id>'
                          u'  <drugbank-id>{id[1][drug/drugbank-id]}</drugbank-id>'
                          u'  <drugbank-id>{id[2][drug/drugbank-id]}</drugbank-id>'
                          u'  <name>{name}</name>'
                          u'  <groups>'
                          u'    <group>{group}</group>'
                          u'  </groups>'
                          u'  <external-links>'
                          u'    <external-link>'
                          u'      <resource>{link[0][drug/external-links/external-link/resource]}</resource>'
                          u'      <url>{link[0][drug/external-links/external-link/url]}</url>'
                          u'    </external-link>'
                          u'    <external-link>'
                          u'      <resource>{link[1][drug/external-links/external-link/resource]}</resource>'
                          u'      <url>{link[1][drug/external-links/external-link/url]}</url>'
                          u'    </external-link>'
                          u'  </external-links>'
                          u'  <snp-effects>'
                          u'    <effect>'
                          u'      <protein-name>{effect[0][drug/snp-effects/effect/protein-name]}</protein-name>'
                          u'      <gene-symbol>{effect[0][drug/snp-effects/effect/gene-symbol]}</gene-symbol>'
                          u'      <uniprot-id>{effect[0][drug/snp-effects/effect/uniprot-id]}</uniprot-id>'
                          u'      <rs-id>{effect[0][drug/snp-effects/effect/rs-id]}</rs-id>'
                          u'      <allele/>'
                          u'      <defining-change>{effect[0][drug/snp-effects/effect/defining-change]}</defining-change>'
                          u'      <description>{effect[0][drug/snp-effects/effect/description]}</description>'
                          u'      <pubmed-id>{effect[0][drug/snp-effects/effect/pubmed-id]}</pubmed-id>'
                          u'      <protein-name>{effect[1][drug/snp-effects/effect/protein-name]}</protein-name>'
                          u'      <gene-symbol>{effect[1][drug/snp-effects/effect/gene-symbol]}</gene-symbol>'
                          u'      <uniprot-id>{effect[1][drug/snp-effects/effect/uniprot-id]}</uniprot-id>'
                          u'      <rs-id>{effect[1][drug/snp-effects/effect/rs-id]}</rs-id>'
                          u'      <allele/>'
                          u'      <defining-change>{effect[1][drug/snp-effects/effect/defining-change]}</defining-change>'
                          u'      <description>{effect[1][drug/snp-effects/effect/description]}</description>'
                          u'      <pubmed-id>{effect[1][drug/snp-effects/effect/pubmed-id]}</pubmed-id>'
                          u'    </effect>'
                          u'  </snp-effects>'
                          u'</drug>'.format(type=drug_type[1], id=identifiers, name=drug_name[1], group=drug_group[1],
                                            link=external_links, effect=effects))
        reader = Reader(stream, selected=[drug_type[0], drug_name[0], drug_group[0]] + identifiers[0].keys() +
                                         external_links[0].keys() + effects[0].keys())

        actual_records = list(reader)

        self.assertItemsEqual(expected_records, actual_records)
