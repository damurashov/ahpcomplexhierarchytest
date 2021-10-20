from ahpy.ahpy import ahpy
import itertools


def to_pairwise(*args):
	if len(args) == 2:
		alternatives = list(args[0])
		weights = list(args[1])
	elif len(args) == 1 and type(args[0]) is dict:
		alternatives = list(args[0].keys())
		weights = list(args[0].values())
	else:
		assert False

	n_alt = len(alternatives)
	assert n_alt == len(weights)

	ret = dict()

	for i in range(0, n_alt):
		for j in range(i + 1, n_alt):
			ret[(alternatives[i], alternatives[j],)] = weights[i] / weights[j]

	return ret


def inverse_weights_pairwise(pairwise):
	return dict(zip(pairwise.keys(), [1 / v for v in pairwise.values()]))


def test():
	target = ahpy.Compare('target', to_pairwise(['attack', 'harvest', 'run'], [3, 1, 3]))

	attack = ahpy.Compare('attack', to_pairwise(['strength', 'enemy strength^1', 'resource^1'], [1, 1, .5]))
	run = ahpy.Compare('run', to_pairwise(['strength^1', 'enemy strength', 'resource'], [1, 2, 1]))
	harvest = ahpy.Compare('harvest', to_pairwise(['strength', 'resource^1'], [1, 3]))

	strength_weights = to_pairwise(['s_attack', 's_hide'], [1.5, 1])
	strength = ahpy.Compare('strength', strength_weights)
	strength_inv = ahpy.Compare('strength^1', inverse_weights_pairwise(strength_weights))

	enemy_strength_weights = to_pairwise(['s_attack', 's_hide'], [.98, 1])
	enemy_strength = ahpy.Compare('enemy strength', enemy_strength_weights)
	enemy_strength_inv = ahpy.Compare('enemy strength^1', inverse_weights_pairwise(enemy_strength_weights))

	resource_weights = to_pairwise(['s_attack', 's_hide'], [1, 1])
	resource = ahpy.Compare('resource', resource_weights)
	resource_inv = ahpy.Compare('resource^1', inverse_weights_pairwise(resource_weights))

	harvest.add_children([strength, resource, enemy_strength, strength_inv, resource_inv, enemy_strength_inv])
	run.add_children([strength, resource, enemy_strength, strength_inv, resource_inv, enemy_strength_inv])
	attack.add_children([strength, resource, enemy_strength, strength_inv, resource_inv, enemy_strength_inv])
	# target.add_children([harvest, run, attack])

	attack.report(show=True)

	# target.add_children([attack, run, harvest])
	# target.add_children([strength, resource, enemy_strength, strength_inv, resource_inv, enemy_strength_inv], 'attack')
	# target.add_children([strength, resource, enemy_strength, strength_inv, resource_inv, enemy_strength_inv], 'run')
	# target.add_children([strength, resource, enemy_strength, strength_inv, resource_inv, enemy_strength_inv], 'harvest')

	target.report(show=True)


if __name__ == "__main__":

	f = 1

	criteria = ahpy.Compare('Criteria', to_pairwise(['Cost^1', 'Safety', 'Style', 'Capacity'], [3, 5, 3, 4]))
	cost = ahpy.Compare('Cost^1', to_pairwise(['Price^1', 'Fuel^1', 'Maintenance^1', 'Resale'], [2, 4, 6, .5]))
	cost_price = ahpy.Compare('Price^1', to_pairwise(['a', 'b'], [1, 2]), 3)
	cost_fuel = ahpy.Compare('Fuel^1', to_pairwise(['a', 'b'], [3, 2]), 3)
	cost_resale = ahpy.Compare('Resale', to_pairwise({'a': 1, 'b': 2}), 3)
	cost_maint = ahpy.Compare('Maintenance^1', to_pairwise(['a', 'b'], [3, 2]), 3)
	safety = ahpy.Compare('Safety', to_pairwise(['a', 'b'], [1, 2]), 3)
	style = ahpy.Compare('Style', to_pairwise(['a', 'b'], [1, 3]), 3)
	capacity = ahpy.Compare('Capacity', {('Cargo', 'Passenger'): 0.2})
	capacity_pass = ahpy.Compare('Passenger', to_pairwise(['a', 'b'], [1, 2]), 3)
	capacity_cargo = ahpy.Compare('Cargo', to_pairwise(['a', 'b'], [5, 2]), precision=3)

	if f:
		cost.add_children([cost_price, cost_fuel, cost_maint, cost_resale])
		capacity.add_children([capacity_cargo, capacity_pass])
		criteria.add_children([cost, safety, style, capacity])
	else:
		criteria.add_children([cost, safety, style, capacity])
		criteria.add_children([capacity_cargo, capacity_pass], 'Capacity')
		criteria.add_children([cost_price, cost_fuel, cost_maint, cost_resale], 'Cost^1')
		criteria._recompute()

	criteria.report(complete=False, show=True)

	print('='*100)
	criteria.update_weights(to_pairwise(['Cost^1', 'Safety', 'Style', 'Capacity'], [3, 5, 3, 1006]), 'Criteria')
	criteria.report(show=True)
	print('='*100)
	criteria.update_weights(to_pairwise(['Cost^1', 'Safety', 'Style', 'Capacity'], [3, 5, 3, 4]), 'Criteria')
	criteria.report(show=True)