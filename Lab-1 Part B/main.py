from fractions import Fraction
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


OBJECTIVE = [1, -8, 1, 4]
CONSTRAINTS = [
    [1, -1, 1, 1],
    [1, -1, 1, -1],
    [-1, -1, 1, 1],
    [1, -1, -1, 1],
]
RIGHT_SIDE = [2, 2, 2, 2]


def to_fraction_list(values):
    return [Fraction(value) for value in values]


def format_fraction(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def variable_name(index):
    return f"x{index + 1}"


def print_variant():
    print("\nВаріант №1")
    print("Z = x1 - 8x2 + x3 + 4x4 -> max")
    print("при обмеженнях:")
    print("  x1 - x2 + x3 + x4 <= 2")
    print("  x1 - x2 + x3 - x4 <= 2")
    print(" -x1 - x2 + x3 + x4 <= 2")
    print("  x1 - x2 - x3 + x4 <= 2")
    print("  xj >= 0, j = 1..4")


def build_initial_tableau():
    variables_count = len(OBJECTIVE)
    constraints_count = len(CONSTRAINTS)
    total_variables = variables_count + constraints_count
    tableau = []

    for row_index, (row, right_side) in enumerate(zip(CONSTRAINTS, RIGHT_SIDE)):
        slack = [Fraction(1 if row_index == col else 0) for col in range(constraints_count)]
        tableau.append(to_fraction_list(row) + slack + [Fraction(right_side)])

    objective_row = [-Fraction(value) for value in OBJECTIVE]
    objective_row += [Fraction(0) for _ in range(constraints_count)]
    objective_row.append(Fraction(0))

    basis = [variables_count + index for index in range(constraints_count)]
    return tableau, objective_row, basis, total_variables


def print_tableau(tableau, objective_row, basis, title):
    variables_count = len(objective_row) - 1
    headers = ["Базис"] + [variable_name(index) for index in range(variables_count)] + ["b"]
    widths = [8] + [9 for _ in range(variables_count)] + [9]

    print(f"\n{title}:")
    print("".join(f"{header:>{width}}" for header, width in zip(headers, widths)))

    for basis_variable, row in zip(basis, tableau):
        values = [variable_name(basis_variable)] + [format_fraction(value) for value in row]
        print("".join(f"{value:>{width}}" for value, width in zip(values, widths)))

    objective_values = ["Z"] + [format_fraction(value) for value in objective_row]
    print("".join(f"{value:>{width}}" for value, width in zip(objective_values, widths)))


def current_solution(tableau, basis, variables_count):
    solution = [Fraction(0) for _ in range(variables_count)]
    for row_index, basis_variable in enumerate(basis):
        if basis_variable < variables_count:
            solution[basis_variable] = tableau[row_index][-1]
    return solution


def objective_value(solution):
    return sum(Fraction(coef) * value for coef, value in zip(OBJECTIVE, solution))


def print_solution(tableau, basis, title):
    variables_count = len(OBJECTIVE)
    solution = current_solution(tableau, basis, variables_count)
    print(f"\n{title}:")
    for index, value in enumerate(solution, start=1):
        print(f"  x{index} = {format_fraction(value)}")
    print(f"  Z = {format_fraction(objective_value(solution))}")


def choose_entering_column(objective_row):
    candidates = [
        (value, index)
        for index, value in enumerate(objective_row[:-1])
        if value < 0
    ]
    if not candidates:
        return None
    return min(candidates)[1]


def choose_leaving_row(tableau, entering_column):
    ratios = []
    for row_index, row in enumerate(tableau):
        coefficient = row[entering_column]
        if coefficient > 0:
            ratios.append((row[-1] / coefficient, row_index))
    if not ratios:
        return None
    return min(ratios)[1]


def pivot(tableau, objective_row, basis, pivot_row, pivot_column):
    pivot_value = tableau[pivot_row][pivot_column]
    tableau[pivot_row] = [value / pivot_value for value in tableau[pivot_row]]

    for row_index, row in enumerate(tableau):
        if row_index == pivot_row:
            continue
        coefficient = row[pivot_column]
        if coefficient != 0:
            tableau[row_index] = [
                value - coefficient * pivot_value
                for value, pivot_value in zip(row, tableau[pivot_row])
            ]

    objective_coefficient = objective_row[pivot_column]
    if objective_coefficient != 0:
        objective_row[:] = [
            value - objective_coefficient * pivot_value
            for value, pivot_value in zip(objective_row, tableau[pivot_row])
        ]

    basis[pivot_row] = pivot_column


def simplex():
    tableau, objective_row, basis, total_variables = build_initial_tableau()
    protocol = []

    print_tableau(tableau, objective_row, basis, "Початкова симплекс-таблиця")
    print_solution(tableau, basis, "Початковий опорний розв'язок")

    iteration = 1
    while True:
        entering_column = choose_entering_column(objective_row)
        if entering_column is None:
            protocol.append("У рядку Z немає від'ємних коефіцієнтів. Оптимум знайдено.")
            break

        leaving_row = choose_leaving_row(tableau, entering_column)
        if leaving_row is None:
            protocol.append("Цільова функція необмежена на множині допустимих розв'язків.")
            return False, tableau, objective_row, basis, protocol

        old_basis = basis[leaving_row]
        protocol.append(
            f"Ітерація {iteration}: у базис входить {variable_name(entering_column)}, "
            f"з базису виходить {variable_name(old_basis)}; "
            f"опорний елемент = {format_fraction(tableau[leaving_row][entering_column])}."
        )

        pivot(tableau, objective_row, basis, leaving_row, entering_column)
        print_tableau(
            tableau,
            objective_row,
            basis,
            f"Симплекс-таблиця після ітерації {iteration}",
        )
        iteration += 1

    return True, tableau, objective_row, basis, protocol


def find_support_solution():
    tableau, objective_row, basis, _ = build_initial_tableau()
    print_tableau(tableau, objective_row, basis, "Початкова таблиця з додатковими змінними")
    print("\nОпорний розв'язок утворюється додатковими змінними:")
    print("  x1 = 0, x2 = 0, x3 = 0, x4 = 0")
    print("  x5 = 2, x6 = 2, x7 = 2, x8 = 2")
    print("  Усі праві частини невід'ємні, тому розв'язок є допустимим.")


def find_optimal_solution():
    success, tableau, objective_row, basis, protocol = simplex()
    print("\nПротокол модифікованих жорданових виключень:")
    for index, step in enumerate(protocol, start=1):
        print(f"  {index}. {step}")

    if not success:
        print("\nОптимальний розв'язок не знайдено.")
        return

    print_solution(tableau, basis, "Оптимальний розв'язок")


def main():
    while True:
        print("\n" + "=" * 68)
        print("Практична робота №1 (part B)")
        print("Лінійне програмування. Модифіковані жорданові виключення")
        print("=" * 68)
        print("1. Показати умову варіанту №1")
        print("2. Знайти початковий опорний розв'язок")
        print("3. Знайти оптимальний розв'язок")
        print("0. Вийти")

        choice = input("\nОберіть дію: ").strip()
        if choice == "1":
            print_variant()
        elif choice == "2":
            find_support_solution()
        elif choice == "3":
            find_optimal_solution()
        elif choice == "0":
            print("\nРоботу програми завершено.")
            break
        else:
            print("\nНевірний пункт меню. Спробуйте ще раз.")


if __name__ == "__main__":
    main()
