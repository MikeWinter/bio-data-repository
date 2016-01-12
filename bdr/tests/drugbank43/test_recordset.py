from django.test import TestCase

from ...formats.drugbank43.parser import RecordSet


class RecordSetTest(TestCase):
    def setUp(self):
        self.instance = RecordSet()

    def test_is_iterable(self):
        from collections import Iterable

        self.assertTrue(issubclass(RecordSet, Iterable))

    def test_empty_recordset_yields_no_elements(self):
        expected_length = 0

        actual_length = len(self.instance)

        self.assertEqual(expected_length, actual_length)

    def test_extending_empty_recordset_creates_record(self):
        name, value = self.generate_random_strings(2)

        self.instance.update(name, value)

        record = list(self.instance).pop()
        self.assertEqual(value, record[name])

    def test_extending_empty_recordset_with_list_creates_records(self):
        name = self.generate_random_string()
        values = self.generate_random_strings(3)

        self.instance.update(name, values)

        result = [record[name] for record in self.instance]
        self.assertListEqual(values, result)

    def test_extending_existing_record_adds_field(self):
        names = self.generate_random_strings(2)
        values = self.generate_random_strings(2)
        expected_length = 1
        expected_values = {name: value for name, value in zip(names, values)}

        self.instance.update(names[0], values[0])
        self.instance.update(names[1], values[1])

        records = tuple(self.instance)
        self.assertEqual(expected_length, len(records))
        record = records[0]
        actual_values = {name: record[name] for name in names}
        self.assertDictEqual(expected_values, actual_values)

    def test_extending_existing_records_with_list_creates_product(self):
        import itertools

        names = self.generate_random_strings(2)
        values = [self.generate_random_strings(2), self.generate_random_strings(2)]
        expected_length = 4
        expected_values = itertools.product(*values)

        for i, name in enumerate(names):
            self.instance.update(name, values[i])

        self.assertEqual(expected_length, len(self.instance))
        actual_values = [tuple(record[name] for name in names) for record in self.instance]
        self.assertItemsEqual(expected_values, actual_values)

    def test_resultset_or_creates_union(self):
        import operator

        instances = (self.instance, RecordSet())
        names = self.generate_random_strings(2)
        values = [self.generate_random_strings(2), self.generate_random_strings(2)]
        expected_values = [{names[i]: value} for i, x in enumerate(values) for value in x]

        for i, instance in enumerate(instances):
            instance.update(names[i], values[i])

        records = reduce(operator.or_, instances)
        actual_values = [{name: record[name]} for record in records for name in record]
        self.assertItemsEqual(expected_values, actual_values)
        self.assertNotIn(id(records), (id(instance) for instance in instances))

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
