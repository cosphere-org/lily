# # -*- coding: utf-8 -*-


# class CommandsConfViewTestCase(TestCase):

#     uri = reverse('internal:commands_conf')

#     @pytest.fixture(autouse=True)
#     def initfixture(self, tmpdir):
#         self.tmpdir = tmpdir

#     def setUp(self):

#         self.app = Client()
#         self.auth_headers = {
#             'HTTP_X_CS_ACCOUNT_TYPE': ADMIN,
#             'HTTP_X_CS_USER_ID': 190,
#         }

#     def test_get(self):

#         conf = self.tmpdir.mkdir('.docs').join('commands_conf.json')
#         conf.write(json.dumps({
#             'COMMAND_1': {'command': 1},
#             'COMMAND_2': {'command': 2},
#         }))

#         with override_settings(LILY_DOCS_COMMANDS_CONF_FILE=str(conf)):
#             respose = self.app.get(
#                 self.uri,
#                 **self.auth_headers)

#             assert respose.status_code == 200
#             assert respose.json() == {
#                 '@type': 'commands_config',
#                 '@event': 'COMMANDS_CONF_FOR_SERVICE_LISTED',
#                 'commands_config': {
#                     'COMMAND_1': {'command': 1},
#                     'COMMAND_2': {'command': 2},
#                 }
#             }
