import sys


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stdin, "reconfigure"):
    sys.stdin.reconfigure(encoding="utf-8")


TASKS = {
    1: {"pred": [], "duration": 8, "people": 3},
    2: {"pred": [], "duration": 6, "people": 2},
    3: {"pred": [1], "duration": 13, "people": 5},
    4: {"pred": [1], "duration": 4, "people": 1},
    5: {"pred": [4], "duration": 5, "people": 2},
    6: {"pred": [2], "duration": 10, "people": 4},
    7: {"pred": [2], "duration": 6, "people": 1},
    8: {"pred": [7], "duration": 9, "people": 2},
    9: {"pred": [5, 6, 8], "duration": 10, "people": 3},
    10: {"pred": [3, 4, 9], "duration": 7, "people": 3},
    11: {"pred": [5, 6, 8], "duration": 11, "people": 5},
}


def successors(tasks=TASKS):
    result = {task: [] for task in tasks}
    for task, data in tasks.items():
        for predecessor in data["pred"]:
            result[predecessor].append(task)
    return result


def topological_order(tasks=TASKS):
    remaining = set(tasks)
    order = []
    while remaining:
        ready = sorted(
            task for task in remaining
            if all(predecessor in order for predecessor in tasks[task]["pred"])
        )
        if not ready:
            raise ValueError("У графі робіт є цикл.")
        order.extend(ready)
        remaining.difference_update(ready)
    return order


def calculate_cpm(tasks=TASKS):
    order = topological_order(tasks)
    succ = successors(tasks)
    result = {}

    for task in order:
        predecessors = tasks[task]["pred"]
        early_start = max((result[p]["EF"] for p in predecessors), default=0)
        early_finish = early_start + tasks[task]["duration"]
        result[task] = {
            "ES": early_start,
            "EF": early_finish,
            "LS": 0,
            "LF": 0,
            "reserve": 0,
        }

    project_duration = max(result[task]["EF"] for task in tasks)

    for task in reversed(order):
        task_successors = succ[task]
        late_finish = min((result[s]["LS"] for s in task_successors), default=project_duration)
        late_start = late_finish - tasks[task]["duration"]
        result[task]["LS"] = late_start
        result[task]["LF"] = late_finish
        result[task]["reserve"] = late_start - result[task]["ES"]

    return order, succ, result, project_duration


def print_variant():
    print("\nВаріант №1")
    print(f"{'Робота':>8} {'Попередні':>14} {'Тривалість':>12} {'Людей':>8}")
    for task in sorted(TASKS):
        predecessors = TASKS[task]["pred"]
        pred_text = ",".join(str(item) for item in predecessors) if predecessors else "-"
        print(f"{task:>8} {pred_text:>14} {TASKS[task]['duration']:>12} {TASKS[task]['people']:>8}")


def print_network():
    _, succ, _, _ = calculate_cpm()
    print("\nСітковий графік робіт")
    print("Формат: робота -> наступні роботи")
    for task in sorted(TASKS):
        next_tasks = succ[task]
        next_text = ", ".join(str(item) for item in next_tasks) if next_tasks else "фініш"
        print(f"  {task} -> {next_text}")


def print_cpm_table():
    _, _, result, project_duration = calculate_cpm()
    print("\nПараметри сіткового графіка")
    print(f"{'Робота':>8} {'t':>5} {'ES':>5} {'EF':>5} {'LS':>5} {'LF':>5} {'R':>5} {'Крит.':>8}")
    for task in sorted(TASKS):
        data = result[task]
        is_critical = "так" if data["reserve"] == 0 else "ні"
        print(
            f"{task:>8} {TASKS[task]['duration']:>5} {data['ES']:>5} {data['EF']:>5} "
            f"{data['LS']:>5} {data['LF']:>5} {data['reserve']:>5} {is_critical:>8}"
        )
    print(f"\nТривалість проєкту: {project_duration}")


def critical_paths():
    _, succ, result, project_duration = calculate_cpm()
    starts = [task for task in TASKS if not TASKS[task]["pred"] and result[task]["reserve"] == 0]
    paths = []

    def walk(task, path):
        critical_successors = [
            item for item in succ[task]
            if result[item]["reserve"] == 0 and result[item]["ES"] == result[task]["EF"]
        ]
        if not critical_successors:
            if result[task]["EF"] == project_duration:
                paths.append(path[:])
            return
        for next_task in critical_successors:
            walk(next_task, path + [next_task])

    for start in starts:
        walk(start, [start])
    return paths


def print_critical_path():
    paths = critical_paths()
    _, _, _, project_duration = calculate_cpm()
    print("\nКритичний шлях")
    for index, path in enumerate(paths, start=1):
        print(f"  Шлях {index}: " + " -> ".join(str(task) for task in path))
    print(f"  Довжина критичного шляху: {project_duration}")


def schedule_from_start_times(start_times):
    finish_times = {
        task: start_times[task] + TASKS[task]["duration"]
        for task in TASKS
    }
    project_duration = max(finish_times.values())
    return finish_times, project_duration


def resource_load(start_times):
    finish_times, project_duration = schedule_from_start_times(start_times)
    loads = []
    for day in range(project_duration):
        active = [
            task for task in sorted(TASKS)
            if start_times[task] <= day < finish_times[task]
        ]
        people = sum(TASKS[task]["people"] for task in active)
        loads.append((day, active, people))
    return loads


def print_calendar_plan(start_times, title):
    finish_times, project_duration = schedule_from_start_times(start_times)
    print(f"\n{title}")
    print(f"{'Робота':>8} {'Початок':>10} {'Кінець':>10} {'Людей':>8} {'Діаграма':>20}")
    for task in sorted(TASKS):
        bar = "." * start_times[task] + "#" * TASKS[task]["duration"]
        print(
            f"{task:>8} {start_times[task]:>10} {finish_times[task]:>10} "
            f"{TASKS[task]['people']:>8} {bar}"
        )
    print(f"Тривалість календарного плану: {project_duration}")


def print_resource_table(start_times, title):
    print(f"\n{title}")
    print(f"{'Період':>8} {'Активні роботи':>24} {'Людей':>8}")
    for day, active, people in resource_load(start_times):
        active_text = ", ".join(str(task) for task in active) if active else "-"
        print(f"{day:>3}-{day + 1:<3} {active_text:>24} {people:>8}")


def early_start_schedule():
    _, _, result, _ = calculate_cpm()
    return {task: result[task]["ES"] for task in TASKS}


def optimize_resources():
    _, _, result, project_duration = calculate_cpm()
    succ = successors()
    start_times = early_start_schedule()
    critical = {task for task in TASKS if result[task]["reserve"] == 0}

    movable = sorted(
        (task for task in TASKS if task not in critical),
        key=lambda task: (TASKS[task]["people"], result[task]["reserve"]),
        reverse=True,
    )

    def peak_load(times):
        loads = resource_load(times)
        peak = max(people for _, _, people in loads)
        total_square = sum(people * people for _, _, people in loads)
        return peak, total_square

    for task in movable:
        best_start = start_times[task]
        best_score = peak_load(start_times)
        min_start = result[task]["ES"]
        max_start = result[task]["LS"]

        for candidate in range(min_start, max_start + 1):
            trial = start_times.copy()
            trial[task] = candidate

            valid = True
            for successor in succ[task]:
                if trial[task] + TASKS[task]["duration"] > trial[successor]:
                    valid = False
                    break
            if not valid:
                continue

            score = peak_load(trial)
            if score < best_score:
                best_score = score
                best_start = candidate

        start_times[task] = best_start

    return start_times, project_duration


def print_calendar_and_resources():
    start_times = early_start_schedule()
    print_calendar_plan(start_times, "Календарний план за ранніми строками")
    print_resource_table(start_times, "Графік завантаження людських ресурсів")


def print_optimized_resources():
    start_times, project_duration = optimize_resources()
    print_calendar_plan(start_times, "Оптимізований календарний план")
    print_resource_table(start_times, "Оптимізований графік завантаження ресурсів")
    _, actual_duration = schedule_from_start_times(start_times)
    if actual_duration == project_duration:
        print("\nТривалість проєкту не змінилася.")
    else:
        print("\nУвага: тривалість проєкту змінилася.")


def main():
    while True:
        print("\n" + "=" * 68)
        print("Практична робота №7")
        print("Сіткове планування. Метод критичного шляху")
        print("=" * 68)
        print("1. Показати умову варіанту №1")
        print("2. Побудувати сітковий графік")
        print("3. Розрахувати параметри графіка")
        print("4. Знайти критичний шлях")
        print("5. Побудувати календарний план і ресурси")
        print("6. Оптимізувати графік людських ресурсів")
        print("0. Вийти")

        choice = input("\nОберіть дію: ").strip()
        if choice == "1":
            print_variant()
        elif choice == "2":
            print_network()
        elif choice == "3":
            print_cpm_table()
        elif choice == "4":
            print_critical_path()
        elif choice == "5":
            print_calendar_and_resources()
        elif choice == "6":
            print_optimized_resources()
        elif choice == "0":
            print("\nРоботу програми завершено.")
            break
        else:
            print("\nНевірний пункт меню. Спробуйте ще раз.")


if __name__ == "__main__":
    main()
