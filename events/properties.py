
# http://appengine-cookbook.appspot.com/recipe/enumproperty

from google.appengine.ext import db

class EnumProperty(db.Property):
    """
    Maps a list of strings to be saved as int. The property is set or get using
    the string value, but it is stored using its index in the 'choices' list.
    """
    data_type = int

    def __init__(self, choices=None, **kwargs):
        if not isinstance(choices, list):
            raise TypeError('Choices must be a list.')
        super(EnumProperty, self).__init__(choices=choices, **kwargs)

    def get_value_for_datastore(self, model_instance):
        value = self.__get__(model_instance, model_instance.__class__)
        if value is not None:
            if isinstance(value, int):
                return value
            else:
                return int(self.choices.index(value))

    def make_value_from_datastore(self, value):
        if value is not None:
            try:
                return self.choices[int(value)]
            except ValueError, e:
                # something is wrong. simply return the value
                return value

    def make_value_from_form(self, value):
        try:
            return int(self.choices.index(value))
        except ValueError:
            if isinstance(value, int):
                return value
            else:
                return int(value)
 
    def empty(self, value):
        return value is None

    def validate(self, value):
        if self.empty(value):
            if self.required:
                raise BadValueError('Property %s is required' % self.name)
        elif not isinstance(value, int):
            if value not in self.choices:
                raise BadValueError('Property %s should be one of %s' % self.name, self.choices)
        else:
            if self.choices:
                if not (value in range(len(self.choices))):
                    raise BadValueError('Property %s should have value 0 to %d' % (self.name, len(self.choices)))
        if self.validator is not None:
            self.validator(value)
        return value
