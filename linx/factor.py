"""
Factor class
"""
import numpy as np

from .errors import ArgumentError
from .log_factor import LogFactor


class Factor:
    """
    Class for representing factors.
    """
    def __init__(self, df=None, cpt=None, log_factor=None):
        if log_factor is not None and df is not None:
            raise ArgumentError(
                "Factor must be supplied with only one of"
                + " dataframe, ConditionalProbabilityTable, or LogFactor."
            )
        if cpt is not None and df is not None:
            raise ArgumentError(
                "Factor must be supplied with only one of"
                + " dataframe, ConditionalProbabilityTable, or LogFactor"
            )

        if df is not None:
            self.df = df.copy()
            self.df['value'] = np.log(self.df['value'])
            self.log_factor = LogFactor(df=self.df)

        elif cpt is not None:
            self.df = cpt.df.copy()
            self.df['value'] = np.log(self.df['value'])
            self.log_factor = LogFactor(df=self.df)

        else:
            self.log_factor = log_factor

    def __repr__(self):
        return f"\nFactor(\nvariables: {self.get_variables()}" \
            + f", \nlog_factor: \n{self.log_factor}\n)"

    def get_variables(self):
        """
        Return variables
        """
        return self.log_factor.get_variables()

    def div(self, other):
        """
        Parameters:
            other: Factor

        Returns: Factor
        """

        return Factor(
            log_factor=self.log_factor.subtract(other.log_factor),
        )

    def filter(self, query):
        """
        Apply filters of a query to this factor.

        Parameters:
            query: Query
                Implements get_filters. Each item is a dict.
                key: string
                    Name of the variable.
                value: callable or string or float or integer
                    We use this for filtering.

        Returns: Factor
        """
        return Factor(log_factor=self.log_factor.filter(query))

    def prod(self, other):
        """
        Parameters:
            other: Factor

        Returns: Factor
        """

        return Factor(
            log_factor=self.log_factor.add(other.log_factor)
        )

    def sum(self, var):
        """
        Parameters:
            var: string
                The variable to be summed out.

        Returns: Factor
        """

        return Factor(log_factor=self.log_factor.sum(var))

    def normalize(self, variables):
        """
        Make sure the values represent probabilities.

        Parameters:
            variables: list[str]
                The variables in the denominator.

        Returns: Factor
        """

        return self.div(
            Factor(
                log_factor=self.log_factor.sum(variables)
            )
        )

    def get_df(self):
        """
        Exponentiates the LogFactor values.

        Returns: pd.DataFrame
        """

        df = self.log_factor.df.copy()
        df['value'] = np.exp(df['value'])
        return df
