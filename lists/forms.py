from django import forms
from django.utils.text import slugify

from .models import Catalog, VisitingList
from .services import generate_sparql_query


class SimpleCatalogForm(forms.Form):
    """Simplified catalog creation form with Wikidata autocomplete."""
    item_type_id = forms.CharField(
        max_length=20,
        label="What is the catalog about?",
        help_text="e.g., churches, parks, museums",
        widget=forms.HiddenInput(attrs={"class": "autocomplete-value"}),
    )
    item_type_label = forms.CharField(
        max_length=200,
        required=True,
        label="",
        widget=forms.TextInput(attrs={
            "class": "autocomplete-input",
            "placeholder": "Start typing (e.g., church, museum, park)...",
            "data-target": "item_type_id",
        }),
    )
    location_id = forms.CharField(
        max_length=20,
        label="Where are these items found?",
        help_text="e.g., Brazil, Germany, Europe, São Paulo",
        widget=forms.HiddenInput(attrs={"class": "autocomplete-value"}),
    )
    location_label = forms.CharField(
        max_length=200,
        required=True,
        label="",
        widget=forms.TextInput(attrs={
            "class": "autocomplete-input",
            "placeholder": "Start typing a location (e.g., Brazil, São Paulo)...",
            "data-target": "location_id",
        }),
    )
    
    name = forms.CharField(
        max_length=200,
        label="Catalog name",
        help_text="Optional - will be auto-generated if left blank",
        required=False,
    )
    
    slug = forms.SlugField(
        max_length=80,
        label="Catalog alias",
        help_text="Optional - will be auto-generated if left blank",
        required=False,
    )
    
    def clean_item_type_id(self):
        item_type_id = self.cleaned_data.get("item_type_id", "").strip()
        if not item_type_id:
            raise forms.ValidationError("Please select what the catalog is about.")
        return item_type_id
    
    def clean_location_id(self):
        location_id = self.cleaned_data.get("location_id", "").strip()
        if not location_id:
            raise forms.ValidationError("Please select where these items are found.")
        return location_id
    
    def clean_slug(self):
        slug = self.cleaned_data.get("slug", "").strip()
        if not slug:
            # Auto-generate from name or type/location labels
            name = self.cleaned_data.get("name", "").strip()
            if name:
                slug = slugify(name)
            else:
                type_label = self.cleaned_data.get("item_type_label", "").strip()
                location_label = self.cleaned_data.get("location_label", "").strip()
                if type_label and location_label:
                    slug = slugify(f"{type_label} {location_label}")
        
        if slug:
            max_length = 80
            slug = slug[:max_length]
            if Catalog.objects.filter(slug__iexact=slug).exists():
                raise forms.ValidationError("This alias is already taken.")
        
        if not slug:
            raise forms.ValidationError("Provide a catalog name or alias.")
        
        return slug
    
    def get_catalog_name(self):
        """Generate catalog name from type and location labels."""
        name = self.cleaned_data.get("name", "").strip()
        if name:
            return name
        
        type_label = self.cleaned_data.get("item_type_label", "").strip()
        location_label = self.cleaned_data.get("location_label", "").strip()
        
        if type_label and location_label:
            return f"{type_label.capitalize()} in {location_label}"
        return "Unnamed catalog"
    
    def get_catalog_description(self):
        """Generate catalog description from type and location labels."""
        type_label = self.cleaned_data.get("item_type_label", "").strip()
        location_label = self.cleaned_data.get("location_label", "").strip()
        
        if type_label and location_label:
            return f"All {type_label} in {location_label}."
        return ""
    
    def get_sparql_query(self):
        """Generate SPARQL query from selected entities."""
        item_type_id = self.cleaned_data.get("item_type_id")
        location_id = self.cleaned_data.get("location_id")
        return generate_sparql_query(item_type_id, location_id)


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
