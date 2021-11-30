import pandas as pd

from ..linx.ds import Factors, Factor


def test_looping():
    df1 = pd.DataFrame([
        {
            'X': 0, 'count': 123,
        },
        {
            'X': 1, 'count': 123,
        }
    ])

    df2 = pd.DataFrame([
        {
            'Y': 0, 'count': 123,
        },
        {
            'Y': 1, 'count': 123,
        }
    ])

    factor_1 = Factor(df=df1)
    factor_2 = Factor(df=df2)

    expected_factors = [
        factor_1,
        factor_2
    ]

    factors = Factors([factor_1, factor_2])

    for i, factor in enumerate(factors):
        assert factor == expected_factors[i]