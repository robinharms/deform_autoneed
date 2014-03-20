from unittest import TestCase

import deform
import colander


def _mk_richtext_form():
    class Schema(colander.Schema):
        richtext = colander.SchemaNode(colander.String(),
                                       widget = deform.widget.RichTextWidget())
    return deform.Form(Schema())


class PopulateResourceRegistryTests(TestCase):

    @property
    def _fut(self):
        from deform_autoneed import populate_resource_registry
        return populate_resource_registry


class AutoCreateTests(TestCase):

    @property
    def _fut(self):
        from deform_autoneed import auto_create
        return auto_create

    def test_auto_create_richtext(self):
        form = _mk_richtext_form()
        self._fut(form)
