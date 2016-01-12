import collections
import itertools
from copy import deepcopy
from xml.dom import Node, pulldom

from .. import Reader as BaseReader, Record

__author__ = "Michael Winter (mail@michael-winter.me.uk)"
__license__ = """
    Biological Dataset Repository: data archival and retrieval.
    Copyright (C) 2015  Michael Winter

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along
    with this program; if not, write to the Free Software Foundation, Inc.,
    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
    """


class Reader(BaseReader):

    MULTIPLES = {
        'drug/drugbank-id',
        'drug/groups/group',
        'drug/classification',
        'drug/classification/alternative-parent',
        'drug/classification/substituent',
        'drug/salts/salt',
        'drug/salts/salt/drugbank-id',
        'drug/synonyms/synonym',
        'drug/products/product',
        'drug/international-brands/international-brand',
        'drug/mixtures/mixture',
        'drug/packagers/packager',
        'drug/manufacturers/manufacturer',
        'drug/prices/price',
        'drug/categories/category',
        'drug/affected-organisms/affected-organism',
        'drug/dosages/dosage',
        'drug/atc-codes/atc-code',
        'drug/atc-codes/atc-code/level',
        'drug/ahfs-codes/ahfs-code',
        'drug/patents/patent',
        'drug/food-interactions/food-interaction',
        'drug/drug-interactions/drug-interaction',
        'drug/sequences/sequence',
        'drug/calculated-properties/property',
        'drug/experimental-properties/property',
        'drug/external-identifiers/external-identifier',
        'drug/external-links/external-link',
        'drug/pathways/pathway',
        'drug/pathways/pathway/drug',
        'drug/pathways/pathway/enzymes',
        'drug/pathways/pathway/enxymes/uniprot-id',
        'drug/reactions/reaction',
        'drug/reactions/reaction/left-element',
        'drug/reactions/reaction/right-element',
        'drug/reactions/reaction/enzymes/enzyme',
        'drug/snp-effects/effect',
        'drug/snp-effects/effect/protein-name',
        'drug/snp-effects/effect/gene-symbol',
        'drug/snp-effects/effect/uniprot-id',
        'drug/snp-effects/effect/rs-id',
        'drug/snp-effects/effect/allele',
        'drug/snp-effects/effect/defining-change',
        'drug/snp-effects/effect/description',
        'drug/snp-effects/effect/pubmed-id',
        'drug/snp-adverse-drug-reactions/reaction',
        'drug/snp-adverse-drug-reactions/reaction/protein-name',
        'drug/snp-adverse-drug-reactions/reaction/gene-symbol',
        'drug/snp-adverse-drug-reactions/reaction/uniprot-id',
        'drug/snp-adverse-drug-reactions/reaction/rs-id',
        'drug/snp-adverse-drug-reactions/reaction/allele',
        'drug/snp-adverse-drug-reactions/reaction/defining-change',
        'drug/snp-adverse-drug-reactions/reaction/description',
        'drug/snp-adverse-drug-reactions/reaction/pubmed-id',
        'drug/targets/target',
        'drug/targets/target/actions/action',
        'drug/targets/target/polypeptide',
        'drug/targets/target/polypeptide/external-identifiers/external-identifier',
        'drug/targets/target/polypeptide/synonyms/synonym',
        'drug/targets/target/polypeptide/pfams/pfam',
        'drug/targets/target/polypeptide/go-classifiers/go-classifier',
        'drug/enzymes/enzyme/',
        'drug/enzymes/enzyme/actions/action',
        'drug/enzymes/enzyme/polypeptide',
        'drug/enzymes/enzyme/polypeptide/external-identifiers/external-identifier',
        'drug/enzymes/enzyme/polypeptide/synonyms/synonym',
        'drug/enzymes/enzyme/polypeptide/pfams/pfam',
        'drug/enzymes/enzyme/polypeptide/go-classifiers/go-classifier',
        'drug/carriers/carrier',
        'drug/carriers/carrier/actions/action',
        'drug/carriers/carrier/polypeptide',
        'drug/carriers/carrier/polypeptide/external-identifiers/external-identifier',
        'drug/carriers/carrier/polypeptide/synonyms/synonym',
        'drug/carriers/carrier/polypeptide/pfams/pfam',
        'drug/carriers/carrier/polypeptide/go-classifiers/go-classifier',
        'drug/transporters/transporter',
        'drug/transporters/transporter/actions/action',
        'drug/transporters/transporter/polypeptide',
        'drug/transporters/transporter/polypeptide/external-identifiers/external-identifier',
        'drug/transporters/transporter/polypeptide/synonyms/synonym',
        'drug/transporters/transporter/polypeptide/pfams/pfam',
        'drug/transporters/transporter/polypeptide/go-classifiers/go-classifier',
    }
    """
    A set of XPath expressions (relative to the drugbank element) to elements
    that can occur multiple times within their respective parents.

    :type: set of str
    """

    def __iter__(self):
        document = pulldom.parse(self._stream)
        for event, node in document:
            if event == pulldom.START_ELEMENT and node.tagName == 'drug':
                document.expandNode(node)

                for record in self._parse_drug(node):
                    yield record

    def _parse_drug(self, element):
        record_set = RecordSet()

        for child in element.childNodes:
            if not self._is_element(child):
                continue
            if child.tagName not in {'snp-effects', 'snp-adverse-drug-reactions'}:
                record_set = self._process_element(child, ['drug'], record_set)
            else:
                for sequence in itertools.ifilter(self._is_element, child.childNodes):
                    record_set = self._process_sequence(sequence.childNodes, 'protein-name')

        return record_set

    def _process_element(self, element, context, record_set):
        name = element.tagName

        for i in range(element.attributes.length):
            attribute = element.attributes.item(i)
            if self._is_attribute_selected(attribute.name, context + [name]):
                record_set.update(attribute.name, attribute.value)

        selected = self._is_element_selected(element, context)
        if selected:
            element.normalize()
        for child in element.childNodes:
            if self._is_element(child):
                pass
            elif selected and self._is_text(child):
                record_set.update(name, child.nodeValue)

        return record_set

    def _process_sequence(self, elements, sentinel):
        return []

    def _has_selected_descendant(self, context):
        xpath = '/'.join(context)
        return any(itertools.ifilter(lambda name: name.startsWith(xpath), self._options['selected']))

    def _is_attribute_selected(self, name, context):
        return False

    def _is_element_selected(self, name, context):
        return False

    @classmethod
    def _element_repeats(cls, name, context):
        return '/'.join(context + [name]) in cls.MULTIPLES

    @staticmethod
    def _is_element(node):
        return node.nodeType == Node.ELEMENT_NODE

    @staticmethod
    def _is_text(node):
        return node.nodeType == Node.TEXT_NODE


class RecordSet(object):
    def __init__(self, records=None):
        self._records = []

    def copy(self):
        copy = RecordSet()
        copy._records = deepcopy(self._records)
        return copy

    def update(self, name, values):
        if not self._records:
            self._records.append(MutableRecord())
        if isinstance(values, basestring) or not isinstance(values, collections.Iterable):
            values = (values,)

        additional_records = []

        for record in self._records:
            original = deepcopy(record)
            iterator = iter(values)
            record[name] = next(iterator)
            for value in iterator:
                duplicate = deepcopy(original)
                duplicate[name] = value
                additional_records.append(duplicate)

        self._records.extend(additional_records)

    def __mul__(self, other):
        if not isinstance(other, RecordSet):
            return NotImplemented

        product = RecordSet()

        return product

    def __or__(self, other):
        if not isinstance(other, RecordSet):
            return NotImplemented

        union = self.copy()
        union._records.extend(deepcopy(other._records))
        return union

    def __iter__(self):
        return iter(self._records)

    def __len__(self):
        return len(self._records)

collections.Iterable.register(RecordSet)
collections.Sized.register(RecordSet)


class MutableRecord(Record):
    """
    Represents a record within a data file, composed of one or more fields.

    By default, records serialise to a comma-separated string.

    Records are typically immutable; this subclass allows client code to extend
    its field list and data.
    """

    def __setitem__(self, field, value):
        self._fields.append(field)
        self._data[field] = value
