import subprocess
import ast
import astor


def add_module_to_function_call(code, module_name, function_name):
    """Adds a module name to function calls in a given code string.

    Args:
    code: The Python code as a string.
    module_name: The module name to add.
    function_name: The function name to target.

    Returns:
    The modified code with the module name added.
    """
    if isinstance(function_name, str):
        function_name = [function_name]

    for fn in function_name:
        lineno, _ = find_function_calls(code, fn)
        for i in lineno:
            line = code.split('\n')[i - 1]
            tree = ast.parse(line.strip())
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and node.id == fn:
                    node.id = f"{module_name}.{fn}"
            code = code.replace(line.strip(), ast.unparse(tree).strip())
    return code


def find_function_calls(source_code, target_function_name):
  """Finds all lines where a given function is called in Python code.

  Args:
    source_code: The Python source code to search.
    target_function_name: The name of the function to find calls to.

  Returns:
    A list of line numbers where the function is called.
  """

  tree = ast.parse(source_code)
  call_lines = []
  call_code = []

  class FunctionCallVisitor(ast.NodeVisitor):
    def visit_Call(self, node):
      # Check for function calls with 'Attribute' (for module.function)
      if isinstance(node.func, ast.Attribute):
        if node.func.attr == target_function_name:
          call_lines.append(node.lineno)
          call_code.append(ast.unparse(node))
      # Check for direct function calls
      elif isinstance(node.func, ast.Name) and node.func.id == target_function_name:
        call_lines.append(node.lineno)
        call_code.append(ast.unparse(node))

  FunctionCallVisitor().visit(tree)
  return call_lines, call_code


def align_function_call_params(code_line, provided_args_in_call, expected_from_reference, placeholder = "TO_CHECK"): 

    class FunctionCallReconstructor(ast.NodeTransformer):
        def __init__(self, expected_args, provided_args, placeholder):
            self.expected_unnamed, self.expected_named = expected_args
            self.provided_unnamed, self.provided_named = provided_args
            self.placeholder = placeholder

        def visit_Call(self, node):
            # Reconstruct unnamed arguments
            num_provided_unnamed = len(self.provided_unnamed)
            num_expected_unnamed = len(self.expected_unnamed)
            # print(num_provided_unnamed, num_expected_unnamed)
            for _ in range(num_provided_unnamed, num_expected_unnamed):
                node.args.append(ast.Name(id=self.placeholder, ctx=ast.Load()))
            # print('hereeere')
            # input(ast.unparse(node))
            # Reconstruct named arguments
            provided_named_keys = [kw.arg for kw in node.keywords]
            for expected_named in self.expected_named:
                if expected_named not in provided_named_keys:
                    node.keywords.append(ast.keyword(arg=expected_named, value=ast.Name(id=self.placeholder, ctx=ast.Load())))

            return node
        
    tree = ast.parse(code_line)
    reconstructor = FunctionCallReconstructor(expected_from_reference, provided_args_in_call, placeholder)
    new_tree = reconstructor.visit(tree)
    return ast.unparse(new_tree)


def add_function_arguments(line, func_name, new_args):
  """Adds arguments to a function call within a line of code.

  Args:
    line: The line of code as a string.
    func_name: The name of the function to modify.
    new_args: A list of strings representing the new arguments to add.

  Returns:
    The modified line of code as a string.
  """
  tree = ast.parse(line)
  for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == func_name:
      if isinstance(new_args, str):
        node.args.extend([ast.parse(new_args).body[0].value])
      elif isinstance(new_args, list):
        # node.args.extend([ast.parse(arg).body[0].value for arg in new_args])
        node.args.extend([ast.parse(str(arg), mode='eval').body for arg in new_args])
      elif isinstance(new_args, dict):
        node.keywords.extend([ast.keyword(arg=arg_name, value=ast.parse(str(arg_value)).body[0].value) for arg_name, arg_value in new_args.items()]) 
      else: 
        raise ValueError("new_args must be a string, list, or dictionary")
  return ast.unparse(tree)


def find_unused_variables(func_code):
    class UnusedVariableFinder(ast.NodeVisitor):
        def __init__(self):
            self.defined_vars = set()
            self.used_vars = set()

        def visit_Name(self, node):
            if isinstance(node.ctx, ast.Store):
                self.defined_vars.add(node.id)
            elif isinstance(node.ctx, ast.Load):
                self.used_vars.add(node.id)

        def get_unused_vars(self):
            return self.defined_vars - self.used_vars

    tree = ast.parse(func_code)
    finder = UnusedVariableFinder()
    finder.visit(tree)
    return list(finder.get_unused_vars())


def find_problematic_stores(func_code): 

    vars_and_content = {}
    problematic_vars_and_content = {}
    
    class FindVars(ast.NodeVisitor): 
        def visit_Assign(self,node): 
            right_side = ast.dump(node.value)
            for target in node.targets:
                if isinstance(target, ast.Name): 
                    vars_and_content[target.id] = right_side
                    # check if right_side contains a reference to the target (not a string, a load)
                    if self.contains_load_of_target(node.value, target.id):
                        problematic_vars_and_content[target.id] = {"rs": right_side, 
                                                                   "lineno": node.lineno,
                                                                   "line": ast.unparse(node)}
            self.generic_visit(node)

        def contains_load_of_target(self, node, target_id):
            for child in ast.walk(node):
                if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load) and child.id == target_id:
                    return True
            return False

    
    FindVars().visit(ast.parse(func_code))
    return problematic_vars_and_content


def function_call_assignment(x, fname, args = []): 


    module = ast.Module(body = [])
    assign_0 = ast.Assign(targets = [ast.Name(id = x, ctx = ast.Store())], value = ast.Call(func = ast.Name(id = fname, ctx = ast.Load()), args = [ast.Name(id = arg, ctx = ast.Load()) for arg in args], keywords = []))
    module.body.append(assign_0)
    return astor.to_source(module)


def get_function_kw_args(code):
    targets = []
    class MyVisitor(ast.NodeVisitor):
        def visit_Call(self, node): 
            # Extract function name and module name if available
            if isinstance(node.func, ast.Attribute):
                module_name = node.func.value.id if isinstance(node.func.value, ast.Name) else None
                function_name = node.func.attr
            elif isinstance(node.func, ast.Name):
                module_name = None
                function_name = node.func.id
            else:
                module_name = None
                function_name = None
                
            t = [{"module": module_name, 'function': function_name, "keyword": kw.arg, 
                  "value": ast.literal_eval(kw.value), 
                  "line": ast.get_source_segment(code, node), 
                  "lhs": get_left_hand_side_from_lineno(code, node.lineno)} for kw in node.keywords]
            targets.extend(t)
            self.generic_visit(node)
    
    MyVisitor().visit(ast.parse(code))
    return targets


def get_left_hand_side_from_lineno(code, lineno):
    line = code.split('\n')[lineno - 1]
    return get_left_side(line.strip())


def get_left_side(line_code): 
    left_side = []
    tree = ast.parse(line_code)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                left_side.append(target.id)
    return left_side


def get_function_code(source_code, function_name):
    tree = ast.parse(source_code)
    
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            start_line = node.lineno
            end_line = node.end_lineno
            result = "\n".join(source_code.split('\n')[start_line - 1:end_line])
            return result
    
    return ""  # Function not found


def get_lines_with_variables(code, target_variable_names):
    if isinstance(target_variable_names, str):
        target_variable_names = [target_variable_names]
    lines_no = []
    for target_variable_name in target_variable_names:
        target_lines_no = get_lines_with_variable(code, target_variable_name)
        lines_no.extend(target_lines_no)
    lines_no = sorted(list(set(lines_no)))
    target_lines = [line.strip() for i, line in enumerate(code.split('\n')) if i + 1 in lines_no] 

    return target_lines, lines_no


def get_lines_with_variable(code, target_variable_name):

    class VariableChecker(ast.NodeVisitor):
        def __init__(self, target_variable_name):
            self.target_variable_name = target_variable_name
            self.found = False

        def visit_Name(self, node):
            if node.id == self.target_variable_name:
                self.found = True
            self.generic_visit(node)

        def check(self, node):
            self.found = False
            self.visit(node)
            return self.found
        
    tree = ast.parse(code)
    lines = []
    lines_no = []
    checker = VariableChecker(target_variable_name)

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            # Check if target_variable_name is a target in the assignment
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == target_variable_name:
                    lines.append(ast.get_source_segment(code, node))
                    lines_no.append(node.lineno)
            # Check if target_variable_name is on the right-hand side of the assignment
            if checker.check(node.value):
                lines.append(ast.get_source_segment(code, node))
                lines_no.append(node.lineno)
        elif isinstance(node, ast.Call):
            # Check if target_variable_name is an argument in the function call
            for arg in node.args:
                if checker.check(arg):
                    lines.append(ast.get_source_segment(code, node))
                    lines_no.append(node.lineno)

    lines_no = sorted(list(set(lines_no)))
    target_lines = [line.strip() for i, line in enumerate(code.split('\n')) if i + 1 in lines_no]

    return lines_no


def get_available_vars_in_function(code, function_name, target_line, to_pop_from_def = ['args', 'kwargs']):
  
    function_code = get_function_code(code, function_name)
    
    function_args = get_function_params(code, function_name)
    for to_pop in to_pop_from_def: 
        if to_pop in function_args: 
            function_args.remove(to_pop)


    lineno = find_line_number(function_code, target_line)
    if lineno > 0: 
        return function_args + get_vars_before_line(function_code, lineno)
    return function_args   


def get_function_params(code, function_name, merge = True):

    # Parse the code into an AST object
    tree = ast.parse(code)

    # Traverse the AST to find the function definition node
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            # Initialize lists for unnamed and named parameters
            unnamed_params = []
            named_params = []

            # Extract the input parameters from the function definition node
            for param in node.args.args:
                unnamed_params.append(param.arg)

            # Extract the default values for named parameters
            defaults = [None] * (len(unnamed_params) - len(node.args.defaults)) + node.args.defaults
            for param, default in zip(unnamed_params, defaults):
                if default is not None:
                    named_params.append(param)
                    unnamed_params.remove(param)

            # Handle keyword-only arguments (Python 3+)
            for kwonly_param in node.args.kwonlyargs:
                named_params.append(kwonly_param.arg)
            if merge:
                return unnamed_params + named_params
            return unnamed_params, named_params

    # Return None if the function definition is not found
    return None, None


def find_line_number(code, target_line):
  """Finds the line number of a given line string in a Python code string.

  Args:
    code: The Python code string to search.
    target_line: The line string to find.

  Returns:
    The line number of the target line, or -1 if not found.
  """
  tree = ast.parse(code)
  for i, node in enumerate(ast.walk(tree)):
    if isinstance(node, ast.stmt) and node.lineno is not None:
      current_line = ast.unparse(node).strip()
      if current_line == target_line:
        return node.lineno
  return -1


def get_vars_before_line(code, target_line):
  """Collects variable names defined before a target line in Python code.

  Args:
    code: The Python code as a string.
    target_line: The line number before which to collect variables.

  Returns:
    A set of variable names.
  """

  tree = ast.parse(code)
  vars_found = []

  class VariableCollector(ast.NodeVisitor):
    def visit_Name(self, node):
      if isinstance(node.ctx, ast.Store) and node.lineno < target_line:
        vars_found.append(node.id)

  VariableCollector().visit(tree)
  return list(set(vars_found))


def function_params_from_source_reference(target_code, function_name, module_path = None):
    """
    detects the module and the function name from the provided target_code with function call 
    
    """
    # print(target_code, function_name)
    # Parse the code into an AST object
    tree = ast.parse(target_code)

    # Traverse the AST to find the function call node: the provided code is likely to be something like my_var = my_module.my_function()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == function_name:
            # Extract the module and function names from the function call node
            module_name = node.func.value.id
            function_name = node.func.attr
            unnamed_params, named_params = get_function_params_from_module(module_name, function_name, module_path = module_path)
            provided_params = get_function_call_arguments(ast.unparse(node).strip())
            
            # PACKAGING 
            from_reference_params = [unnamed_params, named_params]
            from_call_params = [provided_params[0], provided_params[1]]

            return from_reference_params, from_call_params

    # Return None if the function definition is not found
    return None


def get_function_params_from_module(module_name, function_name, merge = False, module_path = None): 
    if module_path is not None: 
        path = module_path
    else: 
    # if module_name == "sode_utils":
    #     print('CAREFUL !! SODE_UTILS IS NOT INSTALLED !!!')
    #     path = os.path.join(os.path.expanduser("~"), "Codes", "SystemDyn", "sode_utils.py")
    # else: 
        path = collect_module_path(module_name)
    
    with open(path, 'r') as file:
        source_code = file.read()
    function_code = get_function_code(source_code, function_name)
    params_unnamed, params_named = get_function_params(function_code, function_name, merge = False)
    if merge: 
        return params_unnamed + params_named
    return params_unnamed, params_named


def collect_module_path(module_name): 
    out = subprocess.run(['python -c "import {mod};print({mod}.__file__)"'.format(mod = module_name)], shell=True, stdout=subprocess.PIPE).stdout.decode('utf-8')
    return out.strip()


def get_function_call_arguments(line):
    tree = ast.parse(line)
    function_call = next(node for node in ast.walk(tree) if isinstance(node, ast.Call))

    # Handle unnamed arguments
    unnamed_params = []
    for arg in function_call.args:
        if isinstance(arg, ast.Name):
            unnamed_params.append(arg.id)
        elif isinstance(arg, ast.BinOp):
            # For binary operations, we can't just return a string identifier
            # We need to convert the expression back to a string
            # This is a simple way to do it, but it may not handle all cases
            expr_str = ast.unparse(arg)
            unnamed_params.append(expr_str)
        # Add more cases here if needed for other types of arguments

    # Handle named arguments
    named_params = [kw.arg for kw in function_call.keywords]

    return unnamed_params, named_params


def construct_dict(keys, values, assign_var = None): 
    
    module = ast.Module(body = [])
    dict_0 = ast.Dict(keys = [ast.Constant(s = str(key)) for key in keys], 
                      values = [handle_value(value) for value in values])
    if assign_var: 
        module.body.append(ast.Assign(targets = [ast.Name(id = assign_var, ctx = ast.Store())], value = dict_0))
    else: 
        module.body.append(ast.Expr(value = dict_0))

    return astor.to_source(module)


def handle_value(value):
    # print(value, type(value))
    if isinstance(value, list):
        print('List: ' + str(value))
        return ast.List(elts=[handle_value(v) for v in value], ctx=ast.Load())
    elif isinstance(value, tuple):
        return ast.Tuple(elts=[handle_value(v) for v in value], ctx=ast.Load())
    elif isinstance(value, ast.AST):
        return ast.Constant(value)
    elif isinstance(value, str): 
        print('Str value: ' + str(value))
        return ast.Constant(value)
    elif isinstance(value, int) or isinstance(value, float):
        return ast.Constant(n = value)
    elif isinstance(value, bool):
        return ast.Constant(value)
    elif value is None:
        return ast.Constant(value)
    else:
        raise ValueError("Unsupported type: {}".format(type(value)))

