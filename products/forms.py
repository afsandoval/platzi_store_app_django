from django import forms

class ProductForm(forms.Form):
    title       = forms.CharField(max_length=255, label='Título')
    price       = forms.DecimalField(max_digits=10, decimal_places=2, label='Precio')
    description = forms.CharField(widget=forms.Textarea, label='Descripción')
    category    = forms.ChoiceField(label='Categoría')
    image       = forms.URLField(label='URL de la imagen')

    def __init__(self, *args, categories=None, **kwargs):
        super().__init__(*args, **kwargs)
        # categories viene como lista de tuplas (id, nombre)
        if categories:
            self.fields['category'].choices = categories
