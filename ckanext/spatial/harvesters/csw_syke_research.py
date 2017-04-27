from ckan import model
from ckan.lib.helpers import json

from ckan.plugins.core import SingletonPlugin, implements

from ckanext.harvest.interfaces import IHarvester

from ckanext.spatial.harvesters.csw import CSWHarvester, text_traceback


class CSWHarvesterSykeResearch(CSWHarvester, SingletonPlugin):
    '''
    A CSW harvester for research metadata from SYKE Metatietopalvelu
    '''
    implements(IHarvester)


    def info(self):

        return {
            'name': 'csw_syke_research',
            'title': 'CSW Server - SYKE research',
            'description': 'SYKE research metadata'
            }


    def get_package_dict(self, iso_values, harvest_object):

        tags = []
        if 'tags' in iso_values:
            for tag in iso_values['tags']:
                tag = tag[:50] if len(tag) > 50 else tag
                tags.append({'name': tag})

        # Add default_tags from config
        default_tags = self.source_config.get('default_tags',[])
        if default_tags:
           for tag in default_tags:
              tags.append({'name': tag})

        package_dict = {
            'title': iso_values['title'],
            'notes': iso_values['abstract'],
            'tags': tags,
            'resources': [],
            'license_id': 'cc-by', # SYKE research metadata has always this license
        }

        # Set address to the metadata view as source
        package_dict['url'] = 'http://metatieto.ymparisto.fi:8080/geoportal/catalog/search/resource/details.page?uuid=' + harvest_object.guid

        # Set author and email as in responsible organization
        individual_name = ''
        organization_name = ''
        contact_email = ''
        if iso_values['responsible-organisation']:
            for party in iso_values['responsible-organisation']:
                if party['individual-name']:
                    individual_name = party['individual-name']
                    if party['organisation-name']:
                        organization_name = party['organisation-name']
                    if party['contact-info']:
                        contact_email = party['contact-info']['email']
                    break
        package_dict['author'] = individual_name
        if len(organization_name) > 0:
            package_dict['author'] = individual_name + ' ' + organization_name
        package_dict['author_email'] = contact_email

        # We need to get the owner organization (if any) from the harvest
        # source dataset
        source_dataset = model.Package.get(harvest_object.source.id)
        if source_dataset.owner_org:
            package_dict['owner_org'] = source_dataset.owner_org

        # Package name
        package = harvest_object.package
        if package is None or package.title != iso_values['title']:
            name = self._gen_new_name(iso_values['title'])
            if not name:
                name = self._gen_new_name(str(iso_values['guid']))
            if not name:
                raise Exception('Could not generate a unique name from the title or the GUID. Please choose a more unique title.')
            package_dict['name'] = name
        else:
            package_dict['name'] = package.name

        return package_dict
