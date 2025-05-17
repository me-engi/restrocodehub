# backend/restaurants/models.py
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
import uuid

# Import Tenant model from the 'users' app
# Ensure 'users' app is listed before 'restaurants' in INSTALLED_APPS if there are
# direct import dependencies at model definition time, or use string references.
from users.models import Tenant # Assuming users.models.Tenant is your defined Tenant model

class Restaurant(models.Model):
    """
    Represents a specific restaurant location or brand operated by a Tenant.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE, # If a Tenant is deleted, all their restaurants are deleted.
                                  # Consider models.PROTECT if restaurants should prevent tenant deletion
                                  # if they have, e.g., active orders or financial records.
        related_name='tenant_restaurants', # Allows tenant.tenant_restaurants.all()
        verbose_name=_("managing tenant")
    )

    name = models.CharField(_("restaurant name"), max_length=255,
                            help_text=_("The public display name of the restaurant location/brand."))
    slug = models.SlugField(_("restaurant slug"), max_length=270, unique=True, # Max length considers tenant slug + name
                            help_text=_("URL-friendly identifier, auto-generated."))
    description = models.TextField(_("description"), blank=True, null=True,
                                   help_text=_("A brief description of the restaurant."))

    # Contact Information
    phone_number = models.CharField(_("phone number"), max_length=30, blank=True, null=True)
    public_email = models.EmailField(_("public email address"), blank=True, null=True,
                                help_text=_("Email for customer inquiries, displayed publicly."))
    website_url = models.URLField(_("website URL"), blank=True, null=True)

    # Address Details
    address_line1 = models.CharField(_("address line 1"), max_length=255)
    address_line2 = models.CharField(_("address line 2"), max_length=255, blank=True, null=True)
    city = models.CharField(_("city"), max_length=100)
    state_province = models.CharField(_("state/province"), max_length=100, blank=True, null=True)
    postal_code = models.CharField(_("postal/zip code"), max_length=20)
    country = models.CharField(_("country"), max_length=100) # Could be a ForeignKey to a Country model

    # Geolocation (crucial for "nearby" searches)
    # For basic storage. For actual geospatial queries, you'd use GeoDjango's PointField
    # and a PostGIS backend. For now, these are simple decimal fields.
    latitude = models.DecimalField(_("latitude"), max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(_("longitude"), max_digits=10, decimal_places=7, null=True, blank=True)

    # Branding
    logo_image = models.ImageField(_("logo image"), upload_to='restaurants/logos/', blank=True, null=True)
    banner_image = models.ImageField(_("banner image"), upload_to='restaurants/banners/', blank=True, null=True)
    # Consider using a third-party library like django-imagekit for image processing (thumbnails, etc.)

    # Operational Status
    is_operational = models.BooleanField(
        _("is operational"), default=True, db_index=True,
        help_text=_("Is this restaurant currently open and accepting orders through the platform?")
    )
    # This flag can be controlled by Tenant Admins or Platform Admins.
    # Real-time open/closed status might be dynamic based on OpeningHours and POS data.

    # Placeholder for POS System specific info if needed at this level
    # pos_system_identifier = models.CharField(_("POS System ID"), max_length=100, blank=True, null=True,
    #                                          help_text=_("Identifier for this restaurant in an external POS system."))

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("restaurant")
        verbose_name_plural = _("restaurants")
        ordering = ['tenant', 'name']
        # A restaurant name should be unique within its tenant to avoid confusion for the tenant admin.
        # Global uniqueness for restaurant names might be too restrictive.
        unique_together = [['tenant', 'name'], ['tenant', 'slug']]

    def __str__(self):
        return f"{self.name} (Tenant: {self.tenant.name})"

    def save(self, *args, **kwargs):
        if not self.slug:
            # Create a unique slug based on tenant name and restaurant name
            base_slug_str = f"{self.tenant.name} {self.name}" if self.tenant else self.name
            base_slug = slugify(base_slug_str)
            slug = base_slug
            counter = 1
            while Restaurant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_full_address(self) -> str:
        """Returns a formatted full address string."""
        parts = [self.address_line1, self.address_line2, self.city, self.state_province, self.postal_code, self.country]
        return ", ".join(filter(None, parts))


class OperatingHoursRule(models.Model):
    """
    Defines a specific operating period for a restaurant on a given day.
    A restaurant can have multiple rules per day (e.g., for lunch and dinner shifts with a break).
    """
    DAY_CHOICES = [
        (0, _('Monday')), (1, _('Tuesday')), (2, _('Wednesday')),
        (3, _('Thursday')), (4, _('Friday')), (5, _('Saturday')), (6, _('Sunday')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='operating_hours_rules',
        verbose_name=_("restaurant")
    )
    day_of_week = models.PositiveSmallIntegerField(_("day of the week"), choices=DAY_CHOICES, db_index=True)
    open_time = models.TimeField(_("open time"))
    close_time = models.TimeField(_("close time"))
    is_closed_on_this_day_override = models.BooleanField(
        _("closed all day (override)"), default=False,
        help_text=_("If checked, this restaurant is closed for the entire selected day, ignoring open/close times.")
    )

    class Meta:
        verbose_name = _("operating hours rule")
        verbose_name_plural = _("operating hours rules")
        ordering = ['restaurant', 'day_of_week', 'open_time']
        # A restaurant shouldn't have overlapping time rules for the same day,
        # but validating this perfectly in the model can be complex.
        # Basic uniqueness:
        unique_together = [['restaurant', 'day_of_week', 'open_time', 'close_time']]

    def __str__(self):
        if self.is_closed_on_this_day_override:
            return f"{self.restaurant.name} - {self.get_day_of_week_display()}: Closed"
        return f"{self.restaurant.name} - {self.get_day_of_week_display()}: {self.open_time.strftime('%I:%M %p')} - {self.close_time.strftime('%I:%M %p')}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.is_closed_on_this_day_override and self.open_time and self.close_time:
            if self.close_time <= self.open_time: # Basic check, doesn't handle overnight
                raise ValidationError(_("Close time must be after open time for a single period."))
        # More complex validation for overlapping periods would go here or in the form/serializer.

class SpecialDayOverride(models.Model):
    """
    Defines special operating hours or closures for specific dates (e.g., holidays).
    Overrides OperatingHoursRule for that specific date.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='special_day_overrides',
        verbose_name=_("restaurant")
    )
    date = models.DateField(_("specific date"), unique_for_date="date", db_index=True,
                            help_text=_("The specific date this override applies to."))
    is_closed_all_day = models.BooleanField(_("closed all day"), default=False)
    open_time = models.TimeField(_("special open time"), null=True, blank=True,
                                 help_text=_("Leave blank if closed all day or using regular hours for this special day."))
    close_time = models.TimeField(_("special close time"), null=True, blank=True,
                                  help_text=_("Leave blank if closed all day or using regular hours for this special day."))
    reason = models.CharField(_("reason/description"), max_length=255, blank=True, null=True,
                              help_text=_("e.g., Christmas Day, Private Event, Staff Training"))

    class Meta:
        verbose_name = _("special day override")
        verbose_name_plural = _("special day overrides")
        ordering = ['restaurant', 'date']
        unique_together = [['restaurant', 'date']]

    def __str__(self):
        status = _("Closed") if self.is_closed_all_day else f"{self.open_time.strftime('%I:%M %p')} - {self.close_time.strftime('%I:%M %p')}" if self.open_time and self.close_time else _("Special Hours")
        return f"{self.restaurant.name} - {self.date.strftime('%Y-%m-%d')}: {status} ({self.reason or 'N/A'})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.is_closed_all_day:
            if self.open_time and not self.close_time:
                raise ValidationError(_("If open time is specified, close time is also required for special hours."))
            if not self.open_time and self.close_time:
                raise ValidationError(_("If close time is specified, open time is also required for special hours."))
            if self.open_time and self.close_time and self.close_time <= self.open_time:
                raise ValidationError(_("Special close time must be after special open time."))
        elif self.open_time or self.close_time: # If closed all day, open/close times should be null
            raise ValidationError(_("If marked as closed all day, open and close times should be blank."))

# Potentially in a new 'staff' app or even 'restaurants' app
# class StaffLocationAssignment(models.Model):
#     staff_user = models.ForeignKey('users.User', on_delete=models.CASCADE)
#     restaurant_location = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
#     role_at_location = models.CharField(max_length=100) # e.g., "Manager", "Chef Lead", "POS Operator"
#     # ... other permissions specific to this assignment ...
#
#     class Meta:
#         unique_together = [['staff_user', 'restaurant_location']]