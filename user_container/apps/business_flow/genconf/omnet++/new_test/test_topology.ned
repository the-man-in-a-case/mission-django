
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
        
        compressor23: Compressor {
            @display("p=184,680");
        }
        
        compressor24: Compressor {
            @display("p=685,589");
        }
        
        compressor25: Compressor {
            @display("p=695,247");
        }
        
        gasNode1: GasNode {
            @display("p=292,770");
        }
        
        gasNode11: GasNode {
            @display("p=584,617");
        }
        
        gasNode12: GasNode {
            @display("p=625,708");
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
        
        gasNode19: GasNode {
            @display("p=236,335");
        }
        
        gasNode2: GasNode {
            @display("p=104,830");
        }
        
        gasNode21: GasNode {
            @display("p=172,535");
        }
        
        gasNode22: GasNode {
            @display("p=87,655");
        }
        
        gasNode3: GasNode {
            @display("p=459,849");
        }
        
        gasNode5: GasNode {
            @display("p=265,684");
        }
        
        gasNode6: GasNode {
            @display("p=247,576");
        }
        
        integratedNode10: IntegratedNode {
            @display("p=477,570");
        }
        
        integratedNode18: IntegratedNode {
            @display("p=327,304");
        }
        
        integratedNode20: IntegratedNode {
            @display("p=156,400");
        }
        
        integratedNode4: IntegratedNode {
            @display("p=418,702");
        }
        
        integratedNode7: IntegratedNode {
            @display("p=381,448");
        }
        
        integratedNode8: IntegratedNode {
            @display("p=436,176");
        }
        
        integratedNode9: IntegratedNode {
            @display("p=532,375");
        }
        

    connections:
        
        gasNode1.out++ --> GasPipe { 
            
            cij = 1.11405; ;
            
            diameter = 5000; ;
            
            length = 200; ;
            
            flow = 100; ;
            
            type = p; ;
            
            qij = 26.7606;
            
        } --> gasNode2.in++;
        
        gasNode1.out++ --> GasPipe { 
            
            cij = 1.21405; ;
            
            diameter = 5000; ;
            
            length = 200; ;
            
            flow = 100; ;
            
            type = p; ;
            
            qij = 26.7606;
            
        } --> gasNode3.in++;
        
        gasNode1.out++ --> GasPipe { 
            
            cij = 1.31405; ;
            
            diameter = 5000; ;
            
            length = 200; ;
            
            flow = 100; ;
            
            type = p; ;
            
            qij = 26.7606;
            
        } --> integratedNode4.in++;
        
        gasNode2.out++ --> GasPipe { 
            
            cij = 1.49543; ;
            
            diameter = 5000; ;
            
            length = 200; ;
            
            flow = 100; ;
            
            type = p; ;
            
            qij = 26.7606;
            
        } --> gasNode3.in++;
        
        gasNode2.out++ --> GasPipe { 
            
            cij = 1.51405; ;
            
            diameter = 5000; ;
            
            length = 200; ;
            
            flow = 100; ;
            
            type = p; ;
            
            qij = 26.7606;
            
        } --> gasNode22.in++;
        
        gasNode21.out++ --> GasPipe { 
            
            cij = 1.71405; ;
            
            diameter = 5000; ;
            
            length = 200; ;
            
            flow = 100; ;
            
            type = p; ;
            
            qij = 26.7606;
            
        } --> integratedNode20.in++;
        
        gasNode2.out++ --> GasPipe { 
            
            cij = 1.81405; ;
            
            diameter = 5000; ;
            
            length = 200; ;
            
            flow = 100; ;
            
            type = p; ;
            
            qij = 26.7606;
            
        } --> gasNode5.in++;
        
        gasNode6.out++ --> GasPipe { 
            
            cij = 1.81405; ;
            
            qij = 26.7606; ;
            
            diameter = 5000; ;
            
            length = 200; ;
            
            flow = 100; ;
            
            type = p;
            
        } --> gasNode21.in++;
        
}