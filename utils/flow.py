def exist_node_in(flow_data: dict, node_id: str) -> bool:
    for node in flow_data["nodes"]:
        if node["id"] == node_id:
            return True
    return False


def exist_edge_in(flow_data: dict, edge_id: str) -> bool:
    for edge in flow_data["edges"]:
        if edge["id"] == edge_id:
            return True
    return False


def update_dict_in_list(
    data_list: list[dict], target_id: str, new_data: dict, key: str = None
) -> list[dict]:
    for index, item in enumerate(data_list):
        if "id" in item and item["id"] == target_id:
            if key is None:
                data_list[index] = new_data
            else:
                data_list[index][key] = new_data
            break
    return data_list
