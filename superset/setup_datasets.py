"""
Automatically configure Superset with Trino connections and dashboards.
This script runs after Superset initialization to set up:
- Trino Delta Lake connection
- Trino Hive connection
- Sample datasets and dashboards
"""

import os
import sys
import time
import logging
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def wait_for_trino(max_attempts=30):
    """Wait for Trino to be ready."""
    import socket
    trino_host = os.environ.get('TRINO_HOST', 'trino')
    trino_port = int(os.environ.get('TRINO_PORT', '8080'))
    
    for i in range(max_attempts):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((trino_host, trino_port))
            sock.close()
            if result == 0:
                logger.info(f"Trino is ready at {trino_host}:{trino_port}")
                time.sleep(5)  # Additional wait for Trino to fully initialize
                return True
        except Exception as e:
            logger.debug(f"Waiting for Trino... ({i+1}/{max_attempts}): {e}")
        time.sleep(2)
    
    logger.warning(f"Trino not available at {trino_host}:{trino_port}, continuing anyway...")
    return False


def wait_for_superset():
    """Wait for Superset to be ready."""
    import requests
    max_attempts = 30
    for i in range(max_attempts):
        try:
            response = requests.get("http://localhost:8088/health")
            if response.status_code == 200:
                logger.info("Superset is ready")
                return True
        except Exception as e:
            logger.debug(f"Waiting for Superset... ({i+1}/{max_attempts})")
            time.sleep(2)
    logger.error("Superset did not become ready in time")
    return False


def get_or_create_database(database_name: str, sqlalchemy_uri: str) -> Optional[int]:
    """Create a database connection if it doesn't exist."""
    from superset import db
    from superset.models.core import Database
    
    # Check if database already exists
    existing_db = db.session.query(Database).filter_by(database_name=database_name).first()
    if existing_db:
        logger.info(f"Database '{database_name}' already exists with id={existing_db.id}")
        return existing_db.id
    
    logger.info(f"Creating database connection: {database_name}")
    
    try:
        database = Database(
            database_name=database_name,
            sqlalchemy_uri=sqlalchemy_uri,
            expose_in_sqllab=True,
            allow_ctas=True,
            allow_cvas=True,
            allow_dml=True,
            allow_run_async=True,
            cache_timeout=None,
            extra='{"allows_virtual_table_explore": true, "engine_params": {"connect_args": {"source": "superset"}}}'
        )
        db.session.add(database)
        db.session.commit()
        logger.info(f"Database '{database_name}' created successfully with id={database.id}")
        return database.id
    except Exception as e:
        logger.error(f"Failed to create database '{database_name}': {e}")
        db.session.rollback()
        return None


def test_database_connection(database_id: int, database_name: str) -> bool:
    """Test database connection."""
    from superset import db
    from superset.models.core import Database
    
    database = db.session.query(Database).get(database_id)
    if not database:
        logger.error(f"Database with id={database_id} not found")
        return False
    
    try:
        logger.info(f"Testing connection to '{database_name}'...")
        database.get_sqla_engine()
        logger.info(f"Connection to '{database_name}' successful")
        return True
    except Exception as e:
        logger.warning(f"Connection test failed for '{database_name}': {e}")
        return False


def create_dataset(database_id: int, schema: str, table_name: str, dataset_name: str) -> Optional[int]:
    """Create a dataset (table reference) if it doesn't exist."""
    from superset import db
    from superset.connectors.sqla.models import SqlaTable
    
    # Check if dataset already exists
    existing_dataset = db.session.query(SqlaTable).filter_by(
        database_id=database_id,
        schema=schema,
        table_name=table_name
    ).first()
    
    if existing_dataset:
        logger.info(f"Dataset '{dataset_name}' already exists with id={existing_dataset.id}")
        return existing_dataset.id
    
    logger.info(f"Creating dataset: {dataset_name} ({schema}.{table_name})")
    
    try:
        dataset = SqlaTable(
            table_name=table_name,
            schema=schema,
            database_id=database_id,
            sql=None,
        )
        db.session.add(dataset)
        db.session.commit()
        
        # Refresh columns
        try:
            dataset.fetch_metadata()
            db.session.commit()
            logger.info(f"Dataset '{dataset_name}' created successfully with id={dataset.id}")
        except Exception as e:
            logger.warning(f"Could not fetch metadata for '{dataset_name}': {e}")
            logger.warning("Table may not exist or may be empty - dataset created but may not work in charts")
        
        return dataset.id
    except Exception as e:
        logger.error(f"Failed to create dataset '{dataset_name}': {e}")
        db.session.rollback()
        return None


def create_chart(slice_name: str, viz_type: str, datasource_id: int, params: dict, datasource_name: str = "") -> Optional[int]:
    """Create a chart if it doesn't exist."""
    from superset import db
    from superset.models.slice import Slice
    import json
    
    # Check if chart already exists
    existing_slice = db.session.query(Slice).filter_by(slice_name=slice_name).first()
    if existing_slice:
        logger.info(f"Chart '{slice_name}' already exists with id={existing_slice.id}")
        return existing_slice.id
    
    logger.info(f"Creating chart: {slice_name} for datasource_id={datasource_id}")
    
    try:
        chart = Slice(
            slice_name=slice_name,
            viz_type=viz_type,
            datasource_id=datasource_id,
            datasource_type='table',
            params=json.dumps(params),
            datasource_name=datasource_name or f"table_{datasource_id}"
        )
        db.session.add(chart)
        db.session.commit()
        logger.info(f"Chart '{slice_name}' created successfully with id={chart.id}")
        return chart.id
    except Exception as e:
        logger.error(f"Failed to create chart '{slice_name}': {e}")
        logger.error(f"Params were: {params}")
        db.session.rollback()
        return None


def create_dashboard(dashboard_title: str, slug: str, chart_ids: list) -> Optional[int]:
    """Create a dashboard with charts if it doesn't exist."""
    from superset import db
    from superset.models.dashboard import Dashboard
    from superset.models.slice import Slice
    import json
    
    # Check if dashboard already exists
    existing_dashboard = db.session.query(Dashboard).filter_by(dashboard_title=dashboard_title).first()
    if existing_dashboard:
        logger.info(f"Dashboard '{dashboard_title}' already exists with id={existing_dashboard.id}")
        return existing_dashboard.id
    
    logger.info(f"Creating dashboard: {dashboard_title} with {len(chart_ids)} charts")
    
    try:
        # Get chart slice names for better layout
        chart_names = {}
        for chart_id in chart_ids:
            chart = db.session.query(Slice).get(chart_id)
            if chart:
                chart_names[chart_id] = chart.slice_name
        
        # Create grid layout - simpler structure
        chart_elements = []
        for idx, chart_id in enumerate(chart_ids):
            col = (idx % 2) * 24  # 0 or 24 (half width each)
            row = (idx // 2) * 16  # Stack rows
            chart_key = f"CHART-{chart_id}"
            chart_elements.append(chart_key)
        
        position_json = {
            "DASHBOARD_VERSION_KEY": "v2",
            "ROOT_ID": {
                "type": "ROOT",
                "id": "ROOT_ID",
                "children": ["GRID_ID"]
            },
            "GRID_ID": {
                "type": "GRID",
                "id": "GRID_ID",
                "children": chart_elements,
                "parents": ["ROOT_ID"]
            }
        }
        
        # Add each chart with proper positioning
        for idx, chart_id in enumerate(chart_ids):
            col = (idx % 2) * 24
            row = (idx // 2) * 16
            chart_key = f"CHART-{chart_id}"
            
            position_json[chart_key] = {
                "type": "CHART",
                "id": chart_key,
                "children": [],
                "parents": ["ROOT_ID", "GRID_ID"],
                "meta": {
                    "width": 24,  # Full width for single column, or 24 for half
                    "height": 16,
                    "chartId": chart_id,
                    "sliceName": chart_names.get(chart_id, f"Chart {chart_id}")
                }
            }
        
        dashboard = Dashboard(
            dashboard_title=dashboard_title,
            slug=slug,
            position_json=json.dumps(position_json),
            published=True,
        )
        
        # Link charts to dashboard
        for chart_id in chart_ids:
            chart = db.session.query(Slice).get(chart_id)
            if chart:
                dashboard.slices.append(chart)
        
        db.session.add(dashboard)
        db.session.commit()
        logger.info(f"Dashboard '{dashboard_title}' created successfully with id={dashboard.id}")
        return dashboard.id
    except Exception as e:
        logger.error(f"Failed to create dashboard '{dashboard_title}': {e}")
        import traceback
        traceback.print_exc()
        db.session.rollback()
        return None


def setup_connections_and_datasets():
    """Set up Trino connections and sample datasets."""
    
    # Database connections configuration
    databases = [
        {
            "name": "Trino - Delta Lake (Production)",
            "uri": "trino://admin@trino:8080/delta",
            "schemas": {
                "prod_hotels": ["hotels"],
                "prod_reviews": ["reviews"],
                "prod_reservations": ["reservations"],
            }
        },
        {
            "name": "Trino - Hive (Raw Data)",
            "uri": "trino://admin@trino:8080/hive",
            "schemas": {
                "raw_hotels": ["hotels_makemytrip"],
                "raw_reviews": ["reviews_detailed", "reviews_aggregated", "reviews_by_city"],
                "raw_reservations": ["reservations_standard", "reservations_standard_2", "reservations_detailed", "makemytrip_external"],
            }
        }
    ]
    
    created_databases = {}
    created_datasets = {}
    
    # Create database connections
    for db_config in databases:
        db_id = get_or_create_database(db_config["name"], db_config["uri"])
        if db_id:
            created_databases[db_config["name"]] = db_id
            test_database_connection(db_id, db_config["name"])
            
            # Create datasets for each schema/table
            for schema, tables in db_config["schemas"].items():
                for table in tables:
                    dataset_name = f"{schema}.{table}"
                    dataset_id = create_dataset(db_id, schema, table, dataset_name)
                    if dataset_id:
                        created_datasets[dataset_name] = dataset_id
    
    return created_databases, created_datasets


def setup_sample_charts_and_dashboards(created_datasets: dict):
    """Create sample charts and dashboards."""
    
    prod_chart_ids = []
    raw_chart_ids = []
    
    # Production charts (note: these may be empty until ETL runs)
    if "prod_hotels.hotels" in created_datasets:
        hotels_dataset_id = created_datasets["prod_hotels.hotels"]
        
        # Chart 1: Hotels by Country
        chart_id = create_chart(
            slice_name="[Prod] Hotels by Country",
            viz_type="dist_bar",
            datasource_id=hotels_dataset_id,
            datasource_name="prod_hotels.hotels",
            params={
                "metrics": ["count"],
                "groupby": ["country"],
                "row_limit": 15,
                "adhoc_filters": [],
                "order_desc": True,
            }
        )
        if chart_id:
            prod_chart_ids.append(chart_id)
        
        # Chart 2: Hotels by City
        chart_id = create_chart(
            slice_name="[Prod] Top Cities by Hotel Count",
            viz_type="dist_bar",
            datasource_id=hotels_dataset_id,
            datasource_name="prod_hotels.hotels",
            params={
                "metrics": ["count"],
                "groupby": ["city"],
                "row_limit": 10,
                "order_desc": True,
            }
        )
        if chart_id:
            prod_chart_ids.append(chart_id)
    
    if "prod_reviews.reviews" in created_datasets:
        reviews_dataset_id = created_datasets["prod_reviews.reviews"]
        
        # Chart 3: Average Rating by Nationality
        chart_id = create_chart(
            slice_name="[Prod] Avg Rating by Reviewer Nationality",
            viz_type="dist_bar",
            datasource_id=reviews_dataset_id,
            datasource_name="prod_reviews.reviews",
            params={
                "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "overall_rating"}, "aggregate": "AVG", "label": "Avg Rating"}],
                "groupby": ["reviewer_nationality"],
                "row_limit": 15,
                "order_desc": True,
            }
        )
        if chart_id:
            prod_chart_ids.append(chart_id)
    
    if "prod_reservations.reservations" in created_datasets:
        reservations_dataset_id = created_datasets["prod_reservations.reservations"]
        
        # Chart 4: Bookings by Market Segment
        chart_id = create_chart(
            slice_name="[Prod] Bookings by Market Segment",
            viz_type="pie",
            datasource_id=reservations_dataset_id,
            datasource_name="prod_reservations.reservations",
            params={
                "metrics": ["count"],
                "groupby": ["market_segment"],
                "row_limit": 10,
            }
        )
        if chart_id:
            prod_chart_ids.append(chart_id)
    
    # Raw data charts - using actual column names from schemas
    if "raw_hotels.hotels_makemytrip" in created_datasets:
        raw_hotels_dataset_id = created_datasets["raw_hotels.hotels_makemytrip"]
        
        # Chart 1: Hotels by City (city_name column)
        chart_id = create_chart(
            slice_name="[Raw] Hotels by City",
            viz_type="dist_bar",
            datasource_id=raw_hotels_dataset_id,
            datasource_name="raw_hotels.hotels_makemytrip",
            params={
                "metrics": ["count"],
                "groupby": ["city_name"],
                "row_limit": 15,
                "adhoc_filters": [],
                "order_desc": True,
            }
        )
        if chart_id:
            raw_chart_ids.append(chart_id)
        
        # Chart 2: Hotels by Rating
        chart_id = create_chart(
            slice_name="[Raw] Hotels by Rating Distribution",
            viz_type="pie",
            datasource_id=raw_hotels_dataset_id,
            datasource_name="raw_hotels.hotels_makemytrip",
            params={
                "metrics": ["count"],
                "groupby": ["hotel_rating"],
                "row_limit": 10,
            }
        )
        if chart_id:
            raw_chart_ids.append(chart_id)
        
        # Chart 3: Total Hotels Count
        chart_id = create_chart(
            slice_name="[Raw] Total Hotels",
            viz_type="big_number_total",
            datasource_id=raw_hotels_dataset_id,
            datasource_name="raw_hotels.hotels_makemytrip",
            params={
                "metric": "count",
            }
        )
        if chart_id:
            raw_chart_ids.append(chart_id)
        
        # Chart 4: Hotels by Country
        chart_id = create_chart(
            slice_name="[Raw] Hotels by Country",
            viz_type="dist_bar",
            datasource_id=raw_hotels_dataset_id,
            datasource_name="raw_hotels.hotels_makemytrip",
            params={
                "metrics": ["count"],
                "groupby": ["county_name"],
                "row_limit": 15,
                "order_desc": True,
            }
        )
        if chart_id:
            raw_chart_ids.append(chart_id)
    
    if "raw_reviews.reviews_by_city" in created_datasets:
        raw_reviews_city_dataset_id = created_datasets["raw_reviews.reviews_by_city"]
        
        # Chart 4: Reviews by City
        chart_id = create_chart(
            slice_name="[Raw] Reviews by City",
            viz_type="dist_bar",
            datasource_id=raw_reviews_city_dataset_id,
            datasource_name="raw_reviews.reviews_by_city",
            params={
                "metrics": ["count"],
                "groupby": ["city"],
                "row_limit": 12,
                "order_desc": True,
            }
        )
        if chart_id:
            raw_chart_ids.append(chart_id)
        
        # Chart 5: Average Overall Rating by City
        chart_id = create_chart(
            slice_name="[Raw] Avg Rating by City",
            viz_type="dist_bar",
            datasource_id=raw_reviews_city_dataset_id,
            datasource_name="raw_reviews.reviews_by_city",
            params={
                "metrics": [{"expressionType": "SIMPLE", "column": {"column_name": "overall_rating"}, "aggregate": "AVG", "label": "Avg Rating"}],
                "groupby": ["city"],
                "row_limit": 10,
                "order_desc": True,
            }
        )
        if chart_id:
            raw_chart_ids.append(chart_id)
        
        # Chart 6: Service vs Cleanliness Scatter
        chart_id = create_chart(
            slice_name="[Raw] Service vs Cleanliness Ratings",
            viz_type="scatter",
            datasource_id=raw_reviews_city_dataset_id,
            datasource_name="raw_reviews.reviews_by_city",
            params={
                "metrics": ["count"],
                "x": "service",
                "y": "cleanliness",
                "row_limit": 500,
            }
        )
        if chart_id:
            raw_chart_ids.append(chart_id)
    
    if "raw_reviews.reviews_detailed" in created_datasets:
        raw_reviews_detailed_dataset_id = created_datasets["raw_reviews.reviews_detailed"]
        
        # Chart 7: Top Hotels by Review Count
        chart_id = create_chart(
            slice_name="[Raw] Most Reviewed Hotels",
            viz_type="dist_bar",
            datasource_id=raw_reviews_detailed_dataset_id,
            datasource_name="raw_reviews.reviews_detailed",
            params={
                "metrics": ["count"],
                "groupby": ["hotel_name"],
                "row_limit": 15,
                "order_desc": True,
            }
        )
        if chart_id:
            raw_chart_ids.append(chart_id)
        
        # Chart 8: Reviews by Nationality
        chart_id = create_chart(
            slice_name="[Raw] Top Reviewer Nationalities",
            viz_type="pie",
            datasource_id=raw_reviews_detailed_dataset_id,
            datasource_name="raw_reviews.reviews_detailed",
            params={
                "metrics": ["count"],
                "groupby": ["reviewer_nationality"],
                "row_limit": 10,
            }
        )
        if chart_id:
            raw_chart_ids.append(chart_id)
    
    if "raw_reservations.reservations_detailed" in created_datasets:
        raw_reservations_dataset_id = created_datasets["raw_reservations.reservations_detailed"]
        
        # Chart 9: Bookings by Country
        chart_id = create_chart(
            slice_name="[Raw] Bookings by Country",
            viz_type="dist_bar",
            datasource_id=raw_reservations_dataset_id,
            datasource_name="raw_reservations.reservations_detailed",
            params={
                "metrics": ["count"],
                "groupby": ["country"],
                "row_limit": 15,
                "order_desc": True,
            }
        )
        if chart_id:
            raw_chart_ids.append(chart_id)
        
        # Chart 10: Bookings by Market Segment
        chart_id = create_chart(
            slice_name="[Raw] Market Segment Distribution",
            viz_type="pie",
            datasource_id=raw_reservations_dataset_id,
            datasource_name="raw_reservations.reservations_detailed",
            params={
                "metrics": ["count"],
                "groupby": ["market_segment"],
                "row_limit": 10,
            }
        )
        if chart_id:
            raw_chart_ids.append(chart_id)
        
        # Chart 11: Canceled vs Completed Bookings
        chart_id = create_chart(
            slice_name="[Raw] Cancellation Status",
            viz_type="pie",
            datasource_id=raw_reservations_dataset_id,
            datasource_name="raw_reservations.reservations_detailed",
            params={
                "metrics": ["count"],
                "groupby": ["is_canceled"],
                "row_limit": 5,
            }
        )
        if chart_id:
            raw_chart_ids.append(chart_id)
        
        # Chart 12: Total Reservations
        chart_id = create_chart(
            slice_name="[Raw] Total Reservations",
            viz_type="big_number_total",
            datasource_id=raw_reservations_dataset_id,
            datasource_name="raw_reservations.reservations_detailed",
            params={
                "metric": "count",
            }
        )
        if chart_id:
            raw_chart_ids.append(chart_id)
    
    # Create dashboards
    all_chart_ids = []
    
    if prod_chart_ids:
        dashboard_id = create_dashboard(
            dashboard_title="Production - Hotel Analytics",
            slug="production-hotel-analytics",
            chart_ids=prod_chart_ids
        )
        if dashboard_id:
            logger.info(f"Production dashboard created. Access at: http://localhost:8088/superset/dashboard/{dashboard_id}/")
        all_chart_ids.extend(prod_chart_ids)
    
    if raw_chart_ids:
        dashboard_id = create_dashboard(
            dashboard_title="Raw Data - Hotel Overview",
            slug="raw-data-hotel-overview",
            chart_ids=raw_chart_ids
        )
        if dashboard_id:
            logger.info(f"Raw data dashboard created. Access at: http://localhost:8088/superset/dashboard/{dashboard_id}/")
        all_chart_ids.extend(raw_chart_ids)
    
    return all_chart_ids, len(prod_chart_ids), len(raw_chart_ids)


def main():
    """Main setup function."""
    logger.info("Starting Superset auto-configuration...")
    
    # Wait for Trino to be ready
    wait_for_trino()
    
    # Wait a bit for Superset to fully start
    time.sleep(5)
    
    try:
        # Set up Flask app context - create app properly
        from superset.app import create_app
        app = create_app()
        
        with app.app_context():
            # Create connections and datasets
            created_databases, created_datasets = setup_connections_and_datasets()
            
            logger.info(f"Created/verified {len(created_databases)} database connections")
            logger.info(f"Created/verified {len(created_datasets)} datasets")
            
            # Create sample charts and dashboards
            chart_ids, prod_count, raw_count = setup_sample_charts_and_dashboards(created_datasets)
            
            logger.info(f"Created {len(chart_ids)} sample charts")
            logger.info("Superset auto-configuration completed successfully!")
            
            # Print summary
            logger.info("\n" + "="*60)
            logger.info("SUPERSET SETUP COMPLETE")
            logger.info("="*60)
            logger.info("Database Connections:")
            for db_name in created_databases.keys():
                logger.info(f"  ✓ {db_name}")
            logger.info(f"\nDatasets: {len(created_datasets)}")
            logger.info(f"Charts: {len(chart_ids)}")
            logger.info(f"  - Production charts: {prod_count}")
            logger.info(f"  - Raw data charts: {raw_count}")
            logger.info("\nDashboards Created:")
            logger.info("  - Production - Hotel Analytics (production Delta Lake data)")
            logger.info("  - Raw Data - Hotel Overview (raw CSV data from S3)")
            logger.info("\nAccess Superset at: http://localhost:8088")
            logger.info("Login: admin / admin")
            logger.info("\nImportant Notes:")
            logger.info("  ⚠ Production charts may be empty until ETL pipeline runs")
            logger.info("  ✓ Raw data charts should work immediately if data is loaded")
            logger.info("\nIf charts show errors, ensure:")
            logger.info("  1. Data is loaded to S3: bash upload_raw_to_s3.sh")
            logger.info("  2. Schemas are created: bash create_trino_schemas.sh")
            logger.info("  3. Trino can query tables: docker exec trino trino --execute 'SELECT COUNT(*) FROM hive.raw_hotels.hotels_makemytrip'")
            logger.info("="*60 + "\n")
            
    except Exception as e:
        logger.error(f"Auto-configuration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
