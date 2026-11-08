% Construction Worker Assignment - Prolog reasoning engine
% Facts are synchronized from the SQLite database by Python.
:- dynamic worker/1, task/1, skill/2, skill_experience/3.
:- dynamic certification/2, available/1, required_skill/2.
:- dynamic minimum_experience/2, required_certification/2.

has_required_skill(W, T) :-
    worker(W), task(T),
    forall(required_skill(T, S), skill(W, S)).

experience_sufficient(Worker, Skill, RequiredYears) :-
    skill_experience(Worker, Skill, ActualYears),
    ActualYears >= RequiredYears.

has_required_experience(Worker, Task) :-
    worker(Worker),
    task(Task),
    minimum_experience(Task, RequiredYears),
    forall(
        required_skill(Task, Skill),
        experience_sufficient(Worker, Skill, RequiredYears)
    ).

has_required_certification(W, T) :-
    worker(W), task(T),
    forall(required_certification(T, C), certification(W, C)).

eligible_worker(W, T) :-
    worker(W), task(T),
    has_required_skill(W, T),
    has_required_experience(W, T),
    has_required_certification(W, T),
    available(W).

recommend_worker(T, W) :- eligible_worker(W, T).
recommend_task(W, T) :- eligible_worker(W, T).

% LISTS:
eligible_worker_list(T, Workers) :-
    findall(W, eligible_worker(W, T), Found), sort(Found, Workers).

% RECURSION:
count_workers([], 0).
count_workers([_|Tail], N) :-
    count_workers(Tail, Rest), N is Rest + 1.

% CONCATENATION:
combine_worker_lists(A, B, Combined) :- append(A, B, Combined).

