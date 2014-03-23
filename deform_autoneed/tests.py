from unittest import TestCase

import deform
import colander
from fanstatic import Library
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
        reg.create_requirement_for('something', 'css/beautify.css', depends = [])
        self.assertIn('css/beautify.css', reg.libraries['deform'].known_resources)

    def test_create_requirement_for_deform_2_style(self):
        reg = self._cut()
        reg.create_requirement_for('something', 'deform:static/css/beautify.css', depends = [])
        self.assertIn('something', reg.requirements)
        self.assertIn('css/beautify.css', reg.libraries['deform'].known_resources)
 
    def test_create_requirement_for_other_lib(self):
        reg = self._cut()
        testing_fixture_dir = resource_filename('deform_autoneed', 'testing_fixture')
        reg.libraries['deform_autoneed'] = Library('deform_autoneed', testing_fixture_dir)
        reg.create_requirement_for('something', 'deform_autoneed:testing_fixture/dummy.js',
                                   depends = ())
        self.assertIn('deform_autoneed', reg.libraries)

    def test_create_requirement_with_unknown_lib(self):
        obj = self._cut()
        self.assertRaises(KeyError, obj.create_requirement_for, 'something', 'unknown:hello/file.js')

    def test_populate_resource_registry(self):
        reg = self._cut()
        reg.populate_from_resources()
        self.assertIn('deform', reg.libraries)
        self.assertIn('jquery.form', reg.requirements)


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
