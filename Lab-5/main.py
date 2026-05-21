import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


COSTS = [
    [9, 4, 6, 9],
    [7, 5, 7, 9],
    [5, 6, 4, 8],
]

SUPPLY = [105, 135, 125]
DEMAND = [85, 125, 105, 50]


def print_matrix(matrix, title, row_prefix="A", col_prefix="B"):
    print(f"\n{title}:")
    headers = [""] + [f"{col_prefix}{index + 1}" for index in range(len(matrix[0]))]
    print("".join(f"{header:>8}" for header in headers))
    for index, row in enumerate(matrix):
        values = [f"{row_prefix}{index + 1}"] + [str(value) if value is not None else "-" for value in row]
        print("".join(f"{value:>8}" for value in values))


def print_variant():
    print("\nВаріант №1")
    print_matrix(COSTS, "Матриця вартостей SP")
    print("\nЗапаси PO:")
    print("  " + " ".join(str(value) for value in SUPPLY))
    print("Потреби PN:")
    print("  " + " ".join(str(value) for value in DEMAND))


def check_balance():
    total_supply = sum(SUPPLY)
    total_demand = sum(DEMAND)
    print_variant()
    print("\nПеревірка форми транспортної задачі:")
    print(f"  Сума запасів: {total_supply}")
    print(f"  Сума потреб:  {total_demand}")
    if total_supply == total_demand:
        print("  Транспортна задача є закритою.")
    elif total_supply > total_demand:
        print("  Транспортна задача є відкритою.")
        print(f"  Потрібно додати фіктивний пункт призначення з потребою {total_supply - total_demand}.")
    else:
        print("  Транспортна задача є відкритою.")
        print(f"  Потрібно додати фіктивний пункт відправлення із запасом {total_demand - total_supply}.")


def empty_plan():
    return [[None for _ in DEMAND] for _ in SUPPLY]


def plan_cost(plan):
    total = 0
    for i, row in enumerate(plan):
        for j, value in enumerate(row):
            if value is not None:
                total += value * COSTS[i][j]
    return total


def print_plan(plan, title):
    printable = [[0 if value is None else value for value in row] for row in plan]
    print_matrix(printable, title)
    print(f"Загальна вартість перевезень: {plan_cost(plan)}")


def northwest_corner_plan(show_steps=True):
    supply = SUPPLY[:]
    demand = DEMAND[:]
    plan = empty_plan()
    i = 0
    j = 0
    step = 1

    if show_steps:
        print("\nМетод північно-західного кута")

    while i < len(supply) and j < len(demand):
        amount = min(supply[i], demand[j])
        plan[i][j] = amount
        if show_steps:
            print(f"  Крок {step}: x{i + 1}{j + 1} = min({supply[i]}, {demand[j]}) = {amount}")
        supply[i] -= amount
        demand[j] -= amount
        step += 1

        if supply[i] == 0 and demand[j] == 0:
            if i + 1 < len(supply) and j + 1 < len(demand):
                j += 1
            else:
                i += 1
                j += 1
        elif supply[i] == 0:
            i += 1
        else:
            j += 1

    return plan


def least_cost_plan(show_steps=True):
    supply = SUPPLY[:]
    demand = DEMAND[:]
    plan = empty_plan()
    step = 1

    if show_steps:
        print("\nМетод мінімального елемента")

    while any(value > 0 for value in supply) and any(value > 0 for value in demand):
        candidates = []
        for i in range(len(supply)):
            for j in range(len(demand)):
                if supply[i] > 0 and demand[j] > 0:
                    candidates.append((COSTS[i][j], i, j))
        _, i, j = min(candidates)
        amount = min(supply[i], demand[j])
        plan[i][j] = amount
        if show_steps:
            print(
                f"  Крок {step}: мінімальна доступна вартість c{i + 1}{j + 1} = {COSTS[i][j]}, "
                f"x{i + 1}{j + 1} = min({supply[i]}, {demand[j]}) = {amount}"
            )
        supply[i] -= amount
        demand[j] -= amount
        step += 1

    return plan


def basis_cells(plan):
    return [(i, j) for i, row in enumerate(plan) for j, value in enumerate(row) if value is not None]


def compute_potentials(plan):
    rows = len(SUPPLY)
    cols = len(DEMAND)
    u = [None] * rows
    v = [None] * cols
    u[0] = 0
    changed = True

    while changed:
        changed = False
        for i, j in basis_cells(plan):
            if u[i] is not None and v[j] is None:
                v[j] = COSTS[i][j] - u[i]
                changed = True
            elif u[i] is None and v[j] is not None:
                u[i] = COSTS[i][j] - v[j]
                changed = True

    return u, v


def reduced_costs(plan, u, v):
    deltas = [[None for _ in DEMAND] for _ in SUPPLY]
    for i in range(len(SUPPLY)):
        for j in range(len(DEMAND)):
            if plan[i][j] is None:
                deltas[i][j] = COSTS[i][j] - u[i] - v[j]
    return deltas


def find_entering_cell(deltas):
    best = None
    for i, row in enumerate(deltas):
        for j, value in enumerate(row):
            if value is not None and value < 0:
                if best is None or value < best[0]:
                    best = (value, i, j)
    return best


def find_cycle(plan, entering):
    cells = set(basis_cells(plan))
    cells.add(entering)
    rows = {}
    cols = {}
    for cell in cells:
        rows.setdefault(cell[0], []).append(cell)
        cols.setdefault(cell[1], []).append(cell)

    def dfs(path, use_row):
        current = path[-1]
        neighbors = rows[current[0]] if use_row else cols[current[1]]
        for neighbor in neighbors:
            if neighbor == current:
                continue
            if neighbor == entering and len(path) >= 4:
                return path
            if neighbor in path:
                continue
            result = dfs(path + [neighbor], not use_row)
            if result:
                return result
        return None

    return dfs([entering], True) or dfs([entering], False)


def optimize_by_potentials(initial_plan):
    plan = [row[:] for row in initial_plan]
    iteration = 1

    while True:
        print_plan(plan, f"План перевезень на ітерації {iteration}")
        u, v = compute_potentials(plan)
        print("\nПотенціали:")
        print("  " + ", ".join(f"u{i + 1} = {u[i]}" for i in range(len(u))))
        print("  " + ", ".join(f"v{j + 1} = {v[j]}" for j in range(len(v))))

        deltas = reduced_costs(plan, u, v)
        print_matrix(deltas, "Оцінки вільних клітин Δij")
        entering = find_entering_cell(deltas)
        if entering is None:
            print("\nУсі оцінки Δij >= 0. План є оптимальним.")
            return plan

        value, i, j = entering
        print(f"\nНайбільш від'ємна оцінка: Δ{i + 1}{j + 1} = {value}. Клітина входить у базис.")
        cycle = find_cycle(plan, (i, j))
        if not cycle:
            raise RuntimeError("Не вдалося побудувати цикл перерахунку.")

        minus_cells = cycle[1::2]
        theta = min(plan[row][col] for row, col in minus_cells)
        print("Цикл перерахунку:")
        print("  " + " -> ".join(f"x{row + 1}{col + 1}" for row, col in cycle))
        print(f"θ = min({', '.join(str(plan[row][col]) for row, col in minus_cells)}) = {theta}")

        for index, (row, col) in enumerate(cycle):
            if index % 2 == 0:
                plan[row][col] = (0 if plan[row][col] is None else plan[row][col]) + theta
            else:
                plan[row][col] -= theta
                if plan[row][col] == 0:
                    plan[row][col] = None
        iteration += 1


def solve_by_potentials():
    print("\nПочатковий план беремо методом мінімального елемента.")
    initial = least_cost_plan(show_steps=True)
    optimal = optimize_by_potentials(initial)
    print_plan(optimal, "Оптимальний план перевезень")


def linear_programming_statement():
    print("\nПостановка транспортної задачі як задачі лінійного програмування")
    print("Мінімізувати:")
    terms = []
    for i in range(len(SUPPLY)):
        for j in range(len(DEMAND)):
            terms.append(f"{COSTS[i][j]}x{i + 1}{j + 1}")
    print("  Z = " + " + ".join(terms) + " -> min")

    print("\nОбмеження за запасами:")
    for i, supply in enumerate(SUPPLY):
        variables = " + ".join(f"x{i + 1}{j + 1}" for j in range(len(DEMAND)))
        print(f"  {variables} = {supply}")

    print("\nОбмеження за потребами:")
    for j, demand in enumerate(DEMAND):
        variables = " + ".join(f"x{i + 1}{j + 1}" for i in range(len(SUPPLY)))
        print(f"  {variables} = {demand}")

    print("\nУмова невід'ємності:")
    print("  xij >= 0")


def simplex_tableau_text():
    print("\nСимплекс-таблиця для транспортної задачі")
    print("У симплекс-формі змінними є перевезення xij.")
    print("Оскільки задача закрита, одне з рівнянь балансу є залежним, тому можна використати 6 незалежних рівнянь.")
    print("\nБазисний план з методу мінімального елемента використовується як початкова базисна точка:")
    plan = least_cost_plan(show_steps=False)
    print_plan(plan, "Початковий базисний план")
    print("\nДалі оптимізація виконується методом потенціалів, який є спеціалізованою формою симплекс-методу для транспортної задачі.")


def main():
    while True:
        print("\n" + "=" * 68)
        print("Практична робота №5")
        print("Транспортна задача. Метод потенціалів")
        print("=" * 68)
        print("1. Показати умову варіанту №1")
        print("2. Перевірити відкритість/закритість задачі")
        print("3. Початковий план методом північно-західного кута")
        print("4. Початковий план методом мінімального елемента")
        print("5. Оптимальний план методом потенціалів")
        print("6. Постановка як задача лінійного програмування")
        print("7. Симплекс-таблиця для транспортної задачі")
        print("0. Вийти")

        choice = input("\nОберіть дію: ").strip()
        if choice == "1":
            print_variant()
        elif choice == "2":
            check_balance()
        elif choice == "3":
            plan = northwest_corner_plan()
            print_plan(plan, "Початковий план методом північно-західного кута")
        elif choice == "4":
            plan = least_cost_plan()
            print_plan(plan, "Початковий план методом мінімального елемента")
        elif choice == "5":
            solve_by_potentials()
        elif choice == "6":
            linear_programming_statement()
        elif choice == "7":
            simplex_tableau_text()
        elif choice == "0":
            print("\nРоботу програми завершено.")
            break
        else:
            print("\nНевірний пункт меню. Спробуйте ще раз.")


if __name__ == "__main__":
    main()
