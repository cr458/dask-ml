import dask
import dask.array as da
import dask.dataframe as dd
import pytest
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.decomposition import PCA
from sklearn.linear_model import LinearRegression, LogisticRegression

from dask_ml.utils import assert_estimator_equal, assert_eq_ar
from dask_ml.wrappers import ParallelPostFit
from dask_ml.datasets import make_classification


def test_it_works():
    clf = ParallelPostFit(GradientBoostingClassifier())

    X, y = make_classification(n_samples=1000, chunks=100)
    clf.fit(X, y)

    assert isinstance(clf.predict(X), da.Array)
    assert isinstance(clf.predict_proba(X), da.Array)


def test_no_method_raises():
    clf = ParallelPostFit(LinearRegression())
    X, y = make_classification(chunks=50)
    clf.fit(X, y)

    with pytest.raises(AttributeError) as m:
        clf.predict_proba(X)

    assert m.match("The wrapped estimator .* 'predict_proba' method.")


@pytest.mark.parametrize('kind', ['numpy', 'dask.dataframe', 'dask.array'])
def test_predict(kind):
    X, y = make_classification(chunks=100)

    if kind == 'numpy':
        X, y = dask.compute(X, y)
    elif kind == 'dask.dataframe':
        X = dd.from_dask_array(X)
        y = dd.from_dask_array(y)

    base = LogisticRegression(random_state=0)
    wrap = ParallelPostFit(LogisticRegression(random_state=0))

    base.fit(X, y)
    wrap.fit(X, y)

    assert_estimator_equal(wrap.estimator, base)

    result = wrap.predict(X)
    expected = base.predict(X)
    assert_eq_ar(result, expected)

    result = wrap.predict_proba(X)
    expected = base.predict_proba(X)
    assert_eq_ar(result, expected)


@pytest.mark.parametrize('kind', ['numpy', 'dask.dataframe', 'dask.array'])
def test_transform(kind):
    X, y = make_classification(chunks=100)

    if kind == 'numpy':
        X, y = dask.compute(X, y)
    elif kind == 'dask.dataframe':
        X = dd.from_dask_array(X)
        y = dd.from_dask_array(y)

    base = PCA(random_state=0)
    wrap = ParallelPostFit(PCA(random_state=0))

    base.fit(X, y)
    wrap.fit(X, y)

    assert_estimator_equal(wrap.estimator, base)

    result = base.transform(X)
    expected = wrap.transform(X)
    assert_eq_ar(result, expected)


def test_multiclass():
    X, y = make_classification(chunks=50, n_classes=3, n_informative=4)
    clf = ParallelPostFit(LogisticRegression(random_state=0))

    clf.fit(X, y)
    result = clf.predict(X)
    expected = clf.estimator.predict(X)

    assert isinstance(result, da.Array)
    assert_eq_ar(result, expected)

    result = clf.predict_proba(X)
    expected = clf.estimator.predict_proba(X)

    assert isinstance(result, da.Array)
    assert_eq_ar(result, expected)
