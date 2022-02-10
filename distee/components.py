from typing import List, Optional, Dict

from .enums import ComponentType, ButtonStyle, TextInputType

########################################################################################################################
# BASE
########################################################################################################################


class BaseComponent:
    __slots__ = [
        'type'
    ]

    def __init__(self, _type: ComponentType):
        self.type: ComponentType = _type

    def to_json(self):
        return {'type': self.type.value}


class CustomIDComponent(BaseComponent):
    __slots__ = ['custom_id']

    def __init__(self, _type: ComponentType, custom_id: str):
        super(CustomIDComponent, self).__init__(_type)
        self.custom_id: str = custom_id

    def to_json(self):
        base = super(CustomIDComponent, self).to_json()
        base['custom_id'] = self.custom_id
        return base


########################################################################################################################
# IMPL
########################################################################################################################

class ActionRow(BaseComponent):
    __slots__ = [
        'components'
    ]
    
    def __init__(self, components: List[BaseComponent] = []):
        super(ActionRow, self).__init__(ComponentType.ACTION_ROW)
        self.components: List[BaseComponent] = components

    def to_json(self):
        base = super(ActionRow, self).to_json()
        base['components'] = [b.to_json() for b in self.components]
        return base


class Button(CustomIDComponent):

    __slots__ = [
        'disabled',
        'style',
        'label',
        'emoji',
        'url'
    ]

    def __init__(self,
                 custom_id: str,
                 disabled: bool = False,
                 style: ButtonStyle = ButtonStyle.PRIMARY,
                 label: str = None,
                 emoji: dict = None,
                 url: Optional[str] = None):
        super(Button, self).__init__(ComponentType.BUTTON, custom_id)
        self.disabled: bool = disabled
        self.style: ButtonStyle = style
        self.label: str = label
        self.emoji: Dict = emoji
        self.url: str = url

    def to_json(self):
        base = super(Button, self).to_json()
        base['disabled'] = self.disabled
        base['style'] = self.style.value
        if self.label is not None:
            base['label'] = self.label
        if self.emoji is not None:
            base['emoji'] = self.emoji
        if self.url is not None:
            base['url'] = self.url
        return base


class SelectOption:

    def __init__(self,
                 label: str,
                 value: str,
                 description: Optional[str] = None,
                 emoji: Optional[Dict] = None,
                 default: Optional[bool] = None):
        self.label = label
        self.value = value
        self.description = description
        self.emoji = emoji
        self.default = default

    def to_json(self):
        b = {
            'label': self.label,
            'value': self.value
        }
        if self.description is not None:
            b['description'] = self.description
        if self.emoji is not None:
            b['emoji'] = self.emoji
        if self.default is not None:
            b['default'] = self.default
        return b


class SelectMenu(CustomIDComponent):

    __slots__ = [
        'options',
        'disabled',
        'placeholder',
        'min_values',
        'max_values'
    ]

    def __init__(self,
                 custom_id: str,
                 options: List[SelectOption],
                 disabled: bool = False,
                 placeholder: str = None,
                 min_values: int = None,
                 max_values: int = None):
        super(SelectMenu, self).__init__(ComponentType.SELECT_MENU, custom_id)
        self.options = options
        self.disabled = disabled
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values

    def to_json(self):
        b = super(SelectMenu, self).to_json()
        b['options'] = [a.to_json() for a in self.options]
        b['disabled'] = self.disabled
        if self.placeholder is not None:
            b['placeholder'] = self.placeholder
        if self.min_values is not None:
            b['min_values'] = self.min_values
        if self.max_values is not None:
            b['max_values'] = self.max_values
        return b


class TextInput(CustomIDComponent):

    __slots__ = [
        'label',
        'style',
        'min_length',
        'max_length',
        'required',
        'value',
        'placeholder'
    ]
    
    def __init__(self,
                 custom_id: str,
                 label: str,
                 style: TextInputType = TextInputType.SHORT,
                 min_length: int = None,
                 max_length: int = None,
                 required: bool = None,
                 value: str = None,
                 placeholder: str = None):
        super(TextInput, self).__init__(ComponentType.TEXT_INPUT, custom_id)
        self.label = label
        self.style = style
        self.min_length = min_length
        self.max_length = max_length
        self.required = required
        self.value = value
        self.placeholder = placeholder

    def to_json(self):
        b = super(TextInput, self).to_json()
        b['label'] = self.label
        b['style'] = self.style.value
        if self.min_length is not None:
            b['min_length'] = self.min_length
        if self.max_length is not None:
            b['max_length'] = self.max_length
        if self.required is not None:
            b['required'] = self.required
        if self.value is not None:
            b['value'] = self.value
        if self.placeholder is not None:
            b['placeholder'] = self.placeholder
        return b


class Modal:

    __slots__ = [
        'custom_id',
        'title',
        'components'
    ]

    def __init__(self,
                 custom_id: str,
                 title: str,
                 components: List[BaseComponent]):
        self.custom_id = custom_id
        self.title = title
        self.components: components

    def to_json(self):
        return {
            'custom_id': self.custom_id,
            'title': self.title,
            'components': [c.to_json() for c in self.components]
        }
