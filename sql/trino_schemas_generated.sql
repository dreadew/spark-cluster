-- ============================================================
-- AUTO-GENERATED TRINO SCHEMAS FOR RAW DATA
-- Generated from CSV files in raw/ directory
-- ============================================================

-- Schema: raw_hotels
CREATE SCHEMA IF NOT EXISTS hive.raw_hotels;
USE hive.raw_hotels;

-- Table: hotels
-- Source: raw/hotels/hotels.csv
-- Columns: county_code, county_name, city_code, city_name, hotel_code...
CREATE TABLE IF NOT EXISTS hotels (
    county_code VARCHAR,
    county_name VARCHAR,
    city_code VARCHAR,
    city_name VARCHAR,
    hotel_code VARCHAR,
    hotel_name VARCHAR,
    hotel_rating VARCHAR,
    address VARCHAR,
    attractions VARCHAR,
    description VARCHAR,
    fax_number VARCHAR,
    hotel_facilities VARCHAR,
    map VARCHAR,
    phone_number VARCHAR,
    pin_code VARCHAR,
    hotel_website_url VARCHAR
)
WITH (
    external_location = 's3://raw/hotels/',
    format = 'CSV',
    skip_header_line_count = 1
);


-- Schema: raw_reservations
CREATE SCHEMA IF NOT EXISTS hive.raw_reservations;
USE hive.raw_reservations;

-- Table: reservations_detailed
-- Source: raw/reservations/detailed/hotel_booking_data_cleaned.csv
-- Columns: hotel, is_canceled, lead_time, arrival_date_year, arrival_date_month...
CREATE TABLE IF NOT EXISTS reservations_detailed (
    hotel VARCHAR,
    is_canceled VARCHAR,
    lead_time VARCHAR,
    arrival_date_year VARCHAR,
    arrival_date_month VARCHAR,
    arrival_date_week_number VARCHAR,
    arrival_date_day_of_month VARCHAR,
    stays_in_weekend_nights VARCHAR,
    stays_in_week_nights VARCHAR,
    adults VARCHAR,
    children VARCHAR,
    babies VARCHAR,
    meal VARCHAR,
    country VARCHAR,
    market_segment VARCHAR,
    distribution_channel VARCHAR,
    is_repeated_guest VARCHAR,
    previous_cancellations VARCHAR,
    previous_bookings_not_canceled VARCHAR,
    reserved_room_type VARCHAR,
    assigned_room_type VARCHAR,
    booking_changes VARCHAR,
    deposit_type VARCHAR,
    agent VARCHAR,
    company VARCHAR,
    days_in_waiting_list VARCHAR,
    customer_type VARCHAR,
    adr VARCHAR,
    required_car_parking_spaces VARCHAR,
    total_of_special_requests VARCHAR,
    reservation_status VARCHAR,
    reservation_status_date VARCHAR
)
WITH (
    external_location = 's3://raw/reservations/detailed/',
    format = 'CSV',
    skip_header_line_count = 1
);

-- Table: reservations_external
-- Source: raw/reservations/external/makemytrip_com-travel_sample.csv
-- Columns: area, city, country, crawl_date, highlight_value...
CREATE TABLE IF NOT EXISTS reservations_external (
    area VARCHAR,
    city VARCHAR,
    country VARCHAR,
    crawl_date VARCHAR,
    highlight_value VARCHAR,
    hotel_overview VARCHAR,
    hotel_star_rating VARCHAR,
    image_urls VARCHAR,
    in_your_room VARCHAR,
    is_value_plus VARCHAR,
    latitude VARCHAR,
    longitude VARCHAR,
    mmt_holidayiq_review_count VARCHAR,
    mmt_location_rating VARCHAR,
    mmt_review_count VARCHAR,
    mmt_review_rating VARCHAR,
    mmt_review_score VARCHAR,
    mmt_traveller_type_review_count VARCHAR,
    mmt_tripadvisor_count VARCHAR,
    pageurl VARCHAR,
    property_address VARCHAR,
    property_id VARCHAR,
    property_name VARCHAR,
    property_type VARCHAR,
    qts VARCHAR,
    query_time_stamp VARCHAR,
    room_types VARCHAR,
    site_review_count VARCHAR,
    site_review_rating VARCHAR,
    sitename VARCHAR,
    state VARCHAR,
    traveller_rating VARCHAR,
    uniq_id VARCHAR
)
WITH (
    external_location = 's3://raw/reservations/external/',
    format = 'CSV',
    skip_header_line_count = 1
);

-- Table: reservations_standard
-- Source: raw/reservations/standard/Hotel Reservations.csv
-- Columns: booking_id, no_of_adults, no_of_children, no_of_weekend_nights, no_of_week_nights...
CREATE TABLE IF NOT EXISTS reservations_standard (
    booking_id VARCHAR,
    no_of_adults VARCHAR,
    no_of_children VARCHAR,
    no_of_weekend_nights VARCHAR,
    no_of_week_nights VARCHAR,
    type_of_meal_plan VARCHAR,
    required_car_parking_space VARCHAR,
    room_type_reserved VARCHAR,
    lead_time VARCHAR,
    arrival_year VARCHAR,
    arrival_month VARCHAR,
    arrival_date VARCHAR,
    market_segment_type VARCHAR,
    repeated_guest VARCHAR,
    no_of_previous_cancellations VARCHAR,
    no_of_previous_bookings_not_canceled VARCHAR,
    avg_price_per_room VARCHAR,
    no_of_special_requests VARCHAR,
    booking_status VARCHAR
)
WITH (
    external_location = 's3://raw/reservations/standard/',
    format = 'CSV',
    skip_header_line_count = 1
);

-- Table: reservations_standard_2
-- Source: raw/reservations/standard_2/Hotel.csv
-- Columns: id, n_adults, n_children, weekend_nights, week_nights...
CREATE TABLE IF NOT EXISTS reservations_standard_2 (
    id VARCHAR,
    n_adults VARCHAR,
    n_children VARCHAR,
    weekend_nights VARCHAR,
    week_nights VARCHAR,
    meal_plan VARCHAR,
    car_parking_space VARCHAR,
    room_type VARCHAR,
    lead_time VARCHAR,
    year VARCHAR,
    month VARCHAR,
    date VARCHAR,
    market_segment VARCHAR,
    repeated_guest VARCHAR,
    previous_cancellations VARCHAR,
    previous_bookings_not_canceled VARCHAR,
    avg_room_price VARCHAR,
    special_requests VARCHAR,
    status VARCHAR
)
WITH (
    external_location = 's3://raw/reservations/standard_2/',
    format = 'CSV',
    skip_header_line_count = 1
);


-- Schema: raw_reviews
CREATE SCHEMA IF NOT EXISTS hive.raw_reviews;
USE hive.raw_reviews;

-- Table: reviews_aggregated
-- Source: raw/reviews/aggregated/hotel_reviews.csv
-- Columns: index, name, area, review_date, rating_attribute...
CREATE TABLE IF NOT EXISTS reviews_aggregated (
    index VARCHAR,
    name VARCHAR,
    area VARCHAR,
    review_date VARCHAR,
    rating_attribute VARCHAR,
    rating_out_of_10 VARCHAR,
    review_text VARCHAR
)
WITH (
    external_location = 's3://raw/reviews/aggregated/',
    format = 'CSV',
    skip_header_line_count = 1
);

-- Table: reviews_by_city
-- Source: raw/reviews/by_city/beijing.csv
-- Columns: doc_id, hotel_name, hotel_url, street, city...
CREATE TABLE IF NOT EXISTS reviews_by_city (
    doc_id VARCHAR,
    hotel_name VARCHAR,
    hotel_url VARCHAR,
    street VARCHAR,
    city VARCHAR,
    state VARCHAR,
    country VARCHAR,
    zip VARCHAR,
    class VARCHAR,
    price VARCHAR,
    num_reviews VARCHAR,
    cleanliness VARCHAR,
    room VARCHAR,
    service VARCHAR,
    location VARCHAR,
    value VARCHAR,
    comfort VARCHAR,
    overall_rating VARCHAR,
    source VARCHAR
)
WITH (
    external_location = 's3://raw/reviews/by_city/',
    format = 'CSV',
    skip_header_line_count = 1
);

-- Table: reviews_detailed
-- Source: raw/reviews/detailed/Hotel_Reviews.csv
-- Columns: hotel_address, additional_number_of_scoring, review_date, average_score, hotel_name...
CREATE TABLE IF NOT EXISTS reviews_detailed (
    hotel_address VARCHAR,
    additional_number_of_scoring VARCHAR,
    review_date VARCHAR,
    average_score VARCHAR,
    hotel_name VARCHAR,
    reviewer_nationality VARCHAR,
    negative_review VARCHAR,
    review_total_negative_word_counts VARCHAR,
    total_number_of_reviews VARCHAR,
    positive_review VARCHAR,
    review_total_positive_word_counts VARCHAR,
    total_number_of_reviews_reviewer_has_given VARCHAR,
    reviewer_score VARCHAR,
    tags VARCHAR,
    days_since_review VARCHAR,
    lat VARCHAR,
    lng VARCHAR
)
WITH (
    external_location = 's3://raw/reviews/detailed/',
    format = 'CSV',
    skip_header_line_count = 1
);

