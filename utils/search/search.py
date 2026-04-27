from django.db.models import Q


class Search(object):
    search_fields = list()

    @classmethod
    def get_clauses(cls, search_term):
        clauses = Q()
        if search_term and cls.search_fields:
            for search_field in cls.search_fields:
                clauses |= Q(**{f"{search_field}__icontains": search_term})

        return clauses
