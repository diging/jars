from django.db.models import Q

from cookies.models import *

from itertools import chain, groupby
from Levenshtein import distance

_normalize = lambda s: s.replace('.', ' ').replace(',', ' ').lower().strip()
_tokenize = lambda s: [part for part in s.split() if len(part) > 2]


def suggest_similar(entity, qs=None):
    """
    Attempt to find :class:`.ConceptEntity` instances that are similar to
    ``entity``.

    Parameters
    ----------
    entity : :class:`.ConceptEntity`

    Returns
    -------
    list
        A list of :class:`.ConceptEntity` instances. Ordered by descending
        similarity.
    """

    rep_ids = Identity.objects.filter(entities=entity.id).values_list('representative', flat=True)
    identities = Identity.objects.filter(representative__id__in=rep_ids)
    if not qs:
        qs = ConceptEntity.objects.all()
    name = _normalize(entity.name)
    suggestions = []
    # suggestions += [o.id ConceptEntity.objects.filter(Q(name__icontains=name) & ~Q(id=entity.id))

    name_parts = _tokenize(name)
    _id = lambda o: o.id
    _name = lambda o: o.name   #similar_entities = similar_entities.filter()
    _find = lambda part: qs.filter(Q(name__icontains=part) & ~Q(id=entity.id) & ~Q(identities__id__in=identities))
    for name, group in groupby(sorted(chain(*[_find(part) for part in name_parts]), key=_name), key=_name):
        for pk, subgroup in groupby(sorted(group, key=_id), key=_id):
            subgroup = [o for o in subgroup]
            suggestions.append((subgroup[0], len(subgroup)))
    _count = lambda o: o[1] - distance(name, _normalize(o[0].name))
    if len(suggestions) == 0:
        return []
    return list(zip(*sorted(suggestions, key=_count)[::-1])[0])
