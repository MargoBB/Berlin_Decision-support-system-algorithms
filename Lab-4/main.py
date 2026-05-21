from fractions import Fraction
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


MATRIX = [
    [1, 1, 2, 6],
    [1, -2, 3, 5],
    [-3, 1, 2, 2],
]

HURWICZ_ALPHA = Fraction(3, 5)
BAYES_PROBABILITIES = [Fraction(1, 4) for _ in range(4)]


def fmt(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def fmt_decimal(value, digits=3):
    return f"{float(Fraction(value)):.{digits}f}"


def strategy_name(index):
    return f"A{index + 1}"


def state_name(index):
    return f"S{index + 1}"


def print_matrix(matrix=MATRIX, title="Матриця корисності U"):
    print(f"\n{title}:")
    headers = [""] + [state_name(index) for index in range(len(matrix[0]))]
    print("".join(f"{header:>8}" for header in headers))
    for index, row in enumerate(matrix):
        values = [strategy_name(index)] + [fmt(value) for value in row]
        print("".join(f"{value:>8}" for value in values))


def best_by_max(values):
    best_value = max(values)
    best_indices = [index for index, value in enumerate(values) if value == best_value]
    return best_value, best_indices


def best_by_min(values):
    best_value = min(values)
    best_indices = [index for index, value in enumerate(values) if value == best_value]
    return best_value, best_indices


def print_best(best_indices):
    return ", ".join(strategy_name(index) for index in best_indices)


def print_variant():
    print("\nВаріант №1")
    print_matrix()
    print("\nПозначення:")
    print("  A1..A3 - стратегії гравця")
    print("  S1..S4 - стани природи")


def wald_criterion():
    print_matrix()
    print("\nКритерій Вальда (принцип максиміну)")
    values = []
    for index, row in enumerate(MATRIX):
        row_min = min(row)
        values.append(Fraction(row_min))
        print(f"  {strategy_name(index)}: min = {row_min}")

    best_value, best_indices = best_by_max(values)
    print(f"\nОбираємо максимальне значення серед мінімумів: {fmt(best_value)}")
    print(f"Оптимальна стратегія за критерієм Вальда: {print_best(best_indices)}")


def optimism_criterion():
    print_matrix()
    print("\nКритерій оптимізму (принцип максимаксу)")
    values = []
    for index, row in enumerate(MATRIX):
        row_max = max(row)
        values.append(Fraction(row_max))
        print(f"  {strategy_name(index)}: max = {row_max}")

    best_value, best_indices = best_by_max(values)
    print(f"\nОбираємо максимальне значення серед максимумів: {fmt(best_value)}")
    print(f"Оптимальна стратегія за критерієм оптимізму: {print_best(best_indices)}")


def hurwicz_criterion(alpha=HURWICZ_ALPHA):
    print_matrix()
    print("\nКритерій Гурвіца (песимізм-оптимізм)")
    print(f"Коефіцієнт оптимізму alpha = {fmt(alpha)} = {fmt_decimal(alpha)}")
    values = []

    for index, row in enumerate(MATRIX):
        row_min = Fraction(min(row))
        row_max = Fraction(max(row))
        value = alpha * row_max + (1 - alpha) * row_min
        values.append(value)
        print(
            f"  {strategy_name(index)}: H = {fmt(alpha)}*{fmt(row_max)} + "
            f"{fmt(1 - alpha)}*{fmt(row_min)} = {fmt(value)} = {fmt_decimal(value)}"
        )

    best_value, best_indices = best_by_max(values)
    print(f"\nНайбільше значення H: {fmt(best_value)}")
    print(f"Оптимальна стратегія за критерієм Гурвіца: {print_best(best_indices)}")


def regret_matrix():
    columns = len(MATRIX[0])
    column_maxima = [max(MATRIX[row][col] for row in range(len(MATRIX))) for col in range(columns)]
    regrets = []
    for row in MATRIX:
        regrets.append([Fraction(column_maxima[col] - row[col]) for col in range(columns)])
    return column_maxima, regrets


def savage_criterion():
    print_matrix()
    print("\nКритерій Севіджа (принцип мінімаксу ризику)")
    column_maxima, regrets = regret_matrix()
    print("\nМаксимуми за станами природи:")
    for index, value in enumerate(column_maxima):
        print(f"  {state_name(index)}: {value}")

    print_matrix(regrets, "Матриця ризиків R")
    values = []
    for index, row in enumerate(regrets):
        row_max = max(row)
        values.append(Fraction(row_max))
        print(f"  {strategy_name(index)}: max ризик = {fmt(row_max)}")

    best_value, best_indices = best_by_min(values)
    print(f"\nОбираємо мінімальне значення серед максимальних ризиків: {fmt(best_value)}")
    print(f"Оптимальна стратегія за критерієм Севіджа: {print_best(best_indices)}")


def bayes_criterion(probabilities=BAYES_PROBABILITIES):
    print_matrix()
    print("\nКритерій Байєса")
    print("Ймовірності станів природи:")
    print("  " + ", ".join(f"P({state_name(index)}) = {fmt(prob)}" for index, prob in enumerate(probabilities)))
    values = []

    for index, row in enumerate(MATRIX):
        expected_value = sum(Fraction(value) * probabilities[col] for col, value in enumerate(row))
        values.append(expected_value)
        print(f"  {strategy_name(index)}: E = {fmt(expected_value)} = {fmt_decimal(expected_value)}")

    best_value, best_indices = best_by_max(values)
    print(f"\nНайбільше математичне сподівання: {fmt(best_value)}")
    print(f"Оптимальна стратегія за критерієм Байєса: {print_best(best_indices)}")


def laplace_criterion():
    print_matrix()
    print("\nКритерій Лапласа")
    print("Усі стани природи вважаються рівноймовірними.")
    probabilities = [Fraction(1, len(MATRIX[0])) for _ in range(len(MATRIX[0]))]
    values = []

    for index, row in enumerate(MATRIX):
        average = sum(Fraction(value) * probabilities[col] for col, value in enumerate(row))
        values.append(average)
        print(f"  {strategy_name(index)}: L = {fmt(average)} = {fmt_decimal(average)}")

    best_value, best_indices = best_by_max(values)
    print(f"\nНайбільше середнє значення: {fmt(best_value)}")
    print(f"Оптимальна стратегія за критерієм Лапласа: {print_best(best_indices)}")


def summary():
    row_minima = [Fraction(min(row)) for row in MATRIX]
    row_maxima = [Fraction(max(row)) for row in MATRIX]
    hurwicz_values = [
        HURWICZ_ALPHA * row_maxima[index] + (1 - HURWICZ_ALPHA) * row_minima[index]
        for index in range(len(MATRIX))
    ]
    _, regrets = regret_matrix()
    savage_values = [max(row) for row in regrets]
    bayes_values = [
        sum(Fraction(value) * BAYES_PROBABILITIES[col] for col, value in enumerate(row))
        for row in MATRIX
    ]
    laplace_values = [sum(Fraction(value) for value in row) / len(row) for row in MATRIX]

    criteria = [
        ("Вальда", row_minima, best_by_max),
        ("Оптимізму", row_maxima, best_by_max),
        ("Гурвіца", hurwicz_values, best_by_max),
        ("Севіджа", savage_values, best_by_min),
        ("Байєса", bayes_values, best_by_max),
        ("Лапласа", laplace_values, best_by_max),
    ]

    print_matrix()
    print("\nПідсумкова таблиця критеріїв:")
    print(f"{'Критерій':<14} {'A1':>8} {'A2':>8} {'A3':>8} {'Оптимум':>14}")
    for name, values, selector in criteria:
        _, best_indices = selector(values)
        formatted = [fmt(value) for value in values]
        print(f"{name:<14} {formatted[0]:>8} {formatted[1]:>8} {formatted[2]:>8} {print_best(best_indices):>14}")


def main():
    while True:
        print("\n" + "=" * 68)
        print("Практична робота №4")
        print("Ігри з природою")
        print("=" * 68)
        print("1. Показати матрицю корисності варіанту №1")
        print("2. Критерій Вальда")
        print("3. Критерій оптимізму")
        print("4. Критерій Гурвіца")
        print("5. Критерій Севіджа")
        print("6. Критерій Байєса")
        print("7. Критерій Лапласа")
        print("8. Підсумкова таблиця")
        print("0. Вийти")

        choice = input("\nОберіть дію: ").strip()
        if choice == "1":
            print_variant()
        elif choice == "2":
            wald_criterion()
        elif choice == "3":
            optimism_criterion()
        elif choice == "4":
            hurwicz_criterion()
        elif choice == "5":
            savage_criterion()
        elif choice == "6":
            bayes_criterion()
        elif choice == "7":
            laplace_criterion()
        elif choice == "8":
            summary()
        elif choice == "0":
            print("\nРоботу програми завершено.")
            break
        else:
            print("\nНевірний пункт меню. Спробуйте ще раз.")


if __name__ == "__main__":
    main()
