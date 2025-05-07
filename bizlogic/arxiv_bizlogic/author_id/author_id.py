import re
import unicodedata
from typing import Optional

from sqlalchemy.orm import Session
from arxiv.db.models import TapirUser, AuthorIds


def make_author_id_base(last_name: str, first_name: str) -> str:
    """Generate the base part of the author ID from last and first names."""

    # Remove accents and convert to ASCII
    last_name = unicodedata.normalize('NFKD', last_name).encode('ASCII', 'ignore').decode('ASCII')
    first_name = unicodedata.normalize('NFKD', first_name).encode('ASCII', 'ignore').decode('ASCII')

    base = re.sub(r'[^a-zA-Z]', '', last_name).lower()
    first_initial = re.sub(r'[^a-zA-Z]', '', first_name).lower()[:1]
    if not first_initial:
        first_initial = "-"
    base += "_" + first_initial
    return base


def next_char(c: str) -> str:
    """Next chr"""
    return chr(ord(c) + 1)


def author_id_generator(session: Session, user_id: str) -> Optional[str]:
    """
    Generate an author ID key for the given user.
    This routine does not check if there's already an author_id assigned to this user.

    Arguments:
        session {sqlalchemy.orm.session.Session} -- The database session
        user_id {str} -- The user ID (int)

    Returns:
        str | None: generated author ID or None
    """

    # Find the user
    user: Optional[TapirUser] = session.query(TapirUser).filter(TapirUser.user_id == user_id).one_or_none()

    if user:
        author_id: Optional[AuthorIds] = session.query(AuthorIds).filter(AuthorIds.user_id == user_id).one_or_none()
        if author_id:
            return str(author_id.author_id)

        base = make_author_id_base(user.last_name, user.first_name)

        # Find existing author IDs with the same base
        pattern_begin = f"{base}_"

        pattern_end = f"{base[:-1]}{next_char(base[-1])}_"
        # This works even if the letter is z as z + 1 is a valid char.
        # eg select * from arXiv_author_ids where author_id between 'xu_z_' and 'xu_{_'; returns 7 rows

        # Original was using like to find it which may scan table. Using between - since the column is indexed
        # this search is def done in O(log2(N)) order. Also, since it starts from the count, it is VERY likely
        # the first one finds the empty slot.
        sequence = session.query(AuthorIds).filter(AuthorIds.author_id.between(pattern_begin, pattern_end)).count()
        for _ in range(10000000):
            sequence += 1
            proposed = f"{pattern_begin}{str(sequence)}"
            if session.query(AuthorIds).filter(AuthorIds.author_id == proposed).count() == 0:
                return proposed
    return None