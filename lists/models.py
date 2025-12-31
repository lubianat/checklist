from django.contrib.auth.models import User
from django.db import models


class Catalog(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=80, unique=True)
    description = models.TextField(blank=True)
    query = models.TextField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="catalogs",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.slug})"


class VisitingList(models.Model):
    id = models.BigAutoField(primary_key=True)
    catalog = models.ForeignKey(
        Catalog,
        on_delete=models.CASCADE,
        related_name="lists",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="visiting_lists",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("catalog", "created_by")

    def __str__(self):
        return f"{self.catalog.name} ({self.created_by.username})"


class VisitingPlace(models.Model):
    catalog = models.ForeignKey(
        Catalog,
        on_delete=models.CASCADE,
        related_name="places",
    )
    entity_id = models.CharField(max_length=32, db_index=True)
    label = models.TextField(blank=True)
    description = models.TextField(blank=True)
    image = models.TextField(blank=True)
    coord = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("catalog", "entity_id")

    def __str__(self):
        return f"{self.entity_id} ({self.catalog.name})"


class PassportStamp(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="passport_stamps",
    )
    place = models.ForeignKey(
        VisitingPlace,
        on_delete=models.CASCADE,
        related_name="stamps",
    )

    class Meta:
        unique_together = ("user", "place")

    def __str__(self):
        return f"{self.user} -> {self.place.entity_id}"
