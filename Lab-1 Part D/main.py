from fractions import Fraction
import math
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
INTEGER_VARIABLES = 4


def format_fraction(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def variable_name(index):
    return f"x{index + 1}"


def fractional_part(value):
    return value - math.floor(value)


def print_variant():
    print("\nВаріант №1")
    print("Z = x1 - 8x2 + x3 + 4x4 -> max")
    print("при обмеженнях:")
    print("  x1 - x2 + x3 + x4 <= 2")
    print("  x1 - x2 + x3 - x4 <= 2")
    print(" -x1 - x2 + x3 + x4 <= 2")
    print("  x1 - x2 - x3 + x4 <= 2")
    print("  xj >= 0, j = 1..4")
    print("  x1, x2, x3, x4 - цілі")


def build_initial_tableau():
    variables_count = len(OBJECTIVE)
    constraints_count = len(CONSTRAINTS)
    tableau = []

    for row_index, (row, right_side) in enumerate(zip(CONSTRAINTS, RIGHT_SIDE)):
        slack = [Fraction(1 if row_index == col else 0) for col in range(constraints_count)]
        tableau.append([Fraction(value) for value in row] + slack + [Fraction(right_side)])

    objective_row = [-Fraction(value) for value in OBJECTIVE]
    objective_row += [Fraction(0) for _ in range(constraints_count)]
    objective_row.append(Fraction(0))

    basis = [variables_count + index for index in range(constraints_count)]
    return tableau, objective_row, basis


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
    solution = current_solution(tableau, basis, INTEGER_VARIABLES)
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


def simplex(tableau, objective_row, basis, title_prefix="Симплекс-таблиця"):
    protocol = []
    iteration = 1

    while True:
        entering_column = choose_entering_column(objective_row)
        if entering_column is None:
            protocol.append("У рядку Z немає від'ємних коефіцієнтів. Оптимум LP-релаксації знайдено.")
            return True, protocol

        leaving_row = choose_leaving_row(tableau, entering_column)
        if leaving_row is None:
            protocol.append("Цільова функція необмежена на множині допустимих розв'язків.")
            return False, protocol

        old_basis = basis[leaving_row]
        protocol.append(
            f"Ітерація {iteration}: у базис входить {variable_name(entering_column)}, "
            f"з базису виходить {variable_name(old_basis)}; "
            f"опорний елемент = {format_fraction(tableau[leaving_row][entering_column])}."
        )
        pivot(tableau, objective_row, basis, leaving_row, entering_column)
        print_tableau(tableau, objective_row, basis, f"{title_prefix} після ітерації {iteration}")
        iteration += 1


def find_fractional_basis_row(tableau, basis):
    candidates = []
    for row_index, basis_variable in enumerate(basis):
        if basis_variable < INTEGER_VARIABLES:
            part = fractional_part(tableau[row_index][-1])
            if part != 0:
                candidates.append((part, row_index))
    if not candidates:
        return None
    return max(candidates)[1]


def add_gomory_cut(tableau, objective_row, basis, source_row):
    old_variables_count = len(objective_row) - 1
    new_variable_index = old_variables_count
    cut_coefficients = []

    for value in tableau[source_row][:-1]:
        cut_coefficients.append(-fractional_part(value))
    cut_right_side = -fractional_part(tableau[source_row][-1])

    for row in tableau:
        row.insert(-1, Fraction(0))
    objective_row.insert(-1, Fraction(0))

    cut_row = cut_coefficients + [Fraction(1), cut_right_side]
    tableau.append(cut_row)
    basis.append(new_variable_index)
    return new_variable_index


def gomory_method():
    tableau, objective_row, basis = build_initial_tableau()
    print_tableau(tableau, objective_row, basis, "Початкова симплекс-таблиця")

    simplex_success, simplex_protocol = simplex(tableau, objective_row, basis)
    print("\nПротокол розв'язання LP-релаксації:")
    for index, step in enumerate(simplex_protocol, start=1):
        print(f"  {index}. {step}")

    if not simplex_success:
        print("\nЦілочисловий розв'язок не знайдено.")
        return

    print_solution(tableau, basis, "Оптимальний розв'язок LP-релаксації")

    gomory_protocol = []
    cut_number = 1
    max_cuts = 10

    while cut_number <= max_cuts:
        source_row = find_fractional_basis_row(tableau, basis)
        if source_row is None:
            gomory_protocol.append("Усі основні змінні x1..x4 мають цілі значення. Відсікання Гоморі не потрібне.")
            break

        new_variable_index = add_gomory_cut(tableau, objective_row, basis, source_row)
        gomory_protocol.append(
            f"Відсікання {cut_number}: побудовано за рядком {source_row + 1}, "
            f"додано змінну {variable_name(new_variable_index)}."
        )
        print_tableau(tableau, objective_row, basis, f"Таблиця після додавання відсікання {cut_number}")

        simplex_success, simplex_protocol = simplex(
            tableau,
            objective_row,
            basis,
            title_prefix=f"Таблиця після відсікання {cut_number}",
        )
        gomory_protocol.extend(simplex_protocol)
        if not simplex_success:
            break
        cut_number += 1

    print("\nПротокол методу Гоморі:")
    for index, step in enumerate(gomory_protocol, start=1):
        print(f"  {index}. {step}")

    print_solution(tableau, basis, "Цілочисловий оптимальний розв'язок")


def show_lp_relaxation():
    tableau, objective_row, basis = build_initial_tableau()
    print_tableau(tableau, objective_row, basis, "Початкова симплекс-таблиця")

    success, protocol = simplex(tableau, objective_row, basis)
    print("\nПротокол симплекс-методу:")
    for index, step in enumerate(protocol, start=1):
        print(f"  {index}. {step}")

    if success:
        print_solution(tableau, basis, "Оптимальний розв'язок LP-релаксації")


def check_integer_solution():
    tableau, objective_row, basis = build_initial_tableau()
    success, _ = simplex(tableau, objective_row, basis)
    if not success:
        print("\nLP-релаксація не має обмеженого оптимального розв'язку.")
        return

    solution = current_solution(tableau, basis, INTEGER_VARIABLES)
    print_solution(tableau, basis, "Розв'язок для перевірки")
    print("\nПеревірка цілочисельності:")
    all_integer = True
    for index, value in enumerate(solution, start=1):
        is_integer = value.denominator == 1
        all_integer = all_integer and is_integer
        status = "ціле" if is_integer else "дробове"
        print(f"  x{index} = {format_fraction(value)} - {status}")

    if all_integer:
        print("\nРозв'язок є цілочисловим, тому він є оптимальним для задачі ЦЛП.")
    else:
        print("\nЄ дробові значення, необхідно будувати відсікання Гоморі.")


def main():
    while True:
        print("\n" + "=" * 68)
        print("Практична робота №1 (part D)")
        print("Цілочислове лінійне програмування. Метод Гоморі")
        print("=" * 68)
        print("1. Показати умову варіанту №1")
        print("2. Розв'язати LP-релаксацію")
        print("3. Перевірити розв'язок на цілочисельність")
        print("4. Розв'язати задачу методом Гоморі")
        print("0. Вийти")

        choice = input("\nОберіть дію: ").strip()
        if choice == "1":
            print_variant()
        elif choice == "2":
            show_lp_relaxation()
        elif choice == "3":
            check_integer_solution()
        elif choice == "4":
            gomory_method()
        elif choice == "0":
            print("\nРоботу програми завершено.")
            break
        else:
            print("\nНевірний пункт меню. Спробуйте ще раз.")


if __name__ == "__main__":
    main()
