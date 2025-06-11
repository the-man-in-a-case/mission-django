## topology.ini.j2

```
[General]
network = {{ general.network }}

# Gas Node 参数设置
{% for node in nodes.gas_nodes %}
{%- if node.load_demand is not none %}
topology.gasNode{{ node.id }}.LoadDemand = {{ node.load_demand }}
{%- endif %}
{%- if node.total_demand is not none %}
topology.gasNode{{ node.id }}.TotalDemand = {{ node.total_demand }}
{%- endif %}
{%- if node.supply is not none %}
topology.gasNode{{ node.id }}.supply = {{ node.supply }}
{%- endif %}
{%- if node.generator_consumption is not none %}
topology.gasNode{{ node.id }}.GeneratorConsumption = {{ node.generator_consumption }}
{%- endif %}
{%- if node.csv is not none %}
topology.gasNode{{ node.id }}.csv = {{ node.csv|lower }}
{%- endif %}
{%- if node.generator_consumption_csv is not none %}
topology.gasNode{{ node.id }}.GeneratorConsumptionCsv = "{{ node.generator_consumption_csv }}"
{%- endif %}
{%- if node.pressure is not none %}
topology.gasNode{{ node.id }}.pressure = {{ node.pressure }}
{%- endif %}

{% endfor %}

# Integrated Node 参数设置
{% for node in nodes.integrated_nodes %}
{%- if node.load_demand is not none %}
topology.integratedNode{{ node.id }}.LoadDemand = {{ node.load_demand }}
{%- endif %}
{%- if node.total_demand is not none %}
topology.integratedNode{{ node.id }}.TotalDemand = {{ node.total_demand }}
{%- endif %}
{%- if node.supply is not none %}
topology.integratedNode{{ node.id }}.supply = {{ node.supply }}
{%- endif %}
{%- if node.generator_consumption is not none %}
topology.integratedNode{{ node.id }}.GeneratorConsumption = {{ node.generator_consumption }}
{%- endif %}
{%- if node.csv is not none %}
topology.integratedNode{{ node.id }}.csv = {{ node.csv|lower }}
{%- endif %}
{%- if node.generator_consumption_csv is not none %}
topology.integratedNode{{ node.id }}.GeneratorConsumptionCsv = "{{ node.generator_consumption_csv }}"
{%- endif %}
{%- if node.pressure is not none %}
topology.integratedNode{{ node.id }}.pressure = {{ node.pressure }}
{%- endif %}

{% endfor %}

# Compressor 参数设置
{% for compressor in nodes.compressor_nodes %}
topology.compressor{{ compressor.id }}.nst = {{ compressor.nst }}
topology.compressor{{ compressor.id }}.np = {{ compressor.np }}
topology.compressor{{ compressor.id }}.T_in = {{ compressor.T_in }}
topology.compressor{{ compressor.id }}.Z_av = {{ compressor.Z_av }}
topology.compressor{{ compressor.id }}.eta = {{ compressor.eta }}
topology.compressor{{ compressor.id }}.pressRatio = {{ compressor.press_ratio }}
topology.compressor{{ compressor.id }}.readInterval = {{ compressor.read_interval }}
topology.compressor{{ compressor.id }}.hpCsvFileName = "{{ compressor.hp_csv_filename }}"

{% endfor %}

# Gas Pipe 参数设置
{% for pipe in edges.gas_pipes %}
topology.{{ pipe.from }}_to_{{ pipe.to }}.diameter = {{ pipe.diameter }}
topology.{{ pipe.from }}_to_{{ pipe.to }}.length = {{ pipe.length }}
topology.{{ pipe.from }}_to_{{ pipe.to }}.flow = {{ pipe.flow }}
topology.{{ pipe.from }}_to_{{ pipe.to }}.cij = {{ pipe.cij }}
topology.{{ pipe.from }}_to_{{ pipe.to }}.type = "{{ pipe.type }}"
topology.{{ pipe.from }}_to_{{ pipe.to }}.qij = "{{ pipe.qij }}"

{% endfor %}
```

## topology.ned.j2

```
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Lesser General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
// 
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Lesser General Public License for more details.
// 
// You should have received a copy of the GNU Lesser General Public License
// along with this program.  If not, see http://www.gnu.org/licenses/.
// 

package o_g_topology_test2.simulations;
import o_g_topology_test2.Compressor;
import o_g_topology_test2.DataProcessor;
import o_g_topology_test2.GasNode;
import o_g_topology_test2.GasPipe;
import o_g_topology_test2.IntegratedNode;


network topology
{
    parameters:

        @display("bgb=1268,1055");

    submodules:
{% for node in nodes.gas_nodes %}
        gasNode{{ node.id }}: GasNode {
            @display("p={{ node_positions['gasNode' + node.id|string].x }},{{ node_positions['gasNode' + node.id|string].y }}");
        }
{% endfor %}
{% for node in nodes.integrated_nodes %}
        integratedNode{{ node.id }}: IntegratedNode {
            @display("p={{ node_positions['integratedNode' + node.id|string].x }},{{ node_positions['integratedNode' + node.id|string].y }}");
        }
{% endfor %}
{% for compressor in nodes.compressor_nodes %}
        compressor{{ compressor.id }}: Compressor {
            @display("p={{ compressor.position.x }},{{ compressor.position.y }}");
        }
{% endfor %}
    connections:

{% for pipe in edges.gas_pipes %}
        {{ pipe.from }}.out++ --> GasPipe { diameter = {{ pipe.diameter }}; length = {{ pipe.length }}; flow = {{ pipe.flow }}; cij = {{ pipe.cij }}; type = "{{ pipe.type }}"; qij = "{{ pipe.qij }}"; } --> {{ pipe.to }}.in++;
{% endfor %}
}
```

