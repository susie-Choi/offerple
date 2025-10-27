"""ROTA Command Line Interface."""

import click
import logging
from pathlib import Path

from ..config import get_config, load_config
from ..__version__ import __version__

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@click.group()
@click.version_option(version=__version__)
@click.option('--config', type=click.Path(exists=True), help='Configuration file')
@click.pass_context
def cli(ctx, config):
    """
    ROTA - Real-time Offensive Threat Assessment
    
    Zero-day vulnerability prediction using behavioral signals.
    """
    ctx.ensure_object(dict)
    
    if config:
        ctx.obj['config'] = load_config(Path(config))
    else:
        ctx.obj['config'] = get_config()


# Spokes commands (Data Collection)
@cli.group()
def spokes():
    """Data collection commands."""
    pass


@spokes.command('collect-cve')
@click.option('--cve-ids', multiple=True, help='Specific CVE IDs to collect')
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.option('--keyword', help='Keyword to search for')
@click.option('--max-results', default=100, help='Maximum results')
@click.option('--output', default='data/raw', help='Output directory')
def collect_cve(cve_ids, start_date, end_date, keyword, max_results, output):
    """Collect CVE data from NVD."""
    from ..spokes import CVECollector
    
    collector = CVECollector(output_dir=output)
    
    if cve_ids:
        stats = collector.collect(cve_ids=list(cve_ids))
    elif start_date and end_date:
        stats = collector.collect(start_date=start_date, end_date=end_date, max_results=max_results)
    elif keyword:
        stats = collector.collect(keyword=keyword, max_results=max_results)
    else:
        click.echo("Error: Must provide --cve-ids, date range, or --keyword")
        return
    
    click.echo(f"✓ Collected {stats['total_records']} CVEs")
    click.echo(f"✓ Saved to {stats['output_dir']}")


@spokes.command('collect-epss')
@click.option('--cve-ids', multiple=True, help='Specific CVE IDs')
@click.option('--date', help='Specific date (YYYY-MM-DD)')
@click.option('--output', default='data/raw', help='Output directory')
def collect_epss(cve_ids, date, output):
    """Collect EPSS scores from FIRST.org."""
    from ..spokes import EPSSCollector
    
    collector = EPSSCollector(output_dir=output)
    
    if cve_ids:
        stats = collector.collect(cve_ids=list(cve_ids), date=date)
    else:
        stats = collector.collect(date=date)
    
    click.echo(f"✓ Collected {stats['total_records']} EPSS scores")
    click.echo(f"✓ Saved to {stats['output_dir']}")


@spokes.command('collect-kev')
@click.option('--output', default='data/raw', help='Output directory')
def collect_kev(output):
    """Collect CISA KEV catalog."""
    from ..spokes import KEVCollector
    
    collector = KEVCollector(output_dir=output)
    stats = collector.collect()
    
    click.echo(f"✓ Collected {stats['total_records']} KEV entries")
    click.echo(f"✓ Saved to {stats['output_dir']}")


@spokes.command('collect-cwe')
@click.option('--output', default='data/raw', help='Output directory')
def collect_cwe(output):
    """Collect CWE database from MITRE."""
    from ..spokes import CWECollector
    
    collector = CWECollector(output_dir=output)
    stats = collector.collect()
    
    click.echo(f"✓ Collected {stats['total_records']} CWE entries")
    click.echo(f"✓ Saved to {stats['output_dir']}")


# Hub commands (Data Integration)
@cli.group()
def hub():
    """Data integration commands."""
    pass


@hub.command('load-cve')
@click.argument('jsonl_file', type=click.Path(exists=True))
@click.option('--neo4j-uri', envvar='NEO4J_URI', help='Neo4j URI')
@click.option('--neo4j-user', envvar='NEO4J_USER', default='neo4j', help='Neo4j username')
@click.option('--neo4j-password', envvar='NEO4J_PASSWORD', help='Neo4j password')
def load_cve(jsonl_file, neo4j_uri, neo4j_user, neo4j_password):
    """Load CVE data into Neo4j."""
    from ..hub import Neo4jConnection, DataLoader
    
    with Neo4jConnection(neo4j_uri, neo4j_user, neo4j_password) as conn:
        loader = DataLoader(conn)
        stats = loader.load_cve_data(Path(jsonl_file))
    
    click.echo(f"✓ Created {stats['nodes_created']} CVE nodes")
    click.echo(f"✓ Updated {stats['nodes_updated']} CVE nodes")


@hub.command('load-epss')
@click.argument('jsonl_file', type=click.Path(exists=True))
@click.option('--neo4j-uri', envvar='NEO4J_URI', help='Neo4j URI')
@click.option('--neo4j-user', envvar='NEO4J_USER', default='neo4j', help='Neo4j username')
@click.option('--neo4j-password', envvar='NEO4J_PASSWORD', help='Neo4j password')
def load_epss(jsonl_file, neo4j_uri, neo4j_user, neo4j_password):
    """Load EPSS data into Neo4j."""
    from ..hub import Neo4jConnection, DataLoader
    
    with Neo4jConnection(neo4j_uri, neo4j_user, neo4j_password) as conn:
        loader = DataLoader(conn)
        stats = loader.load_epss_data(Path(jsonl_file))
    
    click.echo(f"✓ Created {stats['relationships_created']} EPSS relationships")


@hub.command('load-kev')
@click.argument('jsonl_file', type=click.Path(exists=True))
@click.option('--neo4j-uri', envvar='NEO4J_URI', help='Neo4j URI')
@click.option('--neo4j-user', envvar='NEO4J_USER', default='neo4j', help='Neo4j username')
@click.option('--neo4j-password', envvar='NEO4J_PASSWORD', help='Neo4j password')
def load_kev(jsonl_file, neo4j_uri, neo4j_user, neo4j_password):
    """Load KEV data into Neo4j."""
    from ..hub import Neo4jConnection, DataLoader
    
    with Neo4jConnection(neo4j_uri, neo4j_user, neo4j_password) as conn:
        loader = DataLoader(conn)
        stats = loader.load_kev_data(Path(jsonl_file))
    
    click.echo(f"✓ Created {stats['nodes_created']} KEV nodes")
    click.echo(f"✓ Enriched {stats['cves_enriched']} CVE nodes")


@hub.command('load-cwe')
@click.argument('jsonl_file', type=click.Path(exists=True))
@click.option('--neo4j-uri', envvar='NEO4J_URI', help='Neo4j URI')
@click.option('--neo4j-user', envvar='NEO4J_USER', default='neo4j', help='Neo4j username')
@click.option('--neo4j-password', envvar='NEO4J_PASSWORD', help='Neo4j password')
def load_cwe(jsonl_file, neo4j_uri, neo4j_user, neo4j_password):
    """Load CWE data into Neo4j."""
    from ..hub import Neo4jConnection, DataLoader
    
    with Neo4jConnection(neo4j_uri, neo4j_user, neo4j_password) as conn:
        loader = DataLoader(conn)
        stats = loader.load_cwe_data(Path(jsonl_file))
    
    click.echo(f"✓ Created {stats['nodes_created']} CWE nodes")
    click.echo(f"✓ Created {stats['relationships_created']} relationships")


@hub.command('status')
@click.option('--neo4j-uri', envvar='NEO4J_URI', help='Neo4j URI')
@click.option('--neo4j-user', envvar='NEO4J_USER', default='neo4j', help='Neo4j username')
@click.option('--neo4j-password', envvar='NEO4J_PASSWORD', help='Neo4j password')
def hub_status(neo4j_uri, neo4j_user, neo4j_password):
    """Check Neo4j hub status."""
    from ..hub import Neo4jConnection
    
    conn = Neo4jConnection(neo4j_uri, neo4j_user, neo4j_password)
    
    if conn.verify_connectivity():
        click.echo("✓ Neo4j hub is connected")
    else:
        click.echo("✗ Neo4j hub connection failed")


# Wheel commands (Clustering)
@cli.group()
def wheel():
    """Clustering and pattern analysis commands."""
    pass


@wheel.command('cluster')
def cluster():
    """Run vulnerability clustering."""
    click.echo("Clustering not yet implemented")


# Oracle commands (Prediction)
@cli.group()
def oracle():
    """Prediction and risk assessment commands."""
    pass


@oracle.command('predict')
@click.argument('cve_id')
def predict(cve_id):
    """Predict exploitation risk for a CVE."""
    click.echo(f"Prediction for {cve_id} not yet implemented")


# Axle commands (Evaluation)
@cli.group()
def axle():
    """Evaluation and validation commands."""
    pass


@axle.command('validate')
def validate():
    """Run temporal validation."""
    click.echo("Validation not yet implemented")


if __name__ == '__main__':
    cli()


__all__ = ['cli']
