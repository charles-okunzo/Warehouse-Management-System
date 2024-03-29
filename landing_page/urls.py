from django.urls import path
from . import views
from .views import ProductUpdateView, OrderUpdateView,OrderDeleteView, SupplierUpdateView, SupplierDeleteView, CustomerUpdateView, CustomerDeleteView, OrderDetailView, ProductDetailsView, TransferCreateView, TransfersListsView, LocationCreateView

urlpatterns = [
    path('', views.landing_page, name="landing-page"),
    path('dashboard/', views.dashboard, name="dashboard"),
    path('products/', views.products, name="products"),
    path('orders/', views.orders, name="orders"),
    path('customers/', views.customers, name="customers"),
    path('suppliers/', views.suppliers, name="suppliers"),
    path('product/<int:pk>/edit/', ProductUpdateView.as_view(), name="products-update"),
    # path('product/<int:pk>/delete/', ProductDeleteView.as_view(), name="product-delete"),
    path('product/<int:pk>/delete/', views.permanently_delete_product, name="product-delete"),
    path('order/<int:pk>/edit/', OrderUpdateView.as_view(), name="orders-update"),
    path('order/<int:pk>/delete/', OrderDeleteView.as_view(), name="order-delete"),
    path('supplier/<int:pk>/edit/', SupplierUpdateView.as_view(), name="suppliers-update"),
    path('supplier/<int:pk>/delete/', SupplierDeleteView.as_view(), name="supplier-delete"),
    path('customer/<int:pk>/edit/', CustomerUpdateView.as_view(), name="customers-update"),
    path('customer/<int:pk>/delete/', CustomerDeleteView.as_view(), name="customer-delete"),
    path('order/<int:pk>/detail/', OrderDetailView.as_view(), name="order-detail"),
    path('product/<int:pk>/detail/', ProductDetailsView.as_view(), name="product-detail"),
    path('reports', views.reports, name="reports"),
    path('transfers/create', TransferCreateView.as_view(), name="transfers"),
    path('transfers/', TransfersListsView.as_view(), name="transfers-list"),
    path('scan/', views.scanner, name="scanner"),
    path('location/', LocationCreateView.as_view(), name="location"),
    path('import-inventory/', views.excel_import, name='excel_import'),
    path('import-customers/', views.customer_import, name='customer_import'),
    path('import-suppliers/', views.supplier_import, name='supplier_import'),
    path('get-source-location/<int:product_id>/', views.get_source_location, name='get_source_location'),
    path('delete-product/<int:product_id>/', views.softdelete_product, name='softdelete-product'),
    path('restore-product/<int:product_id>/', views.restore_product, name='restore-product'),
    path('trash-list/', views.deleted_items_lists, name='trash-list'),
    path('inventory-reports/', views.inventory_report, name="inventory-reports"),
    path('pending-orders-reports/', views.pendingorder_report, name="pending-orders-reports"),
    path('recent-shipments-reports/', views.recentshipments_report, name="recent-shipments-reports"),


]