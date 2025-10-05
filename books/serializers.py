from rest_framework import serializers

from .models import *


class BookshelfSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bookshelf
        fields = ('name',)


class FormatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Format
        fields = ('book', 'mime_type', 'url')


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('code',)


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ('name', 'birth_year', 'death_year')


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('name',)


class SummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Summary
        fields = ('book', 'text')


class BookSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    authors = PersonSerializer(many=True)
    editors = PersonSerializer(many=True)
    bookshelves = serializers.SerializerMethodField()
    formats = serializers.SerializerMethodField()
    languages = serializers.SerializerMethodField()
    subjects = serializers.SerializerMethodField()
    summaries = serializers.SerializerMethodField()
    translators = PersonSerializer(many=True)

    lookup_field = 'gutenberg_id'

    class Meta:
        model = Book
        fields = (
            'id',
            'title',
            'authors',
            'summaries',
            'editors',
            'translators',
            'subjects',
            'bookshelves',
            'languages',
            'copyright',
            'media_type',
            'formats',
            'download_count'
        )

    def get_bookshelves(self, book):
        bookshelves = [bookshelf.name for bookshelf in book.bookshelves.all()]
        bookshelves.sort()
        return bookshelves

    def get_formats(self, book):
        return {f.mime_type: f.url for f in book.get_formats()}

    def get_id(self, book):
        return book.gutenberg_id

    def get_languages(self, book):
        languages = [language.code for language in book.languages.all()]
        languages.sort()
        return languages

    def get_subjects(self, book):
        subjects = [subject.name for subject in book.subjects.all()]
        subjects.sort()
        return subjects

    def get_summaries(self, book):
        summaries = [summary.text for summary in book.get_summaries()]
        summaries.sort()
        return summaries
