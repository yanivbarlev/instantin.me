/**
 * InstantIn.me Drag-and-Drop Page Builder
 * 
 * Interactive storefront page builder with AI-powered suggestions
 * Supports drag-and-drop blocks: header, product, link, contact, scheduler
 */

class PageBuilder {
    constructor() {
        this.blocks = new Map();
        this.currentStorefront = null;
        this.draggedElement = null;
        this.blockCounter = 0;
        this.unsavedChanges = false;
        
        this.init();
    }
    
    init() {
        this.initializeBuilder();
        this.setupEventListeners();
        this.loadBlockTemplates();
        this.initializeAIIntegration();
    }
    
    initializeBuilder() {
        // Create main builder container if it doesn't exist
        if (!document.getElementById('page-builder')) {
            this.createBuilderInterface();
        }
        
        // Initialize builder state
        this.canvas = document.getElementById('builder-canvas');
        this.sidebar = document.getElementById('builder-sidebar');
        this.toolbar = document.getElementById('builder-toolbar');
        this.preview = document.getElementById('preview-iframe');
        
        // Setup drag and drop zones
        this.setupDragAndDrop();
    }
    
    createBuilderInterface() {
        const builderHTML = `
            <div id="page-builder" class="fixed inset-0 bg-gray-100 z-50 hidden">
                <!-- Builder Toolbar -->
                <div id="builder-toolbar" class="bg-white shadow-md border-b border-gray-200 p-4">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-4">
                            <h1 class="text-xl font-bold text-gray-800">InstantIn.me Page Builder</h1>
                            <div class="flex items-center space-x-2">
                                <button id="ai-suggest-btn" class="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700 transition-colors">
                                    🤖 AI Suggestions
                                </button>
                                <button id="preview-btn" class="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors">
                                    👁️ Preview
                                </button>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <button id="save-btn" class="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 transition-colors">
                                💾 Save
                            </button>
                            <button id="close-builder-btn" class="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 transition-colors">
                                ✕ Close
                            </button>
                        </div>
                    </div>
                </div>
                
                <div class="flex h-full pt-16">
                    <!-- Sidebar with Blocks -->
                    <div id="builder-sidebar" class="w-80 bg-white shadow-lg border-r border-gray-200 overflow-y-auto">
                        <div class="p-4">
                            <h2 class="text-lg font-semibold text-gray-800 mb-4">Content Blocks</h2>
                            
                            <!-- Block Categories -->
                            <div class="space-y-4">
                                <!-- Header Blocks -->
                                <div class="block-category">
                                    <h3 class="text-sm font-medium text-gray-600 mb-2">Header</h3>
                                    <div class="grid grid-cols-1 gap-2">
                                        <div class="block-template" data-type="header" data-variant="hero">
                                            <div class="bg-gradient-to-r from-blue-500 to-purple-600 p-4 rounded-lg cursor-grab hover:shadow-md transition-shadow">
                                                <div class="text-white text-sm font-semibold">Hero Header</div>
                                                <div class="text-blue-100 text-xs">Name, bio, and call-to-action</div>
                                            </div>
                                        </div>
                                        <div class="block-template" data-type="header" data-variant="minimal">
                                            <div class="bg-white border-2 border-gray-300 p-4 rounded-lg cursor-grab hover:shadow-md transition-shadow">
                                                <div class="text-gray-800 text-sm font-semibold">Minimal Header</div>
                                                <div class="text-gray-500 text-xs">Clean name and bio</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Product Blocks -->
                                <div class="block-category">
                                    <h3 class="text-sm font-medium text-gray-600 mb-2">Products</h3>
                                    <div class="grid grid-cols-1 gap-2">
                                        <div class="block-template" data-type="product" data-variant="grid">
                                            <div class="bg-green-50 border-2 border-green-200 p-4 rounded-lg cursor-grab hover:shadow-md transition-shadow">
                                                <div class="text-green-800 text-sm font-semibold">Product Grid</div>
                                                <div class="text-green-600 text-xs">Display products in grid layout</div>
                                            </div>
                                        </div>
                                        <div class="block-template" data-type="product" data-variant="featured">
                                            <div class="bg-yellow-50 border-2 border-yellow-200 p-4 rounded-lg cursor-grab hover:shadow-md transition-shadow">
                                                <div class="text-yellow-800 text-sm font-semibold">Featured Product</div>
                                                <div class="text-yellow-600 text-xs">Highlight a single product</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Link Blocks -->
                                <div class="block-category">
                                    <h3 class="text-sm font-medium text-gray-600 mb-2">Links</h3>
                                    <div class="grid grid-cols-1 gap-2">
                                        <div class="block-template" data-type="link" data-variant="social">
                                            <div class="bg-pink-50 border-2 border-pink-200 p-4 rounded-lg cursor-grab hover:shadow-md transition-shadow">
                                                <div class="text-pink-800 text-sm font-semibold">Social Links</div>
                                                <div class="text-pink-600 text-xs">Instagram, TikTok, Twitter</div>
                                            </div>
                                        </div>
                                        <div class="block-template" data-type="link" data-variant="buttons">
                                            <div class="bg-indigo-50 border-2 border-indigo-200 p-4 rounded-lg cursor-grab hover:shadow-md transition-shadow">
                                                <div class="text-indigo-800 text-sm font-semibold">Link Buttons</div>
                                                <div class="text-indigo-600 text-xs">Custom link buttons</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Contact Blocks -->
                                <div class="block-category">
                                    <h3 class="text-sm font-medium text-gray-600 mb-2">Contact</h3>
                                    <div class="grid grid-cols-1 gap-2">
                                        <div class="block-template" data-type="contact" data-variant="form">
                                            <div class="bg-teal-50 border-2 border-teal-200 p-4 rounded-lg cursor-grab hover:shadow-md transition-shadow">
                                                <div class="text-teal-800 text-sm font-semibold">Contact Form</div>
                                                <div class="text-teal-600 text-xs">Name, email, message</div>
                                            </div>
                                        </div>
                                        <div class="block-template" data-type="contact" data-variant="info">
                                            <div class="bg-cyan-50 border-2 border-cyan-200 p-4 rounded-lg cursor-grab hover:shadow-md transition-shadow">
                                                <div class="text-cyan-800 text-sm font-semibold">Contact Info</div>
                                                <div class="text-cyan-600 text-xs">Email, phone, address</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                
                                <!-- Scheduler Blocks -->
                                <div class="block-category">
                                    <h3 class="text-sm font-medium text-gray-600 mb-2">Scheduler</h3>
                                    <div class="grid grid-cols-1 gap-2">
                                        <div class="block-template" data-type="scheduler" data-variant="calendar">
                                            <div class="bg-orange-50 border-2 border-orange-200 p-4 rounded-lg cursor-grab hover:shadow-md transition-shadow">
                                                <div class="text-orange-800 text-sm font-semibold">Calendar Booking</div>
                                                <div class="text-orange-600 text-xs">Appointment scheduling</div>
                                            </div>
                                        </div>
                                        <div class="block-template" data-type="scheduler" data-variant="quick">
                                            <div class="bg-red-50 border-2 border-red-200 p-4 rounded-lg cursor-grab hover:shadow-md transition-shadow">
                                                <div class="text-red-800 text-sm font-semibold">Quick Book</div>
                                                <div class="text-red-600 text-xs">Simple time slots</div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Main Canvas -->
                    <div class="flex-1 flex flex-col">
                        <!-- Canvas Header -->
                        <div class="bg-gray-50 border-b border-gray-200 p-4">
                            <div class="flex items-center justify-between">
                                <div class="flex items-center space-x-4">
                                    <h2 class="text-lg font-semibold text-gray-800">Canvas</h2>
                                    <div class="flex items-center space-x-2">
                                        <button id="desktop-view" class="px-3 py-1 text-sm bg-blue-600 text-white rounded">Desktop</button>
                                        <button id="tablet-view" class="px-3 py-1 text-sm bg-gray-300 text-gray-700 rounded">Tablet</button>
                                        <button id="mobile-view" class="px-3 py-1 text-sm bg-gray-300 text-gray-700 rounded">Mobile</button>
                                    </div>
                                </div>
                                <div class="text-sm text-gray-500">
                                    Drag blocks here to build your page
                                </div>
                            </div>
                        </div>
                        
                        <!-- Canvas Area -->
                        <div id="builder-canvas" class="flex-1 bg-gray-100 p-8 overflow-y-auto">
                            <div id="canvas-content" class="max-w-md mx-auto bg-white rounded-lg shadow-lg min-h-96 relative">
                                <div id="drop-zone" class="w-full min-h-96 p-6 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center text-center">
                                    <div class="text-gray-400 text-lg mb-2">🎨</div>
                                    <div class="text-gray-600 font-medium mb-1">Start Building Your Page</div>
                                    <div class="text-gray-500 text-sm">Drag blocks from the sidebar to begin</div>
                                </div>
                            </div>
                        </div>
                    
                    <!-- Preview Panel (Hidden by default) -->
                    <div id="preview-panel" class="w-96 bg-white shadow-lg border-l border-gray-200 hidden">
                        <div class="p-4 border-b border-gray-200">
                            <h3 class="text-lg font-semibold text-gray-800">Live Preview</h3>
                        </div>
                        <iframe id="preview-iframe" class="w-full h-full" src="about:blank"></iframe>
                    </div>
                </div>
                
                <!-- Block Edit Modal -->
                <div id="block-edit-modal" class="fixed inset-0 bg-black bg-opacity-50 z-50 hidden">
                    <div class="flex items-center justify-center h-full p-4">
                        <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-96 overflow-y-auto">
                            <div class="p-6">
                                <div class="flex items-center justify-between mb-4">
                                    <h3 id="modal-title" class="text-lg font-semibold text-gray-800">Edit Block</h3>
                                    <button id="close-modal-btn" class="text-gray-400 hover:text-gray-600">
                                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                                        </svg>
                                    </button>
                                </div>
                                <div id="modal-content">
                                    <!-- Dynamic content based on block type -->
                                </div>
                                <div class="flex justify-end space-x-3 mt-6">
                                    <button id="modal-cancel-btn" class="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50">
                                        Cancel
                                    </button>
                                    <button id="modal-save-btn" class="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
                                        Save Changes
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', builderHTML);
    }
    
    setupDragAndDrop() {
        const canvas = document.getElementById('drop-zone');
        
        // Block template drag start
        document.addEventListener('dragstart', (e) => {
            if (e.target.closest('.block-template')) {
                const template = e.target.closest('.block-template');
                this.draggedElement = {
                    type: template.dataset.type,
                    variant: template.dataset.variant
                };
                e.dataTransfer.effectAllowed = 'copy';
            }
        });
        
        // Canvas drop handlers
        canvas.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.dataTransfer.dropEffect = 'copy';
            canvas.classList.add('border-blue-500', 'bg-blue-50');
        });
        
        canvas.addEventListener('dragleave', (e) => {
            canvas.classList.remove('border-blue-500', 'bg-blue-50');
        });
        
        canvas.addEventListener('drop', (e) => {
            e.preventDefault();
            canvas.classList.remove('border-blue-500', 'bg-blue-50');
            
            if (this.draggedElement) {
                this.addBlockToCanvas(this.draggedElement.type, this.draggedElement.variant);
                this.draggedElement = null;
            }
        });
        
        // Make block templates draggable
        document.querySelectorAll('.block-template').forEach(template => {
            template.draggable = true;
        });
    }
    
    addBlockToCanvas(type, variant) {
        const blockId = `block-${++this.blockCounter}`;
        const block = this.createBlock(blockId, type, variant);
        
        // Replace empty drop zone or append to existing content
        const dropZone = document.getElementById('drop-zone');
        const canvasContent = document.getElementById('canvas-content');
        
        if (dropZone && dropZone.children.length <= 3) {
            // First block - replace drop zone
            canvasContent.innerHTML = '';
            canvasContent.appendChild(block);
        } else {
            // Additional blocks
            canvasContent.appendChild(block);
        }
        
        // Store block data
        this.blocks.set(blockId, {
            type,
            variant,
            data: this.getDefaultBlockData(type, variant)
        });
        
        this.unsavedChanges = true;
        this.updatePreview();
    }
    
    createBlock(id, type, variant) {
        const blockElement = document.createElement('div');
        blockElement.id = id;
        blockElement.className = 'block-instance relative group mb-4 p-4 border-2 border-transparent hover:border-blue-300 rounded-lg transition-all';
        blockElement.dataset.type = type;
        blockElement.dataset.variant = variant;
        
        // Add block controls
        const controls = document.createElement('div');
        controls.className = 'absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex space-x-1';
        controls.innerHTML = `
            <button class="edit-block-btn bg-blue-600 text-white p-1 rounded text-xs hover:bg-blue-700" data-block-id="${id}">
                ✏️
            </button>
            <button class="delete-block-btn bg-red-600 text-white p-1 rounded text-xs hover:bg-red-700" data-block-id="${id}">
                🗑️
            </button>
        `;
        
        // Add block content
        const content = this.generateBlockContent(type, variant, this.getDefaultBlockData(type, variant));
        blockElement.innerHTML = content;
        blockElement.appendChild(controls);
        
        return blockElement;
    }
    
    generateBlockContent(type, variant, data = null) {
        // Use provided data or fall back to defaults
        const blockData = data || this.getDefaultBlockData(type, variant);
        
        const templates = {
            header: {
                hero: `
                    <div class="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-6 rounded-lg text-center">
                        <img src="${blockData.image || 'https://via.placeholder.com/80x80/ffffff/333333?text=👤'}" class="w-20 h-20 rounded-full mx-auto mb-4">
                        <h1 class="text-2xl font-bold mb-2">${blockData.name || 'Your Name'}</h1>
                        <p class="text-blue-100 mb-4">${blockData.bio || 'Your bio goes here. Tell your story!'}</p>
                        <button class="bg-white text-blue-600 px-6 py-2 rounded-full font-semibold hover:bg-blue-50">
                            ${blockData.buttonText || 'Get Started'}
                        </button>
                    </div>
                `,
                minimal: `
                    <div class="text-center p-6">
                        <img src="${blockData.image || 'https://via.placeholder.com/60x60/f3f4f6/6b7280?text=👤'}" class="w-15 h-15 rounded-full mx-auto mb-3">
                        <h1 class="text-xl font-bold text-gray-800 mb-2">${blockData.name || 'Your Name'}</h1>
                        <p class="text-gray-600">${blockData.bio || 'Your bio goes here'}</p>
                    </div>
                `
            },
            product: {
                grid: `
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow">
                            <img src="https://via.placeholder.com/120x120/f3f4f6/6b7280?text=📦" class="w-full h-24 object-cover rounded mb-2">
                            <h3 class="font-semibold text-sm">Product 1</h3>
                            <p class="text-green-600 font-bold text-sm">$29.99</p>
                        </div>
                        <div class="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow">
                            <img src="https://via.placeholder.com/120x120/f3f4f6/6b7280?text=📦" class="w-full h-24 object-cover rounded mb-2">
                            <h3 class="font-semibold text-sm">Product 2</h3>
                            <p class="text-green-600 font-bold text-sm">$39.99</p>
                        </div>
                    </div>
                `,
                featured: `
                    <div class="bg-yellow-50 border-2 border-yellow-200 rounded-lg p-4">
                        <div class="flex items-center space-x-4">
                            <img src="https://via.placeholder.com/80x80/fbbf24/ffffff?text=⭐" class="w-20 h-20 rounded-lg">
                            <div class="flex-1">
                                <h3 class="font-bold text-lg text-gray-800">Featured Product</h3>
                                <p class="text-gray-600 text-sm mb-2">This is your best-selling item!</p>
                                <div class="flex items-center justify-between">
                                    <span class="text-green-600 font-bold text-lg">$49.99</span>
                                    <button class="bg-yellow-500 text-white px-4 py-2 rounded hover:bg-yellow-600">
                                        Buy Now
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            },
            link: {
                social: `
                    <div class="text-center">
                        <h3 class="font-semibold text-gray-800 mb-3">Follow Me</h3>
                        <div class="flex justify-center space-x-4">
                            <a href="#" class="bg-pink-500 text-white p-3 rounded-full hover:bg-pink-600 transition-colors">
                                📷
                            </a>
                            <a href="#" class="bg-black text-white p-3 rounded-full hover:bg-gray-800 transition-colors">
                                🎵
                            </a>
                            <a href="#" class="bg-blue-500 text-white p-3 rounded-full hover:bg-blue-600 transition-colors">
                                🐦
                            </a>
                        </div>
                    </div>
                `,
                buttons: `
                    <div class="space-y-3">
                        <a href="#" class="block bg-blue-600 text-white text-center py-3 px-4 rounded-lg hover:bg-blue-700 transition-colors">
                            🔗 My Website
                        </a>
                        <a href="#" class="block bg-green-600 text-white text-center py-3 px-4 rounded-lg hover:bg-green-700 transition-colors">
                            📧 Newsletter
                        </a>
                        <a href="#" class="block bg-purple-600 text-white text-center py-3 px-4 rounded-lg hover:bg-purple-700 transition-colors">
                            🎯 Portfolio
                        </a>
                    </div>
                `
            },
            contact: {
                form: `
                    <div class="bg-gray-50 p-4 rounded-lg">
                        <h3 class="font-semibold text-gray-800 mb-3">${blockData.title || 'Get In Touch'}</h3>
                        <form class="space-y-3">
                            <input type="text" placeholder="Your Name" class="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <input type="email" placeholder="Your Email" class="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <textarea placeholder="Your Message" rows="3" class="w-full px-3 py-2 border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-transparent"></textarea>
                            <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition-colors">
                                ${blockData.submitText || 'Send Message'}
                            </button>
                        </form>
                    </div>
                `,
                info: `
                    <div class="text-center p-4">
                        <h3 class="font-semibold text-gray-800 mb-3">${blockData.title || 'Contact Info'}</h3>
                        <div class="space-y-2 text-sm text-gray-600">
                            <div class="flex items-center justify-center space-x-2">
                                <span>📧</span>
                                <span>${blockData.email || 'hello@yoursite.com'}</span>
                            </div>
                            <div class="flex items-center justify-center space-x-2">
                                <span>📱</span>
                                <span>${blockData.phone || '+1 (555) 123-4567'}</span>
                            </div>
                            <div class="flex items-center justify-center space-x-2">
                                <span>📍</span>
                                <span>${blockData.address || 'Your City, Country'}</span>
                            </div>
                        </div>
                    </div>
                `
            },
            scheduler: {
                calendar: `
                    <div class="bg-orange-50 border border-orange-200 rounded-lg p-4">
                        <h3 class="font-semibold text-gray-800 mb-3 text-center">Book a Meeting</h3>
                        <div class="text-center mb-3">
                            <div class="inline-block bg-white border border-gray-300 rounded p-2 text-sm">
                                📅 Select a date and time
                            </div>
                        </div>
                        <button class="w-full bg-orange-500 text-white py-2 rounded hover:bg-orange-600 transition-colors">
                            Open Calendar
                        </button>
                    </div>
                `,
                quick: `
                    <div class="bg-red-50 border border-red-200 rounded-lg p-4">
                        <h3 class="font-semibold text-gray-800 mb-3 text-center">Quick Booking</h3>
                        <div class="grid grid-cols-2 gap-2 mb-3">
                            <button class="bg-white border border-gray-300 rounded p-2 text-sm hover:bg-gray-50">
                                9:00 AM
                            </button>
                            <button class="bg-white border border-gray-300 rounded p-2 text-sm hover:bg-gray-50">
                                1:00 PM
                            </button>
                            <button class="bg-white border border-gray-300 rounded p-2 text-sm hover:bg-gray-50">
                                3:00 PM
                            </button>
                            <button class="bg-white border border-gray-300 rounded p-2 text-sm hover:bg-gray-50">
                                5:00 PM
                            </button>
                        </div>
                        <button class="w-full bg-red-500 text-white py-2 rounded hover:bg-red-600 transition-colors">
                            Book Now
                        </button>
                    </div>
                `
            }
        };
        
        return templates[type]?.[variant] || '<div class="p-4 text-center text-gray-500">Block content</div>';
    }
    
    getDefaultBlockData(type, variant) {
        const defaults = {
            header: {
                hero: {
                    name: 'Your Name',
                    bio: 'Your bio goes here. Tell your story!',
                    image: 'https://via.placeholder.com/80x80/ffffff/333333?text=👤',
                    buttonText: 'Get Started',
                    buttonUrl: '#'
                },
                minimal: {
                    name: 'Your Name',
                    bio: 'Your bio goes here',
                    image: 'https://via.placeholder.com/60x60/f3f4f6/6b7280?text=👤'
                }
            },
            product: {
                grid: {
                    products: [
                        { name: 'Product 1', price: 29.99, image: 'https://via.placeholder.com/120x120' },
                        { name: 'Product 2', price: 39.99, image: 'https://via.placeholder.com/120x120' }
                    ]
                },
                featured: {
                    name: 'Featured Product',
                    description: 'This is your best-selling item!',
                    price: 49.99,
                    image: 'https://via.placeholder.com/80x80',
                    buttonText: 'Buy Now'
                }
            },
            link: {
                social: {
                    links: [
                        { platform: 'Instagram', url: '#', icon: '📷' },
                        { platform: 'TikTok', url: '#', icon: '🎵' },
                        { platform: 'Twitter', url: '#', icon: '🐦' }
                    ]
                },
                buttons: {
                    buttons: [
                        { text: 'My Website', url: '#', icon: '🔗' },
                        { text: 'Newsletter', url: '#', icon: '📧' },
                        { text: 'Portfolio', url: '#', icon: '🎯' }
                    ]
                }
            },
            contact: {
                form: {
                    title: 'Get In Touch',
                    fields: ['name', 'email', 'message'],
                    submitText: 'Send Message'
                },
                info: {
                    title: 'Contact Info',
                    email: 'hello@yoursite.com',
                    phone: '+1 (555) 123-4567',
                    address: 'Your City, Country'
                }
            },
            scheduler: {
                calendar: {
                    title: 'Book a Meeting',
                    description: 'Select a date and time',
                    buttonText: 'Open Calendar'
                },
                quick: {
                    title: 'Quick Booking',
                    slots: ['9:00 AM', '1:00 PM', '3:00 PM', '5:00 PM'],
                    buttonText: 'Book Now'
                }
            }
        };
        
        return defaults[type]?.[variant] || {};
    }
    
    setupEventListeners() {
        // AI Suggestions
        document.getElementById('ai-suggest-btn')?.addEventListener('click', () => {
            this.getAISuggestions();
        });
        
        // Preview toggle
        document.getElementById('preview-btn')?.addEventListener('click', () => {
            this.togglePreview();
        });
        
        // Save
        document.getElementById('save-btn')?.addEventListener('click', () => {
            this.saveStorefront();
        });
        
        // Close builder
        document.getElementById('close-builder-btn')?.addEventListener('click', () => {
            this.closeBuilder();
        });
        
        // Block controls
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('edit-block-btn')) {
                const blockId = e.target.dataset.blockId;
                this.editBlock(blockId);
            } else if (e.target.classList.contains('delete-block-btn')) {
                const blockId = e.target.dataset.blockId;
                this.deleteBlock(blockId);
            }
        });
        
        // Modal controls
        document.getElementById('close-modal-btn')?.addEventListener('click', () => {
            this.closeModal();
        });
        
        document.getElementById('modal-cancel-btn')?.addEventListener('click', () => {
            this.closeModal();
        });
        
        document.getElementById('modal-save-btn')?.addEventListener('click', () => {
            this.saveBlockEdit();
        });
        
        // Responsive view toggles
        document.getElementById('desktop-view')?.addEventListener('click', () => {
            this.setCanvasView('desktop');
        });
        
        document.getElementById('tablet-view')?.addEventListener('click', () => {
            this.setCanvasView('tablet');
        });
        
        document.getElementById('mobile-view')?.addEventListener('click', () => {
            this.setCanvasView('mobile');
        });
    }
    
    loadBlockTemplates() {
        // Templates are already loaded in createBuilderInterface
        console.log('Block templates loaded');
    }
    
    initializeAIIntegration() {
        this.aiEndpoints = {
            suggestions: '/ai/optimize/storefront',
            generate: '/ai/build/storefront',
            health: '/ai/health'
        };
    }
    
    async getAISuggestions() {
        try {
            const storefrontData = this.getStorefrontData();
            
            const response = await fetch(this.aiEndpoints.suggestions, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    name: storefrontData.name || 'My Storefront',
                    description: storefrontData.description || 'A storefront created with InstantIn.me',
                    blocks: Array.from(this.blocks.values())
                })
            });
            
            if (response.ok) {
                const suggestions = await response.json();
                this.showAISuggestions(suggestions);
            } else {
                this.showNotification('AI suggestions temporarily unavailable', 'warning');
            }
        } catch (error) {
            console.error('AI suggestions error:', error);
            this.showNotification('Could not get AI suggestions', 'error');
        }
    }
    
    showAISuggestions(suggestions) {
        // Create suggestions modal
        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-96 overflow-y-auto">
                <div class="p-6">
                    <div class="flex items-center justify-between mb-4">
                        <h3 class="text-lg font-semibold text-gray-800">🤖 AI Suggestions</h3>
                        <button class="close-suggestions text-gray-400 hover:text-gray-600">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    <div class="space-y-4">
                        ${suggestions.recommendations?.map(rec => `
                            <div class="bg-purple-50 border border-purple-200 rounded-lg p-4">
                                <h4 class="font-semibold text-purple-800 mb-2">${rec.title}</h4>
                                <p class="text-purple-600 text-sm">${rec.description}</p>
                            </div>
                        `).join('') || '<p class="text-gray-500">No suggestions available at this time.</p>'}
                    </div>
                </div>
            </div>
        `;
        
        modal.querySelector('.close-suggestions').addEventListener('click', () => {
            modal.remove();
        });
        
        document.body.appendChild(modal);
    }
    
    togglePreview() {
        const panel = document.getElementById('preview-panel');
        const btn = document.getElementById('preview-btn');
        
        if (panel.classList.contains('hidden')) {
            panel.classList.remove('hidden');
            btn.textContent = '🚫 Hide Preview';
            this.updatePreview();
        } else {
            panel.classList.add('hidden');
            btn.textContent = '👁️ Preview';
        }
    }
    
    updatePreview() {
        const iframe = document.getElementById('preview-iframe');
        if (!iframe || iframe.classList.contains('hidden')) return;
        
        const canvasContent = document.getElementById('canvas-content');
        const previewHTML = `
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Preview</title>
                <script src="https://cdn.tailwindcss.com"></script>
                <style>
                    body { margin: 0; padding: 20px; background: #f9fafb; }
                    .preview-container { max-width: 400px; margin: 0 auto; background: white; border-radius: 8px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }
                </style>
            </head>
            <body>
                <div class="preview-container">
                    ${canvasContent?.innerHTML || '<p class="p-4 text-center text-gray-500">No content to preview</p>'}
                </div>
            </body>
            </html>
        `;
        
        iframe.srcdoc = previewHTML;
    }
    
    editBlock(blockId) {
        const blockData = this.blocks.get(blockId);
        if (!blockData) return;
        
        const modal = document.getElementById('block-edit-modal');
        const modalTitle = document.getElementById('modal-title');
        const modalContent = document.getElementById('modal-content');
        
        modalTitle.textContent = `Edit ${blockData.type} Block`;
        modalContent.innerHTML = this.generateEditForm(blockData);
        
        modal.classList.remove('hidden');
        modal.dataset.editingBlock = blockId;
    }
    
    generateEditForm(blockData) {
        const { type, variant, data } = blockData;
        
        switch (type) {
            case 'header':
                return `
                    <div class="space-y-4">
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Name</label>
                            <input type="text" id="edit-name" value="${data.name || ''}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Bio</label>
                            <textarea id="edit-bio" rows="3" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">${data.bio || ''}</textarea>
                        </div>
                        <div>
                            <label class="block text-sm font-medium text-gray-700 mb-2">Image URL</label>
                            <input type="url" id="edit-image" value="${data.image || ''}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                        </div>
                        ${variant === 'hero' ? `
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Button Text</label>
                                <input type="text" id="edit-button-text" value="${data.buttonText || ''}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Button URL</label>
                                <input type="url" id="edit-button-url" value="${data.buttonUrl || ''}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                            </div>
                        ` : ''}
                    </div>
                `;
            
            case 'contact':
                if (variant === 'info') {
                    return `
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Title</label>
                                <input type="text" id="edit-title" value="${data.title || ''}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Email</label>
                                <input type="email" id="edit-email" value="${data.email || ''}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Phone</label>
                                <input type="tel" id="edit-phone" value="${data.phone || ''}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                            </div>
                            <div>
                                <label class="block text-sm font-medium text-gray-700 mb-2">Address</label>
                                <input type="text" id="edit-address" value="${data.address || ''}" class="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500">
                            </div>
                        </div>
                    `;
                }
                break;
            
            default:
                return `
                    <div class="text-center text-gray-500">
                        <p>Edit form for ${type} (${variant}) is not yet implemented.</p>
                        <p class="text-sm mt-2">Coming soon!</p>
                    </div>
                `;
        }
        
        return '<p class="text-gray-500">Edit form not available</p>';
    }
    
    saveBlockEdit() {
        const modal = document.getElementById('block-edit-modal');
        const blockId = modal.dataset.editingBlock;
        const blockData = this.blocks.get(blockId);
        
        if (!blockData) return;
        
        // Update block data based on form inputs
        const inputs = modal.querySelectorAll('input, textarea');
        inputs.forEach(input => {
            // Convert from kebab-case to camelCase (e.g., 'edit-button-text' -> 'buttonText')
            let key = input.id.replace('edit-', '');
            key = key.replace(/-([a-z])/g, (match, letter) => letter.toUpperCase());
            if (input.value.trim()) {
                blockData.data[key] = input.value.trim();
            }
        });
        
        // Regenerate block content with updated data
        const blockElement = document.getElementById(blockId);
        if (blockElement) {
            const controls = blockElement.querySelector('.absolute');
            blockElement.innerHTML = this.generateBlockContent(blockData.type, blockData.variant, blockData.data);
            if (controls) {
                blockElement.appendChild(controls);
            }
        }
        
        this.unsavedChanges = true;
        this.updatePreview();
        this.closeModal();
    }
    
    deleteBlock(blockId) {
        if (confirm('Are you sure you want to delete this block?')) {
            const blockElement = document.getElementById(blockId);
            if (blockElement) {
                blockElement.remove();
            }
            
            this.blocks.delete(blockId);
            this.unsavedChanges = true;
            this.updatePreview();
            
            // If no blocks left, show drop zone
            const canvasContent = document.getElementById('canvas-content');
            if (canvasContent && canvasContent.children.length === 0) {
                canvasContent.innerHTML = `
                    <div id="drop-zone" class="w-full min-h-96 p-6 border-2 border-dashed border-gray-300 rounded-lg flex flex-col items-center justify-center text-center">
                        <div class="text-gray-400 text-lg mb-2">🎨</div>
                        <div class="text-gray-600 font-medium mb-1">Start Building Your Page</div>
                        <div class="text-gray-500 text-sm">Drag blocks from the sidebar to begin</div>
                    </div>
                `;
                this.setupDragAndDrop();
            }
        }
    }
    
    closeModal() {
        const modal = document.getElementById('block-edit-modal');
        modal.classList.add('hidden');
        modal.dataset.editingBlock = '';
    }
    
    setCanvasView(view) {
        const canvas = document.getElementById('canvas-content');
        const buttons = ['desktop-view', 'tablet-view', 'mobile-view'];
        
        // Update button states
        buttons.forEach(btnId => {
            const btn = document.getElementById(btnId);
            if (btnId === `${view}-view`) {
                btn.className = 'px-3 py-1 text-sm bg-blue-600 text-white rounded';
            } else {
                btn.className = 'px-3 py-1 text-sm bg-gray-300 text-gray-700 rounded';
            }
        });
        
        // Update canvas width
        switch (view) {
            case 'desktop':
                canvas.className = 'max-w-md mx-auto bg-white rounded-lg shadow-lg min-h-96 relative transition-all duration-300';
                break;
            case 'tablet':
                canvas.className = 'max-w-xs mx-auto bg-white rounded-lg shadow-lg min-h-96 relative transition-all duration-300';
                break;
            case 'mobile':
                canvas.className = 'max-w-[280px] mx-auto bg-white rounded-lg shadow-lg min-h-96 relative transition-all duration-300';
                break;
        }
    }
    
    async saveStorefront() {
        try {
            const storefrontData = this.getStorefrontData();
            
            // Here you would typically save to your backend
            console.log('Saving storefront:', storefrontData);
            
            // For now, just show success message
            this.showNotification('Storefront saved successfully!', 'success');
            this.unsavedChanges = false;
            
        } catch (error) {
            console.error('Save error:', error);
            this.showNotification('Failed to save storefront', 'error');
        }
    }
    
    getStorefrontData() {
        const canvasContent = document.getElementById('canvas-content');
        return {
            name: 'My Storefront',
            description: 'Created with InstantIn.me page builder',
            blocks: Array.from(this.blocks.entries()).map(([id, data]) => ({
                id,
                ...data
            })),
            html: canvasContent?.innerHTML || '',
            metadata: {
                totalBlocks: this.blocks.size,
                lastModified: new Date().toISOString()
            }
        };
    }
    
    closeBuilder() {
        if (this.unsavedChanges) {
            if (!confirm('You have unsaved changes. Are you sure you want to close?')) {
                return;
            }
        }
        
        const builder = document.getElementById('page-builder');
        builder.classList.add('hidden');
    }
    
    open(storefrontData = null) {
        const builder = document.getElementById('page-builder');
        builder.classList.remove('hidden');
        
        if (storefrontData) {
            this.loadStorefront(storefrontData);
        }
    }
    
    loadStorefront(data) {
        this.currentStorefront = data;
        // Implementation for loading existing storefront data
        console.log('Loading storefront:', data);
    }
    
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm ${
            type === 'success' ? 'bg-green-100 text-green-800 border border-green-200' :
            type === 'error' ? 'bg-red-100 text-red-800 border border-red-200' :
            type === 'warning' ? 'bg-yellow-100 text-yellow-800 border border-yellow-200' :
            'bg-blue-100 text-blue-800 border border-blue-200'
        }`;
        
        notification.innerHTML = `
            <div class="flex items-center justify-between">
                <span>${message}</span>
                <button class="ml-4 text-current opacity-50 hover:opacity-100" onclick="this.parentElement.parentElement.remove()">
                    ✕
                </button>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
}

// Initialize page builder when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.pageBuilder = new PageBuilder();
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PageBuilder;
} 