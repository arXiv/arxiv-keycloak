import os
import logging

from local_db.start_arxiv_mysql import start_clean_mysql
from arxiv.util.database_loader import DatabaseLoader

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

logger = logging.getLogger(__name__)


def main():
    db_engine = start_clean_mysql()
    loader = DatabaseLoader(db_engine)
    test_data_dir = os.path.join(root_dir, 'tests', 'data')

    # load users
    users = [os.path.join(test_data_dir, filename) for filename in sorted([fn for fn in os.listdir(test_data_dir) if fn.startswith('test-user')])]
    loader.load_data_from_files(users)


if __name__ == '__main__':
    main()
