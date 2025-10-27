"""
Example widgets for testing the carousel and other custom components.

Import and use these in your langgraph_chatkit_server.py to test widgets.
"""

from .custom_widgets import (
    create_image_carousel,
    create_yes_no_buttons,
    create_detail_card,
)


# Example 1: Product Carousel
PRODUCT_CAROUSEL_EXAMPLE = create_image_carousel(
    title="Featured Products",
    items=[
        {
            "id": "prod_1",
            "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop",
            "title": "Wireless Headphones",
            "description": "Premium sound quality with noise cancellation",
            "link_url": "https://www.example.com/products/headphones",
            "link_label": "Shop Now"
        },
        {
            "id": "prod_2",
            "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=300&fit=crop",
            "title": "Smart Watch",
            "description": "Track your fitness and stay connected",
            "link_url": "https://www.example.com/products/watch",
            "link_label": "Shop Now"
        },
        {
            "id": "prod_3",
            "image_url": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&h=300&fit=crop",
            "title": "Designer Sunglasses",
            "description": "UV protection with style",
            "link_url": "https://www.example.com/products/sunglasses",
            "link_label": "Shop Now"
        },
        {
            "id": "prod_4",
            "image_url": "https://images.unsplash.com/photo-1491553895911-0055eca6402d?w=400&h=300&fit=crop",
            "title": "Leather Sneakers",
            "description": "Comfortable and durable footwear",
            "link_url": "https://www.example.com/products/sneakers",
            "link_label": "Shop Now"
        },
        {
            "id": "prod_5",
            "image_url": "https://images.unsplash.com/photo-1553062407-98eeb64c6a62?w=400&h=300&fit=crop",
            "title": "Backpack",
            "description": "Spacious and stylish travel companion",
            "link_url": "https://www.example.com/products/backpack",
            "link_label": "Shop Now"
        }
    ]
)


# Example 2: Blog Posts Carousel
BLOG_CAROUSEL_EXAMPLE = create_image_carousel(
    title="Recommended Reading",
    items=[
        {
            "id": "blog_1",
            "image_url": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=400&h=300&fit=crop",
            "title": "Getting Started with ChatKit",
            "description": "Learn the basics of building chat interfaces",
            "link_url": "https://docs.chatkit.studio/getting-started",
            "link_label": "Read Article"
        },
        {
            "id": "blog_2",
            "image_url": "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b?w=400&h=300&fit=crop",
            "title": "Advanced Widget Patterns",
            "description": "Master complex widget compositions",
            "link_url": "https://docs.chatkit.studio/advanced-widgets",
            "link_label": "Read Article"
        },
        {
            "id": "blog_3",
            "image_url": "https://images.unsplash.com/photo-1488590528505-98d2b5aba04b?w=400&h=300&fit=crop",
            "title": "LangGraph Integration Guide",
            "description": "Connect LangGraph with ChatKit seamlessly",
            "link_url": "https://docs.langgraph.com/chatkit",
            "link_label": "Read Article"
        }
    ]
)


# Example 3: Simple Yes/No
YES_NO_EXAMPLE = create_yes_no_buttons(
    question="Would you like to see more examples?",
    action_type="show_more_examples",
    context={"category": "widgets"}
)


# Example 4: Image Gallery
IMAGE_GALLERY_EXAMPLE = create_image_carousel(
    title="Photo Gallery",
    items=[
        {
            "id": f"photo_{i}",
            "image_url": f"https://picsum.photos/400/300?random={i}",
            "title": f"Photo {i}",
            "description": f"Beautiful image #{i}",
            "link_url": f"https://picsum.photos/1200/800?random={i}",
            "link_label": "View Full Size"
        }
        for i in range(1, 8)
    ]
)


# Example 5: Drilldown Product Carousel
PRODUCT_DRILLDOWN_CAROUSEL = create_image_carousel(
    title="Products (Click for Details)",
    items=[
        {
            "id": "prod_1",
            "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400&h=300&fit=crop",
            "title": "Wireless Headphones",
            "description": "Premium sound quality",
            "item_data": {
                "title": "Wireless Headphones",
                "image_url": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=800&h=600&fit=crop",
                "price": "$299.99",
                "stock": 24,
                "rating": 4.8,
                "reviews": 2847,
                "brand": "AudioTech",
                "color": "Matte Black",
                "warranty": "2 years",
                "full_description": "Premium wireless headphones featuring active noise cancellation, 40-hour battery life, and studio-quality sound. Comfortable over-ear design with memory foam cushions. Includes carrying case and audio cable for wired use.",
            },
        },
        {
            "id": "prod_2",
            "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=300&fit=crop",
            "title": "Smart Watch",
            "description": "Track your fitness",
            "item_data": {
                "title": "Smart Watch Pro",
                "image_url": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=800&h=600&fit=crop",
                "price": "$399.99",
                "stock": 12,
                "rating": 4.6,
                "reviews": 1523,
                "brand": "TechFit",
                "color": "Space Gray",
                "battery_life": "7 days",
                "water_resistance": "50m",
                "full_description": "Advanced smartwatch with comprehensive health monitoring, GPS tracking, and seamless smartphone integration. Features include heart rate monitoring, sleep tracking, workout detection, and mobile payments.",
            },
        },
        {
            "id": "prod_3",
            "image_url": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=400&h=300&fit=crop",
            "title": "Designer Sunglasses",
            "description": "UV protection with style",
            "item_data": {
                "title": "Designer Sunglasses",
                "image_url": "https://images.unsplash.com/photo-1572635196237-14b3f281503f?w=800&h=600&fit=crop",
                "price": "$189.99",
                "stock": 8,
                "rating": 4.9,
                "reviews": 892,
                "brand": "LuxVision",
                "frame_material": "Titanium",
                "lens_type": "Polarized",
                "uv_protection": "100% UV400",
                "full_description": "Handcrafted designer sunglasses with titanium frame and polarized lenses. Offers superior UV protection while maintaining exceptional clarity. Includes premium case and cleaning cloth.",
            },
        },
    ],
    enable_drilldown=True,
    scrollable=True,
)


def get_example_widget(widget_name: str):
    """
    Get an example widget by name.

    Available widgets:
    - "products" - Product carousel with external links
    - "products_drilldown" - Product carousel with drilldown details
    - "blog" - Blog posts carousel
    - "yes_no" - Yes/no buttons
    - "gallery" - Image gallery

    Usage:
        widget = get_example_widget("products")
        yield ThreadItemDoneEvent(item=WidgetItem(..., widget=widget))
    """
    widgets = {
        "products": PRODUCT_CAROUSEL_EXAMPLE,
        "products_drilldown": PRODUCT_DRILLDOWN_CAROUSEL,
        "blog": BLOG_CAROUSEL_EXAMPLE,
        "yes_no": YES_NO_EXAMPLE,
        "gallery": IMAGE_GALLERY_EXAMPLE,
    }

    return widgets.get(widget_name, YES_NO_EXAMPLE)
