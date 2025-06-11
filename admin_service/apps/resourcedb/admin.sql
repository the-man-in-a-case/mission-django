create database Middle_Table_v4_admin;
use Middle_Table_v4_admin;

ALTER DATABASE Middle_Table_v4_admin CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci;

# 创建 Map 表
create table Map(
                    MapID INT AUTO_INCREMENT PRIMARY KEY comment 'map索引ID'
) comment '地图表，一个map由多个Layer组成，map和Layer联合构成主键';

# 创建 Layer 表
create table Layer(
                      LayerID INT AUTO_INCREMENT PRIMARY KEY comment '图层索引ID',
                      type ENUM('FinancialLayer','TransportationLayer','WaterLayer','OilGasLayer','TelecommunicationLayer','PowerLayer','EconomicGraphicLayer','demographicLayer','GeographicLayer','MutualLayer')
) comment 'Layer表，标识Layer的唯一id，并说明Layer的类型';

# 创建Map和Layer映射
create table Map_Layer(
                          Map_Layer INT AUTO_INCREMENT PRIMARY KEY comment 'Map_Layer ID',
                          MapID INT comment 'map索引ID',
                          LayerID INT comment 'Layer索引ID',
                          UNIQUE (MapID, LayerID),
                          FOREIGN KEY (MapID) references Map(MapID)
                              ON DELETE RESTRICT
                              ON UPDATE CASCADE,
                          FOREIGN KEY (LayerID) references Layer(LayerID)
                              ON DELETE RESTRICT
                              ON UPDATE CASCADE
);

# 创建 BaseNode 表
create table BaseNode(
                         ID INT AUTO_INCREMENT PRIMARY KEY,
                         BaseNodeName VARCHAR(50),
                         BaseNodeDesc VARCHAR(255),
                         GeoLocation varchar(255),
                         Nation VARCHAR(50),
                         Province VARCHAR(50),
                         City varchar(50),
                         District VARCHAR(50),
                         Street VARCHAR(50),
                         No VARCHAR(50),
                         Location VARCHAR(50),
                         Attribute json,
                         CISType ENUM('001', '002', '003', '004', '005', '006'),
                         SubType ENUM('1-1Terminal', '1-2Bearer', '2-1Gen', '2-2Trans', '2-3Dis','2-4Load','3-1GasExploit','3-2GasTrans','3-3GasLoad','4-1Draw','4-2Gen','4-3Trans','4-4Dis','4-5SecondSup','4-6Load'),
                         ModelName VARCHAR(50) COMMENT '仿真模型的名称',
                         Coverage VARCHAR(255) COMMENT '覆盖区域，与具体的区域表对应',
                         Owner VARCHAR(50) COMMENT '所有者'
) comment '节点基类表';




# 创建 BaseEdge 表
create table BaseEdge(
                         ID INT AUTO_INCREMENT PRIMARY KEY comment '线路编号',
                         BaseEdgeName VARCHAR(50),
                         BaseEdgeDesc VARCHAR(255),
                         GeoLocation varchar(255),
                         Nation VARCHAR(50),
                         Province VARCHAR(50),
                         City varchar(50),
                         District VARCHAR(50),
                         Street VARCHAR(50),
                         No VARCHAR(50),
                         Location VARCHAR(50)
) comment '边基类表';


# 创建 Node 表
create table Node(
                     NodeID INT AUTO_INCREMENT PRIMARY KEY comment 'NodeID ID',
                     LayerID INT COMMENT 'Layer索引ID',
                     BaseNodeID INT comment '节点的ID',
                     UNIQUE (LayerID, BaseNodeID),
                     foreign key (LayerID) references Layer(LayerID)
                         ON DELETE RESTRICT
                         ON UPDATE CASCADE,
                     foreign key (BaseNodeID) references BaseNode(ID)
                         ON DELETE RESTRICT
                         ON UPDATE CASCADE
) comment 'Node表，标识每一个Layer中含有的node，LayerID和NodeID共同构成主键';

# 创建 MechanismRelationship 表
create table MechanismRelationShip(
                                      ID INT AUTO_INCREMENT PRIMARY KEY comment '边业务属性ID',
                                      Business text comment '表述业务关系',
                                      Function text comment '表述功能',
                                      Composition text comment '表述组成',
                                      Behavior text comment '表述行为关系',
                                      State text comment '表述状态关系'
) comment 'MechanismRelationship表，标识一个边应当具有的业务属性';

# 创建 Edge 表
create table Edge(
                     EdgeID INT AUTO_INCREMENT PRIMARY KEY COMMENT  'Edge索引ID',
                     SourceNodeID INT comment '源节点的ID',
                     MechanismRelationshipID INT comment '边业务属性：业务、功能、组成、行为、状态',
                     DestinationNodeId INT comment '目的节点的ID',

                     foreign key (EdgeID) references BaseEdge(ID)
                         ON DELETE RESTRICT
                         ON UPDATE CASCADE,
                     foreign key (SourceNodeID) references BaseNode(ID)
                         ON DELETE RESTRICT
                         ON UPDATE CASCADE,
                     foreign key (DestinationNodeId) references BaseNode(ID)
                         ON DELETE RESTRICT
                         ON UPDATE CASCADE,
                     foreign key (MechanismRelationshipID) references MechanismRelationShip(ID)
                         ON DELETE RESTRICT
                         ON UPDATE CASCADE
) comment 'Node表，标识每一个Layer中含有的node，LayerID和NodeID共同构成主键';


# 创建 IntraEdge 表
create table IntraEdge(
                          IntraEdgeID INT AUTO_INCREMENT PRIMARY KEY COMMENT  'IntraEdge索引ID',
                          LayerID INT COMMENT 'Layer索引ID',
                          EdgeID INT comment '节点的ID',
                          Unique (LayerID, EdgeID),
                          foreign key (LayerID) references Layer(LayerID)
                              ON DELETE RESTRICT
                              ON UPDATE CASCADE,
                          foreign key (EdgeID) references Edge(EdgeID)
                              ON DELETE RESTRICT
                              ON UPDATE CASCADE
) comment 'IntraEdge表，标识每一个Layer中含有的IntraEdge，LayerID和NodeID共同构成主键';
