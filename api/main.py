"""
FastAPI Analytical API
Exposes insights from the medical telegram data warehouse.
"""
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from typing import List, Optional
import re
from collections import Counter

from api.database import get_db
from api import schemas

# Create FastAPI app
app = FastAPI(
    title="Medical Telegram Analytics API",
    description="API for analyzing Ethiopian medical business data from Telegram channels",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Medical Telegram Analytics API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "top_products": "/api/reports/top-products",
            "channel_activity": "/api/channels/{channel_name}/activity",
            "search_messages": "/api/search/messages",
            "visual_content": "/api/reports/visual-content"
        }
    }


@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint."""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")


@app.get("/api/reports/top-products", response_model=List[schemas.ProductMention], tags=["Reports"])
async def get_top_products(
    limit: int = Query(10, ge=1, le=100, description="Number of top products to return"),
    db: Session = Depends(get_db)
):
    """
    Get the top most frequently mentioned products or terms across all channels.
    
    This endpoint analyzes message text to identify frequently mentioned terms
    that are likely to be product names.
    """
    try:
        # Query messages
        query = text("""
            SELECT 
                message_text,
                channel_username,
                views
            FROM marts.fct_messages
            WHERE message_length > 0
        """)
        
        result = db.execute(query)
        rows = result.fetchall()
        
        # Extract terms (simple word tokenization)
        # In production, you'd use NLP for better extraction
        term_data = {}
        for row in rows:
            text_content = row[0]
            channel = row[1]
            views = row[2]
            
            # Extract words (filter common words)
            words = re.findall(r'\b[A-Za-z]{4,}\b', text_content)
            
            for word in words:
                word_lower = word.lower()
                if word_lower not in term_data:
                    term_data[word_lower] = {
                        'channels': set(),
                        'count': 0,
                        'total_views': 0
                    }
                term_data[word_lower]['channels'].add(channel)
                term_data[word_lower]['count'] += 1
                term_data[word_lower]['total_views'] += views
        
        # Convert to list and sort
        products = []
        for term, data in term_data.items():
            if data['count'] >= 3:  # Filter out rare terms
                products.append({
                    'term': term,
                    'mention_count': data['count'],
                    'channel_count': len(data['channels']),
                    'avg_views': round(data['total_views'] / data['count'], 2)
                })
        
        # Sort by mention count and return top N
        products.sort(key=lambda x: x['mention_count'], reverse=True)
        return products[:limit]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching top products: {str(e)}")


@app.get("/api/channels/{channel_name}/activity", response_model=schemas.ChannelActivity, tags=["Channels"])
async def get_channel_activity(
    channel_name: str,
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Get posting activity and trends for a specific channel.
    
    Returns daily activity metrics and overall channel statistics.
    """
    try:
        # Check if channel exists
        channel_check = text("""
            SELECT channel_username, channel_name, total_posts
            FROM marts.dim_channels
            WHERE channel_username = :channel
        """)
        channel_result = db.execute(channel_check, {"channel": channel_name}).fetchone()
        
        if not channel_result:
            raise HTTPException(status_code=404, detail=f"Channel '{channel_name}' not found")
        
        # Get daily activity
        daily_query = text("""
            SELECT 
                d.full_date,
                COUNT(f.message_id) as post_count,
                SUM(f.views) as total_views,
                SUM(f.forwards) as total_forwards,
                COUNT(CASE WHEN f.has_image THEN 1 END) as posts_with_images
            FROM marts.fct_messages f
            JOIN marts.dim_dates d ON f.date_key = d.date_key
            WHERE f.channel_username = :channel
                AND d.full_date >= CURRENT_DATE - INTERVAL ':days days'
            GROUP BY d.full_date
            ORDER BY d.full_date DESC
        """)
        
        daily_result = db.execute(daily_query, {"channel": channel_name, "days": days})
        daily_activity = []
        for row in daily_result:
            daily_activity.append({
                "date": row[0],
                "post_count": row[1],
                "total_views": row[2] or 0,
                "total_forwards": row[3] or 0,
                "posts_with_images": row[4]
            })
        
        # Get most active day and hour
        most_active_day_query = text("""
            SELECT d.day_name, COUNT(*) as count
            FROM marts.fct_messages f
            JOIN marts.dim_dates d ON f.date_key = d.date_key
            WHERE f.channel_username = :channel
            GROUP BY d.day_name
            ORDER BY count DESC
            LIMIT 1
        """)
        most_active_day = db.execute(most_active_day_query, {"channel": channel_name}).fetchone()
        
        most_active_hour_query = text("""
            SELECT message_hour, COUNT(*) as count
            FROM marts.fct_messages
            WHERE channel_username = :channel
            GROUP BY message_hour
            ORDER BY count DESC
            LIMIT 1
        """)
        most_active_hour = db.execute(most_active_hour_query, {"channel": channel_name}).fetchone()
        
        # Calculate average posts per day
        avg_posts = channel_result[2] / max(days, 1)
        
        return {
            "channel_username": channel_result[0],
            "channel_name": channel_result[1],
            "total_posts": channel_result[2],
            "date_range": {
                "days": days,
                "from": daily_activity[-1]["date"] if daily_activity else None,
                "to": daily_activity[0]["date"] if daily_activity else None
            },
            "daily_activity": daily_activity,
            "avg_posts_per_day": round(avg_posts, 2),
            "most_active_day": most_active_day[0].strip() if most_active_day else "Unknown",
            "most_active_hour": most_active_hour[0] if most_active_hour else 0
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching channel activity: {str(e)}")


@app.get("/api/search/messages", response_model=List[schemas.MessageDetail], tags=["Search"])
async def search_messages(
    query: str = Query(..., min_length=1, max_length=200, description="Search keyword"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """
    Search for messages containing a specific keyword.
    
    Performs case-insensitive search on message text.
    """
    try:
        search_query = text("""
            SELECT 
                message_id,
                channel_username,
                message_date,
                message_text,
                has_image,
                views,
                forwards,
                message_length,
                message_length_category,
                engagement_category,
                forward_rate_percentage
            FROM marts.fct_messages
            WHERE LOWER(message_text) LIKE LOWER(:query)
            ORDER BY views DESC
            LIMIT :limit
        """)
        
        result = db.execute(search_query, {"query": f"%{query}%", "limit": limit})
        
        messages = []
        for row in result:
            messages.append({
                "message_id": row[0],
                "channel_username": row[1],
                "message_date": row[2],
                "message_text": row[3],
                "has_image": row[4],
                "views": row[5],
                "forwards": row[6],
                "message_length": row[7],
                "message_length_category": row[8],
                "engagement_category": row[9],
                "forward_rate_percentage": row[10]
            })
        
        return messages
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching messages: {str(e)}")


@app.get("/api/reports/visual-content", response_model=schemas.VisualContentStats, tags=["Reports"])
async def get_visual_content_stats(db: Session = Depends(get_db)):
    """
    Get statistics about image usage and visual content across channels.
    
    Includes YOLO detection results and engagement analysis by image type.
    """
    try:
        # Total images
        total_images_query = text("SELECT COUNT(*) FROM marts.fct_image_detections")
        total_images = db.execute(total_images_query).scalar()
        
        # Images by category
        category_query = text("""
            SELECT image_category, COUNT(*) as count
            FROM marts.fct_image_detections
            GROUP BY image_category
            ORDER BY count DESC
        """)
        category_result = db.execute(category_query)
        images_by_category = {row[0]: row[1] for row in category_result}
        
        # Images by channel
        channel_query = text("""
            SELECT channel_username, COUNT(*) as count
            FROM marts.fct_image_detections
            GROUP BY channel_username
            ORDER BY count DESC
        """)
        channel_result = db.execute(channel_query)
        images_by_channel = {row[0]: row[1] for row in channel_result}
        
        # Average detections per image
        avg_detections_query = text("""
            SELECT AVG(num_detections)
            FROM marts.fct_image_detections
        """)
        avg_detections = db.execute(avg_detections_query).scalar() or 0.0
        
        # Engagement by category
        engagement_query = text("""
            SELECT 
                image_category,
                AVG(views) as avg_views,
                AVG(forwards) as avg_forwards
            FROM marts.fct_image_detections
            GROUP BY image_category
        """)
        engagement_result = db.execute(engagement_query)
        engagement_by_category = {}
        for row in engagement_result:
            engagement_by_category[row[0]] = {
                "avg_views": round(row[1], 2),
                "avg_forwards": round(row[2], 2)
            }
        
        return {
            "total_images": total_images or 0,
            "images_by_category": images_by_category,
            "images_by_channel": images_by_channel,
            "avg_detections_per_image": round(avg_detections, 2),
            "engagement_by_category": engagement_by_category
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching visual content stats: {str(e)}")


@app.get("/api/channels", response_model=List[schemas.ChannelStats], tags=["Channels"])
async def list_channels(db: Session = Depends(get_db)):
    """
    List all channels with their statistics.
    """
    try:
        query = text("""
            SELECT 
                channel_username,
                channel_name,
                channel_type,
                total_posts,
                posts_with_images,
                image_usage_percentage,
                avg_views,
                avg_forwards,
                total_views,
                total_forwards,
                first_post_date,
                last_post_date
            FROM marts.dim_channels
            ORDER BY total_posts DESC
        """)
        
        result = db.execute(query)
        
        channels = []
        for row in result:
            channels.append({
                "channel_username": row[0],
                "channel_name": row[1],
                "channel_type": row[2],
                "total_posts": row[3],
                "posts_with_images": row[4],
                "image_usage_percentage": row[5],
                "avg_views": row[6],
                "avg_forwards": row[7],
                "total_views": row[8],
                "total_forwards": row[9],
                "first_post_date": row[10],
                "last_post_date": row[11]
            })
        
        return channels
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching channels: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
