from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType
from django.db.models.query import QuerySet
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image, ImageDraw
import datetime

# Create your models here.

def generate_qr_code(data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer)
    filename = f'{data}-qr.png'
    filebuffer = File(buffer, name=filename)
    return filebuffer
class Location(models.Model):
    ZONE_CHOICES = [
    ('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'),
    ('F', 'F'), ('G', 'G'), ('H', 'H'), ('I', 'I'), ('J', 'J'),
    ('K', 'K'), ('L', 'L'), ('M', 'M'), ('N', 'N'), ('O', 'O'),
    ('P', 'P'), ('Q', 'Q'), ('R', 'R'), ('S', 'S'), ('T', 'T'),
    ('U', 'U'), ('V', 'V'), ('W', 'W'), ('X', 'X'), ('Y', 'Y'),
    ('Z', 'Z')
    ]

    CHOICES = [
    (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'),
    (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')
    ]



    zone = models.CharField(max_length=1, choices=ZONE_CHOICES)
    row = models.PositiveIntegerField(choices=CHOICES)
    bay = models.PositiveIntegerField(choices=CHOICES)
    tier = models.PositiveIntegerField(choices=CHOICES)

    def __str__(self):
        return f"{self.zone}, {self.row}, {self.bay}, {self.tier}"
    
class ProductManager(models.Manager):
    def get_queryset(self) -> QuerySet:
        return super().get_queryset().filter(is_deleted = False)
    
    def deleted(self):
        return super().get_queryset().filter(is_deleted = True)

class Product(models.Model):
    unit_choices = [
        ("milligrams", "milligrams"),
        ("grams", "grams"),
        ("Kilograms", "Kilograms"),
        ("millilitres", "millilitres"),
        ("Litres", "Litres"),
        ("metres", "metres"),
        ("Units", "Units")
    ]
    nature_choices = [
        ("Purchase", "Purchase"),
        ("Return", "Return"),
        ("Transfer", "Transfer"),
        ("Reject", "Reject")
    ]
    category_choices = [
        ("Grocery", "Grocery"),
        ("Stationery", "Stationery"),
        ("Furniture", "Furniture"),
        ("Jewellery", "Jewellery"),
        ("Clothing", "Clothing"),
        ("Electronic", "Electronic")
    ]
    sku = models.CharField(verbose_name = "Stock Keeping Unit", max_length=50, unique=True) #Stock Keeping Unit
    item_name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=50, choices=category_choices)
    quantity = models.PositiveIntegerField()
    description = models.TextField(blank=True)
    location = models.ForeignKey(Location, verbose_name=" Available Locations(Zone, Row, Bay, Tier)", related_name="product_location", on_delete=models.SET_NULL, null=True, blank=True)
    product_image = models.ImageField("product_images", default="No-image-found.jpg")
    user = models.ForeignKey(User, related_name="created_by", on_delete=models.CASCADE)
    item_created_at = models.DateTimeField(auto_now_add=True)
    item_updated_at = models.DateTimeField(auto_now=True)
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True)

    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    reason_for_deleting = models.TextField(null=True, blank=True)
    objects = ProductManager()

    class Meta:
        unique_together = ('item_name', 'location')

    def __str__(self):
        return f'{self.sku} - {self.item_name}'
    
    def delete(self, reason='', user=None, *args, **kwargs):
        self.is_deleted = True
        self.deleted_at = datetime.datetime.now()
        self.reason_for_deleting = reason
        self.deleted_by = user
        self.save()

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.reason_for_deleting = ''
        self.deleted_by=None
        self.save()

    def permanently_delete(self):
        self.delete()

    def save(self, *args, **kwargs):
        super().save()

        img = Image.open(self.product_image.path)

        if img.height > 300 or img.width > 300:
            output_size = (300, 300)
            img.thumbnail(output_size)
            img.save(self.product_image.path)
        
        if not self.qr_code:
            # Generate a simple table in Python string format with two columns and seven rows.

            table_data = [
                ('SKU', self.sku),
                ('Product Name', self.item_name),
                ('Quantity', self.quantity),
                ('Category', self.category),
                ('Location', self.location),
                ('Description', self.description),
            ]

            # Create a table string
            data = 'Product Details\n' + \
                        '\n'.join('{} \t- {} \t'.format(row[0], row[1]) for row in table_data)
            #saves a qr image with encorded instance data
            # data = f"{self.sku} {self.item_name} {self.quantity} {self.category}"  # This should be the data unique to each instance
            self.qr_code = generate_qr_code(data)
        super().save(*args, **kwargs)
    
    def transfer(self, quantity):
        if quantity <= self.quantity:
            self.quantity -= quantity
            self.save()
        else:
            raise ValueError("Transferred quantity exceeds available quantity.")
    def add_inventory(self, quantity):
        self.quantity += quantity
        self.save()

    def remove_inventory(self, quantity):
        if quantity <= self.quantity:
            self.quantity -= quantity
            self.save()
        else:
            raise ValueError(f"Insufficient Stock! Only {self.quantity} units available.")

class ProductTransfers(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    source_location = models.ForeignKey(Location, related_name='transfers_from', on_delete=models.CASCADE, blank=True)
    destination_location = models.ForeignKey(Location, related_name='transfers_to', on_delete=models.CASCADE)
    quantity_transferred = models.PositiveIntegerField()
    transfer_date = models.DateTimeField(auto_now_add=True)
    reason = models.TextField(default='Hello')
    user = models.ForeignKey(User, related_name='transfers_made', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product.item_name} from {self.source_location} to {self.destination_location}"
    
    def save(self, *args, **kwargs):
        if not self.pk:  # Check if this is a new instance
            # Set the source_location based on the selected product
            self.source_location = self.product.source_location

        super().save(*args, **kwargs)


class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ("Purchase Orders", "Purchase Orders"),
        ("Sales Orders", "Sales Orders")
    ]
    order_id = models.CharField(verbose_name='Order ID', max_length=50, unique=True)
    order_created_at = models.DateTimeField(auto_now_add=True)
    order_updated_at = models.DateTimeField(auto_now=True)
    item = models.ForeignKey(Product, related_name= "ordered_item", on_delete=models.CASCADE)
    total_items = models.PositiveIntegerField(verbose_name='Total Items')
    order_type = models.CharField(verbose_name='Order Type', blank=True, choices=ORDER_TYPE_CHOICES)
    status = models.CharField(verbose_name='Status', choices=[('Pending', 'Pending'), ('Processing', 'Processing'), ('GIT', 'GIT'), ('Completed', 'Completed')])
    notes = models.TextField(verbose_name='Notes', blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    associated_name = GenericForeignKey('content_type', 'object_id')

    def __str__(self) -> str:
        return f'Order no: {self.order_id}'


class Customer(models.Model):
    cust_f_name = models.CharField(verbose_name='First Name', max_length=100)
    cust_l_name = models.CharField(verbose_name='Last Name', max_length=100)
    orders = GenericRelation(Order)
    email = models.EmailField(verbose_name='Email Address', max_length=50, unique=True)
    mobile_no = models.PositiveIntegerField(verbose_name='Mobile No. e.g., 254712345678', blank=True, null=True)
    address = models.TextField(verbose_name='Address', blank=True)
    notes = models.TextField(verbose_name='Notes', blank=True)

    def __str__(self) -> str:
        return f'{self.cust_f_name} {self.cust_l_name}'

class Supplier(models.Model):
    sup_f_name = models.CharField(verbose_name='First Name', max_length=100)
    sup_l_name = models.CharField(verbose_name='Last Name', max_length=100)
    orders = GenericRelation(Order)
    email = models.EmailField(verbose_name='Email Address', blank=True, max_length=50, unique=True)
    mobile_no = models.PositiveIntegerField(verbose_name='Mobile No. e.g., 254712345678', blank=True, null=True)
    address = models.TextField(verbose_name='Address', blank=True)
    notes = models.TextField(verbose_name='Notes', blank=True)

    def __str__(self) -> str:
        return f'{self.sup_f_name} {self.sup_l_name}'