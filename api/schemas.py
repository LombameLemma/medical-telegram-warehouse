"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


# Channel schemas
class ChannelBase(BaseModel):
    channel_username: str
    channel_name: str
    channel_type: str


class ChannelStats(ChannelBase):
    """Channel with statistics."""
    total_posts: int
    posts_with_images: int
    image_usage_percentage: float
    avg_views: float
    avg_forwards: float
    total_views: int
    total_forwards: int
    first_post_date: datetime
    last_post_date: datetime
    
    class Config:
        from_attributes = True


# Message schemas
class MessageBase(BaseModel):
    message_id: int
    channel_username: str
    message_date: datetime
    message_text: str
    has_image: bool
    views: int
    forwards: int


class MessageDetail(MessageBase):
    """Detailed message information."""
    message_length: int
    message_length_category: str
    engagement_category: str
    forward_rate_percentage: float
    
    class Config:
        from_attributes = True


# Product/Top Terms schemas
class ProductMention(BaseModel):
    """Top mentioned product or term."""
    term: str = Field(..., description="Product name or term")
    mention_count: int = Field(..., description="Number of mentions")
    channel_count: int = Field(..., description="Number of channels mentioning")
    avg_views: float = Field(..., description="Average views for messages with this term")


# Channel Activity schemas
class DailyActivity(BaseModel):
    """Daily posting activity."""
    date: date
    post_count: int
    total_views: int
    total_forwards: int
    posts_with_images: int


class ChannelActivity(BaseModel):
    """Channel activity summary."""
    channel_username: str
    channel_name: str
    total_posts: int
    date_range: dict
    daily_activity: List[DailyActivity]
    avg_posts_per_day: float
    most_active_day: str
    most_active_hour: int


# Visual Content schemas
class VisualContentStats(BaseModel):
    """Statistics about visual content."""
    total_images: int
    images_by_category: dict
    images_by_channel: dict
    avg_detections_per_image: float
    engagement_by_category: dict


# Image Detection schemas
class ImageDetection(BaseModel):
    """Image detection information."""
    message_id: int
    channel_name: str
    image_category: str
    detected_classes: str
    num_detections: int
    avg_confidence: float
    views: int
    forwards: int
    
    class Config:
        from_attributes = True


# Search schemas
class SearchRequest(BaseModel):
    """Search request parameters."""
    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of results")


# Generic response schemas
class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None


class SuccessResponse(BaseModel):
    """Success response."""
    message: str
    data: Optional[dict] = None
