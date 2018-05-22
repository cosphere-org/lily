# -*- coding: utf-8 -*-
# # -*- coding: utf-8 -*-

# import logging
# import json

# from django.conf import settings

# from lily.base.events import EventFactory


# logger = logging.getLogger()


# event = EventFactory(logger)


# class AngularClientRenderer:

#     # -- COLLECTOR class !!!!! with it's assertions
#     def render_by_domain_index(self):

#         by_domain_index = {}
#         for filepath in settings.LILY_COMMAND_ENTRYPOINTS:
#             with open(filepath, 'r') as f:
#                 content = json.loads(f.read())
#                 for name, conf in content['commands'].items():
#                     command = Command(name, conf)

#                     by_domain_index.setdefault(command.domain_id, {})

#                     if not command.is_private:
#                         if by_domain_index[command.domain_id].get(name):
#                             raise event.ServerError(
#                                 'DUPLICATE_PIBLIC_DOMAIN_COMMAND_DETECTED',
#                                 data={
#                                     'command_name': name,
#                                     'domain_id': command.domain_id
#                                 })

#                         else:
#                             by_domain_index[command.domain_id][name] = command

#         return by_domain_index

#     # -- domain renderer -> renders three files and folder !!!!
#     # -- I also need service renderer which is feed by all commands and domains
#     # -- at once
#     def render_command(command):

#         c = command
#         if c.method == 'get':
#             return '''
#             {c.header}
#             public {c.camel_name}({c.signature.input}): DataState<{c.response.name}> {
#                 return this.client.getDataState<{c.response.name}>({c.signature.call_args});
#             }

#             '''.format(c=c)  # noqa

#         else:
#             return '''
#             {c.header}
#             public {c.camel_name}({c.signature.input}): Observable<{c.response.name}> {
#                 return this.client
#                     .{c.method}<{c.response.name}>({c.signature.call_args})
#                     .pipe(filter(x => !_.isEmpty(x)));
#             }

#             '''.format(c=c)  # noqa


# if __name__ == '__main__':
#     repo = AngularClientRepo()
#     repo.pull()
#     repo.install()
#     repo.build()
#     repo.cd_to_repo()
#     next_version = repo.upgrade_version(
#         AngularClientRepo.VERSION_UPGRADE.MINOR)
#     repo.add_all()
#     repo.commit(next_version)
#     repo.push()
