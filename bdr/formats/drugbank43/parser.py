import collections
import itertools
from xml.dom import Node, pulldom

from .. import Converter as BaseConverter, Reader as BaseReader, Record as BaseRecord

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


class Converter(BaseConverter):
    """
    Converts records to nominally identical types, but with the option to elide
    fields.
    """

    def __init__(self, reader, fields, comment, escape, line_terminator, quote, separator, **kwargs):
        super(Converter, self).__init__(reader, kwargs, fields)
        self.comment_char = comment
        self.escape_char = escape
        self.quote_char = quote
        self.separator_char = separator
        self.line_terminator = line_terminator

    def __iter__(self):
        for record in self._reader:
            values = []
            for field in self._fields:
                value = self.prepare_value(record.get(field, u''))
                values.append(value)
            yield unicode(self.separator_char.join(values) + self.line_terminator).encode('utf_8')

    def prepare_value(self, value):
        """
        Make a value safe for output according the options specified for
        conversion.

        If a value contains special characters, these must be escaped or quoted
        as determined by the conversion settings. This includes literal escape
        and quote characters (if applicable).

        :param value: The value to make safe.
        :type value: str | unicode
        :return: The equivalent escaped or quoted value.
        :rtype: str | unicode
        :raise ValueError: if the conversion rules will result in emitting a
                           value containing ambiguous special characters.
        """
        if self.escape_char:
            value = value.replace(self.escape_char, self.escape_char * 2)
        if self.quote_char:
            replacement = self.escape_char + self.quote_char if self.escape_char else self.quote_char * 2
            value = value.replace(self.quote_char, replacement)
            if value.startswith(self.comment_char) or self.separator_char in value or self.line_terminator in value:
                value = u"{0}{1}{0}".format(self.quote_char, value)
        elif self.escape_char:
            if value.startswith(self.comment_char):
                value = self.escape_char + value
            value = value.replace(self.separator_char, self.escape_char + self.separator_char)
            value = value.replace(self.line_terminator, self.escape_char + self.line_terminator)
        elif value.startswith(self.comment_char) or self.separator_char in value or self.line_terminator in value:
            raise ValueError(value)
        return unicode(value)


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
        # 'drug/snp-effects/effect/protein-name',
        # 'drug/snp-effects/effect/gene-symbol',
        # 'drug/snp-effects/effect/uniprot-id',
        # 'drug/snp-effects/effect/rs-id',
        # 'drug/snp-effects/effect/allele',
        # 'drug/snp-effects/effect/defining-change',
        # 'drug/snp-effects/effect/description',
        # 'drug/snp-effects/effect/pubmed-id',
        'drug/snp-adverse-drug-reactions/reaction',
        # 'drug/snp-adverse-drug-reactions/reaction/protein-name',
        # 'drug/snp-adverse-drug-reactions/reaction/gene-symbol',
        # 'drug/snp-adverse-drug-reactions/reaction/uniprot-id',
        # 'drug/snp-adverse-drug-reactions/reaction/rs-id',
        # 'drug/snp-adverse-drug-reactions/reaction/allele',
        # 'drug/snp-adverse-drug-reactions/reaction/defining-change',
        # 'drug/snp-adverse-drug-reactions/reaction/description',
        # 'drug/snp-adverse-drug-reactions/reaction/pubmed-id',
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
            if event == pulldom.START_ELEMENT and node.nodeName == 'drug':
                document.expandNode(node)

                for record in self._parse_drug(node):
                    yield record

                node.unlink()

    def _parse_drug(self, element):
        record_set = RecordSet()

        child = element.firstChild
        while child:
            if self._is_element(child):
                if child.nodeName not in {'snp-effects', 'snp-adverse-drug-reactions'}:
                    name = child.nodeName
                    print 'drugs', name, self._element_repeats(name, ('drug',))
                    if not self._element_repeats(name, ('drug',)):
                        new_records = self._process_element(child, ('drug',))
                    else:
                        new_records = RecordSet()
                        while child and child.nodeName == name:
                            new_records |= self._process_element(child, ('drug',))
                            child = child.nextSibling
                            while child and not self._is_element(child):
                                child = child.nextSibling
                        child = child.previousSibling
                    record_set *= new_records
                else:
                    sequences = RecordSet()
                    for sequence in itertools.ifilter(self._is_element, child.childNodes):
                        sequences |= self._process_sequence(sequence, ('drug', child.nodeName), 'pubmed-id')
                    record_set *= sequences
            child = child.nextSibling
        return record_set

    def _process_element(self, element, context):
        records = RecordSet()
        for i in range(element.attributes.length):
            attribute = element.attributes.item(i)
            if self._is_attribute_selected(attribute.name, element.nodeName, context):
                records *= Record({self._build_xpath(element.nodeName, context, attribute.name): attribute.value})

        selected = self._is_element_selected(element.nodeName, context)
        if selected:
            element.normalize()
        node = element.firstChild
        while node:
            if self._is_element(node):
                name = node.nodeName
                if not self._element_repeats(name, context):
                    new_records = self._process_element(node, context + (element.nodeName,))
                else:
                    new_records = RecordSet()
                    while node and node.nodeName == name:
                        if self._is_element(node):
                            new_records |= self._process_element(node, context + (element.nodeName,))
                        node = node.nextSibling
                records *= new_records
            elif selected and self._is_text(node):
                records *= Record({self._build_xpath(element.nodeName, context): node.nodeValue})
            node = node.nextSibling
        return records

    def _process_sequence(self, parent, context, sentinel):
        records = RecordSet()
        node = parent.firstChild
        while node:
            if self._is_element(node):
                if not self._element_repeats(node.nodeName, context + (parent.nodeName,)):
                    new_records = self._process_element(node, context + (parent.nodeName,))
                else:
                    new_records = RecordSet()
                    name = node.nodeName
                    while node and node.nodeName == name:
                        if self._is_element(node):
                            new_records |= self._process_element(node, context + (parent.nodeName,))
                        node = node.nextSibling
                records *= new_records
            elif self._is_element_selected(parent.nodeName, context) and self._is_text(node):
                records *= Record({self._build_xpath(parent.nodeName, context): node.nodeValue})
            node = node.nextSibling
        return records

    def _has_selected_descendant(self, context):
        xpath = self._build_xpath(context[-1], context[:-1])
        return any(itertools.ifilter(lambda name: name.startsWith(xpath), self._options['selected']))

    def _is_attribute_selected(self, name, element, context):
        xpath = self._build_xpath(element, context, name)
        return xpath in self._options['selected']

    def _is_element_selected(self, name, context):
        xpath = self._build_xpath(name, context)
        return xpath in self._options['selected']

    @staticmethod
    def _build_xpath(element, context, attribute=None):
        path = '/'.join(context + (element,))
        if attribute is not None:
            path += '@' + attribute
        return path

    @classmethod
    def _element_repeats(cls, name, context):
        xpath = cls._build_xpath(name, context)
        return xpath in cls.MULTIPLES

    @staticmethod
    def _is_element(node):
        return node.nodeType == Node.ELEMENT_NODE

    @staticmethod
    def _is_text(node):
        return node.nodeType == Node.TEXT_NODE


class RecordSet(object):
    def __init__(self, records=None):
        if records is None:
            records = [Record.IDENTITY]
        self._records = tuple(records)

    def __mul__(self, other):
        if isinstance(other, RecordSet):
            return type(self)(a | b for a in self for b in other)
        if isinstance(other, Record):
            return self * type(self)([other])
        return NotImplemented

    def __or__(self, other):
        if not isinstance(other, RecordSet):
            return NotImplemented
        records = filter(lambda o: o != Record.IDENTITY, self._records + tuple(other._records)) or [Record.IDENTITY]
        return type(self)(records)

    def __iter__(self):
        return iter(self._records)

    def __len__(self):
        return len(self._records)

collections.Iterable.register(RecordSet)
collections.Sized.register(RecordSet)


class Record(BaseRecord):
    """
    Represents a record within a data file, composed of one or more fields.

    By default, records serialise to a comma-separated string.
    """

    def __init__(self, *args, **kwargs):
        data = dict(*args, **kwargs)
        self._fields = tuple(data)
        self._data = data

    def __or__(self, other):
        if not isinstance(other, Record):
            return NotImplemented
        return type(self)(self._data.items() + other._data.items())

Record.IDENTITY = Record()