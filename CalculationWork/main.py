from fractions import Fraction
import itertools
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


OBJECTIVES = [
    {"name": "Z1", "coeff": [1, 2, 1, 0], "sense": "max"},
    {"name": "Z2", "coeff": [-1, -2, 1, 1], "sense": "min"},
    {"name": "Z3", "coeff": [-2, -1, 1, 1], "sense": "max"},
]

CONSTRAINTS = [
    ([2, -1, 3, 4], 10, "2x1 - x2 + 3x3 + 4x4 <= 10"),
    ([1, 1, 1, -1], 5, "x1 + x2 + x3 - x4 <= 5"),
    ([1, 2, -2, 4], 12, "x1 + 2x2 - 2x3 + 4x4 <= 12"),
]

NONNEGATIVITY = [
    ([1, 0, 0, 0], 0, "x1 = 0"),
    ([0, 1, 0, 0], 0, "x2 = 0"),
    ([0, 0, 1, 0], 0, "x3 = 0"),
    ([0, 0, 0, 1], 0, "x4 = 0"),
]


def fr(value):
    return Fraction(value)


def fmt(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def fmt_decimal(value, digits=4):
    return f"{float(Fraction(value)):.{digits}f}"


def dot(coefficients, vector):
    return sum(fr(c) * fr(x) for c, x in zip(coefficients, vector))


def solve_linear_system(matrix, rhs):
    n = len(rhs)
    augmented = [[fr(value) for value in row] + [fr(rhs[index])] for index, row in enumerate(matrix)]

    for col in range(n):
        pivot = None
        for row in range(col, n):
            if augmented[row][col] != 0:
                pivot = row
                break
        if pivot is None:
            return None
        if pivot != col:
            augmented[col], augmented[pivot] = augmented[pivot], augmented[col]

        pivot_value = augmented[col][col]
        augmented[col] = [value / pivot_value for value in augmented[col]]

        for row in range(n):
            if row == col:
                continue
            factor = augmented[row][col]
            if factor != 0:
                augmented[row] = [
                    value - factor * pivot_value
                    for value, pivot_value in zip(augmented[row], augmented[col])
                ]

    return [augmented[row][-1] for row in range(n)]


def is_feasible(point):
    if any(value < 0 for value in point):
        return False
    for coefficients, bound, _ in CONSTRAINTS:
        if dot(coefficients, point) > bound:
            return False
    return True


def all_vertices():
    active_constraints = CONSTRAINTS + NONNEGATIVITY
    vertices = []
    seen = set()

    for selected in itertools.combinations(range(len(active_constraints)), 4):
        matrix = [active_constraints[index][0] for index in selected]
        rhs = [active_constraints[index][1] for index in selected]
        point = solve_linear_system(matrix, rhs)
        if point is None or not is_feasible(point):
            continue
        key = tuple(point)
        if key not in seen:
            seen.add(key)
            labels = [active_constraints[index][2] for index in selected]
            vertices.append({"point": point, "active": labels})

    return vertices


def objective_value(objective, point):
    return dot(objective["coeff"], point)


def optimize_objective(objective, vertices):
    values = [(objective_value(objective, item["point"]), item) for item in vertices]
    if objective["sense"] == "max":
        best_value = max(value for value, _ in values)
    else:
        best_value = min(value for value, _ in values)
    best_items = [item for value, item in values if value == best_value]
    return best_value, best_items


def print_variant():
    print("\nВаріант №1")
    print("Цільові функції:")
    print("  Z1 = x1 + 2x2 + x3 -> max")
    print("  Z2 = -x1 - 2x2 + x3 + x4 -> min")
    print("  Z3 = -2x1 - x2 + x3 + x4 -> max")
    print("\nОбмеження:")
    for _, _, text in CONSTRAINTS:
        print(f"  {text}")
    print("  x1, x2, x3, x4 >= 0")


def print_vertices():
    vertices = all_vertices()
    print("\nВершини допустимої області:")
    print(f"{'№':>3} {'x1':>10} {'x2':>10} {'x3':>10} {'x4':>10}")
    for index, item in enumerate(vertices, start=1):
        point = item["point"]
        print(f"{index:>3} " + "".join(f"{fmt(value):>10}" for value in point))
    return vertices


def solve_single_objectives():
    vertices = print_vertices()
    optimal = []
    print("\nРозв'язання окремих задач лінійного програмування:")
    for objective in OBJECTIVES:
        best_value, best_items = optimize_objective(objective, vertices)
        point = best_items[0]["point"]
        optimal.append({"objective": objective, "value": best_value, "point": point})
        print(f"\n{objective['name']} ({objective['sense']}):")
        print("  X* = (" + ", ".join(fmt(value) for value in point) + ")")
        print(f"  {objective['name']}* = {fmt(best_value)} = {fmt_decimal(best_value)}")
    return optimal


def build_regret_matrix(optimal):
    ideals = [item["value"] for item in optimal]
    points = [item["point"] for item in optimal]
    matrix = []

    for point in points:
        row = []
        for objective_index, objective in enumerate(OBJECTIVES):
            value = objective_value(objective, point)
            if objective["sense"] == "max":
                regret = ideals[objective_index] - value
            else:
                regret = value - ideals[objective_index]
            row.append(regret)
        matrix.append(row)

    return matrix


def print_regret_matrix():
    optimal = solve_single_objectives()
    matrix = build_regret_matrix(optimal)
    print("\nМатриця мір неоптимальності:")
    print(f"{'Розв.':>8} {'Z1':>10} {'Z2':>10} {'Z3':>10}")
    for index, row in enumerate(matrix, start=1):
        print(f"{'X' + str(index):>8} " + "".join(f"{fmt(value):>10}" for value in row))
    return optimal, matrix


def solve_minimax_regret(regret_matrix):
    rows = len(regret_matrix)
    cols = len(regret_matrix[0])
    best = None

    # Variables are p1..pm,t. Constraints: column expected regrets <= t, pi >= 0.
    constraints = []
    for col in range(cols):
        constraints.append(([regret_matrix[row][col] for row in range(rows)] + [-1], 0, f"g{col + 1}=t"))
    for row in range(rows):
        vector = [0 for _ in range(rows + 1)]
        vector[row] = 1
        constraints.append((vector, 0, f"p{row + 1}=0"))

    equality = [1 for _ in range(rows)] + [0]
    equality_rhs = 1

    for active in itertools.combinations(range(len(constraints)), rows):
        matrix = [equality] + [constraints[index][0] for index in active]
        rhs = [equality_rhs] + [constraints[index][1] for index in active]
        solution = solve_linear_system(matrix, rhs)
        if solution is None:
            continue
        probabilities = solution[:rows]
        value = solution[-1]
        if any(probability < 0 for probability in probabilities):
            continue
        expected = [
            sum(probabilities[row] * regret_matrix[row][col] for row in range(rows))
            for col in range(cols)
        ]
        if any(item > value for item in expected):
            continue
        if best is None or value < best["value"]:
            best = {"probabilities": probabilities, "value": value, "expected": expected}

    return best


def compromise_solution():
    optimal, matrix = print_regret_matrix()
    game = solve_minimax_regret(matrix)
    probabilities = game["probabilities"]
    points = [item["point"] for item in optimal]

    compromise = []
    for variable_index in range(4):
        value = sum(probabilities[row] * points[row][variable_index] for row in range(len(points)))
        compromise.append(value)

    print("\nРозв'язання матричної гри мінімаксного жалю:")
    print("  Вагові коефіцієнти для знайдених оптимальних розв'язків:")
    for index, probability in enumerate(probabilities, start=1):
        print(f"    λ{index} = {fmt(probability)} = {fmt_decimal(probability)}")
    print(f"  Значення гри: {fmt(game['value'])} = {fmt_decimal(game['value'])}")

    print("\nОчікувані міри неоптимальності за цією стратегією:")
    for index, value in enumerate(game["expected"], start=1):
        print(f"  Z{index}: {fmt(value)} = {fmt_decimal(value)}")

    print("\nВектор компромісного розв'язку:")
    print("  Xc = (" + ", ".join(fmt(value) for value in compromise) + ")")
    print("\nЗначення цільових функцій у компромісній точці:")
    for objective in OBJECTIVES:
        value = objective_value(objective, compromise)
        print(f"  {objective['name']}(Xc) = {fmt(value)} = {fmt_decimal(value)}")


def main():
    while True:
        print("\n" + "=" * 74)
        print("Розрахункова робота")
        print("Багатокритеріальна оптимізація. Теоретико-ігровий підхід")
        print("=" * 74)
        print("1. Показати умову варіанту №1")
        print("2. Показати вершини допустимої області")
        print("3. Розв'язати окремі задачі ЛП")
        print("4. Побудувати матрицю мір неоптимальності")
        print("5. Знайти компромісний розв'язок")
        print("0. Вийти")

        choice = input("\nОберіть дію: ").strip()
        if choice == "1":
            print_variant()
        elif choice == "2":
            print_vertices()
        elif choice == "3":
            solve_single_objectives()
        elif choice == "4":
            print_regret_matrix()
        elif choice == "5":
            compromise_solution()
        elif choice == "0":
            print("\nРоботу програми завершено.")
            break
        else:
            print("\nНевірний пункт меню. Спробуйте ще раз.")


if __name__ == "__main__":
    main()
