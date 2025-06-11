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
        gasNode2: GasNode {
            @display("p=104,830");
        }
        gasNode22: GasNode {
            @display("p=87,655");
        }
        gasNode21: GasNode {
            @display("p=172,535");
        }
        gasNode6: GasNode {
            @display("p=247,576");
        }
        gasNode5: GasNode {
            @display("p=265,684");
        }
        compressor23: Compressor {
            @display("p=184,680");
        }
        gasNode1: GasNode {
            @display("p=292,770");
        }
        gasNode3: GasNode {
            @display("p=459,849");
        }
        integratedNode20: IntegratedNode {
            @display("p=156,400");
        }
        integratedNode7: IntegratedNode {
            @display("p=381,448");
        }
        integratedNode4: IntegratedNode {
            @display("p=418,702");
        }
        integratedNode10: IntegratedNode {
            @display("p=477,570");
        }
        gasNode12: GasNode {
            @display("p=625,708");
        }
        gasNode11: GasNode {
            @display("p=584,617");
        }
        integratedNode18: IntegratedNode {
            @display("p=327,304");
        }
        gasNode19: GasNode {
            @display("p=236,335");
        }
        integratedNode9: IntegratedNode {
            @display("p=532,375");
        }
        integratedNode8: IntegratedNode {
            @display("p=436,176");
        }
        gasNode13: GasNode {
            @display("p=831,650");
        }
        gasNode14: GasNode {
            @display("p=735,474");
        }
        gasNode15: GasNode {
            @display("p=799,334");
        }
        gasNode16: GasNode {
            @display("p=792,139");
        }
        gasNode17: GasNode {
            @display("p=608,98");
        }
        compressor25: Compressor {
            @display("p=695,247");
        }
        compressor24: Compressor {
            @display("p=685,589");
        }
    connections:

        gasNode1.out++ --> GasPipe {  cij = 1.11405; } --> gasNode2.in++;
        gasNode1.out++ --> GasPipe {  cij = 1.21405; } --> gasNode3.in++;
        gasNode1.out++ --> GasPipe {  cij = 1.31405; } --> integratedNode4.in++;
        gasNode2.out++ --> GasPipe {  cij = 1.49543; } --> gasNode3.in++;
        gasNode2.out++ --> GasPipe {  cij = 1.51405; } --> gasNode22.in++;
        gasNode21.out++ --> GasPipe {  cij = 1.71405; } --> integratedNode20.in++;
        gasNode2.out++ --> GasPipe {  cij = 1.81405; } --> gasNode5.in++;
        gasNode3.out++ --> GasPipe --> integratedNode4.in++;
        integratedNode4.out++ --> GasPipe --> integratedNode10.in++;
        integratedNode4.out++ --> GasPipe --> gasNode11.in++;
        integratedNode4.out++ --> GasPipe --> gasNode12.in++;
        gasNode5.out++ --> GasPipe --> gasNode6.in++;
        gasNode6.out++ --> GasPipe {  cij = 1.81405; qij = 10.322;} --> gasNode21.in++;
        gasNode6.out++ --> GasPipe --> integratedNode10.in++;
        gasNode6.out++ --> GasPipe --> integratedNode7.in++;
        integratedNode7.out++ --> GasPipe --> integratedNode9.in++;
        integratedNode7.out++ --> GasPipe --> integratedNode18.in++;
        integratedNode7.out++ --> GasPipe --> integratedNode20.in++;
        integratedNode8.out++ --> GasPipe --> integratedNode18.in++;
        integratedNode8.out++ --> GasPipe --> integratedNode9.in++;
        integratedNode9.out++ --> GasPipe --> integratedNode10.in++;
        integratedNode10.out++ --> GasPipe --> gasNode11.in++;
        gasNode11.out++ --> GasPipe --> gasNode12.in++;
        gasNode12.out++ --> GasPipe --> gasNode13.in++;
        gasNode13.out++ --> GasPipe --> gasNode14.in++;
        gasNode14.out++ --> GasPipe --> gasNode15.in++;
        gasNode15.out++ --> GasPipe --> gasNode16.in++;
        gasNode14.out++ --> GasPipe --> integratedNode10.in++;
        gasNode15.out++ --> GasPipe --> integratedNode9.in++;
        gasNode16.out++ --> GasPipe --> gasNode17.in++;
        gasNode17.out++ --> GasPipe --> integratedNode8.in++;
        integratedNode18.out++ --> GasPipe --> gasNode19.in++;
        gasNode19.out++ --> GasPipe --> integratedNode20.in++;
        gasNode17.out++ --> GasPipe --> integratedNode9.in++;
        compressor25.out++ --> GasPipe --> gasNode17.in++;
        compressor23.out++ --> GasPipe --> gasNode6.in++;
        compressor24.out++ --> GasPipe --> gasNode14.in++;
        compressor23.out++ --> GasPipe --> gasNode2.in++;
        compressor25.out++ --> GasPipe --> gasNode15.in++;
        compressor24.out++ --> GasPipe --> gasNode12.in++;
        gasNode22.out++ --> GasPipe --> gasNode21.in++;
}
