from fractions import Fraction
import random
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


A1 = [
    [3, 1, 1],
    [2, -2, 1],
    [-1, -3, -2],
]

A2 = [
    [2, 5],
    [8, 1],
]

A3 = [
    [16, 20, 15, 19],
    [22, 18, 17, 11],
]


def fmt(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def fmt_decimal(value, digits=3):
    return f"{float(Fraction(value)):.{digits}f}"


def print_matrix(matrix, title):
    print(f"\n{title}:")
    for row in matrix:
        print("  " + " ".join(f"{value:>6}" for value in row))


def print_variant():
    print("\nВаріант №1")
    print_matrix(A1, "Матриця гри A1")
    print_matrix(A2, "Матриця гри A2")
    print_matrix(A3, "Матриця гри A3")


def saddle_points(matrix):
    row_minima = [min(row) for row in matrix]
    column_maxima = [max(matrix[row][col] for row in range(len(matrix))) for col in range(len(matrix[0]))]
    lower_value = max(row_minima)
    upper_value = min(column_maxima)
    points = []

    if lower_value == upper_value:
        for row_index, row in enumerate(matrix):
            for col_index, value in enumerate(row):
                if value == lower_value and value == row_minima[row_index] and value == column_maxima[col_index]:
                    points.append((row_index, col_index, value))

    return row_minima, column_maxima, lower_value, upper_value, points


def check_a1_pure_strategy():
    print_matrix(A1, "Матриця гри A1")
    row_minima, column_maxima, lower_value, upper_value, points = saddle_points(A1)

    print("\nМінімуми рядків:")
    for index, value in enumerate(row_minima, start=1):
        print(f"  min A{index} = {value}")
    print(f"  Нижня ціна гри alpha = max(min рядків) = {lower_value}")

    print("\nМаксимуми стовпців:")
    for index, value in enumerate(column_maxima, start=1):
        print(f"  max B{index} = {value}")
    print(f"  Верхня ціна гри beta = min(max стовпців) = {upper_value}")

    if points:
        print("\nОскільки alpha = beta, гра має розв'язок у чистих стратегіях.")
        for row, col, value in points:
            print(f"  Сідлова точка: A{row + 1}, B{col + 1}; ціна гри v = {value}")
        print("  Оптимальна стратегія гравця A: обрати рядок A1.")
        print("  Оптимальна стратегія гравця B: обрати B2 або B3.")
    else:
        print("\nОскільки alpha != beta, розв'язок у чистих стратегіях відсутній.")


def simulate_a1(rounds=20, seed=42):
    print_matrix(A1, "Матриця гри A1")
    print("\nТеоретичні оптимальні стратегії:")
    print("  Гравець A: P = (1, 0, 0)")
    print("  Гравець B: Q = (0, 1/2, 1/2)")
    print("  Теоретична ціна гри v = 1")

    random.seed(seed)
    total = 0
    print("\nПротокол моделювання матричної гри:")
    print(f"{'№':>3} {'rA':>8} {'A':>6} {'rB':>8} {'B':>6} {'виграш A':>10} {'накоп.':>10} {'середній':>10}")
    for index in range(1, rounds + 1):
        random_a = random.random()
        random_b = random.random()
        row = 0
        col = 1 if random_b < 0.5 else 2
        payoff = A1[row][col]
        total += payoff
        average = Fraction(total, index)
        print(
            f"{index:>3} {random_a:>8.3f} {'A1':>6} {random_b:>8.3f} "
            f"{'B' + str(col + 1):>6} {payoff:>10} {total:>10} {fmt_decimal(average):>10}"
        )

    print(f"\nСередній виграш після {rounds} партій: {fmt_decimal(Fraction(total, rounds))}")
    print("За оптимальних стратегій він збігається з теоретичною ціною гри v = 1.")


def solve_2x2_game(matrix, title):
    a, b = map(Fraction, matrix[0])
    c, d = map(Fraction, matrix[1])
    denominator = a - b - c + d

    if denominator == 0:
        raise ValueError("Для цієї матриці формула 2x2 має нульовий знаменник.")

    p = (d - c) / denominator
    q = (d - b) / denominator
    value = (a * d - b * c) / denominator

    print_matrix(matrix, title)
    print("\nАналітичний розв'язок гри 2x2:")
    print("  p - імовірність вибору першого рядка гравцем A")
    print("  q - імовірність вибору першого стовпця гравцем B")
    print(f"  p = (d - c) / (a - b - c + d) = {fmt(p)} = {fmt_decimal(p)}")
    print(f"  q = (d - b) / (a - b - c + d) = {fmt(q)} = {fmt_decimal(q)}")
    print(f"  v = (ad - bc) / (a - b - c + d) = {fmt(value)} = {fmt_decimal(value)}")
    print("\nОптимальні змішані стратегії:")
    print(f"  P* = ({fmt(p)}, {fmt(1 - p)})")
    print(f"  Q* = ({fmt(q)}, {fmt(1 - q)})")
    print(f"  Ціна гри v = {fmt(value)}")
    return p, q, value


def solve_a2():
    row_minima, column_maxima, lower_value, upper_value, points = saddle_points(A2)
    print_matrix(A2, "Матриця гри A2")
    print(f"\nНижня ціна alpha = {lower_value}")
    print(f"Верхня ціна beta = {upper_value}")
    if points:
        print("Гра має сідлову точку.")
        return
    print("Сідлова точка відсутня, тому шукаємо змішані стратегії.")
    solve_2x2_game(A2, "Матриця гри A2")
    print("\nГрафічна інтерпретація:")
    print("  Для гравця A: 2p + 8(1-p) = 5p + 1(1-p)")
    print("  8 - 6p = 1 + 4p, тому p = 7/10.")
    print("  Для гравця B: 2q + 5(1-q) = 8q + 1(1-q)")
    print("  5 - 3q = 1 + 7q, тому q = 2/5.")


def reduce_a3():
    print_matrix(A3, "Початкова матриця гри A3")
    print("\nГравець B мінімізує виграш A, тому можна видалити доміновані стовпці.")
    print("  Стовпець B1 = (16, 22) домінується стовпцем B3 = (15, 17).")
    print("  Стовпець B2 = (20, 18) домінується стовпцем B3 = (15, 17).")
    reduced = [
        [15, 19],
        [17, 11],
    ]
    print_matrix(reduced, "Зведена матриця 2x2 за стовпцями B3 та B4")
    return reduced


def solve_a3():
    reduced = reduce_a3()
    p, q, value = solve_2x2_game(reduced, "Зведена матриця A3")
    print("\nПовернення до початкової гри A3:")
    print(f"  P* = ({fmt(p)}, {fmt(1 - p)}) для рядків A1, A2")
    print(f"  Q* = (0, 0, {fmt(q)}, {fmt(1 - q)}) для стовпців B1, B2, B3, B4")
    print(f"  Ціна гри v = {fmt(value)}")
    print("\nГрафічна інтерпретація:")
    print("  Для гравця A: 15p + 17(1-p) = 19p + 11(1-p)")
    print("  17 - 2p = 11 + 8p, тому p = 3/5.")
    print("  Для гравця B: 15q + 19(1-q) = 17q + 11(1-q)")
    print("  19 - 4q = 11 + 6q, тому q = 4/5.")


def main():
    while True:
        print("\n" + "=" * 68)
        print("Практична робота №3")
        print("Матричні ігри з нульовою сумою")
        print("=" * 68)
        print("1. Показати умову варіанту №1")
        print("2. Перевірити A1 на чисті стратегії")
        print("3. Змоделювати гру A1")
        print("4. Розв'язати гру A2 2x2")
        print("5. Розв'язати гру A3 2xn зі зведенням до 2x2")
        print("0. Вийти")

        choice = input("\nОберіть дію: ").strip()
        if choice == "1":
            print_variant()
        elif choice == "2":
            check_a1_pure_strategy()
        elif choice == "3":
            simulate_a1()
        elif choice == "4":
            solve_a2()
        elif choice == "5":
            solve_a3()
        elif choice == "0":
            print("\nРоботу програми завершено.")
            break
        else:
            print("\nНевірний пункт меню. Спробуйте ще раз.")


if __name__ == "__main__":
    main()
