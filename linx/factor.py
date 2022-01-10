"""
Factor class
"""
import numpy as np

from .data import ParquetData
from .errors import ArgumentError
from .log_factor import LogFactor
from .factor_one import FactorOne


class Factor:
    """
    Class for representing factors.
    """
    def __init__(self, data=None, cpt=None, log_factor=None):
        if log_factor is not None and data is not None:
            raise ArgumentError(
                "Factor must be supplied with only one of"
                + " Data, ConditionalProbabilityTable, or LogFactor."
            )
        if cpt is not None and data is not None:
            raise ArgumentError(
                "Factor must be supplied with only one of"
                + " Data, ConditionalProbabilityTable, or LogFactor"
            )

        if data is not None:
            df = data.read()
            df['value'] = np.log(df['value'])

            self.log_factor = LogFactor(
                data=ParquetData(df, data.storage_folder)
            )

        elif cpt is not None:
            data = cpt.data

            df = data.read()
            df['value'] = np.log(df['value'])

            self.log_factor = LogFactor(
                data=ParquetData(df, data.storage_folder)
            )

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

        summation = self.log_factor.add(other.log_factor)
        factor = Factor(
            log_factor=summation
        )
        return factor

    def sum(self, var):
        """
        Get the other variables besides the one being passed in. Group by those
        variables. Take the sum.

        Parameters:
            var: string
                The variable to be summed out.

        Returns: Factor
        """

        if isinstance(var, str):
            variables = [var]

        df = self.get_df()

        other_vars = list(
            set(self.get_variables()) - set(variables)
        )

        if not other_vars:
            return FactorOne()
        return_df = df.groupby(other_vars).sum()[['value']].reset_index()

        return Factor(
            data=ParquetData(
                return_df,
                storage_folder=self.log_factor.get_data().get_storage_folder()
            )
        )

    def normalize(self, variables=None):
        """
        Make sure the values represent probabilities.

        Parameters:
            variables: list[str]
                The variables in the denominator.

        Returns: Factor
        """

        df = self.get_df()

        if not variables:
            df['value'] = df['value'] / df['value'].sum()

            return Factor(
                data=ParquetData(
                    df,
                    storage_folder=self
                    .log_factor.get_data().get_storage_folder()
                )
            )

        sum_df = df.groupby(variables)[['value']].sum()
        merged = df.merge(sum_df, on=variables)
        merged['value'] = merged['value_x'] / merged['value_y']

        return Factor(
            data=ParquetData(
                merged.drop(columns=['value_x', 'value_y']),
                storage_folder=self.log_factor.get_data().get_storage_folder()
            )
        )

    def get_df(self):
        """
        Exponentiates the LogFactor values.

        Returns: pd.DataFrame
        """

        df = self.log_factor.data.read()
        df['value'] = np.exp(df['value'])
        return df
