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

    def test_create_requirement_for_deform_1_style(self):
        reg = self._cut(add_basics = False)
        from deform_autoneed import deform_autoneed_lib
        print deform_autoneed_lib.known_resources
        reg.create_requirement_for('something', 'css/form.css', depends = [])
        self.assertIn('something', reg.requirements)
        self.assertIn('css/form.css', reg.paths)        
 
    def test_create_requirement_for_deform_2_style(self):
        reg = self._cut()
        reg.create_requirement_for('something', 'deform:static/css/form.css', depends = [])
        self.assertIn('something', reg.requirements)
        self.assertIn('deform:static/css/form.css', reg.paths)        
 
    def test_create_requirement_for_other_lib(self):
        reg = self._cut()
        testing_fixture_dir = resource_filename('deform_autoneed', 'testing_fixture')
        reg.libraries['other'] = Library('other', testing_fixture_dir)
        reg.create_requirement_for('something', 'other:testing_fixture/dummy.js',
                                   remove_leading = 'testing_fixture/', depends = ())
        self.assertIn('other', reg.libraries)

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
