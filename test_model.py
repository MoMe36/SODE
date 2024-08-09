import matplotlib.pyplot as plt 
import numpy as np 
from scipy.integrate import odeint 
import sode_utils

def SD(x,t, args): 

    # CONSTANTS
    initial_deer_density = args['constants']['initial_deer_density']
    food_volume = args['constants']['food_volume']
    area_size = args['constants']['area_size']
    initial_food_per_deer = args['constants']['initial_food_per_deer']
    
    
    # STOCKS
    deer_population = x[0]
    
    
    # DYNAMICS
    predator_population = sode_utils.step_after_time(t, func_id='step_after_time_predatorpopulation')
    average_number_of_deer_killed_by_a_given_predator = sode_utils.piecewise_linear(deer_population / area_size / initial_deer_density, func_id='piecewise_linear_averagenumberofdeerkilledbyagi')
    food_per_deer = food_volume / deer_population
    growth_rate_factor = sode_utils.piecewise_linear(food_per_deer / initial_food_per_deer, func_id='piecewise_linear_growthratefactor')
    net_growth_rate = growth_rate_factor * deer_population
    predation_rate = predator_population * average_number_of_deer_killed_by_a_given_predator
    
    
    return net_growth_rate - predation_rate 



# INIT

t = np.linspace(0, 10, 10) # Unit: year # Extraction method: best_guess_time_horizon
deer_population = 5000.0 # Using model implicit knowledge
x = [deer_population]

# SIM
# result = odeint(SD, x, t, args = (None, ))
result = odeint(SD, x, t,
    args = ({'constants': {'initial_deer_density': 0.005, 'food_volume': 100000, 'area_size': 1000000,
    'initial_food_per_deer': 20}
}, )
    )


# PLOT 

sode_utils.simple_plot(result, t)