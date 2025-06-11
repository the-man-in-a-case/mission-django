from influxdb_client import InfluxDBClient

# 参数设置（保持原有配置）
url = "http://192.168.119.200:8087"
token = "oYIDVNEHbwIZZvrNfFpQou42VV9QIvSJ9uzbkZE-zZNFkFkv3TN7l23GobiNHfNSfMNYj9aFIhtcpq6Tn9UqKA=="
org = "my-org"
bucket = "003"

def query_influxdb_data(target_id: str = 'abc') -> list:
    """
    查询InfluxDB数据并转换格式
    :param target_id: 要查询的id（默认abc）
    :return: 包含日志字符串和原始数据的列表
    """
    try:
        # 初始化客户端
        client = InfluxDBClient(url=url, token=token, org=org)
        query_api = client.query_api()

        # 构造带参数的查询语句
        # query = f'''
        # from(bucket: "{bucket}")
        #   |> range(start: -72h)
        #   |> filter(fn: (r) => r._measurement == "GasNode")
        #   |> filter(fn: (r) => r.nodeName == "gasNode14")
        #   |> filter(fn: (r) => r.id == "{target_id}")
        # '''

        query = f'''
        from(bucket: "{bucket}")
          |> range(start: -30d)
          |> filter(fn: (r) => r.id == "{target_id}")
        '''

        # 执行查询并处理结果
        tables = query_api.query(query)
        # 新增：按时间、测量类型、id、节点分组（键为元组，值为字段字典）
        grouped_data = {}
        for table in tables:
            for record in table.records:
                raw_data = dict(record.values)
                # 提取关键分组字段（需确保这些字段存在，否则跳过）
                try:
                    time = raw_data['_time']
                    measurement = raw_data['_measurement']
                    node_id = raw_data['id']
                    node_name = raw_data['nodeName']
                    field = raw_data['_field']
                    value = raw_data['_value']
                except KeyError as e:
                    continue  # 跳过缺失关键字段的记录
                
                # 构造分组键（时间、测量类型、id、节点）
                group_key = (time, measurement, node_id, node_name)
                # 初始化或更新分组字段字典
                if group_key not in grouped_data:
                    grouped_data[group_key] = {}
                grouped_data[group_key][field] = value  # 按字段存储值

        # 生成合并后的日志消息
        result = []
        for (time, measurement, node_id, node_name), fields in grouped_data.items():
            # 将字段字典转换为"字段1=值1, 字段2=值2"格式
            fields_str = ", ".join([f"{k}={v}" for k, v in fields.items()])
            log_msg = (
                f"时间{time}，测量类型{measurement}，id={node_id}，节点{node_name}，"
                f"字段值：{fields_str}"
            )
            result.append(log_msg)
        return result
    except Exception as e:
        return [{"error": f"查询失败: {str(e)}"}]