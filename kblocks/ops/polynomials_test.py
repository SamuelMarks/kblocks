import numpy as np
import tensorflow as tf

from kblocks.ops import polynomials as p


def get_inner_products(builder, order, n_divs=1e6):
    n_divs = int(n_divs)
    a, b = builder.get_domain()

    def transform_bounds(a):
        if a == -np.inf:
            a = -100.0
        elif a == np.inf:
            a = 100.0
        elif isinstance(a, int):
            a = float(a)
        return a

    a = transform_bounds(a)
    b = transform_bounds(b)

    x = tf.linspace(a, b, n_divs)
    x = x[1:-1]
    polynomials = builder.get_polynomials(x, order)
    weighting_fn = builder.get_weighting_fn(x)

    norms = []
    dx = (b - a) / n_divs
    for i in range(order):
        ni = []
        poly = polynomials[i]
        integrand = poly * poly * weighting_fn
        integral = tf.reduce_sum(integrand) * dx
        ni.append(integral / builder.get_normalization_factor(i) - 1)
        for j in range(i + 1, order):
            integrand = poly * polynomials[j] * weighting_fn
            integral = tf.reduce_sum(integrand) * dx
            ni.append(integral)
        norms.append(ni)
    return norms


class PolynomialBuilderTest(tf.test.TestCase):
    def _test_orthogonal(self, builder, order=5):
        with tf.device("cpu:0"):
            norms = get_inner_products(builder, order)
            norms = tf.concat(norms, axis=0)
            self.assertAllLess(self.evaluate(tf.abs(norms)), 1e-2)

    def test_legendre_orthogonal(self):
        self._test_orthogonal(p.LegendrePolynomialBuilder())

    def test_chebyshev_first_orthogonal(self):
        self._test_orthogonal(p.FirstChebyshevPolynomialBuilder())

    def test_chebyshev_second_orthogonal(self):
        self._test_orthogonal(p.SecondChebyshevPolynomialBuilder())

    def test_hermite_orthogonal(self):
        self._test_orthogonal(p.HermitePolynomialBuilder())

    def test_gaussian_hermite_orthogonal(self):
        for stddev in (1.0, 2.0):
            self._test_orthogonal(p.GaussianHermitePolynomialBuilder(stddev=stddev))

    def test_gegenbauer_orthogonal(self):
        for lam in (0.0, 0.75, 0.85):
            self._test_orthogonal(p.GegenbauerPolynomialBuilder(lam=lam))

    def test_geom(self):
        builder = p.GeometricPolynomialBuilder()
        x = tf.random.normal((1000,), dtype=tf.float32)
        actual = builder(x, 4)
        expected = tf.expand_dims(x, axis=0) ** tf.expand_dims(
            tf.range(4, dtype=tf.float32), axis=1
        )
        actual, expected = self.evaluate((actual, expected))
        np.testing.assert_allclose(actual, expected)

    def test_nd(self):
        builder = p.NdPolynomialBuilder(max_order=3, is_total_order=True)
        polys = builder(tf.random.normal(shape=(3,)))
        self.assertEqual(polys.shape.as_list(), [20])
        polys = builder(tf.random.normal(shape=(10, 3)), unstack_axis=-1, stack_axis=-1)
        self.assertEqual(polys.shape.as_list(), [10, 20])
        xyz = tf.random.normal(shape=(3, 10))
        actual = builder(xyz, unstack_axis=0, stack_axis=0)
        x, y, z = tf.unstack(xyz, axis=0)
        expected = [
            x ** 0 * y ** 0 * z ** 0,
            x ** 0 * y ** 0 * z ** 1,
            x ** 0 * y ** 0 * z ** 2,
            x ** 0 * y ** 0 * z ** 3,
            x ** 0 * y ** 1 * z ** 0,
            x ** 0 * y ** 1 * z ** 1,
            x ** 0 * y ** 1 * z ** 2,
            # x ** 0 * y ** 1 * z ** 3,
            x ** 0 * y ** 2 * z ** 0,
            x ** 0 * y ** 2 * z ** 1,
            # x ** 0 * y ** 2 * z ** 2,
            # x ** 0 * y ** 2 * z ** 3,
            y ** 3,
            x ** 1 * y ** 0 * z ** 0,
            x ** 1 * y ** 0 * z ** 1,
            x ** 1 * y ** 0 * z ** 2,
            # x ** 1 * y ** 0 * z ** 3,
            x ** 1 * y ** 1 * z ** 0,
            x ** 1 * y ** 1 * z ** 1,
            # x ** 1 * y ** 1 * z ** 2,
            # x ** 1 * y ** 1 * z ** 3,
            x ** 1 * y ** 2 * z ** 0,
            # x ** 1 * y ** 2 * z ** 1,
            # x ** 1 * y ** 2 * z ** 2,
            # x ** 1 * y ** 2 * z ** 3,
            x ** 2 * y ** 0 * z ** 0,
            x ** 2 * y ** 0 * z ** 1,
            # x ** 2 * y ** 0 * z ** 2,
            # x ** 2 * y ** 0 * z ** 3,
            x ** 2 * y ** 1 * z ** 0,
            # x ** 2 * y ** 1 * z ** 1,
            # x ** 2 * y ** 1 * z ** 2,
            # x ** 2 * y ** 1 * z ** 3,
            # x ** 2 * y ** 2 * z ** 0,
            # x ** 2 * y ** 2 * z ** 1,
            # x ** 2 * y ** 2 * z ** 2,
            # x ** 2 * y ** 2 * z ** 3,
            x ** 3,
        ]

        self.assertEqual(actual.shape.as_list(), [20, 10])
        expected = tf.stack(expected, axis=0)
        actual, expected = self.evaluate((actual, expected))
        np.testing.assert_allclose(actual, expected)


if __name__ == "__main__":
    tf.test.main()
