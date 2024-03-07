import random
from typing import Dict, Tuple
from collections import defaultdict
from models.class_model import Class
from models.class_types import ClassTypes
from models.course_model import Course
from models.group_model import Group
from models.science_degree_types import ScienceDegreeType
from models.subject_model import Subject
from models.subject_types import SubjectType
from models.teacher_model import Teacher
from typing import List

class SchedulingQLearning:
    def __init__(self, groups, teachers, subjects, class_types, subject_types, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.groups = groups
        self.teachers = teachers
        self.subjects = subjects
        self.class_types = class_types
        self.subject_types = subject_types
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.q_table = defaultdict(lambda: defaultdict(int))

    def get_state(self, schedule):
        state = []
        for day in ["monday", "tuesday", "wednesday", "thursday", "friday" ]:
            day_schedule = schedule[day]
            for period in range(1, 6):
                if period in day_schedule:
                    subject, teacher = day_schedule[period]
                    state.append((subject.name, subject.type.value, teacher.science_degree.value))
                else:
                    state.append(None)
        return tuple(state)

    def get_available_actions(self, state, schedule):
        actions = []
        for subject in self.subjects:
            for teacher in self.teachers:
                if subject in teacher.subjects:
                    if subject.type == SubjectType.lectures and teacher.science_degree == ScienceDegreeType.lecturer and self.get_subject_count_in_a_week(subject, schedule) < subject.count_per_term:
                        actions.append((subject, teacher))
                    elif subject.type == SubjectType.practics and teacher.science_degree == ScienceDegreeType.assistant and self.get_subject_count_in_a_week(subject, schedule) < subject.count_per_term:
                        actions.append((subject, teacher))
        return actions

    def get_reward(self, state, action, next_state):
        reward = 0
        schedule = self.get_schedule_from_state(next_state)

        # Проверка на наличие окон между парами
        for day, periods in schedule.items():
            last_period = None
            for period, subject_teacher in periods.items():
                if subject_teacher is not None and last_period is not None and period - last_period > 1:
                    reward -= 30
                last_period = period

        # Проверка на соответствие типа преподавателя типу предмета
        for day, periods in schedule.items():
            for period, subject_teacher in periods.items():
                if subject_teacher is not None:
                    subject, teacher = subject_teacher
                    if subject.type == SubjectType.lectures and teacher.science_degree != ScienceDegreeType.lecturer:
                        reward -= 10
                    elif subject.type == SubjectType.practics and teacher.science_degree == ScienceDegreeType.lecturer:
                        reward -= 10
        
        # Проверка на наличие всех предметов в расписании
        scheduled_subjects = set()
        for day, periods in schedule.items():
            for period, subject_teacher in periods.items():
                if subject_teacher is not None:
                    subject, teacher = subject_teacher
                    scheduled_subjects.add(subject)

        if len(scheduled_subjects) != len(self.subjects):
            missing_subjects = set(self.subjects) - scheduled_subjects
            for subject in missing_subjects:
                reward -= 50
        else:
            reward += 250
                
        return reward   
    
    def get_subject_count_in_a_week(self, subject, schedule):
        # Проверка на соответствие количества предметов заданному количеству
        subject_counts = {}
        for day, periods in schedule.items():
            for period, subject_teacher in periods.items():
                if subject_teacher is not None:
                    temp_subject, teacher = subject_teacher
                    subject_counts[temp_subject] = subject_counts.get(temp_subject, 0) + 1

        for temp_subject, count in subject_counts.items():
            if subject == temp_subject:
                return count
        return 0

    def update_q_table(self, state, action, next_state, reward):
        current_q = self.q_table[state][action]
        next_max_q = max([self.q_table[next_state][a] for a in self.get_available_actions(next_state, self.get_schedule_from_state(next_state))])
        new_q = current_q + self.alpha * (reward + self.gamma * next_max_q - current_q)
        self.q_table[state][action] = new_q

    def choose_action(self, state, schedule):
        if random.random() < self.epsilon:
            # Случайное действие (исследование)
            actions = self.get_available_actions(state, schedule)
            return random.choice(actions) if actions else None
        else:
            # Выбор действия с максимальным Q-значением (использование)
            q_values = {action: self.q_table[state][action] for action in self.get_available_actions(state, schedule)}
            if not q_values:
                return None
            max_q = max(q_values.values())
            best_actions = [action for action, q in q_values.items() if q == max_q]
            return random.choice(best_actions)

    def add_subject(self, schedule, subject, teacher, day, period):
        schedule[day][period] = (subject, teacher)

    def train(self, num_iterations):
        for iteration in range(num_iterations):
            group = random.choice(self.groups)
            schedule = {day: {} for day in ["monday", "tuesday", "wednesday", "thursday", "friday" ]}
            state = self.get_state(schedule)

            while True:
                action = self.choose_action(state, schedule)
                if action is None:
                    break

                subject, teacher = action
                day = random.choice(list(schedule.keys()))
                available_periods = [period for period in range(1, 6) if period not in schedule[day]]
                if not available_periods:
                    break

                period = random.choice(available_periods)
                self.add_subject(schedule, subject, teacher, day, period)
                next_state = self.get_state(schedule)
                reward = self.get_reward(state, action, next_state)
                self.update_q_table(state, action, next_state, reward)
                state = next_state

    def get_schedule_from_state(self, state):
        schedule = {day: {} for day in ["monday", "tuesday", "wednesday", "thursday", "friday" ]}
        for period, subject_info in enumerate(state):
            if subject_info is not None:
                subject_name, subject_type, teacher_degree = subject_info
                subject = next((s for s in self.subjects if s.name == subject_name and s.type.value == subject_type), None)
                teacher = next((t for t in self.teachers if t.science_degree.value == teacher_degree and subject in t.subjects), None)
                day = period // 5
                period_in_day = period % 5 + 1
                day_name = list(schedule.keys())[day]
                schedule[day_name][period_in_day] = (subject, teacher)
        return schedule

    def get_optimal_schedule(self, group):
        state = self.get_state({day: {} for day in ["monday", "tuesday", "wednesday", "thursday", "friday" ]})
        schedule = self.get_schedule_from_state(state)
        best_action = max(self.get_available_actions(state, schedule), key=lambda action: self.q_table[state][action])
        while best_action is not None:
            subject, teacher = best_action
            day = random.choice(list(schedule.keys()))
            available_periods = [period for period in range(1, 6) if period not in schedule[day]]
            if not available_periods:
                break
            period = random.choice(available_periods)
            self.add_subject(schedule, subject, teacher, day, period)
            state = self.get_state(schedule)
            best_action = max(self.get_available_actions(state, schedule), key=lambda action: self.q_table[state][action], default=None)
        return schedule
    

def generate_random_data():
    # Генерация случайных данных
    # num_groups = random.randint(1, 5)

    subject_names = ["Math", "Physics", "Chemistry", "Biology", "Computer Science"]
    subject_types = [SubjectType.lectures, SubjectType.practics]
    # subjects = [Subject(name, random.randint(5, 7), random.choice(subject_types)) for name in subject_names]
    subjects = [Subject("Math", 6, SubjectType.lectures), Subject("Physics", 4, SubjectType.lectures), Subject("Biology", 6, SubjectType.practics), Subject("Computer Science", 8, SubjectType.practics), Subject("Chemistry", 8, SubjectType.practics)]
    groups = [Group("Group 1", Course(1, "Course 1", subjects))]
    # num_teachers = random.randint(5, 10)
    # teacher_names = [f"Teacher {i}" for i in range(num_teachers)]
    teacher_degrees = [ScienceDegreeType.lecturer, ScienceDegreeType.assistant]
    # teachers = [Teacher(name, random.choice(teacher_degrees), random.sample(subjects, random.randint(1, len(subjects)))) for name in teacher_names]
    teachers = [Teacher("1", ScienceDegreeType.lecturer, [subjects[0], subjects[1]]), Teacher("2", ScienceDegreeType.assistant, [subjects[2], subjects[3]]), Teacher("2", ScienceDegreeType.assistant, [subjects[4]])]
    class_types = {
        "Lecture Hall 1": ClassTypes.lecture,
        "Lecture Hall 2": ClassTypes.lecture,
        "Computer Lab 1": ClassTypes.pc_class,
        "Computer Lab 2": ClassTypes.pc_class,
        "Lecture Hall 3": ClassTypes.lecture,
        "Lecture Hall 4": ClassTypes.lecture,
        "Computer Lab 3": ClassTypes.pc_class,
        "Computer Lab 4": ClassTypes.pc_class,
    }

    return groups, teachers, subjects, class_types, subject_types

def main():
    groups, teachers, subjects, class_types, subject_types = generate_random_data()

    # Создание экземпляра модели Q-learning
    q_learning = SchedulingQLearning(groups, teachers, subjects, class_types, subject_types)

    # Обучение модели
    num_iterations = 100000
    q_learning.train(num_iterations)

    # Тестирование модели на случайной группе
    test_group = random.choice(groups)
    optimal_schedule = q_learning.get_optimal_schedule(test_group)

    # Вывод оптимального расписания
    print(f"Optimal schedule for {test_group.name} ({test_group.course.course_name}):")
    for day, periods in optimal_schedule.items():
        print(f"{day.capitalize()}:")
        for period, (subject, teacher) in periods.items():
            print(f"  Period {period}: {subject.name} ({subject.type.name}) - {teacher.name}")

if __name__ == "__main__":
    main()