from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import ProductCreationForm, OrderCreationForm, CustomerCreationForm, SupplierCreationForm, TransferCreationForm, DeleteReasonForm
from .models import Product, Order, Customer, Supplier, ProductTransfers, Location
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.views.generic.edit import UpdateView, DeleteView
from django.urls import reverse_lazy
from django.views.generic import DetailView, CreateView, ListView
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from .utils import import_from_excel, import_customer, import_supplier, get_source_location_for_product


# Create your views here.



def landing_page(request):
    return render(request, "landing_page/index.html")

@login_required
def dashboard(request):
    inventory = Product.objects.all()
    pending = Order.objects.filter(status = 'Pending')
    transit = Order.objects.filter(status = 'GIT')
    all_orders = Order.objects.all()
    all_customers = Customer.objects.all()
    all_suppliers = Supplier.objects.all()
    context = {
        "inventory":inventory,
        "pending":pending,
        "transit":transit,
        'all_orders':all_orders,
        'all_customers':all_customers,
        'all_suppliers':all_suppliers
    }
    return render(request, 'landing_page/dashboard.html', context)

@login_required
def products(request):
    if request.method == "POST":
        product_form = ProductCreationForm(request.POST, request.FILES)
        if product_form.is_valid():
            product_form.instance.user = request.user
            product_form.save()
            messages.success(request, f'Product Added Successfully!')
            return redirect('products')
    else:
        product_form = ProductCreationForm()
        
    products = Product.objects.all().order_by('-pk')

    paginator_prods = Paginator(products, 8)
    page_number = request.GET.get('page')
    products_page = paginator_prods.get_page(page_number)
    context = {
        "product_form": product_form,
        "products": products,
        "products_page":products_page
    }

    return render(request, 'landing_page/products.html', context)

def softdelete_product(request, product_id):
    product = get_object_or_404(Product, pk=product_id)

    if request.method == "POST":
        form = DeleteReasonForm(request.POST)
    
        if form.is_valid():
            reason = form.cleaned_data.get('reason')
            product.delete(reason, user=request.user)
            messages.success(request, f'Item deleted successfully!')
            return redirect('products')
    else:
        form = DeleteReasonForm()
    
    return render(request, 'landing_page/confirm_softdelete.html', {'form':form, 'product':product})

def restore_product(request, product_id):
    product = Product.objects.deleted().get(pk=product_id)
    product.restore()
    messages.success(request, f'Product Restored')
    return redirect('trash-list')

def permanently_delete_product(request, pk):
    product = Product.objects.deleted().get(pk=pk)
    product.permanently_delete()
    messages.success(request, f'Product Permenently deleted')
    return redirect('trash-list')

def deleted_items_lists(request):
    products = Product.objects.deleted()
    paginator_prods = Paginator(products, 8)
    page_number = request.GET.get('page')
    products_page = paginator_prods.get_page(page_number)

    context = {
        "products": products,
        "products_page":products_page
    }
    return render(request, 'landing_page/trash.html', context)


@login_required
def orders(request):
    if request.method == "POST":
        # in_order_form = OrderCreationForm(request.POST)
        # out_order_form = OrderCreationForm(request.POST)
        order_form = OrderCreationForm(request.POST)
        # if in_order_form.is_valid():
        #     in_order_form.instance.order_type = 'Inbound'
        #     in_order_form.save()
            
        #     messages.success(request, f'Order Added Successfully!')
        #     return redirect('orders')
        # elif out_order_form.is_valid():
        #     out_order_form.instance.order_type = 'Outbound'
        #     out_order_form.save()
        if order_form.is_valid():
            # order_type = order_form.cleaned_data['order_type']
            # if order_type == "Inbound":
            #     product = order_form.cleaned_data['item']
            #     quantity = order_form.cleaned_data['total_items']
            #     product.add_inventory(quantity)
            # else:
            #     try:
            #         product = order_form.cleaned_data['item']
            #         quantity = order_form.cleaned_data['total_items']
            #         # Assuming the 'transfer' method raises ValueError if the condition fails
            #         product.remove_inventory(quantity)
            #     except ValueError as e:
            #         # Add a non-field error
            #         order_form.add_error(None, str(e))
                # print(order_form.cleaned_data)
            order_form.save()

            messages.success(request, f'Order Added Successfully!')
            return redirect('orders')

    else:
        # in_order_form = OrderCreationForm()
        # out_order_form = OrderCreationForm()
        order_form = OrderCreationForm()
    #Inbound orders == Purchase Orders
    #Outbound Orders == Sales Orders
    inbound_orders = Order.objects.filter(order_type = 'Purchase Orders')
    outbound_orders = Order.objects.filter(order_type = 'Sales Orders')
    paginator_inbound = Paginator(inbound_orders, 8)
    page_number_in = request.GET.get('page')
    customers_page_in = paginator_inbound.get_page(page_number_in)

    paginator_outbound = Paginator(outbound_orders, 8)
    page_number_out = request.GET.get('page')
    customers_page_out = paginator_outbound.get_page(page_number_out)
    context = {
        # "in_order_form": in_order_form,
        # "out_order_form": out_order_form,
        "order_form":order_form,
        "inbound_orders": inbound_orders,
        "outbound_orders":outbound_orders,
        "customers_page_in":customers_page_in,
        "customers_page_out":customers_page_out
    }

    return render(request, 'landing_page/orders.html', context)

@login_required
def customers(request):
    if request.method == "POST":
        customer_form = CustomerCreationForm(request.POST)
        if customer_form.is_valid():
            customer_form.save()
            messages.success(request, f'Customer Added Successfully!')
            return redirect('customers')
    else:
        customer_form = CustomerCreationForm()
        customers = Customer.objects.all()

        paginator = Paginator(customers, 8)
        page_number = request.GET.get('page')
        customers_page = paginator.get_page(page_number)
    context = {
        "customer_form": customer_form,
        "customers":customers,
        "customers_page": customers_page
    }

    return render(request, 'landing_page/customers.html', context)

@login_required
def suppliers(request):
    if request.method == "POST":
        suppliers_form = SupplierCreationForm(request.POST)
        if suppliers_form.is_valid():
            suppliers_form.save()
            messages.success(request, f'Supplier Added Successfully!')
            return redirect('suppliers')
    else:
        suppliers_form = SupplierCreationForm()
        suppliers = Supplier.objects.all()

        paginator = Paginator(suppliers, 8)
        page_number = request.GET.get('page')
        suppliers_page = paginator.get_page(page_number)
    context = {
        "supplier_form": suppliers_form,
        "suppliers":suppliers,
        "suppliers_page": suppliers_page
    }

    return render(request, 'landing_page/suppliers.html', context)

class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    template_name = 'landing_page/product_update.html'
    fields = [ "sku", "item_name", "quantity", "category", "location", "description", "product_image",]
    success_url = reverse_lazy('products')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'Item edited successfully!')
        return super().form_valid(form)
    
# class ProductDeleteView(LoginRequiredMixin, DeleteView):
#     model = Product
#     template_name = 'landing_page/product_delete.html'
#     success_url = reverse_lazy('trash-list')

#     def form_valid(self, form):
#         messages.success(self.request, f'Item permanently deleted!')
#         return super().form_valid(form)
#     def get_queryset(self):
#         queryset = super().get_queryset()
#         return queryset.filter(pk=self.kwargs.get('pk'))

class OrderUpdateView(LoginRequiredMixin, UpdateView):
    model = Order
    template_name = 'landing_page/order_update.html'
    fields = [ "order_id", "item", "order_type", "total_items", "status", "notes"]
    success_url = reverse_lazy('orders')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'Order edited successfully!')
        return super().form_valid(form)
    
class OrderDeleteView(LoginRequiredMixin, DeleteView):
    model = Order
    template_name = 'landing_page/order_delete.html'
    success_url = reverse_lazy('orders')

    def form_valid(self, form):
        messages.success(self.request, f'Order deleted successfully!')
        return super().form_valid(form)
    

class SupplierUpdateView(LoginRequiredMixin, UpdateView):
    model = Supplier
    template_name = 'landing_page/supplier_update.html'
    fields = ['sup_f_name', 'sup_l_name', 'email', 'mobile_no', 'address', 'notes']
    success_url = reverse_lazy('suppliers')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'Supplier details edited successfully!')
        return super().form_valid(form)
    
class SupplierDeleteView(LoginRequiredMixin, DeleteView):
    model = Supplier
    template_name = 'landing_page/supplier_delete.html'
    success_url = reverse_lazy('suppliers')

    def form_valid(self, form):
        messages.success(self.request, f'Suppliers details deleted successfully!')
        return super().form_valid(form)
    
class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model = Customer
    template_name = 'landing_page/customer_update.html'
    fields = ['cust_f_name', 'cust_l_name', 'email', 'mobile_no', 'address', 'notes']
    success_url = reverse_lazy('customers')

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f'Customer details edited successfully!')
        return super().form_valid(form)
    
class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    template_name = 'landing_page/customer_delete.html'
    success_url = reverse_lazy('customers')

    def form_valid(self, form):
        messages.success(self.request, f'Customers details deleted successfully!')
        return super().form_valid(form)
    
class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'landing_page/order_detail.html'
    context_object_name = 'order_detail'


def reports(request):
    today = timezone.localdate()
    todays_inventory = Product.objects.filter(item_created_at__date=today)
    pending = Order.objects.filter(status = 'Pending')
    recent_shipments = Order.objects.filter(status = 'GIT', order_created_at__date = today)

    context = {
        'today':today,
        'todays_inventory':todays_inventory,
        'pending':pending,
        'recent_shipments':recent_shipments
    }
    return render(request, 'landing_page/reports.html', context)

def inventory_report(request):
    today = timezone.localdate()
    todays_inventory = Product.objects.filter(item_created_at__date=today)
    pending = Order.objects.filter(status = 'Pending')
    recent_shipments = Order.objects.filter(status = 'GIT', order_created_at__date = today)
    context = {
        'today':today,
        'todays_inventory':todays_inventory,
        'pending':pending,
        'recent_shipments':recent_shipments
    }
    return render(request, 'reports/inventory_report.html',context)

def pendingorder_report(request):
    today = timezone.localdate()
    pending = Order.objects.filter(status = 'Pending')
    context = {
        'today':today,
        'pending':pending,
    }
    return render(request, 'reports/pending_orders.html',context)

def recentshipments_report(request):
    today = timezone.localdate()
    recent_shipments = Order.objects.filter(status = 'GIT', order_created_at__date = today)
    context = {
        'today':today,
        'recent_shipments':recent_shipments
    }
    return render(request, 'reports/recent_shipments_reports.html', context)

class ProductDetailsView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'landing_page/product_detail.html'
    context_object_name = 'product_detail'

def get_source_location(request, product_id):
    # Logic to get the source location for the given product
    source_location = get_source_location_for_product(product_id)
    return JsonResponse({'source_location_id': source_location.id})

class TransferCreateView(LoginRequiredMixin, CreateView):
    model = ProductTransfers
    template_name = 'landing_page/transfers.html'
    form_class = TransferCreationForm
    success_url = reverse_lazy('transfers-list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.save()
        
        try:
            product = form.cleaned_data['product']
            quantity = form.cleaned_data['quantity_transferred']
            # Assuming the 'transfer' method raises ValueError if the condition fails
            # product.transfer(quantity)
            messages.success(self.request, f'Product transfer recorded successfully!')
            return super().form_valid(form)
        except ValueError as e:
            # Add a non-field error
            form.add_error(None, str(e))
            return super().form_invalid(form)
        

class TransfersListsView(LoginRequiredMixin, ListView):
    model = ProductTransfers
    template_name = 'landing_page/transfer_list.html'
    context_object_name = 'transfer_list'

def scanner(request):
    return render(request, "landing_page/scan.html")

class LocationCreateView(LoginRequiredMixin, CreateView):
    model = Location
    template_name = "landing_page/location.html"
    fields = ['zone', 'row', 'bay', 'tier']
    success_url = reverse_lazy('transfers-list')

    def form_valid(self, form):
        form.save()

        messages.success(self.request, f'Location Added successfully!')
        return super().form_valid(form)
    

def excel_import(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        
        
        if not excel_file:
            messages.error(request, 'No file provided!', 'danger')
        
        try:
            user = request.user
            import_from_excel(excel_file, user)
            messages.success(request, 'Inventory uploaded successfully.')

        except ValueError as e:
            # Return a user-friendly error message or redirect
            messages.error(request, e, 'danger')
            # return HttpResponseBadRequest(f"Error processing file: {e}")
            return redirect('excel_import')
        except Exception as e:
            # For any other exception, return a server error
            messages.error(request, e, 'danger')
            return redirect('excel_import')
        
        
        return redirect('products')
    
    return render(request, 'imports/excel_import.html')

def customer_import(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('customer_file')

        if not excel_file:
            # return HttpResponseBadRequest('No file provided!')
            messages.error(request, 'No file provided!', 'danger')
            
        
        try:
            import_customer(excel_file)
            messages.success(request, 'Customer(s) uploaded successfully.')
        except ValueError as e:
            # Return a user-friendly error message or redirect
            messages.error(request, e, 'danger')
            # return HttpResponseBadRequest(f"Error processing file: {e}")
            return redirect('customer_import')
        except Exception as e:
            # For any other exception, return a server error
            messages.error(request, e, 'danger')
            return redirect('customer_import')
        
        
        return redirect('customers')
    
    return render(request, 'imports/customers_import.html')

def supplier_import(request):
    if request.method == 'POST':
        excel_file = request.FILES.get('supplier_file')

        if not excel_file:
            # return HttpResponseBadRequest('No file provided!')
            messages.error(request, 'No file provided!', 'danger')
            
        
        try:
            import_supplier(excel_file)
            messages.success(request, 'Supplier(s) uploaded successfully.')
        except ValueError as e:
            # Return a user-friendly error message or redirect
            messages.error(request, e, 'danger')
            # return HttpResponseBadRequest(f"Error processing file: {e}")
            return redirect('supplier_import')
        except Exception as e:
            # For any other exception, return a server error
            messages.error(request, e, 'danger')
            return redirect('supplier_import')
        
        
        return redirect('suppliers')
    
    return render(request, 'imports/suppliers_import.html')

