
import sode_utils
import ast
import json
import sode_code_utils
import sk_utils
import os
import basic_utils
import inspect
from argparse import ArgumentParser
import glob
import subprocess
import shutil

def generate_simulation_adjustment_options(system_dynamics = None, constants = None, simulation_time_params = None, function_params = None, user_observation = None): 
    
    icl_examples = basic_utils.load_icl(inspect.currentframe())
    
    
    messages = [
            {"role": "system", "content": """
    You are a simulation parameter adjustment expert assisting the user in aligning simulation parameters with their request. Concretely, you are expected to provide three distinct adjustment options that each make a single change to the parameters to meet the user's requirements.
    For each option, first write the rationale / concise description and then a structured representation of it (that include the update type (constant, time, function), the target_variable_name, and the updated value or parameters. 
    
    If the proposed option involves: 
        * function modification, the updated_value_or_params must be a list of [[x0, y0], [x1, y1], ...] where each pair represents a point in the function.
        * time horizon modification, the updated_value_or_params must be a list with [unit (str), start_time_value, stop_time_value, delta_value]. 
        * constant modification, the updated_value_or_params must be the new value of the constant.
    Answer in a JSON format as follows:
    ```json
    {{
    
        "option_a" : ["A concise description of approach A that aligns the parameters with the user request by making a single change.", update_type, target_variable, updated_value_or_params], // update_type is either 'constant' 'time', or 'function' and updated_value_or_params is the new value for a constant or the new parameters for a function
        "option_b" : ["A concise description of approach B that aligns the parameters with the user request by making a single change.", update_type, target_variable, updated_value_or_params], // update_type is either 'constant' 'time', or 'function' and updated_value_or_params is the new value for a constant or the new parameters for a function
        "option_c" : ["A concise description of approach C that aligns the parameters with the user request by making a single change.", update_type, target_variable, updated_value_or_params] // update_type is either 'constant' 'time', or 'function' and updated_value_or_params is the new value for a constant or the new parameters for a function
    
    }} 
    ```
    """}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n System Dynamics\n{}\n\n Constants\n{}\n\n Simulation Time Params\n{}\n\n Function Params\n{}\n\n User Observation\n{}\n\nGenerate three distinct adjustment options, each containing a single change to the simulation parameters, to align with the user's request (every provided variable can be modified (aka: changing constant values, functions parameters or even time horizon)). Select wisely. \n\n".format(icl_examples, system_dynamics, constants, simulation_time_params, function_params, user_observation)}
    ]
    
    
    parseable = False
    while not parseable: 
        initial_answer, parseable, results = basic_utils.safe_gemini_ask(messages, model = 'pro') 
        
    # basic_utils.crprint(json.dumps(results, indent = 4))
    
    return results["option_a"], results["option_b"], results["option_c"]


def determine_initial_conditions(system_dynamics_description = None, identified_stocks = None): 
    
    icl_examples = basic_utils.load_icl(inspect.currentframe())
    
    
    messages = [
            {"role": "system", "content": """
    You are a System Dynamics expert assisting the user in determining initial conditions for identified stocks. In particular, you will analyze the characteristics of the stocks and provide explicit initial conditions or suggest suitable values when not explicitly defined. Concretely, you are expected to take a list of identified stocks as input and return a list of initial conditions for these stocks.
    Answer in a JSON format as follows:
    ```json
    {{
        "rationale" : "A concise extract from the text (if available) or your concise rationale for the suggested initial conditions",
        "initial_conditions" : [
            [
                "The name of the stock 0",
                "The explicit initial value of the stock, if available", // if not available, write null for parsing purposes 
                "The suggested initial value of the stock when no explicit value is given"
            ],
            [
                "The name of the stock 1",
                "The explicit initial value of the stock, if available", // if not available, write null for parsing purposes
                "The suggested initial value of the stock when no explicit value is given"
            ],
            // add more items as needed...
        ]
    
    }} 
    ```
    """}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n System Dynamics Description\n{}\n\n Identified Stocks\n{}\n\nAnalyze the system dynamics description and identified stocks to determine explicit initial conditions or suggest suitable values for each stock.\n\n".format(icl_examples, system_dynamics_description, identified_stocks)}
    ]
    
    parseable = False
    while not parseable: 
        initial_answer, parseable, results = basic_utils.safe_gemini_ask(messages, model = 'pro') 
        
    # basic_utils.crprint(json.dumps(results, indent = 4))
    
    return results["initial_conditions"]


def update_system_dynamics_equation(rationale = None, target_variable = None, current_equation = None, currently_involved_vars = None): 
    
    icl_examples= basic_utils.load_icl(inspect.currentframe())
    
    
    messages = [
            {"role": "system", "content": """
    You are a skilled mathematician assisting the user in incorporating new influences into mathematical equations representing system dynamics. Concretely, you are expected to enhance an equation by adding a new term that reflects the influence of a specific variable, based on a provided description of this influence.
    Answer in a JSON format as follows:
    ```json
    {{
    
        "updated_equation" : "write the updated mathematical operation (right-side only) using variable names whenever adequate", // beyond obvious (+, - , / , * ), available functions are [piecewise_linear(the_driving_variable), conditional(the_driving_variable), step_after_time(the_driving_variable)] where the_driving_variable represents the quantity to which the function will be applied, if constant, simply write null
        "involved_variables" : ["var0", "var1", ...], // list of variables directly influencing the target variable
    
    }} 
    ```
    """}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n Rationale\n{}\n\n Target Variable\n{}\n\n Current operation\n{}\n\nCurrently involved variables: \n{}\n\nGiven a rationale, target variable, and its current equation representation, append the right side of the equation that reflects the described influence.\n\n".format(icl_examples, rationale, target_variable, current_equation, currently_involved_vars)}
    ]
    
    parseable = False
    while not parseable: 
        initial_answer, parseable, results = basic_utils.safe_gemini_ask(messages, model = 'pro')
        
    # basic_utils.crprint(json.dumps(results, indent = 4))
    
    return results["updated_equation"], results["involved_variables"]


def match_variable_names(names_from_string = None, grounded_variables = None): 
    
    icl_examples = basic_utils.load_icl(inspect.currentframe())
    
    
    messages = [
            {"role": "system", "content": """
    You are an expert data analyst with string matching expertise assisting the user in matching potentially misspelled variable names to a list of correctly spelled, grounded variable names. Concretely, you are expected to analyze each variable name extracted from an input string and match it to the closest variable name from the grounded list, considering potential misspellings. 
    Answer in a JSON format as follows:
    ```json
    {{
    
        "matches" : [
            [
                "Variable name 0 as found in the input string",
                "Matching variable name from the grounded list"
            ],
            [
                "Variable name 1 as found in the input string",
                "Matching variable name from the grounded list"
            ],
            // add more items as needed...
        ]    
    }} 
    ```
    """}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n Names From String\n{}\n\n Grounded Variables\n{}\n\nGiven a string containing potentially misspelled variable names and a list of grounded variable names, match each misspelled name to its correctly spelled counterpart, returning a nested list of [misspelled_name, grounded_name] pairs.\n\n".format(icl_examples, names_from_string, grounded_variables)}
    ]
    
    parseable = False
    while not parseable: 
        initial_answer, parseable, results = basic_utils.safe_gemini_ask(messages, model = 'pro') 
    # basic_utils.crprint(json.dumps(results, indent = 4))
    
    return results["matches"]


def suggest_variable_usage(system_description = None, variable_name = None): 
    
    icl_examples = basic_utils.load_icl(inspect.currentframe())
    
    
    messages = [
            {"role": "system", "content": """
    You are an AI agent suggesting direct usage for a given variable/constant based on the provided system dynamics description. You will receive the description of the system dynamics and the name of the variable/constant.  Your task is to suggest how this variable/constant can be used in the model of the system dynamics. 
    Answer in a JSON format as follows:
    ```json
    {{
    
        "direct_suggestion" : "Suggested direct usage of the variable/constant in the system dynamics model", // which variables or processes are directly influenced/ depend on the variable/constant
        "directly_influenced_variables": ["var0", "var1", ...], // list of variables directly influenced by the variable/constant
        "next_step" : "Next step in the analysis process" // description of the next step in the analysis process
    
    }} 
    ```
    """}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n System Description\n{}\n\n Variable Name\n{}\n\nGiven the system dynamics description and the name of a variable, suggest the direct influence of the variable of interest and provide a concise overview of next step.\n\n".format(icl_examples, system_description, variable_name)}
    ]
    
    parseable = False
    while not parseable: 
        initial_answer, parseable, results = basic_utils.safe_gemini_ask(messages, model = 'pro') 
    # basic_utils.crprint(json.dumps(results, indent = 4))
    
    return results["direct_suggestion"], results["directly_influenced_variables"]


def recommend_function_config(system_dynamics_description = None, target_variable = None, function_code = None): 
    
    icl_examples = basic_utils.load_icl(inspect.currentframe())
    
    
    messages = [
            {"role": "system", "content": """
You are an expert AI agent in control systems and optimization, assisting the user in configuring functions for specific system dynamics. 
You will be provided with a description of the system, the **target relationship for which we are trying to define an initial configuration** and the code of the function that requires configuration so it's inner working are clear and the proposed configuration is relevant.
Concretely, you are expected to recommend a list of x,y values in a reasonable range that could be used to configure the function. Your output should be a JSON with a single key 'function_config_recommandation' containing a list of dictionaries, each dictionary representing a recommended x,y pair.
Answer in a JSON format as follows:
```json
{{  
    "rationale": "A concise extract from the text (if available) or your concise rationale for the recommendation",
    "function_config_recommandation" : [
        [x0, y0],
        // add as needed...     
        ]

}} 
```
    """}, 
        {"role": "user", "content": " {} For this particular task instance, the following elements are provided:\n System Dynamics Description\n{}\n\n Target relationship: \n{}\n\nFunction Code\n{}\n\nGiven the system dynamics description and the function code, recommend a list of x,y values in a reasonable range that could be used to configure the function.\n\n".format(icl_examples, system_dynamics_description, target_variable, function_code)}
    ]

    
    parseable = False
    while not parseable: 
        initial_answer, parseable, results = basic_utils.safe_gemini_ask(messages, model = 'pro') 
    # basic_utils.crprint(json.dumps(results, indent = 4))
    
    return results['rationale'], results["function_config_recommandation"]


def system_dynamics_code_completer(system_description=None, incomplete_code=None, available_variables=""):

    icl_examples = ""
    messages = [
        {
            "role": "system",
            "content": """
You are an efficient AI agent, assisting the user in completing code snippets based on system dynamics descriptions. 
In particular, you have exceptional skills in filling in missing elements in code. You will be provided with a system dynamics description, an incomplete code snippet and some available variables in the considered system. Concretely, you are expected to analyze the system dynamics description, identify the missing element in the code snippet, and suggest a completion with a level of certainty (an integer between 0 and 10, with 10 indicating maximal confidence).
The provided variables can be used to complete the code snippet. These are the following: 
{}
Answer in a JSON format as follows:
    ```json
    {{
        "suggested_element_replacement" : ["initial_variable_name_to_replace", "variable_name_to_use_as_a_replacement", "sentence from the text supporting your replacement suggestion"], // only the part for the replacement as the answer will be directly inserted
        "confidence" : 0-10 // integer between 0 and 10
    }} 
    ```
""".format(available_variables),
        },
        {
            "role": "user",
            "content": " {} For this particular task instance, the following elements are provided:\n System Description\n{}\n\n Incomplete Code\n{}\n\nFill in the missing element in the code snippet based on the system dynamics description\n\n".format(
                icl_examples, system_description, incomplete_code
            ),
        },
    ]
    parseable = False
    while not parseable: 
        # initial_answer, parseable, results = momeutils.safe_llm_ask(messages, model = "pro")
        initial_answer, parseable, results = basic_utils.safe_gemini_ask(messages, model = 'pro') 
    # basic_utils.crprint(json.dumps(results, indent=4))
    return (results["suggested_element_replacement"], results["confidence"])

def extract_overlapping_constants(text=None):
    icl_examples = ""
    messages = [
        {
            "role": "system",
            "content": """
You are a specialized AI agent, assisting the user in identifying overlapping constants in dynamic systems. In particular, you have exceptional skills in extracting relevant information from text. You will be provided with text describing constants for a dynamic system. Concretely, you are expected to carefully analyze the text and identify names of constants that refer to the same entity, grouping them accordingly.
Answer in a JSON format as follows:
```json
    {{
    "overlapping" : [
    ["name0","name0 bis", "name0 ter"...],
    ["name1","name1 bis", ...],
     // add as needed... 
    ]

}} 
```
""",
        },
        {
            "role": "user",
            "content": " {} For this particular task instance, the following elements are provided:\n Text\n{}\n\nFind and group names of constants that refer to the same entity\n\n".format(
                icl_examples, text
            ),
        },
    ]
    parseable = False
    while not parseable: 
        initial_answer, parseable, results = basic_utils.safe_gemini_ask(messages, model = 'pro') 
    # basic_utils.crprint(json.dumps(results, indent=4))
    return results["overlapping"]


def extract_system_constants(system_description=None):
    icl_examples = ""
    messages = [
        {
            "role": "system",
            "content": """
    You are a skilled AI assistant, helping the user in extracting system constants. In particular, you are skilled in parsing system descriptions to identify constants. You will be provided with a system description. 
    Concretely, you are expected to extract constants from the given system description and provide a JSON object with a list of identified constants, including their names, values, and units. If the value of some constants is not explicitly provided, you should still include them in your answer and put null as the value.
    Answer in a JSON format as follows:
    ```json
        {{
            "identified_constants" : [
                ["constant name","constant_value", "unit"]
                    // add as needed... 
                ]
        }} 
    ```
        """,
        },
        {
            "role": "user",
            "content": " {} For this particular task instance, the following elements are provided:\n System Description\n{}\n\nExtract constants from the given system description\n\n".format(
                icl_examples, system_description
            ),
        },
    ]
    parseable = False
    while not parseable: 

        initial_answer, parseable, results = basic_utils.safe_gemini_ask(messages, model = 'pro') 
    # basic_utils.crprint(json.dumps(results, indent=4))
    return results["identified_constants"]

def extract_system_time_horizon(system_description=None):
    icl_examples = ""
    messages = [
        {
            "role": "system",
            "content": """
You are a skilled AI assistant, helping the user in extracting time horizons from system dynamics. In particular, you are skilled in parsing system dynamics descriptions to identify time horizon information. You will be provided with a system description. 
Concretely, you are expected to help frame the time horizon of the system dynamics described in the text. If available, you should extract the time horizon information and provide a JSON object with the identified time horizon, otherwise provide your best guess based on the contents and your implicit expert knowledge.
Answer in a JSON format as follows:
```json
    {{
        "extracted_time_horizon" : ["sentence from the text supporting your time horizon extraction", time_unit, simulation_start, simulation_stop, simulation_delta], // simulation_start, simulation_stop, simulation_delta are the time horizon parameters (float or int) --> use this if the time horizon is explicitly mentioned in the text. Make sure it is included in your answer even if the value is not explicitly provided in the text.
        "best_guess_time_horizon" : ["sentence from the text supporting your time horizon extraction", time_unit, simulation_start, simulation_stop, simulation_delta] // --> use this if the time horizon is not explicitly mentioned in the text. Make sure it is included in your answer even if the value is explicitly provided in the text.
    }} 
```

"""
        },
        {
            "role": "user",
            "content": " {} For this particular task instance, the following elements are provided:\n System Description\n{}\n\nExtract (or provide best guess) time horizon from the given system description. Make sure both JSON keys are present in your answer, leaving the one not corresponding as an empty list.\n\n".format(
                icl_examples, system_description
            ),
        },
    ]
    parseable = False
    while not parseable: 
        initial_answer, parseable, results = basic_utils.safe_gemini_ask(messages, model = 'pro') 
    # basic_utils.crprint(json.dumps(results, indent=4))
    
    processed_result = {"start": None, "stop": None, "delta": None, "unit": None, "extraction_mode": None}
    target = "extracted_time_horizon" if len(results["extracted_time_horizon"]) > 0 else "best_guess_time_horizon"
    processed_result["unit"] = results[target][1]
    processed_result["start"] = results[target][2]
    processed_result["stop"] = results[target][3]
    processed_result["delta"] = results[target][4]
    processed_result["extraction_mode"] = target
    return processed_result

def identify_influencing_elements(system_description=None, current_func = None, target_variable=None, unused_variables = None, problematic_var = None, problematic_line = None, additional_message = None):
    icl_examples = ""

    if unused_variables is not None: 

        target_variable = problematic_var # thats for printing purposes

        content = """
# ========================
# SYSTEM DYNAMICS DESC
{system}
# ========================

In fact, a first pass has already been done to create the system but a set of issues have been identified. 
{unused}

We are currently focusing the the following problematic line of code in the system: 
Problematic line {prob} to update: {line}

Using the above system description{add_unused}extract elements that influence the target variable: ** {problematic_value} ** from the system dynamics description using the provided JSON formatting. 

        """.format(
            prob = "(because {})".format(additional_message) if additional_message is not None else "",
            system = system_description,
            problematic_value = problematic_var, 
            add_unused = " and, if relevant the provided unused variables, " if len(unused_variables) > 0 else ", ",  
            line = problematic_line['line'].replace('sode_utils.', '').replace('sutils.', ''),
            unused = "Some constants / variables are not used in the system. They may be useful for the completion of the system. \nUnused variables:\n{}".format("\n* ".join([""] + unused_variables)) if len(unused_variables) > 0 else "")

    else: 

        content = " {} For this particular task instance, the following elements are provided:\n System Description\n{}\n\n The existing dynamics as a sample code function from which you can pull existing variables: \n{}\n\nTarget Variable\n{}\n\nExtract elements that influence a given target variable from a system dynamics description\n\n".format(
                icl_examples, system_description, current_func, target_variable
            )

    messages = [
        {
            "role": "system",
            "content": """
You are a remarkably efficient AI agent, supporting the user in identifying elements influencing a target variable in dynamic systems. In particular, you have exceptional skills in extracting relevant information from system descriptions. 
Concretely, you are expected to process a system description and a target variable, and then identify the elements that influence the target variable, providing a JSON output with the involved variables and their relationships, along with a concise description of the required mathematical operations. In case of constants, please flag them as such and collect their values. 
When writing equations, avoid using numerical values if a constant is involved. In those cases, simply refer to the constant by its name.
It is paramount that you only focus on the first stage of the analysis, which is identifying the elements influencing the target variable: that is identify the immediate variables that directly influence the target variable (as the full system will be iteratively constructed in subsequent steps).
The answer structure also enables to flag constants and their values. 
Answer in a JSON format as follows:
    ```json
    {{
        "text_reference": "sentence from the text supporting your analysis regarding the target variable", 
        "is_constant" : [true/false, value if true else null], // if constant, obviously the field equation and directly_involved_variables are not needed
        "directly_involved_variables" : [var0, var1,...  ], // list of variables directly influencing the target variable. If above constant is true, simply write null
        "equation" : "write the mathematical operation (right-side only) using variable names whenever adequate", // beyond obvious (+, - , / , * ), available functions are [piecewise_linear(the_driving_variable), conditional(the_driving_variable), step_after_time(the_driving_variable)] where the_driving_variable represents the quantity to which the function will be applied, if constant, simply write null
        "next_step" : "Next step in the analysis process", // description of the next step in the analysis process    
    }} 
    ```
                """,
        },
        {
            "role": "user",
            "content": content
        },
    ]

    parseable = False
    while not parseable: 
        initial_answer, parseable, results = basic_utils.safe_gemini_ask(messages, model = 'pro') 
    # basic_utils.crprint("Target variable is {}\n\n{}".format(target_variable, json.dumps(results, indent=4)))
    return (
        results["directly_involved_variables"],
        results["equation"],
        results["is_constant"],
    )




def system_dynamics_analyzer(system_description=None):
    icl_examples = ""
    messages = [
        {
            "role": "system",
            "content": '\nYou are a highly efficient AI agent, supporting the user in analyzing system dynamics. In particular, you excel at identifying crucial components in complex systems. \nYou will be provided with a description of the system. Concretely, you are expected to analyze the system description to identify the main stocks to be tracked in the system, and then provide a JSON object with a list of the identified stocks.\nBe mindful, as the stocks in your answer must be explicitely targeted by the text. That is, there might be some quantities/stocks that could be worth tracking but for simplification purposes, you should strongly adhere to the ones explicitely identified as target in the text. \nAnswer in a JSON format as follows:\n```json\n{{\n"identified_stocks" : [\n    "stock1",\n    // add as needed... \n    ], \n"target_stocks" : [identified_stock0, ...] // from the identified stocks, which one(s) are the main target(s) of the system description \n    \n}} \n```\n',
        },
        {
            "role": "user",
            "content": " {} For this particular task instance, the following elements are provided:\n System Description\n{}\n\nAnalyze the system description to identify the main stocks to be tracked\n\n".format(
                icl_examples, system_description
            ),
        },
    ]
    parseable = False
    while not parseable: 
        initial_answer, parseable, results = basic_utils.safe_gemini_ask(messages, model = 'pro') 
    # basic_utils.crprint(json.dumps(results, indent=4))
    return results["target_stocks"]


def init_system_structure( target_stocks, time_params, stocks_ci, constants=None, structure_path=os.path.join(os.path.dirname(__file__), ".tmp.json"),):


    to_save = [var_name_format(target_stocks)] if isinstance(target_stocks, str) else [var_name_format(t) for t in target_stocks]
    constant_cleaned = [[var_name_format(c[0]), c[1], c[2]] for c in constants if constants is not None]
    stocks_ci_cleaned = [[var_name_format(c[0]), c[1], c[2]] for c in stocks_ci]
    result_dict = {"target_stocks": [var_name_format(s) for s in to_save], 
                   "time_params": time_params, 
                   "constants": constant_cleaned, 
                   "stocks_ci": stocks_ci_cleaned,
                   }

    return result_dict


def var_name_format(var):
    if var is None:
        return None
    return var.strip().lower().replace(" ", "_").replace('\'', '').replace('\"', '').replace(':', "")


def scp(is_constant):
    # safe constant processing 
    if isinstance(is_constant, list):
        return is_constant
    elif isinstance(is_constant, bool):
        return [is_constant, None]

def sprv(required_vars):
    # safe processing of required variables
    if required_vars is None:
        return None
    return [var_name_format(v) for v in required_vars]

def sep(current_eq, current_vars): 
    if current_eq is None:
        return None
    elif current_eq.strip() == "null":
        return None
    


    # REQUIRED TO AVOID PARTIAL REPLACEMENTS
    current_vars = sorted(current_vars, key = lambda x: len(x), reverse = True)

    for v in current_vars:
        current_eq = current_eq.replace(v, var_name_format(v))
    # momeutils.uinput('Equation out: {}'.format(current_eq))   
    return current_eq

def get_unit_from_structure(structure, var):
    # print(var)
    for existing_constant in structure["constants"]:
        if var == existing_constant[0]:

            return existing_constant[2]

    return ""


def run_system_construction(config):
    system_desc = open(config['system_description_path']).read()
    structure = json.load(open(config['structure_file_path']))

    structure["workflow"] = []
    processed_vars = []

    def process_variable(var):
        basic_utils.crprint("Processing variable: {}".upper().format(var))
        if var is None:
            basic_utils.crprint("Found constant (most likely)")
            return
        if var_name_format(var) in processed_vars + ['t']:
            basic_utils.crprint("Variable already processed")
            return
        elif var_name_format(var) in [var_name_format(s[0]) for s in structure["constants"]]:
            basic_utils.crprint("Variable identified as constant")
            return
        

        intermediate_code = code_func_construction(config, override_structure = structure)
        intermediate_code ="Current system dynamics function:\n\n```python\ndef SD{}```\n\n".format(intermediate_code.split('# INIT')[0].split('def SD')[1])

        (required_vars, eq, is_constant) = identify_influencing_elements(system_desc, intermediate_code, var)
        structure["workflow"].insert(0, 
            {
                "target": var,
                "code_name": var_name_format(var),
                "operation": sep(eq, required_vars), # ENSURES THAT THE VARIABLES ARE FORMATTED --> AVOIDS FOOD PER DEER / INITIAL FOOD PER DEER 
                "variables": sprv(required_vars),
                "is_constant": scp(is_constant) + [get_unit_from_structure(structure, var)],
            }
        )

        processed_vars.append(structure["workflow"][0]["code_name"])
        if required_vars is not None:
            for v in required_vars:
                process_variable(v)

    for constant in structure["constants"]:
        structure = add_constant_to_structure(structure, constant)
    for stock in structure["target_stocks"]:
        process_variable(stock)
   
   
    return structure

def add_constant_to_structure(structure, constant): 
    structure['workflow'].append(
        {
            "target": constant[0],
            "code_name": var_name_format(constant[0]),
            "operation": None,
            "variables": None,
            "is_constant": [True, constant[1], get_unit_from_structure(structure, var_name_format(constant[0]))],
        }
    )
    return structure   




def clean_system_constants(config):
    
    structure_path = config['structure_file_path']

    structure = json.load(open(structure_path, "r"))
    collected_constants = []
    collected_constants += [[var_name_format(s[0]), s[1]] for s in structure["constants"]]
    for step in structure["workflow"]:
        if step["is_constant"][0]:
            if not var_name_format(step["target"]) in [c[0] for c in collected_constants]:
                collected_constants.append([step["target"], step["is_constant"][1]])
    collected_constants = "\n".join(["{} = {}".format(c[0], c[1]) for c in collected_constants])

    doubles = extract_overlapping_constants(collected_constants)


    to_keep = []
    to_replace = []
    for double in doubles:
        if len(double) == 1:
            basic_utils.crline('Skipping {} because single element'.format(double[0]))
            continue
        # if any one of the double is in structure["constants"], that's the one to keep, otherwise, first one arbitrarily kept 
        if double[0] in [c[0] for c in structure["constants"]]:
            to_keep.append(double[0])
            to_replace.append(double[1])
        elif double[1] in [c[0] for c in structure["constants"]]:
            to_keep.append(double[1])
            to_replace.append(double[0])
        else: 
            to_keep.append(double[0])
            to_replace.append(double[1])

    # RECONSTRUCT THE SYSTEM
    new_system = {}
    new_system["target_stocks"] = structure["target_stocks"]
    new_system["time_params"] = structure["time_params"]
    new_system["stocks_ci"] = structure["stocks_ci"]
    new_system["constants"] = [c for c in structure["constants"] if c[0] not in to_replace]

    new_system["workflow"] = []
    for step in structure["workflow"]:
        
        if step["target"] in to_replace:
            continue
        else: 
            reconstructed_step = step
            for i in range(len(to_replace)):
                reconstructed_step['target'] = reconstructed_step['target'].replace(to_replace[i], to_keep[i])
                reconstructed_step['code_name'] = reconstructed_step['code_name'].replace(to_replace[i], to_keep[i])
                if reconstructed_step['variables'] is not None:
                    reconstructed_step['variables'] = [reconstructed_step['variables'][j].replace(to_replace[i], to_keep[i]).replace(var_name_format(to_replace[i]), to_keep[i]) for j in range(len(reconstructed_step['variables']))]
                if reconstructed_step['operation'] is not None:
                    reconstructed_step['operation'] = reconstructed_step['operation'].replace(to_replace[i], to_keep[i]).replace(var_name_format(to_replace[i]), to_keep[i])    
                
            new_system["workflow"].append(reconstructed_step)
    

    return new_system



def spe(eq_desc, missing_placeholder = "TO_CHECK"):
    # momeutils.crline(eq_desc)
    if eq_desc.strip() == "null": 
        return missing_placeholder
    return eq_desc if not "=" in eq_desc else eq_desc.split("=")[-1].strip()



def clean_system_eqs(config):

    structure_path = config['structure_file_path']
    missing_placeholder = config['missing_placeholder']
    structure = json.load(open(structure_path, "r"))
    for step in structure["workflow"]:
        if step["operation"] is not None:
            valid = False 
            try: 
                ast.parse(step["operation"])
                valid = True 

            except:
                basic_utils.crline('Invalid syntax for {} Inserting placeholder {}'.format(step["operation"], missing_placeholder))
                step['operation'] = missing_placeholder
        else:
            if not step['is_constant'][0]:
                step['operation'] = missing_placeholder
            
    return structure



def code_func_construction(config, **kwargs): 
    structure_file_path = config['structure_file_path']
    structure = json.load(open(structure_file_path, 'r'))
    if 'override_structure' in kwargs.keys(): 
        structure = kwargs['override_structure'] 

    template_file = config['template_file']
    
    code = open(template_file, "r").read()

    to_return = []
    for stock in structure["target_stocks"]:
        for step in structure["workflow"]:
            if step["code_name"] == var_name_format(stock):

                to_return.append(spe(step["operation"]))
    to_return = ", ".join(to_return)

    system_dynamics = []
    system_constants = []
    system_stocks = []

    for step in structure["workflow"]:#[::-1]:
        if step["code_name"] in [var_name_format(s) for s in sorted(structure["target_stocks"])]:
            system_stocks.append("{} = {}".format(step["code_name"], "x[{}]".format(len(system_stocks))))
            continue
        constant = scp(step["is_constant"])
        if constant[0]:
            system_constants.append(
                "{n} = args['constants']['{n}']".format(n = step["code_name"])
            )
        elif step["operation"] is None:
            system_dynamics.append(
                "{} = {}".format(step["code_name"], "to_check".upper())
            )
        else:
            system_dynamics.append(
                "{} = {}".format(step["code_name"], spe(step["operation"]))
            )
    system_dynamics = "\n    ".join(
        [""] + ['# CONSTANTS'] + system_constants + [""] * 2 + ['# STOCKS'] + system_stocks + [""] * 2 + ['# DYNAMICS'] + system_dynamics + [""] * 2
    )
    code = code.replace("TO_REPLACE", system_dynamics)
    code = code.replace("TO_RETURN", to_return)
    return code

def handle_code_time_params(current_code, structure):

    time_params = structure["time_params"]
    time_start = time_params['start']
    time_stop = time_params['stop']
    time_delta = time_params['delta']
    time_unit = time_params['unit']
    extraction_method = time_params['extraction_mode']
    current_code = current_code.replace("TIME_HORIZON", "t = np.linspace({}, {}, {}) # Unit: {} # Extraction method: {}".format(time_start, time_stop, int((time_stop - time_start) / time_delta), time_unit, extraction_method)) 
    return current_code


def handle_simulation_params(current_code, structure): 
    
    stocks_ci = structure['stocks_ci']
    stocks_values_and_msg = [[var_name_format(s[0]), s[1] if s[1] is not None else s[2], "From text" if s[1] is not None else "Using model implicit knowledge"] for s in stocks_ci]
    init_values = ["{} = {} # {}".format(s[0], s[1], s[2]) for s in stocks_values_and_msg]

    init_values += ["x = [{}]".format(", ".join([var_name_format(s) for s in sorted(structure["target_stocks"])]))]
    init_values = "\n".join(init_values)

    current_code = current_code.replace("INIT_VALUES", init_values)

    
    # PREPARING SIMULATION 

    constant_list = sode_code_utils.construct_dict([c[0] for c in structure['constants']], [c[1] for c in structure['constants']])
    current_code = current_code.replace('RUN_SIM', sode_code_utils.function_call_assignment('result', 'odeint', ['SD', 'x', 't', "args = ({}, )".format("{{'constants': {}}}".format(constant_list))]))
    
    return current_code    

def handle_function_calls(current_code, target_lib, missing_placeholder, 
                          target_functions = ['lookup', 'step_after_time', 'conditional', 'piecewise_linear']):
      
    for target_function in target_functions:

        lines_no, _  = sode_code_utils.find_function_calls(current_code, target_function)

        for line_no in lines_no: 
            line = current_code.split('\n')[line_no -1]


            cleaned_identifier = "".join([c for c in line.split("=")[0].lower() if c.isalnum()])[:30]
            updated_line = sode_code_utils.add_function_arguments(line.strip(), target_function, {'func_id': f'"{target_function}_{cleaned_identifier}"'})

            current_code = current_code.replace(line.strip(), updated_line)


    current_code = sode_code_utils.add_module_to_function_call(current_code, target_lib, target_functions)
    for target_function in target_functions:
        line_no, _ = sode_code_utils.find_function_calls(current_code, target_function)
        for no in line_no:
            line = current_code.split('\n')[no - 1]
            expected_from_reference, provided_in_call = sode_code_utils.function_params_from_source_reference(line.strip(), target_function, module_path = os.path.join(os.path.dirname(__file__), 'sode_utils.py')) # DIRTY FIX

            reconstructed_line = sode_code_utils.align_function_call_params(line.strip(), provided_in_call, expected_from_reference, placeholder = missing_placeholder)

            current_code = current_code.replace(line.strip(), reconstructed_line.strip())   
            
    return current_code


def code_construction(config):

    structure_file_path = config['structure_file_path']
    output_code_path = config['target_code_file']
    target_lib = config['target_lib']
    missing_placeholder = config['missing_placeholder']

    structure = json.load(open(structure_file_path, "r"))
    code = code_func_construction(config)

    # OUTSIDE OF MAIN FUNCTION 

    # TIME PARAMS 
    code = handle_code_time_params(code, structure)
    
    # SIM PARAMS 
    code = handle_simulation_params(code, structure)
    # UPDATING FUNCTIONS CALLS TO HANDLE USAGE 
    
    code = handle_function_calls(code, target_lib, missing_placeholder)

    with open(output_code_path, "w") as f:
        f.write(code)
    return output_code_path

def update_structure_eq(structure_path, target_var, replacement_eq):
    structure = json.load(open(structure_path, "r"))

    assert isinstance(target_var, str)


    for step in structure["workflow"]:
        if step["code_name"] == var_name_format(target_var):
            step["operation"] = replacement_eq
    with open(structure_path, "w") as f:
        json.dump(structure, f, indent=4)
    return structure_path

def code_placeholder_check(config):
    
    system_desc = open(config['system_description_path']).read()
    path = config['target_code_file']
    structure_path = config['structure_file_path']
    target_placeholders = config['missing_placeholder']
    
    system_structure = json.load(open(structure_path, "r"))

    code = open(path, "r").read() 
    # LOOKS FOR THE PLACEHOLDERS IN THE CODE
    target_lines, lines_no = sode_code_utils.get_lines_with_variables(code, target_placeholders)
    
    
    for line, lineno in zip(target_lines, lines_no):
        basic_utils.crline('Processing {}'.format(line))

        # COLLECTS VARIABLE DEFINED IN THE FUNCTION SD ABOVE THE TARGET PLACEHOLDER (ALSO GATHERS VARIABLES IN THE FUNCTION DEF (AKA TIME))
        vars = sode_code_utils.get_available_vars_in_function(code, "SD", line)
        suggested, confidence = system_dynamics_code_completer(system_description = system_desc, incomplete_code = line, available_variables = "\n * ".join([""] + vars))
        
        accepted = basic_utils.uinput('Initial line: {}\nSuggested replacement: {}\nBased on : {}\nModel Confidence: {}/10\nAccept? (y/n)'.format(line, suggested[1], suggested[2], confidence)).strip().lower()
        if accepted == "y": 
            updated_line = line.replace(suggested[0], suggested[1])

            code = code.replace(line.strip(), updated_line.strip())

            # Updating the structure 
            for step in system_structure["workflow"]:
                if step["code_name"] == var_name_format(sode_code_utils.get_left_side(line)[0]):
                    step["operation"] = suggested[1]

    
    return system_structure
   

def handle_problematic_stores(system_desc, current_system_structure_path, system_func):
    
    """
    Handle problematic variable stores in the system function by identifying and resolving issues.

    This function analyzes the system function for unused variables and problematic stores,
    then proposes and applies corrections based on user validation.

    """
    stage_log = {}
    
    unused_variables = sode_code_utils.find_unused_variables(system_func) 
    problematic_stores = sode_code_utils.find_problematic_stores(system_func) # IN SOME CASES, THE MODEL WAS USING A VAR IN ITS DEFINITION EG: X = X +1 

    for k in problematic_stores.keys(): 
        
        # CAREFUL TO THE REPLACE SODE_UTILS in identify_influencing_elements: SUPPOSED TO PREVENT MODEL DISTRACTION BUT ITS A TEMPORARY FIX 
        involved_vars, eq, _ = identify_influencing_elements(system_desc, unused_variables=unused_variables, problematic_var = k, problematic_line = problematic_stores[k], additional_message="The variable is called AND defined in the same line. Left-hand side is fine but RHS must contain some other variables.")
        
        user_validation = basic_utils.uinput("Identified issue with {k}\n{ps}\nProposed resolution: {k} = {eq}\n Accept y/n".format(k = k,
                                                                                                                                   eq = eq, 
                                                                                                                                   ps = problematic_stores[k]['line'])).strip().lower()
        
        if user_validation == "y":
            # update structured representation 
            stage_log[k] = {"issue": "problematic_store",
                            "valid": True, 
                            "rejection_reason": None,
                            "target_vars": k,
                            "current_eq": problematic_stores[k]['line'],
                            "to_insert": {
                                "operation": eq,
                                "variables": involved_vars
                                }                                    
                            }

        
        else: 
            stage_log[k] = {"issue": "problematic_store",
                            "valid": False, 
                            "rejection_reason": "User validation not given",
                            "target_vars": k,
                            "current_eq": problematic_stores[k]['line'],
                            "proposed_eq": eq, 
                            "proposed_vars": involved_vars
                            }
    return stage_log


def check_unused_variables(system_desc, current_system_structure_path, system_func):

    """
Checks for unused variables in the system function. Clear suggestions are provided to integrate these variables into the system dynamics.
If the suggestion is unclear, it is added to a log for further analysis.   
    
    """
    stage_log = {}
    current_system_structure = json.load(open(current_system_structure_path, "r"))
    
    unused_variables = sode_code_utils.find_unused_variables(system_func)
    available_vars =[s['code_name'] for s in current_system_structure["workflow"]]
    for var in unused_variables:
        rationale, target_vars = suggest_variable_usage(system_desc, var)

        target_vars_aligned = {v : None for v in target_vars}
        for tv in target_vars: 
            if tv in available_vars:
                target_vars_aligned[tv] = tv
        
        # IF SOME VARIABLE NAMES DO NOT MATCH, GO THROUGH LLM 
        missing = [k for k, v in target_vars_aligned.items() if v is None]
        if len(missing) > 0:
            result = match_variable_names(missing, available_vars)
            for r in result: 
                target_vars_aligned[r[0]] = r[1]
        
        for k in target_vars_aligned.keys(): 
            current_representation = [s for s in current_system_structure["workflow"] if s["code_name"] == target_vars_aligned[k]][0]
            new_eq, new_vars = update_system_dynamics_equation(rationale, target_vars_aligned[k], current_representation['operation'], current_representation['variables'])

            # check if new vars are in the structure
            missing_new_vars = [v for v in new_vars if v not in available_vars]
            if len(missing_new_vars) > 0: # if some variables are not in the structure, log for further updates / analysis 
                stage_log[k] = {"issue": "Introduced new variables",
                            "valid": False,
                            "rejection_reason": "Variables not found in the structure",
                            "rationale": rationale,
                            "target_vars": target_vars_aligned[k],
                            "suggested_new_vars": new_vars,
                            "missing_vars": missing_new_vars,
                            "new_eq": new_eq}   
                         
            else:  # ask for user validation before integration 
                valid = basic_utils.uinput('{} was defined but not used. Proposed integration in {}\nOld eq: {}\nNew eq: {}\nValid ? (y/n)'.format(k, target_vars_aligned[k], current_representation['operation'], new_eq))
                if valid.strip().lower() == "y":
                  
                  
                    stage_log[k] = {"issue": "Introduced new variables",
                                "valid": True,
                                "rejection_reason": None,
                                "rationale": rationale,
                                "current_target_vars": target_vars_aligned[k],
                                "current_eq" : current_representation['operation'],
                                "to_insert": {
                                    "variables": new_vars,
                                    "operation": new_eq  
                                }
                            }
                else:
                    stage_log[k] = {"issue": "Introduced new variables",
                                "valid": False,
                                "rejection_reason": "User validation not given",
                                "rationale": rationale,
                                "target_vars": target_vars_aligned[k],
                                "new_vars": new_vars,
                                "new_eq": new_eq}
    return stage_log
                   
                   

def collect_undefined(data): 
    defined_vars = [s['code_name'] for s in data['workflow']]

    to_check = {}
    for i, s in enumerate(data['workflow']): 
        if s['variables'] is not None:
            for v in s['variables']:
                if v not in defined_vars:
                    if v == 't' or v == "time": 
                        continue
                    if v not in to_check.keys():
                        to_check[v] = []
                    to_check[v].append(i)
    return to_check


def system_issue_checks(data, structure_file_path):
    
    
    nb_invalids = 0
    for k in data['check_results'].keys():  # all the checks (eg. problematic_stores, system_integrity...) 
        for current in data['check_results'][k].keys(): # all the variables that have issues
            if data['check_results'][k][current]['valid']:
                # update the structure 
                step_id = [i for i, s in enumerate(data['workflow']) if s["code_name"] == current][0]
                data['workflow'][step_id]['operation'] = data['check_results'][k][current]['to_insert']['operation']
                data['workflow'][step_id]['variables'] = data['check_results'][k][current]['to_insert']['variables']
            else: 
                nb_invalids += 1
    
    with open(structure_file_path, "w") as f: # STILL UPDATING THE STRUCTURE FILE FOR THE CHANGES MAKING SENSE 
        json.dump(data, f, indent=4)
    if nb_invalids > 0:        
        return False
    
    return True

def run_function_check(config):  

    system_desc = open(config['system_description_path']).read()
    structure_file_path = config['structure_file_path']
    target_code_file = config['target_code_file']

    data = json.load(open(structure_file_path))
    func = sode_code_utils.get_function_code(open(target_code_file).read(), "SD")

    problematic_stores_log = handle_problematic_stores(system_desc, structure_file_path, func)
    system_integrity_log = check_unused_variables(system_desc, structure_file_path, func)

    if 'check_results' not in data.keys():
        data['check_results'] = {}
    data['check_results']['problematic_stores'] = problematic_stores_log
    data['check_results']['system_integrity'] = system_integrity_log
    valid = system_issue_checks(data, structure_file_path)
    if valid: 
        code_construction(config)
    return valid
        



def initialize_function_config(config): 
        
    system_desc = open(config['system_description_path']).read()
    code_path = config['target_code_file']
   
   
    code = open(code_path).read()
    kw_args = sode_code_utils.get_function_kw_args(sode_code_utils.get_function_code(code, "SD"))
    kw_args = sode_code_utils.get_function_kw_args(sode_code_utils.get_function_code(code, "SD"))

    # automated filling of the function config
    function_configs = {}
    for kw in kw_args: 
        if kw["keyword"] == "func_id": 
            # constructing the prompt for filling the function config 
            func_file = code_path if kw['module'] == None else os.path.join(os.path.dirname(__file__), kw['module'] + ".py")
            func_code = sode_code_utils.get_function_code(open(func_file).read(), kw['function'])
            rationale, suggested_config = recommend_function_config(system_dynamics_description = system_desc, target_variable= kw['line'], function_code = func_code)
            function_configs[kw['value']] = {"rationale": rationale, 
                                             "values" : suggested_config, 
                                             "target": kw['lhs'][0], 
                                             'function_type': " ".join(kw['value'].split('_')[:-1])} # target is the variable name in the function, useful for downstream processing
    

    basic_utils.crline('Function config initialized') 
    return function_configs
   



def load_config(config_path, **kwargs): 
    # Loading 
    with open(config_path, "r") as f: 
        config = json.load(f)
        
    # Checking for changes ;
    nb_changes = 0
    for k in config.keys(): 
        if k in kwargs.keys():
            if config[k] != kwargs[k]:
                nb_changes += 1
                config[k] = kwargs[k]

    # Saving changes 
    if nb_changes > 0:
        basic_utils.crline('Updating config file')
        with open(config_path, "w") as f: 
            json.dump(config, f, indent=4)
        

    return config

def initial_build(config_path, **kwargs): 
    
    config = load_config(config_path, **kwargs)

    system_desc_path = config["system_description_path"]
    if system_desc_path is None:
        basic_utils.crline('No system description provided. Use the --d flag to provide a system description file')
        return

    system_desc = open(system_desc_path, "r").read()

    basic_utils.crline('Identifying time parameters, you know how it goes')
    time_params = extract_system_time_horizon(system_desc)
    basic_utils.crline('Looking for those witty stocks')
    stocks = system_dynamics_analyzer(system_desc)
    basic_utils.crline('Determining initial conditions')
    stocks_initial_conditions = determine_initial_conditions(system_desc, stocks)
    basic_utils.crline('Figuring out constants')
    constants = extract_system_constants(system_desc)

    save_system_structure(init_system_structure(stocks,  time_params, stocks_initial_conditions, constants, structure_path = config["structure_file_path"]), output_name = config["structure_file_path"])
    save_system_structure(run_system_construction(config), output_name = config["structure_file_path"])
    

    code_construction(config)

def system_check(config_path, **kwargs):

    config = load_config(config_path, **kwargs)

    basic_utils.crline('Checking constant consistency')
    save_system_structure(clean_system_constants(config), output_name = config["structure_file_path"])
    basic_utils.crline('Checking equation consistency')
    save_system_structure(clean_system_eqs(config), output_name = config["structure_file_path"])    

    code_construction(config)
    basic_utils.crline('Fuzzy function interace, anyone ? ')
    save_system_structure(code_placeholder_check(config), output_name = config["structure_file_path"])
    
    basic_utils.crline('Undefined variables ?')
    valid = run_function_check(config)
    print('\n\n= = = = = Checks completed = = = = = \n\n')
    if valid: 
        basic_utils.crline('Initializing function params')
        init_system(config)
        basic_utils.crline('Ready to launch ! ')
    else: 
        basic_utils.crline('System not ready yet - Check the logs for more details {}'.format(config["structure_file_path"]))
    return valid 

    
def run_sim(config_path, **kwargs):
    config = load_config(config_path, **kwargs)
    subprocess.run(["python", config["target_code_file"]])

def save_system_structure(structure, output_name = None):
    
    if output_name is None: 
        output_name = os.path.join(os.path.dirname(__file__), "resulting_system.json")
    
    with open(output_name, "w") as f:
        json.dump(structure, f, indent=4)

def save_function_config(function_config, output_file):
    with open(output_file, "w") as f:
        json.dump(function_config, f, indent=4)

def init_system(config, **kwargs):


    save_function_config(initialize_function_config(config), config["function_config_file"])
    sode_utils.make_graph(config)

def propagate_graph_changes(config, **kwargs):
    
    config = load_config(config, **kwargs)
    structure, func_config = sode_utils.graph_to_structure(config)
    save_system_structure(structure, output_name = config["structure_file_path"])
    save_function_config(func_config, config["function_config_file"])
    code_construction(config)
    

def handle_backups(config, after_loop = False, target_files = ['structure_file_path', 'function_config_file'], backup_suffix = "_backup"): 
    
    if after_loop:
        for k in target_files: 
            if os.path.exists(config[k].replace('.json', backup_suffix + '.json')):
                os.remove(config[k].replace('.json', backup_suffix + '.json'))
    
    else: 
        # IF BACKUP EXISTS, REVERT TO IT
        if os.path.exists(config['structure_file_path'].replace('.json', backup_suffix + '.json')):
            for k in target_files: # REVERTING 
                shutil.copy(config[k].replace('.json', backup_suffix + '.json'), config[k])
        else:
            for k in target_files:
                shutil.copy(config[k], config[k].replace('.json', backup_suffix + '.json'))
    

def collab_prompt_design(config):
    
    system_desc = open(config['system_description_path']).read()
    system_data = json.load(open(config['structure_file_path'], "r"))   
    function_config_data = json.load(open(config['function_config_file'], "r"))
    available_constants = "\n".join(["{}: {}".format(c[0], c[1]) for c in system_data['constants']])
    time_params = "Time unit: {}. From {} to {} with a {} {} delta ".format(system_data['time_params']['unit'], system_data['time_params']['start'], system_data['time_params']['stop'], system_data['time_params']['delta'], system_data['time_params']['unit'])
    function_params = "Some variables rely on functions with the following parameters: \n{}".format("\n".join(["{target} relies on a {ftype} function with params (sequence of (x,y)): \n {p}".format(target = f['target'], ftype = f['function_type'], p = f['values']) for f in function_config_data.values()]))

    
    return [system_desc, available_constants, time_params, function_params]


def user_option_selection(options): 
    for i, o in enumerate(options): 
        basic_utils.crline("Option {}\nRationale:{}\nUpdate type: {} - Target: {} - Update params: {}\n\n".format(i+1, *o))
    selected = basic_utils.uinput('Selected option')
    return options[int(selected)-1]

def handle_option_update(selected, config):
    
    if selected[1].strip().lower() == "function": 
        target_data = json.load(open(config['function_config_file'], "r"))
        for k in target_data.keys(): 
            if target_data[k]['target'] == selected[2]:
                basic_utils.crline('Updating function config for {}\nOld values {}\nNew values: {}'.format(k, target_data[k]['values'], selected[3]))
                target_data[k]['values'] = selected[3]
        save_function_config(target_data, config['function_config_file'])
    else: # targeting time or constant 
        target_data = json.load(open(config['structure_file_path'], "r"))
        if selected[1].strip().lower() == "time":
            time_unit, time_start, time_stop, time_delta = selected[3]
            target_data['time_params']['unit'] = time_unit
            target_data['time_params']['start'] = time_start
            target_data['time_params']['stop'] = time_stop
            target_data['time_params']['delta'] = time_delta
        else:
            for c in target_data['constants']:
                if c[0] == selected[2]:
                    c[1] = selected[3]
        save_system_structure(target_data, output_name = config['structure_file_path'])    
        
        
        

def colab_loop(config_path, **kwargs): 

    config = load_config(config_path, **kwargs)
    basic_utils.crline('Starting the collaborative loop ! \nCurrent files are backed up. \nWrite "done" when you are with the changes --> will override the current files and remove backups')
    
    handle_backups(config)
    
    done = False 
    while not done: 
        run_sim(config_path)
        u_request = basic_utils.uinput('Changes (or "done" to conclude and save) ? ').strip()
        if u_request.lower() == "done":
            done = True
        
        else:

            basic_utils.crline('Generating options...')
            options = generate_simulation_adjustment_options(*collab_prompt_design(config), user_observation = u_request)
            selected = user_option_selection(options)
            handle_option_update(selected, config)
            
            # REGENERATE THE CODE
            code_construction(config)


    handle_backups(config, after_loop = True)
        



def init_config_file(file_path):

    run_config = {
        "system_description_path": None,
        "structure_file_path": os.path.join(os.path.dirname(__file__), "resulting_system.json"),
        "target_code_file": os.path.join(os.path.dirname(__file__), "current_model.py"),
        "function_config_file": os.path.join(os.path.dirname(__file__), "function_config.json"),
        "template_file": os.path.join(os.path.dirname(__file__), "template.txt"),
        "interactive_graph_folder": os.path.join(os.path.dirname(__file__), "interactive_graph"),
        "missing_placeholder": "TO_CHECK", 
        "target_lib": "sode_utils",
    } 
    with open(file_path, "w") as f:
        json.dump(run_config, f, indent=4)
        
def run_tests(local_config_path = os.path.join(os.path.dirname(__file__), "config.json")): 
    
    init_config_file(local_config_path)
    initial_build(local_config_path, system_description_path = os.path.join(os.path.dirname(__file__), "deers.txt"), 
                                    structure_file_path = os.path.join(os.path.dirname(__file__), "test_system.json"),
                                    target_code_file = os.path.join(os.path.dirname(__file__), "test_model.py"),
    )
    system_check(local_config_path)
    run_sim(local_config_path)
    propagate_graph_changes(local_config_path)
    
    

if __name__ == "__main__":
    
    run_tests()
