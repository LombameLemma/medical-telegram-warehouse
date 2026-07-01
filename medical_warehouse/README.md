# Medical Warehouse dbt Project

This dbt project transforms raw Telegram data into a dimensional data warehouse optimized for analytics.

## Project Structure

```
medical_warehouse/
├── dbt_project.yml          # Project configuration
├── profiles.yml             # Database connection profiles
├── packages.yml             # External package dependencies
├── models/
│   ├── staging/             # Staging layer - clean raw data
│   │   ├── sources.yml      # Source definitions
│   │   └── stg_telegram_messages.sql
│   └── marts/               # Marts layer - dimensional models
│       ├── dim_channels.sql
│       ├── dim_dates.sql
│       ├── fct_messages.sql
│       ├── fct_image_detections.sql
│       └── schema.yml       # Tests and documentation
└── tests/                   # Custom data tests
    ├── assert_no_future_messages.sql
    ├── assert_positive_views.sql
    └── assert_valid_message_length.sql
```

## Data Flow

```
raw.telegram_messages (PostgreSQL)
    ↓
staging.stg_telegram_messages (VIEW)
    ↓
    ├─► marts.dim_channels (TABLE)
    ├─► marts.dim_dates (TABLE)
    └─► marts.fct_messages (TABLE)
            ↓
        marts.fct_image_detections (TABLE)
```

## Models

### Staging Layer

#### stg_telegram_messages
**Type**: View  
**Purpose**: Clean and standardize raw telegram data

**Transformations**:
- Type casting (timestamps, integers)
- Text trimming and normalization
- Null handling with COALESCE
- Calculated fields (message_length, is_weekend)
- Data validation filters

**Key Fields**:
- message_id: Unique identifier
- channel_username: Normalized channel name
- message_date: Properly typed timestamp
- message_text: Cleaned text content
- has_image: Boolean media flag
- views, forwards: Engagement metrics

### Marts Layer

#### dim_channels
**Type**: Table  
**Grain**: One row per channel

**Purpose**: Channel master data and aggregated metrics

**Key Fields**:
- channel_key: Surrogate key (MD5 hash of username)
- channel_username: Natural key
- channel_type: Classification (Pharmaceutical/Cosmetics/Medical/Other)
- total_posts: Count of all posts
- avg_views: Average views per post
- image_usage_percentage: % of posts with images

**Business Logic**:
- Channel classification based on name matching
- Aggregated metrics calculated from all messages
- Updated on each dbt run

#### dim_dates
**Type**: Table  
**Grain**: One row per date

**Purpose**: Calendar dimension for time-series analysis

**Key Fields**:
- date_key: Surrogate key
- full_date: Actual date value
- year, month, day: Date parts
- day_of_week: 0 = Sunday, 6 = Saturday
- day_name: Full day name
- is_weekend: Boolean flag
- week_start_date/end_date: Week boundaries

**Generation**:
- Date spine generated from min/max message dates
- All dates in range included for continuous time series
- Pre-calculated calendar attributes

#### fct_messages
**Type**: Table  
**Grain**: One row per message

**Purpose**: Core fact table with message-level metrics

**Key Fields**:
- message_id: Primary key
- channel_key: Foreign key to dim_channels
- date_key: Foreign key to dim_dates
- message_text: Full message content
- views, forwards: Additive metrics
- views_per_character: Calculated metric
- forward_rate_percentage: Ratio metric
- message_length_category: Dimension attribute
- engagement_category: Dimension attribute

**Measures**:
- Additive: views, forwards, message_length
- Non-additive: forward_rate_percentage, views_per_character
- Semi-additive: None

#### fct_image_detections
**Type**: Table  
**Grain**: One row per image

**Purpose**: YOLO detection results integrated with message data

**Key Fields**:
- message_id: Links to fct_messages
- channel_key, date_key: Conformed dimensions
- image_category: promotional/product_display/lifestyle/other
- detected_classes: Comma-separated object list
- num_detections: Count of detected objects
- avg_confidence: Average detection confidence
- views, forwards: Denormalized for convenience

**Integration**:
- Loads from raw.yolo_detections (populated by Python script)
- Joins with fct_messages on message_id
- Only includes messages with images

## Testing

### Schema Tests (in schema.yml)

**Uniqueness Tests**:
- dim_channels.channel_key
- dim_dates.date_key
- fct_messages.message_id

**Not Null Tests**:
- All primary keys
- All foreign keys
- Critical business fields

**Relationship Tests**:
- fct_messages.channel_key → dim_channels.channel_key
- fct_messages.date_key → dim_dates.date_key

**Accepted Values Tests**:
- channel_type: 'Pharmaceutical', 'Cosmetics', 'Medical', 'Other'
- message_length_category: 'Empty', 'Short', 'Medium', 'Long', 'Very Long'
- engagement_category: 'Low', 'Medium', 'High', 'Very High'

### Custom Tests (in tests/)

**assert_no_future_messages**:
- Ensures no messages have dates in the future
- Query returns 0 rows to pass

**assert_positive_views**:
- Ensures view and forward counts are non-negative
- Query returns 0 rows to pass

**assert_valid_message_length**:
- Ensures calculated message_length matches actual text length
- Query returns 0 rows to pass

## Running dbt

### Setup

```bash
# Install packages
dbt deps

# Test connection
dbt debug
```

### Development

```bash
# Run all models
dbt run

# Run specific model
dbt run --select stg_telegram_messages

# Run specific folder
dbt run --select staging.*
dbt run --select marts.*

# Run tests
dbt test

# Test specific model
dbt test --select fct_messages
```

### Documentation

```bash
# Generate documentation
dbt docs generate

# Serve documentation site
dbt docs serve
# Opens browser to http://localhost:8080
```

### Production

```bash
# Full refresh (rebuild from scratch)
dbt run --full-refresh

# Run with specific profile
dbt run --profile prod

# Run and test
dbt build
```

## Configuration

### profiles.yml

```yaml
medical_warehouse:
  target: dev
  outputs:
    dev:
      type: postgres
      host: "{{ env_var('DB_HOST', 'localhost') }}"
      port: 5432
      user: "{{ env_var('DB_USER', 'postgres') }}"
      password: "{{ env_var('DB_PASSWORD') }}"
      dbname: "{{ env_var('DB_NAME', 'medical_warehouse') }}"
      schema: public
      threads: 4
```

### Environment Variables

Required:
- DB_HOST: PostgreSQL host
- DB_PORT: PostgreSQL port
- DB_NAME: Database name
- DB_USER: Database user
- DB_PASSWORD: Database password

## Best Practices

### Model Naming

- `stg_<source>_<table>`: Staging models
- `dim_<entity>`: Dimension tables
- `fct_<event>`: Fact tables

### SQL Style

- Use CTEs for readability
- One model per file
- Use meaningful aliases
- Comment complex logic
- Use dbt_utils for common operations

### Testing

- Add tests for all primary keys
- Test foreign key relationships
- Add custom tests for business rules
- Test after every model change

### Performance

- Staging models as views (no storage cost)
- Marts as tables (fast query performance)
- Add indexes in post-hooks if needed
- Consider incremental models for large tables

## Troubleshooting

### Issue: Connection Failed

```bash
# Test connection
dbt debug

# Check environment variables
echo $DB_HOST
echo $DB_USER
```

### Issue: Model Not Found

```bash
# Parse project to check for errors
dbt parse

# Compile specific model
dbt compile --select model_name
```

### Issue: Tests Failing

```bash
# Run failing test with details
dbt test --select test_name

# See compiled SQL
cat target/compiled/medical_warehouse/tests/test_name.sql
```

### Issue: Slow Performance

```bash
# Run with debug logging
dbt run --debug

# Check query plans in PostgreSQL
psql -c "EXPLAIN ANALYZE <query>"
```

## Resources

- [dbt Documentation](https://docs.getdbt.com/)
- [dbt Discourse](https://discourse.getdbt.com/)
- [dbt Style Guide](https://github.com/dbt-labs/corp/blob/main/dbt_style_guide.md)
- [Dimensional Modeling](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/)
