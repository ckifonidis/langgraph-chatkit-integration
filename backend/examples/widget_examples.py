"""
Example widgets for testing the carousel and other custom components.

Import and use these in your langgraph_chatkit_server.py to test widgets.
"""

from .custom_widgets import create_image_carousel, create_yes_no_buttons


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


def get_example_widget(widget_name: str):
    """
    Get an example widget by name.

    Available widgets:
    - "products" - Product carousel
    - "blog" - Blog posts carousel
    - "yes_no" - Yes/no buttons
    - "gallery" - Image gallery

    Usage:
        widget = get_example_widget("products")
        yield ThreadItemDoneEvent(item=WidgetItem(..., widget=widget))
    """
    widgets = {
        "products": PRODUCT_CAROUSEL_EXAMPLE,
        "blog": BLOG_CAROUSEL_EXAMPLE,
        "yes_no": YES_NO_EXAMPLE,
        "gallery": IMAGE_GALLERY_EXAMPLE,
    }

    return widgets.get(widget_name, YES_NO_EXAMPLE)
