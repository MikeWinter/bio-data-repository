from django.test import TestCase

from ...formats.drugbank43.parser import Record, RecordSet


class RecordSetTest(TestCase):
    def setUp(self):
        self.instance = RecordSet()

    def test_is_iterable(self):
        from collections import Iterable

        self.assertTrue(issubclass(RecordSet, Iterable))

    def test_empty_recordset_yields_identity_record(self):
        expected_length = 1
        expected_fields = []

        records = list(self.instance)
        actual_length = len(records)
        actual_fields = records.pop().fields

        self.assertEqual(expected_length, actual_length)
        self.assertItemsEqual(expected_fields, actual_fields)

    def test_extending_empty_recordset_creates_record(self):
        name, value = self.generate_random_strings(2)

        self.instance *= Record({name: value})

        record = list(self.instance).pop()
        self.assertEqual(value, record[name])

    def test_extending_existing_record_adds_field(self):
        names = self.generate_random_strings(2)
        values = self.generate_random_strings(2)
        expected_length = 1
        expected_values = {name: value for name, value in zip(names, values)}

        self.instance *= Record({names[0]: values[0]})
        self.instance *= Record({names[1]: values[1]})

        records = tuple(self.instance)
        self.assertEqual(expected_length, len(records))
        record = records[0]
        actual_values = {name: record[name] for name in names}
        self.assertDictEqual(expected_values, actual_values)

    # def test_resultset_or_creates_union(self):
    #     import operator
    #
    #     instances = [self.instance, RecordSet()]
    #     names = self.generate_random_strings(2)
    #     values = [self.generate_random_strings(2), self.generate_random_strings(2)]
    #     expected_values = [{names[i]: value} for i, x in enumerate(values) for value in x]
    #
    #     for i, instance in enumerate(instances):
    #         instances[i] = instance * Record(zip(names, values[i]))
    #         # for value in values[i]:
    #         #     record = Record({names[i]: value})
    #         #     print record
    #         #     instances[i] = instance * record
    #         #     print [str(o) for o in instance]
    #         print [str(o) for o in instances[i]]
    #
    #     records = reduce(operator.or_, instances)
    #     actual_values = [{name: record[name]} for record in records for name in record]
    #     print expected_values
    #     print actual_values
    #     self.assertItemsEqual(expected_values, actual_values)
    #     self.assertNotIn(id(records), (id(instance) for instance in instances))

    @staticmethod
    def generate_random_string(max_length=10):
        import random
        import string

        characters = [random.choice(string.letters) for _ in range(random.randrange(1, max_length))]
        return "".join(characters)

    @classmethod
    def generate_random_strings(cls, count=2, max_length=10):
        strings = [cls.generate_random_string(max_length) for _ in range(count)]
        return strings
