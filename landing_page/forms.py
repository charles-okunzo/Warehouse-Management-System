from collections.abc import Mapping
from typing import Any

from django.core.files.base import File
from django.db.models.base import Model
from django.forms.utils import ErrorList
from .models import Product, Order, Customer, Supplier, ProductTransfers, Location
from django import forms
from django.contrib.contenttypes.models import ContentType


class ProductCreationForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
                "sku",
                "item_name",
                "quantity",
                "category",
                "location",
                "description",
                "product_image",
                  ]
    def __init__(self, *args, **kwargs):
        super(ProductCreationForm, self).__init__(*args, **kwargs)
        # Set the choices for location
        used_locations = Product.objects.exclude(location__isnull=True).values_list('location', flat=True)
        available_locations = Location.objects.exclude(id__in=used_locations)
        self.fields['location'].queryset = available_locations
        
class OrderCreationForm(forms.ModelForm):
    supplier = forms.ModelChoiceField(queryset=Supplier.objects.all(), required=False)
    customer = forms.ModelChoiceField(queryset=Customer.objects.all(), required=False)

    class Meta:
        model = Order
        exclude = ['associated_name', 'content_type', 'object_id']

    def __init__(self, *args, **kwargs):
          super(OrderCreationForm, self).__init__(*args, **kwargs)
          
          if self.instance.id:  # If order already exists
              if self.instance.order_type == "Purchase Orders":
                  self.fields['supplier'].initial = self.instance.associated_name
              else:
                  self.fields['customer'].initial = self.instance.associated_name

    def save(self, commit=True):
        instance = super(OrderCreationForm, self).save(commit=False)
        
        if instance.order_type == "Purchase Orders":
            supplier = self.cleaned_data['supplier']
            instance.associated_name = supplier
            instance.content_type = ContentType.objects.get_for_model(Supplier)
            instance.object_id = supplier.id if supplier else None

            product = self.cleaned_data['item']
            quantity = self.cleaned_data['total_items']
            product.add_inventory(quantity)
        else:
            customer = self.cleaned_data['customer']
            instance.associated_name = customer
            instance.content_type = ContentType.objects.get_for_model(Customer)
            instance.object_id = customer.id if customer else None
        
        if commit:
            instance.save()
        return instance
    #validate the Tota items field to ensure enough stock is available before placing orders.
    def clean(self):
        cleaned_data = super().clean()
        order_type = self.cleaned_data['order_type']
        if order_type == "Sales Orders":
            try:
                product = self.cleaned_data['item']
                quantity = self.cleaned_data['total_items']
                # Assuming the 'transfer' method raises ValueError if the condition fails
                product.remove_inventory(quantity)
            except ValueError as e:
                # Add a non-field error
                raise forms.ValidationError(str(e))
    
class CustomerCreationForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['cust_f_name', 'cust_l_name', 'email', 'mobile_no', 'address', 'notes']


class SupplierCreationForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['sup_f_name', 'sup_l_name', 'email', 'mobile_no', 'address', 'notes']

class TransferCreationForm(forms.ModelForm):
    class Meta:
        model = ProductTransfers
        fields = ['product', 'source_location', 'destination_location', 'quantity_transferred', 'reason']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Disable the source_location field
        self.fields['source_location'].widget.attrs['disabled'] = True
        self.fields['source_location'].widget.attrs['required'] = False
        used_locations = Product.objects.exclude(location__isnull=True).values_list('location', flat=True)
        available_locations = Location.objects.exclude(id__in=used_locations)
        self.fields['destination_location'].queryset = available_locations

    def clean(self):
        cleaned_data = super().clean()
        product = cleaned_data.get('product')
        
        # Auto-populate source_location if product is selected
        if product:
            cleaned_data['source_location'] = product.location

        destination_location = cleaned_data.get('destination_location')

        # Ensure that the destination location is not the same as the source location
        if destination_location == cleaned_data['source_location']:
            raise forms.ValidationError("Destination location cannot be the same as the source location.")

        return cleaned_data
    
class DeleteReasonForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea, label='Reason for Deleting')