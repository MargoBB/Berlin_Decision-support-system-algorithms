from fractions import Fraction
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


VARIANT_A = [
    [2, -1, 3],
    [1, 3, -2],
    [3, 1, -1],
]

VARIANT_B = [4, 2, 3]


def to_fraction_matrix(matrix):
    return [[Fraction(value) for value in row] for row in matrix]


def to_fraction_vector(vector):
    return [Fraction(value) for value in vector]


def format_fraction(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def print_matrix(matrix, title="Матриця"):
    print(f"\n{title}:")
    for row in matrix:
        print("  " + " ".join(f"{format_fraction(value):>9}" for value in row))


def print_vector(vector, title="Вектор"):
    print(f"\n{title}:")
    for index, value in enumerate(vector, start=1):
        print(f"  x{index} = {format_fraction(value)}")


def print_plain_vector(vector, title="Вектор"):
    print(f"\n{title}:")
    for value in vector:
        print(f"  {format_fraction(value):>9}")


def print_augmented(matrix, title="Розширена матриця"):
    print(f"\n{title}:")
    for row in matrix:
        left = " ".join(f"{format_fraction(value):>9}" for value in row[:-1])
        right = f"{format_fraction(row[-1]):>9}"
        print(f"  {left} | {right}")


def parse_fraction(value):
    return Fraction(value.strip().replace(",", "."))


def read_positive_int(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value <= 0:
                raise ValueError
            return value
        except ValueError:
            print("Помилка: введіть додатне ціле число.")


def read_matrix(rows, cols, name):
    print(f"\nВведіть матрицю {name} розміром {rows}x{cols}.")
    print("Елементи рядка вводьте через пробіл, наприклад: 2 -1 3")
    matrix = []
    for row_index in range(rows):
        while True:
            try:
                raw = input(f"Рядок {row_index + 1}: ")
                row = [parse_fraction(item) for item in raw.split()]
                if len(row) != cols:
                    raise ValueError
                matrix.append(row)
                break
            except ValueError:
                print("Помилка: введіть правильну кількість чисел.")
    return matrix


def read_vector(size, name):
    while True:
        try:
            raw = input(f"\nВведіть вектор {name} з {size} елементів через пробіл: ")
            vector = [parse_fraction(item) for item in raw.split()]
            if len(vector) != size:
                raise ValueError
            return vector
        except ValueError:
            print("Помилка: введіть правильну кількість чисел.")


def swap_rows(matrix, first, second, protocol):
    matrix[first], matrix[second] = matrix[second], matrix[first]
    protocol.append(f"R{first + 1} <-> R{second + 1}")


def scale_row(matrix, row, coefficient, protocol):
    matrix[row] = [value * coefficient for value in matrix[row]]
    protocol.append(f"R{row + 1} = R{row + 1} * {format_fraction(coefficient)}")


def add_scaled_row(matrix, target, source, coefficient, protocol):
    matrix[target] = [
        value + coefficient * source_value
        for value, source_value in zip(matrix[target], matrix[source])
    ]
    sign = "+" if coefficient >= 0 else "-"
    protocol.append(
        f"R{target + 1} = R{target + 1} {sign} "
        f"{format_fraction(abs(coefficient))} * R{source + 1}"
    )


def jordan_reduce(matrix, pivot_columns=None, full=True):
    result = [row[:] for row in matrix]
    rows = len(result)
    cols = len(result[0]) if rows else 0
    protocol = []
    pivot_columns = pivot_columns if pivot_columns is not None else range(cols)
    pivot_row = 0

    for col in pivot_columns:
        if pivot_row >= rows:
            break

        pivot = None
        for candidate in range(pivot_row, rows):
            if result[candidate][col] != 0:
                pivot = candidate
                break

        if pivot is None:
            protocol.append(f"Стовпець {col + 1}: опорний елемент відсутній")
            continue

        if pivot != pivot_row:
            swap_rows(result, pivot_row, pivot, protocol)

        pivot_value = result[pivot_row][col]
        if pivot_value != 1:
            scale_row(result, pivot_row, Fraction(1, 1) / pivot_value, protocol)

        target_rows = range(rows) if full else range(pivot_row + 1, rows)
        for row in target_rows:
            if row == pivot_row:
                continue
            if result[row][col] != 0:
                add_scaled_row(result, row, pivot_row, -result[row][col], protocol)

        pivot_row += 1

    return result, pivot_row, protocol


def inverse_matrix(matrix):
    n = len(matrix)
    augmented = []
    for row_index, row in enumerate(to_fraction_matrix(matrix)):
        identity_part = [
            Fraction(1 if row_index == col_index else 0)
            for col_index in range(n)
        ]
        augmented.append(row + identity_part)

    reduced, rank, protocol = jordan_reduce(augmented, pivot_columns=range(n), full=True)
    left = [row[:n] for row in reduced]
    identity = [[Fraction(1 if i == j else 0) for j in range(n)] for i in range(n)]

    if rank < n or left != identity:
        return None, protocol

    return [row[n:] for row in reduced], protocol


def matrix_rank(matrix):
    reduced, rank, protocol = jordan_reduce(to_fraction_matrix(matrix), full=False)
    return rank, reduced, protocol


def multiply_matrix_vector(matrix, vector):
    return [
        sum(row[col] * vector[col] for col in range(len(vector)))
        for row in matrix
    ]


def solve_by_inverse(matrix, vector):
    inverse, protocol = inverse_matrix(matrix)
    if inverse is None:
        return None, protocol
    solution = multiply_matrix_vector(inverse, to_fraction_vector(vector))
    return solution, protocol


def solve_by_jordan(matrix, vector):
    augmented = [
        row[:] + [value]
        for row, value in zip(to_fraction_matrix(matrix), to_fraction_vector(vector))
    ]
    reduced, rank, protocol = jordan_reduce(
        augmented,
        pivot_columns=range(len(matrix[0])),
        full=True,
    )
    n = len(vector)

    for row in reduced:
        if all(value == 0 for value in row[:n]) and row[-1] != 0:
            return None, reduced, protocol, "Система несумісна"

    if rank < n:
        return None, reduced, protocol, "Система має безліч розв'язків"

    return [reduced[i][-1] for i in range(n)], reduced, protocol, "Єдиний розв'язок"


def solve_by_gauss(matrix, vector):
    augmented = [
        row[:] + [value]
        for row, value in zip(to_fraction_matrix(matrix), to_fraction_vector(vector))
    ]
    triangular, rank, protocol = jordan_reduce(
        augmented,
        pivot_columns=range(len(matrix[0])),
        full=False,
    )
    n = len(vector)

    for row in triangular:
        if all(value == 0 for value in row[:n]) and row[-1] != 0:
            return None, triangular, protocol, "Система несумісна"

    if rank < n:
        return None, triangular, protocol, "Система має безліч розв'язків"

    solution = [Fraction(0) for _ in range(n)]
    for row_index in range(n - 1, -1, -1):
        right_side = triangular[row_index][-1]
        known_sum = sum(
            triangular[row_index][col] * solution[col]
            for col in range(row_index + 1, n)
        )
        solution[row_index] = (
            right_side - known_sum
        ) / triangular[row_index][row_index]
        protocol.append(
            f"x{row_index + 1} = "
            f"({format_fraction(right_side)} - {format_fraction(known_sum)}) / "
            f"{format_fraction(triangular[row_index][row_index])} = "
            f"{format_fraction(solution[row_index])}"
        )

    return solution, triangular, protocol, "Єдиний розв'язок"


def print_protocol(protocol):
    print("\nПротокол перетворень:")
    if not protocol:
        print("  Перетворення не виконувалися.")
        return
    for index, operation in enumerate(protocol, start=1):
        print(f"  {index}. {operation}")


def choose_matrix_for_inverse_or_rank(square_only):
    mode = input("Використати матрицю A з варіанту №1? (т/н): ").strip().lower()
    if mode in ("", "т", "так", "y", "yes"):
        return VARIANT_A

    if square_only:
        n = read_positive_int("Введіть розмір квадратної матриці n: ")
        return read_matrix(n, n, "A")

    rows = read_positive_int("Кількість рядків n: ")
    cols = read_positive_int("Кількість стовпців m: ")
    return read_matrix(rows, cols, "A")


def choose_system():
    mode = input("Використати A та B з варіанту №1? (т/н): ").strip().lower()
    if mode in ("", "т", "так", "y", "yes"):
        return VARIANT_A, VARIANT_B

    n = read_positive_int("Введіть розмір системи n: ")
    matrix = read_matrix(n, n, "A")
    vector = read_vector(n, "B")
    return matrix, vector


def run_inverse_task():
    print("\n--- Пошук оберненої матриці ---")
    matrix = choose_matrix_for_inverse_or_rank(square_only=True)
    print_matrix(to_fraction_matrix(matrix), "Вхідна матриця A")
    inverse, protocol = inverse_matrix(matrix)
    print_protocol(protocol)
    if inverse is None:
        print("\nОбернена матриця не існує, оскільки матриця вироджена.")
    else:
        print_matrix(inverse, "Обернена матриця A^-1")


def run_rank_task():
    print("\n--- Обчислення рангу матриці ---")
    matrix = choose_matrix_for_inverse_or_rank(square_only=False)
    print_matrix(to_fraction_matrix(matrix), "Вхідна матриця A")
    rank, reduced, protocol = matrix_rank(matrix)
    print_protocol(protocol)
    print_matrix(reduced, "Східчастий вигляд матриці")
    print(f"\nРанг матриці A: {rank}")


def run_solve_task(method):
    print("\n--- Розв'язання системи лінійних алгебраїчних рівнянь ---")
    matrix, vector = choose_system()

    print_matrix(to_fraction_matrix(matrix), "Матриця A")
    print_plain_vector(to_fraction_vector(vector), "Вектор B")

    if method == "inverse":
        solution, protocol = solve_by_inverse(matrix, vector)
        print_protocol(protocol)
    elif method == "jordan":
        solution, reduced, protocol, status = solve_by_jordan(matrix, vector)
        print_protocol(protocol)
        print_augmented(reduced, "Матриця після приведення методом Жордана")
        print(f"\nСтан системи: {status}")
    else:
        solution, triangular, protocol, status = solve_by_gauss(matrix, vector)
        print_protocol(protocol)
        print_augmented(triangular, "Трикутний вигляд матриці")
        print(f"\nСтан системи: {status}")

    if solution is None:
        print("\nРозв'язок не знайдено.")
        return

    print_vector(solution, "Вектор розв'язку X")


def print_variant():
    print("\nВаріант №1")
    print_matrix(to_fraction_matrix(VARIANT_A), "A")
    print_plain_vector(to_fraction_vector(VARIANT_B), "B")


def main():
    while True:
        print("\n" + "=" * 64)
        print("Практична робота №1 (part A)")
        print("Звичайні жорданові виключення")
        print("=" * 64)
        print("1. Показати матрицю та вектор варіанту №1")
        print("2. Знайти обернену матрицю")
        print("3. Обчислити ранг матриці")
        print("4. Розв'язати СЛАР через обернену матрицю")
        print("5. Розв'язати СЛАР методом Жордана")
        print("6. Розв'язати СЛАР методом Гаусса")
        print("0. Вийти")

        choice = input("\nОберіть дію: ").strip()
        if choice == "1":
            print_variant()
        elif choice == "2":
            run_inverse_task()
        elif choice == "3":
            run_rank_task()
        elif choice == "4":
            run_solve_task("inverse")
        elif choice == "5":
            run_solve_task("jordan")
        elif choice == "6":
            run_solve_task("gauss")
        elif choice == "0":
            print("\nРоботу програми завершено.")
            break
        else:
            print("\nНевірний пункт меню. Спробуйте ще раз.")


if __name__ == "__main__":
    main()
