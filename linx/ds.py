"""
Data Structures module.

Classes:
    - ConditionalProbabilityTable
    - DirectedAcyclicGraph
    - Factor
    - Factors
    - BayesianNetwork
    - MarkovNetwork
"""


class ConditionalProbabilityTable:
    """
    Conditional Probability Table class. Meant to be used to represent
    conditional probabilities for Bayesian Networks.
    """

    # pylint:disable=too-few-public-methods
    def __init__(self, df, outcomes, givens=None):
        self.df = df

        if givens is None:
            givens = []

        self.givens = givens
        self.outcomes = outcomes

        self.__validate__()

    def __validate__(self):
        existing_cols = self.df.reset_index().columns

        if 'count' not in existing_cols:
            raise ValueError("The column 'count' must exist.")

        given_plus_outcomes_cols = set(self.givens + self.outcomes)

        if given_plus_outcomes_cols.intersection(
            set(existing_cols) - {'count'}
        ) != given_plus_outcomes_cols:

            raise ValueError(
                "Mismatch between dataframe columns {existing_cols} and"
                + " given and outcomes {given_plus_outcomes_cols}"
            )

    def get_givens(self):
        """
        Returns list[str]
            List of variable names that are being conditioned on.
        """
        return self.givens

    def get_outcomes(self):
        """
        Returns list[str]
            List of variable names in the left side of the query.
        """
        return self.outcomes


class DirectedAcyclicGraph:
    """
    Directed Acyclic Graph. Useful for representing Bayesian Networks.
    """
    def __init__(self):
        self.children = {}
        self.nodes = {}

    def add_edge(self, start, end):
        """
        Add edge from start node to end node.

        Parameters:
            start: str
                Start node.
            end: str
                End node.
        """

        if start not in self.children:
            self.children[start] = [end]
        elif end not in self.children[start]:
            self.children[start].append(end)

    def add_node(self, node):
        """
        Add edge from start node to end node.

        Parameters:
            node: str
                Node to add.
        """

        if node not in self.nodes:
            self.nodes[node] = 1

    def get_neighbors(self, node):
        """
        Parameters:
            node: str

        Returns: list[str]
        """

        return self.get_parents(node) + self.get_children(node)

    def get_parents(self, node):
        """
        Parameters:
            node: str

        Returns: list[str]
        """
        parents = []

        for other_node, children in self.children.items():
            if node in children:
                parents.append(other_node)

        return parents

    def get_children(self, node):
        """
        Parameters:
            node: str

        Returns: list[str]
        """

        if node not in self.children:
            return []

        return self.children[node]


class Factor:
    """
    Class for representing factors.
    """
    def __init__(self, df=None, cpt=None):
        if df is not None:
            self.df = df.copy()
        else:
            self.df = cpt.df.copy()

    def __repr__(self):
        return f"Factor({self.get_variables()})"

    def get_variables(self):
        """
        Return variables
        """
        return list(set(self.df.columns) - {'count'})

    def div(self, other):
        """
        Parameters:
            other: Factor

        Returns: Factor
        """

        left_vars = set(list(self.get_variables()))
        right_vars = set(list(other.get_variables()))
        common = list(
            left_vars.intersection(right_vars)
        )

        merged = self.df.merge(other.df, on=common)
        merged['count'] = merged.count_x / merged.count_y

        return Factor(
            merged[
                list(left_vars.union(right_vars.union({'count'})))
            ]
        )

    def prod(self, other):
        """
        Parameters:
            other: Factor

        Returns: Factor
        """

        left_vars = set(list(self.get_variables()))
        right_vars = set(list(other.get_variables()))
        common = list(
            left_vars.intersection(right_vars)
        )

        merged = self.df.merge(other.df, on=common)
        merged['count'] = merged.count_x * merged.count_y

        return Factor(
            merged[
                list(left_vars.union(right_vars.union({'count'})))
            ]
        )

    def sum(self, var):
        """
        Parameters:
            var: string
                The variable to be summed out.

        Returns: Factor
        """

        other_vars = list(set(self.get_variables()) - {'count', var})
        new_df = self.df.groupby(other_vars)\
            .sum()[['count']].reset_index()

        return Factor(new_df)


class Factors():
    """
    Helper for doing a bunch of operations on Factors.

    Parameters:
        factors: list[Factor]
    """

    def __init__(self, factors):
        self.factors = factors

    def prod(self):
        """
        Multiply set of factors
        """
        factor_prod = None

        for factor in self.factors:
            if factor_prod is None:
                factor_prod = factor
            else:
                factor_prod = factor_prod.prod(factor)

        return factor_prod


class BayesianNetwork(DirectedAcyclicGraph):
    """
    Bayesian Network that stores ConditionalProbabilityTables.
    """

    def __init__(self):
        self.cpts = {}
        super().__init__()

    def add_node(self, cpt):
        """
        Add a conditional probability table. This adds a node.

        Parameters:
            cpt: ConditionalProbabilityTable
        """
        outcomes = cpt.get_outcomes()
        if cpt.get_givens():
            raise ValueError(
                "There should not be any givens for the CPT when adding a"
                + " node."
            )

        if len(outcomes) != 1:
            raise ValueError(
                "There should only be one outcome for a CPT of a "
                + "Bayesian Network."
            )

        for outcome in outcomes:
            self.cpts[outcome] = cpt

            super().add_node(outcome)

    def add_edge(self, cpt):
        """
        Add a conditional probability table. This in turn adds an edge.

        Parameters:
            cpt: ConditionalProbabilityTable
        """
        outcomes = cpt.get_outcomes()
        givens = cpt.get_givens()

        if len(outcomes) != 1:
            raise ValueError(
                "There should only be one outcome for a CPT of a "
                + "Bayesian Network."
            )

        for outcome in outcomes:
            self.cpts[outcome] = cpt

            for given in givens:
                super().add_edge(start=given, end=outcome)

    def find_cpt_for_node(self, node):
        """
        Find conditional probability table for node.

        Parameters:
            node: str

        Returns: ConditionalProbabilityTable
        """

        return self.cpts[node]


class MarkovNetwork:
    """
    Markov network. A data structure that has undirected edges. Each clique
    represents a factor.
    """
    def __init__(self):
        self.factors = {}

    def add_factor(self, factor):
        """
        Add factor.

        Parameters:
            factor: Factor
                Something that responds to get_variables.
        """
        variables = factor.get_variables()
        for var in variables:
            if var not in self.factors:
                self.factors[var] = []
            self.factors[var].append(factor)

    def get_factors(self, node=None):
        """
        If node is None, returns all factors.

        Parameters:
            node: string or None

        Returns: list[Factor]
        """
        if node is None:
            factors = []
            for _, v in self.factors.items():
                factors = factors + v

            return factors
        else:
            return self.factors[node]

    def get_variables(self):
        """
        Get all the variables

        Returns: list[string]
        """

        return list(self.factors.keys())
