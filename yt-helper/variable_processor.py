import os

def process_variable(
        env_variable_name : str, 
        list_separator : str = ",",
        pair_separator : str = ";",
        pair_eq : str = "=",
        single_value_key : str = "id",
        legacy_item_separator : str = ":", 
        legacy_item_list : list[str] = ["id", "subscription_start"]) -> list[dict[str, str]]:
    result_list : list[dict[str, str]] = list()
    env_value_list : str = os.getenv(env_variable_name, "")
    if env_value_list and len(env_value_list) > 0:
        current_value : str
        for current_value in env_value_list.split(list_separator):
            current_dict : dict[str, str] = process_single_value(
                env_value = current_value,
                pair_separator = pair_separator,
                pair_eq = pair_eq,
                single_value_key = single_value_key,
                legacy_item_separator = legacy_item_separator,
                legacy_item_list = legacy_item_list
            )
            result_list.append(current_dict)
    return result_list

def process_single_value(
        env_value : str,
        pair_separator : str,
        pair_eq : str,
        single_value_key : str,
        legacy_item_separator : str, 
        legacy_item_list : list[str]) -> dict[str, str]:
    result_dict : dict[str, str] = dict()
    if env_value and len(env_value) > 0:
        if not pair_separator in env_value and not pair_eq in env_value:
            if legacy_item_separator in env_value:
                legacy_value_list : list[str] = env_value.split(legacy_item_separator)
                # zip
                v_len : int = len(legacy_value_list)
                k_len : int = len(legacy_item_list)
                for x in range(0, min(v_len, k_len)):
                    k : str = legacy_item_list[x]
                    v : str = legacy_value_list[x]
                    if k and len(k) > 0 and v and len(v) > 0:
                        result_dict[legacy_item_list[x]] = legacy_value_list[x]
            else:
                result_dict[single_value_key] = env_value
        else:
            current_pair : str
            for current_pair in env_value.split(pair_separator):
                if current_pair and len(current_pair) > 0:
                    pair_k : str
                    pair_v : str
                    pair_k, pair_v = current_pair.split(pair_eq)
                    if pair_k in result_dict:
                        raise Exception(f"Duplicate key [{pair_k}]")
                    result_dict[pair_k] = pair_v
    return result_dict