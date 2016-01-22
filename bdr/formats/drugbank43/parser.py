import collections
import operator
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
    REPEATED_ELEMENTS = {
        u'drug/drugbank-id',
        u'drug/groups/group',
        u'drug/classification',
        u'drug/classification/alternative-parent',
        u'drug/classification/substituent',
        u'drug/salts/salt',
        u'drug/salts/salt/drugbank-id',
        u'drug/synonyms/synonym',
        u'drug/products/product',
        u'drug/international-brands/international-brand',
        u'drug/mixtures/mixture',
        u'drug/packagers/packager',
        u'drug/manufacturers/manufacturer',
        u'drug/prices/price',
        u'drug/categories/category',
        u'drug/affected-organisms/affected-organism',
        u'drug/dosages/dosage',
        u'drug/atc-codes/atc-code',
        u'drug/atc-codes/atc-code/level',
        u'drug/ahfs-codes/ahfs-code',
        u'drug/patents/patent',
        u'drug/food-interactions/food-interaction',
        u'drug/drug-interactions/drug-interaction',
        u'drug/sequences/sequence',
        u'drug/calculated-properties/property',
        u'drug/experimental-properties/property',
        u'drug/external-identifiers/external-identifier',
        u'drug/external-links/external-link',
        u'drug/pathways/pathway/drugs/drug',
        u'drug/pathways/pathway/enzymes/uniprot-id',
        u'drug/reactions/reaction',
        u'drug/reactions/reaction/left-element',
        u'drug/reactions/reaction/right-element',
        u'drug/reactions/reaction/enzymes/enzyme',
        u'drug/snp-effects/effect',
        u'drug/snp-adverse-drug-reactions/reaction',
        u'drug/targets/target',
        u'drug/targets/target/actions/action',
        u'drug/targets/target/polypeptide',
        u'drug/targets/target/polypeptide/external-identifiers/external-identifier',
        u'drug/targets/target/polypeptide/synonyms/synonym',
        u'drug/targets/target/polypeptide/pfams/pfam',
        u'drug/targets/target/polypeptide/go-classifiers/go-classifier',
        u'drug/enzymes/enzyme/',
        u'drug/enzymes/enzyme/actions/action',
        u'drug/enzymes/enzyme/polypeptide',
        u'drug/enzymes/enzyme/polypeptide/external-identifiers/external-identifier',
        u'drug/enzymes/enzyme/polypeptide/synonyms/synonym',
        u'drug/enzymes/enzyme/polypeptide/pfams/pfam',
        u'drug/enzymes/enzyme/polypeptide/go-classifiers/go-classifier',
        u'drug/carriers/carrier',
        u'drug/carriers/carrier/actions/action',
        u'drug/carriers/carrier/polypeptide',
        u'drug/carriers/carrier/polypeptide/external-identifiers/external-identifier',
        u'drug/carriers/carrier/polypeptide/synonyms/synonym',
        u'drug/carriers/carrier/polypeptide/pfams/pfam',
        u'drug/carriers/carrier/polypeptide/go-classifiers/go-classifier',
        u'drug/transporters/transporter',
        u'drug/transporters/transporter/actions/action',
        u'drug/transporters/transporter/polypeptide',
        u'drug/transporters/transporter/polypeptide/external-identifiers/external-identifier',
        u'drug/transporters/transporter/polypeptide/synonyms/synonym',
        u'drug/transporters/transporter/polypeptide/pfams/pfam',
        u'drug/transporters/transporter/polypeptide/go-classifiers/go-classifier',
    }
    """
    A set of XPath expressions (relative to the drugbank element) to elements
    that can occur multiple times within their respective parents.

    :type: set of str
    """
    SEQUENCES = {
        u'drug/snp-effects/effect': [(u'protein-name', u'pubmed-id')],
        u'drug/snp-adverse-drug-reactions/reaction': [(u'protein-name', u'pubmed-id')],
    }
    """
    A dictionary declaring elements that contain repeating element sequences,
    and a list of tag names pairs that occur at the start and end of those sequences.

    :type: dict of list
    """

    def __iter__(self):
        document = pulldom.parse(self._stream)
        for event, node in document:
            if event == pulldom.START_ELEMENT and node.nodeName == u'drug':
                document.expandNode(node)

                for record in self._process_node(node, ()):
                    yield record

                node.unlink()

    def _process_node(self, node, context):
        record_set = RecordSet()
        name = node.nodeName
        sequences = []
        content = u''
        repeated = {}
        child = node.firstChild
        while child:
            if self._is_element(child):
                child_records = self._process_node(child, context + (name,))
                if not self._element_repeats(child.nodeName, context + (name,)):
                    record_set *= child_records
                else:
                    repeated.setdefault(child.nodeName, []).append(child_records)
            elif self._is_text(child):
                content += child.nodeValue

            if self._is_sequence_end(child, context + (name,)):
                for values in repeated.values():
                    record_set *= reduce(operator.or_, values, RecordSet())
                sequences.append(record_set)
                record_set = RecordSet()
                repeated = {}

            child = child.nextSibling

        record_set = reduce(operator.or_, sequences, RecordSet())
        if self._is_element_selected(name, context):
            record_set *= Record({self._build_xpath(name, context): content})
        for attribute, value in node.attributes.items():
            if self._is_attribute_selected(attribute, name, context):
                record_set *= Record({self._build_xpath(name, context, attribute): value})
        return record_set

    @classmethod
    def _is_sequence_end(cls, node, context):
        next_element = cls._next_element(node)
        if next_element is None:
            return True

        xpath = cls._build_xpath(context[-1], context[:-1])
        delimiters = cls.SEQUENCES.get(xpath, [])
        for start, end in delimiters:
            if node.nodeName == end and next_element.nodeName == start:
                return True
        return False

    @classmethod
    def _next_element(cls, node):
        node = node.nextSibling
        while node is not None and not cls._is_element(node):
            node = node.nextSibling
        return node

    def _is_attribute_selected(self, name, element, context):
        xpath = self._build_xpath(element, context, name)
        return xpath in self._options['selected']

    def _is_element_selected(self, name, context):
        xpath = self._build_xpath(name, context)
        return xpath in self._options['selected']

    @staticmethod
    def _build_xpath(element, context, attribute=None):
        path = u'/'.join(context + (element,))
        if attribute is not None:
            path += u'@' + attribute
        return path

    @classmethod
    def _element_repeats(cls, name, context):
        xpath = cls._build_xpath(name, context)
        return xpath in cls.REPEATED_ELEMENTS

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
