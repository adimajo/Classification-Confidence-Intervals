#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""AUTHOR: KENNETH CHEN.

Unit tests for classification_confidence_intervals.py.

"""


from conftest import (
    valid_cl,
    valid_ep,
    valid_pfc,
    valid_ps,
    valid_sl,
    valid_sp,
)
import pytest
from sklearn import datasets
import numpy as np
from sklearn.utils.validation import check_random_state
from sklearn import svm
from sklearn.preprocessing import LabelEncoder, OneHotEncoder

from classificationconfidenceintervals import ClassificationConfidenceIntervals


def make_prediction(dataset=None, binary=False):
    """Make some classification predictions on a toy dataset using a SVC

    If binary is True restrict to a binary classification problem instead of a
    multiclass classification problem
    """

    if dataset is None:
        # import some data to play with
        dataset = datasets.load_iris()

    X = dataset.data
    y = dataset.target

    if binary:
        # restrict to a binary classification task
        X, y = X[y < 2], y[y < 2]

    n_samples, n_features = X.shape
    p = np.arange(n_samples)

    rng = check_random_state(37)
    rng.shuffle(p)
    X, y = X[p], y[p]
    half = int(n_samples / 2)

    # add noisy features to make the problem harder and avoid perfect results
    rng = np.random.RandomState(0)
    X = np.c_[X, rng.randn(n_samples, 200 * n_features)]

    # run classifier, get class probabilities and label predictions
    clf = svm.SVC(kernel='linear', probability=True, random_state=0)
    probas_pred = clf.fit(X[:half], y[:half]).predict_proba(X[half:])

    if binary:
        # only interested in probabilities of the positive case
        # XXX: do we really want a special API for the binary case?
        probas_pred = probas_pred[:, 1]

    y_pred = clf.predict(X[half:])
    y_true = y[half:]
    return y_true, y_pred, probas_pred


def test_iris():
    iris = datasets.load_iris()
    y_true, y_pred, _ = make_prediction(dataset=iris, binary=False)
    le = LabelEncoder()
    le.fit(np.unique(y_true))
    y_true = le.transform(y_true)
    y_pred = le.transform(y_pred)
    enc = OneHotEncoder()
    y_true_matrix = enc.fit_transform(y_true.reshape(-1, 1)).toarray()
    y_pred_matrix = enc.transform(y_pred.reshape(-1, 1)).toarray()
    pos_rate_cis, ppv_cis, npv_cis, recall_cis = [], [], [], []
    ci = 0.95
    for j in range(y_true_matrix.shape[1]):
        class_ci = ClassificationConfidenceIntervals(
            sample_labels=y_true_matrix[:, j],
            sample_predictions=y_pred_matrix[:, j],
            population_size=1000000,
            population_flagged_count=50000,
            confidence_level=ci).get_cis()
        pos_rate_cis.append(class_ci[0].tnorm_ci)
        ppv_cis.append(class_ci[1].tnorm_ci)
        npv_cis.append(class_ci[2].tnorm_ci)
        recall_cis.append(class_ci[3].tnorm_ci)


@pytest.mark.parametrize(
    "sample_labels, sample_predictions, population_size, "
    "population_flagged_count, confidence_level, exact_precision",
    [
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, None),
    ],
)
def test_init(
    sample_labels,
    sample_predictions,
    population_size,
    population_flagged_count,
    confidence_level,
    exact_precision,
):
    """Unit test for __init__ method in ClassificationConfidenceIntervals class."""
    ClassificationConfidenceIntervals(
        sample_labels=sample_labels,
        sample_predictions=sample_predictions,
        population_size=population_size,
        population_flagged_count=population_flagged_count,
        confidence_level=confidence_level,
        exact_precision=exact_precision,
    )


@pytest.mark.parametrize(
    "sample_labels, sample_predictions, population_size, "
    "population_flagged_count, confidence_level, exact_precision",
    [
        ([], valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep),
        (None, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep),
        ("string", valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep),
        (-100, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep),
        ({0: 400, 1: 400}, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep),
        (valid_sl, [], valid_ps, valid_pfc, valid_cl, valid_ep),
        (valid_sl, None, valid_ps, valid_pfc, valid_cl, valid_ep),
        (valid_sl, "string", valid_ps, valid_pfc, valid_cl, valid_ep),
        (valid_sl, -100, valid_ps, valid_pfc, valid_cl, valid_ep),
        (valid_sl, {0: 400, 1: 400}, valid_ps, valid_pfc, valid_cl, valid_ep),
        (valid_sl[:-5], valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep),
        (valid_sl, valid_sp[:-5], valid_ps, valid_pfc, valid_cl, valid_ep),
        ([1, 2, 3, 4], [1, 2, 3, 4], valid_ps, valid_pfc, valid_cl, valid_ep),
        ([1, [1], 0, 0], [1, [1], 0, 0], valid_ps, valid_pfc, valid_cl, valid_ep),
        ([1, 1, 0, 0], [1, 1, 0, 0], valid_ps, valid_pfc, valid_cl, valid_ep),
        ([1, 1, 0, 0], [0, 0, 1, 1], valid_ps, valid_pfc, valid_cl, valid_ep),
        (valid_sl, valid_sp, [], valid_pfc, valid_cl, valid_ep),
        (valid_sl, valid_sp, None, valid_pfc, valid_cl, valid_ep),
        (valid_sl, valid_sp, "string", valid_pfc, valid_cl, valid_ep),
        (valid_sl, valid_sp, -100, valid_pfc, valid_cl, valid_ep),
        (valid_sl, valid_sp, {0: 400, 1: 400}, valid_pfc, valid_cl, valid_ep),
        (valid_sl, valid_sp, valid_ps, [], valid_cl, valid_ep),
        (valid_sl, valid_sp, valid_ps, None, valid_cl, valid_ep),
        (valid_sl, valid_sp, valid_ps, "string", valid_cl, valid_ep),
        (valid_sl, valid_sp, valid_ps, -100, valid_cl, valid_ep),
        (valid_sl, valid_sp, valid_ps, {0: 400, 1: 400}, valid_cl, valid_ep),
        (valid_sl, valid_sp, 105, 100.5, valid_cl, valid_ep),
        (valid_sl, valid_sp, 105.5, 100, valid_cl, valid_ep),
        (valid_sl, valid_sp, len(valid_sl) - 1, valid_pfc, valid_cl, valid_ep),
        (valid_sl, valid_sp, 400, 401, valid_cl, valid_ep),
        (valid_sl, valid_sp, valid_ps, valid_pfc, [], valid_ep),
        (valid_sl, valid_sp, valid_ps, valid_pfc, None, valid_ep),
        (valid_sl, valid_sp, valid_ps, valid_pfc, "string", valid_ep),
        (valid_sl, valid_sp, valid_ps, valid_pfc, -100, valid_ep),
        (valid_sl, valid_sp, valid_ps, valid_pfc, {0: 400, 1: 400}, valid_ep),
        (valid_sl, valid_sp, valid_ps, valid_pfc, 0.0, valid_ep),
        (valid_sl, valid_sp, valid_ps, valid_pfc, 1.0, valid_ep),
        (valid_sl, valid_sp, valid_ps, valid_pfc, 2.0, valid_ep),
        (valid_sl, valid_sp, valid_ps, valid_pfc, -2.0, valid_ep),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, []),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, "string"),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, -0.0001),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, 1.0001),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, {0: 400, 1: 400}),
    ],
)
def test_bad_init(
    sample_labels,
    sample_predictions,
    population_size,
    population_flagged_count,
    confidence_level,
    exact_precision,
):
    """Unit test for bad inputs to __init__ method in ClassificationConfidenceIntervals class."""
    with pytest.raises(Exception):
        ClassificationConfidenceIntervals(
            sample_labels=sample_labels,
            sample_predictions=sample_predictions,
            population_size=population_size,
            population_flagged_count=population_flagged_count,
            confidence_level=confidence_level,
            exact_precision=exact_precision,
        )


@pytest.mark.parametrize(
    "sample_labels, sample_predictions, population_size, "
    "population_flagged_count, confidence_level, exact_precision, plot_filename",
    [
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep, ""),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, None, "test_plot"),
    ],
)
def test_get_cis(
    sample_labels,
    sample_predictions,
    population_size,
    population_flagged_count,
    confidence_level,
    exact_precision,
    plot_filename,
):
    """Unit test for get_cis method in ClassificationConfidenceIntervals class."""
    classification_confidence_intervals = ClassificationConfidenceIntervals(
        sample_labels=sample_labels,
        sample_predictions=sample_predictions,
        population_size=population_size,
        population_flagged_count=population_flagged_count,
        confidence_level=confidence_level,
        exact_precision=exact_precision,
    )
    classification_confidence_intervals.get_cis(n_iters=100, plot_filename=plot_filename)


@pytest.mark.parametrize(
    "sample_labels, sample_predictions, population_size, "
    "population_flagged_count, confidence_level, exact_precision, n_iters, plot_filename",
    [
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep, 100, []),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep, 100, -100),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep, 100, {0: 400, 1: 400}),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep, 0, "test_plot"),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep, [], "test_plot"),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep, "string", "test_plot"),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep, -100, "test_plot"),
        (valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep, {0: 400}, "test_plot"),
    ],
)
def test_bad_get_cis(
    sample_labels,
    sample_predictions,
    population_size,
    population_flagged_count,
    confidence_level,
    exact_precision,
    n_iters,
    plot_filename,
):
    """Unit test for bad inputs to get_cis method in ClassificationConfidenceIntervals class."""
    classification_confidence_intervals = ClassificationConfidenceIntervals(
        sample_labels=sample_labels,
        sample_predictions=sample_predictions,
        population_size=population_size,
        population_flagged_count=population_flagged_count,
        confidence_level=confidence_level,
        exact_precision=exact_precision,
    )
    with pytest.raises(Exception):
        classification_confidence_intervals.get_cis(n_iters=n_iters, plot_filename=plot_filename)


@pytest.mark.parametrize(
    "sample_labels, sample_predictions, population_size, "
    "population_flagged_count, confidence_level, exact_precision",
    [(valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep)],
)
def test_overwrite(
    sample_labels,
    sample_predictions,
    population_size,
    population_flagged_count,
    confidence_level,
    exact_precision,
):
    """Unit test for read_only_properties wrapper."""
    classification_confidence_intervals = ClassificationConfidenceIntervals(
        sample_labels=sample_labels,
        sample_predictions=sample_predictions,
        population_size=population_size,
        population_flagged_count=population_flagged_count,
        confidence_level=confidence_level,
        exact_precision=exact_precision,
    )

    pos_rate_cis, ppv_cis, npv_cis, recall_cis = classification_confidence_intervals.get_cis()

    with pytest.raises(Exception):
        pos_rate_cis.tnorm_ci = tuple([0.5, 0.8])


@pytest.mark.parametrize(
    "sample_labels, sample_predictions, population_size, "
    "population_flagged_count, confidence_level, exact_precision",
    [(valid_sl, valid_sp, valid_ps, valid_pfc, valid_cl, valid_ep)],
)
def test_str_repr_del(
    sample_labels,
    sample_predictions,
    population_size,
    population_flagged_count,
    confidence_level,
    exact_precision,
):
    """Unit test for str, repr, and del methods."""
    classification_confidence_intervals = ClassificationConfidenceIntervals(
        sample_labels=sample_labels,
        sample_predictions=sample_predictions,
        population_size=population_size,
        population_flagged_count=population_flagged_count,
        confidence_level=confidence_level,
        exact_precision=exact_precision,
    )
    pos_rate_cis, _, _, _ = classification_confidence_intervals.get_cis()

    assert (
        classification_confidence_intervals.__str__()
        == classification_confidence_intervals.__repr__()
    )
    del classification_confidence_intervals

    assert pos_rate_cis.__str__() == pos_rate_cis.__repr__()
    del pos_rate_cis
