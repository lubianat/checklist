from django import forms
from django.utils.text import slugify

from .models import Catalog, VisitingList


class CatalogForm(forms.ModelForm):
    class Meta:
        model = Catalog
        fields = ["name", "slug", "description", "query"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "query": forms.Textarea(attrs={"rows": 6}),
        }
        labels = {
            "name": "Catalog name",
            "slug": "Catalog alias",
            "description": "Catalog description",
            "query": "Catalog query",
        }
        help_texts = {
            "slug": "Shareable alias used in the URL. Leave blank to auto-generate.",
            "query": "Return ?item. Optional: ?itemLabel, ?itemDescription, ?image, ?coord.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False

    def clean_slug(self):
        slug = (self.cleaned_data.get("slug") or "").strip()
        if not slug:
            slug = (self.cleaned_data.get("name") or "").strip()
        slug = slugify(slug)
        max_length = self.fields["slug"].max_length
        if max_length:
            slug = slug[:max_length]
        if not slug:
            raise forms.ValidationError("Provide a catalog name or alias.")
        if Catalog.objects.filter(slug__iexact=slug).exists():
            raise forms.ValidationError("This alias is already taken.")
        return slug

    def clean_query(self):
        query = (self.cleaned_data.get("query") or "").strip()
        if "?item" not in query:
            raise forms.ValidationError("Query must reference ?item.")
        return query
