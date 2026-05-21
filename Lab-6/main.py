import itertools
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


COSTS = [
    [7, 10, 5, 7],
    [8, 11, 16, 14],
    [13, 9, 10, 5],
    [21, 19, 15, 18],
]


def print_matrix(matrix, title):
    print(f"\n{title}:")
    headers = [""] + [f"R{index + 1}" for index in range(len(matrix[0]))]
    print("".join(f"{header:>8}" for header in headers))
    for index, row in enumerate(matrix):
        values = [f"P{index + 1}"] + [str(value) for value in row]
        print("".join(f"{value:>8}" for value in values))


def print_variant():
    print("\nВаріант №1")
    print_matrix(COSTS, "Матриця вартостей робіт")
    print("\nПозначення:")
    print("  P1..P4 - співробітники")
    print("  R1..R4 - роботи")


def row_reduction(matrix):
    result = []
    row_minima = []
    for row in matrix:
        minimum = min(row)
        row_minima.append(minimum)
        result.append([value - minimum for value in row])
    return result, row_minima


def column_reduction(matrix):
    cols = len(matrix[0])
    column_minima = [min(matrix[row][col] for row in range(len(matrix))) for col in range(cols)]
    result = []
    for row in matrix:
        result.append([value - column_minima[col] for col, value in enumerate(row)])
    return result, column_minima


def min_zero_cover(matrix):
    n = len(matrix)
    zero_cells = {(i, j) for i in range(n) for j in range(n) if matrix[i][j] == 0}
    best_rows = set()
    best_cols = set(range(n))
    best_count = 2 * n

    for rows_mask in range(1 << n):
        rows = {i for i in range(n) if rows_mask & (1 << i)}
        for cols_mask in range(1 << n):
            cols = {j for j in range(n) if cols_mask & (1 << j)}
            if len(rows) + len(cols) >= best_count:
                continue
            if all(i in rows or j in cols for i, j in zero_cells):
                best_rows = rows
                best_cols = cols
                best_count = len(rows) + len(cols)

    return best_rows, best_cols


def adjust_matrix(matrix, covered_rows, covered_cols):
    n = len(matrix)
    uncovered = [
        matrix[i][j]
        for i in range(n)
        for j in range(n)
        if i not in covered_rows and j not in covered_cols
    ]
    minimum = min(uncovered)
    result = [row[:] for row in matrix]

    for i in range(n):
        for j in range(n):
            if i not in covered_rows and j not in covered_cols:
                result[i][j] -= minimum
            elif i in covered_rows and j in covered_cols:
                result[i][j] += minimum

    return result, minimum


def assignment_from_zero_matrix(matrix):
    n = len(matrix)
    for permutation in itertools.permutations(range(n)):
        if all(matrix[row][permutation[row]] == 0 for row in range(n)):
            return list(permutation)
    return None


def assignment_cost(assignment, matrix=COSTS):
    return sum(matrix[row][col] for row, col in enumerate(assignment))


def print_assignment(assignment, title):
    print(f"\n{title}:")
    for row, col in enumerate(assignment):
        print(f"  P{row + 1} -> R{col + 1}, вартість = {COSTS[row][col]}")
    print(f"Загальна мінімальна вартість: {assignment_cost(assignment)}")


def solve_hungarian():
    print_matrix(COSTS, "Початкова матриця вартостей")

    reduced_rows, row_minima = row_reduction(COSTS)
    print("\nРедукція за рядками:")
    for index, minimum in enumerate(row_minima, start=1):
        print(f"  Рядок P{index}: мінімум = {minimum}")
    print_matrix(reduced_rows, "Матриця після редукції рядків")

    matrix, column_minima = column_reduction(reduced_rows)
    print("\nРедукція за стовпцями:")
    for index, minimum in enumerate(column_minima, start=1):
        print(f"  Стовпець R{index}: мінімум = {minimum}")
    print_matrix(matrix, "Матриця після редукції стовпців")

    iteration = 1
    while True:
        covered_rows, covered_cols = min_zero_cover(matrix)
        print(f"\nІтерація {iteration}: покриття нулів")
        print("  Покриті рядки: " + (", ".join(f"P{i + 1}" for i in sorted(covered_rows)) or "немає"))
        print("  Покриті стовпці: " + (", ".join(f"R{j + 1}" for j in sorted(covered_cols)) or "немає"))
        print(f"  Кількість ліній: {len(covered_rows) + len(covered_cols)}")

        assignment = assignment_from_zero_matrix(matrix)
        if assignment is not None and len(covered_rows) + len(covered_cols) == len(matrix):
            print("\nКількість ліній дорівнює розмірності матриці, можна виконати призначення.")
            print_assignment(assignment, "Оптимальне призначення")
            return assignment

        matrix, minimum = adjust_matrix(matrix, covered_rows, covered_cols)
        print(f"  Мінімальний непокритий елемент = {minimum}")
        print_matrix(matrix, f"Матриця після перетворення {iteration}")
        iteration += 1


def brute_force_check():
    print("\nПеревірка повним перебором усіх призначень")
    best_assignment = None
    best_cost = None
    for permutation in itertools.permutations(range(len(COSTS))):
        cost = assignment_cost(permutation)
        description = ", ".join(f"P{i + 1}->R{job + 1}" for i, job in enumerate(permutation))
        print(f"  {description}: Z = {cost}")
        if best_cost is None or cost < best_cost:
            best_cost = cost
            best_assignment = permutation

    print_assignment(best_assignment, "Найкраще призначення за повним перебором")


def linear_programming_statement():
    print("\nПостановка задачі призначення як задачі лінійного програмування")
    terms = []
    for i in range(len(COSTS)):
        for j in range(len(COSTS[i])):
            terms.append(f"{COSTS[i][j]}x{i + 1}{j + 1}")
    print("Мінімізувати:")
    print("  Z = " + " + ".join(terms) + " -> min")

    print("\nКожен співробітник виконує рівно одну роботу:")
    for i in range(len(COSTS)):
        variables = " + ".join(f"x{i + 1}{j + 1}" for j in range(len(COSTS[i])))
        print(f"  {variables} = 1")

    print("\nКожна робота призначається рівно одному співробітнику:")
    for j in range(len(COSTS[0])):
        variables = " + ".join(f"x{i + 1}{j + 1}" for i in range(len(COSTS)))
        print(f"  {variables} = 1")

    print("\nУмова бінарності:")
    print("  xij ∈ {0, 1}")


def simplex_tableau_text():
    print("\nСимплекс-таблиця для задачі призначення")
    print("Змінні xij показують, чи призначений співробітник Pi на роботу Rj.")
    print("Оскільки кожен рядок і кожен стовпець має суму 1, задача призначення є спеціальним випадком транспортної задачі.")
    print("\nУ симплекс-формі можна використовувати 7 незалежних обмежень:")
    print("  4 обмеження для співробітників та 3 незалежні обмеження для робіт.")
    print("Угорський метод є спеціалізованим алгоритмом для цієї симплекс-структури.")

    assignment = solve_hungarian()
    print("\nОтримане призначення можна подати як бінарну матрицю X:")
    binary = [[0 for _ in range(len(COSTS))] for _ in range(len(COSTS))]
    for i, j in enumerate(assignment):
        binary[i][j] = 1
    print_matrix(binary, "Матриця призначень X",)


def main():
    while True:
        print("\n" + "=" * 68)
        print("Практична робота №6")
        print("Задача про призначення. Угорський метод")
        print("=" * 68)
        print("1. Показати умову варіанту №1")
        print("2. Розв'язати задачу угорським методом")
        print("3. Перевірити результат повним перебором")
        print("4. Постановка як задача лінійного програмування")
        print("5. Симплекс-таблиця для задачі призначення")
        print("0. Вийти")

        choice = input("\nОберіть дію: ").strip()
        if choice == "1":
            print_variant()
        elif choice == "2":
            solve_hungarian()
        elif choice == "3":
            brute_force_check()
        elif choice == "4":
            linear_programming_statement()
        elif choice == "5":
            simplex_tableau_text()
        elif choice == "0":
            print("\nРоботу програми завершено.")
            break
        else:
            print("\nНевірний пункт меню. Спробуйте ще раз.")


if __name__ == "__main__":
    main()
