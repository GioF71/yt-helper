def process_variable(
        env_value_list : str, 
        list_separator : str = ",",
        pair_separator : str = "|",
        pair_eq : str = ":",
        single_value_key : str = "id") -> list[dict[str, str]]:
    result_list : list[dict[str, str]] = list()
    if env_value_list and len(env_value_list) > 0:
        current_value : str
        for current_value in env_value_list.split(list_separator):
            current_dict : dict[str, str] = process_single_value(
                env_value = current_value,
                pair_separator = pair_separator,
                pair_eq = pair_eq,
                single_value_key = single_value_key
            )
            result_list.append(current_dict)
    return result_list

def process_single_value(
        env_value : str,
        pair_separator : str = "|",
        pair_eq : str = ":",
        single_value_key : str = "id") -> dict[str, str]:
    result_dict : dict[str, str] = dict()
    if env_value and len(env_value > 0):
        if not pair_separator in env_value and not pair_eq in env_value:
            result_dict[single_value_key] = env_value
        else:
            current_pair : str
            for current_pair in env_value.split(pair_separator):
                pair_k : str
                pair_v : str
                pair_k, pair_v = current_pair.split(pair_eq)
                if pair_k in result_dict:
                    raise Exception(f"Duplicate key [{pair_k}]")
                result_dict[pair_k] = pair_v
    return result_dict