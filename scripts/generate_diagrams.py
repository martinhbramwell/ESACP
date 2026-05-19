#!/usr/bin/env python3
"""
ESACP Diagram Generator
Converts architecture.yml to Mermaid diagrams

Usage:
    python3 generate_diagrams.py
    python3 generate_diagrams.py --output ../docker/observability/grafana/provisioning/dashboards/json/
"""

import argparse
import yaml
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


def load_architecture(yaml_file):
    """Load architecture from YAML file"""
    with open(yaml_file, 'r') as f:
        return yaml.safe_load(f)


def generate_mermaid(architecture, template_file, output_file):
    """Generate Mermaid diagram from architecture"""
    
    # Load Jinja2 template
    template_dir = Path(template_file).parent
    template_name = Path(template_file).name
    
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    
    # Render template
    mermaid_content = template.render(**architecture)
    
    # Write output
    with open(output_file, 'w') as f:
        f.write(mermaid_content)
    
    print(f"✅ Generated: {output_file}")
    return mermaid_content


def main():
    parser = argparse.ArgumentParser(
        description="Generate Mermaid diagrams from architecture.yml"
    )
    
    parser.add_argument(
        "--architecture",
        default="internal_docs/architecture.yml",
        help="Path to architecture.yml"
    )
    
    parser.add_argument(
        "--template",
        default="internal_docs/templates/mermaid.j2",
        help="Path to Jinja2 template"
    )
    
    parser.add_argument(
        "--output",
        default="internal_docs/diagrams/architecture.mmd",
        help="Output path for Mermaid file"
    )
    
    args = parser.parse_args()
    
    # Resolve paths
    project_root = Path(__file__).parent.parent
    arch_file = project_root / args.architecture
    template_file = project_root / args.template
    output_file = project_root / args.output
    
    # Ensure output directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load architecture
    print(f"📖 Loading architecture from {arch_file}")
    architecture = load_architecture(arch_file)
    
    # Generate diagram
    print(f"🎨 Generating Mermaid diagram")
    generate_mermaid(architecture, template_file, output_file)
    
    print(f"\n✅ Diagram generation complete!")
    print(f"\nTo view the diagram:")
    print(f"1. Open {output_file}")
    print(f"2. Copy content to https://mermaid.live")
    print(f"3. Or use in Grafana Dynamic Text Panel")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
