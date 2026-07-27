from django.core.cache import cache

from .models import Category

CATEGORY_TREE_CACHE_KEY = 'category_tree'
CATEGORY_TREE_CACHE_TTL = 60 * 60


class CategoryTreeService:
    @staticmethod
    def get_tree():
        cached = cache.get(CATEGORY_TREE_CACHE_KEY)
        if cached is not None:
            return cached

        tree = CategoryTreeService._build_tree()
        cache.set(CATEGORY_TREE_CACHE_KEY, tree, CATEGORY_TREE_CACHE_TTL)
        return tree

    @staticmethod
    def get_category_and_descendant_ids(category_id):
        tree = CategoryTreeService.get_tree()
        target_id = str(category_id)

        node = CategoryTreeService._find_node(tree, target_id)
        if node is None:
            return [category_id]

        ids = []
        stack = [node]
        while stack:
            current = stack.pop()
            ids.append(current['id'])
            stack.extend(current['children'])
        return ids

    @staticmethod
    def _find_node(nodes, target_id):
        stack = list(nodes)
        while stack:
            node = stack.pop()
            if node['id'] == target_id:
                return node
            stack.extend(node['children'])
        return None


    @staticmethod
    def _build_tree():
        categories = list(Category.objects.all().values('id', 'name', 'slug', 'parent_id'))

        by_parent = {}
        for cat in categories:
            by_parent.setdefault(cat['parent_id'], []).append(cat)

        roots = by_parent.get(None, [])
        tree = []

        for root in roots:
            node = {
                'id': str(root['id']),
                'name': root['name'],
                'slug': root['slug'],
                'children': [],
            }
            tree.append(node)

            stack = [(root['id'], node)]
            while stack:
                parent_id, parent_node = stack.pop()
                for child in by_parent.get(parent_id, []):
                    child_node = {
                        'id': str(child['id']),
                        'name': child['name'],
                        'slug': child['slug'],
                        'children': [],
                    }
                    parent_node['children'].append(child_node)
                    stack.append((child['id'], child_node))

        return tree

    @staticmethod
    def invalidate():
        cache.delete(CATEGORY_TREE_CACHE_KEY)
