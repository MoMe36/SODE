import numpy as np 
import json 
import os 
import glob 
import basic_utils
import networkx as nx
import matplotlib.pyplot as plt
import sk_utils

def display_structure(config):
    
    structure_path = config['structure_file_path']

    data = json.load(open(structure_path, 'r'))
    graph = nx.DiGraph()
    node_shapes = {
        'constant': 'o',  # circle
        'target_stock': 's',  # square
        'default': 'd'  # diamond
    }
    node_colors = {
        'constant': 'skyblue',
        'target_stock': 'green',
        'default': 'lightgray'
    }
    for w in data['workflow']:
        label = w['target'].replace('_', " ").capitalize()
        if w['is_constant'][0]:
            graph.add_node(w['code_name'], label=label, shape=node_shapes['constant'], color=node_colors['constant'])
        elif w['code_name'] in data['target_stocks']:
            graph.add_node(w['code_name'], label=label, shape=node_shapes['target_stock'], color=node_colors['target_stock'])
        else:
            graph.add_node(w['code_name'], label=label, shape=node_shapes['default'], color=node_colors['default'])

    edges = []
    for w in data['workflow']:
        if w['variables'] is None: 
            continue
        for v in w['variables']:  
            edges.append([v, w['code_name']])
    graph.add_edges_from(edges)

    pos = nx.spring_layout(graph)
    node_sizes = [1500 for _ in graph.nodes()]
    node_edge_colors = [node[1]['color'] for node in graph.nodes(data=True)]
    node_face_colors = [node[1]['color'] for node in graph.nodes(data=True)]

    nx.draw_networkx_nodes(graph, pos, node_size=node_sizes, node_shape='o', node_color=node_face_colors, edgecolors=node_edge_colors)
    nx.draw_networkx_labels(graph, pos, font_size=10)
    nx.draw_networkx_edges(graph, pos, width=0.5, edge_color='gray')
    plt.axis('off')
    plt.show()

def make_graph(config): 
    
    structure_path = config['structure_file_path']
    function_config_path = config['function_config_file']
    output_path = config['interactive_graph_folder']
        

    
    data = json.load(open(structure_path, 'r'))

    sk_utils.init_obsidian_vault(output_path, exists_ok=False)
    for w in data['workflow']: 
        if w["is_constant"][0]: 
            tag = ['constant']
        elif w['code_name'] in data['target_stocks']:
            tag = ['target_stock']
        else:
            tag = ['default']

        node_path = sk_utils.add_node_to_graph(output_path, contents = [["Target",  w["target"].replace('_', ' ').capitalize()], 
                                                                    ["Operation", w["operation"]], 
                                                                    ["Constant", "\n".join([str(w["is_constant"][1]), w["is_constant"][2] if isinstance(w['is_constant'][2], str) else "unit?"]) if w['is_constant'][0] else ""],
                                                                    ["Links", "\n".join(['[[{}]]'.format(l.strip().replace('_', ' ').capitalize()) for l in w['variables']]) if w['variables'] is not None else ""]],
                                           tags = tag, name_override=w['code_name'].replace('_', ' ').capitalize())
    # ADDING THE TIME NODE
    time_node = sk_utils.add_node_to_graph(output_path, 
                           contents = [["Params", "\n".join("{}: {}".format(k,v) for k,v in data['time_params'].items())]], 
                           tags = ["time"], name_override= "Time Params")
    
    # INITIAL CONDITIONS NODE 
    stocks_ci = [[s[0], s[1] if s[1] is not None else s[2], "explicit" if s[1] is not None else "implicit"] for s in data['stocks_ci']]
    initial_conditions = sk_utils.add_node_to_graph(output_path,
                                                contents = [["Conditions per stock", "\n".join("{} | {} | {}".format(k,v,q) for k,v,q in stocks_ci)]],
                                                tags = ["initial_conditions"], name_override= "Initial Conditions")
    
    
    # ADDING THE FUNCTION CONFIG_NODES
    if not os.path.exists(function_config_path):
        function_config = {}
        basic_utils.crline('Missing function file')
        return 
    
    function_config = json.load(open(function_config_path, 'r'))
    fc_node = sk_utils.add_node_to_graph(output_path,
                            contents = "Function config central node", 
                            tags = ["function_config"], name_override= "Function Config")
    for k, v in function_config.items():   
        n = sk_utils.add_node_to_graph(output_path, 
                               parent_path= fc_node, 
                               contents = [["Function ID", k], ["Rationale", v['rationale']], ["Params",  sk_utils.to_markdown_table(v['values'],  'x,y'.split(','))]],
                               tags = ["function_config"], name_override= k)


def process_variable_from_graph(raw_names):
    return [v.strip().replace('[[', '').replace(']]', '').replace(' ', '_').lower() for v in raw_names.strip().split('\n')]

def collect_sorted_nodes(graph_folder = os.path.join(os.path.dirname(__file__), "interactive_graph")):
    target_stock_nodes = sk_utils.collect_files_in_folder(graph_folder, target_tags = ['target_stock'])
    constant_nodes = sk_utils.collect_files_in_folder(graph_folder, target_tags = ['constant'])
    default_nodes = sk_utils.collect_files_in_folder(graph_folder, target_tags = ['default'])


    # RECURSIVE FUNCTION TO SORT NODES 

    def recursive_sort(node, sorted_nodes, unsorted_nodes):
        # Get the dependencies of the current node
        dependencies = process_variable_from_graph(sk_utils.get_node_section(node, "Links"))
        
        # Recursively sort the dependencies
        for dependency in dependencies:
            if dependency in unsorted_nodes:
                # Move the dependency to the sorted_nodes list
                sorted_nodes.append(unsorted_nodes.pop(unsorted_nodes.index(dependency)))
                recursive_sort(dependency, sorted_nodes, unsorted_nodes)
        
        # If all dependencies are sorted, add the current node to the sorted list
        if all(dependency not in unsorted_nodes for dependency in dependencies):
            sorted_nodes.append(node)
    
    # Initialize the sorted list with the target_stock_nodes
    final_list = target_stock_nodes[:]
    
    # Initialize the unsorted list with the default_nodes and constant_nodes
    unsorted_nodes = default_nodes + constant_nodes
    
    # Recursively sort the nodes
    for node in target_stock_nodes:
        recursive_sort(node, final_list, unsorted_nodes)
    
    # Add any remaining nodes to the final list
    final_list.extend(unsorted_nodes)

    return final_list # target_stock_nodes + sorted default_nodes + constant_nodes

def graph_to_structure(config): 
    
    graph_folder = config['interactive_graph_folder']
    
    nodes = collect_sorted_nodes(graph_folder)
    target_stocks = [sk_utils.get_node_section(f, "Target").strip().lower().replace(' ', '_') for f in sk_utils.collect_files_in_folder(graph_folder, target_tags = ['target_stock'])]
    target_stocks = [sk_utils.get_node_section(f, "Target").strip().lower().replace(' ', '_') for f in sk_utils.collect_files_in_folder(graph_folder, target_tags = ['target_stock'])]
    workflow = []
    # input(target_stocks)
    
    constants = []
    for node in nodes:
        target = sk_utils.get_node_section(node, "Target").strip()

        if target.strip().lower().replace(' ', '_') in [w['target'] for w in workflow]:
            print('Skipping ' + target)
            continue
        
        constant = sk_utils.get_node_section(node, "Constant")
        if constant.strip() == "": 
            constant = [False, None, ""] # not a constant, no value, no unit
            operation = sk_utils.get_node_section(node, "Operation").strip()    

        else:
            unit = constant.strip().split('\n')[-1]
            constant_value = constant.strip().split('\n')[0]
            # print(unit, constant_value, node)
            constant = [True, float(constant_value.strip()) if '.' in constant_value.strip() else int(constant_value.strip()), unit]
            constants.append([target.strip().lower().replace(' ', '_')] + constant[1:])
            operation = None
            


        variables = process_variable_from_graph(sk_utils.get_node_section(node, "Links"))
        workflow.append({"target": target.strip().lower().replace(' ', '_'), 
                         "code_name": target.strip().lower().replace(' ', '_'), 
                         "operation": operation,
                         "variables": variables,
                         "is_constant": constant,  })
        
    # CONSTRUCTING THE TIME NODE
    time_node = sk_utils.get_node_section(sk_utils.collect_files_in_folder(graph_folder, target_tags = ['time'])[0], "Params").strip()
    time_node = sk_utils.get_node_section(sk_utils.collect_files_in_folder(graph_folder, target_tags = ['time'])[0], "Params").strip()
    time_params = {}
    for line in time_node.split('\n'):
        k = line.split(':')[0].strip()
        v = line.split(':')[1].strip()
        if v.isnumeric():
            time_params[k] = float(v) if '.' in v else int(v)
            
        else:
            time_params[k] = v
            
    # COLLECTING THE INITIAL CONDITIONS
    initial_conditions = sk_utils.get_node_section(sk_utils.collect_files_in_folder(graph_folder, target_tags = ['initial_conditions'])[0], "Conditions per stock").strip()
    initial_conditions = sk_utils.get_node_section(sk_utils.collect_files_in_folder(graph_folder, target_tags = ['initial_conditions'])[0], "Conditions per stock").strip()
    stocks_ci = []
    for ci in initial_conditions.split('\n'):
        target, value, explicit = ci.split('|')
        stocks_ci.append([target.strip().lower().replace(' ', '_'), 
                          float(value.strip()) if explicit.strip() == "explicit" else None, 
                          float(value.strip()) if explicit.strip() == "implicit" else None])
    

    updated_sys_structure = {"target_stocks": target_stocks,
                             "time_params": time_params,
                                "constants": constants,
                                "stocks_ci": stocks_ci,
                                "workflow": workflow}
    
    
    # CONSTRUCTING THE FUNCTION CONFIG NODES
    function_config_nodes = sk_utils.collect_files_in_folder(graph_folder, target_tags = ['function_config'])
    function_config = {}
    for fc in function_config_nodes:
        if sk_utils.check_section(fc, "Function ID"):
            func_id = sk_utils.get_node_section(fc, "Function ID").strip()
            rationale = sk_utils.get_node_section(fc, "Rationale").strip()
            values = sk_utils.from_markdown_table_to_df(sk_utils.get_node_section(fc, "Params").strip())
            values = sk_utils.from_markdown_table_to_df(sk_utils.get_node_section(fc, "Params").strip())
            # process the values to be a list of lists
            function_config[func_id] = {"rationale": rationale, "values": values.values.tolist()}


    return updated_sys_structure, function_config
       
def simple_plot(sim_result, t): 
    nb_sims = sim_result.shape[1]   
    # clever square plot 
    nb_rows = int(np.ceil(np.sqrt(nb_sims)))
    nb_cols = int(np.ceil(nb_sims / nb_rows))
    if nb_sims == 1: 
        fig, axes = plt.subplots(1, 1, figsize=(15, 15))
        axes.plot(t, sim_result[:,0], '-o', markersize=3)
        axes.set_xlabel('Time')
        axes.set_ylabel('Deer Population')
        axes.set_title('Deer Population Growth')
    else: 
        f, axes = plt.subplots(nb_rows, nb_cols, figsize=(15, 15))
        for i in range(nb_sims):
            axes[i].plot(t, sim_result[:,i], '-o', markersize=3)
            axes[i].set_xlabel('Time')
            axes[i].set_ylabel('Deer Population')
            axes[i].set_title('Deer Population Growth')
    plt.savefig(os.path.join(os.path.dirname(__file__), 'latest_simulations.png'))
    plt.show()

def process_table_input(table_input):
    table = []
    valid = False 
    try: 
        for pair in table_input.split('|'):
            x, y = pair.split(',')
            table.append([float(x.strip()), float(y.strip())])
        valid = True
    except: 
        pass
    return table, valid

def create_function_params(func_id):
    if func_id.startswith('piecewise_linear'):
        basic_utils.crline('Enter a sequence of x,y pairs for the piecewise linear function using the following format: x1,y1 | x2,y2 | ,...')
        valid = False
        while not valid: 
            table, valid = process_table_input(input())
           

    elif func_id.startswith('step_after_time'):
        basic_utils.crline('Enter a sequence of step_value, after_time pairs for the step_after_time function using the following format: step_value1, after_time1 | step_value2, after_time2 | ,...')
        valid = False
        while not valid: 
            table, valid = process_table_input(input())
    return table

def collect_function_params(func_id):
    f_path = os.path.join(os.path.dirname(__file__), 'function_config.json')    
    if not os.path.exists(f_path):
        func_data  = {}
        with open(f_path, 'w') as f:
            json.dump(func_data, f, indent=4)
    else: 
        func_data = json.load(open(f_path, 'r'))
    if func_id in func_data.keys():
        params = func_data[func_id]['values']
        if params is None: 
            params = create_function_params(func_id)
    else: 
        params = create_function_params(func_id)
    

    return params

def lookup(x,table):

    # interpolate between two points
    if x >= np.max(table[:,0]):
        return table[-1,1]
    if x <= np.min(table[:,0]):
        return table[0,1]
    
    target_element = np.min(np.where(table[:,0] > x))
    x1, y1 = table[target_element-1]
    x2, y2 = table[target_element]
    return y1 + (y2-y1)/(x2-x1)*(x-x1)

def piecewise_linear(x, func_id = None):
    
    table = np.array(collect_function_params(func_id))
    # table is a 2D numpy array with the first column being the x values and the second column being the y values

    # interpolate between two points
    if x >= np.max(table[:,0]):
        return table[-1,1]
    if x <= np.min(table[:,0]):
        return table[0,1]
    
    target_element = np.min(np.where(table[:,0] > x))
    x1, y1 = table[target_element-1]
    x2, y2 = table[target_element]
    return y1 + (y2-y1)/(x2-x1)*(x-x1)

def check_step_after_time(t, table):

    # table is a 2D numpy array with the first column being the step values and the second column being the after_time values

    
    pos = np.where(table[:,1] > t)[0]
    if len(pos) == 0:
        return table[-1,0]
    target_element = np.min(pos)
    if t >= table[target_element, 1]:
        result = table[target_element, 0]
    else:
        result = table[target_element-1, 0]
    # result = table[target_element, 0]
    # print('t', t, 'target_element', target_element, 'result', result)
    return result

def step_after_time(t, func_id = None): 
    loaded_table = collect_function_params(func_id) 
    result = check_step_after_time(t, np.array(loaded_table)) 
    # input(result)
    return result

def conditional(condition, true_val, false_val):
    if condition:
        return true_val
    else:
        return false_val


to_smooth = []  
def smooth(x, time_period): 
    to_smooth.append(x)
    return np.mean(to_smooth[-time_period:])