from django.core.cache import cache
from django.db import IntegrityError
from django.test import TestCase

from .models import Category
from .services import CATEGORY_TREE_CACHE_KEY, CategoryTreeService


class CategoryModelTests(TestCase):

    def test_slug_must_be_unique(self):
        Category.objects.create(name='Electronics', slug='electronics')
        with self.assertRaises(IntegrityError):
            Category.objects.create(name='Electronics Again', slug='electronics')


class CategoryTreeServiceTests(TestCase):

    def setUp(self):
        cache.clear()
        self.root = Category.objects.create(name='Electronics', slug='electronics')
        self.child = Category.objects.create(name='Phones', slug='phones', parent=self.root)
        self.grandchild = Category.objects.create(name='Smartphones', slug='smartphones', parent=self.child)

    def test_get_category_and_descendant_ids_returns_full_subtree(self):
        ids = CategoryTreeService.get_category_and_descendant_ids(self.root.id)
        self.assertCountEqual(ids, [str(self.root.id), str(self.child.id), str(self.grandchild.id)])

    def test_get_tree_populates_redis_cache(self):
        self.assertIsNone(cache.get(CATEGORY_TREE_CACHE_KEY))
        CategoryTreeService.get_tree()
        self.assertIsNotNone(cache.get(CATEGORY_TREE_CACHE_KEY))

    def test_invalidate_clears_cache(self):
        CategoryTreeService.get_tree()
        CategoryTreeService.invalidate()
        self.assertIsNone(cache.get(CATEGORY_TREE_CACHE_KEY))
