import unittest

from arxiv_bizlogic.bizmodels.user_model import VetoStatusEnum

from arxiv_oauth2.biz.account_biz import AccountInfoModel, CAREER_STATUS, CategoryIdModel, CategoryGroup


class TestAccountModel(unittest.TestCase):

    def test_account_info_model(self):
        info = AccountInfoModel(
            id="100",
            email_verified=True,
            scopes=["great"],
            username="test-user",
            email="test@example.com",
            first_name="First",
            last_name="Last",
            suffix_name=None,
            country="us",
            affiliation="arxiv.org",
            default_category=CategoryIdModel(archive="cs", subject_class="DB"),  # : Optional[CategoryIdModel] = None
            groups=[CategoryGroup.CS],
            url="www.example.com",
            career_status=CAREER_STATUS("Staff"),
            tracking_cookie=None,
            veto_status=VetoStatusEnum('ok')
        )
        user_model = info.to_user_model_data()
        self.assertEqual({'affiliation': 'arxiv.org',
                          'archive': 'cs',
                          'country': 'us',
                          'dirty': False,
                          'email': 'test@example.com',
                          'email_bouncing': False,
                          'email_verified': True,
                          'first_name': 'First',
                          'flag_allow_tex_produced': False,
                          'flag_approved': True,
                          'flag_banned': False,
                          'flag_can_lock': False,
                          'flag_deleted': False,
                          'flag_edit_system': False,
                          'flag_edit_users': False,
                          'flag_email_verified': False,
                          'flag_group_cs': True,
                          'flag_group_econ': False,
                          'flag_group_eess': False,
                          'flag_group_math': False,
                          'flag_group_nlin': False,
                          'flag_group_physics': False,
                          'flag_group_q_bio': False,
                          'flag_group_q_fin': False,
                          'flag_group_stat': False,
                          'flag_group_test': False,
                          'flag_html_email': False,
                          'flag_internal': False,
                          'flag_proxy': False,
                          'flag_wants_email': False,
                          'id': '100',
                          'joined_date': None,
                          'joined_remote_host': '',
                          'last_name': 'Last',
                          'oidc_id': None,
                          'original_subject_classes': 'cs.DB',
                          'policy_class': 2,
                          'scopes': ['great'],
                          'share_email': 8,
                          'share_first_name': True,
                          'share_last_name': True,
                          'subject_class': 'DB',
                          'suffix_name': None,
                          'tracking_cookie': None,
                          'type': 1,
                          'url': 'www.example.com',
                          'username': 'test-user',
                          'veto_status': 'ok'}, user_model)  # add assertion here


if __name__ == '__main__':
    unittest.main()
