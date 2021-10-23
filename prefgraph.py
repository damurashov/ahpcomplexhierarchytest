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
		print('--->> ' + context)
		children = self.get_children_of(context)
		print("children: " + str(children))

		if not children:
			print('<<---')
			return assessed

		for child in children:
			if not (child in assessed.keys()):
				assessed = self._get_weights(child, assessed)

		compare = ahpy.Compare(context, self.graph[context])
		lower_contexts = [ahpy.Compare(child, Graph.to_pairwise(assessed[child])) for child in children if child in assessed.keys()]

		print("lower contexts: " + str(lower_contexts))

		if lower_contexts:
			compare.add_children(lower_contexts)

		assessed[context] = compare.target_weights

		print('<<---')
		return assessed

	def get_weights(self):
		"""
		:return: Returns weighted alternatives in the form {"a1": weight_a1, "a2": weight_a2,...}
		"""
		return self._get_weights(self.root)[self.root]


if __name__ == "__main__":
	graph = Graph("target")
	graph.set_weights("target", Graph.to_pairwise({"b1": 1, "b2": 3, "b3": 4}))
	graph.set_weights("b1", Graph.to_pairwise({"c1": 30, "c2": 50}))
	graph.set_weights("b2", Graph.to_pairwise({"c2": 30, "c3": 50}))
	graph.set_weights("b3", Graph.to_pairwise({"c1": 10, "c3": 100}))

	graph_copy = copy.deepcopy(graph)
	graph_copy.set_weights("c1", Graph.to_pairwise({"Alternative 1": 10, "Alternative 2": 20}))
	graph_copy.set_weights("c2", Graph.to_pairwise({"Alternative 1": 10, "Alternative 2": 1}))
	graph_copy.set_weights("c3", Graph.to_pairwise({"Alternative 1": 10, "Alternative 2": 3}))

	print(graph.graph)
	print(graph_copy.graph)

	print(graph_copy.get_weights())
