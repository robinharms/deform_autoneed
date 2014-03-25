from unittest import TestCase

import deform
import colander
from fanstatic import Library
from fanstatic import Resource
from fanstatic import get_needed
from fanstatic import init_needed
from pkg_resources import resource_filename


def _mk_reg():
    from deform_autoneed import ResourceRegistry
    return ResourceRegistry()

def _clearFLib(*args):
    from deform_autoneed import deform_autoneed_lib
    #To clear any old registered resources - needs to be done on test start too for some reason.
    deform_autoneed_lib.known_resources = {}

def _mk_richtext_form():
    class Schema(colander.Schema):
        richtext = colander.SchemaNode(colander.String(),
                                       widget = deform.widget.RichTextWidget())
    return deform.Form(Schema())


class ResourceRegistryTests(TestCase):
    setUp = tearDown = _clearFLib

    @property
    def _cut(self):
        from deform_autoneed import ResourceRegistry
        return ResourceRegistry

    def test_init(self):
        testing_lib = Library('testing_lib', 'testing_fixture')
        obj = self._cut(libraries = {'testing_lib': testing_lib})
        self.assertIn('deform', obj.libraries)
        self.assertIn('testing_lib', obj.libraries)

    def test_create_requirement_for_deform_1_style(self):
        reg = self._cut(add_basics = False)
        reg.create_requirement_for('something', 'css/beautify.css', requirement_depends = [])
        self.assertIn('css/beautify.css', reg.libraries['deform'].known_resources)

    def test_create_requirement_for_deform_2_style(self):
        reg = self._cut()
        reg.create_requirement_for('something', 'deform:static/css/beautify.css', requirement_depends = [])
        self.assertIn('something', reg.requirements)
        self.assertIn('css/beautify.css', reg.libraries['deform'].known_resources)
 
    def test_create_requirement_for_other_lib(self):
        reg = self._cut()
        testing_fixture_dir = resource_filename('deform_autoneed', 'testing_fixture')
        reg.libraries['deform_autoneed'] = Library('deform_autoneed', testing_fixture_dir)
        reg.create_requirement_for('something', 'deform_autoneed:testing_fixture/dummy.js',
                                   requirement_depends = ())
        self.assertIn('deform_autoneed', reg.libraries)

    def test_create_resource_with_new_lib(self):
        obj = self._cut()
        testing_fixture_dir = resource_filename('deform_autoneed', 'testing_fixture')
        library = Library('deform_autoneed', testing_fixture_dir)
        obj.create_resource('deform_autoneed:testing_fixture/dummy.js', library = library)
        self.assertIn('deform_autoneed', obj.libraries)

    def test_create_resource_with_existing_lib(self):
        obj = self._cut()
        testing_fixture_dir = resource_filename('deform_autoneed', 'testing_fixture')
        obj.libraries['deform_autoneed'] = library = Library('deform_autoneed', testing_fixture_dir)
        res = obj.create_resource('deform_autoneed:testing_fixture/dummy.js')
        self.assertEqual(res.library, library)

    def test_create_resource_already_existing_resource(self):
        obj = self._cut()
        testing_fixture_dir = resource_filename('deform_autoneed', 'testing_fixture')
        library = Library('deform_autoneed', testing_fixture_dir)
        res1 = obj.create_resource('deform_autoneed:testing_fixture/dummy.js', library = library)
        res2 = obj.create_resource('deform_autoneed:testing_fixture/dummy.js')
        self.assertEqual(res1, res2)

    def test_create_requirement_with_unknown_lib(self):
        obj = self._cut()
        self.assertRaises(KeyError, obj.create_requirement_for, 'something', 'unknown:hello/file.js')

    def test_populate_resource_registry(self):
        reg = self._cut()
        reg.populate_from_resources()
        self.assertIn('deform', reg.libraries)
        self.assertIn('jquery.form', reg.requirements)

    def test_resource_package_path(self):
        testing_lib = Library('deform_autoneed', 'testing_fixture')
        resource = Resource(testing_lib, 'dummy.js')
        obj = self._cut(libraries = {'deform_autoneed': testing_lib})
        obj.requirements['something'] = [resource]
        resource_path = 'deform_autoneed:testing_fixture/dummy.js'
        self.assertEqual(obj.resource_package_path(resource), resource_path)

    def test_resource_package_path_nonexistent(self):
        testing_lib = Library('deform_autoneed', 'testing_fixture')
        resource = Resource(testing_lib, 'dummy.js')
        obj = self._cut()
        self.assertRaises(KeyError, obj.resource_package_path, resource)

    def test_find_resource_abspath(self):
        obj = self._cut(add_basics = False)
        obj.create_requirement_for('something', 'css/beautify.css', requirement_depends = [])
        abspath = obj.requirements['something'][0].fullpath()
        res = obj.find_resource(abspath)
        self.assertIsInstance(res, Resource)
        self.assertEqual(res.fullpath(), abspath)

    def test_find_resource_relpath(self):
        obj = self._cut(add_basics = False)
        obj.create_requirement_for('something', 'css/beautify.css', requirement_depends = [])
        relpath = 'deform:static/css/beautify.css'
        res = obj.find_resource(relpath)
        self.assertIsInstance(res, Resource)

    def test_remove_resources(self):
        obj = self._cut()
        obj.create_requirement_for('something', 'css/beautify.css', requirement_depends = [])
        #Just to make sure the test works
        self.assertEqual(len(obj.requirements['something']), 1)
        self.assertIn('css/beautify.css', obj.libraries['deform'].known_resources)
        #Actual test
        obj.remove_resources('deform:static/css/beautify.css')
        self.assertEqual(len(obj.requirements['something']), 0)
        self.assertNotIn('css/beautify.css', obj.libraries['deform'].known_resources)

    def test_replace_resource_resource_objects(self):
        obj = self._cut()
        obj.libraries['deform_autoneed'] = library = Library('deform_autoneed', 'testing_fixture')
        resource_js = Resource(library, 'dummy.js')
        resource_css = Resource(library, 'dummy.css')
        obj.requirements['dummy'] = [resource_js]
        obj.replace_resource(resource_js, resource_css)
        self.assertEqual(obj.requirements['dummy'], [resource_css])

    def test_replace_resource_resource_paths(self):
        obj = self._cut()
        obj.libraries['deform_autoneed'] = library = Library('deform_autoneed', 'testing_fixture')
        resource_js = Resource(library, 'dummy.js')
        obj.requirements['dummy'] = [resource_js]
        obj.replace_resource('deform_autoneed:testing_fixture/dummy.js', 'deform_autoneed:testing_fixture/dummy.css')
        self.assertNotIn(resource_js, obj.requirements['dummy'])
        self.assertEqual(obj.requirements['dummy'][0].relpath, 'dummy.css')


class AutoNeedTests(TestCase):
    tearDown = _clearFLib

    def setUp(self):
        _clearFLib()
        self.reg = _mk_reg()
        self.reg.populate_from_resources()
        init_needed()

    def tearDown(self):
        _clearFLib()

    @property
    def _fut(self):
        from deform_autoneed import auto_need
        return auto_need

    def test_auto_need(self):
        form = _mk_richtext_form()
        self._fut(form, reg = self.reg)
        resources = get_needed().resources()
        self.assertIn('deform.js', [x.filename for x in resources])


class IntegrationTests(TestCase):
    tearDown = _clearFLib

    def setUp(self):
        _clearFLib()
        init_needed()

    def test_includeme(self):
        import deform_autoneed
        deform_autoneed.includeme()
        self.assertIn('jquery.form', deform_autoneed.resource_registry.requirements)

    def test_deform_integration_render(self):
        import deform_autoneed
        deform_autoneed.includeme()
        form = _mk_richtext_form()
        form.render()
        resources = get_needed().resources()
        self.assertIn('deform.js', [x.filename for x in resources])

    def test_deform_integration_exception_render(self):
        import deform_autoneed
        deform_autoneed.includeme()
        form = _mk_richtext_form()
        try:
            form.validate([('foo', 'bar')])
        except deform.ValidationFailure as exc:
            exc.render()
        resources = get_needed().resources()
        self.assertIn('deform.js', [x.filename for x in resources])
