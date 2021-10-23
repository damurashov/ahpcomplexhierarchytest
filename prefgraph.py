"""
This module performs AHP "convolutions". The reason it has been written is because ahpy doesn't seem to process non-tree
graphs correctly. Here is an example of a graph that this module operates on

{
	"c0" : {"c10": .3, "c11": .2, "c12": .5},
	"c10": {"c20": .5, "c21": .5},
	"c11": {"c21": .3, "c22": .7},
	"c12": {"c20": .4, "c22": .6},
	"c20": {"a1":..., "a2": ..., "a3": ...},
	"c21": {... leaves - the same},
	"c22": {... leaves - the same}
}

Formally, the graph has the following properties

0. The graph is oriented
1. There is exactly one vertex without a parent (the root)
2. There are vertices without children (alternatives, "leaves")
3. For every vertex of the graph, there exists a path to any of the alternatives (so we can assess alternatives in the context of the root)
4. For every 2 edges (a, X1), (a, X2), there are no paths between X1 and X2 (so we can divide the graph into "levels")

However, the implementation does not offer any facilities to check whether or not the structure of a given graph
satisfies the requirements. Therefore, in cases when it's not the BEHAVIOR IS UNDEFINED
"""

from functools import reduce
from ahpy.ahpy import ahpy
import copy
import itertools


class Graph:

	@staticmethod
	def to_pairwise(*args):
		"""
		From plain non-normalized weight vectors to pairwise comparisons
		:param args: ["a","b", "c"], [33, 44, 66]  OR  {"a": 33, "b": 44, "c": 66}
		:return: {("a", "b"): a / b, ("a","c"): a / c, ("b","c"): b / c}
		"""
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

	@staticmethod
	def _pair_format(pair: tuple):
		vert_a, vert_b = pair

		if vert_a > vert_b:
			return vert_a, vert_b
		else:
			return vert_b, vert_a

	@staticmethod
	def _key_format(pairwise):
		formatted = dict()

		# Order vertices in alphabetical order
		for k, val in zip(pairwise.keys(), pairwise.values()):
			k_ord = Graph._pair_format(k)
			val = val if k == k_ord else 1 / val
			formatted[k_ord] = val

		return formatted

	def __init__(self, root_name):
		self.graph = dict()
		self.root = root_name

	def set_weights(self, context, pairwise):
		"""
		Used for both update
		:param context: name of the vertex which the weights will be attached to
		:param pairwise: {("a","b"): a pref. over b, ("b","c"): b pref. over c, ...}
		"""
		# self.graph[context].update(Graph._key_format(pairwise))
		if context in self.graph.keys():
			self.graph[context].update(pairwise)
		else:
			self.graph[context] = pairwise

	def get_children_of(self, node_name) -> set:
		"""
		:return: Names of the vertex's children
		"""
		if node_name in self.graph:
			return set(reduce(lambda a, b: a + b, self.graph[node_name].keys(), ()))
		else:
			return []

	def __str__(self):
		print(self.graph)

	def _get_weights(self, context, assessed: dict = dict()) -> dict:
		"""
		Recursive call for "convolving" the alternatives up to the given context
		:param context: name of the vertex
		:param assessed: The nodes in the context of which the leaves have been assessed by the moment.
		Format: {context1: {alt1: weight, alt2: weight}, context2: {...}}
		:return: dict of assessed vertices (extended).
		"""

		def __trace(s):
			pass

		__trace('--->> ' + context)
		children = self.get_children_of(context)
		__trace("children: " + str(children))

		if not children:
			__trace('<<--- ' + context)
			return assessed

		for child in children:
			if not (child in assessed.keys()):
				assessed = self._get_weights(child, assessed)

		compare = ahpy.Compare(context, self.graph[context])
		lower_contexts = [ahpy.Compare(child, Graph.to_pairwise(assessed[child])) for child in children if child in assessed.keys()]

		__trace("lower contexts: " + str(lower_contexts))

		if lower_contexts:
			compare.add_children(lower_contexts)

		assessed[context] = compare.target_weights

		__trace('<<---' + context)
		return assessed

	def get_weights(self):
		"""
		:return: Returns weighted alternatives in the form {"a1": weight_a1, "a2": weight_a2,...}
		"""
		return self._get_weights(self.root)[self.root]


def ahpy_simple():
	experience_comparisons = {('Moll', 'Nell'): 1 / 4, ('Moll', 'Sue'): 4, ('Nell', 'Sue'): 9}
	education_comparisons = {('Moll', 'Nell'): 3, ('Moll', 'Sue'): 1 / 5, ('Nell', 'Sue'): 1 / 7}
	charisma_comparisons = {('Moll', 'Nell'): 5, ('Moll', 'Sue'): 9, ('Nell', 'Sue'): 4}
	age_comparisons = {('Moll', 'Nell'): 1 / 3, ('Moll', 'Sue'): 5, ('Nell', 'Sue'): 9}
	criteria_comparisons = {('Experience', 'Education'): 4, ('Experience', 'Charisma'): 3, ('Experience', 'Age'): 7,
							('Education', 'Charisma'): 1 / 3, ('Education', 'Age'): 3,
							('Charisma', 'Age'): 5}

	experience = ahpy.Compare('Experience', experience_comparisons, precision=3, random_index='saaty')
	education = ahpy.Compare('Education', education_comparisons, precision=3, random_index='saaty')
	charisma = ahpy.Compare('Charisma', charisma_comparisons, precision=3, random_index='saaty')
	age = ahpy.Compare('Age', age_comparisons, precision=3, random_index='saaty')
	criteria = ahpy.Compare('Criteria', criteria_comparisons, precision=3, random_index='saaty')

	criteria.add_children([experience, education, charisma, age])

	print(criteria.target_weights)


def graph_simple():
	graph = Graph("Criteria")
	graph.set_weights("Experience", {('Moll', 'Nell'): 1 / 4, ('Moll', 'Sue'): 4, ('Nell', 'Sue'): 9})
	graph.set_weights("Education", {('Moll', 'Nell'): 3, ('Moll', 'Sue'): 1 / 5, ('Nell', 'Sue'): 1 / 7})
	graph.set_weights("Charisma", {('Moll', 'Nell'): 5, ('Moll', 'Sue'): 9, ('Nell', 'Sue'): 4})
	graph.set_weights("Age", {('Moll', 'Nell'): 1 / 3, ('Moll', 'Sue'): 5, ('Nell', 'Sue'): 9})
	graph.set_weights("Criteria", {('Experience', 'Education'): 4, ('Experience', 'Charisma'): 3,
								   ('Experience', 'Age'): 7, ('Education', 'Charisma'): 1 / 3, ('Education', 'Age'): 3,
								   ('Charisma', 'Age'): 5})

	print(graph.get_weights())


def ahpy_complex():
	def m(elements, judgments):
		return dict(zip(elements, judgments))

	cri = ('Cost', 'Safety', 'Style', 'Capacity')
	c_cri = list(itertools.combinations(cri, 2))
	criteria = ahpy.Compare('Criteria', m(c_cri, (3, 7, 3, 9, 1, 1 / 7)), 3)

	alt = ('Accord Sedan', 'Accord Hybrid', 'Pilot', 'CR-V', 'Element', 'Odyssey')
	pairs = list(itertools.combinations(alt, 2))

	costs = ('Price', 'Fuel', 'Maintenance', 'Resale')
	c_pairs = list(itertools.combinations(costs, 2))
	cost = ahpy.Compare('Cost', m(c_pairs, (2, 5, 3, 2, 2, .5)), precision=3)

	cost_price_m = (9, 9, 1, 0.5, 5, 1, 1 / 9, 1 / 9, 1 / 7, 1 / 9, 1 / 9, 1 / 7, 1 / 2, 5, 6)
	cost_price = ahpy.Compare('Price', m(pairs, cost_price_m), 3)

	# cost_fuel_m = (1/1.13, 1.41, 1.15, 1.24, 1.19, 1.59, 1.3, 1.4, 1.35, 1/1.23, 1/1.14, 1/1.18, 1.08, 1.04, 1/1.04)
	cost_fuel_m = (31, 35, 22, 27, 25, 26)
	# cost_fuel = ahpy.Compare('Fuel', m(pairs, cost_fuel_m), 3)
	cost_fuel = ahpy.Compare('Fuel', m(alt, cost_fuel_m), 3)

	# cost_resale_m = (3, 4, 1 / 2, 2, 2, 2, 1 / 5, 1, 1, 1 / 6, 1 / 2, 1 / 2, 4, 4, 1)
	cost_resale_m = (0.52, 0.46, 0.44, 0.55, 0.48, 0.48)
	# cost_resale = ahpy.Compare('Resale', m(pairs, cost_resale_m), 3)
	cost_resale = ahpy.Compare('Resale', m(alt, cost_resale_m), 3)

	cost_maint_m = (1.5, 4, 4, 4, 5, 4, 4, 4, 5, 1, 1.2, 1, 1, 3, 2)
	cost_maint = ahpy.Compare('Maintenance', m(pairs, cost_maint_m), 3)

	safety_m = (1, 5, 7, 9, 1 / 3, 5, 7, 9, 1 / 3, 2, 9, 1 / 8, 2, 1 / 8, 1 / 9)
	safety = ahpy.Compare('Safety', m(pairs, safety_m), 3)

	style_m = (1, 7, 5, 9, 6, 7, 5, 9, 6, 1 / 6, 3, 1 / 3, 7, 5, 1 / 5)
	style = ahpy.Compare('Style', m(pairs, style_m), 3)

	capacity = ahpy.Compare('Capacity', {('Cargo', 'Passenger'): 0.2})

	# capacity_pass_m = (1, 1 / 2, 1, 3, 1 / 2, 1 / 2, 1, 3, 1 / 2, 2, 6, 1, 3, 1 / 2, 1 / 6)
	capacity_pass_m = (5, 5, 8, 5, 4, 8)
	# capacity_pass = ahpy.Compare('Passenger', m(pairs, capacity_pass_m), 3)
	capacity_pass = ahpy.Compare('Passenger', m(alt, capacity_pass_m), 3)

	# capacity_cargo_m = (1, 1 / 2, 1 / 2, 1 / 2, 1 / 3, 1 / 2, 1 / 2, 1 / 2, 1 / 3, 1, 1, 1 / 2, 1, 1 / 2, 1 / 2)
	capacity_cargo_m = (14, 14, 87.6, 72.9, 74.6, 147.4)
	# capacity_cargo = ahpy.Compare('Cargo', m(pairs, capacity_cargo_m), precision=3)
	capacity_cargo = ahpy.Compare('Cargo', m(alt, capacity_cargo_m), precision=3)

	cost.add_children([cost_price, cost_fuel, cost_maint, cost_resale])
	capacity.add_children([capacity_cargo, capacity_pass])
	criteria.add_children([cost, safety, style, capacity])

	print(criteria.target_weights)


def graph_complex():
	def m(elements, judgments):
		return dict(zip(elements, judgments))

	cri = ('Cost', 'Safety', 'Style', 'Capacity')
	c_cri = list(itertools.combinations(cri, 2))
	criteria = m(c_cri, (3, 7, 3, 9, 1, 1 / 7))

	alt = ('Accord Sedan', 'Accord Hybrid', 'Pilot', 'CR-V', 'Element', 'Odyssey')
	pairs = list(itertools.combinations(alt, 2))

	costs = ('Price', 'Fuel', 'Maintenance', 'Resale')
	c_pairs = list(itertools.combinations(costs, 2))
	cost = m(c_pairs, (2, 5, 3, 2, 2, .5))

	cost_price_m = (9, 9, 1, 0.5, 5, 1, 1 / 9, 1 / 9, 1 / 7, 1 / 9, 1 / 9, 1 / 7, 1 / 2, 5, 6)
	cost_price = m(pairs, cost_price_m)

	cost_fuel_m = (31, 35, 22, 27, 25, 26)
	cost_fuel = Graph.to_pairwise(m(alt, cost_fuel_m))

	cost_resale_m = (0.52, 0.46, 0.44, 0.55, 0.48, 0.48)
	cost_resale = m(alt, cost_resale_m)
	cost_resale = Graph.to_pairwise(cost_resale)

	cost_maint_m = (1.5, 4, 4, 4, 5, 4, 4, 4, 5, 1, 1.2, 1, 1, 3, 2)
	cost_maint = m(pairs, cost_maint_m)

	safety_m = (1, 5, 7, 9, 1 / 3, 5, 7, 9, 1 / 3, 2, 9, 1 / 8, 2, 1 / 8, 1 / 9)
	safety = m(pairs, safety_m)

	style_m = (1, 7, 5, 9, 6, 7, 5, 9, 6, 1 / 6, 3, 1 / 3, 7, 5, 1 / 5)
	style = m(pairs, style_m)

	capacity = {('Cargo', 'Passenger'): 0.2}

	capacity_pass_m = (5, 5, 8, 5, 4, 8)
	capacity_pass = Graph.to_pairwise(m(alt, capacity_pass_m))

	capacity_cargo_m = (14, 14, 87.6, 72.9, 74.6, 147.4)
	capacity_cargo = Graph.to_pairwise(m(alt, capacity_cargo_m))

	graph = Graph("Criteria")
	graph.set_weights("Criteria", criteria)
	graph.set_weights("Cost", cost)
	graph.set_weights("Price", cost_price)
	graph.set_weights("Fuel", cost_fuel)
	graph.set_weights("Resale", cost_resale)
	graph.set_weights("Maintenance", cost_maint)
	graph.set_weights("Safety", safety)
	graph.set_weights("Style", style)
	graph.set_weights("Capacity", capacity)
	graph.set_weights("Passenger", capacity_pass)
	graph.set_weights("Cargo", capacity_cargo)

	print(graph.get_weights())


if __name__ == "__main__":
	# ahpy_simple()
	# graph_simple()
	ahpy_complex()
	graph_complex()