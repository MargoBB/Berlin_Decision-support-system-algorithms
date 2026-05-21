from fractions import Fraction
import itertools
import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


def f(value):
    return Fraction(value)


def fmt(value):
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    return f"{value.numerator}/{value.denominator}"


def print_variant():
    print("\nВаріант №1")
    print("Пряма задача Z:")
    print("  Z = x1 + x2 -> max")
    print("  2x1 + x2 = 3")
    print("  x1 + 2x2 <= 5")
    print("  x1 >= 0, x2 >= 0")


def build_dual():
    print("\nПобудова двоїстої задачі W")
    print("У прямій задачі перше обмеження є рівністю, тому y1 - вільна змінна.")
    print("Друге обмеження має знак <= у задачі максимуму, тому y2 >= 0.")
    print("\nДвоїста задача:")
    print("  W = 3y1 + 5y2 -> min")
    print("  2y1 + y2 >= 1")
    print("  y1 + 2y2 >= 1")
    print("  y1 - довільна за знаком, y2 >= 0")


def solve_2x2(a1, b1, c1, a2, b2, c2):
    determinant = a1 * b2 - a2 * b1
    if determinant == 0:
        return None
    x = (c1 * b2 - c2 * b1) / determinant
    y = (a1 * c2 - a2 * c1) / determinant
    return x, y


def primal_constraints(point):
    x1, x2 = point
    return [
        ("2x1 + x2 = 3", 2 * x1 + x2 == 3),
        ("x1 + 2x2 <= 5", x1 + 2 * x2 <= 5),
        ("x1 >= 0", x1 >= 0),
        ("x2 >= 0", x2 >= 0),
    ]


def dual_constraints(point):
    y1, y2 = point
    return [
        ("2y1 + y2 >= 1", 2 * y1 + y2 >= 1),
        ("y1 + 2y2 >= 1", y1 + 2 * y2 >= 1),
        ("y2 >= 0", y2 >= 0),
    ]


def primal_objective(point):
    x1, x2 = point
    return x1 + x2


def dual_objective(point):
    y1, y2 = point
    return 3 * y1 + 5 * y2


def print_point(name, point):
    print(f"  {name} = ({fmt(point[0])}, {fmt(point[1])})")


def primal_candidates():
    # Equality 2x1 + x2 = 3 is always active. Other boundary lines are:
    # x1 + 2x2 = 5, x1 = 0, x2 = 0.
    lines = [
        ("x1 + 2x2 = 5", (f(1), f(2), f(5))),
        ("x1 = 0", (f(1), f(0), f(0))),
        ("x2 = 0", (f(0), f(1), f(0))),
    ]
    candidates = []
    for name, (a2, b2, c2) in lines:
        point = solve_2x2(f(2), f(1), f(3), a2, b2, c2)
        if point is not None:
            candidates.append((f"2x1 + x2 = 3; {name}", point))
    return candidates


def dual_candidates():
    # Boundary lines of W:
    # 2y1 + y2 = 1, y1 + 2y2 = 1, y2 = 0.
    lines = [
        ("2y1 + y2 = 1", (f(2), f(1), f(1))),
        ("y1 + 2y2 = 1", (f(1), f(2), f(1))),
        ("y2 = 0", (f(0), f(1), f(0))),
    ]
    candidates = []
    for first, second in itertools.combinations(lines, 2):
        name1, (a1, b1, c1) = first
        name2, (a2, b2, c2) = second
        point = solve_2x2(a1, b1, c1, a2, b2, c2)
        if point is not None:
            candidates.append((f"{name1}; {name2}", point))
    return candidates


def solve_primal_graphically():
    print("\nГрафічне розв'язання прямої задачі")
    print("Перевіряємо точки перетину граничних прямих.")
    feasible = []

    for source, point in primal_candidates():
        print(f"\nТочка з умов: {source}")
        print_point("X", point)
        checks = primal_constraints(point)
        for text, ok in checks:
            print(f"  {text}: {'так' if ok else 'ні'}")
        if all(ok for _, ok in checks):
            value = primal_objective(point)
            feasible.append((value, point))
            print(f"  Z = {fmt(value)}")
        else:
            print("  Точка не належить допустимій області.")

    best = max(feasible, key=lambda item: item[0])
    print("\nОптимальний розв'язок прямої задачі:")
    print_point("X*", best[1])
    print(f"  Zmax = {fmt(best[0])}")
    return best


def solve_dual_graphically():
    print("\nГрафічне розв'язання двоїстої задачі")
    print("Перевіряємо точки перетину граничних прямих.")
    feasible = []

    for source, point in dual_candidates():
        print(f"\nТочка з умов: {source}")
        print_point("Y", point)
        checks = dual_constraints(point)
        for text, ok in checks:
            print(f"  {text}: {'так' if ok else 'ні'}")
        if all(ok for _, ok in checks):
            value = dual_objective(point)
            feasible.append((value, point))
            print(f"  W = {fmt(value)}")
        else:
            print("  Точка не належить допустимій області.")

    best = min(feasible, key=lambda item: item[0])
    print("\nОптимальний розв'язок двоїстої задачі:")
    print_point("Y*", best[1])
    print(f"  Wmin = {fmt(best[0])}")
    return best


def print_simplex_tableau():
    print("\nСимплекс-таблиця для прямої задачі")
    print("Для рівності вводимо штучну змінну a1, для нерівності - додаткову змінну x3.")
    print("Метод великої M: Z = x1 + x2 - M*a1 -> max")
    print("\nПочаткова система:")
    print("  2x1 + x2 + a1 = 3")
    print("  x1 + 2x2 + x3 = 5")
    print("\nОскільки оптимальна точка графічно дорівнює X* = (1/3, 7/3),")
    print("штучна змінна a1 виходить з базису, а значення цільової функції:")
    print("  Zmax = x1 + x2 = 1/3 + 7/3 = 8/3")


def compare_results():
    primal = solve_primal_graphically()
    dual = solve_dual_graphically()
    print("\nПорівняння результатів")
    print(f"  Zmax = {fmt(primal[0])}")
    print(f"  Wmin = {fmt(dual[0])}")
    if primal[0] == dual[0]:
        print("  Значення збігаються, що підтверджує теорему двоїстості.")
    else:
        print("  Значення не збігаються, потрібно перевірити розрахунок.")


def main():
    while True:
        print("\n" + "=" * 68)
        print("Практична робота №2")
        print("Двоїста задача лінійного програмування")
        print("=" * 68)
        print("1. Показати умову варіанту №1")
        print("2. Побудувати двоїсту задачу")
        print("3. Розв'язати пряму задачу графічно")
        print("4. Розв'язати двоїсту задачу графічно")
        print("5. Показати симплекс-підготовку прямої задачі")
        print("6. Порівняти результати прямої та двоїстої задач")
        print("0. Вийти")

        choice = input("\nОберіть дію: ").strip()
        if choice == "1":
            print_variant()
        elif choice == "2":
            build_dual()
        elif choice == "3":
            solve_primal_graphically()
        elif choice == "4":
            solve_dual_graphically()
        elif choice == "5":
            print_simplex_tableau()
        elif choice == "6":
            compare_results()
        elif choice == "0":
            print("\nРоботу програми завершено.")
            break
        else:
            print("\nНевірний пункт меню. Спробуйте ще раз.")


if __name__ == "__main__":
    main()
