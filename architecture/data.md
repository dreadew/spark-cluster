# Example Data Architecture Documentation

### Raw datasets

```
s3://raw/
├── hotels/
│   └── hotels.csv
│
├── reservations/
│   ├── standard/Hotel_Reservations.csv
│   ├── standard_2/Hotel.csv
│   ├── detailed/hotel_booking_data_cleaned.csv
│   └── external/makemytrip_com-travel_sample.csv
│
└── reviews/
    ├── detailed/Hotel_Reviews_2.csv
    ├── aggregated/hotel_reviews.csv
    └── by_city/*.csv
        ├── beijing.csv
        ├── chicago.csv
        ├── dubai.csv
        ├── las-vegas.csv
        ├── london.csv
        ├── montreal.csv
        ├── new-delhi.csv
        ├── new-york-city.csv
        ├── san-francisco.csv
        └── shanghai.csv
```

## 🎯 Production schemas

### Hotels
- **Partition by**: по `country`, `city`

### Reviews Production
- **Partition by**: по `review_date`

### Reservations Production
- **Partition by**: по `arrival_year`, `arrival_month`

### Hotels Mapping

| Production Field | Source | Raw Field |
|-----------------|--------|-----------|
| hotel_id | Generated | UUID based on name + location |
| hotel_name | makemytrip | HotelName |
| hotel_code | makemytrip | HotelCode |
| rating | makemytrip | HotelRating → CAST(AS DOUBLE) |
| country | makemytrip | countyName |
| city | makemytrip | cityName |
| address | makemytrip | Address |
| zip_code | makemytrip | PinCode |
| latitude | external | latitude → CAST(AS DOUBLE) |
| longitude | external | longitude → CAST(AS DOUBLE) |
| facilities | makemytrip | HotelFacilities → SPLIT(',') |
| phone | makemytrip | PhoneNumber |
| website | makemytrip | HotelWebsiteUrl |

### Reviews Mapping

| Production Field | Source | Raw Field |
|-----------------|--------|-----------|
| review_id | Generated | UUID or doc_id |
| hotel_id | Lookup | hotel_name → hotels.hotel_id |
| hotel_name | **detailed** | hotel_name |
| reviewer_nationality | **detailed** | reviewer_nationality |
| reviewer_type | **detailed** | tags → PARSE |
| review_date | **detailed** | review_date → CAST(AS DATE) |
| review_text | aggregated | review_text (fallback) |
| positive_review | **detailed** | positive_review |
| negative_review | **detailed** | negative_review |
| overall_rating | **detailed** | reviewer_score → CAST(AS DOUBLE) |
| cleanliness_rating | by_city | cleanliness → CAST(AS DOUBLE) |
| room_rating | by_city | room → CAST(AS DOUBLE) |
| service_rating | by_city | service → CAST(AS DOUBLE) |
| location_rating | by_city | location → CAST(AS DOUBLE) |
| value_rating | by_city | value → CAST(AS DOUBLE) |
| comfort_rating | by_city | comfort → CAST(AS DOUBLE) |

### Reservations Mapping

| Production Field | Source | Raw Field |
|-----------------|--------|-----------|
| booking_id | standard/detailed | booking_id / Generated |
| hotel_id | Lookup | hotel name → hotels.hotel_id |
| num_adults | standard | no_of_adults → CAST(AS INT) |
| num_children | standard | no_of_children → CAST(AS INT) |
| num_babies | detailed | babies → CAST(AS INT) |
| arrival_date | standard | arrival_year + arrival_month + arrival_date |
| num_weekend_nights | standard | no_of_weekend_nights → CAST(AS INT) |
| num_week_nights | standard | no_of_week_nights → CAST(AS INT) |
| room_type | standard | room_type_reserved |
| lead_time | standard | lead_time → CAST(AS INT) |
| market_segment | standard | market_segment_type |
| avg_price_per_room | standard | avg_price_per_room → CAST(AS DOUBLE) |
| meal_plan | standard | type_of_meal_plan |
| car_parking_required | standard | required_car_parking_space → CAST(AS BOOLEAN) |
| num_special_requests | standard | no_of_special_requests → CAST(AS INT) |
| is_repeated_guest | standard | repeated_guest → CAST(AS BOOLEAN) |
| previous_cancellations | standard | no_of_previous_cancellations → CAST(AS INT) |
| booking_status | standard | booking_status |
| is_canceled | detailed | is_canceled → CAST(AS BOOLEAN) |

## 📝 Data Quality Rules

### Hotels
- ✅ hotel_name NOT NULL
- ✅ rating BETWEEN 0 AND 5
- ✅ city NOT NULL
- ✅ Deduplicate by (hotel_name, city, address)

### Reviews
- ✅ review_date NOT NULL
- ✅ overall_rating BETWEEN 0 AND 10
- ✅ All specific ratings BETWEEN 0 AND 10
- ✅ review_text NOT NULL OR negative_review NOT NULL

### Reservations
- ✅ booking_id NOT NULL
- ✅ arrival_date >= booking_date
- ✅ num_adults > 0
- ✅ num_nights > 0
- ✅ avg_price_per_room > 0
