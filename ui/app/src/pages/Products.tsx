import { useState, useEffect } from 'react';
import { Edit3, Trash2, Eye, Tag, Filter, Search, Loader2, Settings, Plus } from 'lucide-react';
import Header from '../components/Header';
import DataTable, { type Column } from '../components/DataTable';
import Modal from '../components/Modal';
import ConfirmDialog from '../components/ConfirmDialog';
import CategoryPieChart from '../components/CategoryPieChart';
import { useAuth } from '../context/AuthContext';
import type { ProductResponse, ProductCreateRequest, ProductUpdateRequest, CategoryResponse, CategoryProductPercentage } from '../types';
import * as productsApi from '../api/products';
import * as categoriesApi from '../api/categories';
import { ApiError } from '../api/client';

export default function Products() {
    const { isAdmin } = useAuth();
    const [showAddModal, setShowAddModal] = useState(false);
    const [showEditModal, setShowEditModal] = useState(false);
    const [showDetailModal, setShowDetailModal] = useState(false);
    const [showCategoryModal, setShowCategoryModal] = useState(false);
    const [confirmDialog, setConfirmDialog] = useState<{
        isOpen: boolean;
        title: string;
        message: string;
        onConfirm: () => void;
    }>({ isOpen: false, title: '', message: '', onConfirm: () => {} });
    const [selectedProduct, setSelectedProduct] = useState<ProductResponse | null>(null);
    
    // Data state
    const [products, setProducts] = useState<ProductResponse[]>([]);
    const [totalProducts, setTotalProducts] = useState(0);
    const [categories, setCategories] = useState<CategoryResponse[]>([]);
    const [categoryDistribution, setCategoryDistribution] = useState<CategoryProductPercentage[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    
    // Filter state
    const [categoryFilter, setCategoryFilter] = useState<number | null>(null);
    const [searchQuery, setSearchQuery] = useState('');
    const [limit] = useState(50);
    const [offset] = useState(0);
    
    // Form state for create
    const [createForm, setCreateForm] = useState<ProductCreateRequest>({
        sku: '',
        name: '',
        description: null,
        category_id: null,
        reorder_point: 0,
    });
    
    // Form state for update
    const [updateForm, setUpdateForm] = useState<ProductUpdateRequest>({
        name: '',
        description: null,
        category_name: null,
        reorder_point: 0,
    });
    
    const [submitting, setSubmitting] = useState(false);

    // Fetch categories and distribution once on mount
    useEffect(() => {
        fetchCategories();
    }, []);

    // Fetch products when filters change
    useEffect(() => {
        fetchProducts();
    }, [categoryFilter, searchQuery, limit, offset]);

    const fetchCategories = async () => {
        try {
            const response = await categoriesApi.listCategories();
            setCategories(response.categories);
        } catch (err) {
            console.error('Error fetching categories:', err);
            // Don't block the UI if categories fail to load
        }
    };

    const fetchCategoryDistribution = async () => {
        try {
            const response = await categoriesApi.getProductDistribution();
            setCategoryDistribution(response.distribution);
        } catch (err) {
            console.error('Error fetching category distribution:', err);
            // Don't block the UI if distribution fails to load
        }
    };
    useEffect(() => {
        fetchCategoryDistribution();
    }, []);

    const fetchProducts = async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await productsApi.listProducts(
                categoryFilter,
                searchQuery || null,
                limit,
                offset
            );
            setProducts(response.products);
            setTotalProducts(response.total);
        } catch (err) {
            const errorMsg = err instanceof ApiError ? err.message : 'Failed to load products';
            setError(errorMsg);
            console.error('Error fetching products:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateProduct = async (e: React.FormEvent) => {
        e.preventDefault();
        setSubmitting(true);
        try {
            await productsApi.createProduct(createForm);
            setShowAddModal(false);
            setCreateForm({
                sku: '',
                name: '',
                description: null,
                category_id: null,
                reorder_point: 0,
            });
            fetchProducts();
        } catch (err) {
            const errorMsg = err instanceof ApiError ? err.message : 'Failed to create product';
            alert(`Error: ${errorMsg}`);
            console.error('Error creating product:', err);
        } finally {
            setSubmitting(false);
        }
    };

    const handleUpdateProduct = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!selectedProduct) return;
        
        setSubmitting(true);
        try {
            await productsApi.updateProduct(selectedProduct.id, updateForm);
            setShowEditModal(false);
            setSelectedProduct(null);
            fetchProducts();
        } catch (err) {
            const errorMsg = err instanceof ApiError ? err.message : 'Failed to update product';
            alert(`Error: ${errorMsg}`);
            console.error('Error updating product:', err);
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeleteProduct = async (productId: number) => {
        setConfirmDialog({
            isOpen: true,
            title: 'Delete Product',
            message: 'Are you sure you want to delete this product? This will also delete related stock records.',
            onConfirm: async () => {
                setConfirmDialog({ ...confirmDialog, isOpen: false });
                try {
                    await productsApi.deleteProduct(productId);
                    fetchProducts();
                    if (showDetailModal) {
                        setShowDetailModal(false);
                        setSelectedProduct(null);
                    }
                } catch (err) {
                    const errorMsg = err instanceof ApiError ? err.message : 'Failed to delete product';
                    alert(`Error: ${errorMsg}`);
                    console.error('Error deleting product:', err);
                }
            },
        });
    };

    const openDetail = (product: ProductResponse) => {
        setSelectedProduct(product);
        setShowDetailModal(true);
    };

    const openEdit = (product: ProductResponse) => {
        setSelectedProduct(product);
        setUpdateForm({
            name: product.name,
            description: product.description,
            category_name: product.category_name,
            reorder_point: product.reorder_point,
        });
        setShowEditModal(true);
    };

    const columns: Column<ProductResponse>[] = [
        {
            key: 'name',
            label: 'Product',
            sortable: true,
            render: (p) => (
                <div className="flex items-center gap-3">
                    <div
                        className="w-9 h-9 rounded-lg flex items-center justify-center text-xs font-bold flex-shrink-0"
                        style={{
                            background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.12), rgba(139, 92, 246, 0.12))',
                            color: '#818cf8',
                        }}
                    >
                        {p.name.substring(0, 2).toUpperCase()}
                    </div>
                    <div>
                        <p className="text-sm font-medium text-white">{p.name}</p>
                        <p className="text-xs text-slate-500">{p.description || 'No description'}</p>
                    </div>
                </div>
            ),
        },
        {
            key: 'sku',
            label: 'SKU',
            sortable: true,
            render: (p) => <span className="font-mono text-xs text-slate-300 bg-white/5 px-2 py-1 rounded">{p.sku}</span>,
        },
        {
            key: 'category_id',
            label: 'Category',
            sortable: true,
            render: (p) => (
                <div className="flex items-center gap-1.5">
                    <Tag size={12} className="text-slate-500" />
                    <span className="text-sm text-slate-300">
                        {p.category_name ? `${p.category_name}` : 'Uncategorized'}
                    </span>
                </div>
            ),
        },
        {
            key: 'reorder_point',
            label: 'Reorder Point',
            sortable: true,
            render: (p) => <span className="text-sm text-amber-400">{p.reorder_point}</span>,
        },
        {
            key: 'actions',
            label: '',
            render: (p) => (
                <div className="flex items-center gap-1 justify-end">
                    <button
                        onClick={(e) => { e.stopPropagation(); openDetail(p); }}
                        className="p-2 rounded-lg text-slate-400 hover:text-blue-400 hover:bg-blue-400/10 transition-all"
                        title="View Details"
                    >
                        <Eye size={16} />
                    </button>
                    {isAdmin && (
                        <>
                            <button
                                onClick={(e) => { e.stopPropagation(); openEdit(p); }}
                                className="p-2 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-amber-400/10 transition-all"
                                title="Edit"
                            >
                                <Edit3 size={16} />
                            </button>
                            <button
                                onClick={(e) => { e.stopPropagation(); handleDeleteProduct(p.id); }}
                                className="p-2 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-400/10 transition-all"
                                title="Delete"
                            >
                                <Trash2 size={16} />
                            </button>
                        </>
                    )}
                </div>
            ),
        },
    ];

    return (
        <div>
            <Header
                title="Products"
                subtitle={`${totalProducts} products in catalog`}
                onAddNew={isAdmin ? () => setShowAddModal(true) : undefined}
                addNewLabel="Add Product"
            />

            {/* Product Distribution Chart */}
            <div className="px-8 mb-6">
                <div className="glass-card p-6 animate-fade-in" style={{ animationDelay: '0.1s' }}>
                    <div className="mb-4">
                        <h2 className="text-lg font-bold text-white mb-1">Product Distribution by Category</h2>
                        <p className="text-xs text-slate-400">Visual breakdown of products across different categories</p>
                    </div>
                    <div className="h-80">
                        <CategoryPieChart data={categoryDistribution} />
                    </div>
                </div>
            </div>

            {/* Search and Filters */}
            <div className="px-8 mb-5 space-y-3 animate-fade-in">
                {/* Search bar */}
                <div className="relative max-w-md">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                    <input
                        type="text"
                        placeholder="Search products by name or SKU..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-blue-500/30"
                        style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                    />
                </div>
                
                {/* Category filter */}
                <div className="flex items-center gap-3 flex-wrap">
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                        <Filter size={14} />
                        <span>Category:</span>
                    </div>
                    {isAdmin && (
                        <button
                            onClick={() => setShowCategoryModal(true)}
                            className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all bg-purple-500/10 text-purple-300 border border-purple-500/30 hover:bg-purple-500/20"
                            title="Manage Categories"
                        >
                            <Settings size={12} className="inline mr-1" />
                            Manage
                        </button>
                    )}
                    <button
                        onClick={() => setCategoryFilter(null)}
                        className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                            categoryFilter === null
                                ? 'bg-accent-blue/20 text-blue-300 border border-blue-500/30'
                                : 'bg-white/5 text-slate-400 border border-transparent hover:bg-white/10'
                        }`}
                    >
                        All Categories
                    </button>
                    {categories.map((cat) => (
                        <button
                            key={cat.id}
                            onClick={() => setCategoryFilter(cat.id)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                                categoryFilter === cat.id
                                    ? 'bg-accent-blue/20 text-blue-300 border border-blue-500/30'
                                    : 'bg-white/5 text-slate-400 border border-transparent hover:bg-white/10'
                            }`}
                        >
                            {cat.name}
                        </button>
                    ))}
                </div>
            </div>

            {/* Loading/Error/Content */}
            <div className="px-8 pb-8">
                {loading ? (
                    <div className="flex items-center justify-center py-20">
                        <Loader2 size={32} className="text-blue-400 animate-spin" />
                    </div>
                ) : error ? (
                    <div className="text-center py-20">
                        <p className="text-rose-400 text-sm">{error}</p>
                        <button
                            onClick={fetchProducts}
                            className="mt-4 px-4 py-2 rounded-lg text-sm text-white bg-white/5 hover:bg-white/10 transition-colors"
                        >
                            Retry
                        </button>
                    </div>
                ) : (
                    <DataTable
                        columns={columns}
                        data={products}
                        keyExtractor={(p) => p.id.toString()}
                        onRowClick={openDetail}
                        emptyMessage="No products found"
                    />
                )}
            </div>

            {/* Add Product Modal */}
            <Modal isOpen={showAddModal} onClose={() => setShowAddModal(false)} title="Add New Product" size="lg">
                <form onSubmit={handleCreateProduct} className="space-y-5">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-2">Product Name *</label>
                            <input
                                type="text"
                                required
                                value={createForm.name}
                                onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                                className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-blue-500/30"
                                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                                placeholder="Enter product name"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-2">SKU *</label>
                            <input
                                type="text"
                                required
                                value={createForm.sku}
                                onChange={(e) => setCreateForm({ ...createForm, sku: e.target.value })}
                                className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-blue-500/30"
                                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                                placeholder="e.g., ELEC-SP-003"
                            />
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-2">Description</label>
                        <textarea
                            value={createForm.description || ''}
                            onChange={(e) => setCreateForm({ ...createForm, description: e.target.value || null })}
                            className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-blue-500/30 resize-none"
                            rows={3}
                            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                            placeholder="Product description..."
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-2">Category</label>
                            <select
                                value={createForm.category_id || ''}
                                onChange={(e) => setCreateForm({ ...createForm, category_id: e.target.value ? parseInt(e.target.value) : null })}
                                className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all focus:ring-2 focus:ring-blue-500/30"
                                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)', color: 'white' }}
                            >
                                <option value="" style={{ background: '#1e293b', color: 'white' }}>No category</option>
                                {categories.map(cat => (
                                    <option key={cat.id} value={cat.id} style={{ background: '#1e293b', color: 'white' }}>
                                        {cat.name}
                                    </option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-2">Reorder Point</label>
                            <input
                                type="number"
                                value={createForm.reorder_point}
                                onChange={(e) => setCreateForm({ ...createForm, reorder_point: parseInt(e.target.value) || 0 })}
                                className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-blue-500/30"
                                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                                placeholder="Minimum stock level"
                                min={0}
                            />
                        </div>
                    </div>
                    <div className="flex justify-end gap-3 pt-3">
                        <button
                            type="button"
                            onClick={() => setShowAddModal(false)}
                            disabled={submitting}
                            className="px-5 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                            style={{ background: 'rgba(255,255,255,0.05)' }}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={submitting}
                            className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                            style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)', boxShadow: '0 4px 16px rgba(59,130,246,0.3)' }}
                        >
                            {submitting && <Loader2 size={16} className="animate-spin" />}
                            {submitting ? 'Creating...' : 'Create Product'}
                        </button>
                    </div>
                </form>
            </Modal>

            {/* Edit Product Modal */}
            <Modal isOpen={showEditModal} onClose={() => setShowEditModal(false)} title="Edit Product" size="lg">
                <form onSubmit={handleUpdateProduct} className="space-y-5">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-2">Product Name</label>
                            <input
                                type="text"
                                value={updateForm.name || ''}
                                onChange={(e) => setUpdateForm({ ...updateForm, name: e.target.value })}
                                className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-blue-500/30"
                                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                                placeholder="Enter product name"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-2">SKU (Read-only)</label>
                            <input
                                type="text"
                                value={selectedProduct?.sku || ''}
                                disabled
                                className="w-full px-4 py-3 rounded-xl text-sm text-slate-500 bg-white/5 cursor-not-allowed"
                                style={{ border: '1px solid rgba(255,255,255,0.08)' }}
                            />
                        </div>
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-2">Description</label>
                        <textarea
                            value={updateForm.description || ''}
                            onChange={(e) => setUpdateForm({ ...updateForm, description: e.target.value || null })}
                            className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-blue-500/30 resize-none"
                            rows={3}
                            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                            placeholder="Product description..."
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-2">Category Name</label>
                            <input
                                type="text"
                                value={updateForm.category_name || ''}
                                onChange={(e) => setUpdateForm({ ...updateForm, category_name: e.target.value || null })}
                                className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-blue-500/30"
                                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                                placeholder="Optional"
                            />
                        </div>
                        <div>
                            <label className="block text-xs font-medium text-slate-400 mb-2">Reorder Point</label>
                            <input
                                type="number"
                                value={updateForm.reorder_point || 0}
                                onChange={(e) => setUpdateForm({ ...updateForm, reorder_point: parseInt(e.target.value) || 0 })}
                                className="w-full px-4 py-3 rounded-xl text-sm text-white placeholder-slate-500 outline-none transition-all focus:ring-2 focus:ring-blue-500/30"
                                style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                                placeholder="Minimum stock level"
                                min={0}
                            />
                        </div>
                    </div>
                    <div className="flex justify-end gap-3 pt-3">
                        <button
                            type="button"
                            onClick={() => setShowEditModal(false)}
                            disabled={submitting}
                            className="px-5 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white transition-colors disabled:opacity-50"
                            style={{ background: 'rgba(255,255,255,0.05)' }}
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={submitting}
                            className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-[1.02] active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                            style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)', boxShadow: '0 4px 16px rgba(59,130,246,0.3)' }}
                        >
                            {submitting && <Loader2 size={16} className="animate-spin" />}
                            {submitting ? 'Updating...' : 'Update Product'}
                        </button>
                    </div>
                </form>
            </Modal>

            {/* Product Detail Modal */}
            <Modal
                isOpen={showDetailModal}
                onClose={() => { setShowDetailModal(false); setSelectedProduct(null); }}
                title="Product Details"
                size="lg"
            >
                {selectedProduct && (
                    <div className="space-y-6">
                        {/* Product info */}
                        <div className="flex items-start gap-4">
                            <div
                                className="w-14 h-14 rounded-xl flex items-center justify-center text-lg font-bold flex-shrink-0"
                                style={{
                                    background: 'linear-gradient(135deg, rgba(59,130,246,0.15), rgba(139,92,246,0.15))',
                                    color: '#818cf8',
                                }}
                            >
                                {selectedProduct.name.substring(0, 2).toUpperCase()}
                            </div>
                            <div className="flex-1">
                                <h3 className="text-xl font-bold text-white">{selectedProduct.name}</h3>
                                <p className="text-sm text-slate-400 mt-1">{selectedProduct.description || 'No description'}</p>
                                <div className="flex items-center gap-3 mt-3 flex-wrap">
                                    <span className="font-mono text-xs bg-white/5 text-slate-300 px-2.5 py-1 rounded-lg">
                                        SKU: {selectedProduct.sku}
                                    </span>
                                    <span className="text-xs text-slate-400 flex items-center gap-1">
                                        <Tag size={12} />
                                        {selectedProduct.category_name ? `Category ${selectedProduct.category_name}` : 'Uncategorized'}
                                    </span>
                                </div>
                            </div>
                        </div>

                        {/* Product stats */}
                        <div className="grid grid-cols-2 gap-3">
                            <div className="p-4 rounded-xl" style={{ background: 'rgba(245,158,11,0.08)' }}>
                                <p className="text-xs text-slate-400 mb-1">Reorder Point</p>
                                <p className="text-2xl font-bold text-amber-400">{selectedProduct.reorder_point}</p>
                            </div>
                            <div className="p-4 rounded-xl" style={{ background: 'rgba(139,92,246,0.08)' }}>
                                <p className="text-xs text-slate-400 mb-1">Product ID</p>
                                <p className="text-2xl font-bold text-purple-400">{selectedProduct.id}</p>
                            </div>
                        </div>

                        {/* Action buttons */}
                        {isAdmin && (
                            <div className="flex gap-3 pt-4 border-t border-white/5">
                                <button
                                    onClick={() => {
                                        setShowDetailModal(false);
                                        openEdit(selectedProduct);
                                    }}
                                    className="flex-1 px-4 py-2.5 rounded-xl text-sm font-medium text-white transition-all hover:scale-[1.02]"
                                    style={{ background: 'linear-gradient(135deg, #3b82f6, #6366f1)' }}
                                >
                                    Edit Product
                                </button>
                                <button
                                    onClick={() => handleDeleteProduct(selectedProduct.id)}
                                    className="px-4 py-2.5 rounded-xl text-sm font-medium text-rose-400 hover:bg-rose-400/10 transition-all"
                                    style={{ border: '1px solid rgba(244,63,94,0.3)' }}
                                >
                                    Delete
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </Modal>

            {/* Category Management Modal */}
            <Modal
                isOpen={showCategoryModal}
                onClose={() => setShowCategoryModal(false)}
                title="Manage Categories"
                size="lg"
            >
                <CategoryManagement
                    categories={categories}
                    onCategoriesChange={fetchCategories}
                    onClose={() => setShowCategoryModal(false)}
                />
            </Modal>

            {/* Confirmation Dialog */}
            <ConfirmDialog
                isOpen={confirmDialog.isOpen}
                title={confirmDialog.title}
                message={confirmDialog.message}
                onConfirm={confirmDialog.onConfirm}
                onCancel={() => setConfirmDialog({ ...confirmDialog, isOpen: false })}
            />
        </div>
    );
}

// Category Management Component
function CategoryManagement({
    categories,
    onCategoriesChange,
    onClose,
}: {
    categories: CategoryResponse[];
    onCategoriesChange: () => void;
    onClose: () => void;
}) {
    const [editingCategory, setEditingCategory] = useState<CategoryResponse | null>(null);
    const [newCategoryName, setNewCategoryName] = useState('');
    const [newCategoryParentId, setNewCategoryParentId] = useState<number | null>(null);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [confirmDialog, setConfirmDialog] = useState<{
        isOpen: boolean;
        categoryId: number | null;
    }>({ isOpen: false, categoryId: null });

    const handleCreateCategory = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newCategoryName.trim()) {
            setError('Category name is required');
            return;
        }

        setSubmitting(true);
        setError(null);
        try {
            await categoriesApi.createCategory({
                name: newCategoryName,
                parent_id: newCategoryParentId,
            });
            setNewCategoryName('');
            setNewCategoryParentId(null);
            onCategoriesChange();
        } catch (err) {
            const errorMsg = err instanceof ApiError ? err.message : 'Failed to create category';
            setError(errorMsg);
        } finally {
            setSubmitting(false);
        }
    };

    const handleUpdateCategory = async (categoryId: number, name: string) => {
        setSubmitting(true);
        setError(null);
        try {
            await categoriesApi.updateCategory(categoryId, { name });
            setEditingCategory(null);
            onCategoriesChange();
        } catch (err) {
            const errorMsg = err instanceof ApiError ? err.message : 'Failed to update category';
            setError(errorMsg);
        } finally {
            setSubmitting(false);
        }
    };

    const handleDeleteCategory = async (categoryId: number) => {
        setConfirmDialog({ isOpen: true, categoryId });
    };

    const confirmDeleteCategory = async () => {
        if (!confirmDialog.categoryId) return;

        setConfirmDialog({ isOpen: false, categoryId: null });
        setError(null);
        try {
            await categoriesApi.deleteCategory(confirmDialog.categoryId);
            onCategoriesChange();
        } catch (err) {
            const errorMsg = err instanceof ApiError ? err.message : 'Failed to delete category';
            setError(errorMsg);
        }
    };

    return (
        <div className="space-y-5">
            {error && (
                <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-400 text-sm">
                    {error}
                </div>
            )}

            {/* Create new category form */}
            <form onSubmit={handleCreateCategory} className="p-4 rounded-xl" style={{ background: 'rgba(139,92,246,0.05)', border: '1px solid rgba(139,92,246,0.2)' }}>
                <h4 className="text-sm font-semibold text-purple-300 mb-3 flex items-center gap-2">
                    <Plus size={16} />
                    Add New Category
                </h4>
                <div className="grid grid-cols-3 gap-3">
                    <div className="col-span-2">
                        <input
                            type="text"
                            value={newCategoryName}
                            onChange={(e) => setNewCategoryName(e.target.value)}
                            placeholder="Category name..."
                            className="w-full px-4 py-2.5 rounded-xl text-sm text-white placeholder-slate-500 outline-none focus:ring-2 focus:ring-purple-500/30"
                            style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={submitting || !newCategoryName.trim()}
                        className="px-4 py-2.5 rounded-xl text-sm font-semibold text-white transition-all hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                        style={{ background: 'linear-gradient(135deg, #8b5cf6, #6366f1)', boxShadow: '0 4px 16px rgba(139,92,246,0.3)' }}
                    >
                        {submitting ? <Loader2 size={16} className="animate-spin" /> : <Plus size={16} />}
                        Create
                    </button>
                </div>
            </form>

            {/* Categories list */}
            <div className="space-y-2">
                <h4 className="text-xs font-medium text-slate-400 mb-3">Existing Categories ({categories.length})</h4>
                {categories.length === 0 ? (
                    <div className="text-center py-8 text-slate-500 text-sm">
                        No categories yet. Create one above.
                    </div>
                ) : (
                    <div className="space-y-2 max-h-[400px] overflow-y-auto">
                        {categories.map((cat) => (
                            <div
                                key={cat.id}
                                className="flex items-center gap-3 p-3 rounded-xl transition-all hover:bg-white/5"
                                style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.05)' }}
                            >
                                {editingCategory?.id === cat.id ? (
                                    <>
                                        <input
                                            type="text"
                                            defaultValue={cat.name}
                                            onKeyDown={(e) => {
                                                if (e.key === 'Enter') {
                                                    handleUpdateCategory(cat.id, e.currentTarget.value);
                                                } else if (e.key === 'Escape') {
                                                    setEditingCategory(null);
                                                }
                                            }}
                                            autoFocus
                                            className="flex-1 px-3 py-1.5 rounded-lg text-sm text-white outline-none focus:ring-2 focus:ring-blue-500/30"
                                            style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.1)' }}
                                        />
                                        <button
                                            onClick={() => setEditingCategory(null)}
                                            className="px-3 py-1.5 text-xs text-slate-400 hover:text-white transition-colors"
                                        >
                                            Cancel
                                        </button>
                                    </>
                                ) : (
                                    <>
                                        <Tag size={14} className="text-purple-400" />
                                        <span className="flex-1 text-sm text-white">{cat.name}</span>
                                        <button
                                            onClick={() => setEditingCategory(cat)}
                                            className="p-1.5 rounded-lg text-slate-400 hover:text-amber-400 hover:bg-amber-400/10 transition-all"
                                            title="Edit"
                                        >
                                            <Edit3 size={14} />
                                        </button>
                                        <button
                                            onClick={() => handleDeleteCategory(cat.id)}
                                            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-400/10 transition-all"
                                            title="Delete"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Close button */}
            <div className="flex justify-end pt-3 border-t border-white/5">
                <button
                    onClick={onClose}
                    className="px-5 py-2.5 rounded-xl text-sm font-medium text-slate-400 hover:text-white transition-colors"
                    style={{ background: 'rgba(255,255,255,0.05)' }}
                >
                    Done
                </button>
            </div>

            {/* Confirmation Dialog for Category Deletion */}
            <ConfirmDialog
                isOpen={confirmDialog.isOpen}
                title="Delete Category"
                message="Are you sure you want to delete this category? Products in this category will become uncategorized."
                onConfirm={confirmDeleteCategory}
                onCancel={() => setConfirmDialog({ isOpen: false, categoryId: null })}
            />
        </div>
    );
}
